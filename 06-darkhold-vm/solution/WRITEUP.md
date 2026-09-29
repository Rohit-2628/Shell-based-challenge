# Challenge 06: The Darkhold Virtual Machine - Writeup

## Overview
- **Category**: Reverse Engineering / Esoteric VM
- **Difficulty**: Hard
- **Provided**: `darkhold_vm` (ELF binary), `sigil.enc` (encrypted bytecode)
- **Target**: TCP Service on port `1340`

---

## 1. Static Analysis & VM Architecture

Decompiling the stripped binary `darkhold_vm` in Ghidra or IDA reveals an execution loop with a 4-register state `uint8_t r[4]`, an instruction pointer `pc`, and an input buffer:

```c
typedef struct {
    uint8_t r[4];       // R0, R1, R2, R3
    uint8_t input[16];
    uint8_t output[16];
    size_t pc;
    int fault;
} DarkholdVM;
```

### Opcode Dispatch Table
Reversing the `switch (op)` statement discloses the following ISA:

| Opcode | Mnemonic | Operands | Operation |
|---|---|---|---|
| `0x10` | `OP_LOAD_IMM` | `reg, imm` | `r[reg] = imm` |
| `0x11` | `OP_LOAD_IN` | `reg, idx` | `r[reg] = input[idx]` |
| `0x12` | `OP_STORE_OUT`| `reg, idx` | `output[idx] = r[reg]` |
| `0x20` | `OP_ADD` | `ra, rb` | `r[ra] = (r[ra] + r[rb]) & 0xFF` |
| `0x21` | `OP_SUB` | `ra, rb` | `r[ra] = (r[ra] - r[rb]) & 0xFF` |
| `0x22` | `OP_XOR` | `ra, rb` | `r[ra] ^= r[rb]` |
| `0x23` | `OP_ROL` | `reg, bits` | `r[reg] = rol8(r[reg], bits)` |
| `0x24` | `OP_ROR` | `reg, bits` | `r[reg] = ror8(r[reg], bits)` |
| `0x25` | `OP_SBOX` | `reg` | `r[reg] = SBOX[r[reg]]` |
| `0x30` | `OP_ASSERT_EQ`| `reg, target` | Check `r[reg] == target`, else fault |
| `0x3F` | `OP_HALT` | none | Terminate execution |

---

## 2. Disassembling `sigil.enc`

Disassembling `sigil.enc` reveals 4 identical transformation blocks, each operating on 4 consecutive input bytes `[in0, in1, in2, in3]`:

```python
# Block operations:
R0 = rol8(in0, 3)
R1 = SBOX[in1]
R0 ^= R1
R2 = (in2 + R0) & 0xFF
R3 = SBOX[in3] ^ R2
R1 = (R1 + R3) & 0xFF
R2 = rol8(R2, 5)

# Assertions at end of block:
assert R0 == target0
assert R1 == target1
assert R2 == target2
assert R3 == target3
```

---

## 3. Mathematical Inversion

Every operation in the block is strictly bijective over $\mathbb{Z}_{256}$:

1. **Recover `in2`**:
   $$R_2 = \text{rol}_5(in_2 + R_0) = t_2 \implies in_2 + R_0 = \text{ror}_5(t_2)$$
   Since $R_0 = t_0$:
   $$in_2 = (\text{ror}_5(t_2) - t_0) \pmod{256}$$

2. **Recover `in3`**:
   $$R_3 = \text{SBOX}[in_3] \oplus (in_2 + R_0) = t_3 \implies \text{SBOX}[in_3] = t_3 \oplus \text{ror}_5(t_2)$$
   $$in_3 = \text{INV\_SBOX}[t_3 \oplus \text{ror}_5(t_2)]$$

3. **Recover `in1`**:
   $$R_1 = \text{SBOX}[in_1] + R_3 = t_1 \implies \text{SBOX}[in_1] = (t_1 - t_3) \pmod{256}$$
   $$in_1 = \text{INV\_SBOX}[(t_1 - t_3) \pmod{256}]$$

4. **Recover `in0`**:
   $$R_0 = \text{rol}_3(in_0) \oplus \text{SBOX}[in_1] = t_0 \implies \text{rol}_3(in_0) = t_0 \oplus \text{SBOX}[in_1]$$
   $$in_0 = \text{ror}_3(t_0 \oplus \text{SBOX}[in_1])$$

---

## 4. Exploitation

Running `solve.py` extracts the assertions from `sigil.enc`, executes the analytical inversion, finds the required sigil `SIGIL{N1GR3D0_V1CT0R!!}`, transmits it to port 1340, and obtains the flag:

```bash
python3 solution/solve.py 127.0.0.1 1340
```
Flag: `YUVA{d4rkh0ld_4lcamy_v1rtu4l_m4ch1n3_3821}`
