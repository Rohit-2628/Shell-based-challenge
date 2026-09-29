#!/usr/bin/env python3
"""
The Golem's Seal: Post-Quantum Lattice Authentication Daemon
Runs on TCP port 1341.
"""
import os
import sys
import json
import random
import socketserver

PORT = 1341
DEFAULT_FLAG = "YUVA{p0st_qu4ntum_l4tt1c3_g0l3m_d1s4rm3d_5829}"
FLAG = os.environ.get("FLAG", DEFAULT_FLAG)

N = 8
Q = 257

# Fixed secret signing polynomial for the Golem legion
# Generated once per server startup or fixed dynamic seed
SECRET_S = [1, -1, 0, -1, 1, 0, -1, 1]

def poly_mul(a, b):
    res = [0] * N
    for i in range(N):
        for j in range(N):
            deg = i + j
            coeff = a[i] * b[j]
            if deg >= N:
                res[deg - N] = (res[deg - N] - coeff) % Q
            else:
                res[deg] = (res[deg] + coeff) % Q
    return [x % Q for x in res]

BANNER = r"""
╔════════════════════════════════════════════════════════════════════════════════╗
║             GOLEM BASTION // POST-QUANTUM LATTICE AUTHENTICATION               ║
║                     POLYNOMIAL RING R_q = Z_257[x]/(x^8 + 1)                   ║
╚════════════════════════════════════════════════════════════════════════════════╝
[!] The Sovereign Golems of Latveria guard the Sub-Quantum Collider.
[!] Protocol: Lyubashevsky-Fiat-Shamir Identification with Aborts.
[!] Commands:
    1: Intercept Golem Patrol Identification Transcript
    2: Issue Administrative Disarm Command
    3: Disconnect
"""

class GolemHandler(socketserver.StreamRequestHandler):
    def handle(self):
        try:
            self.wfile.write(BANNER.encode("utf-8"))
            self.wfile.flush()

            while True:
                self.wfile.write(b"\nSelect Command (1-3): ")
                self.wfile.flush()
                choice = self.rfile.readline().decode("utf-8", errors="ignore").strip()

                if choice == "1":
                    # Prover generates transcript
                    # Flawed PRNG: y_i drawn from [0, 4] instead of [-B, B]
                    c = [random.choice([0, 1]) for _ in range(N)]
                    y = [random.randint(0, 4) for _ in range(N)]
                    cs = poly_mul(c, SECRET_S)
                    z = [(y[i] + cs[i]) % Q for i in range(N)]
                    
                    data = {"challenge_c": c, "response_z": z}
                    self.wfile.write(f"[+] INTERCEPTED TRANSCRIPT:\n{json.dumps(data)}\n".encode("utf-8"))
                    self.wfile.flush()

                elif choice == "2":
                    self.wfile.write(b"\n[*] INITIATING ADMINISTRATIVE OVERRIDE PROTOCOL...\n")
                    chal = [random.choice([0, 1]) for _ in range(N)]
                    self.wfile.write(f"[?] Golem Challenge Nonce: {json.dumps(chal)}\n".encode("utf-8"))
                    self.wfile.write(b"[?] Enter response vector z (JSON list of 8 ints): ")
                    self.wfile.flush()

                    resp_line = self.rfile.readline().decode("utf-8", errors="ignore").strip()
                    try:
                        resp_z = json.loads(resp_line)
                    except Exception:
                        self.wfile.write(b"[-] Invalid JSON format!\n")
                        self.wfile.flush()
                        continue

                    if not isinstance(resp_z, list) or len(resp_z) != N:
                        self.wfile.write(b"[-] Invalid vector dimensions.\n")
                        self.wfile.flush()
                        continue

                    # Verify that z - chal * s mod Q is small error y in [0, 4]
                    cs = poly_mul(chal, SECRET_S)
                    valid = True
                    for i in range(N):
                        err = (resp_z[i] - cs[i]) % Q
                        if err < 0 or err > 4:
                            valid = False
                            break

                    if valid:
                        self.wfile.write(b"\n[+] POST-QUANTUM SIGNATURE VERIFIED BY GOLEM SENTINEL.\n")
                        self.wfile.write(b"[+] GOLEM LEGION STANDING DOWN. SUBTERRANEAN PASSAGE SECURED.\n")
                        self.wfile.write(f"[+] FLAG: {FLAG}\n\n".encode("utf-8"))
                        self.wfile.flush()
                        break
                    else:
                        self.wfile.write(b"[-] INVALID SIGNATURE. GOLEM SENTINEL ACTIVATES HYPER-KINETIC CANNON.\n")
                        self.wfile.flush()
                        break

                elif choice == "3":
                    self.wfile.write(b"[*] Terminating link.\n")
                    self.wfile.flush()
                    break
        except Exception:
            pass

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True

if __name__ == "__main__":
    print(f"[*] Starting Golem Lattice Daemon on port {PORT}...")
    server = ThreadedTCPServer(("0.0.0.0", PORT), GolemHandler)
    server.serve_forever()
