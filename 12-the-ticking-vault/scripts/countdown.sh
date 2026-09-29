#!/bin/bash
# Self-destruct countdown. Runs 5-10 minutes (randomized). The player defuses
# it by either deleting TRIGGER_FILE or creating DEFUSED_FILE as root.
set -uo pipefail

TOTAL=$(( (RANDOM % 301) + 300 ))   # 300-600 seconds = 5-10 minutes
REMAINING=$TOTAL
TRIGGER_FILE="/tmp/vault_trigger"
DEFUSED_FILE="/tmp/defused"

touch "$TRIGGER_FILE"
chmod 644 "$TRIGGER_FILE"
echo "[countdown] Vault will incinerate in ${TOTAL}s unless defused."

while [ "$REMAINING" -gt 0 ]; do
    if [ ! -f "$TRIGGER_FILE" ] || [ -f "$DEFUSED_FILE" ]; then
        echo "[countdown] Defused! Timer stopped with ${REMAINING}s remaining."
        exit 0
    fi

    echo "$REMAINING" > /tmp/countdown_remaining
    chmod 644 /tmp/countdown_remaining 2>/dev/null || true
    sleep 1
    REMAINING=$((REMAINING - 1))
done

if [ -f "$TRIGGER_FILE" ] && [ ! -f "$DEFUSED_FILE" ]; then
    echo "[countdown] Time's up. Self-destructing."
    /usr/local/bin/cleanup.sh
fi
