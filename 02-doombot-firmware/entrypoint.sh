#!/bin/bash
set -e

DEFAULT_FLAG="YUVA{v1ct0r_v0n_d00m_m4st3r_0f_sc13nc3_4nd_m4g1c_9902}"
export FLAG="${FLAG:-$DEFAULT_FLAG}"

echo "[+] Latverian Doombot C2 node booting..."
echo "[+] Active Directive: Loaded"

exec python3 /app/c2_server.py
