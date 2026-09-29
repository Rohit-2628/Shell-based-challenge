#!/usr/bin/env bash
set -e

echo "[*] Starting Latveria CI Build Runner (X08 Docker-in-Docker Node)..."

# Ensure SSH host keys are generated
if [ ! -f /etc/ssh/ssh_host_rsa_key ]; then
    ssh-keygen -A
fi

# Ensure privilege separation directory exists
mkdir -p /run/sshd /var/run /var/log
chmod 0755 /run/sshd

# Start inner Docker daemon
echo "[*] Launching Inner Docker Daemon..."
rm -f /var/run/docker.pid /var/run/docker.sock

# Start dockerd with vfs (or overlay2 if permitted by host)
dockerd --storage-driver=vfs --data-root=/var/lib/docker > /var/log/dockerd.log 2>&1 &
DOCKER_PID=$!

echo "[*] Waiting for inner Docker daemon socket initialization..."
MAX_WAIT=30
COUNT=0
while ! docker info >/dev/null 2>&1; do
    sleep 1
    COUNT=$((COUNT + 1))
    if [ $COUNT -ge $MAX_WAIT ]; then
        echo "[-] Timeout waiting for inner Docker daemon. Recent dockerd logs:"
        tail -n 25 /var/log/dockerd.log || true
        break
    fi
done

if docker info >/dev/null 2>&1; then
    echo "[+] Inner Docker daemon is active and operational!"
    # Ensure operator user has socket access permissions
    chmod 666 /var/run/docker.sock || true
    
    echo "[*] Seeding inner containers, networks, images, and target..."
    python3 /app/challenge/snapshot/seed_state.py "${FLAG:-}" "${VAULT_AUTH_TOKEN:-}"
else
    echo "[!] Warning: Docker daemon was not ready within timeout. Check permissions."
fi

echo "172.28.20.2 dind-service.local" >> /etc/hosts 2>/dev/null || true

echo "[+] Launching OpenSSH Daemon on port 22..."
exec /usr/sbin/sshd -D -e
