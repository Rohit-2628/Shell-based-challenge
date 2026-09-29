#!/usr/bin/env python3
"""
Latveria Edge API Gateway (v1.1)
Frontend API router connecting frontend pipeline to microservice mesh.
"""

import http.server
import json
import os
import sys

PORT = int(os.environ.get("PORT", "8080"))
BACKEND_TARGET = os.environ.get("VAULT_SERVICE_DISCOVERY", "latveria-vault-core.vault-internal-net:8443")

class GatewayHandler(http.server.BaseHTTPRequestHandler):
    def _send_json(self, status_code, data):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Server", "Latveria-API-Gateway/1.1")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode("utf-8"))

    def do_GET(self):
        if self.path in ["/", "/index.html"]:
            self._send_json(200, {
                "service": "Latveria Edge API Gateway",
                "version": "1.1",
                "routes": {
                    "/health": "Gateway health status",
                    "/routes": "Microservice routing topology",
                    "/proxy/vault": "Vault proxy endpoint (Isolated - direct mesh access restricted)"
                }
            })
        elif self.path == "/health":
            self._send_json(200, {"status": "ok", "gateway": "latveria-api-gateway"})
        elif self.path == "/routes":
            self._send_json(200, {
                "mesh_topology": {
                    "frontend_network": "ci-frontend-net (172.28.10.0/24)",
                    "isolated_network": "vault-internal-net (172.28.20.0/24)",
                    "target_service": BACKEND_TARGET,
                    "access_policy": "Direct peer connection required on vault-internal-net"
                }
            })
        else:
            self._send_json(404, {"error": "Route Not Found", "path": self.path})

    def log_message(self, format, *args):
        sys.stderr.write(f"[{self.log_date_time_string()}] {self.address_string()} - {format % args}\n")

if __name__ == "__main__":
    print(f"[*] Starting Latveria API Gateway on port {PORT}...")
    server = http.server.HTTPServer(("0.0.0.0", PORT), GatewayHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
