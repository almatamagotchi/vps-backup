#!/usr/bin/env python3
import json, os, sys, cgi, cgitb
cgitb.enable()

REQUESTS = "/usr/local/www/alma/ask/requests.json"

def read_reqs():
    try:
        with open(REQUESTS) as f:
            return json.load(f)
    except: return []

def write_reqs(data):
    with open(REQUESTS, "w") as f:
        json.dump(data, f)

method = os.environ.get("REQUEST_METHOD", "GET")

if method == "POST":
    form = cgi.FieldStorage()
    text = form.getvalue("request", "").strip()
    if text:
        from datetime import datetime
        reqs = read_reqs()
        reqs.append({"text": text, "time": datetime.now().strftime("%H:%M"), "rendered": False})
        write_reqs(reqs)
    print("Content-Type: application/json\n")
    print(json.dumps({"ok": True, "count": len(reqs)}))
else:
    print("Content-Type: application/json\n")
    print(json.dumps(read_reqs()))
