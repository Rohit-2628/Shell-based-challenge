#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <sys/stat.h>

#define GREEN "\033[38;5;35m"
#define GOLD  "\033[38;5;178m"
#define RED   "\033[1;31m"
#define RESET "\033[0m"

static const char *TAUNTS[] = {
    "ACCESS DENIED. DOOM LAUGHS AT YOUR ATTEMPT.",
    "WRONG. THE GRID REMAINS ARMED.",
    "THAT IS NOT THE FLAG I AM LOOKING FOR."
};
#define NUM_TAUNTS (int)(sizeof(TAUNTS) / sizeof(TAUNTS[0]))

static int file_exists(const char *path) {
    return access(path, F_OK) == 0;
}

// Hash `input` via the real sha256sum binary, writing input to a fixed,
// non-attacker-controlled temp path first (never interpolated into a
// shell string) so there is no injection surface from what the player
// typed.
static int sha256_of(const char *input, char *out_hex, size_t out_len) {
    (void)out_len;
    char tmp_path[64];
    snprintf(tmp_path, sizeof(tmp_path), "/tmp/.vault_guess_%d", getpid());

    FILE *f = fopen(tmp_path, "w");
    if (!f) return -1;
    fputs(input, f);
    fclose(f);

    char cmd[128];
    snprintf(cmd, sizeof(cmd), "sha256sum %s", tmp_path);

    FILE *p = popen(cmd, "r");
    if (!p) {
        remove(tmp_path);
        return -1;
    }
    char line[256] = {0};
    if (!fgets(line, sizeof(line), p)) {
        pclose(p);
        remove(tmp_path);
        return -1;
    }
    pclose(p);
    remove(tmp_path);

    // sha256sum output: "<64 hex chars>  <path>\n"
    if (strlen(line) < 64) return -1;
    strncpy(out_hex, line, 64);
    out_hex[64] = '\0';
    return 0;
}

int main(void) {
    char input[512];

    if (!file_exists("/tmp/.armed") && !file_exists("/tmp/.destruct_end")) {
        printf("THE DEFENSE GRID IS NOT ARMED.\n");
        return 1;
    }

    printf(RED "[!] LATVERIAN DEFENSE GRID — OVERRIDE TERMINAL [!]" RESET "\n");
    printf("ENTER ROOT-LEVEL OVERRIDE FLAG: ");
    fflush(stdout);

    if (!fgets(input, sizeof(input), stdin)) {
        return 1;
    }
    input[strcspn(input, "\n")] = '\0';

    char local_hash[65];
    if (sha256_of(input, local_hash, sizeof(local_hash)) != 0) {
        printf(RED "[-] Internal error hashing input." RESET "\n");
        return 1;
    }

    FILE *secret = fopen("/etc/.doom_secret", "r");
    char expected_hash[128] = {0};
    if (secret) {
        if (!fgets(expected_hash, sizeof(expected_hash), secret)) {
            expected_hash[0] = '\0';
        }
        fclose(secret);
        expected_hash[strcspn(expected_hash, "\n")] = '\0';
    }

    if (expected_hash[0] != '\0' && strcmp(local_hash, expected_hash) == 0) {
        // Hand the guess to the root watchdog for authoritative verification -
        // this local check is only for instant feedback, it cannot itself
        // disarm the timer.
        FILE *f = fopen("/tmp/.disarm_attempt", "w");
        if (f) {
            fputs(input, f);
            fclose(f);
            chmod("/tmp/.disarm_attempt", 0600);
        }

        for (int i = 0; i < 10; i++) {
            if (file_exists("/tmp/.disarmed")) break;
            usleep(500000);
        }

        if (system("clear") != 0) { /* non-fatal */ }
        printf(GREEN
            " ________  ________  ________  _____ ______\n"
            "|\\   ___ \\|\\   __  \\|\\   __  \\|\\   _ \\  _   \\\n"
            "\\ \\  \\_|\\ \\ \\  \\|\\  \\ \\  \\|\\  \\ \\  \\\\\\__\\ \\  \\\n"
            " \\ \\  \\ \\\\ \\ \\  \\\\\\  \\ \\  \\\\\\  \\ \\  \\\\|__| \\  \\\n"
            "  \\ \\  \\_\\\\ \\ \\  \\\\\\  \\ \\  \\\\\\  \\ \\  \\    \\ \\  \\\n"
            "   \\ \\_______\\ \\_______\\ \\_______\\ \\__\\    \\ \\__\\\n"
            "    \\|_______|\\|_______|\\|_______|\\|__|     \\|__|\n"
            RESET "\n");
        printf(GREEN "[+] DEFENSE GRID DISARMED. YOU HAVE SURVIVED LATVERIA... FOR NOW." RESET "\n\n");
        printf(GOLD "FLAG: %s" RESET "\n", input);
        printf("Submit the flag above to the scoreboard.\n");
    } else {
        srand((unsigned int)time(NULL) ^ (unsigned int)getpid());
        printf(RED "[-] %s" RESET "\n", TAUNTS[rand() % NUM_TAUNTS]);
    }

    return 0;
}
