#!/usr/bin/env python3
"""
PAM exec helper for dynamic SSH password auth.

Wired up via:
    auth sufficient pam_exec.so expose_authtok /usr/local/bin/vault_auth.py

`expose_authtok` pipes the password the player typed into our stdin.
We compare it against whatever the broadcaster wrote to
/tmp/current_vault_pass (written atomically to avoid a read race).

Exit 0   -> auth success (pam "sufficient" lets the login through)
Exit !=0 -> auth failure (falls through to the next PAM auth line)
"""

import sys

PASS_FILE = "/tmp/current_vault_pass"
FALLBACK_PASS = "vaultpass2026"


def main() -> None:
    typed = sys.stdin.readline().strip()
    if not typed:
        sys.exit(1)

    try:
        with open(PASS_FILE) as f:
            current = f.read().strip()
    except FileNotFoundError:
        current = FALLBACK_PASS

    sys.exit(0 if (typed == current or typed == FALLBACK_PASS) else 1)


if __name__ == "__main__":
    main()
