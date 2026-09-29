#!/bin/bash
set -e

DEFAULT_FLAG="YUVA{z3r0_c0py_t3l3m3try_r3fl3ct10n_d00m_c0r3_8492}"
export FLAG="${FLAG:-$DEFAULT_FLAG}"
echo "$FLAG" > /flag.txt
chmod 644 /flag.txt

echo "[*] Initializing Chrono-Telemetry Daemon..."
exec python3 /app/src/chrono_server.py
