#!/usr/bin/env python3
"""
Bytecode compiler and generator for Darkhold VM.
Builds the 32-instruction alchemical transformation sequence and emits sigil.enc.
"""
import os

ALCHEMICAL_SBOX = [
    0x63, 0x7c, 0x77, 0x7b, 0xf2, 0x6b, 0x6f, 0xc5, 0x30, 0x01, 0x67, 0x2b, 0xfe, 0xd7, 0xab, 0x76,
    0xca, 0x82, 0xc9, 0x7d, 0xfa, 0x59, 0x47, 0xf0, 0xad, 0xd4, 0xa2, 0xaf, 0x9c, 0xa4, 0x72, 0xc0,
    0xb7, 0xfd, 0x93, 0x26, 0x36, 0x3f, 0xf7, 0xcc, 0x34, 0xa5, 0xe5, 0xf1, 0x71, 0xd8, 0x31, 0x15,
    0x04, 0xc7, 0x23, 0xc3, 0x18, 0x96, 0x05, 0x9a, 0x07, 0x12, 0x80, 0xe2, 0xeb, 0x27, 0xb2, 0x75,
    0x09, 0x83, 0x2c, 0x1a, 0x1b, 0x6e, 0x5a, 0xa0, 0x52, 0x3b, 0xd6, 0xb3, 0x29, 0xe3, 0x2f, 0x84,
    0x53, 0xd1, 0x00, 0xed, 0x20, 0xfc, 0xb1, 0x5b, 0x6a, 0xcb, 0xbe, 0x39, 0x4a, 0x4c, 0x58, 0xcf,
    0xd0, 0xef, 0xaa, 0xfb, 0x43, 0x4d, 0x33, 0x85, 0x45, 0xf9, 0x02, 0x7f, 0x50, 0x3c, 0x9f, 0xa8,
    0x51, 0xa3, 0x40, 0x8f, 0x92, 0x9d, 0x38, 0xf5, 0xbc, 0xb6, 0xda, 0x21, 0x10, 0xff, 0xf3, 0xd2,
    0xcd, 0x0c, 0x13, 0xec, 0x5f, 0x97, 0x44, 0x17, 0xc4, 0xa7, 0x7e, 0x3d, 0x64, 0x5d, 0x19, 0x73,
    0x60, 0x81, 0x4f, 0xdc, 0x22, 0x2a, 0x90, 0x88, 0x46, 0xee, 0xb8, 0x14, 0xde, 0x5e, 0x0b, 0xdb,
    0xe0, 0x32, 0x3a, 0x0a, 0x49, 0x06, 0x24, 0x5c, 0xc2, 0xd3, 0xac, 0x62, 0x91, 0x95, 0xe4, 0x79,
    0xe7, 0xc8, 0x37, 0x6d, 0x8d, 0xd5, 0x4e, 0xa9, 0x6c, 0x56, 0xf4, 0xea, 0x65, 0x7a, 0xae, 0x08,
    0xba, 0x78, 0x25, 0x2e, 0x1c, 0xa6, 0xb4, 0xc6, 0xe8, 0xdd, 0x74, 0x1f, 0x4b, 0xbd, 0x8b, 0x8a,
    0x70, 0x3e, 0xb5, 0x66, 0x48, 0x03, 0xf6, 0x0e, 0x61, 0x35, 0x57, 0xb9, 0x86, 0xc1, 0x1d, 0x9e,
    0xe1, 0xf8, 0x98, 0x11, 0x69, 0xd9, 0x8e, 0x94, 0x9b, 0x1e, 0x87, 0xe9, 0xce, 0x55, 0x28, 0xdf,
    0x8c, 0xa1, 0x89, 0x0d, 0xbf, 0xe6, 0x42, 0x68, 0x41, 0x99, 0x2d, 0x0f, 0xb0, 0x54, 0xbb, 0x16
]

INV_SBOX = [0] * 256
for i, v in enumerate(ALCHEMICAL_SBOX):
    INV_SBOX[v] = i

