#!/usr/bin/env bash
set -e

echo "[*] Starting Latveria Defense Grid Node (X07 Container Workstation)..."

# Ensure SSH host keys are generated
if [ ! -f /etc/ssh/ssh_host_rsa_key ]; then
    ssh-keygen -A
fi

# Ensure privilege separation directory exists
mkdir -p /run/sshd
chmod 0755 /run/sshd

echo "[+] Launching OpenSSH Daemon on port 22..."
exec /usr/sbin/sshd -D -e
