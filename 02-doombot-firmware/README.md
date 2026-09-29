# Challenge 02: Doombot Firmware Link

## 1. Challenge Overview & Quick Reference

| Attribute | Value |
|---|---|
| **Challenge Name** | Doombot Firmware Link |
| **Directory** | `02-doombot-firmware` |
| **Category** | Reverse Engineering |
| **Difficulty** | Medium (Stage 1) |
| **Target Solve Time** | ~10 minutes |
| **Connection** | `nc <host> 1338` |
| **Default Static Flag** | `YUVA{v1ct0r_v0n_d00m_m4st3r_0f_sc13nc3_4nd_m4g1c_9902}` |
| **Dynamic Env Vars** | `FLAG` (flag override), `PORT` (port override, default 1338) |
| **Handouts** | `handouts/doombot_auth` (64-bit ELF executable) |

---

## 2. Clear Objective

The player must reverse-engineer the stripped 64-bit ELF client authentication routine (`handouts/doombot_auth`), identify the cryptographic key and bitwise transformation steps, implement a Python client to interact with the live C2 daemon on TCP port 1338, dynamically compute the valid signature for a server-generated random nonce, and capture the mission directive flag.

The flag is held in memory by the C2 daemon and only released upon supplying the mathematically valid 32-character hex signature for the dynamic nonce.

---

## 3. Architecture & Story ("Vulnerability First")

### The Story
A downed Doombot patrol scout chip was recovered along the perimeter wall of Castle Doom. The chip contains a stripped firmware client binary (`doombot_auth`) configured to periodically check in with the Latveria Tactical Defense Grid central C2 node. Upon connection, the C2 node broadcasts a dynamic 8-byte challenge nonce and terminates unless authenticated within 15 seconds.

### Intended Technical Concept
```
[Live C2 Server (:1338)] ──(Issues 8-byte Random Nonce)──► [Attacker Python Client]
                                                                  │
                                            ┌─────────────────────┴─────────────────────┐
                                            │ Reverse-Engineered Signature Pipeline:    │
                                            │ 1. Expansion with 'LATVERIA_VICTOR!'      │
                                            │ 2. Permutation Mapping (PERMUTATION_MAP) │
                                            │ 3. Rolling Feedback XOR Transformation    │
                                            └─────────────────────┬─────────────────────┘
                                                                  │
[Live C2 Server (:1338)] ◄──(32-hex Response Signature)───────────┘
        │
(Valid Signature Verified)
        │
        ▼
[Releases Flag: FLAG{...}]
```

1. **Deterministic Forward Cipher**: The signature algorithm does not use asymmetric cryptography or secret server-side state. It is a completely deterministic, forward-only keyed transformation.
2. **Reverse Engineering Steps**:
   - **Key extraction**: The 16-byte key `LATVERIA_VICTOR!` is embedded in the binary text.
   - **Stage 1 (Expansion)**: 8 input bytes expand into 16 bytes via bitwise rotation and XOR.
   - **Stage 2 (Permutation)**: Fixed index permutation array `[7, 2, 15, 0, 11, 4, 13, 8, 1, 14, 3, 10, 5, 12, 9, 6]`.
   - **Stage 3 (Rolling Feedback)**: CBC-style rolling addition and XOR with constant `0xAA`.

---

## 4. How to Run on Any System (Quick Spin-Up)

### 1. Build and Start the Container
```bash
cd 02-doombot-firmware
docker compose up -d --build
```

### 2. Verify Port & Access
```bash
# Verify TCP listener on port 1338
nc 127.0.0.1 1338
```

### 3. Spin Up with Custom Dynamic Flag
```bash
FLAG="FLAG{custom_dynamic_doombot_flag_999}" docker compose up -d --build
```

### 4. Standalone Execution (Without Docker)
```bash
python3 src/c2_server.py
```

### 5. Teardown
```bash
docker compose down
```

---

## 5. Progressive Hints

- **Hint 1 (Reconnaissance)**: Run `strings handouts/doombot_auth` and grep for uppercase words or keys. You should locate the constant string `LATVERIA_VICTOR!`.
- **Hint 2 (Decompilation)**: Load `handouts/doombot_auth` into Ghidra or IDA. Locate the signature function that processes the 8-byte nonce buffer. Notice how the loop iterates through an expansion, a permutation lookup table, and a rolling feedback loop.
- **Hint 3 (Exploitation)**: Because the algorithm is deterministic and public in the binary, write a 25-line Python script that connects to port 1338, parses the `NONCE:` string from the banner, computes the signature, and sends it back.

---

## 6. Step-by-Step Intended Solve Path

1. **Static Analysis of Handout**:
   ```bash
   file handouts/doombot_auth
   strings handouts/doombot_auth | grep "LATVERIA"
   ```
2. **Decompile the Algorithm**:
   Decompiling `compute_signature` reveals:
   - For $i \in [0, 7]$:
     - $E[2i] = ((N[i] \oplus K[2i]) + 0x37) \pmod{256}$
     - $E[2i+1] = \text{ror}_3(N[i]) \oplus K[2i+1]$
   - Permute with `MAP = [7, 2, 15, 0, 11, 4, 13, 8, 1, 14, 3, 10, 5, 12, 9, 6]`.
   - Rolling feedback:
     - $O[0] = P[0] \oplus 0x5D$
     - $O[i] = ((P[i] + O[i-1]) \pmod{256}) \oplus 0xAA$
3. **Execute Solver**:
   Run the solver against the target daemon to grab the flag:
   ```bash
   python3 solution/solve.py 127.0.0.1 1338
   ```

---

## 7. Exact Solution Script Code & Execution

Run the automated Python exploit script from the challenge directory:

```bash
python3 solution/solve.py 127.0.0.1 1338
```

### Complete Exploit Script (`solution/solve.py`):
```python
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

    result = s.recv(2048).decode('utf-8', errors='ignore')
    print(result)

    for line in result.splitlines():
        if "FLAG{" in line:
            flag = line[line.find("FLAG{"):].split()[0]
            print(f"[+] Captured Flag: {flag}")
            s.close()
            return flag

    s.close()
    return None

if __name__ == "__main__":
    h = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    p = int(sys.argv[2]) if len(sys.argv) > 2 else 1338
    solve(h, p)
```

---

## 8. CTF Quality, Security & Anti-Shortcut Audit

- **Clear Objective**: Clear network service authentication challenge; authenticate with the correct signature to receive the flag.
- **No Unintended Shortcuts**:
  - The ELF handout `doombot_auth` does NOT contain the flag string.
  - The C2 server strictly generates nonces dynamically and only outputs the flag if the client response matches `expected_sig`.
  - No shell or OS command injection vectors exist on port 1338.
- **Challenge Isolation**: The container runs under an unprivileged user `ctf` (UID 1001) in an isolated network namespace.
- **Resetability**: Each TCP connection is stateless and independently handled by `ThreadedTCPServer`. Disconnections or failed attempts do not impact subsequent attempts.
- **Performance**: Lightweight Python `socketserver` handling up to hundreds of concurrent connections with negligible memory consumption.

---

## 9. Author & Admin Notes

- Timeouts are set to 15 seconds per connection in `src/c2_server.py`.
- Detailed reference guide available in [GUIDE.md](file:///home/alucard/ch-j/02-doombot-firmware/GUIDE.md).
