#!/bin/bash
set -euo pipefail

echo "[*] Initializing D27 — Private Container Registry Challenge..."

# 1. Setup Flag securely
DEFAULT_FLAG="YUVA{pr1v4t3_r3g1stry_l4y3r_3xf1ltr4t10n_9901}"
FLAG_VALUE="${CHALLENGE_FLAG:-${FLAG:-${DYNAMIC_FLAG:-$DEFAULT_FLAG}}}"
mkdir -p /opt/vault
echo "${FLAG_VALUE}" > /opt/vault/flag.txt
chown -R vault:vault /opt/vault
chmod 700 /opt/vault
chmod 400 /opt/vault/flag.txt

# Unset and clear FLAG variable from environment to prevent env leaks
unset FLAG CHALLENGE_FLAG DYNAMIC_FLAG || true
export -n FLAG CHALLENGE_FLAG DYNAMIC_FLAG || true

# 2. Ensure SSH Host Keys
ssh-keygen -A >/dev/null 2>&1 || true

# 3. Seed Container Registry Store if empty
if [ ! -d "/var/lib/latveria-registry/repositories" ]; then
    echo "[*] Generating synthetic OCI / Docker Registry v2 image repositories..."
    python3 /challenge/registry/generate_seed_data.py /var/lib/latveria-registry
fi
chown -R registry:registry /var/lib/latveria-registry
chmod -R 755 /var/lib/latveria-registry

# 4. Setup Workstation for developer
if [ ! -f "/home/developer/notes/incident_report_SEC-2026-9901.txt" ]; then
    /challenge/workstation/setup_workstation.sh
fi
chown -R developer:developer /home/developer
chmod 750 /home/developer

# 5. Start Internal Vault Daemon (user: vault) on 127.0.0.1:8080
echo "[*] Starting internal Orbital Vault daemon (user: vault)..."
su -s /bin/bash vault -c "python3 /challenge/vault/server.py --host 127.0.0.1 --port 8080" >/var/log/vault-server.log 2>&1 &
VAULT_PID=$!

sleep 1
if ! kill -0 $VAULT_PID 2>/dev/null; then
    echo "[!] Vault daemon failed to start! Log:"
    cat /var/log/vault-server.log
    exit 1
fi

# 6. Start Private Container Registry Daemon (user: registry) on port 5000
echo "[*] Starting Private Container Registry v2 daemon (user: registry)..."
su -s /bin/bash registry -c "python3 /challenge/registry/registry_server.py --host 0.0.0.0 --port 5000 --storage /var/lib/latveria-registry" >/var/log/registry-server.log 2>&1 &
REGISTRY_PID=$!

sleep 1
if ! kill -0 $REGISTRY_PID 2>/dev/null; then
    echo "[!] Registry daemon failed to start! Log:"
    cat /var/log/registry-server.log
    exit 1
fi

# 7. Start Nginx on Port 80 (proxying to Registry on 5000)
if command -v nginx >/dev/null 2>&1; then
    echo "[*] Starting Nginx HTTP gateway on TCP/80..."
    nginx -g "daemon on;"
fi

echo "[*] Starting OpenSSH Server on TCP/22..."
mkdir -p /run/sshd
exec /usr/sbin/sshd -D -e
