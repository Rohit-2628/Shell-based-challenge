#!/usr/bin/env python3
"""
Latveria Tactical Defense Grid - Doombot C2 Server
Verifies Doombot activation nonces and issues mission directives.
"""
import os
import sys
import secrets
import socketserver

DOOM_KEY = b"LATVERIA_VICTOR!"
PERMUTATION_MAP = [7, 2, 15, 0, 11, 4, 13, 8, 1, 14, 3, 10, 5, 12, 9, 6]

def compute_signature(nonce_bytes: bytes) -> str:
    # Stage 1: Keyed Expansion & Bit-Twiddling
    expanded = bytearray(16)
    for i in range(8):
        b = nonce_bytes[i]
        expanded[2 * i] = ((b ^ DOOM_KEY[2 * i]) + 0x37) & 0xFF
        ror = ((b >> 3) | (b << 5)) & 0xFF
        expanded[2 * i + 1] = ror ^ DOOM_KEY[2 * i + 1]

    # Stage 2: Permutation mapping
    permuted = bytearray(16)
    for i in range(16):
        permuted[i] = expanded[PERMUTATION_MAP[i]]

    # Stage 3: Rolling CBC-like feedback transformation
    output_bytes = bytearray(16)
    output_bytes[0] = permuted[0] ^ 0x5D
    for i in range(1, 16):
        output_bytes[i] = ((permuted[i] + output_bytes[i - 1]) & 0xFF) ^ 0xAA

    return output_bytes.hex()

class DoombotC2Handler(socketserver.StreamRequestHandler):
    def handle(self):
        self.request.settimeout(15.0)
        try:
            self.wfile.write(b"============================================================\n")
            self.wfile.write(b" [*] LATVERIA TACTICAL DEFENSE GRID - DOOMBOT C2 v4.2\n")
            self.wfile.write(b" [*] CONNECTED COMMAND UNIT REGISTERED: RECON-9\n")
            self.wfile.write(b"============================================================\n")

            # Generate random 8-byte nonce (16 hex chars)
            nonce_bytes = secrets.token_bytes(8)
            nonce_hex = nonce_bytes.hex()
            expected_sig = compute_signature(nonce_bytes)

            self.wfile.write(f"[!] AUTHENTICATION CHALLENGE NONCE: {nonce_hex}\n".encode())
            self.wfile.write(b"[?] ENTER 32-HEX AUTHORIZATION RESPONSE: ")
            self.wfile.flush()

            line = self.rfile.readline().decode('utf-8', errors='ignore').strip()

            if line.lower() == expected_sig.lower():
                flag = os.environ.get("FLAG", "YUVA{v1ct0r_v0n_d00m_m4st3r_0f_sc13nc3_4nd_m4g1c_9902}")
                self.wfile.write(b"\n[+] ACCESS GRANTED. WELCOME, COMMANDER DOOMBOT.\n")
                self.wfile.write(f"[+] FLEET DEPLOYMENT DIRECTIVE: {flag}\n".encode())
            else:
                self.wfile.write(b"\n[-] AUTHENTICATION FAILED. Countermeasure armed.\n")
            self.wfile.flush()
        except Exception as e:
            pass

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 1338))
    server = ThreadedTCPServer(("0.0.0.0", port), DoombotC2Handler)
    print(f"[*] Doombot C2 Server listening on port {port}...")
    server.serve_forever()
