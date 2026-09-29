# Challenge 07: The Golem's Seal

## 1. Challenge Overview & Quick Reference

| Attribute | Value |
|---|---|
| **Challenge Name** | The Golem's Seal |
| **Directory** | `07-golems-seal` |
| **Category** | Post-Quantum Cryptography / Lattice Ring-LWE / Hidden Number Problem |
| **Difficulty** | Hard (Stage 2) |
| **Target Solve Time** | ~15–20 minutes |
| **Connection** | `nc <host> 1341` |
| **Default Static Flag** | `YUVA{p0st_qu4ntum_l4tt1c3_g0l3m_d1s4rm3d_5829}` |
| **Dynamic Env Vars** | `FLAG` (flag override), `PORT` (port override, default 1341) |
| **Handouts** | `handouts/golem_client.py`, `handouts/transcripts.json` |

---

## 2. Clear Objective

The player must analyze Doom's post-quantum lattice identification protocol over the polynomial ring $R_q = \mathbb{Z}_{257}[x]/(x^8 + 1)$, exploit a biased / truncated PRNG noise distribution in the server's rejection sampling subroutine, recover the master 8-degree signing secret polynomial $s(x) \in \{-1, 0, 1\}^8$, connect to TCP port 1341, sign an administrative challenge nonce, and disarm the Golem legion to claim the flag.

The flag is stored in `/flag.txt` inside the container and only released when the server verifies that the player's signature polynomial $z(x)$ satisfies the lattice equation $z \equiv y + c \cdot s \pmod{257}$ under small infinity-norm bounds.

---

## 3. Architecture & Story ("Vulnerability First")

### The Story
Guarding the Sub-Quantum Arcane Collider beneath Castle Doom is a battalion of Runic Titanium Golems. Recognizing the threat of Shor's quantum factoring algorithm, Doom fortified the golems with a lattice-based Ring Learning With Errors (Ring-LWE) identification protocol. However, Doom's custom silicon PRNG truncated the rejection sampling bounds, causing the ephemeral masking polynomials to leak entropy.

### Intended Technical Concept
```
[Live Golem Bastion (:1341)] ──► Option 1: Collect Transcripts (c, z)
                                               │
                                               ▼
             [Mathematical Model: z = (y + c * s) mod 257 in Z_257[x]/(x^8 + 1)]
             [Vulnerability: PRNG Truncation Leaks y_i in [0, 4]]
                                               │
                                               ▼
           [Search Candidate Space: s_i in {-1, 0, 1}^8 -> 3^8 = 6,561 candidates]
           [Filter Condition: for all i in [0, 7]: (z_i - (c * s)_i) mod 257 <= 4]
                                               │
                                               ▼
                           [Uniquely Recover Secret Key s(x)]
                                               │
                                               ▼
                   [Live Golem Bastion (:1341)] ──► Option 2: Request Admin Nonce c
                                               │
                                               ▼
                         [Compute Valid Signature: z = (y + c * s) mod 257]
                                               │
                                               ▼
               [Transmit Forged Signature z ──► Disarm Golems ──► Flag]
```

1. **Ring-LWE Arithmetic**: Operations are conducted in the cyclotomic quotient ring $\mathbb{Z}_{257}[x]/(x^8 + 1)$, where degree reductions satisfy $x^8 \equiv -1$.
2. **Entropy Leakage**: In standard Fiat-Shamir lattice signatures, ephemeral masking vector $y$ must be drawn from a wide Gaussian or uniform distribution. Here, Doom's generator restricts $y_i \in [0, 4]$.
3. **Filtering Complexity**: Because $n = 8$ and each secret coefficient $s_i \in \{-1, 0, 1\}$, there are only $3^8 = 6,561$ total candidate polynomials. With 3–4 transcripts, testing $(z_i - (c \cdot s)_i) \pmod{257} \le 4$ eliminates all impostors in under 50 milliseconds in pure Python.

---

## 4. How to Run on Any System (Quick Spin-Up)

### 1. Build and Start the Container
```bash
cd 07-golems-seal
docker compose up -d --build
```

### 2. Verify Port & Access
```bash
# Verify TCP listener on port 1341
nc 127.0.0.1 1341
```

### 3. Spin Up with Custom Dynamic Flag
```bash
FLAG="FLAG{custom_dynamic_golem_pq_flag_3333}" docker compose up -d --build
```

### 4. Standalone Execution (Without Docker)
```bash
python3 src/golem_server.py
```

### 5. Teardown
```bash
docker compose down
```

---

## 5. Progressive Hints

- **Hint 1 (Protocol Structure)**: Inspect `handouts/golem_client.py` and `handouts/transcripts.json`. What polynomial ring is being used? Note the modulus $q = 257$ and polynomial modulus $x^8 + 1$.
- **Hint 2 (Noise Bounds)**: Look closely at how $y$ is generated in the transcript samples: $y_i = z_i - (c \cdot s)_i \pmod{257}$. Check the range of $y_i$ across all samples—notice that $y_i$ is strictly in $[0, 4]$.
- **Hint 3 (Exhaustive Reduction)**: The ternary secret has only $3^8 = 6561$ possibilities. Iterate over all candidates, compute $c \cdot s$, and keep only the secret $s$ for which $z_i - (c \cdot s)_i \in [0, 4]$ across all coefficients and transcripts.

---

## 6. Step-by-Step Intended Solve Path

1. **Collect 3–4 Transcripts**:
   Connect to port 1341, select Option 1, and parse challenge polynomials $c(x)$ and response polynomials $z(x)$.
