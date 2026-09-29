#!/bin/bash
set -euo pipefail

echo "[*] Initializing D29 — Cloud Mirror Challenge..."

# 1. Setup Flag securely
DEFAULT_FLAG="YUVA{cl0ud_m1rr0r_ssrf_m3t4d4t4_0bj_st0r3_7a9e2f}"
FLAG_VALUE="${FLAG:-$DEFAULT_FLAG}"
mkdir -p /opt/storage
echo "${FLAG_VALUE}" > /opt/storage/flag.txt
chown -R storage:storage /opt/storage
chmod 700 /opt/storage
chmod 400 /opt/storage/flag.txt

# Unset and clear FLAG variable from environment to prevent env leaks
unset FLAG || true
export -n FLAG || true

# 2. Seed Mock Object Store if empty
if [ ! -d "/var/lib/latveria-storage/public-assets" ]; then
    echo "[*] Generating synthetic mock object storage buckets..."
    python3 /challenge/object_store/seed_data.py /var/lib/latveria-storage
fi
chown -R storage:storage /var/lib/latveria-storage
chmod -R 755 /var/lib/latveria-storage

# 3. Start Mock Metadata Service Daemon (user: metadata) on 127.0.0.1:8181
echo "[*] Starting Mock Metadata Service daemon (user: metadata)..."
su -s /bin/bash metadata -c "python3 /challenge/metadata_service/metadata_server.py --host 127.0.0.1 --port 8181" >/var/log/metadata-server.log 2>&1 &

# 4. Start Mock Object Storage Daemon (user: storage) on 127.0.0.1:9000
echo "[*] Starting Mock Object Store daemon (user: storage)..."
su -s /bin/bash storage -c "python3 /challenge/object_store/object_store_server.py --host 127.0.0.1 --port 9000 --storage /var/lib/latveria-storage" >/var/log/storage-server.log 2>&1 &

# 5. Start Image Fetcher / Web App (user: mirrorapp) on 127.0.0.1:8000
echo "[*] Starting Cloud Mirror Web Application (user: mirrorapp)..."
su -s /bin/bash mirrorapp -c "python3 /challenge/app/server.py --host 127.0.0.1 --port 8000" >/var/log/mirrorapp-server.log 2>&1 &

sleep 0.5

# 6. Start Nginx on Port 80 in foreground
echo "[*] Starting Nginx HTTP gateway on TCP/80..."
exec nginx -g "daemon off;"
