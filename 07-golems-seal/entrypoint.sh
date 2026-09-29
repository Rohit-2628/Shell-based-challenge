#!/bin/bash
set -e

DEFAULT_FLAG="YUVA{p0st_qu4ntum_l4tt1c3_g0l3m_d1s4rm3d_5829}"
export FLAG="${FLAG:-$DEFAULT_FLAG}"
echo "$FLAG" > /flag.txt
chmod 644 /flag.txt

echo "[*] Initializing Golem Lattice Daemon..."
exec python3 /app/src/golem_server.py
