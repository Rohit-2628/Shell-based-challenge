#!/bin/bash
set -e

APP_DIR="${APP_DIR:-$(cd "$(dirname "$0")" && pwd)}"

echo "[*] Initializing Latveria Citadel // Secret Zero Machine Identity Infrastructure (X09)..."

# 1. Initialize PKI and State Manager
echo "[+] Initializing Challenge-Local Root CA and PKI store..."
python3 -c "import sys; sys.path.insert(0, '${APP_DIR}/challenge'); from ca.pki_manager import pki_manager; from config.config_manager import state_manager; pki_manager.initialize_or_load_ca(); state_manager.load_or_initialize_state(); print('[+] Challenge PKI ready. Root CA fingerprint:', pki_manager.ca_cert.fingerprint(pki_manager.ca_cert.signature_hash_algorithm).hex()[:16])"

# 2. Start Flag Service on 127.0.0.1:8084
echo "[+] Starting Isolated Flag Vault on 127.0.0.1:8084..."
python3 "${APP_DIR}/challenge/flag_service/flag_server.py" &
FLAG_PID=$!

# 3. Start Protected Target Service on 127.0.0.1:8083
echo "[+] Starting Protected Target Service on 127.0.0.1:8083..."
python3 "${APP_DIR}/challenge/target/target_server.py" &
TARGET_PID=$!

# 4. Start Secret Service on 127.0.0.1:8082
echo "[+] Starting Secret Zero Distribution Service on 127.0.0.1:8082..."
python3 "${APP_DIR}/challenge/secret_service/secret_server.py" &
SECRET_PID=$!

# 5. Start Identity Authority Service on 127.0.0.1:8081
echo "[+] Starting Identity Authority Service on 127.0.0.1:8081..."
python3 "${APP_DIR}/challenge/identity_service/identity_server.py" &
IDENTITY_PID=$!

# Allow internal services to bind
sleep 1

# 6. Start Public Gateway & Bootstrap Portal on 0.0.0.0:${PORT:-80}
echo "[+] Starting Public Bootstrap Gateway on 0.0.0.0:${PORT:-80}..."
python3 "${APP_DIR}/challenge/bootstrap_service/app.py" &
GATEWAY_PID=$!

cleanup() {
    echo "[*] Terminating all Secret Zero services..."
    kill -TERM "$GATEWAY_PID" "$IDENTITY_PID" "$SECRET_PID" "$TARGET_PID" "$FLAG_PID" 2>/dev/null || true
    wait "$GATEWAY_PID" "$IDENTITY_PID" "$SECRET_PID" "$TARGET_PID" "$FLAG_PID" 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM

wait -n "$GATEWAY_PID" "$IDENTITY_PID" "$SECRET_PID" "$TARGET_PID" "$FLAG_PID"
