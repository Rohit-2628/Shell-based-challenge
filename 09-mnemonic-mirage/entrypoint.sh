#!/bin/bash
set -e

DEFAULT_FLAG="YUVA{cl34n_l4b3l_tr0j4n_bl1nds_d00ms_c0rt3x_1928}"
export FLAG="${FLAG:-$DEFAULT_FLAG}"
echo "$FLAG" > /flag.txt
chmod 644 /flag.txt

echo "[*] Initializing Mnemonic Mirage Biometric Gateway..."
exec python3 /app/src/mirage_server.py
