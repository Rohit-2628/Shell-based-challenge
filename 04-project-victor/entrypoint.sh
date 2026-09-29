#!/bin/bash
set -e

DEFAULT_FLAG="YUVA{d00m_m0d3l_gu4rdr41ls_sh4tt3r3d_b3y0nd_r3p41r_1048}"
export FLAG="${FLAG:-$DEFAULT_FLAG}"

echo "[+] Booting Project VICTOR AI Core..."
echo "[+] Guardrail and Input Classification Matrix: ONLINE"

exec python3 /app/victor_advisor.py