2. **Generate All 6,561 Ternary Candidates**:
   ```python
   candidates = [[]]
   for _ in range(8):
       candidates = [curr + [v] for curr in candidates for v in (-1, 0, 1)]
   ```
3. **Filter Candidates Against Transcripts**:
   Multiply $c \cdot s \pmod{x^8 + 1, 257}$. Discard candidates where $(z_i - (c \cdot s)_i) \pmod{257} > 4$. Exactly 1 candidate will survive.
4. **Sign the Admin Challenge**:
   Select Option 2 on the server. Read the challenge polynomial $c$.
   Choose $y = [2, 2, 2, 2, 2, 2, 2, 2]$ (within valid bound $[0, 4]$) and compute $z = (y + c \cdot s) \pmod{257}$.
5. **Submit Signature**:
   Send $z$ as a JSON array or comma-separated list. Server verifies the signature and prints the flag.

---

## 7. Exact Solution Script Code & Execution

Run the automated Python exploit script from the challenge directory:

```bash
python3 solution/solve.py 127.0.0.1 1341
```

### Complete Exploit Script (`solution/solve.py`):
```python
#!/usr/bin/env python3
"""
Automated solve script for Challenge 07: The Golem's Seal
Exploits PRNG noise truncation in Ring-LWE identification protocol,
recovers secret polynomial s(x), forges disarm signature, and retrieves the flag.
"""
import sys
import socket
import json

N = 8
Q = 257

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

def recover_secret(transcripts):
    candidates = [[]]
    for _ in range(N):
        candidates = [curr + [v] for curr in candidates for v in (-1, 0, 1)]

    for c, z in transcripts:
        filtered = []
        for cand in candidates:
            cs = poly_mul(c, cand)
            valid = True
            for i in range(N):
                diff = (z[i] - cs[i]) % Q
                if diff > 4:
                    valid = False
                    break
            if valid:
                filtered.append(cand)
        candidates = filtered
        if len(candidates) == 1:
            break
            
    if len(candidates) == 1:
        return candidates[0]
    return candidates[0] if candidates else None

def solve(host="127.0.0.1", port=1341):
    print(f"[*] Connecting to Golem Bastion at {host}:{port}...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, int(port)))

    def read_until(prompt):
        buf = ""
        while prompt not in buf:
            chunk = s.recv(1024).decode("utf-8", errors="ignore")
            if not chunk:
                break
            buf += chunk
        return buf

    transcripts = []
    read_until("Choice > ")
    
    print("[*] Harvesting authentication transcripts from server...")
    for _ in range(4):
        s.sendall(b"1\n")
        data = read_until("Choice > ")
        for line in data.splitlines():
            if line.startswith("c = "):
                c = json.loads(line.split(" = ")[1])
            elif line.startswith("z = "):
                z = json.loads(line.split(" = ")[1])
                transcripts.append((c, z))

    print(f"[+] Harvested {len(transcripts)} transcripts.")
    s_poly = recover_secret(transcripts)
    print(f"[+] Successfully recovered master secret polynomial s(x): {s_poly}")

    print("[*] Requesting disarm authorization challenge (Option 2)...")
    s.sendall(b"2\n")
    challenge_data = read_until("Signature z > ")
    
    c_chal = None
    for line in challenge_data.splitlines():
        if "Challenge Nonce c =" in line:
            c_chal = json.loads(line.split(" = ")[1])
            break

    print(f"[+] Received Admin Challenge c(x): {c_chal}")

    y_fixed = [2] * N
    cs_chal = poly_mul(c_chal, s_poly)
    z_forged = [(y_fixed[i] + cs_chal[i]) % Q for i in range(N)]
    print(f"[+] Forging signature z(x): {z_forged}")

    s.sendall(json.dumps(z_forged).encode("utf-8") + b"\n")
    final_resp = read_until("\n\n")
    print(final_resp)

    for line in final_resp.splitlines():
        if "FLAG{" in line:
            flag = line[line.find("FLAG{"):].split()[0]
            print(f"[+] Captured Flag: {flag}")
            s.close()
            return flag

    s.close()
    return None

if __name__ == "__main__":
    h = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    p = int(sys.argv[2]) if len(sys.argv) > 2 else 1341
    solve(h, p)
```

---

## 8. CTF Quality, Security & Anti-Shortcut Audit

- **Clear Objective**: Recover polynomial secret $s(x)$ via lattice reduction/noise bias and sign the admin nonce.
- **No Unintended Shortcuts**:
  - The handouts (`transcripts.json`, `golem_client.py`) do not leak $s(x)$ or the flag.
  - The server verifies signatures against fresh randomly generated nonces per session; replaying old $z$ values fails.
  - Server bounds check verifies $||z - c \cdot s||_\infty \le 4$; guessing an unauthenticated vector succeeds with probability $< (5/257)^8 \approx 3 \times 10^{-14}$.
- **Challenge Isolation**: Runs as unprivileged user `ctf` with no external dependencies.
- **Resetability**: Each session operates independently on its own TCP socket.
- **Performance**: Solves in under 0.1s; minimal CPU usage.

---

## 9. Author & Admin Notes

- Designed to teach the fundamentals of lattice-based signature vulnerabilities and why discrete Gaussian sampling / strict rejection sampling is critical in Ring-LWE.
- Complete reference guide available in [GUIDE.md](file:///home/alucard/ch-j/07-golems-seal/GUIDE.md).
