#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

#define GOLD  "\033[38;5;178m"
#define RED   "\033[1;31m"
#define RESET "\033[0m"

static const char *TAUNTS[] = {
    "INCORRECT. LATVERIA DOES NOT REWARD GUESSWORK.",
    "WRONG. TRY AGAIN, IF YOU DARE.",
    "DENIED. THE STATE ARCHIVE REMAINS SEALED.",
    "A FAILED ATTEMPT IS NOW LOGGED."
};
#define NUM_TAUNTS (int)(sizeof(TAUNTS) / sizeof(TAUNTS[0]))

static void type_out(const char *text, useconds_t delay_us) {
    for (size_t i = 0; i < strlen(text); i++) {
        putchar(text[i]);
        fflush(stdout);
        usleep(delay_us);
    }
    putchar('\n');
}

int main(void) {
    char input[256];

    printf(GOLD "=== LATVERIAN STATE ARCHIVE — VAULT TERMINAL ===" RESET "\n");
    printf("Enter decryption key: ");
    fflush(stdout);

    if (!fgets(input, sizeof(input), stdin)) {
        return 1;
    }
    input[strcspn(input, "\n")] = '\0';

    time_t now = time(NULL);
    struct tm tmnow;
    localtime_r(&now, &tmnow);

    int cur_min  = tmnow.tm_min;
    int prev_min = (cur_min + 59) % 60;
    int next_min = (cur_min + 1) % 60;

    char expected_cur[16], expected_prev[16], expected_next[16];
    snprintf(expected_cur,  sizeof(expected_cur),  "doom_%02d", cur_min);
    snprintf(expected_prev, sizeof(expected_prev), "doom_%02d", prev_min);
    snprintf(expected_next, sizeof(expected_next), "doom_%02d", next_min);

    if (strcmp(input, expected_cur) == 0 ||
        strcmp(input, expected_prev) == 0 ||
        strcmp(input, expected_next) == 0) {

        if (system("clear") != 0) { /* non-fatal */ }
        if (system("cat /opt/latveria_assets/vault_reveal.ansi") != 0) { /* non-fatal */ }
        printf("\n");
        type_out("THIS WAS NEVER A STATE SERVER.", 30000);
        type_out("YOU ARE STANDING IN MY DOMAIN.", 30000);
        printf("\n");
        printf(RED "[!] LATVERIAN DEFENSE GRID ARMED." RESET "\n");
        printf(GOLD "[!] TIME REMAINING: 20 MINUTES" RESET "\n");
        printf("Escalate, find the override flag, and run ./abort_destruct to survive.\n");

        // Signal the root-owned watchdog to start the real countdown and
        // lock this vault out - only root can do that, this binary can't
        // chmod itself.
        FILE *f = fopen("/tmp/.armed", "w");
        if (f) fclose(f);

    } else {
        srand((unsigned int)time(NULL) ^ (unsigned int)getpid());
        printf(RED "[-] %s" RESET "\n", TAUNTS[rand() % NUM_TAUNTS]);
    }

    return 0;
}
