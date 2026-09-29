#!/usr/bin/env python3
"""
Automated solve script for Challenge 3: Embassy Wiretap Protocol
Performs dynamic DOOM-NET handshake, HMAC authentication, and telemetry query.
"""
import sys
import socket
import struct
import hmac
import hashlib

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

def recv_packet(s):
    hdr = s.recv(12)
    if len(hdr) < 12:
        raise RuntimeError("Truncated header")
    magic, ver, mtype, seq, plen, csum = struct.unpack("!4sBBHHH", hdr)
    payload = b""
    while len(payload) < plen:
        chunk = s.recv(plen - len(payload))
        if not chunk:
            break
        payload += chunk
    return mtype, seq, payload

def solve(host="127.0.0.1", port=8042):
    print(f"[*] Connecting to Latverian Embassy Relay at {host}:{port}...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))

    # Step 1: Send HELLO_REQ
    print("[*] Sending MSG_HELLO_REQ...")
    s.sendall(build_packet(MSG_HELLO_REQ, 1, b"INTRUDER_AGENT"))

    # Step 2: Receive HELLO_RESP
    mtype, seq, salt = recv_packet(s)
    if mtype != MSG_HELLO_RESP or len(salt) != 8:
        print(f"[-] Unexpected HELLO response: mtype={mtype}, salt={salt.hex()}")
        s.close()
        return None

    print(f"[+] Received Session Challenge Salt: {salt.hex()}")

    # Step 3: Compute HMAC and send AUTH_REQ
    auth_mac = hmac.new(SHARED_PSK, salt, hashlib.sha256).digest()
    print(f"[*] Authenticating with HMAC-SHA256 signature ({len(auth_mac)} bytes)...")
    s.sendall(build_packet(MSG_AUTH_REQ, 2, auth_mac))

    # Step 4: Verify AUTH_RESP
    mtype, seq, auth_res = recv_packet(s)
    if mtype != MSG_AUTH_RESP or auth_res != b"\x00":
        print(f"[-] Authentication failed: status={auth_res}")
        s.close()
        return None
    print("[+] Authentication SUCCESSFUL!")

    # Step 5: Send QUERY_REQ for CMD_ORBITAL_TELEMETRY
    print("[*] Querying record 0x1337 (ORBITAL_TELEMETRY)...")
    cmd_payload = struct.pack("!H", CMD_ORBITAL_TELEMETRY)
    s.sendall(build_packet(MSG_QUERY_REQ, 3, cmd_payload))

    # Step 6: Receive QUERY_RESP
    mtype, seq, secret_data = recv_packet(s)
    response_text = secret_data.decode('utf-8', errors='ignore')
    print(f"[+] Server Response:\n{response_text}")

    for line in response_text.splitlines():
        if "FLAG{" in line or "YUVA{" in line:
            print(f"[+] Captured Flag: {line.strip()}")
            s.close()
            return line.strip()

    s.close()
    return None

if __name__ == "__main__":
    h = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    p = int(sys.argv[2]) if len(sys.argv) > 2 else 8042
    solve(h, p)
