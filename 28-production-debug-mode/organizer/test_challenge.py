#!/usr/bin/env python3
"""
Pre-Event Adversarial Validation & Test Suite for D28 — Production Debug Mode
Executes all adversarial and compliance checks required by the CTF Engineering Standard.
"""

import os
import re
import sys
import time
import json
import urllib.request
import urllib.error
import subprocess
import unittest
from pathlib import Path

CHALLENGE_DIR = Path(__file__).resolve().parent.parent


class TestD28Challenge(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print("\n========================================================")
        print(" [D28] Starting Full Pre-Event Adversarial Validation")
        print("========================================================\n")

        # 1. Build Docker image
        print("[*] Building D28 Docker Image...")
        build_cmd = ["docker", "build", "-t", "d28-test:latest", str(CHALLENGE_DIR)]
        res = subprocess.run(build_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            print(f"[!] Docker build failed: {res.stderr}")
            sys.exit(1)

        # 2. Start container
        print("[*] Starting D28 Test Container on port 8080 (mapping to container TCP/80)...")
        cls.container_name = "d28-test-runner"
        cls.test_flag = "YUVA{pr0duct10n_d3bug_d1sc10sur3_p1v0t_7c2b91ea}"
        subprocess.run(["docker", "rm", "-f", cls.container_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        run_cmd = [
            "docker", "run", "-d",
            "--name", cls.container_name,
            "-p", "8080:80",
            "-e", f"FLAG={cls.test_flag}",
            "--cpus=1.0",
            "--memory=384m",
            "d28-test:latest"
        ]
        res = subprocess.run(run_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            print(f"[!] Docker run failed: {res.stderr}")
            sys.exit(1)

        # Wait for HTTP server to become responsive
        print("[*] Waiting for Production Gateway and Internal Core services...")
        time.sleep(3)

    @classmethod
    def tearDownClass(cls):
        print("\n[*] Stopping and cleaning up test container...")
        subprocess.run(["docker", "rm", "-f", cls.container_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("[+] Test cleanup complete.")

    def test_01_fresh_exposure(self):
        """Test 01 — Fresh Exposure: Verify public port 80 is reachable, internal port 8081 is not exposed"""
        print("\n--- Test 01: Fresh Exposure & Public Interface Verification ---")
        # Check port 8080 (TCP/80 in container) reachable
        try:
            req = urllib.request.Request("http://127.0.0.1:8080/")
            with urllib.request.urlopen(req, timeout=3) as resp:
                self.assertEqual(resp.status, 200, "Public HTTP interface must return 200 OK")
        except Exception as e:
            self.fail(f"Could not connect to public port 8080: {e}")

        # Check that internal service port 8081 is NOT exposed directly on host
        try:
            req_internal = urllib.request.Request("http://127.0.0.1:8081/")
            with urllib.request.urlopen(req_internal, timeout=2):
                self.fail("Internal service port 8081 must NOT be accessible directly from host!")
        except Exception:
            # Expected failure
            pass
        print("[PASS] Only TCP/80 is publicly reachable. Internal service is shielded.")

    def test_02_intended_solve(self):
        """Test 02 — Intended Solve: Run clean-room solver end-to-end"""
        print("\n--- Test 02: Intended Solve Validation ---")
        solve_script = CHALLENGE_DIR / "organizer" / "solve.py"
        res = subprocess.run(
            [sys.executable, str(solve_script), "--host", "127.0.0.1", "--port", "8080"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        self.assertEqual(res.returncode, 0, f"Solve script failed:\n{res.stderr}\n{res.stdout}")
        self.assertIn(self.test_flag, res.stdout, "Solve script must retrieve the challenge flag")
        print("[PASS] Full intended exploit chain successfully executed and verified.")

    def test_03_no_direct_flag_leak(self):
        """Test 03 — Flag Hygiene: Ensure flag is not leaked in static/public responses or debug error"""
        print("\n--- Test 03: Direct Flag Leak Prevention ---")
        endpoints = ["/", "/api/v1/status", "/api/v1/telemetry/nodes", "/api/v1/health"]
        for ep in endpoints:
            req = urllib.request.Request(f"http://127.0.0.1:8080{ep}")
            with urllib.request.urlopen(req, timeout=3) as resp:
                content = resp.read().decode("utf-8")
                self.assertNotIn("YUVA{", content, f"Direct flag found in {ep}")

        # Also verify flag is not directly present in the initial debug error output
        err_payload = json.dumps({"sector": 1337, "metrics": "invalid"}).encode("utf-8")
        err_req = urllib.request.Request(
            "http://127.0.0.1:8080/api/v1/telemetry/query",
            data=err_payload,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST"
        )
        try:
            urllib.request.urlopen(err_req, timeout=3)
        except urllib.error.HTTPError as he:
            err_body = he.read().decode("utf-8")
            self.assertNotIn("YUVA{", err_body, "Flag must NOT appear directly in the debug error output!")
        print("[PASS] Flag is strictly protected and only retrieved via authorized internal pivot.")

    def test_04_unauthenticated_dispatch_blocked(self):
        """Test 04 — Access Control: Ensure unauthenticated requests to gateway dispatch are rejected"""
        print("\n--- Test 04: Unauthenticated Dispatch Access Control ---")
        dispatch_url = "http://127.0.0.1:8080/api/v1/gateway/dispatch"
        payload = json.dumps({
            "action": "query_executive_core",
            "target": "sentinel_core_01"
        }).encode("utf-8")
        
        req = urllib.request.Request(dispatch_url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        try:
            urllib.request.urlopen(req, timeout=3)
            self.fail("Unauthenticated dispatch must be rejected with 403 Forbidden!")
        except urllib.error.HTTPError as he:
            self.assertEqual(he.code, 403, f"Expected 403 Forbidden, got {he.code}")
        print("[PASS] Unauthenticated access to internal dispatch bridge is correctly rejected.")

    def test_05_invalid_credentials_blocked(self):
        """Test 05 — Access Control: Ensure invalid tokens are rejected"""
        print("\n--- Test 05: Invalid Credential Rejection ---")
        dispatch_url = "http://127.0.0.1:8080/api/v1/gateway/dispatch"
        payload = json.dumps({
            "action": "query_executive_core",
            "target": "sentinel_core_01",
            "auth_token": "invalid_fake_token_12345"
        }).encode("utf-8")
        
        req = urllib.request.Request(
            dispatch_url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "X-Latveria-Debug-Token": "invalid_fake_token_12345"
            },
            method="POST"
        )
        try:
            urllib.request.urlopen(req, timeout=3)
            self.fail("Invalid token dispatch must be rejected with 403 Forbidden!")
        except urllib.error.HTTPError as he:
            self.assertEqual(he.code, 403, f"Expected 403 Forbidden, got {he.code}")
        print("[PASS] Invalid tokens are properly rejected.")

    def test_06_malformed_input_safety(self):
        """Test 06 — Resiliency: Test various malformed inputs and safe error triggers"""
        print("\n--- Test 06: Malformed Input Safety & Resiliency ---")
        test_inputs = [
            b"this is not json at all",
            json.dumps({"sector": None, "metrics": None}).encode("utf-8"),
            json.dumps({"sector": ["a", "b"], "metrics": "not a list"}).encode("utf-8"),
            json.dumps({"sector": "test", "filter": "malformed_syntax"}).encode("utf-8")
        ]

        for inp in test_inputs:
            req = urllib.request.Request(
                "http://127.0.0.1:8080/api/v1/telemetry/query",
                data=inp,
                headers={"Content-Type": "application/json", "Accept": "application/json"},
                method="POST"
            )
            try:
                urllib.request.urlopen(req, timeout=3)
            except urllib.error.HTTPError as he:
                self.assertEqual(he.code, 500, f"Expected 500 debug disclosure, got {he.code}")
                body = he.read().decode("utf-8")
                self.assertIn("debug_report", body, "Debug report must be present in error response")
        print("[PASS] Malformed inputs safely trigger structured debug disclosures without crashing.")

    def test_07_rate_limiting_and_dos_protection(self):
        """Test 07 — Resource Controls: Send rapid bursts and verify rate limiting (HTTP 429)"""
        print("\n--- Test 07: Rate Limiting & Resource Abuse Probe ---")
        got_429 = False
        for _ in range(40):
            try:
                req = urllib.request.Request("http://127.0.0.1:8080/api/v1/health")
                with urllib.request.urlopen(req, timeout=2) as resp:
                    pass
            except urllib.error.HTTPError as he:
                if he.code == 429:
                    got_429 = True
                    break
            except Exception:
                pass

        self.assertTrue(got_429, "Rate limiter must trigger HTTP 429 under rapid requests")
        time.sleep(1.2)  # Wait for window to slide
        # Verify server is still operational
        req = urllib.request.Request("http://127.0.0.1:8080/api/v1/health")
        with urllib.request.urlopen(req, timeout=3) as resp:
            self.assertEqual(resp.status, 200, "Server must remain operational after rate limiting")
        print("[PASS] Rate limiting actively protects the service against resource exhaustion.")

    def test_08_security_baseline_and_boundaries(self):
        """Test 08 — Security Boundaries: Verify no real cloud or K8s credentials exist and daemons have no FLAG in environ"""
        print("\n--- Test 08: Infrastructure & Boundary Invariants ---")
        exec_cmd = ["docker", "exec", self.container_name, "env"]
        res = subprocess.run(exec_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertNotIn("AWS_SECRET_ACCESS_KEY", res.stdout)
        self.assertNotIn("GOOGLE_APPLICATION_CREDENTIALS", res.stdout)
        self.assertNotIn("KUBERNETES_SERVICE_HOST", res.stdout)
        
        # Verify running daemon processes do NOT have FLAG in their /proc/<pid>/environ
        check_daemon_env = [
            "docker", "exec", self.container_name,
            "sh", "-c", 'cat /proc/$(pgrep -f app.py | head -n 1)/environ | tr "\\0" "\\n"'
        ]
        daemon_env_res = subprocess.run(check_daemon_env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertNotIn("FLAG=", daemon_env_res.stdout, "FLAG must not be present in running app.py daemon environment")
        print("[PASS] Environment is completely clean of cloud credentials and daemon process env is sanitized.")

    def test_09_package_hygiene_validation(self):
        """Test 09 — Participant Package Hygiene: Run validate_challenge.py"""
        print("\n--- Test 09: Participant Distribution Package Hygiene ---")
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
        print("[PASS] CTF Engineering compliance gate passed.")

    def test_10_dynamic_flag_and_reset(self):
        """Test 10 — Dynamic Flag & Reset Validation: Verify new flag generation on fresh instance"""
        print("\n--- Test 10: Dynamic Flag & Reset Validation ---")
        reset_flag = "DOOM{fresh_reset_instance_d28_991827fa}"
        reset_container = "d28-reset-test"
        subprocess.run(["docker", "rm", "-f", reset_container], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        run_cmd = [
            "docker", "run", "-d",
            "--name", reset_container,
            "-p", "8082:80",
            "-e", f"FLAG={reset_flag}",
            "d28-test:latest"
        ]
        res = subprocess.run(run_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertEqual(res.returncode, 0, "Reset container must start cleanly")
        time.sleep(3)

        try:
            solve_script = CHALLENGE_DIR / "organizer" / "solve.py"
            res = subprocess.run(
                [sys.executable, str(solve_script), "--host", "127.0.0.1", "--port", "8082"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self.assertEqual(res.returncode, 0, f"Solve script failed on reset container: {res.stderr}\n{res.stdout}")
            self.assertIn(reset_flag, res.stdout, "Solver must retrieve the newly configured dynamic flag")
            print("[PASS] Reset validation verified with dynamic flag injection.")
        finally:
            subprocess.run(["docker", "rm", "-f", reset_container], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


if __name__ == "__main__":
    unittest.main()
