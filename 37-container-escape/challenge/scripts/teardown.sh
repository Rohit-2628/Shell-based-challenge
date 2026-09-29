#!/usr/bin/env bash
set -euo pipefail

# X07 Teardown Script
# Fully purges all runtime containers, VM disk images, and ephemeral states.

INSTANCE_ID="${1:-default}"

echo "[*] Tearing down X07 instance: $INSTANCE_ID..."

# 1. Stop and remove Docker containers
if command -v docker >/dev/null 2>&1; then
    docker stop x07-escape-lab 2>/dev/null || true
    docker rm -f x07-escape-lab 2>/dev/null || true
fi

# 2. Halt and destroy Vagrant VM if present
if command -v vagrant >/dev/null 2>&1 && [ -f Vagrantfile ]; then
    vagrant destroy -f 2>/dev/null || true
fi

# 3. Kill any running QEMU processes matching instance
pkill -f "x07_instance_${INSTANCE_ID}" 2>/dev/null || true

# 4. Remove ephemeral disk overlays and temporary test directories
rm -rf "/var/lib/ctf-vms/x07/x07_instance_${INSTANCE_ID}.qcow2" 2>/dev/null || true
rm -rf /tmp/x07_mock_host 2>/dev/null || true
rm -rf /tmp/cgrp /tmp/host_flag.txt /tmp/cmd 2>/dev/null || true

echo "[+] Teardown complete. Zero persistent state remaining."
