#!/bin/bash
set -e

echo "[+] Initializing container security environment..."

# Create operator user
if ! id -u operator >/dev/null 2>&1; then
    groupadd -g 1000 operator
    useradd -u 1000 -g operator -m -s /bin/bash operator
    echo "operator:operator" | chpasswd
fi

# Grant sudo inside the container so operator can exercise container-level capabilities
echo "operator ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/operator
chmod 0440 /etc/sudoers.d/operator

# Ensure SSH host keys exist
ssh-keygen -A

# Ensure SSH runtime directory exists
mkdir -p /run/sshd
chmod 0755 /run/sshd

# Setup MOTD & Banner
cp /app/challenge/container/banner.txt /etc/ssh/banner.txt
cp /app/challenge/container/motd /etc/motd
echo "cat /etc/motd" >> /home/operator/.bashrc
chown operator:operator /home/operator/.bashrc

echo "[+] Container environment ready."
