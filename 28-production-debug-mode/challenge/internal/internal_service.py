#!/usr/bin/env python3
"""
Latveria Internal Executive Core Service
Listens privately on 127.0.0.1:8081 (ClusterIP only).
Provides executive command processing and secure flag retrieval for authenticated debug dispatch.
"""

import argparse
import json
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler

REQUIRED_AUTH_TOKEN = "latveria_dbg_admin_8b91a742cd3f"
REQUIRED_ACTION = "query_executive_core"
REQUIRED_TARGET = "sentinel_core_01"

FLAG_FILE_PATH = "/opt/vault/flag.txt"


def get_flag():
    if os.path.exists(FLAG_FILE_PATH):
        try:
            with open(FLAG_FILE_PATH, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception as e:
            return f"ERROR_READING_FLAG: {e}"
    return os.environ.get("FLAG", "YUVA{pr0duct10n_d3bug_d1sc10sur3_p1v0t_7c2b91ea}")


class InternalNexusHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Suppress noisy standard logs or output structured logs
        sys.stderr.write(f"[InternalNexus] {self.address_string()} - - [{self.log_date_time_string()}] {format % args}\n")

    def send_json(self, status_code: int, data: dict):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Internal-Service", "latveria-internal-core-v2")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            self.send_json(200, {
                "status": "UP",
                "service": "latveria-internal-core",
                "cluster_scope": "private-cluster-ip-only"
            })
        else:
            self.send_json(404, {"status": "error", "message": "Endpoint not found"})

    def do_POST(self):
        if self.path == "/api/v2/nexus/executive/control":
            auth_header = self.headers.get("X-Latveria-Debug-Token", "")
            
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length > 0:
                raw_body = self.rfile.read(content_length).decode("utf-8", errors="ignore")
                try:
                    body = json.loads(raw_body)
                except json.JSONDecodeError:
                    self.send_json(400, {"status": "error", "message": "Malformed JSON payload"})
                    return
            else:
                body = {}

            token = auth_header or body.get("auth_token", "")
            if token != REQUIRED_AUTH_TOKEN:
                self.send_json(403, {
                    "status": "forbidden",
                    "error": "AccessDenied",
                    "message": "Invalid or missing executive debug authorization token"
                })
                return

            action = body.get("action", "")
            target = body.get("target", "")

            if action != REQUIRED_ACTION or target != REQUIRED_TARGET:
                self.send_json(400, {
                    "status": "error",
                    "error": "InvalidCommandSpecification",
                    "message": f"Expected action='{REQUIRED_ACTION}' and target='{REQUIRED_TARGET}', received action='{action}' target='{target}'"
                })
                return

            # Clearance verified - return executive core response with dynamic flag
            flag = get_flag()
            self.send_json(200, {
                "status": "success",
                "message": "Executive Core Override Acknowledged. Security clearance verified.",
                "core_id": target,
                "system_state": "ACTIVE_OVERRIDE",
                "telemetry_stream": "LATVERIA_HIGH_ORBIT_GRID_SYNC",
                "flag": flag
            })
        else:
            self.send_json(404, {"status": "error", "message": "Unknown internal endpoint"})


def main():
    parser = argparse.ArgumentParser(description="Latveria Internal Executive Core Service")
    parser.add_argument("--host", default="127.0.0.1", help="Host interface (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8081, help="Port (default: 8081)")
    args = parser.parse_args()

    server = HTTPServer((args.host, args.port), InternalNexusHandler)
    print(f"[*] Latveria Internal Executive Core listening on http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
