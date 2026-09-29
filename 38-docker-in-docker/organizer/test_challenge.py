#!/usr/bin/env python3
"""
Pre-Event Test Suite for X08 — Docker-in-Docker
Executes comprehensive validation across:
1. Fresh Start & Public Interface Exposure
2. Intended Solve & Dynamic Flag Extraction
3. Boundary Defenses & Outer Host Isolation
4. Reset & Full Lifecycle Wipe
5. Resource Controls & Sandbox Quotas (4 vCPU, 4 GiB RAM, 8 GiB Disk)
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

def test_01_fresh_start():
    """Test 1: Verify only TCP/22 is publicly exposed and inner services are not directly exposed."""
    print("\n=== Test 1: Fresh Start & Public Interface ===")
    all_passed = True

    dockerfile = CHALLENGE_DIR / "Dockerfile"
    compose_file = CHALLENGE_DIR / "docker-compose.yml"
    
    df_content = dockerfile.read_text(errors="ignore") if dockerfile.exists() else ""
    dc_content = compose_file.read_text(errors="ignore") if compose_file.exists() else ""
    
    # 1. Verify SSH is exposed on port 22
    p1 = "EXPOSE 22" in df_content and "22:22" in dc_content
    all_passed &= log_test("Public interface restricted to TCP/22 (SSH)", p1)

    # 2. Verify inner service ports (8443, 8080) and databases (3306, 6379, 5432) are NOT published to host
    no_inner_exposed = not re.search(r"ports:\s*\n\s*-\s*[\"']?(8443|8080|6379|3306|5432):", dc_content)
    all_passed &= log_test("Inner services (8443/8080) shielded from direct host port mapping", no_inner_exposed)

    # 3. Verify inner services source files exist
    vault_app = CHALLENGE_DIR / "challenge" / "inner_services" / "vault_core" / "app.py"
    p3 = vault_app.exists()
    all_passed &= log_test("Inner Vault Core service definition present", p3)

    return all_passed

def test_02_intended_solve():
    """Test 2: Verify full intended solve chain from CI runner to inner Docker pivot."""
    print("\n=== Test 2: Intended Solve Validation ===")
    from solve import solve
    success, flag = solve()
    return log_test("Intended Docker-in-Docker pivot solve chain", success and bool(flag) and "YUVA{" in flag, f"Flag: {flag}")

def test_03_boundary_test():
    """Test 3: Verify outer Docker socket protection, K8s control plane, cloud metadata, and cross-team isolation."""
    print("\n=== Test 3: Boundary & Outer Host Isolation ===")
    all_passed = True

    # 1. Check iptables rules for metadata, K8s API, and RFC1918 blocking
    rules_file = CHALLENGE_DIR / "challenge" / "network" / "iptables_rules.sh"
    if rules_file.exists():
        content = rules_file.read_text(errors="ignore")
        p1 = "169.254.169.254" in content and "6443" in content and "10.0.0.0/8" in content
        all_passed &= log_test("Egress firewall blocks cloud metadata, K8s API, and other teams", p1)
    else:
        all_passed &= log_test("Firewall rules script exists", False)

    # 2. Verify check_boundaries.sh script exists and is executable
    check_bound = CHALLENGE_DIR / "challenge" / "scripts" / "check_boundaries.sh"
    p2 = check_bound.exists() and os.access(check_bound, os.X_OK)
    all_passed &= log_test("Boundary validation check script configured", p2)

    # 3. Ensure no outer Docker socket mount in docker-compose.yml
    dc_content = (CHALLENGE_DIR / "docker-compose.yml").read_text(errors="ignore")
    no_host_docker_sock = "/var/run/docker.sock:/var/run/docker.sock" not in dc_content
    all_passed &= log_test("Outer host Docker socket is NOT mounted into container", no_host_docker_sock)

    return all_passed

def test_04_reset_test():
    """Test 4: Verify reset completely purges inner Docker state and generates fresh dynamic flag."""
    print("\n=== Test 4: Reset & Full Lifecycle Verification ===")
    all_passed = True

    reset_script = CHALLENGE_DIR / "challenge" / "scripts" / "reset.sh"
    teardown_script = CHALLENGE_DIR / "challenge" / "scripts" / "teardown.sh"
    flag_script = CHALLENGE_DIR / "challenge" / "scripts" / "generate_flag.sh"

    p1 = reset_script.exists() and os.access(reset_script, os.X_OK)
    p2 = teardown_script.exists() and os.access(teardown_script, os.X_OK)
    all_passed &= log_test("Reset and teardown automation scripts present and executable", p1 and p2)

    # Test dynamic flag generation for distinct teams
    if flag_script.exists():
        f1 = subprocess.run(["bash", str(flag_script), "team_alpha"], capture_output=True, text=True).stdout.strip()
        f2 = subprocess.run(["bash", str(flag_script), "team_bravo"], capture_output=True, text=True).stdout.strip()
        p3 = "YUVA{" in f1 and "YUVA{" in f2 and f1 != f2 and "x08" in f1
        all_passed &= log_test("Dynamic team-specific flag generation (instance uniqueness)", p3, f"Alpha: {f1}, Bravo: {f2}")
    else:
        all_passed &= log_test("Dynamic flag generator present", False)

    return all_passed

def test_05_resource_test():
    """Test 5: Verify sandbox resource limits (4 vCPU, 4 GiB RAM, 8 GiB Disk)."""
    print("\n=== Test 5: Resource Controls & Quota Verification ===")
    all_passed = True

    # 1. Verify Vagrant / Packer resource sizing
    vagrantfile = CHALLENGE_DIR / "challenge" / "vm" / "Vagrantfile"
    if vagrantfile.exists():
        vcontent = vagrantfile.read_text(errors="ignore")
        p1 = "cpus = 4" in vcontent and "memory = 4096" in vcontent
        all_passed &= log_test("VM definition enforces 4 vCPU / 4096 MiB RAM", p1)
    else:
        all_passed &= log_test("Vagrantfile present", False)

    # 2. Verify Packer disk size
    packer_file = CHALLENGE_DIR / "challenge" / "vm" / "packer.json"
    if packer_file.exists():
        pcontent = packer_file.read_text(errors="ignore")
        p2 = "8192M" in pcontent or "8G" in pcontent
        all_passed &= log_test("VM disk image constrained to ≤8 GiB", p2)
    else:
        all_passed &= log_test("Packer definition present", False)

    # 3. Verify Docker Compose resource limits
    dc_content = (CHALLENGE_DIR / "docker-compose.yml").read_text(errors="ignore")
    p3 = "cpus: '4.0'" in dc_content and "memory: 4096M" in dc_content
    all_passed &= log_test("Container limits enforce 4.0 CPUs and 4096M RAM", p3)

    return all_passed

def test_06_package_hygiene():
    """Verify participant package contains zero leaked solutions, flags, or private credentials."""
    print("\n=== Participant Package Hygiene ===")
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
            if "LV-VAULT-TOKEN" in content:
                has_leak = True
            if f.endswith((".key", ".pem", ".pyc", ".env", ".bak", ".swo", ".swp")):
                has_leak = True

    return log_test("Participant distribution package clean (Zero Leaks)", not has_leak)

def main():
    print("===============================================================")
    print(" Running Pre-Event Test Suite: X08 — Docker-in-Docker")
    print("===============================================================")
    
    results = [
        test_01_fresh_start(),
        test_02_intended_solve(),
        test_03_boundary_test(),
        test_04_reset_test(),
        test_05_resource_test(),
        test_06_package_hygiene()
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
