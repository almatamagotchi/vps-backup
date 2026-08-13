#!/usr/bin/env python3
import json, os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from datetime import datetime

RF = "/usr/local/www/alma/show/requests.json"

def rd():
    try:
        with open(RF) as f: return json.load(f)
    except: return []

def wr(d):
    os.makedirs(os.path.dirname(RF), exist_ok=True)
    with open(RF, "w") as f: json.dump(d, f, indent=2)

class H(BaseHTTPRequestHandler):
    def _j(self, d, s=200):
        b = json.dumps(d).encode()
        self.send_response(s)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)
    def do_OPTIONS(self): self._j({}, 204)
    def _m(self, p, *eps):
        for e in eps:
            if p == e or p == "/api" + e: return True
        return False
    def do_GET(self):
        p = urlparse(self.path).path
        if self._m(p, "/requests"): self._j(rd())
        else: self._j({"error": "not found"}, 404)
    def do_POST(self):
        p = urlparse(self.path).path
        if self._m(p, "/submit"):
            try:
                n = int(self.headers.get("Content-Length", 0))
                b = json.loads(self.rfile.read(n))
                t = b.get("request", "").strip()
                if not t:
                    self._j({"error": "empty request"}, 400)
                    return
                r = rd()
                r.append({"text": t, "time": datetime.now().strftime("%H:%M"), "rendered": False})
                wr(r)
                self._j({"ok": True, "count": len(r)})
            except json.JSONDecodeError: self._j({"error": "invalid json"}, 400)
            except Exception as e: self._j({"error": str(e)}, 500)
        else: self._j({"error": "not found"}, 404)
    def log_message(self, f, *a): print(f"[api] {a[0]} {a[1]} {a[2]}")

HTTPServer(("127.0.0.1", 8090), H).serve_forever()
