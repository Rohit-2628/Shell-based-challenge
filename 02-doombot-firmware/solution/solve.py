#!/usr/bin/env python3
"""
Automated solve script for Challenge 2: Doombot Firmware Link
Connects to C2 node, parses nonce, computes signature, and retrieves the flag.
"""
import sys
import socket
import re

DOOM_KEY = b"LATVERIA_VICTOR!"
PERMUTATION_MAP = [7, 2, 15, 0, 11, 4, 13, 8, 1, 14, 3, 10, 5, 12, 9, 6]

def compute_signature(nonce_bytes: bytes) -> str:
    expanded = bytearray(16)
    for i in range(8):
        b = nonce_bytes[i]
        expanded[2 * i] = ((b ^ DOOM_KEY[2 * i]) + 0x37) & 0xFF
        ror = ((b >> 3) | (b << 5)) & 0xFF
        expanded[2 * i + 1] = ror ^ DOOM_KEY[2 * i + 1]

    permuted = bytearray(16)
    for i in range(16):
        permuted[i] = expanded[PERMUTATION_MAP[i]]

    output_bytes = bytearray(16)
    output_bytes[0] = permuted[0] ^ 0x5D
    for i in range(1, 16):
        output_bytes[i] = ((permuted[i] + output_bytes[i - 1]) & 0xFF) ^ 0xAA

    return output_bytes.hex()

def solve(host="127.0.0.1", port=1338):
    print(f"[*] Connecting to Doombot C2 at {host}:{port}...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))

    banner = ""
    while "RESPONSE:" not in banner:
        chunk = s.recv(1024).decode('utf-8', errors='ignore')
        if not chunk:
            break
        banner += chunk

    print(banner, end="")

    match = re.search(r"NONCE:\s*([0-9a-fA-F]{16})", banner)
    if not match:
        print("[-] Failed to find nonce in banner.")
        s.close()
        return None

    nonce_hex = match.group(1)
    print(f"\n[+] Extracted Nonce: {nonce_hex}")

    nonce_bytes = bytes.fromhex(nonce_hex)
    response_sig = compute_signature(nonce_bytes)
    print(f"[+] Computed Authorization Signature: {response_sig}")

    s.sendall(response_sig.encode() + b"\n")

    result = ""
    while True:
        chunk = s.recv(1024).decode('utf-8', errors='ignore')
        if not chunk:
            break
        result += chunk
        if "FLAG{" in result or "YUVA{" in result:
            break

    print(result)

    for line in result.splitlines():
        if "FLAG{" in line or "YUVA{" in line:
            print(f"[+] Solved! Flag: {line.strip()}")
            s.close()
            return line.strip()

    s.close()
    return None

if __name__ == "__main__":
    h = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    p = int(sys.argv[2]) if len(sys.argv) > 2 else 1338
    solve(h, p)
