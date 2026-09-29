# Challenge 2: Doombot Firmware Link — Solution Writeup

## Summary
- **Category**: Reverse Engineering
- **Difficulty**: Intermediate
- **Techniques**: Static analysis in Ghidra / IDA Pro, anti-debugging bypass, custom cipher reversal, socket automation.

---

## Step 1: Initial Reconnaissance
We are given an x86_64 ELF binary `doombot_auth`. Checking file properties:
```bash
file doombot_auth
# ELF 64-bit LSB pie executable, x86-64, dynamically linked, stripped
checksec --file=doombot_auth
# Full RELRO, Canary found, NX enabled, PIE enabled
```
Running it locally without arguments:
```
============================================================
[*] DOOMBOT UNIT v4.2 - SECURE ACTIVATION SUITE
[*] LATVERIAN MILITARY STANDARD 904-B
============================================================
Usage: ./doombot_auth <16-hex-nonce> <32-hex-response>
Example: ./doombot_auth 0123456789abcdef 4a8f90...
```

---

## Step 2: Static Analysis & Anti-Debugging
Decompiling `main` in Ghidra:
1. **Anti-debugging routine (`check_debugger`)**:
   - Inspects `/proc/self/status` for `TracerPid`.
   - If a tracer is detected, checks `/proc/<TracerPid>/comm` for tools like `gdb`, `strace`, `ltrace`, or `r2`.
   - If found, outputs `INTRUSION DETECTED: Tamper flag raised.` and exits with code 137.
   - *Bypass*: When patching or analyzing statically, this check can be NOPed out or ignored since our goal is extracting the algorithm.

2. **Core Algorithm (`compute_doombot_signature`)**:
   The binary takes an 8-byte nonce and expands it into 16 bytes using a hardcoded key `"LATVERIA_VICTOR!"`:
   ```c
   // Expansion
   for (int i = 0; i < 8; i++) {
       uint8_t b = nonce[i];
       expanded[2 * i] = (uint8_t)((b ^ DOOM_KEY[2 * i]) + 0x37);
       uint8_t ror = (uint8_t)((b >> 3) | (b << 5));
       expanded[2 * i + 1] = (uint8_t)(ror ^ DOOM_KEY[2 * i + 1]);
   }
   ```
   Next, it applies a permutation table `[7, 2, 15, 0, 11, 4, 13, 8, 1, 14, 3, 10, 5, 12, 9, 6]`:
   ```c
   for (int i = 0; i < 16; i++) {
       permuted[i] = expanded[PERMUTATION_MAP[i]];
   }
   ```
   Finally, it applies a feedback loop (similar to CBC-mode XOR with additions):
   ```c
   output[0] = permuted[0] ^ 0x5D;
   for (int i = 1; i < 16; i++) {
       output[i] = ((permuted[i] + output[i - 1]) & 0xFF) ^ 0xAA;
   }
   ```
   The result is formatted as a 32-character hexadecimal string.

---

## Step 3: Automated Solver
Since the binary does not generate the response for a given nonce (it only validates candidate responses), we replicate `compute_doombot_signature` in Python.

When connected to `nc <host> 1338`:
1. Receive challenge nonce (e.g., `7f3a8b19d4e2c05f`).
2. Compute the 32-hex authorization signature.
3. Send the signature to the server.
4. Read the dynamic deployment flag.

Flag:
`YUVA{v1ct0r_v0n_d00m_m4st3r_0f_sc13nc3_4nd_m4g1c_9902}`
