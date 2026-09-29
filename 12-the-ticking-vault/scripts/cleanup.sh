#!/bin/bash
# Executed by countdown.sh when the timer reaches 0.
# Destroys vault state and terminates the container.
set -uo pipefail

echo "[cleanup] Vault self-destruct initiated. Incinerating vault contents..."
pkill -9 sshd 2>/dev/null || true
pkill -9 -f broadcaster.py 2>/dev/null || true
pkill -9 cron 2>/dev/null || true
shred -u /tmp/current_vault_pass 2>/dev/null || true
rm -f /root/flag.txt 2>/dev/null || true

echo "[cleanup] Vault destroyed."
# Exit main container process
kill 1 2>/dev/null || exit 0
