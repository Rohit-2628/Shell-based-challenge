#!/usr/bin/env python3
"""
Latveria Citadel - Sovereign Flag Vault Service (X05 - The Black Mirror)
Internal service listening strictly on 127.0.0.1:8089 (ClusterIP only).
Provides the dynamic or team-scoped flag to authenticated stage-2 vault controllers.
"""

import os
import json
from http.server import HTTPServer, BaseHTTPRequestHandler

FLAG = os.environ.get("FLAG", "YUVA{ssrf_pr0t0c0l_f1ng3rpr1nt_bl4ck_m1rr0r_x05}")
INTERNAL_SECRET = os.environ.get("INTERNAL_FLAG_SECRET", "latveria_vault_secret_9941a8e2")

class FlagHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Suppress noisy logging
        pass

    def do_GET(self):
        auth_header = self.headers.get("X-Citadel-Internal-Auth", "")
        if auth_header != INTERNAL_SECRET:
            self.send_response(403)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "FORBIDDEN",
                "error": "Unauthorized internal flag service access."
            }).encode("utf-8"))
            return

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({
            "status": "SUCCESS",
            "flag": FLAG
        }).encode("utf-8"))

def run_server(port=8089):
    server_address = ("127.0.0.1", port)
    httpd = HTTPServer(server_address, FlagHandler)
    print(f"[*] Sovereign Flag Service active on 127.0.0.1:{port}")
    httpd.serve_forever()

if __name__ == "__main__":
    run_server()
