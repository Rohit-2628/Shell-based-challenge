#!/bin/bash
set -e

DEFAULT_FLAG="YUVA{byz4nt1n3_qu0rum_c0ll4ps3d_by_d0ubl3_p0lygl0t_8831}"
export FLAG="${FLAG:-$DEFAULT_FLAG}"
echo "$FLAG" > /flag.txt
chmod 644 /flag.txt

echo "[*] Initializing Bicameral Tribunal Daemon..."
exec python3 /app/src/tribunal_server.py
