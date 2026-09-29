#!/usr/bin/env python3
"""
Pre-Event Adversarial Validation & Test Suite for D27 — Private Container Registry
Runs all required adversarial, layer forensic, shortcut resistance, boundary,
and compliance checks.
"""

import gzip
import io
import json
import os
import re
import subprocess
import sys
import tarfile
import time
import unittest
import urllib.request
import urllib.error
from pathlib import Path

CHALLENGE_DIR = Path(__file__).resolve().parent.parent

class TestD27Challenge(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print("\n========================================================")
        print(" [D27] Starting Full Pre-Event Adversarial Validation")
        print("========================================================\n")

        # 1. Build Docker image
        print("[*] Building D27 Docker Image...")
        build_cmd = ["docker", "build", "-t", "d27-test:latest", str(CHALLENGE_DIR)]
        res = subprocess.run(build_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            print(f"[!] Docker build failed:\n{res.stderr}")
            sys.exit(1)

        # 2. Run container
        print("[*] Starting D27 Test Container on ports 8080:80 and 2222:22...")
        cls.container_name = "d27-test-runner"
        subprocess.run(["docker", "rm", "-f", cls.container_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        run_cmd = [
            "docker", "run", "-d",
            "--name", cls.container_name,
            "-p", "8080:80",
            "-p", "2222:22",
            "-e", "FLAG=YUVA{pr1v4t3_r3g1stry_l4y3r_3xf1ltr4t10n_9901}",
            "--cpus=2.0",
            "--memory=1g",
            "d27-test:latest"
        ]
        res = subprocess.run(run_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            print(f"[!] Docker run failed:\n{res.stderr}")
            sys.exit(1)

        print("[*] Waiting for services to initialize...")
        time.sleep(4)

    @classmethod
    def tearDownClass(cls):
        print("\n[*] Stopping and cleaning up test container...")
        subprocess.run(["docker", "rm", "-f", cls.container_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("[+] Test cleanup complete.")

    def run_ssh_exec(self, cmd: str):
        """Execute a command inside the container as user developer"""
        exec_cmd = ["docker", "exec", "-u", "developer", self.container_name, "bash", "-c", cmd]
        return subprocess.run(exec_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    def test_01_fresh_exposure(self):
        """Test 01 — Fresh Exposure: Verify public ports 80 (HTTP) and 22 (SSH) are reachable"""
        print("\n--- Test 01: Fresh Exposure & Public Interface Verification ---")
        # Check HTTP port 8080 (mapped from 80)
        req = urllib.request.Request("http://127.0.0.1:8080/")
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            body = resp.read().decode("utf-8")
            self.assertIn("State Container Registry v2", body)

        # Check Registry API /v2/_catalog
        req_cat = urllib.request.Request("http://127.0.0.1:8080/v2/_catalog")
        with urllib.request.urlopen(req_cat, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertIn("latveria/orbital-sentinel", data["repositories"])

        # Check SSH port 2222 reachable
        nc_cmd = ["nc", "-z", "-w", "2", "127.0.0.1", "2222"]
        res = subprocess.run(nc_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(res.returncode, 0, "SSH Port 2222 must be reachable")
        print("[PASS] Documented gateway interfaces (HTTP port 80 & SSH port 22) verified active.")

    def test_02_intended_solve(self):
        """Test 02 — Intended Solve: Run automated solver end-to-end"""
        print("\n--- Test 02: Intended Solve Validation ---")
        solve_script = CHALLENGE_DIR / "organizer" / "solve.py"
        res = subprocess.run(
            [sys.executable, str(solve_script), "--container", self.container_name, "--mode", "container"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        self.assertEqual(res.returncode, 0, f"Solve script failed:\n{res.stderr}\n{res.stdout}")
        self.assertIn("YUVA{pr1v4t3_r3g1stry_l4y3r_3xf1ltr4t10n_9901}", res.stdout)
        print("[PASS] Full intended exploit chain executed successfully and verified.")

    def test_03_image_layer_forensics_validation(self):
        """Test 03 — Image Layer Forensics: Verify historical vs current image isolation"""
        print("\n--- Test 03: Image Layer Forensics & Historical Secret Isolation ---")
        # 1. Fetch latest manifest
        req_latest = urllib.request.Request(
            "http://127.0.0.1:8080/v2/latveria/orbital-sentinel/manifests/latest",
            headers={"Accept": "application/vnd.docker.distribution.manifest.v2+json"}
        )
        with urllib.request.urlopen(req_latest, timeout=5) as resp:
            latest_man = json.loads(resp.read().decode("utf-8"))
        
        # Check all layers of latest image: none must contain orbital_vault.conf or the secret
        for layer in latest_man["layers"]:
            blob = urllib.request.urlopen(f"http://127.0.0.1:8080/v2/latveria/orbital-sentinel/blobs/{layer['digest']}").read()
            with gzip.GzipFile(fileobj=io.BytesIO(blob), mode="rb") as gz:
                with tarfile.open(fileobj=gz) as tar:
                    for m in tar.getmembers():
                        self.assertNotIn("orbital_vault.conf", m.name, "orbital_vault.conf MUST NOT exist in latest image layers!")

        # 2. Fetch v1.0.0 manifest
        req_v1 = urllib.request.Request(
            "http://127.0.0.1:8080/v2/latveria/orbital-sentinel/manifests/v1.0.0",
            headers={"Accept": "application/vnd.docker.distribution.manifest.v2+json"}
        )
        with urllib.request.urlopen(req_v1, timeout=5) as resp:
            v1_man = json.loads(resp.read().decode("utf-8"))

        # Check v1.0.0 layers: layer 3 MUST contain orbital_vault.conf
        found_secret = False
        for layer in v1_man["layers"]:
            blob = urllib.request.urlopen(f"http://127.0.0.1:8080/v2/latveria/orbital-sentinel/blobs/{layer['digest']}").read()
            try:
                with gzip.GzipFile(fileobj=io.BytesIO(blob), mode="rb") as gz:
                    with tarfile.open(fileobj=gz) as tar:
                        for m in tar.getmembers():
                            if "orbital_vault.conf" in m.name:
                                f_content = tar.extractfile(m).read().decode("utf-8")
                                self.assertIn("latv_vault_sec_89f2a481c90e37b2d5140e678a119c8f", f_content)
                                found_secret = True
            except Exception:
                pass
        self.assertTrue(found_secret, "Historical tag v1.0.0 must contain the secret in its historical layer.")

        # 3. Flag MUST NOT be anywhere inside the registry blobs or manifests
        res = subprocess.run(
            ["docker", "exec", self.container_name, "grep", "-rn", "YUVA{", "/var/lib/latveria-registry"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        self.assertEqual(res.stdout.strip(), "", "Flag MUST NOT be inside any registry layer or metadata!")
        print("[PASS] Image layer forensic isolation verified: latest is clean, v1.0.0 holds historical secret, flag is absent from registry.")

    def test_04_shortcut_resistance(self):
        """Test 04 — Shortcut Resistance & Final Service Authentication Checks"""
        print("\n--- Test 04: Shortcut Resistance & Auth Rejections ---")
        # 1. Flag not in /home/developer
        res = self.run_ssh_exec("grep -rn 'YUVA{' /home/developer 2>/dev/null || true")
        self.assertEqual(res.stdout.strip(), "", "Direct flag found in /home/developer")

        # 2. Flag not in files on workstation
        res = self.run_ssh_exec("grep -rn 'YUVA{' /challenge/workstation /tmp /var/log/nginx 2>/dev/null || true")
        self.assertEqual(res.stdout.strip(), "", "Flag found in world-readable logs/workstation files")

        # 3. Test Vault Service rejection of anonymous requests
        res = self.run_ssh_exec("curl -s -X POST http://127.0.0.1:8080/api/v1/vault/override")
        data = json.loads(res.stdout)
        self.assertEqual(data.get("status"), "UNAUTHORIZED")

        # 4. Test Vault Service rejection of decoy tokens
        res_decoy = self.run_ssh_exec("curl -s -X POST http://127.0.0.1:8080/api/v1/vault/override -H 'X-Latverian-Token: latv_test_auth_token_sample_non_functional'")
        data_decoy = json.loads(res_decoy.stdout)
        self.assertEqual(data_decoy.get("status"), "FORBIDDEN")
        self.assertEqual(data_decoy.get("error"), "DECOY_TOKEN_REJECTED")

        # 5. Test Vault Service rejection of arbitrary token
        res_bad = self.run_ssh_exec("curl -s -X POST http://127.0.0.1:8080/api/v1/vault/override -H 'X-Latverian-Token: invalid_random_token_12345'")
        data_bad = json.loads(res_bad.stdout)
        self.assertEqual(data_bad.get("status"), "FORBIDDEN")
        self.assertEqual(data_bad.get("error"), "INVALID_TOKEN")
        print("[PASS] Shortcut resistance verified: Anonymous, decoy, and invalid tokens properly rejected.")

    def test_05_boundary_and_privileges(self):
        """Test 05 — Boundary Testing: Verify user developer cannot access protected files or modify registry"""
        print("\n--- Test 05: Security Boundary & Privilege Verification ---")
        # 1. Developer cannot read /opt/vault/flag.txt directly
        res = self.run_ssh_exec("cat /opt/vault/flag.txt 2>&1 || true")
        self.assertIn("Permission denied", res.stdout + res.stderr)

        # 2. Developer cannot sudo
        res = self.run_ssh_exec("sudo -l 2>&1 || true")
        self.assertTrue("not found" in (res.stdout + res.stderr) or "sudoers" in (res.stdout + res.stderr) or res.returncode != 0)

        # 3. Developer cannot read vault daemon process /proc
        res = self.run_ssh_exec("cat /proc/1/environ 2>&1 || true")
        self.assertIn("Permission denied", res.stdout + res.stderr)

        # 4. Registry rejects write operations (POST / PUT / DELETE)
        res_post = subprocess.run(
            ["curl", "-s", "-X", "POST", "http://127.0.0.1:8080/v2/latveria/orbital-sentinel/blobs/uploads/"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        self.assertIn("DENIED", res_post.stdout)
        print("[PASS] Security boundary, non-root user separation, and read-only registry verified.")

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
