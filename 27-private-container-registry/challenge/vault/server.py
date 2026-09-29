#!/usr/bin/env python3
"""
Latverian Orbital Defense Mesh — Internal Vault Service Daemon
Runs as isolated unprivileged user 'vault' on 127.0.0.1:8080.
Validates the historical credential recovered from the private container registry.
"""

import argparse
import json
import os
import sys
from http import HTTPStatus
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

# Expected authentic credentials from historical image layer v1.0.0
VALID_TOKEN = "latv_vault_sec_89f2a481c90e37b2d5140e678a119c8f"
VALID_CALLER = "orbital_defense_service_master"
VALID_ACTION = "OVERRIDE_DEFENSE_GRID"

# Known decoy tokens
DECOY_TOKENS = {
    "latv_test_auth_token_sample_non_functional": "Decoy test token from core-auth prototype rejected.",
    "latv_telemetry_dummy_debug_key_112": "Decoy telemetry key from telemetry-relay rejected.",
    "TEST_TOKEN": "Sample placeholder rejected.",
    "DEBUG_SECRET": "Debug placeholder rejected."
}

FLAG_FILE = Path("/opt/vault/flag.txt")

def get_flag() -> str:
    if FLAG_FILE.exists():
        try:
            return FLAG_FILE.read_text().strip()
        except Exception as e:
            sys.stderr.write(f"[!] Error reading flag file: {e}\n")
    return os.environ.get("FLAG", "YUVA{pr1v4t3_r3g1stry_l4y3r_3xf1ltr4t10n_9901}")

class VaultHandler(BaseHTTPRequestHandler):
    server_version = "Latveria-VaultDaemon/3.1.0"

    def log_message(self, format, *args):
        sys.stderr.write(f"[{self.log_date_time_string()}] [VAULT] {self.client_address[0]} {format % args}\n")
        sys.stderr.flush()

    def send_json(self, status_code: int, data: dict):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Server", self.server_version)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        if not path:
            path = "/"

        if path == "/" or path == "/healthz":
            self.send_json(HTTPStatus.OK, {
                "status": "ONLINE",
                "service": "Latveria Orbital Defense Vault Daemon",
                "version": "3.1.0-internal",
                "auth_required": True,
                "endpoints": {
                    "override": "/api/v1/vault/override",
                    "status": "/api/v1/vault/status"
                }
            })
            return

        if path == "/api/v1/vault/status":
            self.send_json(HTTPStatus.OK, {
                "mesh_status": "LOCKED",
                "defense_grid": "ACTIVE",
                "override_node": "DOOM-ORBITAL-ALPHA-01",
                "notice": "Authentication token required via /api/v1/vault/override."
            })
            return

        self.send_json(HTTPStatus.NOT_FOUND, {
            "status": "ERROR",
            "message": f"Endpoint '{path}' not recognized."
        })

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path != "/api/v1/vault/override":
            self.send_json(HTTPStatus.NOT_FOUND, {
                "status": "ERROR",
                "message": f"POST endpoint '{path}' not found."
            })
            return

        # Extract parameters from headers or JSON body
        token = self.headers.get("X-Latverian-Token") or self.headers.get("X-Internal-Token")
        caller = self.headers.get("X-Caller-ID")
        action = self.headers.get("X-Gateway-Action")

        # Check Authorization Bearer header
        auth_header = self.headers.get("Authorization", "")
        if not token and auth_header.startswith("Bearer "):
            token = auth_header[len("Bearer "):].strip()

        # Parse JSON body if present
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length > 0:
            try:
                body_bytes = self.rfile.read(content_length)
                body_json = json.loads(body_bytes.decode("utf-8"))
                if not token and "token" in body_json:
                    token = body_json["token"]
                if not token and "LATVERIAN_INTERNAL_TOKEN" in body_json:
                    token = body_json["LATVERIAN_INTERNAL_TOKEN"]
                if not caller and "caller" in body_json:
                    caller = body_json["caller"]
                if not caller and "LATVERIAN_CALLER_ID" in body_json:
                    caller = body_json["LATVERIAN_CALLER_ID"]
                if not action and "action" in body_json:
                    action = body_json["action"]
                if not action and "LATVERIAN_GATEWAY_ACTION" in body_json:
                    action = body_json["LATVERIAN_GATEWAY_ACTION"]
            except Exception:
                pass

        if not token:
            self.send_json(HTTPStatus.UNAUTHORIZED, {
                "status": "UNAUTHORIZED",
                "error": "MISSING_CREDENTIALS",
                "message": "Missing Latverian internal token. Header 'X-Latverian-Token' or Authorization Bearer required."
            })
            return

        # Check decoy tokens
        if token in DECOY_TOKENS:
            self.send_json(HTTPStatus.FORBIDDEN, {
                "status": "FORBIDDEN",
                "error": "DECOY_TOKEN_REJECTED",
                "message": DECOY_TOKENS[token]
            })
            return

        # Check genuine token
        if token != VALID_TOKEN:
            self.send_json(HTTPStatus.FORBIDDEN, {
                "status": "FORBIDDEN",
                "error": "INVALID_TOKEN",
                "message": "Provided token signature does not match Orbital Defense Mesh master key."
            })
            return

        # Success - unlock vault and return flag
        flag_val = get_flag()
        self.send_json(HTTPStatus.OK, {
            "status": "SUCCESS",
            "message": "Orbital Defense Vault unlocked. Master override authority verified.",
            "authorization": {
                "caller": caller or VALID_CALLER,
                "action": action or VALID_ACTION,
                "token_scope": "ORBITAL_DEFENSE_MASTER_LEVEL5",
                "verified": True
            },
            "grid_state": {
                "status": "OVERRIDDEN",
                "orbital_satellite": "LATVERIA-ORBITAL-SAT-01",
                "defense_protocol": "ZEPHYR-99",
                "lock_state": "DISENGAGED"
            },
            "flag": flag_val
        })

def run_vault_server(host="127.0.0.1", port=8080):
    server_address = (host, port)
    httpd = HTTPServer(server_address, VaultHandler)
    print(f"[*] Latveria Orbital Vault Service listening on http://{host}:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Shutting down vault service.")
        httpd.server_close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Latveria Orbital Vault Service")
    parser.add_argument("--host", default="127.0.0.1", help="Binding interface (internal only)")
    parser.add_argument("--port", type=int, default=8080, help="Port to listen on")
    args = parser.parse_args()
    
    run_vault_server(args.host, args.port)
