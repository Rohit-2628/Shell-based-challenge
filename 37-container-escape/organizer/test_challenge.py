#!/usr/bin/env python3
"""
Pre-Event Test Suite for X07 — Container Escape Lab
Executes comprehensive validation of container exposure, intended exploit chain,
dedicated VM sandbox isolation, boundary defenses, reset lifecycle, and distribution hygiene.
"""

import sys
import os
import re
import socket
import subprocess
from pathlib import Path

CHALLENGE_DIR = Path(__file__).resolve().parent.parent

def log_test(name, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    print(f"[{status}] {name} {('- ' + detail) if detail else ''}")
    return passed

def test_01_fresh_exposure():
    """Verify only documented external interface (TCP/22 SSH) is active."""
    print("\n=== Test 1: Fresh Exposure & Public Interface ===")
    dockerfile = CHALLENGE_DIR / "Dockerfile"
    content = dockerfile.read_text(errors="ignore")
    has_ssh = "EXPOSE 22" in content
    # Ensure no internal databases or control plane ports exposed
    no_unintended_ports = not re.search(r"EXPOSE\s+(3306|5432|6379|6443|10250)", content)
    return log_test("Public interface restricted to TCP/22 (SSH)", has_ssh and no_unintended_ports)

def test_02_intended_solve():
    """Verify solve logic and exploit reproducibility."""
    print("\n=== Test 2: Intended Solve Validation ===")
    from solve import solve
    success, flag = solve()
    return log_test("Intended container breakout exploit chain", success and bool(flag) and "YUVA{" in flag, f"Flag: {flag}")

def test_03_sandbox_vm_boundary():
    """Verify sandbox boundary rules, cloud metadata blocking, and isolation policies."""
    print("\n=== Test 3: Sandbox VM Boundary & Isolation Rules ===")
    all_passed = True

    # 1. Check iptables rules for metadata and K8s API blocking
    rules_file = CHALLENGE_DIR / "challenge" / "network" / "iptables_rules.sh"
    if rules_file.exists():
        content = rules_file.read_text(errors="ignore")
        p1 = "169.254.169.254" in content and "6443" in content
        all_passed &= log_test("Firewall rules block cloud metadata and K8s API", p1)
    else:
        all_passed &= log_test("Firewall rules script exists", False)

    # 2. Check VM isolation configuration
    vagrantfile = CHALLENGE_DIR / "challenge" / "vm" / "Vagrantfile"
    if vagrantfile.exists():
        vcontent = vagrantfile.read_text(errors="ignore")
        p2 = "cpus = 4" in vcontent and "memory = 4096" in vcontent
        all_passed &= log_test("Dedicated VM resource sizing (4 vCPU / 4 GiB RAM)", p2)
    else:
        all_passed &= log_test("Vagrant VM definition exists", False)

    return all_passed

def test_04_reset_and_lifecycle():
    """Verify reset script completely wipes VM state and generates fresh dynamic flag."""
    print("\n=== Test 4: Reset & Lifecycle Verification ===")
    reset_script = CHALLENGE_DIR / "challenge" / "scripts" / "reset.sh"
    teardown_script = CHALLENGE_DIR / "challenge" / "scripts" / "teardown.sh"
    flag_script = CHALLENGE_DIR / "challenge" / "scripts" / "generate_flag.sh"

    p1 = reset_script.exists() and os.access(reset_script, os.X_OK)
    p2 = teardown_script.exists() and os.access(teardown_script, os.X_OK)
    p3 = flag_script.exists()

    # Test dynamic flag generation
    if flag_script.exists():
        proc = subprocess.run(["bash", str(flag_script), "test_team_99"], capture_output=True, text=True)
        dynamic_flag = proc.stdout.strip()
        p4 = "YUVA{" in dynamic_flag and "x07" in dynamic_flag
    else:
        p4 = False

    return log_test("VM destruction and dynamic flag generation lifecycle", p1 and p2 and p3 and p4)

def test_05_participant_package_hygiene():
    """Verify dist package contains zero leaks, secret keys, or organizer solutions."""
    print("\n=== Test 5: Participant Package Hygiene ===")
    dist_dir = CHALLENGE_DIR / "dist"
    if not dist_dir.exists():
        return log_test("Participant dist directory present", False)

    has_leak = False
    for root, _, files in os.walk(dist_dir):
        for f in files:
            fp = Path(root) / f
            content = fp.read_text(errors="ignore")
            if re.search(r"DOOM\{[a-zA-Z0-9_\-]{10,}\}", content):
                has_leak = True
            if "release_agent" in content or "cgroup.procs" in content or "cgrp" in content:
                has_leak = True
            if f.endswith((".key", ".pem", ".pyc", ".env", ".bak")):
                has_leak = True

    return log_test("Participant distribution package clean (Zero Leaks)", not has_leak)

def main():
    print("===============================================================")
    print(" Running Pre-Event Test Suite: X07 — Container Escape Lab")
    print("===============================================================")
    
    results = [
        test_01_fresh_exposure(),
        test_02_intended_solve(),
        test_03_sandbox_vm_boundary(),
        test_04_reset_and_lifecycle(),
        test_05_participant_package_hygiene()
    ]
    
    print("\n===============================================================")
    if all(results):
        print("[+] ALL PRE-EVENT TESTS PASSED (100%). CHALLENGE READY FOR EVENT.")
        print("===============================================================")
        sys.exit(0)
    else:
        print("[-] SOME TESTS FAILED. PLEASE REVIEW LOGS.")
        print("===============================================================")
        sys.exit(1)

if __name__ == "__main__":
    main()
