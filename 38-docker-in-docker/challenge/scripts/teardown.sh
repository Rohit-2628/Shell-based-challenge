#!/usr/bin/env bash
set -euo pipefail

# X08 Teardown Script
# Fully purges all runtime containers, inner Docker daemon state, VM disk images, and ephemeral states.

INSTANCE_ID="${1:-default}"

echo "[*] Tearing down X08 instance: $INSTANCE_ID..."

# 1. Stop and remove Docker containers and compose stack
if command -v docker >/dev/null 2>&1; then
    # Stop inner containers if accessible
    docker exec x08-docker-in-docker sh -c "docker rm -f \$(docker ps -aq) 2>/dev/null || true; docker volume prune -f 2>/dev/null || true; docker network prune -f 2>/dev/null || true" 2>/dev/null || true
    
    docker stop x08-docker-in-docker 2>/dev/null || true
    docker rm -f x08-docker-in-docker 2>/dev/null || true
fi

# 2. Halt and destroy Vagrant VM if present
if command -v vagrant >/dev/null 2>&1 && [ -f Vagrantfile ]; then
    vagrant destroy -f 2>/dev/null || true
fi

# 3. Kill any running QEMU processes matching instance
pkill -f "x08_instance_${INSTANCE_ID}" 2>/dev/null || true

# 4. Remove ephemeral disk overlays and temporary test directories
rm -rf "/var/lib/ctf-vms/x08/x08_instance_${INSTANCE_ID}.qcow2" 2>/dev/null || true
rm -rf /tmp/x08_scratch 2>/dev/null || true

echo "[+] Teardown complete. Zero persistent state remaining."
