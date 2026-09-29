#!/bin/bash
set -e

echo "[*] Initializing Latveria Citadel Sovereign Microservice Mesh (X02 - Microservice Trust)..."

# Ensure runtime directories exist
export PKI_DIR="${PKI_DIR:-/tmp/citadel_mesh_pki}"
mkdir -p "$PKI_DIR"

# Synchronously initialize Root CA & Service A credentials once
python3 -c "import sys; sys.path.insert(0, '/app/challenge'); from common.mesh_crypto import ensure_pki_initialized; ensure_pki_initialized()"

# 1. Start Service A (Telemetry Agent) on 127.0.0.1:8081
echo "[+] Launching Service A (Telemetry Agent) on 127.0.0.1:8081..."
python3 /app/challenge/service_a/app.py &
SERVICE_A_PID=$!

# 2. Start Service B (Core Controller) on 127.0.0.1:8082
echo "[+] Launching Service B (Core Controller) on 127.0.0.1:8082..."
python3 /app/challenge/service_b/app.py &
SERVICE_B_PID=$!

# 3. Start Admin Service (Citadel Vault) on 127.0.0.1:8083
echo "[+] Launching Admin Service (Citadel Vault) on 127.0.0.1:8083..."
python3 /app/challenge/admin/app.py &
ADMIN_PID=$!

# Wait for internal microservices to initialize
sleep 1

# 4. Start Public Gateway Ingress on 0.0.0.0:${PORT:-80}
echo "[+] Launching Public Ingress Gateway on 0.0.0.0:${PORT:-80}..."
python3 /app/challenge/gateway/app.py &
GATEWAY_PID=$!

# Trap signals for graceful termination
cleanup() {
    echo "[*] Shutting down all Citadel microservices..."
    kill -TERM "$GATEWAY_PID" "$SERVICE_A_PID" "$SERVICE_B_PID" "$ADMIN_PID" 2>/dev/null || true
    wait "$GATEWAY_PID" "$SERVICE_A_PID" "$SERVICE_B_PID" "$ADMIN_PID" 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM

# Supervise processes
wait -n "$GATEWAY_PID" "$SERVICE_A_PID" "$SERVICE_B_PID" "$ADMIN_PID"
