#!/bin/bash
set -e

DEFAULT_FLAG="YUVA{h4ck1ng_th3_l4tv3r14n_d1pl0m4t1c_w1r3_5183}"
export FLAG="${FLAG:-$DEFAULT_FLAG}"

echo "[+] Starting Latverian Embassy Diplomatic Relay..."
echo "[+] Protocol DOOM-NET/2.0 active on port 8042"

exec python3 /app/embassy_relay.py
