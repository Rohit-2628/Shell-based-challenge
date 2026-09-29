#!/usr/bin/env python3
"""
Darkhold VM Network Daemon
Hosts the arcane verification service on TCP port 1340.
"""
import os
import sys
import socketserver
import subprocess

PORT = 1340
DEFAULT_FLAG = "YUVA{d4rkh0ld_4lcamy_v1rtu4l_m4ch1n3_3821}"
FLAG = os.environ.get("FLAG", DEFAULT_FLAG)
BYTECODE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sigil.enc")
VM_BIN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "darkhold_vm")

BANNER = r"""
╔════════════════════════════════════════════════════════════════════════════════╗
║             DARKHOLD ARCANE COMPUTATION ENGINE // LATVERIA OCCULT CORE        ║
║                    SUB-QUANTUM TALISMAN DISPATCH INTERFACE                     ║
╚════════════════════════════════════════════════════════════════════════════════╝
[!] The Sanctum of the Dread Lord Doom requires the consecrated Talisman Sigil.
[!] Handout binaries: 'darkhold_vm' and 'sigil.enc'
[!] Enter 24-character Astral Sigil (format: SIGIL{...}):
> """

class DarkholdTCPHandler(socketserver.StreamRequestHandler):
    def handle(self):
        try:
            self.wfile.write(BANNER.encode("utf-8"))
            self.wfile.flush()
            
            line = self.rfile.readline().decode("utf-8", errors="ignore").strip()
            if not line:
                return

            # Invoke local VM binary for verification
            res = subprocess.run([VM_BIN, BYTECODE_PATH, line], capture_output=True, text=True, timeout=5)
            if res.returncode == 0 and "ACCESS GRANTED" in res.stdout:
                self.wfile.write(b"\n[+] TALISMAN RESONANCE ACHIEVED! ACCESS GRANTED.\n")
                self.wfile.write(f"[+] SUB-VAULT UNLOCKED! FLAG: {FLAG}\n\n".encode("utf-8"))
            else:
                self.wfile.write(b"\n[-] ALCHEMICAL DIVERGENCE: SIGIL REJECTED BY DARKHOLD CORE.\n")
                self.wfile.write(b"[-] NEUROTOXIN CANISTERS CHARGING. DISCONNECTING.\n\n")
            self.wfile.flush()
        except Exception as e:
            pass

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True

if __name__ == "__main__":
    print(f"[*] Starting Darkhold VM Daemon on port {PORT}...")
    server = ThreadedTCPServer(("0.0.0.0", PORT), DarkholdTCPHandler)
    server.serve_forever()
