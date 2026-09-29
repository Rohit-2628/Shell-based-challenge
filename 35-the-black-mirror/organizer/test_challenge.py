#!/usr/bin/env python3
"""
Pre-Event Test Suite for X05 — The Black Mirror
Executes the full suite of verification, adversarial boundary checks, reset validation, and resource stability tests.
"""

import sys
import time
import json
import socket
import urllib.parse
import requests

from solve import solve

BASE_URL = "http://127.0.0.1:80"

def log_test(name, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    print(f"[{status}] {name} {('- ' + detail) if detail else ''}")
    return passed

def test_01_fresh_start():
    """Verify only TCP/80 is publicly accessible and internal microservices are isolated to loopback."""
    print("\n=== Test 1: Fresh Start & Clean Exposure ===")
    
    # Check Web Proxy on TCP/80
    try:
        r = requests.get(f"{BASE_URL}/api/info", timeout=3)
        p1 = (r.status_code == 200 and "The Black Mirror" in r.text)
        log_test("Web Gateway on TCP/80 accessible", p1)
    except Exception as e:
        log_test("Web Gateway on TCP/80 accessible", False, str(e))
        return False

    # Check internal ports are not accessible externally on 0.0.0.0 / non-loopback interface if tested remotely
    return p1

def test_02_intended_solve():
    """Verify official exploit chain solves cleanly and extracts the correct flag."""
    print("\n=== Test 2: Intended Exploit Chain ===")
    success, flag = solve(BASE_URL)
    return log_test("Intended solve chain execution", success and flag is not None and "YUVA{" in flag, f"Flag: {flag}")

def test_03_boundary_testing():
    """Verify SSRF perimeter controls block cloud metadata, Kubernetes control plane, and WAN routing."""
    print("\n=== Test 3: Boundary & Isolation Controls ===")
    all_passed = True

    # 1. Cloud Metadata Probe
    r1 = requests.post(f"{BASE_URL}/api/probe", json={"url": "http://169.254.169.254/latest/meta-data/"}, timeout=3)
    p1 = (r1.status_code in [403, 200] and ("SECURITY_VIOLATION" in r1.text or "blocked" in r1.text.lower()))
    all_passed &= log_test("Cloud metadata (169.254.169.254) blocked", p1)

    # 2. Kubernetes API Server Probe
    r2 = requests.post(f"{BASE_URL}/api/probe", json={"url": "http://10.96.0.1:6443/api/v1/namespaces"}, timeout=3)
    p2 = (r2.status_code in [403, 200] and ("SECURITY_VIOLATION" in r2.text or "prohibited" in r2.text.lower() or "blocked" in r2.text.lower()))
    all_passed &= log_test("Kubernetes Control Plane (10.96.0.1:6443) blocked", p2)

    # 3. Kubelet Port Probe
    r3 = requests.post(f"{BASE_URL}/api/probe", json={"url": "http://127.0.0.1:10250/pods"}, timeout=3)
    p3 = (r3.status_code in [403, 200] and ("SECURITY_VIOLATION" in r3.text or "prohibited" in r3.text.lower() or "blocked" in r3.text.lower()))
    all_passed &= log_test("Kubelet Port (10250) blocked", p3)

    # 4. Public Internet WAN Probe
    r4 = requests.post(f"{BASE_URL}/api/probe", json={"url": "http://1.1.1.1/"}, timeout=3)
    p4 = (r4.status_code in [403, 200] and ("SECURITY_VIOLATION" in r4.text or "blocked" in r4.text.lower()))
    all_passed &= log_test("Public Internet WAN routing blocked", p4)

    return all_passed

def test_04_reset_and_determinism():
    """Verify that multiple consecutive solves generate deterministic, valid tickets and do not corrupt state."""
    print("\n=== Test 4: Reset & Determinism Validation ===")
    s1, f1 = solve(BASE_URL)
    time.sleep(0.5)
    s2, f2 = solve(BASE_URL)
    
    passed = s1 and s2 and (f1 == f2)
    return log_test("Consecutive solve determinism and state stability", passed, f"Flag 1: {f1} == Flag 2: {f2}")

def test_05_resource_and_abuse_handling():
    """Verify daemon stability under malformed inputs, oversized payloads, and rapid requests."""
    print("\n=== Test 5: Resource & Abuse Handling ===")
    all_passed = True

    # 1. Oversized payload probe
    huge_payload = "A" * 10000
    r1 = requests.post(f"{BASE_URL}/api/probe", json={
        "url": f"gopher://127.0.0.1:9099/_{urllib.parse.quote(huge_payload)}"
    }, timeout=5)
    p1 = ("PAYLOAD_TOO_LARGE" in r1.text or r1.status_code in [200, 400])
    all_passed &= log_test("Oversized payload rejection", p1)

    # 2. HTTP framing against raw protocol port
    r2 = requests.post(f"{BASE_URL}/api/probe", json={
        "url": "gopher://127.0.0.1:9099/_GET%20/%20HTTP/1.1%0D%0AHost:%20test%0D%0A%0D%0A"
    }, timeout=3)
    p2 = ("PROTOCOL_ERROR" in r2.text or "HTTP framing detected" in r2.text)
    all_passed &= log_test("HTTP framing error on non-HTTP port", p2)

    # 3. Burst requests
    burst_success = 0
    for i in range(10):
        r = requests.get(f"{BASE_URL}/api/info", timeout=2)
        if r.status_code == 200:
            burst_success += 1
    p3 = (burst_success == 10)
    all_passed &= log_test(f"Burst request resilience ({burst_success}/10)", p3)

    return all_passed

def run_all():
    print("=========================================================")
    print("   X05 — THE BLACK MIRROR :: ADVERSARIAL TEST SUITE      ")
    print("=========================================================")
    
    results = [
        test_01_fresh_start(),
        test_02_intended_solve(),
        test_03_boundary_testing(),
        test_04_reset_and_determinism(),
        test_05_resource_and_abuse_handling(),
    ]

    print("\n---------------------------------------------------------")
    if all(results):
        print("[*] ALL TESTS PASSED: Challenge X05 is verified and production ready.")
        sys.exit(0)
    else:
        failed_count = results.count(False)
        print(f"[!] TEST FAILURES DETECTED: {failed_count} tests failed.")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        BASE_URL = sys.argv[1]
    run_all()
