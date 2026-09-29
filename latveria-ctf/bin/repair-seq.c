/*
 * latveria-repair-seq -- SUID root (4755).
 *
 * Never holds the master key or the flag as compiled-in constants; both
 * are read at runtime from root-only (0600) config files that the
 * unprivileged caller cannot open directly, but which this binary can
 * read because its *effective* uid is 0 while it runs.
 *
 * Talks to the Snapshot Watchdog over a root-only (0600) Unix domain
 * socket to apply/refund the 60s guess penalty. Because the socket file
 * permissions gate connect(), only a process with effective uid 0 -- i.e.
 * only this binary, never the caller directly -- can ever reach it.
 *
 * Usage: latveria-repair-seq <master_key_hex>
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <errno.h>

#define FAILSAFE_CONF   "/etc/latveria/failsafe.conf"
#define VAULT_CONF      "/etc/latveria/vault.conf"
#define DISPLAY_PATH    "/run/latveria/display"
#define CTL_SOCK        "/run/latveria/ctl.sock"
#define MAX_LINE        512

/* Constant-time comparison: always walks the full length of the longer
 * buffer so execution time does not leak *where* a mismatch occurred, and
 * does not short-circuit even when lengths differ. */
static int constant_time_eq(const char *a, size_t alen, const char *b, size_t blen) {
    size_t maxlen = alen > blen ? alen : blen;
    unsigned char diff = (unsigned char)(alen != blen);
    for (size_t i = 0; i < maxlen; i++) {
        unsigned char ca = i < alen ? (unsigned char)a[i] : 0;
        unsigned char cb = i < blen ? (unsigned char)b[i] : 0;
        diff |= (ca ^ cb);
    }
    return diff == 0;
}

/* Reads KEY=value out of a small config file. Returns -1 if not found. */
static int read_conf_value(const char *path, const char *key, char *out, size_t outlen) {
    FILE *f = fopen(path, "r");
    if (!f) return -1;
    char line[MAX_LINE];
    size_t keylen = strlen(key);
    int found = -1;
    while (fgets(line, sizeof(line), f)) {
        if (strncmp(line, key, keylen) == 0 && line[keylen] == '=') {
            char *val = line + keylen + 1;
            size_t vlen = strlen(val);
            while (vlen > 0 && (val[vlen-1] == '\n' || val[vlen-1] == '\r')) {
                val[--vlen] = '\0';
            }
            strncpy(out, val, outlen - 1);
            out[outlen - 1] = '\0';
            found = 0;
            break;
        }
    }
    fclose(f);
    return found;
}

/* Very small, tolerant check of "doombot_alive": true|false in the
 * world-readable display file. We deliberately do not link a JSON
 * library for a single boolean field. */
static int doombot_is_alive(void) {
    FILE *f = fopen(DISPLAY_PATH, "r");
    if (!f) return 1; /* fail safe: assume alive, refuse to proceed */
    char buf[512];
    size_t n = fread(buf, 1, sizeof(buf) - 1, f);
    fclose(f);
    buf[n] = '\0';
    char *pos = strstr(buf, "\"doombot_alive\"");
    if (!pos) return 1;
    return strstr(pos, "true") != NULL;
}

/* Sends a single command to the watchdog over the control socket and
 * returns its raw text response in out (best-effort, not parsed beyond
 * what the caller needs). Returns 0 on success. */
static int ctl_request(const char *cmd, char *out, size_t outlen) {
    int fd = socket(AF_UNIX, SOCK_STREAM, 0);
    if (fd < 0) return -1;

    struct sockaddr_un addr;
    memset(&addr, 0, sizeof(addr));
    addr.sun_family = AF_UNIX;
    strncpy(addr.sun_path, CTL_SOCK, sizeof(addr.sun_path) - 1);

    if (connect(fd, (struct sockaddr *)&addr, sizeof(addr)) != 0) {
        close(fd);
        return -1;
    }
    send(fd, cmd, strlen(cmd), 0);
    ssize_t n = recv(fd, out, outlen - 1, 0);
    close(fd);
    if (n < 0) return -1;
    out[n] = '\0';
    return 0;
}

static void print_hex_flag(const char *flag) {
    printf("[DUMP] Core registers:\n");
    for (size_t i = 0; flag[i] != '\0'; i++) {
        printf("\\x%02x", (unsigned char)flag[i]);
    }
    printf("\n");
}

int main(int argc, char **argv) {
    if (argc != 2) {
        fprintf(stderr, "usage: %s <master_key>\n", argv[0]);
        return 2;
    }

    if (doombot_is_alive()) {
        printf("[REFUSED] Doombot is actively heartbeating. Containment stable.\n");
        printf("[REFUSED] Repair sequence unavailable while defenses are active.\n");
        return 1;
    }

    char master_key[MAX_LINE];
    if (read_conf_value(FAILSAFE_CONF, "MASTER_KEY", master_key, sizeof(master_key)) != 0) {
        fprintf(stderr, "[ERROR] Internal state unavailable.\n");
        return 1;
    }

    const char *supplied = argv[1];
    if (!constant_time_eq(supplied, strlen(supplied), master_key, strlen(master_key))) {
        printf("[FAIL] Master Authentication Key rejected.\n");
        return 1;
    }

    char flag[MAX_LINE];
    if (read_conf_value(VAULT_CONF, "FLAG", flag, sizeof(flag)) != 0) {
        fprintf(stderr, "[ERROR] Internal state unavailable.\n");
        return 1;
    }

    printf("[OK] Master Authentication Key Accepted.\n");
    printf("[INFO] Emergency diagnostic dump initiated ahead of scheduled snapshot revert...\n");
    print_hex_flag(flag);
    printf("[INPUT REQUIRED] Enter recovered core signature to confirm systems nominal: ");
    fflush(stdout);

    char input[MAX_LINE];
    if (!fgets(input, sizeof(input), stdin)) {
        printf("\n[ERROR] No input received.\n");
        return 1;
    }
    size_t ilen = strlen(input);
    while (ilen > 0 && (input[ilen-1] == '\n' || input[ilen-1] == '\r')) {
        input[--ilen] = '\0';
    }

    /* Commit the penalty BEFORE the throttle sleep and BEFORE evaluating
     * the guess. This is deliberate: it means killing this process during
     * the sleep window below can never dodge the 60s cost of a guess that
     * turns out wrong. A correct guess gets the 60s refunded after we
     * confirm the match, below. */
    char ctl_resp[128];
    int remaining = -1;
    if (ctl_request("BEGIN", ctl_resp, sizeof(ctl_resp)) == 0) {
        char *p = strstr(ctl_resp, "remaining_seconds\":");
        if (p) remaining = atoi(p + strlen("remaining_seconds\":"));
    }

    sleep(3); /* throttle */

    if (constant_time_eq(input, ilen, flag, strlen(flag))) {
        ctl_request("REFUND", ctl_resp, sizeof(ctl_resp));
        ctl_request("DISARM", ctl_resp, sizeof(ctl_resp));
        printf("[OK] Systems verified online. Snapshot revert cancelled.\n");
        printf("[HALT] Containment breach logged. Sequence complete.\n");
        return 0;
    } else {
        printf("[FAIL] Recovery signature invalid.\n");
        if (remaining >= 0) {
            printf("[WARNING] -60s applied. Clock remaining: %dm %02ds\n",
                   remaining / 60, remaining % 60);
        }
        return 1;
    }
}
