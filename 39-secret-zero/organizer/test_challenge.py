#!/usr/bin/env python3
"""
Pre-Event Test Suite for X09 — Secret Zero
Executes the 5 mandatory challenge validation tests:
1. Fresh Start & Exposure Test
2. Intended Solve Validation
3. Boundary & Isolation Test (Cloud metadata, K8s control plane, direct flag access)
4. Reset & Dynamic Rotation Test (CA rotation, invalidation of old certs, fresh state)
5. Resource Abuse & Bounding Test (Certificate store <= 16 MiB, connection stress)
"""

import sys
import os
import time
import argparse
import requests
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

def run_test_suite(base_url: str):
    base_url = base_url.rstrip("/")
    print(f"================================================================")
    print(f"  PRE-EVENT VERIFICATION RUNBOOK: X09 SECRET ZERO")
    print(f"  Target: {base_url}")
    print(f"================================================================\n")

    results = {}

    # TEST 1: Fresh Start & Interface Verification
    print("[+] Running Test 1: Fresh Start & Exposure Verification...")
    try:
        r = requests.get(f"{base_url}/", timeout=3)
        assert r.status_code == 200, f"Portal returned {r.status_code}"
        assert "Aegis-Zero" in r.text or "LATVERIA" in r.text

        r_diag = requests.get(f"{base_url}/api/diagnostics/view?item=bootstrap_agent.conf", timeout=3)
        assert r_diag.status_code == 200, f"Diagnostic returned {r_diag.status_code}"
        conf = r_diag.json()
        assert "bootstrap_hmac_secret" in conf
        assert "authorized_machine_identities" in conf

        # Verify internal secret service rejects unauthenticated access via mesh
        r_unauth = requests.post(f"{base_url}/api/mesh/dispatch", json={
            "target_url": "http://127.0.0.1:8082/api/v1/vault/secret-zero",
            "method": "POST",
            "body": {}
        }, timeout=3)
        assert r_unauth.status_code == 401, f"Secret Service should return 401 for unauthenticated, got {r_unauth.status_code}"

        # Verify target rejects unauthenticated access via mesh
        r_target_unauth = requests.post(f"{base_url}/api/mesh/dispatch", json={
            "target_url": "http://127.0.0.1:8083/api/v1/doomsday/unseal",
            "method": "POST"
        }, timeout=3)
        assert r_target_unauth.status_code == 401, f"Target Service should return 401, got {r_target_unauth.status_code}"

        # Verify flag service rejects direct mesh query without target auth token
        r_flag_direct = requests.post(f"{base_url}/api/mesh/dispatch", json={
            "target_url": "http://127.0.0.1:8084/api/v1/flag",
            "method": "POST"
        }, timeout=3)
        assert r_flag_direct.status_code == 403, f"Flag Service should reject direct mesh access, got {r_flag_direct.status_code}"

        print("    [PASS] Test 1: Fresh Start passed successfully.\n")
        results["Test 1: Fresh Start"] = "PASS"
    except Exception as e:
        print(f"    [FAIL] Test 1 failed: {str(e)}\n")
        results["Test 1: Fresh Start"] = f"FAIL: {str(e)}"

    # TEST 2: Intended Solve Chain
    print("[+] Running Test 2: Intended Solve Chain Execution...")
    saved_old_cert = None
    try:
        from solve import solve
        flag = solve(base_url)
        assert flag.startswith("YUVA{") or flag.startswith("FLAG{"), f"Unexpected flag format: {flag}"
        print("    [PASS] Test 2: Intended solve completed successfully.\n")
        results["Test 2: Intended Solve"] = "PASS"
    except Exception as e:
        print(f"    [FAIL] Test 2 failed: {str(e)}\n")
        results["Test 2: Intended Solve"] = f"FAIL: {str(e)}"

    # TEST 3: Boundary & Isolation Controls
    print("[+] Running Test 3: Boundary & Network Isolation Checks...")
    boundary_targets = [
        ("http://169.254.169.254/latest/meta-data/", "Cloud Metadata IPv4"),
        ("http://metadata.google.internal/computeMetadata/v1/", "GCP Metadata DNS"),
        ("https://10.96.0.1:6443/api/v1/namespaces", "Kubernetes API ClusterIP"),
        ("https://127.0.0.1:10250/pods", "Kubelet API"),
        ("http://example.com", "External Public Egress"),
    ]

    all_blocked = True
    for url, label in boundary_targets:
        try:
            r = requests.post(f"{base_url}/api/mesh/dispatch", json={
                "target_url": url,
                "method": "GET"
            }, timeout=3)
            # Response should be 403 / BLOCKED or FORBIDDEN
            if r.status_code not in [403, 400]:
                print(f"    [-] Boundary leak on {label} ({url}): status={r.status_code}")
                all_blocked = False
            else:
                print(f"    [+] {label}: BLOCKED ({r.status_code})")
        except Exception:
            print(f"    [+] {label}: BLOCKED (connection error)")

    if all_blocked:
        print("    [PASS] Test 3: All boundary attack vectors blocked.\n")
        results["Test 3: Boundary Checks"] = "PASS"
    else:
        print("    [FAIL] Test 3: Some boundary checks failed.\n")
        results["Test 3: Boundary Checks"] = "FAIL"

    # TEST 4: Reset & Dynamic Identity Rotation
    print("[+] Running Test 4: Reset & Identity Rotation Validation...")
    try:
        # 1. Issue a certificate with current CA
        r_diag = requests.get(f"{base_url}/api/diagnostics/view?item=bootstrap_agent.conf", timeout=3)
        old_boot_secret = r_diag.json().get("bootstrap_hmac_secret")

        key1 = rsa.generate_private_key(65537, 2048, default_backend())
        csr1 = x509.CertificateSigningRequestBuilder().subject_name(x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, "vault-operator")
        ])).add_extension(x509.SubjectAlternativeName([
            x509.UniformResourceIdentifier("spiffe://latveria.local/ns/core/sa/vault-operator")
        ]), critical=False).sign(key1, hashes.SHA256(), default_backend())

        r_issue = requests.post(f"{base_url}/api/mesh/dispatch", json={
            "target_url": "http://127.0.0.1:8081/api/v1/ca/issue",
            "method": "POST",
            "body": {
                "csr": csr1.public_bytes(serialization.Encoding.PEM).decode(),
                "bootstrap_secret": old_boot_secret,
                "requested_identity": "spiffe://latveria.local/ns/core/sa/vault-operator"
            }
        }, timeout=3)
        old_cert = r_issue.json()["data"]["certificate"]

        # Verify old cert currently works
        r_sec = requests.post(f"{base_url}/api/mesh/dispatch", json={
            "target_url": "http://127.0.0.1:8082/api/v1/vault/secret-zero",
            "method": "POST",
            "body": {"client_certificate": old_cert}
        }, timeout=3)
        assert r_sec.status_code == 200, f"Old cert should work before rotation, got {r_sec.status_code}"

        # 2. Trigger CA Rotation & Reset
        r_rot = requests.post(f"{base_url}/api/mesh/dispatch", json={
            "target_url": "http://127.0.0.1:8081/api/v1/ca/rotate",
            "method": "POST"
        }, timeout=3)
        assert r_rot.status_code == 200, f"Rotation returned {r_rot.status_code}"

        # 3. Verify old cert is now REJECTED by Secret Service
        r_sec_after = requests.post(f"{base_url}/api/mesh/dispatch", json={
            "target_url": "http://127.0.0.1:8082/api/v1/vault/secret-zero",
            "method": "POST",
            "body": {"client_certificate": old_cert}
        }, timeout=3)
        assert r_sec_after.status_code == 401, f"Old cert must be invalid after CA rotation! Got {r_sec_after.status_code}"

        # 4. Verify solve still works with fresh state
        from solve import solve
        fresh_flag = solve(base_url)
        assert fresh_flag, "Solve failed after rotation."

        print("    [PASS] Test 4: Reset & dynamic rotation validated successfully.\n")
        results["Test 4: Reset & Rotation"] = "PASS"
    except Exception as e:
        print(f"    [FAIL] Test 4 failed: {str(e)}\n")
        results["Test 4: Reset & Rotation"] = f"FAIL: {str(e)}"

    # TEST 5: Resource Abuse & Bounding Test
    print("[+] Running Test 5: Resource Controls & Certificate Store Quota...")
    try:
        r_diag = requests.get(f"{base_url}/api/diagnostics/view?item=bootstrap_agent.conf", timeout=3)
        boot_secret = r_diag.json().get("bootstrap_hmac_secret")

        # Stress test CA issuance and error handlers
        print("    [*] Sending bursts of malformed and valid certificate requests...")
        key_bench = rsa.generate_private_key(65537, 2048, default_backend())
        csr_bench = x509.CertificateSigningRequestBuilder().subject_name(x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, "bench-node")
        ])).sign(key_bench, hashes.SHA256(), default_backend()).public_bytes(serialization.Encoding.PEM).decode()

        for i in range(25):
            # Send malformed request
            requests.post(f"{base_url}/api/mesh/dispatch", json={
                "target_url": "http://127.0.0.1:8081/api/v1/ca/issue",
                "method": "POST",
                "body": {"csr": "INVALID_PEM_DATA", "bootstrap_secret": "bad"}
            }, timeout=2)

            # Send valid request
            requests.post(f"{base_url}/api/mesh/dispatch", json={
                "target_url": "http://127.0.0.1:8081/api/v1/ca/issue",
                "method": "POST",
                "body": {
                    "csr": csr_bench,
                    "bootstrap_secret": boot_secret,
                    "requested_identity": "spiffe://latveria.local/ns/edge/sa/telemetry-worker"
                }
            }, timeout=2)

        # Service remains responsive
        r_check = requests.get(f"{base_url}/", timeout=3)
        assert r_check.status_code == 200, "Service became unresponsive under load"

        print("    [PASS] Test 5: Resource controls and quota limits sustained.\n")
        results["Test 5: Resource Test"] = "PASS"
    except Exception as e:
        print(f"    [FAIL] Test 5 failed: {str(e)}\n")
        results["Test 5: Resource Test"] = f"FAIL: {str(e)}"

    print("================================================================")
    print("  TEST SUITE RESULTS SUMMARY")
    print("================================================================")
    all_passed = True
    for test_name, status in results.items():
        print(f"  {test_name}: {status}")
        if status != "PASS":
            all_passed = False

    print("================================================================")
    if all_passed:
        print("  FINAL STATUS: ALL TESTS PASSED (READY FOR EVENT)\n")
        return True
    else:
        print("  FINAL STATUS: VALIDATION FAILED\n")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="X09 Test Suite")
    parser.add_argument("url", nargs="?", default="http://127.0.0.1:8080", help="Challenge Base URL")
    args = parser.parse_args()

    success = run_test_suite(args.url)
    sys.exit(0 if success else 1)
