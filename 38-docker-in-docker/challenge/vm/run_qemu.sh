#!/usr/bin/env bash
set -euo pipefail

# X08 — Docker-in-Docker QEMU/KVM Runner
# Spins up an ephemeral, disposable QEMU VM with exact masterbook resource allocations (4 vCPU / 4GB RAM / 8GB disk).

IMAGE_DIR="${IMAGE_DIR:-/var/lib/ctf-vms/x08}"
VM_DISK="${1:-${IMAGE_DIR}/x08_instance_$$.qcow2}"
BASE_IMAGE="${BASE_IMAGE:-/var/lib/ctf-images/x08-base.qcow2}"
SSH_HOST_PORT="${SSH_HOST_PORT:-2222}"

echo "[*] Creating disposable copy-on-write overlay for instance..."
mkdir -p "$(dirname "$VM_DISK")"
qemu-img create -f qcow2 -b "$BASE_IMAGE" -F qcow2 "$VM_DISK" 8G

echo "[*] Starting isolated VM instance with 4 vCPUs and 4GB RAM..."
exec qemu-system-x86_64 \
    -enable-kvm \
    -m 4096 \
    -smp 4 \
    -cpu host \
    -drive file="$VM_DISK",if=virtio,format=qcow2 \
    -netdev user,id=net0,hostfwd=tcp::"${SSH_HOST_PORT}"-:22 \
    -device virtio-net-pci,netdev=net0 \
    -nographic \
    -snapshot \
    -serial mon:stdio
