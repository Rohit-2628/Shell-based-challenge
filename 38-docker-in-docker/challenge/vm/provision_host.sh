#!/usr/bin/env bash
set -euo pipefail

echo "======================================================="
echo " Provisioning Host Environment for X08 Docker-in-Docker"
echo "======================================================="

export DEBIAN_FRONTEND=noninteractive

# Update packages and install Docker runtime & network isolation tools
apt-get update
apt-get install -y --no-install-recommends \
    docker.io \
    iptables \
    curl \
    util-linux \
    kmod \
    procps

# Ensure Docker is started on VM host
systemctl enable --now docker

# Create unprivileged player sandbox environment on host if needed
useradd -m -s /bin/bash sandbox-user || true

# Apply VM Network Isolation / iptables
if [ -f /opt/x08/challenge/network/iptables_rules.sh ]; then
    bash /opt/x08/challenge/network/iptables_rules.sh
fi

echo "[+] Host provisioning complete."
