#!/bin/bash
set -e

echo "===================================================================="
echo "  STARTING LATVERIA SOVEREIGN CI/CD SANDBOX ENVIRONMENT (X04)"
echo "===================================================================="

# 1. Initialize pristine seed snapshot
echo "[*] Initializing challenge storage, Git repositories, inner Docker daemon state, and registry..."
python3 /app/challenge/snapshot/seed_state.py

# 2. Configure Docker CLI wrapper in system path
if [ ! -f /usr/local/bin/docker ] && [ -w /usr/local/bin ]; then
    cp /app/challenge/inner_docker/docker_cli.py /usr/local/bin/docker
    chmod +x /usr/local/bin/docker
fi

export DOCKER_HOST="tcp://127.0.0.1:2375"
export PATH="/app/challenge/inner_docker:$PATH"

# 3. Start Inner Docker Daemon on 127.0.0.1:2375
echo "[*] Launching challenge-local Inner Docker Daemon (DinD)..."
python3 /app/challenge/inner_docker/docker_daemon.py &
PID_DOCKER=$!

# 4. Start Internal OCI Registry on 127.0.0.1:5000
echo "[*] Launching challenge-local OCI Registry v2..."
python3 /app/challenge/registry/registry_server.py &
PID_REGISTRY=$!

# 5. Start Internal Git HTTP Backend on 127.0.0.1:8081
echo "[*] Launching Git HTTP Smart Service..."
python3 /app/challenge/git_server/git_http.py &
PID_GIT_HTTP=$!

# 6. Start Internal CI Orchestrator on 127.0.0.1:8082
echo "[*] Launching CI Pipeline Orchestrator & Runner Service..."
python3 /app/challenge/ci/ci_server.py &
PID_CI=$!

# 7. Start Internal Production Mock on 127.0.0.1:8083
echo "[*] Launching Sovereign Production Mainframe Mock..."
python3 /app/challenge/production/prod_server.py &
PID_PROD=$!

# 8. Start SSH Git Service on TCP/22 (or configured SSH_PORT)
SSH_PORT=${SSH_PORT:-22}
echo "[*] Launching Git SSH Service on port ${SSH_PORT}..."
python3 /app/challenge/git_server/ssh_server.py ${SSH_PORT} &
PID_SSH=$!

# Wait briefly for microservices to bind
sleep 1.5

cleanup() {
    echo "[*] Shutting down X04 services..."
    kill -TERM $PID_DOCKER $PID_REGISTRY $PID_GIT_HTTP $PID_CI $PID_PROD $PID_SSH 2>/dev/null || true
    exit 0
}

trap cleanup SIGTERM SIGINT

# 9. Start Main Reverse Proxy Gateway on 0.0.0.0:80 (Foreground)
PORT=${PORT:-80}
echo "[+] Starting Latveria CI/CD Web Gateway on port ${PORT}..."
exec python3 /app/challenge/gateway/app.py
