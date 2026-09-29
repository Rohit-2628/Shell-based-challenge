#!/usr/bin/env python3
"""
Latveria Core Security Vault Service (v2.5-enterprise)
Internal microservice deployed on isolated vault network.
Requires internal token authorization for flag release.
"""

import http.server
import json
import os
import sys

PORT = int(os.environ.get("PORT", "8443"))
AUTH_TOKEN = os.environ.get("VAULT_AUTH_TOKEN", "LV-VAULT-TOKEN-9c48e2a1b730f56d")
FLAG = os.environ.get("FLAG", "YUVA{d1nd_n3st3d_d0ck3r_d43m0n_p1v0t_x08_7f8e9a2b}")

class VaultHandler(http.server.BaseHTTPRequestHandler):
    def _send_json(self, status_code, data):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Server", "Latveria-Vault-Core/2.5-enterprise")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode("utf-8"))

    def do_GET(self):
        client_ip = self.client_address[0]
        
        if self.path in ["/", "/index.html"]:
            self._send_json(200, {
                "service": "Latveria Defense Grid - Core Security Vault",
                "version": "2.5-enterprise",
                "status": "active",
                "network_zone": "vault-internal-net",
                "documentation": "/api/v1/vault/status"
            })
        elif self.path == "/health":
            self._send_json(200, {"status": "healthy", "service": "latveria-vault-core"})
        elif self.path == "/api/v1/vault/status":
            self._send_json(200, {
                "vault_state": "sealed",
                "auth_mechanism": "token",
                "token_header": "X-Vault-Access-Token",
                "network_domain": "vault-internal-net",
                "endpoints": [
                    "/health",
                    "/api/v1/vault/status",
                    "/api/v1/vault/flag"
                ]
            })
        elif self.path == "/api/v1/vault/flag":
            token = self.headers.get("X-Vault-Access-Token")
            if not token:
                self._send_json(401, {
                    "error": "Unauthorized",
                    "message": "Missing 'X-Vault-Access-Token' header in request.",
                    "code": 401
                })
                return
            
            if token.strip() != AUTH_TOKEN.strip():
                self._send_json(403, {
                    "error": "Forbidden",
                    "message": "Invalid vault access token provided.",
                    "code": 403
                })
                return

            self._send_json(200, {
                "status": "unlocked",
                "flag": FLAG,
                "message": "Flag release authorized by Doom Inner Security Protocol.",
                "authorized_client": client_ip
            })
        else:
            self._send_json(404, {"error": "Not Found", "path": self.path})

    def log_message(self, format, *args):
        sys.stderr.write(f"[{self.log_date_time_string()}] {self.address_string()} - {format % args}\n")

if __name__ == "__main__":
    print(f"[*] Starting Latveria Vault Core on port {PORT}...")
    server = http.server.HTTPServer(("0.0.0.0", PORT), VaultHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
