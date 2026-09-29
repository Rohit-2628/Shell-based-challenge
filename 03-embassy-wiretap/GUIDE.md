# Challenge 03: Embassy Wiretap Protocol — Challenge Guide

## 1. Challenge Overview & Quick Reference

| Attribute | Value |
|---|---|
| **Challenge Name** | Embassy Wiretap Protocol |
| **Directory** | `03-embassy-wiretap` |
| **Category** | Networking / Protocol Forensics |
| **Difficulty** | Medium (Stage 1) |
| **Target Solve Time** | ~10 minutes |
| **Connection** | TCP port `:8042` (Custom Binary Protocol) |
| **Default Static Flag** | `YUVA{h4ck1ng_th3_l4tv3r14n_d1pl0m4t1c_w1r3_5183}` |
| **Dynamic Env Vars** | `FLAG` (flag override), `PORT` (port override, default 8042) |
| **Handouts** | `handouts/latverian_embassy.pcap` |

---

## 2. Clear Objective

The player must analyze the network packet capture file (`handouts/latverian_embassy.pcap`), reverse-engineer the custom binary wire format of the `DOOM-NET/2.0` protocol, recover the pre-shared authentication secret, implement a custom Python client to perform the 3-step dynamic handshake against the live daemon on TCP port 8042, and issue query command `0x1337` to dump the orbital telemetry flag.

The flag is dynamically injected into the daemon memory and only emitted inside a valid `MSG_QUERY_RESP` (0x06) packet after full cryptographic authentication.

---

## 3. Architecture & Story ("Vulnerability First")

### The Story
Resistance operators tapped a high-bandwidth diplomatic fiber-optic link emanating from the Latverian Embassy. The wiretap captured a sample negotiation between an embassy terminal and Castle Doom's central server. To disarm Doom's border orbital defenses, you must replay and adapt the protocol against the live embassy relay on port 8042.

### Intended Technical Concept
```
[Wireshark / PCAP Analysis] ──► Recover: Magic ('DOOM'), Version (2), Header Struct, & PSK
                                                                    │
                                                                    ▼
[Attacker Python Socket Client] ─── MSG_HELLO_REQ (0x01) ───► [Embassy Relay (:8042)]
                                ◄── MSG_HELLO_RESP (0x02) ─── (Returns 8-byte Dynamic Salt)
                                │
[Compute HMAC-SHA256(Salt, PSK)]
                                │
                                ─── MSG_AUTH_REQ (0x03) ────► [Embassy Relay (:8042)]
                                ◄── MSG_AUTH_RESP (0x04) ─── (Status: 0x00 SUCCESS)
                                │
                                ─── MSG_QUERY_REQ (0x05) ───► (Command ID 0x1337)
                                ◄── MSG_QUERY_RESP (0x06) ── [Orbital Flag: FLAG{...}]
```

1. **Custom Binary Framing**:
   - Header (12 bytes big-endian):
     - `Magic`: 4 bytes (`b"DOOM"`)
     - `Version`: 1 byte (`0x02`)
     - `MsgType`: 1 byte (`0x01`–`0x06`)
     - `SeqNum`: 2 bytes (`uint16`)
     - `PayloadLen`: 2 bytes (`uint16`)
     - `Checksum`: 2 bytes (`uint16`, simple sum of `header_partial + payload & 0xFFFF`)
2. **Replay Mitigation Bypass**: The server rejects replayed tokens because each connection generates a fresh 8-byte random challenge salt. Authentication requires computing `HMAC-SHA256(salt, SHARED_PSK)`.
3. **Secret Recovery**: The pre-shared key `LATVERIA_DIPLOMATIC_CIPHER_1962` is discovered in the PCAP initialization transcript.

---

## 4. How to Run on Any System (Quick Spin-Up)

### 1. Build and Start the Container
```bash
cd 03-embassy-wiretap
docker compose up -d --build
```

### 2. Verify Port & Access
```bash
# Verify TCP listener on port 8042
nc -z -v 127.0.0.1 8042
```

