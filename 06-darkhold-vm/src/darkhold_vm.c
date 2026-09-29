#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <stdint.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <time.h>

#define PORT 1340
#define SIGIL_LEN 16
#define MAX_BYTECODE 1024

// Custom Arcane S-Box (affine permutation over GF(256))
static const uint8_t ALCHEMICAL_SBOX[256] = {
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
};

// VM State
typedef struct {
    uint8_t r[4];       // R0, R1, R2, R3
    uint8_t input[16];
    uint8_t output[16];
    size_t pc;
    int fault;
} DarkholdVM;

enum Opcode {
    OP_LOAD_IMM   = 0x10, // OP_LOAD_IMM reg, imm
    OP_LOAD_IN    = 0x11, // OP_LOAD_IN reg, idx
    OP_STORE_OUT  = 0x12, // OP_STORE_OUT reg, idx
    OP_ADD        = 0x20, // OP_ADD reg_a, reg_b  -> reg_a = reg_a + reg_b
    OP_SUB        = 0x21, // OP_SUB reg_a, reg_b  -> reg_a = reg_a - reg_b
    OP_XOR        = 0x22, // OP_XOR reg_a, reg_b  -> reg_a = reg_a ^ reg_b
    OP_ROL        = 0x23, // OP_ROL reg, bits     -> reg = rol(reg, bits)
    OP_ROR        = 0x24, // OP_ROR reg, bits     -> reg = ror(reg, bits)
    OP_SBOX       = 0x25, // OP_SBOX reg          -> reg = sbox[reg]
    OP_ASSERT_EQ  = 0x30, // OP_ASSERT_EQ reg, target
    OP_HALT       = 0x3F  // OP_HALT
};

static inline uint8_t rol8(uint8_t v, uint8_t shift) {
    shift &= 7;
    return (v << shift) | (v >> (8 - shift));
}

static inline uint8_t ror8(uint8_t v, uint8_t shift) {
    shift &= 7;
    return (v >> shift) | (v << (8 - shift));
}

int execute_vm(const uint8_t *code, size_t code_len, const uint8_t *input_sigil) {
    DarkholdVM vm;
    memset(&vm, 0, sizeof(vm));
    memcpy(vm.input, input_sigil, 16);

    while (vm.pc < code_len && !vm.fault) {
        uint8_t op = code[vm.pc++];
        if (op == OP_HALT) {
            break;
        }

        switch (op) {
            case OP_LOAD_IMM: {
                if (vm.pc + 2 > code_len) { vm.fault = 1; break; }
                uint8_t reg = code[vm.pc++] & 3;
                uint8_t imm = code[vm.pc++];
                vm.r[reg] = imm;
                break;
            }
            case OP_LOAD_IN: {
                if (vm.pc + 2 > code_len) { vm.fault = 1; break; }
                uint8_t reg = code[vm.pc++] & 3;
                uint8_t idx = code[vm.pc++] & 15;
                vm.r[reg] = vm.input[idx];
                break;
            }
            case OP_STORE_OUT: {
                if (vm.pc + 2 > code_len) { vm.fault = 1; break; }
                uint8_t reg = code[vm.pc++] & 3;
                uint8_t idx = code[vm.pc++] & 15;
                vm.output[idx] = vm.r[reg];
                break;
            }
            case OP_ADD: {
                if (vm.pc + 2 > code_len) { vm.fault = 1; break; }
                uint8_t ra = code[vm.pc++] & 3;
                uint8_t rb = code[vm.pc++] & 3;
                vm.r[ra] = (vm.r[ra] + vm.r[rb]) & 0xFF;
                break;
            }
            case OP_SUB: {
                if (vm.pc + 2 > code_len) { vm.fault = 1; break; }
                uint8_t ra = code[vm.pc++] & 3;
                uint8_t rb = code[vm.pc++] & 3;
                vm.r[ra] = (vm.r[ra] - vm.r[rb]) & 0xFF;
                break;
            }
            case OP_XOR: {
                if (vm.pc + 2 > code_len) { vm.fault = 1; break; }
                uint8_t ra = code[vm.pc++] & 3;
                uint8_t rb = code[vm.pc++] & 3;
                vm.r[ra] ^= vm.r[rb];
                break;
            }
            case OP_ROL: {
                if (vm.pc + 2 > code_len) { vm.fault = 1; break; }
                uint8_t reg = code[vm.pc++] & 3;
                uint8_t bits = code[vm.pc++];
                vm.r[reg] = rol8(vm.r[reg], bits);
                break;
            }
            case OP_ROR: {
                if (vm.pc + 2 > code_len) { vm.fault = 1; break; }
                uint8_t reg = code[vm.pc++] & 3;
                uint8_t bits = code[vm.pc++];
                vm.r[reg] = ror8(vm.r[reg], bits);
                break;
            }
            case OP_SBOX: {
                if (vm.pc + 1 > code_len) { vm.fault = 1; break; }
                uint8_t reg = code[vm.pc++] & 3;
                vm.r[reg] = ALCHEMICAL_SBOX[vm.r[reg]];
                break;
            }
            case OP_ASSERT_EQ: {
                if (vm.pc + 2 > code_len) { vm.fault = 1; break; }
                uint8_t reg = code[vm.pc++] & 3;
                uint8_t tgt = code[vm.pc++];
                if (vm.r[reg] != tgt) {
                    vm.fault = 1;
                }
                break;
            }
            default:
                vm.fault = 1;
                break;
        }
    }

    return (vm.fault == 0);
}

int main(int argc, char **argv) {
    if (argc < 3) {
        printf("Usage: %s <bytecode_file> <SIGIL{...}>\n", argv[0]);
        return 1;
    }

    FILE *f = fopen(argv[1], "rb");
    if (!f) {
        perror("fopen bytecode");
        return 1;
    }
    uint8_t code[MAX_BYTECODE];
    size_t len = fread(code, 1, MAX_BYTECODE, f);
    fclose(f);

    const char *sigil_str = argv[2];
    if (strncmp(sigil_str, "SIGIL{", 6) != 0 || strlen(sigil_str) < 23 || sigil_str[22] != '}') {
        printf("[-] Invalid format! Required: SIGIL{16_BYTES}\n");
        return 1;
    }

    uint8_t raw[16];
    memcpy(raw, sigil_str + 6, 16);

    if (execute_vm(code, len, raw)) {
        printf("[+] TALISMAN RESONANCE ACHIEVED! ACCESS GRANTED.\n");
        return 0;
    } else {
        printf("[-] ALCHEMICAL DIVERGENCE: SIGIL REJECTED BY DARKHOLD CORE.\n");
        return 1;
    }
}
