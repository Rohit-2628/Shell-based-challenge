#!/bin/bash
set -e

APP_DIR="${APP_DIR:-$(cd "$(dirname "$0")" && pwd)}"

echo "[*] Initializing Latveria Citadel // The Black Mirror (Challenge X05)..."

# 1. Start Isolated Flag Service on 127.0.0.1:8089
echo "[+] Starting Isolated Sovereign Flag Vault on 127.0.0.1:8089..."
python3 "${APP_DIR}/challenge/flag_service/flag_server.py" &
FLAG_PID=$!

# 2. Start Sovereign Reflection Protocol Daemon (SRP/1.0) on 127.0.0.1:9099
echo "[+] Starting Sovereign Reflection Protocol Daemon (SRP/1.0) on 127.0.0.1:9099..."
python3 "${APP_DIR}/challenge/internal_protocol/daemon.py" &
SRP_PID=$!

# 3. Start Next Stage Sovereign Vault Controller on 127.0.0.1:8088
echo "[+] Starting Sovereign Vault Controller (Stage 2) on 127.0.0.1:8088..."
python3 "${APP_DIR}/challenge/next_stage/vault.py" &
VAULT_PID=$!

# Allow internal microservices to bind
sleep 1

# 4. Start Public Web Gateway & SSRF Mirror Probe on 0.0.0.0:${PORT:-80}
echo "[+] Starting Public Web Proxy & Ingress Gateway on 0.0.0.0:${PORT:-80}..."
python3 "${APP_DIR}/challenge/web_proxy/app.py" &
GATEWAY_PID=$!

# Cleanup trap
cleanup() {
    echo "[*] Terminating all Black Mirror services..."
    kill -TERM "$GATEWAY_PID" "$VAULT_PID" "$SRP_PID" "$FLAG_PID" 2>/dev/null || true
    wait "$GATEWAY_PID" "$VAULT_PID" "$SRP_PID" "$FLAG_PID" 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM

wait -n "$GATEWAY_PID" "$VAULT_PID" "$SRP_PID" "$FLAG_PID"