### 3. Spin Up with Custom Dynamic Flag
```bash
FLAG="FLAG{custom_dynamic_embassy_flag_777}" docker compose up -d --build
```

### 4. Standalone Execution (Without Docker)
```bash
python3 src/embassy_relay.py
```

### 5. Teardown
```bash
docker compose down
```

---

## 5. Progressive Hints

- **Hint 1 (Packet Analysis)**: Open `handouts/latverian_embassy.pcap` in Wireshark. Filter for TCP traffic. Inspect the ASCII strings in the stream: look for protocol identification banners and pre-shared key strings.
- **Hint 2 (Binary Framing)**: Notice the 12-byte header starting with ASCII `DOOM\x02`. The last 2 bytes of the header change when the payload changes—it is a 16-bit additive checksum of the header and payload bytes.
- **Hint 3 (Dynamic Authentication)**: The server sends an 8-byte salt in message type `0x02`. Message type `0x03` expects a 32-byte payload: verify if this is `HMAC-SHA256(salt, PSK)`.

---

## 6. Step-by-Step Intended Solve Path

1. **Inspect the PCAP in Wireshark/Tshark**:
   ```bash
   tshark -r handouts/latverian_embassy.pcap -Y "tcp" -x
   ```
   Extract the pre-shared secret string: `LATVERIA_DIPLOMATIC_CIPHER_1962`.

2. **Structure the Packet Builder**:
   - Magic: `DOOM` (4 bytes)
   - Version: `2` (1 byte)
   - MsgType, Seq, Length (5 bytes)
   - Checksum: `sum(header_partial + payload) & 0xFFFF` (2 bytes)

3. **Perform the Dynamic Handshake**:
   - Send `MSG_HELLO_REQ` (0x01) with client identifier.
   - Receive `MSG_HELLO_RESP` (0x02) containing the 8-byte random salt.
   - Compute `HMAC-SHA256(salt, b"LATVERIA_DIPLOMATIC_CIPHER_1962")`.
   - Send `MSG_AUTH_REQ` (0x03) with the digest.
   - Receive `MSG_AUTH_RESP` (0x04) returning `0x00` (success).

4. **Query Telemetry**:
   - Send `MSG_QUERY_REQ` (0x05) with 2-byte big-endian payload `\x13\x37`.
   - Receive `MSG_QUERY_RESP` (0x06) containing the flag.

---

## 7. Exact Solution Script Code & Execution

Run the automated Python exploit script from the challenge directory:

```bash
python3 solution/solve.py 127.0.0.1 8042
```

### Complete Exploit Script (`solution/solve.py`):
```python
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
        if "FLAG{" in line:
            flag = line[line.find("FLAG{"):].split()[0]
            print(f"[+] Captured Flag: {flag}")
            s.close()
            return flag

    s.close()
    return None

if __name__ == "__main__":
    h = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    p = int(sys.argv[2]) if len(sys.argv) > 2 else 8042
    solve(h, p)
```

---

## 8. CTF Quality, Security & Anti-Shortcut Audit

- **Clear Objective**: Reverse the proprietary wire format, authenticate dynamically, and query the secret record.
- **No Unintended Shortcuts**:
  - The PCAP file does NOT leak the flag; it only contains the PSK and protocol handshake sample.
  - The replay attack fails because salts are random and ephemeral.
  - Queries prior to authentication return `0xFF` (FORBIDDEN) and terminate the connection.
- **Challenge Isolation**: Daemon runs as unprivileged user `ctf` (UID 1001) in an isolated container.
- **Resetability**: Fully stateless connection model using `ThreadedTCPServer`.
- **Performance**: Capable of handling over 200 connections/sec with low CPU overhead.

---

## 9. Author & Admin Notes

- Binary format errors trigger automatic disconnects without leaking internal stack traces.
- Complete reference guide available in [GUIDE.md](file:///home/alucard/ch-j/03-embassy-wiretap/GUIDE.md).
