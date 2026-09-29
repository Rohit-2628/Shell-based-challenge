#!/bin/bash
set -euo pipefail

echo "[*] Initializing D28 — Production Debug Mode Challenge..."

# 1. Setup Flag securely
FLAG_VALUE="${FLAG:-YUVA{pr0duct10n_d3bug_d1sc10sur3_p1v0t_7c2b91ea}}"
mkdir -p /opt/vault
echo "${FLAG_VALUE}" > /opt/vault/flag.txt
chown -R vault:vault /opt/vault
chmod 700 /opt/vault
chmod 400 /opt/vault/flag.txt

# Unset and clear FLAG variable from environment to prevent env leaks
unset FLAG || true
export -n FLAG || true
echo "unset FLAG" >> /etc/profile
echo "unset FLAG" >> /etc/bash.bashrc

# 2. Start Internal Executive Core Daemon (user: vault) on 127.0.0.1:8081
echo "[*] Starting Internal Executive Core Daemon (user: vault) on 127.0.0.1:8081..."
su -s /bin/bash vault -c "python3 /challenge/internal/internal_service.py --host 127.0.0.1 --port 8081" >/var/log/internal-core.log 2>&1 &
INTERNAL_PID=$!

sleep 1
if ! kill -0 $INTERNAL_PID 2>/dev/null; then
    echo "[!] Internal Core daemon failed to start! Log:"
    cat /var/log/internal-core.log
    exit 1
fi

# 3. Start Production Gateway API (user: prod) on 0.0.0.0:80
echo "[*] Starting Production Telemetry Gateway on TCP/80..."
su -s /bin/bash prod -c "python3 /challenge/production/app.py --host 0.0.0.0 --port 80" >/var/log/production-gateway.log 2>&1 &
GATEWAY_PID=$!

sleep 1
if ! kill -0 $GATEWAY_PID 2>/dev/null; then
    echo "[!] Production Gateway failed to start! Log:"
    cat /var/log/production-gateway.log
    exit 1
fi

echo "[*] All D28 services started successfully."

# Supervisor loop
while true; do
    if ! kill -0 $INTERNAL_PID 2>/dev/null; then
        echo "[!] Internal Core service died! Exiting..."
        exit 1
    fi
    if ! kill -0 $GATEWAY_PID 2>/dev/null; then
        echo "[!] Production Gateway died! Exiting..."
        exit 1
    fi
    sleep 5
done
