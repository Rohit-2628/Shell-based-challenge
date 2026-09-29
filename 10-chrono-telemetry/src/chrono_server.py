#!/usr/bin/env python3
"""
Chrono-Telemetry Stream: Binary Protocol Daemon
Exposes TCP port 8043.
"""
import os
import sys
import zlib
import struct
import socketserver

PORT = 8043
DEFAULT_FLAG = "YUVA{z3r0_c0py_t3l3m3try_r3fl3ct10n_d00m_c0r3_8492}"
FLAG = os.environ.get("FLAG", DEFAULT_FLAG)

MAGIC = b"CHRN"
VERSION = 0x0301

TYPE_TELEMETRY   = 0x0001
TYPE_DIAGNOSTICS = 0x0002
TYPE_HEARTBEAT   = 0x0003
TYPE_ADMIN_CMD   = 0x00A0
TYPE_RESPONSE    = 0x00FF

CMD_DRAIN_CORE   = 0x1337

# Active Dynamic Admin Token (16 bytes)
ADMIN_TOKEN = os.environ.get("CHRONO_ADMIN_TOKEN", "DOOM_CHRONO_8941").encode("utf-8").ljust(16, b"_")[:16]

# Internal Session Buffer layout (32 bytes):
# [0..15]: System Header b"LATV_CHRN_SYS31!"
# [16..31]: ADMIN_TOKEN
INTERNAL_SESSION_BUFFER = b"LATV_CHRN_SYS31!" + ADMIN_TOKEN

def pack_packet(type_id, payload):
    crc = zlib.crc32(payload) & 0xFFFFFFFF
    header = struct.pack(">4sHHI I", MAGIC, VERSION, type_id, len(payload), crc)
    return header + payload

def parse_header(header_bytes):
    if len(header_bytes) < 16:
        return None
    magic, ver, type_id, plen, crc = struct.unpack(">4sHHI I", header_bytes)
    if magic != MAGIC or ver != VERSION:
        return None
    return type_id, plen, crc

class ChronoHandler(socketserver.StreamRequestHandler):
    def handle(self):
        try:
            print(f"[*] Connection from {self.client_address}")
            while True:
                header_bytes = self.rfile.read(16)
                if not header_bytes or len(header_bytes) < 16:
                    break

                res = parse_header(header_bytes)
                if not res:
                    break
                type_id, plen, expected_crc = res

                payload = self.rfile.read(plen)
                if len(payload) != plen:
                    break

                calc_crc = zlib.crc32(payload) & 0xFFFFFFFF
                if calc_crc != expected_crc:
                    err_resp = pack_packet(TYPE_RESPONSE, b"[-] CRC32 Verification Failed\n")
                    self.wfile.write(err_resp)
                    self.wfile.flush()
                    continue

                # Process by Type
                if type_id == TYPE_HEARTBEAT:
                    resp = pack_packet(TYPE_RESPONSE, b"[+] CHRONO-CORE STABLE: UPTIME=481290s STATUS=NOMINAL\n")
                    self.wfile.write(resp)
                    self.wfile.flush()

                elif type_id == TYPE_DIAGNOSTICS:
                    if len(payload) < 8:
                        continue
                    query_id, reflection_flag = struct.unpack(">II", payload[:8])
                    
                    # Polymorphic zero-copy buffer reflection flaw
                    if reflection_flag & 0x80000000:
                        offset = reflection_flag & 0x7FFFFFFF
                        if offset + 16 <= len(INTERNAL_SESSION_BUFFER):
                            leaked = INTERNAL_SESSION_BUFFER[offset:offset+16]
                        else:
                            leaked = b"\x00" * 16
                        resp_data = struct.pack(">II", query_id, 0) + leaked
                        resp = pack_packet(TYPE_RESPONSE, resp_data)
                    else:
                        resp_data = struct.pack(">II", query_id, 0x01) + b"SYSTEM_HEALTHY_FLUX_OPTIMAL_CORE_300K"
                        resp = pack_packet(TYPE_RESPONSE, resp_data)
                    self.wfile.write(resp)
                    self.wfile.flush()

                elif type_id == TYPE_ADMIN_CMD:
                    if len(payload) < 24:
                        self.wfile.write(pack_packet(TYPE_RESPONSE, b"[-] Truncated Admin Capsule\n"))
                        self.wfile.flush()
                        continue

                    token = payload[:16]
                    cmd_id, param_len = struct.unpack(">II", payload[16:24])

                    if token == ADMIN_TOKEN:
                        if cmd_id == CMD_DRAIN_CORE:
                            success_msg = (
                                f"[+] ADMINISTRATIVE TOKEN VERIFIED: MASTER DOOM AUTHENTICATED.\n"
                                f"[+] EXECUTING COMMAND: CHRONO_DRAIN_CORE (0x1337)...\n"
                                f"[+] TEMPORAL STABILIZER COLD PURGE INITIATED. CORE COLLAPSED.\n"
                                f"[+] MASTER FLAG: {FLAG}\n"
                            ).encode("utf-8")
                            self.wfile.write(pack_packet(TYPE_RESPONSE, success_msg))
                            self.wfile.flush()
                            break
                        else:
                            self.wfile.write(pack_packet(TYPE_RESPONSE, b"[-] Unknown Command ID\n"))
                            self.wfile.flush()
                    else:
                        self.wfile.write(pack_packet(TYPE_RESPONSE, b"[-] ACCESS DENIED: Invalid Admin Token\n"))
                        self.wfile.flush()

        except Exception as e:
            pass

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True

if __name__ == "__main__":
    print(f"[*] Starting Chrono-Telemetry Server on port {PORT}...")
    server = ThreadedTCPServer(("0.0.0.0", PORT), ChronoHandler)
    server.serve_forever()
