#!/bin/bash
set -e

DEFAULT_FLAG="YUVA{4dv3rs4r14l_p3rturb4t10n_bl1nds_d00ms_s3ns0rs_8271}"
export FLAG="${FLAG:-$DEFAULT_FLAG}"

echo "[+] Aegis-Doom Airspace Security Grid initializing..."
echo "[+] Computer Vision Classifier: ONLINE on port 8000"

exec python3 /app/server.py
