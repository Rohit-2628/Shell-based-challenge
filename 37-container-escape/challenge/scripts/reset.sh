#!/usr/bin/env bash
set -euo pipefail

# X07 Environment Reset Script
# Complete destruction and deterministic fresh recreation of VM sandbox and flag state.

INSTANCE_ID="${1:-default}"
TEAM_ID="${2:-team_local}"

echo "======================================================="
echo " Initiating Complete Reset for X07 Instance: $INSTANCE_ID"
echo "======================================================="

# Step 1: Teardown existing instance state
if [ -f "$(dirname "$0")/teardown.sh" ]; then
    bash "$(dirname "$0")/teardown.sh" "$INSTANCE_ID"
fi

# Step 2: Generate dynamic team flag
NEW_FLAG=$(bash "$(dirname "$0")/generate_flag.sh" "$TEAM_ID")
export CHALLENGE_FLAG="$NEW_FLAG"

echo "[*] Fresh flag seeded for $TEAM_ID: (Protected)"

# Step 3: Recreate fresh container / VM instance
if command -v vagrant >/dev/null 2>&1 && [ -f Vagrantfile ]; then
    echo "[*] Triggering fresh Vagrant VM provisioning..."
    vagrant destroy -f || true
    vagrant up --provision
elif command -v docker >/dev/null 2>&1; then
    echo "[*] Resetting local container testing environment..."
    docker stop x07-escape-lab 2>/dev/null || true
    docker rm -f x07-escape-lab 2>/dev/null || true
    
    # Write fresh mock host flag for local development sandbox
    mkdir -p /tmp/x07_mock_host/root
    echo "$NEW_FLAG" > /tmp/x07_mock_host/root/flag.txt
    chmod 0600 /tmp/x07_mock_host/root/flag.txt
    
    docker-compose down -v 2>/dev/null || true
    docker-compose up -d --build
fi

echo "[+] Reset successfully completed. Clean state active."
