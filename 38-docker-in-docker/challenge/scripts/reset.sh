#!/usr/bin/env bash
set -euo pipefail

# X08 Environment Reset Script
# Complete destruction and deterministic fresh recreation of VM sandbox, inner Docker daemon, and flag state.

INSTANCE_ID="${1:-default}"
TEAM_ID="${2:-team_local}"

echo "======================================================="
echo " Initiating Complete Reset for X08 Instance: $INSTANCE_ID"
echo "======================================================="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHALLENGE_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Step 1: Teardown existing instance state
if [ -f "${SCRIPT_DIR}/teardown.sh" ]; then
    bash "${SCRIPT_DIR}/teardown.sh" "$INSTANCE_ID"
fi

# Step 2: Generate dynamic team flag
NEW_FLAG=$(bash "${SCRIPT_DIR}/generate_flag.sh" "$TEAM_ID")
export CHALLENGE_FLAG="$NEW_FLAG"
export FLAG="$NEW_FLAG"

echo "[*] Fresh flag seeded for $TEAM_ID: (Protected)"

# Step 3: Recreate fresh container / VM instance
if command -v vagrant >/dev/null 2>&1 && [ -f "${CHALLENGE_ROOT}/challenge/vm/Vagrantfile" ]; then
    echo "[*] Triggering fresh Vagrant VM provisioning..."
    cd "${CHALLENGE_ROOT}/challenge/vm"
    vagrant destroy -f || true
    FLAG="$NEW_FLAG" vagrant up --provision
elif command -v docker >/dev/null 2>&1; then
    echo "[*] Resetting local container testing environment..."
    cd "${CHALLENGE_ROOT}"
    docker stop x08-docker-in-docker 2>/dev/null || true
    docker rm -f x08-docker-in-docker 2>/dev/null || true
    
    docker compose down -v 2>/dev/null || true
    FLAG="$NEW_FLAG" docker compose up -d --build
    
    echo "[*] Waiting for inner Docker daemon and service seeding..."
    sleep 5
fi

echo "[+] Reset successfully completed. Clean DinD state active."
