#!/usr/bin/env python3
"""
Latverian Embassy Diplomatic Telemetry Relay (DOOM-NET/2.0)
Listens on port 8042.
Handles HELLO, AUTH, and QUERY requests with dynamic session salts.
"""
import os
import sys
import struct
import hmac
import hashlib
import secrets
import socketserver

MAGIC = b"DOOM"
VERSION = 2

MSG_HELLO_REQ  = 0x01
MSG_HELLO_RESP = 0x02
MSG_AUTH_REQ   = 0x03
MSG_AUTH_RESP  = 0x04
MSG_QUERY_REQ  = 0x05
MSG_QUERY_RESP = 0x06

SHARED_PSK = b"LATVERIA_DIPLOMATIC_CIPHER_1962"
CMD_ORBITAL_TELEMETRY = 0x1337

def calc_checksum(header_partial: bytes, payload: bytes) -> int:
    return sum(header_partial + payload) & 0xFFFF

def build_packet(msg_type: int, seq_num: int, payload: bytes) -> bytes:
    header_partial = struct.pack("!4sBBHH", MAGIC, VERSION, msg_type, seq_num, len(payload))
    csum = calc_checksum(header_partial, payload)
    return header_partial + struct.pack("!H", csum) + payload

def parse_packet(header_bytes: bytes, rfile):
    if len(header_bytes) < 12:
        return None, "Header too short"
    magic, ver, mtype, seq, plen, csum = struct.unpack("!4sBBHHH", header_bytes)
    if magic != MAGIC:
        return None, f"Invalid magic header: {magic}"
    if ver != VERSION:
        return None, f"Invalid version: {ver}"

    payload = rfile.read(plen)
    if len(payload) != plen:
        return None, "Truncated payload read"

    expected_csum = calc_checksum(header_bytes[:10], payload)
    if csum != expected_csum:
        return None, f"Checksum mismatch: expected {expected_csum}, got {csum}"

    return (mtype, seq, payload), None

class EmbassyRelayHandler(socketserver.StreamRequestHandler):
    def handle(self):
        self.request.settimeout(15.0)
        salt = secrets.token_bytes(8)
        authenticated = False
        seq = 0

        try:
            while True:
                header = self.rfile.read(12)
                if not header:
                    break

                pkt, err = parse_packet(header, self.rfile)
                if err:
                    print(f"[-] Client error: {err}")
                    break

                mtype, client_seq, payload = pkt
                seq += 1

                if mtype == MSG_HELLO_REQ:
                    # Client initiated session: respond with dynamic 8-byte challenge salt
                    resp = build_packet(MSG_HELLO_RESP, seq, salt)
                    self.wfile.write(resp)
                    self.wfile.flush()

                elif mtype == MSG_AUTH_REQ:
                    # Client must send HMAC-SHA256(salt, SHARED_PSK)
                    expected_mac = hmac.new(SHARED_PSK, salt, hashlib.sha256).digest()
                    if hmac.compare_digest(payload, expected_mac):
                        authenticated = True
                        resp = build_packet(MSG_AUTH_RESP, seq, b"\x00") # 0x00 = SUCCESS
                    else:
                        resp = build_packet(MSG_AUTH_RESP, seq, b"\x01") # 0x01 = AUTH_FAIL
                    self.wfile.write(resp)
                    self.wfile.flush()

                elif mtype == MSG_QUERY_REQ:
                    if not authenticated:
                        resp = build_packet(MSG_AUTH_RESP, seq, b"\xff") # FORBIDDEN
                        self.wfile.write(resp)
                        self.wfile.flush()
                        break

                    if len(payload) >= 2:
                        cmd_id = struct.unpack("!H", payload[:2])[0]
                        if cmd_id == CMD_ORBITAL_TELEMETRY:
                            flag = os.environ.get("FLAG", "YUVA{h4ck1ng_th3_l4tv3r14n_d1pl0m4t1c_w1r3_5183}")
                            secret_data = f"[DIPLOMATIC DISPATCH: TOP SECRET]\nORBITAL SATELLITE KEYS LOADED.\nPERIMETER ACCESS CODE: {flag}\n".encode()
                            resp = build_packet(MSG_QUERY_RESP, seq, secret_data)
                            self.wfile.write(resp)
                            self.wfile.flush()
                            break
                        else:
                            resp = build_packet(MSG_QUERY_RESP, seq, b"ERR: UNKNOWN COMMAND ID")
                            self.wfile.write(resp)
                            self.wfile.flush()
                else:
                    break
        except Exception as e:
            pass

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8042))
    server = ThreadedTCPServer(("0.0.0.0", port), EmbassyRelayHandler)
    print(f"[*] Latverian Embassy Relay listening on port {port}...")
    server.serve_forever()
