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

    banner = read_until("Select Command (1-3):")
    print(banner)

    # Collect 4 transcripts
    transcripts = []
    for _ in range(4):
        s.sendall(b"1\n")
        data = read_until("Select Command (1-3):")
        # Extract json
        start = data.find("{")
        end = data.find("}", start) + 1
        obj = json.loads(data[start:end])
        transcripts.append((obj["challenge_c"], obj["response_z"]))

    print(f"[+] Collected {len(transcripts)} transcripts.")
    s_poly = recover_secret(transcripts)
    print(f"[+] Recovered Secret Polynomial s(x): {s_poly}")
    assert s_poly is not None, "Failed to recover secret polynomial"

    # Send disarm command
    s.sendall(b"2\n")
    chal_data = read_until("Enter response vector z")
    print(chal_data)

    c_start = chal_data.find("[")
    c_end = chal_data.find("]", c_start) + 1
    chal = json.loads(chal_data[c_start:c_end])
    print(f"[+] Received Challenge Nonce: {chal}")

    # Compute valid signature z = y + chal * s mod Q
    # Choose y_i = 2 (which is in [0, 4])
    cs = poly_mul(chal, s_poly)
    forged_z = [(2 + cs[i]) % Q for i in range(N)]
    print(f"[+] Forged Response Vector z: {forged_z}")

    s.sendall(json.dumps(forged_z).encode("utf-8") + b"\n")

    res = ""
    while True:
        chunk = s.recv(1024).decode("utf-8", errors="ignore")
        if not chunk:
            break
        res += chunk
        if "FLAG{" in res or "YUVA{" in res:
            break

    print(res)
    s.close()

    for line in res.splitlines():
        if "YUVA{" in line:
            flag = line[line.find("YUVA{"):].split()[0]
            print(f"[+] Successfully solved Challenge 07! Flag: {flag}")
            return flag
        if "FLAG{" in line:
            flag = line[line.find("FLAG{"):].split()[0]
            print(f"[+] Successfully solved Challenge 07! Flag: {flag}")
            return flag

    return None

if __name__ == "__main__":
    h = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    p = int(sys.argv[2]) if len(sys.argv) > 2 else 1341
    solve(h, p)
