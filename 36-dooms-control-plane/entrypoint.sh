#!/bin/bash
set -e

APP_DIR="${APP_DIR:-$(cd "$(dirname "$0")" && pwd)}"

echo "[*] Initializing Latveria Citadel // Doom's Control Plane (Challenge X06)..."

# 1. Start Isolated Flag Service on 127.0.0.1:8084
echo "[+] Starting Isolated Sovereign Flag Vault on 127.0.0.1:8084..."
python3 "${APP_DIR}/challenge/flag_service/flag_server.py" &
FLAG_PID=$!

# 2. Start Workload Manager Simulator (WMS) on 127.0.0.1:8082
echo "[+] Starting Workload Manager Simulator (WMS) on 127.0.0.1:8082..."
python3 "${APP_DIR}/challenge/workload_manager/wms_daemon.py" &
WMS_PID=$!

# 3. Start Sovereign Core Service on 127.0.0.1:8083
echo "[+] Starting Sovereign Core Service on 127.0.0.1:8083..."
python3 "${APP_DIR}/challenge/core_service/core_server.py" &
CORE_PID=$!

# 4. Start Synthetic Control Plane API on 127.0.0.1:8081
echo "[+] Starting Synthetic Control Plane API on 127.0.0.1:8081..."
python3 "${APP_DIR}/challenge/control_api/control_server.py" &
CONTROL_PID=$!

# Allow internal microservices to bind
sleep 1

# 5. Start Public Web Gateway & Mesh Dispatcher on 0.0.0.0:${PORT:-80}
echo "[+] Starting Public Web Gateway on 0.0.0.0:${PORT:-80}..."
python3 "${APP_DIR}/challenge/web_portal/app.py" &
GATEWAY_PID=$!

# Cleanup trap
cleanup() {
    echo "[*] Terminating all Doom Control Plane services..."
    kill -TERM "$GATEWAY_PID" "$CONTROL_PID" "$CORE_PID" "$WMS_PID" "$FLAG_PID" 2>/dev/null || true
    wait "$GATEWAY_PID" "$CONTROL_PID" "$CORE_PID" "$WMS_PID" "$FLAG_PID" 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM

wait -n "$GATEWAY_PID" "$CONTROL_PID" "$CORE_PID" "$WMS_PID" "$FLAG_PID"
