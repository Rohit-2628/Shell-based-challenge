#!/usr/bin/env python3
"""
Latveria Citadel - Sovereign Vault Controller (Stage 2)
Challenge ID: X05 - The Black Mirror
Internal HTTP service listening strictly on 127.0.0.1:8088 (ClusterIP only).

Validates Stage-2 authorization tickets derived from the internal SRP/1.0 protocol daemon
and retrieves the final flag from the isolated Sovereign Flag Service.
"""

import os
import sys
import json
import hmac
import hashlib
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

PORT = int(os.environ.get("VAULT_PORT", 8088))
FLAG_SERVICE_URL = os.environ.get("FLAG_SERVICE_URL", "http://127.0.0.1:8089")
INTERNAL_SECRET = os.environ.get("INTERNAL_FLAG_SECRET", "latveria_vault_secret_9941a8e2")
SHARED_SECRET = os.environ.get("SRP_SHARED_SECRET", "srp_mirror_secret_3948102847192048").encode()
NODE_ID = "NODE-4143"

def verify_ticket(ticket: str) -> bool:
    if not ticket or not ticket.startswith("SRP_AUTH_"):
        return False
    parts = ticket.split("_")
    # Expected format: SRP_AUTH_<NONCE>_<NODEID>_<SIG>
    if len(parts) < 5:
        return False
    nonce = parts[2]
    node = parts[3]
    sig = parts[4]

    expected_sig = hmac.new(SHARED_SECRET, f"{nonce.lower()}:{NODE_ID}".encode(), hashlib.sha256).hexdigest()[:24]
    if hmac.compare_digest(sig, expected_sig):
        return True
    
    # Also support uppercase nonce matching
    expected_sig_upper = hmac.new(SHARED_SECRET, f"{nonce}:{NODE_ID}".encode(), hashlib.sha256).hexdigest()[:24]
    if hmac.compare_digest(sig, expected_sig_upper):
        return True

    return False

def fetch_flag() -> str:
    try:
        req = urllib.request.Request(
            f"{FLAG_SERVICE_URL}/",
            headers={"X-Citadel-Internal-Auth": INTERNAL_SECRET}
        )
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("flag", "DOOM{error_fetching_flag}")
    except Exception as e:
        return f"YUVA{{flag_service_unavailable_{e}}}"

class VaultHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Quiet handler
        pass

    def send_json(self, status_code: int, data: dict):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("X-Citadel-Vault-Node", NODE_ID)
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode("utf-8"))

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/v1/vault/unlock":
            qs = parse_qs(parsed.query)
            ticket = qs.get("ticket", [""])[0]
            self.handle_unlock(ticket)
            return

        if parsed.path in ["/", "/api", "/api/v1/vault"]:
            self.send_json(403, {
                "status": "FORBIDDEN",
                "service": "Citadel Sovereign Vault Gateway (Stage 2)",
                "error": "Direct unauthenticated access prohibited.",
                "required_action": "Submit a valid SRP authorization ticket to POST /api/v1/vault/unlock with {'ticket': 'SRP_AUTH_...'}",
                "upstream_protocol": "Sovereign Reflection Protocol (SRP/1.0 on TCP/9099)"
            })
            return

        self.send_json(404, {"status": "NOT_FOUND", "error": f"Endpoint '{parsed.path}' does not exist."})

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/v1/vault/unlock":
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len).decode("utf-8", errors="replace")
            ticket = ""
            try:
                data = json.loads(body)
                ticket = data.get("ticket", "")
            except Exception:
                # Check form data or plain text
                if "ticket=" in body:
                    qs = parse_qs(body)
                    ticket = qs.get("ticket", [""])[0]
                else:
                    ticket = body.strip()

            self.handle_unlock(ticket)
            return

        self.send_json(404, {"status": "NOT_FOUND", "error": f"Endpoint '{parsed.path}' does not exist."})

    def handle_unlock(self, ticket: str):
        if not ticket:
            self.send_json(400, {
                "status": "BAD_REQUEST",
                "error": "Missing ticket parameter.",
                "hint": "Obtain ticket via SRP/1.0 daemon on 127.0.0.1:9099 ('NONCE' -> 'MIRROR <nonce> NODE-4143')"
            })
            return

        if not verify_ticket(ticket):
            self.send_json(401, {
                "status": "UNAUTHORIZED",
                "error": "Invalid or forged SRP authorization ticket.",
                "provided_ticket": ticket
            })
            return

        flag = fetch_flag()
        self.send_json(200, {
            "status": "AUTHORIZATION_GRANTED",
            "message": "Black Mirror core resonance synchronized. Sovereign Citadel vault unlocked.",
            "stage": "STAGE_2_COMPLETE",
            "vault_status": "DISARMED",
            "flag": flag
        })

def run_server():
    server_address = ("127.0.0.1", PORT)
    httpd = HTTPServer(server_address, VaultHandler)
    print(f"[*] Sovereign Vault Controller active on 127.0.0.1:{PORT}")
    httpd.serve_forever()

if __name__ == "__main__":
    run_server()
