#!/usr/local/bin/python3
"""Refresh Caltrain departure data from 511.org API.
Fetches next departures for California Ave and Palo Alto stations (NB+SB).
Writes combined results to caltrain.json for the dashboard.
"""
import gzip
import json
import os
import urllib.request

API_KEY = "e04a2c65-748c-4355-9333-1ffb3f7b0436"
OUT = "/usr/local/www/alma/paloalto/caltrain.json"
TMP = OUT + ".tmp"

STATIONS = {
    "california_ave": {"name": "California Ave", "nb": "70191", "sb": "70192"},
    "palo_alto": {"name": "Palo Alto", "nb": "70171", "sb": "70172"},
}


def fetch_stop(stop_code):
    url = (
        "https://api.511.org/transit/StopMonitoring"
        f"?api_key={API_KEY}&agency=CT&stopCode={stop_code}&format=json"
    )
    req = urllib.request.Request(url, headers={"Accept-Encoding": "gzip"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read()
            if resp.headers.get("Content-Encoding") == "gzip":
                raw = gzip.decompress(raw)
        data = json.loads(raw.decode("utf-8-sig"))
    except Exception as exc:
        print(f"ERROR fetching stop {stop_code}: {exc}", flush=True)
        return []
    visits = (
        data.get("ServiceDelivery", {})
        .get("StopMonitoringDelivery", {})
        .get("MonitoredStopVisit", [])
    )
    result = []
    for v in visits[:5]:
        mvj = v.get("MonitoredVehicleJourney", {})
        mc = mvj.get("MonitoredCall", {})
        result.append(
            {
                "line": mvj.get("LineRef", ""),
                "destination": mc.get("DestinationDisplay", ""),
                "expected": mc.get("ExpectedDepartureTime", ""),
                "aimed": mc.get("AimedDepartureTime", ""),
            }
        )
    return result


def main():
    result = {}
    for key, station in STATIONS.items():
        nb = fetch_stop(station["nb"])
        sb = fetch_stop(station["sb"])
        result[key] = {"name": station["name"], "nb": nb, "sb": sb}

    from datetime import datetime, timezone

    payload = {
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "stations": result,
    }

    with open(TMP, "w") as f:
        json.dump(payload, f, separators=(",", ":"))
    os.rename(TMP, OUT)
    os.chmod(OUT, 0o644)
    print("Caltrain data refreshed OK", flush=True)


if __name__ == "__main__":
    main()