OP_LOAD_IMM   = 0x10
OP_LOAD_IN    = 0x11
OP_STORE_OUT  = 0x12
OP_ADD        = 0x20
OP_SUB        = 0x21
OP_XOR        = 0x22
OP_ROL        = 0x23
OP_ROR        = 0x24
OP_SBOX       = 0x25
OP_ASSERT_EQ  = 0x30
OP_HALT       = 0x3F

SECRET_SIGIL = b"N1GR3D0_V1CT0R!!" # 16 bytes

def rol8(v, shift):
    shift &= 7
    return ((v << shift) | (v >> (8 - shift))) & 0xFF

def ror8(v, shift):
    shift &= 7
    return ((v >> shift) | (v << (8 - shift))) & 0xFF

def build_bytecode(target_sigil):
    bytecode = bytearray()
    
    # Process 4 blocks of 4 bytes: [4*k, 4*k+1, 4*k+2, 4*k+3]
    # For each block:
    # R0 = in[4k], R1 = in[4k+1], R2 = in[4k+2], R3 = in[4k+3]
    # R0 = (R0 ^ 0x5D) + 0x37
    # R1 = rol(R1, 3) ^ R0
    # R2 = SBOX[R2] ^ R1
    # R3 = (R3 + R2) ^ 0xA5
    # Then cross-mix:
    # R0 = R0 ^ R3
    # R1 = (R1 + R0) & 0xFF
    # R2 = ror(R2 ^ R1, 2)
    # R3 = SBOX[R3] ^ R2
    
    expected_outputs = []
    
    for block in range(4):
        base = block * 4
        # Load inputs into R0, R1, R2, R3
        bytecode.extend([OP_LOAD_IN, 0, base])
        bytecode.extend([OP_LOAD_IN, 1, base + 1])
        bytecode.extend([OP_LOAD_IN, 2, base + 2])
        bytecode.extend([OP_LOAD_IN, 3, base + 3])
        
        # R0 = (R0 ^ 0x5D) + 0x37
        bytecode.extend([OP_LOAD_IMM, 3, 0x5D])
        bytecode.extend([OP_XOR, 0, 3])
        bytecode.extend([OP_LOAD_IMM, 3, 0x37])
        bytecode.extend([OP_ADD, 0, 3])
        
        # R1 = rol(R1, 3) ^ R0
        bytecode.extend([OP_ROL, 1, 3])
        bytecode.extend([OP_XOR, 1, 0])
        
        # R2 = SBOX[R2] ^ R1
        bytecode.extend([OP_SBOX, 2])
        bytecode.extend([OP_XOR, 2, 1])
        
        # R3 = (R3 + R2) ^ 0xA5
        bytecode.extend([OP_ADD, 3, 2])
        bytecode.extend([OP_LOAD_IMM, 2, 0xA5]) # note: temp using reg 2? Wait! R2 was used above!
        # To avoid clobbering R2, let's use a cleaner sequence:
        pass

    # Let's write a very clean, modular macro generation:
    bytecode = bytearray()
    targets = []
    
    for b in range(4):
        idx0, idx1, idx2, idx3 = b*4, b*4+1, b*4+2, b*4+3
        r0 = target_sigil[idx0]
        r1 = target_sigil[idx1]
        r2 = target_sigil[idx2]
        r3 = target_sigil[idx3]
        
        # Op 1: R0 = (R0 ^ 0x4A)
        # Op 2: R0 = (R0 + 0x1B) & 0xFF
        # Op 3: R1 = rol(R1, 3) ^ R0
        # Op 4: R2 = SBOX[R2]
        # Op 5: R2 = R2 ^ R1
        # Op 6: R3 = (R3 + R2) & 0xFF
        # Op 7: R3 = R3 ^ 0x7E
        # Op 8: R0 = R0 ^ R3
        
        # Bytecode instructions:
        # Load inputs
        bytecode.extend([OP_LOAD_IN, 0, idx0])
        bytecode.extend([OP_LOAD_IN, 1, idx1])
        bytecode.extend([OP_LOAD_IN, 2, idx2])
        bytecode.extend([OP_LOAD_IN, 3, idx3])
        
        # R0 = (R0 ^ 0x4A) + 0x1B
        # Load imm into scratch? Wait, we can do:
        # We don't have scratch, but we can do OP_ADD with imm if we have it, or load imm into R0 using XOR/ADD:
        # Wait, OP_LOAD_IMM loads into a reg. If all 4 regs hold values, we can mix them directly!
        # Look at how elegant this is:
        # 1. R0 = rol(R0, 3)
        # 2. R1 = SBOX[R1]
        # 3. R0 = R0 ^ R1
        # 4. R2 = (R2 + R0) & 0xFF
        # 5. R3 = SBOX[R3]
        # 6. R3 = R3 ^ R2
        # 7. R1 = (R1 + R3) & 0xFF
        # 8. R2 = rol(R2, 5)
        # This uses NO scratch registers, only R0..R3 and imm constants for ROL!
        pass
        
    return bytecode

