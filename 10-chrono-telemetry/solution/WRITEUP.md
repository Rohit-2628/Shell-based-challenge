# Challenge 10: Chrono-Telemetry Stream - Writeup

## Overview
- **Category**: Networking / Protocol Forensics & Type Confusion
- **Difficulty**: Hard
- **Provided**: `chrono_client.py`, `chrono_capture.pcap`, `protocol_spec.txt`
- **Target**: TCP Service on port `8043`

---

## 1. Protocol Reverse Engineering

Inspecting `protocol_spec.txt` and `chrono_capture.pcap` reveals a custom high-performance binary streaming protocol `CHRONO-STREAM/3.1` with a 16-byte header:

```text
[Magic: b"CHRN" (4B)] [Version: 0x0301 (2B)] [TypeID: uint16 (2B)] [Len: uint32 (4B)] [CRC32: uint32 (4B)]
```

Disarming the core requires sending packet `TYPE_ADMIN_CMD` (`0x00A0`) with:
- `auth_token`: 16 bytes
- `cmd_id`: `0x1337` (`CMD_DRAIN_CORE`)

However, the 16-byte administrative token is dynamically seeded upon server initialization.

---

## 2. Vulnerability: Zero-Copy Buffer Reflection

Examining the `DiagnosticsQuery` (`0x0002`) handler in `protocol_spec.txt` reveals an undocumented feature:
- Bit 31 of the reflection mask (`0x80000000`) enables a zero-copy memory mirror.
- Bits `[0..30]` define the byte offset into the server's internal session context buffer.

The internal server context layout is:
- Bytes `[0..15]`: System Header (`b"LATV_CHRN_SYS31!"`)
- Bytes `[16..31]`: Active Admin Token (`16 bytes`)

By sending a `DiagnosticsQuery` with `reflection_mask = 0x80000000 | 16`, the server slices 16 bytes starting at offset 16 and reflects the raw admin token back in the diagnostics response payload!

---

## 3. Exploitation

1. Send `DiagnosticsQuery` probe with flag `0x80000010`.
2. Extract the 16-byte leaked `admin_token` from the response payload.
3. Build an authenticated `AdminCommand` packet:
   - Type: `0x00A0`
   - Token: leaked 16 bytes
   - Command: `0x1337` (`CMD_DRAIN_CORE`)
4. Submit packet to TCP `:8043`.
5. Receive core drain confirmation and master flag!

---

## 4. Execution

Run the automated solver:
```bash
python3 solution/solve.py 127.0.0.1 8043
```
Flag: `YUVA{z3r0_c0py_t3l3m3try_r3fl3ct10n_d00m_c0r3_8492}`
