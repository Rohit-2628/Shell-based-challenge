#!/usr/bin/env python3
"""
Latveria Sovereign Defense Grid - Production Telemetry Dispatcher (Mock)
Internal Production Gateway Service (DOOM-PROD-GW-v4.2)
Protected by CI Release Trust Chain & HMAC-SHA256 Signatures.
"""

import os
import sys
import json
import time
import hmac
import hashlib
from http.server import HTTPServer, BaseHTTPRequestHandler

# Configuration & Secrets (Loaded inside production environment only)
PORT = int(os.environ.get("PROD_PORT", "8080"))
HOST = os.environ.get("PROD_HOST", "127.0.0.1")

# The expected CI credentials (must match what was committed in historical CI setup)
EXPECTED_SIGNING_KEY = os.environ.get("DOOM_CI_SIGNING_KEY", "latv_ci_sec_984f8a32b91c49e7b1a0d8f3319082ec")
EXPECTED_DEPLOY_TOKEN = os.environ.get("DOOM_DEPLOY_TOKEN", "DOOM_PROD_DEPLOY_TOKEN_v4.2.9812")
EXPECTED_CALLER_ID = os.environ.get("DOOM_CALLER_ID", "latveria_ci_agent_99")
EXPECTED_ACTION = "PROD_DISPATCH_RELEASE"

FLAG_FILE = os.environ.get("FLAG_PATH", "/opt/production/flag.txt")
DEFAULT_FLAG = "YUVA{c0mpr0m1s3d_d3v_h1st0ry_hm4c_auth_8821}"

def get_flag():
    if os.path.exists(FLAG_FILE):
        try:
            with open(FLAG_FILE, "r") as f:
                return f.read().strip()
        except Exception as e:
            sys.stderr.write(f"Error reading flag file: {e}\n")
    return os.environ.get("FLAG", DEFAULT_FLAG)


class ProductionHandler(BaseHTTPRequestHandler):
    server_version = "DoomProductionGateway/4.2"
    sys_version = ""

    def _send_json(self, status_code, data):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Doom-Node", "LATV-PROD-CORE-01")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            self._send_json(200, {
                "status": "HEALTHY",
                "service": "Latveria Sovereign Defense Grid - Telemetry Dispatcher",
                "version": "4.2.1-prod",
                "timestamp": int(time.time())
            })
            return

        if self.path in ["/", "/api/v1/info"]:
            self._send_json(200, {
                "system": "Latveria Sovereign Production Mesh",
                "subsystem": "Orbital Defense Telemetry Dispatch Gateway",
                "environment": "PRODUCTION",
                "status": "ARMED_AND_LOCKED",
                "auth_protocol": "LATVERIA_CI_HMAC_V2",
                "endpoints": {
                    "/health": "Service liveness probe (GET)",
                    "/api/v1/info": "Public node information (GET)",
                    "/api/v1/telemetry/deploy": "Authorized CI pipeline deployment & telemetry dispatch endpoint (POST)",
                    "/api/v1/vault/status": "Production vault verification endpoint (POST)"
                },
                "notice": "All deployment requests must be signed by authorized Doom CI pipeline release keys."
            })
            return

        self._send_json(404, {"error": "NOT_FOUND", "message": "The requested endpoint does not exist."})

    def do_POST(self):
        if self.path not in ["/api/v1/telemetry/deploy", "/api/v1/vault/status", "/api/v1/production/dispatch"]:
            self._send_json(404, {"error": "NOT_FOUND", "message": "Unknown dispatch endpoint."})
            return

        # 1. Read request headers
        deploy_token = self.headers.get("X-Doom-Deploy-Token")
        signature = self.headers.get("X-Doom-Signature")
        timestamp_header = self.headers.get("X-Doom-Timestamp")
        caller_id = self.headers.get("X-Doom-Caller")

        if not all([deploy_token, signature, timestamp_header, caller_id]):
            self._send_json(401, {
                "error": "MISSING_AUTHENTICATION_HEADERS",
                "message": "CI trust headers required: X-Doom-Deploy-Token, X-Doom-Signature, X-Doom-Timestamp, X-Doom-Caller",
                "status": "DENIED"
            })
            return

        # 2. Validate Timestamp (within 600s window to avoid replay / desync)
        try:
            req_time = int(timestamp_header)
            current_time = int(time.time())
            if abs(current_time - req_time) > 600:
                self._send_json(403, {
                    "error": "TIMESTAMP_OUT_OF_BOUNDS",
                    "message": f"Timestamp drift too large. Current server time: {current_time}, Received: {req_time}",
                    "status": "DENIED"
                })
                return
        except ValueError:
            self._send_json(400, {"error": "INVALID_TIMESTAMP", "message": "X-Doom-Timestamp must be an integer epoch."})
            return

        # 3. Validate Deploy Token & Caller ID
        if deploy_token != EXPECTED_DEPLOY_TOKEN:
            self._send_json(403, {
                "error": "INVALID_DEPLOY_TOKEN",
                "message": "The supplied deploy token is revoked or invalid for production stage.",
                "status": "DENIED"
            })
            return

        if caller_id != EXPECTED_CALLER_ID:
            self._send_json(403, {
                "error": "UNAUTHORIZED_CALLER",
                "message": f"Caller '{caller_id}' is not an authorized CI pipeline agent.",
                "status": "DENIED"
            })
            return

        # 4. Parse payload
        content_len = int(self.headers.get("Content-Length", 0))
        body_bytes = self.rfile.read(content_len) if content_len > 0 else b"{}"
        try:
            payload = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
        except Exception:
            payload = {}

        action = payload.get("action", EXPECTED_ACTION)

        # 5. Verify HMAC-SHA256 signature
        # Formula: hmac_sha256(key, f"{caller}:{timestamp}:{action}:{token}")
        signing_data = f"{caller_id}:{timestamp_header}:{action}:{deploy_token}".encode("utf-8")
        expected_sig = hmac.new(EXPECTED_SIGNING_KEY.encode("utf-8"), signing_data, hashlib.sha256).hexdigest()

        if not hmac.compare_digest(signature.lower(), expected_sig.lower()):
            self._send_json(403, {
                "error": "SIGNATURE_VERIFICATION_FAILED",
                "message": "HMAC-SHA256 signature validation failed. Release key invalid.",
                "status": "DENIED"
            })
            return

        # 6. Success! CI trust chain validated -> Return Flag
        flag_val = get_flag()
        self._send_json(200, {
            "status": "SUCCESS",
            "message": "CI trust chain verified. Production telemetry dispatch mesh unlocked.",
            "authorization": {
                "caller": caller_id,
                "action": action,
                "token_id": "TOKEN-LATV-RELEASE-V4",
                "pipeline_verified": True
            },
            "dispatch_result": {
                "target": payload.get("target", "orbital-defense-node-01"),
                "state": "DEPLOYED",
                "telemetry_stream": "ACTIVE"
            },
            "flag": flag_val
        })

    def log_message(self, format, *args):
        # Keep internal logs clean
        sys.stderr.write(f"[PROD-GW] {self.address_string()} - {format % args}\n")


def main():
    print(f"[*] Starting Latveria Sovereign Production Mock on {HOST}:{PORT}...")
    server = HTTPServer((HOST, PORT), ProductionHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
