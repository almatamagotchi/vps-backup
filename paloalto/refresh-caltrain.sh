#!/usr/local/bin/python3
"""Refresh Caltrain departure data from 511.org API — with carry-forward.

511.org intermittently returns empty stop-monitoring responses (transient
failures / rate limiting). An empty response must NOT overwrite good data,
or the board shows "no trains" for a direction that has plenty. This version
retries once on network errors and carries forward the previous round's
departures when a refresh comes back empty, as long as those departures are
still in the future (grace: 2 minutes). Stations that genuinely have no
departures (e.g. the SF northbound terminus) stay empty honestly.

Stop codes from the 511.org CT stops list (operator_id=CT):
  san_francisco 70011/70012, millbrae 70061/70062, hillsdale 70111/70112,
  san_mateo 70091/70092, redwood_city 70141/70142, menlo_park 70161/70162,
  palo_alto 70171/70172, california_ave 70191/70192,
  mountain_view 70211/70212, sj_diridon 70261/70262.
"""
import datetime
import gzip
import json
import os
import time
import urllib.request

API_KEY = "e04a2c65-748c-4355-9333-1ffb3f7b0436"
OUT = "/usr/local/www/alma/paloalto/caltrain.json"
TMP = OUT + ".tmp"

STATIONS = {
    "san_francisco": {"name": "San Francisco", "nb": "70011", "sb": "70012"},
    "millbrae": {"name": "Millbrae", "nb": "70061", "sb": "70062"},
    "hillsdale": {"name": "Hillsdale", "nb": "70111", "sb": "70112"},
    "san_mateo": {"name": "San Mateo", "nb": "70091", "sb": "70092"},
    "redwood_city": {"name": "Redwood City", "nb": "70141", "sb": "70142"},
    "menlo_park": {"name": "Menlo Park", "nb": "70161", "sb": "70162"},
    "palo_alto": {"name": "Palo Alto", "nb": "70171", "sb": "70172"},
    "california_ave": {"name": "California Ave", "nb": "70191", "sb": "70192"},
    "mountain_view": {"name": "Mountain View", "nb": "70211", "sb": "70212"},
    "sj_diridon": {"name": "San Jose Diridon", "nb": "70261", "sb": "70262"},
}

GRACE_S = 120  # keep carried-forward departures at most this far in the past


def fetch_stop(stop_code):
    url = (
        "https://api.511.org/transit/StopMonitoring"
        f"?api_key={API_KEY}&agency=CT&stopCode={stop_code}&format=json"
    )
    req = urllib.request.Request(
        url, headers={"Accept-Encoding": "gzip", "User-Agent": "caltrain-refresh/1.0"}
    )
    for attempt in (1, 2):
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw = resp.read()
                if resp.headers.get("Content-Encoding") == "gzip":
                    raw = gzip.decompress(raw)
            data = json.loads(raw.decode("utf-8-sig"))
        except Exception as exc:
            print(f"ERROR fetching stop {stop_code} (attempt {attempt}): {exc}", flush=True)
            if attempt == 1:
                time.sleep(2.5)
            continue
        visits = (
            data.get("ServiceDelivery", {})
            .get("StopMonitoringDelivery", {})
            .get("MonitoredStopVisit", [])
        )
        deps = []
        for visit in visits:
            mvj = visit.get("MonitoredVehicleJourney", {})
            if not mvj:
                continue
            call = mvj.get("MonitoredCall") or {}
            deps.append({
                "line": mvj.get("LineRef", ""),
                "destination": mvj.get("DestinationName", ""),
                "expected": call.get("ExpectedDepartureTime", ""),
                "aimed": call.get("AimedDepartureTime", ""),
            })
        return deps
    return []


def future_only(deps, now_ts):
    """Keep only departures still ahead (or within GRACE_S of passing)."""
    out = []
    for d in deps:
        exp = d.get("expected") or ""
        try:
            ts = datetime.datetime.fromisoformat(exp.replace("Z", "+00:00")).timestamp()
        except Exception:
            out.append(d)
            continue
        if ts >= now_ts - GRACE_S:
            out.append(d)
    return out


def main():
    now_ts = time.time()
    prev = {}
    try:
        with open(OUT) as fh:
            prev = json.load(fh).get("stations", {})
    except Exception:
        prev = {}

    result = {
        "updated": datetime.datetime.now(datetime.timezone.utc)
        .strftime("%Y-%m-%dT%H:%M:%SZ"),
        "stations": {},
    }
    for key, cfg in STATIONS.items():
        nb = fetch_stop(cfg["nb"])
        sb = fetch_stop(cfg["sb"])
        p = prev.get(key) or {}
        nb = nb or future_only(p.get("nb", []), now_ts)
        sb = sb or future_only(p.get("sb", []), now_ts)
        if nb or sb:
            result["stations"][key] = {
                "name": cfg["name"],
                "nb": nb,
                "sb": sb,
            }
        else:
            print(f"WARN: no data for {key} this round", flush=True)

    with open(TMP, "w") as fh:
        json.dump(result, fh)
    os.replace(TMP, OUT)
    print(f"caltrain.json updated: {len(result['stations'])} stations", flush=True)


if __name__ == "__main__":
    main()
