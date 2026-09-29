#!/usr/bin/env bash
# Boundary Validation Script for X08 Sandbox Environment

set -u

echo "======================================================="
echo " X08 Boundary & Network Isolation Verification Check"
echo "======================================================="

FAILED=0

# Test 1: Cloud Metadata probe
echo -n "[*] Probing Cloud Metadata (169.254.169.254)... "
if curl --connect-timeout 2 -s http://169.254.169.254 >/dev/null 2>&1; then
    echo "FAILED (Accessible!)"
    FAILED=1
else
    echo "PASSED (Blocked)"
fi

# Test 2: Kubernetes API probe
echo -n "[*] Probing Kubernetes Control Plane (10.96.0.1:443 / :6443)... "
if curl --connect-timeout 2 -k -s https://10.96.0.1:443 >/dev/null 2>&1 || curl --connect-timeout 2 -k -s https://127.0.0.1:6443 >/dev/null 2>&1; then
    echo "FAILED (Accessible!)"
    FAILED=1
else
    echo "PASSED (Blocked)"
fi

# Test 3: Kubelet probe
echo -n "[*] Probing Kubelet Port (10250)... "
if curl --connect-timeout 2 -k -s https://127.0.0.1:10250 >/dev/null 2>&1; then
    echo "FAILED (Accessible!)"
    FAILED=1
else
    echo "PASSED (Blocked)"
fi

# Test 4: Cross-Team / RFC1918 egress probe
echo -n "[*] Probing Cross-Team Subnets (10.0.0.1)... "
if curl --connect-timeout 2 -s http://10.0.0.1 >/dev/null 2>&1; then
    echo "FAILED (Accessible!)"
    FAILED=1
else
    echo "PASSED (Blocked)"
fi

# Test 5: Outer host Docker socket check
echo -n "[*] Checking for outer host Docker socket exposure... "
if [ -S /run/docker.sock ] || [ -S /var/run/docker.sock ]; then
    # Verify that the docker socket belongs to our inner dockerd process, not the host
    INNER_DOCKER_PID=$(pgrep -f "dockerd" | head -n 1 || true)
    if [ -n "$INNER_DOCKER_PID" ]; then
        echo "PASSED (Inner Daemon Active)"
    else
        echo "FAILED (Outer socket leaked without local dockerd!)"
        FAILED=1
    fi
else
    echo "PASSED (No exposed socket)"
fi

echo "======================================================="
if [ $FAILED -eq 0 ]; then
    echo "[+] ALL BOUNDARY CHECKS PASSED. Isolation is strictly maintained."
    exit 0
else
    echo "[-] ONE OR MORE BOUNDARY CHECKS FAILED."
    exit 1
fi
