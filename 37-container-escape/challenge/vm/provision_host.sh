#!/usr/bin/env bash
set -euo pipefail

echo "======================================================="
echo " Provisioning Host Environment for X07 Container Escape"
echo "======================================================="

export DEBIAN_FRONTEND=noninteractive

# Update packages and install Docker runtime
apt-get update
apt-get install -y --no-install-recommends \
    docker.io \
    iptables \
    curl \
    util-linux \
    cgroup-tools \
    kmod \
    procps

# Ensure Docker is started
systemctl enable --now docker

# Create Host Flag strictly in host root (Never baked into container image)
FLAG_VALUE="${CHALLENGE_FLAG:-YUVA{c0nt41n3r_3sc4p3_cgr0up_c4ps_s4ndb0x_vm_x07}}"
echo "$FLAG_VALUE" > /root/flag.txt
chmod 0600 /root/flag.txt
chown root:root /root/flag.txt

# Create non-root player sandbox environment on host if needed
useradd -m -s /bin/bash sandbox-user || true

# Apply VM Network Isolation / iptables
if [ -f /opt/x07/challenge/network/iptables_rules.sh ]; then
    bash /opt/x07/challenge/network/iptables_rules.sh
fi

echo "[+] Host provisioning complete."
