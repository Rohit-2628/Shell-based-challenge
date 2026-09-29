#!/bin/bash
set -e

# Deterministic static fallback flag
STATIC_FLAG="DOOM{t1ck1ng_v4ult_c0r3_s3cur1ty_d3fus3d_9842}"

# Determine and validate candidate flag
CANDIDATE_FLAG="${FLAG:-${DYNAMIC_FLAG:-}}"

# Strip whitespace / newlines
CANDIDATE_FLAG="$(echo -n "$CANDIDATE_FLAG" | tr -d '\r\n' | awk '{$1=$1};1')"

FLAG_REGEX='^DOOM\{[A-Za-z0-9_@!#%&*-]+\}$'

# Flag validation: non-empty, must match standard DOOM{...} pattern
if [[ -n "$CANDIDATE_FLAG" && "$CANDIDATE_FLAG" =~ $FLAG_REGEX ]]; then
    SELECTED_FLAG="$CANDIDATE_FLAG"
    FLAG_MODE="DYNAMIC"
else
    SELECTED_FLAG="$STATIC_FLAG"
    FLAG_MODE="STATIC FALLBACK"
fi

# Organizer status output (never log plaintext flag value)
echo "[vault-init] FLAG MODE: ${FLAG_MODE}"

# Store flag securely in root-only file
echo -n "$SELECTED_FLAG" > /root/flag.txt
chmod 600 /root/flag.txt
chown root:root /root/flag.txt

# Sync root user credentials
echo "root:$SELECTED_FLAG" | chpasswd 2>/dev/null || true

# Platform reporting hook if reporting file/path is requested by infrastructure
if [ -n "${FLAG_REPORT_PATH:-}" ]; then
    echo -n "$SELECTED_FLAG" > "$FLAG_REPORT_PATH" 2>/dev/null || true
fi

# Scrub flag secrets from environment before starting services or player access
unset FLAG DYNAMIC_FLAG CANDIDATE_FLAG SELECTED_FLAG STATIC_FLAG FLAG_REGEX

# Ensure log directory exists for log rotation
mkdir -p /var/log/vault
chmod 755 /var/log/vault

# Start cron daemon
cron

# Start broadcaster in background
python3 /usr/local/bin/broadcaster.py &

# Start countdown timer in background
/usr/local/bin/countdown.sh &

# Start SSH daemon in foreground (PID 1 handler)
exec /usr/sbin/sshd -D
