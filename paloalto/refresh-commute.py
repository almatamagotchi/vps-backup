#!/usr/local/bin/python3
"""refresh-commute.py — live-traffic door-to-door commute times for the paloalto board.

Calls the TomTom Routing API (traffic=true) for every board destination,
writes commute.json into the board's docroot. Carry-forward on failure:
if a run can't produce any route, the previous file is left in place
(up to MAX_AGE) so the board never goes blank.

Key lives in /usr/local/etc/paloalto-tomtom.key (root-only, 600).
Runs from root's crontab every 10 minutes.
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request

KEY_FILE = "/usr/local/etc/paloalto-tomtom.key"
OUT = "/usr/local/www/alma/paloalto/commute.json"
TMP = OUT + ".tmp"
MAX_AGE = 3 * 3600          # don't carry a stale file forward past 3h
STALE_AFTER = 25 * 60       # board treats data older than this as stale

ORIGIN = (-122.1473, 37.4074)  # 3210 porter dr, palo alto (matches the board)

# name, lon, lat — mirrors COMMUTE_DEST in index.html exactly
DEST = [
    ("San Francisco", -122.3935, 37.7955),
    ("SFO",           -122.3840, 37.6225),
    ("SJC",           -121.9293, 37.3633),
    ("Oakland",       -122.2747, 37.7958),
    ("Vallejo",       -122.2630, 38.1005),
    ("Livermore",     -121.7683, 37.6834),
    ("Hayward",       -122.0858, 37.6709),
    ("Santa Cruz",    -122.0154, 36.9646),
    ("Gilroy",        -121.5654, 37.0253),
    ("Long Beach",    -118.1459, 33.8277),
]


def load_key():
    try:
        with open(KEY_FILE) as fh:
            key = fh.read().strip()
        return key or None
    except OSError:
        return None


def fetch_route(key, name, lon, lat):
    url = (
        "https://api.tomtom.com/routing/1/calculateRoute/"
        f"{ORIGIN[1]},{ORIGIN[0]}:{lat},{lon}/json"
        f"?key={key}&traffic=true&travelMode=car&routeType=fastest&departAt=now"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "alma-paloalto-board/1.0"})
    with urllib.request.urlopen(req, timeout=25) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    routes = data.get("routes") or []
    if not routes:
        raise ValueError("no route returned")
    s = routes[0].get("summary") or {}
    seconds = s.get("travelTimeInSeconds")
    if not seconds:
        raise ValueError("no travelTimeInSeconds")
    return {
        "seconds": int(seconds),
        "meters": int(s.get("lengthInMeters") or 0),
        "delay_seconds": int(s.get("trafficDelayInSeconds") or 0),
        "departure": s.get("departureTime"),
    }


def carry_forward():
    """Return True if an acceptable previous file was left in place."""
    try:
        st = os.stat(OUT)
        age = time.time() - st.st_mtime
        if age < MAX_AGE:
            print(f"carry-forward: keeping previous commute.json ({int(age)}s old)", flush=True)
            return True
    except OSError:
        pass
    print("no usable previous commute.json to carry forward", flush=True)
    return False


def main():
    key = load_key()
    if not key:
        print(f"no key at {KEY_FILE} — carrying forward (or board falls back to free-flow)", flush=True)
        carry_forward()
        return 1

    routes = {}
    errors = 0
    for name, lon, lat in DEST:
        try:
            routes[name] = fetch_route(key, name, lon, lat)
            d = routes[name]
            print(f"  {name}: {d['seconds'] // 60}m (+{d['delay_seconds'] // 60}m traffic)", flush=True)
        except (urllib.error.URLError, urllib.error.HTTPError, ValueError,
                KeyError, json.JSONDecodeError) as e:
            errors += 1
            routes[name] = None
            print(f"  {name}: FAILED ({e})", flush=True)
        time.sleep(0.2)

    ok = sum(1 for v in routes.values() if v)
    if ok == 0:
        print(f"all {len(DEST)} routes failed — carrying forward", flush=True)
        carry_forward()
        return 1

    payload = {
        "updated": int(time.time()),
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source": "tomtom-live-traffic",
        "routes": routes,
    }
    with open(TMP, "w") as fh:
        json.dump(payload, fh)
    os.replace(TMP, OUT)
    os.chmod(OUT, 0o644)
    print(f"commute.json written: {ok}/{len(DEST)} routes, {errors} errors", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
