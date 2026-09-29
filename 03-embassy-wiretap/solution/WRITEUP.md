# Challenge 3: Embassy Wiretap Protocol — Solution Writeup

## Summary
- **Category**: Networking
- **Difficulty**: Intermediate
- **Techniques**: PCAP packet inspection (Wireshark), custom layer-7 binary protocol reverse-engineering, cryptographic challenge-response authentication, TCP network client implementation.

---

## Step 1: PCAP Analysis (Wireshark)
Opening `latverian_embassy.pcap` in Wireshark reveals two key traffic components:
1. **Syslog notification on UDP 514**:
   ```
   LATVERIA-EMBASSY-GW[1042]: [AUTH] DOOM-NET v2 service starting on :8042 (PSK: LATVERIA_DIPLOMATIC_CIPHER_1962)
   ```
   This gives us the pre-shared key:
   `LATVERIA_DIPLOMATIC_CIPHER_1962`.

2. **TCP conversation on port 8042**:
   Following the TCP stream reveals structured binary frames prefixed with magic bytes `DOOM` (`0x444f4f4d`).

---

## Step 2: Protocol Dissection
Analyzing the byte offsets in the 12-byte header:
- `0x00..0x03`: Magic string `b"DOOM"`
- `0x04`: Version `0x02`
- `0x05`: Message Type
  - `0x01`: `HELLO_REQ` (Client -> Server)
  - `0x02`: `HELLO_RESP` (Server -> Client, returns 8-byte dynamic salt)
  - `0x03`: `AUTH_REQ` (Client -> Server, 32 bytes HMAC-SHA256 of salt using PSK)
  - `0x04`: `AUTH_RESP` (Server -> Client, `0x00` status for success)
  - `0x05`: `QUERY_REQ` (Client -> Server, 2-byte command ID: `0x1337`)
  - `0x06`: `QUERY_RESP` (Server -> Client, secret telemetry payload containing flag)
- `0x06..0x07`: Sequence Number (`uint16_be`)
- `0x08..0x09`: Payload Length (`uint16_be`)
- `0x0A..0x0B`: Checksum (`uint16_be`): `sum(header[:10] + payload) & 0xFFFF`

---

## Step 3: Solver Implementation
Because the live server issues a distinct random salt on each connection, simply replaying captured packets will fail. We write a Python client (`solve.py`) to execute the dynamic handshake:
1. Connect to live container on port 8042.
2. Send `MSG_HELLO_REQ` with sequence `1`.
3. Receive `MSG_HELLO_RESP` and extract the 8-byte salt.
4. Calculate `hmac.new(b"LATVERIA_DIPLOMATIC_CIPHER_1962", salt, hashlib.sha256).digest()`.
5. Send `MSG_AUTH_REQ` with the HMAC.
6. Verify `MSG_AUTH_RESP` (`0x00`).
7. Send `MSG_QUERY_REQ` with command ID `0x1337` (`b"\x13\x37"`).
8. Receive `MSG_QUERY_RESP` and extract the dynamic flag.

Flag:
`YUVA{h4ck1ng_th3_l4tv3r14n_d1pl0m4t1c_w1r3_5183}`
