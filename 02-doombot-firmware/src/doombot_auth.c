/*
 * DOOMBOT FIRMWARE ACTIVATION MODULE v4.2
 * PROPERTY OF LATVERIA MINISTRY OF DEFENSE
 * CONFIDENTIAL AND PROPRIETARY TO DOCTOR VICTOR VON DOOM
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <unistd.h>
#include <sys/ptrace.h>
#include <ctype.h>

static const uint8_t DOOM_KEY[16] = "LATVERIA_VICTOR!";
static const uint8_t PERMUTATION_MAP[16] = {
    7, 2, 15, 0, 11, 4, 13, 8, 1, 14, 3, 10, 5, 12, 9, 6
};

// Anti-debugging verification routine
static int check_debugger(void) {
    FILE *f = fopen("/proc/self/status", "r");
    if (f) {
        char line[128];
        int tracer_pid = 0;
        while (fgets(line, sizeof(line), f)) {
            if (strncmp(line, "TracerPid:", 10) == 0) {
                tracer_pid = atoi(line + 10);
                break;
            }
        }
        fclose(f);

        if (tracer_pid > 0) {
            char path[64];
            snprintf(path, sizeof(path), "/proc/%d/comm", tracer_pid);
            FILE *comm_f = fopen(path, "r");
            if (comm_f) {
                char comm[64];
                if (fgets(comm, sizeof(comm), comm_f)) {
                    // Check if tracer is an interactive debugger / tracer
                    if (strstr(comm, "gdb") || strstr(comm, "lldb") ||
                        strstr(comm, "strace") || strstr(comm, "ltrace") ||
                        strstr(comm, "r2") || strstr(comm, "ida")) {
                        fclose(comm_f);
                        return 1;
                    }
                }
                fclose(comm_f);
            }
        }
    }
    return 0;
}

static uint8_t hex_char_to_val(char c) {
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    return 0;
}

// Compute the 32-hex Doombot authorization signature from an 8-byte nonce
void compute_doombot_signature(const uint8_t *nonce, char *output_hex) {
    uint8_t expanded[16];
    uint8_t permuted[16];
    uint8_t output_bytes[16];

    // Stage 1: Keyed Expansion & Bit-Twiddling
    for (int i = 0; i < 8; i++) {
        uint8_t b = nonce[i];
        expanded[2 * i] = (uint8_t)((b ^ DOOM_KEY[2 * i]) + 0x37);
        uint8_t ror = (uint8_t)((b >> 3) | (b << 5));
        expanded[2 * i + 1] = (uint8_t)(ror ^ DOOM_KEY[2 * i + 1]);
    }

    // Stage 2: Permutation mapping
    for (int i = 0; i < 16; i++) {
        permuted[i] = expanded[PERMUTATION_MAP[i]];
    }

    // Stage 3: Rolling CBC-like feedback transformation
    output_bytes[0] = (uint8_t)(permuted[0] ^ 0x5D);
    for (int i = 1; i < 16; i++) {
        output_bytes[i] = (uint8_t)(((permuted[i] + output_bytes[i - 1]) & 0xFF) ^ 0xAA);
    }

    // Encode to 32-character hexadecimal string
    for (int i = 0; i < 16; i++) {
        sprintf(output_hex + (i * 2), "%02x", output_bytes[i]);
    }
    output_hex[32] = '\0';
}

int main(int argc, char *argv[]) {
    printf("============================================================\n");
    printf("[*] DOOMBOT UNIT v4.2 - SECURE ACTIVATION SUITE\n");
    printf("[*] LATVERIAN MILITARY STANDARD 904-B\n");
    printf("============================================================\n");

    if (check_debugger()) {
        printf("[!] INTRUSION DETECTED: Tamper flag raised. Neural link severed.\n");
        return 137;
    }

    if (argc < 3) {
        printf("Usage: %s <16-hex-nonce> <32-hex-response>\n", argv[0]);
        printf("Example: %s 0123456789abcdef 4a8f90...\n", argv[0]);
        return 1;
    }

    const char *nonce_str = argv[1];
    const char *resp_str = argv[2];

    if (strlen(nonce_str) != 16 || strlen(resp_str) != 32) {
        printf("[-] Error: Nonce must be 16 hex chars; Response must be 32 hex chars.\n");
        return 1;
    }

    uint8_t nonce_bytes[8];
    for (int i = 0; i < 8; i++) {
        nonce_bytes[i] = (uint8_t)((hex_char_to_val(nonce_str[2 * i]) << 4) |
                                    hex_char_to_val(nonce_str[2 * i + 1]));
    }

    char expected_resp[33];
    compute_doombot_signature(nonce_bytes, expected_resp);

    if (strcasecmp(resp_str, expected_resp) == 0) {
        printf("[+] AUTHENTICATION SUCCESSFUL!\n");
        printf("[+] Doombot unit operational. Latverian sovereignty preserved.\n");
        return 0;
    } else {
        printf("[-] AUTHENTICATION FAILED!\n");
        printf("[-] Invalid signature for nonce %s.\n", nonce_str);
        return 2;
    }
}
