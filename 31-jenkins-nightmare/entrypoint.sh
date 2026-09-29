#!/bin/bash
set -e

echo "[*] Initializing Latveria Sovereign CI/CD Infrastructure (Jenkins Nightmare)..."

# Ensure runtime directories exist
mkdir -p /tmp/ci_build_workspace /tmp/ci_artifacts /tmp/registry_storage

# 1. Start Internal Private OCI Container Registry (127.0.0.1:5000)
echo "[+] Launching Local OCI Container Registry on 127.0.0.1:5000..."
python3 /app/challenge/registry/registry_server.py &
REGISTRY_PID=$!

# 2. Start Internal Production Mock Mainframe (127.0.0.1:8081)
echo "[+] Launching Isolated Production Mock Mainframe on 127.0.0.1:8081..."
python3 /app/challenge/production/prod_server.py &
PRODUCTION_PID=$!

# Wait for internal services to become ready
sleep 1

# 3. Start Public CI Gateway & Orchestrator (0.0.0.0:80)
echo "[+] Launching Sovereign CI Gateway Orchestrator on 0.0.0.0:${PORT:-80}..."
python3 /app/challenge/ci/app.py &
GATEWAY_PID=$!

# Trap signals for graceful shutdown
cleanup() {
    echo "[*] Shutting down all services..."
    kill -TERM "$GATEWAY_PID" "$REGISTRY_PID" "$PRODUCTION_PID" 2>/dev/null || true
    wait "$GATEWAY_PID" "$REGISTRY_PID" "$PRODUCTION_PID" 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM

# Keep container alive and supervise processes
wait -n "$GATEWAY_PID" "$REGISTRY_PID" "$PRODUCTION_PID"
