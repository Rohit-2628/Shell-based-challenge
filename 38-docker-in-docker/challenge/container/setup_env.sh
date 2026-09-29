#!/bin/bash
set -e

echo "[+] Initializing CI runner security and user environment..."

# Create operator group and user safely
if ! getent group operator >/dev/null 2>&1; then
    groupadd -g 1000 operator
fi
if ! id -u operator >/dev/null 2>&1; then
    useradd -u 1000 -g operator -m -s /bin/bash operator
    echo "operator:operator" | chpasswd
fi

# Ensure docker group exists and operator is a member
if ! getent group docker >/dev/null 2>&1; then
    groupadd -g 999 docker
fi
usermod -aG docker operator

# Grant restricted sudo inside the runner for container debugging if needed
echo "operator ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/operator
chmod 0440 /etc/sudoers.d/operator

# Ensure SSH host keys exist
ssh-keygen -A

# Ensure SSH runtime directory exists
mkdir -p /run/sshd
chmod 0755 /run/sshd

# Setup SSH config, MOTD & Banner
cp /app/challenge/container/sshd_config /etc/ssh/sshd_config
cp /app/challenge/container/banner.txt /etc/ssh/banner.txt
cp /app/challenge/container/motd /etc/motd
echo "cat /etc/motd" >> /home/operator/.bashrc
chown operator:operator /home/operator/.bashrc

echo "[+] CI runner environment initialized."
