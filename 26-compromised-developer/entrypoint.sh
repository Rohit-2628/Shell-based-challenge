#!/bin/bash
set -euo pipefail

echo "[*] Initializing D26 - Compromised Developer Environment..."

# 1. Setup Flag
FLAG_VALUE="${FLAG:-DOOM{c0mpr0m1s3d_d3v_t0_pr0d_p1p3l1n3_8a39f1c7}}"
mkdir -p /opt/production
echo "${FLAG_VALUE}" > /opt/production/flag.txt
chown -R prod:prod /opt/production
chmod 700 /opt/production
chmod 400 /opt/production/flag.txt

# Wipe FLAG from environment so no child processes inherit it
unset FLAG || true

# 2. Ensure SSH Host Keys
ssh-keygen -A >/dev/null 2>&1 || true

# 3. Setup Workstation Environment if not already present
if [ ! -d "/home/developer/projects/latveria-telemetry-dispatch/.git" ]; then
    /challenge/workstation/setup_workstation.sh
fi
chown -R developer:developer /home/developer
chmod 750 /home/developer

# 4. Start Production Mock as unprivileged user 'prod' in background
echo "[*] Starting internal production service daemon (user: prod)..."
su -s /bin/bash prod -c "python3 /challenge/production/server.py" >/var/log/production-server.log 2>&1 &
PROD_PID=$!

# Wait briefly for production service to start
sleep 1
if ! kill -0 $PROD_PID 2>/dev/null; then
    echo "[!] Production service failed to start! Check /var/log/production-server.log"
    cat /var/log/production-server.log
    exit 1
fi

echo "[*] Starting OpenSSH Server on TCP/22..."
mkdir -p /run/sshd
# Start sshd with clean environment
exec env -i PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" /usr/sbin/sshd -D -e