def generate_challenge():
    sigil = SECRET_SIGIL
    bytecode = bytearray()
    
    # 4 blocks of 4 bytes
    for b in range(4):
        i0, i1, i2, i3 = b*4, b*4+1, b*4+2, b*4+3
        r0, r1, r2, r3 = sigil[i0], sigil[i1], sigil[i2], sigil[i3]
        
        # 1. Load inputs
        bytecode.extend([OP_LOAD_IN, 0, i0])
        bytecode.extend([OP_LOAD_IN, 1, i1])
        bytecode.extend([OP_LOAD_IN, 2, i2])
        bytecode.extend([OP_LOAD_IN, 3, i3])
        
        # 2. Transform block
        # R0 = rol(R0, 3)
        bytecode.extend([OP_ROL, 0, 3])
        r0 = rol8(r0, 3)
        
        # R1 = SBOX[R1]
        bytecode.extend([OP_SBOX, 1])
        r1 = ALCHEMICAL_SBOX[r1]
        
        # R0 = R0 ^ R1
        bytecode.extend([OP_XOR, 0, 1])
        r0 ^= r1
        
        # R2 = (R2 + R0) & 0xFF
        bytecode.extend([OP_ADD, 2, 0])
        r2 = (r2 + r0) & 0xFF
        
        # R3 = SBOX[R3]
        bytecode.extend([OP_SBOX, 3])
        r3 = ALCHEMICAL_SBOX[r3]
        
        # R3 = R3 ^ R2
        bytecode.extend([OP_XOR, 3, 2])
        r3 ^= r2
        
        # R1 = (R1 + R3) & 0xFF
        bytecode.extend([OP_ADD, 1, 3])
        r1 = (r1 + r3) & 0xFF
        
        # R2 = rol(R2, 5)
        bytecode.extend([OP_ROL, 2, 5])
        r2 = rol8(r2, 5)
        
        # Assertions
        bytecode.extend([OP_ASSERT_EQ, 0, r0])
        bytecode.extend([OP_ASSERT_EQ, 1, r1])
        bytecode.extend([OP_ASSERT_EQ, 2, r2])
        bytecode.extend([OP_ASSERT_EQ, 3, r3])

    bytecode.append(OP_HALT)
    return bytecode

if __name__ == "__main__":
    bc = generate_challenge()
    out_dir = os.path.dirname(os.path.abspath(__file__))
    enc_path = os.path.join(out_dir, "sigil.enc")
    with open(enc_path, "wb") as f:
        f.write(bc)
    print(f"[+] Emitted {len(bc)} bytes of Darkhold VM bytecode to {enc_path}")
    
    # Also copy to handouts
    handout_enc = os.path.join(out_dir, "..", "handouts", "sigil.enc")
    with open(handout_enc, "wb") as f:
        f.write(bc)
    print(f"[+] Copied to {handout_enc}")
