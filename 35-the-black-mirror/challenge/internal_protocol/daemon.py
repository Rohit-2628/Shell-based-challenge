#!/usr/bin/env python3
"""
Latveria Citadel - Sovereign Reflection Protocol Daemon (SRP/1.0)
Challenge ID: X05 - The Black Mirror
Internal non-HTTP service listening strictly on 127.0.0.1:9099 (ClusterIP only).

Protocol Specification (SRP/1.0):
- Line-based TCP protocol terminated with CRLF (\r\n) or LF (\n).
- Connection Banner: +OK BLACK_MIRROR_CORE v1.0.4 READY (SRP/1.0 LATVERIA-INTERNAL NODE-4143; TYPE 'HELP')
- Supported Commands:
  - HELP                           : Print available commands
  - PING                           : Returns +PONG BLACK_MIRROR_CORE_ACTIVE
  - STATUS                         : Returns node state, ID (NODE-4143), and next-stage gateway endpoint
  - NONCE                          : Generates a temporary cryptographic reflection nonce
  - MIRROR <nonce> <node_id>       : Validates nonce & node_id, returns stage-2 vault authorization ticket
  - QUIT                           : Disconnects
- Error Responses:
  - -ERR PROTOCOL_ERROR: ... (on HTTP framing / unrecognized tokens)
  - -ERR INVALID_NODE: ...
  - -ERR INVALID_NONCE: ...
"""

import os
import sys
import time
import hmac
import hashlib
import socket
import threading
from typing import Dict

NODE_ID = "NODE-4143"
SHARED_SECRET = os.environ.get("SRP_SHARED_SECRET", "srp_mirror_secret_3948102847192048").encode()
NONCE_EXPIRY_SECONDS = 300
ACTIVE_NONCES: Dict[str, float] = {}
NONCE_LOCK = threading.Lock()

def generate_nonce() -> str:
    seed = f"{time.time()}:{os.urandom(8).hex()}".encode()
    nonce = hashlib.sha256(seed).hexdigest()[:16]
    with NONCE_LOCK:
        # Clean expired nonces
        now = time.time()
        expired = [k for k, v in ACTIVE_NONCES.items() if now - v > NONCE_EXPIRY_SECONDS]
        for k in expired:
            del ACTIVE_NONCES[k]
        ACTIVE_NONCES[nonce] = now
    return nonce

def is_valid_nonce(nonce: str) -> bool:
    with NONCE_LOCK:
        now = time.time()
        if nonce in ACTIVE_NONCES:
            if now - ACTIVE_NONCES[nonce] <= NONCE_EXPIRY_SECONDS:
                return True
            else:
                del ACTIVE_NONCES[nonce]
    # Also accept deterministic static test nonces for automated test harnesses
    if nonce == "TEST_NONCE_0001":
        return True
    return False

def compute_ticket(nonce: str, node_id: str) -> str:
    sig = hmac.new(SHARED_SECRET, f"{nonce}:{node_id.upper()}".encode(), hashlib.sha256).hexdigest()[:24]
    return f"SRP_AUTH_{nonce.upper()}_{node_id.upper().replace('-', '')}_{sig}"

