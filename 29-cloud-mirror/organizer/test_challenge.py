#!/usr/bin/env python3
"""
Pre-Event Adversarial Validation & Test Suite for D29 — Cloud Mirror
Tests:
1. Fresh Start & Public Interface Exposure (TCP/80 only)
2. Intended Solve (Clean-room SSRF -> Metadata -> Object Store -> Flag)
3. Security Boundary & Metadata/Control-Plane Protection
4. Reset & Lifecycle Dynamic Flag Validation
5. Resource Abuse & Rate Limiting Stability
6. Participant Package Hygiene & Safety Compliance Gate
"""

import json
import os
import subprocess
import sys
import time
import unittest
import urllib.request
import urllib.error
from pathlib import Path

CHALLENGE_DIR = Path(__file__).resolve().parent.parent

def wait_for_gateway(url: str = "http://127.0.0.1:8080/api/v1/health", max_retries: int = 15, delay: float = 0.5):
    """Poll health endpoint until active."""
    for _ in range(max_retries):
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=2) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(delay)
    return False

class TestD29Challenge(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print("\n========================================================")
        print(" [D29] Starting Full Pre-Event Adversarial Validation")
        print("========================================================\n")

        # 1. Build Docker image
        print("[*] Building D29 Docker Image...")
        build_cmd = ["docker", "build", "-t", "d29-test:latest", str(CHALLENGE_DIR)]
        res = subprocess.run(build_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            print(f"[!] Docker build failed:\n{res.stderr}")
            sys.exit(1)

        # 2. Run container
        print("[*] Starting D29 Test Container on port 8080:80...")
        cls.container_name = "d29-test-runner"
        subprocess.run(["docker", "rm", "-f", cls.container_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        run_cmd = [
            "docker", "run", "-d",
            "--name", cls.container_name,
            "-p", "8080:80",
            "-e", "FLAG=YUVA{cl0ud_m1rr0r_ssrf_m3t4d4t4_0bj_st0r3_7a9e2f}",
            "--cpus=2.0",
            "--memory=768m",
            "d29-test:latest"
        ]
        res = subprocess.run(run_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            print(f"[!] Docker run failed:\n{res.stderr}")
            sys.exit(1)

        print("[*] Waiting for services to initialize...")
        if not wait_for_gateway():
            print("[!] Timed out waiting for Cloud Mirror gateway to become healthy!")
            sys.exit(1)

    @classmethod
    def tearDownClass(cls):
        print("\n[*] Stopping and cleaning up test container...")
        subprocess.run(["docker", "rm", "-f", cls.container_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("[+] Test cleanup complete.")

    def test_01_fresh_exposure(self):
        """Test 01 — Fresh Exposure: Verify public port 80 is reachable and internal services are private"""
        print("\n--- Test 01: Fresh Exposure & Public Interface Verification ---")
        
        # Check HTTP port 8080 (mapped from 80)
        req = urllib.request.Request("http://127.0.0.1:8080/")
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            body = resp.read().decode("utf-8")
            self.assertIn("LATVERIAN ORBITAL DEFENSE", body)
            self.assertIn("Cloud Mirror", body)

        # Check that internal daemons are NOT exposed on host ports
        for forbidden_port in [8181, 9000]:
            nc_cmd = ["nc", "-z", "-w", "1", "127.0.0.1", str(forbidden_port)]
            res = subprocess.run(nc_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertNotEqual(res.returncode, 0, f"Internal daemon port {forbidden_port} must not be exposed on host!")

        print("[PASS] Only documented public interface (TCP/80) is accessible.")

    def test_02_intended_solve(self):
        """Test 02 — Intended Solve: Run automated solver end-to-end"""
        print("\n--- Test 02: Intended Solve Validation ---")
        solve_script = CHALLENGE_DIR / "organizer" / "solve.py"
        res = subprocess.run(
            [sys.executable, str(solve_script), "--url", "http://127.0.0.1:8080"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        self.assertEqual(res.returncode, 0, f"Solve script failed:\n{res.stderr}\n{res.stdout}")
        self.assertIn("YUVA{cl0ud_m1rr0r_ssrf_m3t4d4t4_0bj_st0r3_7a9e2f}", res.stdout)
        print("[PASS] Full intended exploit chain executed cleanly.")

    def test_03_boundary_and_metadata_protection(self):
        """Test 03 — Boundary Protection: Verify SSRF blocks K8s API & private buckets reject bad auth"""
        print("\n--- Test 03: Security Boundary & Metadata Protection ---")
        
        # 1. Test SSRF blocking of Kubernetes control plane
        payload_k8s = {"url": "https://kubernetes.default.svc:443/api/v1"}
        req_k8s = urllib.request.Request(
            "http://127.0.0.1:8080/api/v1/fetch",
            data=json.dumps(payload_k8s).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req_k8s, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data.get("status"), "blocked", "K8s API query must be blocked!")

        # 2. Test SSRF blocking of Kubelet port 10250
        payload_kubelet = {"url": "http://127.0.0.1:10250/pods"}
        req_kubelet = urllib.request.Request(
            "http://127.0.0.1:8080/api/v1/fetch",
            data=json.dumps(payload_kubelet).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req_kubelet, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data.get("status"), "blocked", "Kubelet probe must be blocked!")

        # 3. Test Object Store rejection of unauthenticated requests to private bucket
        payload_unauth = {"url": "http://storage.internal/api/v1/storage/classified-orbital-mirror"}
        req_unauth = urllib.request.Request(
            "http://127.0.0.1:8080/api/v1/fetch",
            data=json.dumps(payload_unauth).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req_unauth, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data.get("http_status"), 401, "Unauthenticated access to classified bucket must return 401 Unauthorized")

        # 4. Test Object Store rejection of decoy / invalid token
        payload_decoy = {
            "url": "http://storage.internal/api/v1/storage/classified-orbital-mirror",
            "headers": {"Authorization": "Bearer invalid_decoy_token_9981"}
        }
        req_decoy = urllib.request.Request(
            "http://127.0.0.1:8080/api/v1/fetch",
            data=json.dumps(payload_decoy).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req_decoy, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data.get("http_status"), 403, "Invalid token must return 403 Forbidden")

        print("[PASS] Security boundaries, metadata isolation, and object store auth verification passed.")

    def test_04_reset_and_dynamic_flag(self):
        """Test 04 — Reset Test: Recreate container with new flag and verify state update"""
        print("\n--- Test 04: Reset & Dynamic Flag Validation ---")
        new_flag = "DOOM{d29_reset_dyn_flag_verified_89a0b1}"
        
        # Stop existing container and launch new one
        subprocess.run(["docker", "rm", "-f", self.container_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        run_cmd = [
            "docker", "run", "-d",
            "--name", self.container_name,
            "-p", "8080:80",
            "-e", f"FLAG={new_flag}",
            "--cpus=2.0",
            "--memory=768m",
            "d29-test:latest"
        ]
        res = subprocess.run(run_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertEqual(res.returncode, 0, "Container recreation failed")
        
        if not wait_for_gateway():
            self.fail("Gateway did not become healthy after container reset!")

        # Run solver again
        solve_script = CHALLENGE_DIR / "organizer" / "solve.py"
        res = subprocess.run(
            [sys.executable, str(solve_script), "--url", "http://127.0.0.1:8080"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        self.assertEqual(res.returncode, 0, f"Solve script failed after reset:\n{res.stderr}\n{res.stdout}")
        self.assertIn(new_flag, res.stdout, "Solver did not recover the newly generated reset flag!")
        print("[PASS] Reset validation verified: Fresh container yields fresh dynamic flag.")

    def test_05_resource_and_rate_limiting(self):
        """Test 05 — Resource Controls: Test rate limiting and repeated SSRF requests"""
        print("\n--- Test 05: Resource Controls & Rate Limiting Stability ---")
        
        # Dispatch rapid requests to test rate limiter behavior
        rate_limit_triggered = False
        for i in range(25):
            try:
                payload = {"url": "http://storage.internal/api/v1/storage/public-assets/theme.css"}
                req = urllib.request.Request(
                    "http://127.0.0.1:8080/api/v1/fetch",
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=2) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    if data.get("error") == "RateLimitExceeded" or data.get("http_status") == 429:
                        rate_limit_triggered = True
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    rate_limit_triggered = True
            except Exception:
                pass

        self.assertTrue(rate_limit_triggered, "Rate limiting (429) must trigger under rapid burst traffic.")
        
        # Verify service recovers cleanly after brief wait
        time.sleep(1.2)
        health_req = urllib.request.Request("http://127.0.0.1:8080/api/v1/health")
        with urllib.request.urlopen(health_req, timeout=3) as resp:
            self.assertEqual(resp.status, 200)

        print("[PASS] Rate limiting and resource stability verified.")

    def test_06_package_hygiene(self):
        """Test 06 — Participant Package Hygiene: Run validate_challenge.py"""
        print("\n--- Test 06: Participant Distribution Package Hygiene ---")
        validator = CHALLENGE_DIR.parent / ".agents" / "skills" / "ctf-challenge-engineering" / "scripts" / "validate_challenge.py"
        res = subprocess.run(
            [sys.executable, str(validator), str(CHALLENGE_DIR), "--dist-dir", str(CHALLENGE_DIR / "dist")],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        print(res.stdout)
        self.assertEqual(res.returncode, 0, f"Validator script failed:\n{res.stdout}")
        self.assertIn("FINAL STATUS:\n`PASS`", res.stdout)
        print("[PASS] Challenge compliance validator passed with status PASS.")


if __name__ == "__main__":
    unittest.main()
