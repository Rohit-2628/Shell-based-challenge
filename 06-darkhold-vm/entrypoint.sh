#!/bin/bash
set -e

DEFAULT_FLAG="YUVA{d4rkh0ld_4lcamy_v1rtu4l_m4ch1n3_3821}"
export FLAG="${FLAG:-$DEFAULT_FLAG}"
echo "$FLAG" > /flag.txt
chmod 644 /flag.txt

echo "[*] Initializing Darkhold Arcane VM Service..."
exec python3 /app/src/darkhold_server.py