class ClientHandler(threading.Thread):
    def __init__(self, client_sock: socket.socket, client_addr):
        super().__init__(daemon=True)
        self.sock = client_sock
        self.addr = client_addr

    def run(self):
        self.sock.settimeout(10.0)
        try:
            # 1. Send connection greeting banner
            greeting = f"+OK BLACK_MIRROR_CORE v1.0.4 READY (SRP/1.0 LATVERIA-INTERNAL {NODE_ID}; TYPE 'HELP')\r\n"
            self.sock.sendall(greeting.encode("utf-8"))

            buffer = b""
            while True:
                chunk = self.sock.recv(4096)
                if not chunk:
                    break
                buffer += chunk

                if len(buffer) > 8192:
                    self.sock.sendall(b"-ERR PAYLOAD_TOO_LARGE: Maximum request length exceeded.\r\n")
                    break

                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    line_str = line.decode("utf-8", errors="replace").strip("\r")
                    if not line_str:
                        continue

                    response, should_close = self.process_command(line_str)
                    self.sock.sendall(response.encode("utf-8"))
                    if should_close:
                        return
        except (socket.timeout, ConnectionResetError, BrokenPipeError):
            pass
        except Exception as e:
            try:
                self.sock.sendall(f"-ERR INTERNAL_ERROR: {str(e)}\r\n".encode("utf-8"))
            except Exception:
                pass
        finally:
            try:
                self.sock.close()
            except Exception:
                pass

    def process_command(self, line: str) -> (str, bool):
        parts = line.strip().split()
        if not parts:
            return "-ERR EMPTY_COMMAND\r\n", False

        cmd = parts[0].upper()

        # Check for HTTP framing attempts (GET, POST, HEAD, PUT, OPTIONS, etc.)
        if cmd in ["GET", "POST", "HEAD", "PUT", "DELETE", "OPTIONS", "CONNECT", "TRACE", "PATCH", "HTTP/1.1", "HTTP/1.0"]:
            return (
                "-ERR PROTOCOL_ERROR: HTTP framing detected. HTTP is not supported on port 9099.\r\n"
                "-ERR HINT: Sovereign Reflection Protocol (SRP/1.0) required. Send 'HELP' or 'STATUS'.\r\n",
                False
            )

        if cmd == "HELP" or cmd == "?":
            return (
                "+OK SRP/1.0 COMMANDS:\r\n"
                "  STATUS                           - Query mirror node state and vault gateway\r\n"
                "  NONCE                            - Issue reflection session nonce\r\n"
                "  MIRROR <nonce> <node_id>         - Generate stage-2 vault authorization ticket\r\n"
                "  PING                             - Heartbeat probe\r\n"
                "  QUIT                             - Disconnect\r\n",
                False
            )

        if cmd == "PING":
            return "+PONG BLACK_MIRROR_CORE_ACTIVE\r\n", False

        if cmd == "STATUS":
            return (
                f"+OK STATUS: NODE={NODE_ID} STATE=ACTIVE PROTOCOL=SRP/1.0 "
                f"VAULT_GATEWAY=http://127.0.0.1:8088/api/v1/vault/unlock MAX_SESSIONS=10\r\n",
                False
            )

        if cmd == "NONCE":
            nonce = generate_nonce()
            return f"+OK NONCE: {nonce}\r\n", False

        if cmd == "MIRROR":
            if len(parts) < 3:
                return "-ERR SYNTAX_ERROR: Usage: MIRROR <nonce> <node_id>\r\n", False
            nonce = parts[1]
            node = parts[2].upper()

            if node != NODE_ID and node != "0X4143":
                return f"-ERR INVALID_NODE: Node ID '{node}' mismatch. Expected active node identifier from STATUS (e.g. {NODE_ID}).\r\n", False

            if not is_valid_nonce(nonce):
                return "-ERR INVALID_NONCE: Nonce expired or invalid. Request a new token with 'NONCE'.\r\n", False

            ticket = compute_ticket(nonce, NODE_ID)
            return f"+OK MIRROR_AUTH_TICKET: {ticket}\r\n", False

        if cmd == "QUIT" or cmd == "EXIT":
            return "+OK BYE\r\n", True

        return f"-ERR UNKNOWN_COMMAND: Unrecognized command '{parts[0]}'. Send 'HELP' for SRP/1.0 syntax.\r\n", False


def run_daemon(port=9099):
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind(("127.0.0.1", port))
    server_sock.listen(15)
    print(f"[*] Sovereign Reflection Protocol Daemon (SRP/1.0) listening on 127.0.0.1:{port}")

    while True:
        try:
            client_sock, client_addr = server_sock.accept()
            handler = ClientHandler(client_sock, client_addr)
            handler.start()
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"[!] Accept error: {e}", file=sys.stderr)

if __name__ == "__main__":
    port = int(os.environ.get("SRP_PORT", 9099))
    run_daemon(port)
