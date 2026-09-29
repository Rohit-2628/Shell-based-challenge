#!/bin/bash
# Rotates vault log files. Runs every minute as root via /etc/cron.d/vault-cron.
#
# NOTE: this file is intentionally world-writable (chmod 777) — that's the
# misconfiguration the player is meant to find and exploit for priv-esc.

LOG_DIR="/var/log/vault"
mkdir -p "$LOG_DIR"
find "$LOG_DIR" -type f -mtime +1 -delete
echo "$(date): log rotation check complete" >> "$LOG_DIR/rotate.log"
