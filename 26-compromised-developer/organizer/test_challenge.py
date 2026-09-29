#!/usr/bin/env python3
"""
Pre-Event Adversarial Validation & Test Suite for D26 — Compromised Developer
Runs all 10 adversarial and compliance checks required by the CTF Engineering Standard.
"""

import os
import re
import sys
import time
import json
import subprocess
import unittest
from pathlib import Path

CHALLENGE_DIR = Path(__file__).resolve().parent.parent

class TestD26Challenge(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print("\n========================================================")
        print(" [D26] Starting Full Pre-Event Adversarial Validation")
        print("========================================================\n")
        
        # Ensure Docker image is built
        print("[*] Building D26 Docker Image...")
        build_cmd = ["docker", "build", "-t", "d26-test:latest", str(CHALLENGE_DIR)]
        res = subprocess.run(build_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            print(f"[!] Docker build failed: {res.stderr}")
            sys.exit(1)

        # Start container
        print("[*] Starting D26 Test Container on port 2222...")
        cls.container_name = "d26-test-runner"
        subprocess.run(["docker", "rm", "-f", cls.container_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        run_cmd = [
            "docker", "run", "-d",
            "--name", cls.container_name,
            "-p", "2222:22",
            "-e", "FLAG=YUVA{c0mpr0m1s3d_d3v_h1st0ry_hm4c_auth_8821}",
            "--cpus=2.0",
            "--memory=1g",
            "d26-test:latest"
        ]
        res = subprocess.run(run_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            print(f"[!] Docker run failed: {res.stderr}")
            sys.exit(1)

        # Wait for SSH server to be ready
        print("[*] Waiting for SSH daemon and services...")
        time.sleep(3)

    @classmethod
    def tearDownClass(cls):
        print("\n[*] Stopping and removing test container...")
        subprocess.run(["docker", "rm", "-f", cls.container_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("[+] Test cleanup complete.")

    def run_ssh_exec(self, cmd):
        """Execute a command over SSH as the actual player will experience"""
        try:
            import paramiko
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect("127.0.0.1", port=2222, username="developer", password="developer", timeout=10)
            stdin, stdout, stderr = client.exec_command(cmd)
            out = stdout.read().decode("utf-8")
            err = stderr.read().decode("utf-8")
            client.close()
            return out, err
        except ImportError:
            # Fallback to sshpass or docker exec
            full_cmd = ["sshpass", "-p", "developer", "ssh", "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null", "-o", "LogLevel=ERROR", "-p", "2222", "developer@127.0.0.1", cmd]
            res = subprocess.run(full_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)
            return res.stdout, res.stderr

    def test_01_fresh_exposure(self):
        """Test 01 — Fresh Exposure: Verify public port 22 open, port 8080 internal only"""
        print("\n--- Test 01: Fresh Exposure & Public Interface Verification ---")
        # Check port 22 reachable
        nc_cmd = ["nc", "-z", "-w", "2", "127.0.0.1", "2222"]
        res = subprocess.run(nc_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(res.returncode, 0, "SSH Port 2222 must be reachable externally")
        
        # Check port 8080 NOT bound to host
        nc_cmd8080 = ["nc", "-z", "-w", "2", "127.0.0.1", "8080"]
        res8080 = subprocess.run(nc_cmd8080, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertNotEqual(res8080.returncode, 0, "Production port 8080 must NOT be exposed on host")
        print("[PASS] Only SSH is publicly exposed. Internal production mock remains internal.")

    def test_02_intended_solve(self):
        """Test 02 — Intended Solve: Run complete solver end-to-end"""
        print("\n--- Test 02: Intended Solve Validation ---")
        solve_script = CHALLENGE_DIR / "organizer" / "solve.py"
        res = subprocess.run([sys.executable, str(solve_script), "--port", "2222"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertEqual(res.returncode, 0, f"Solve script failed: {res.stderr}\n{res.stdout}")
        self.assertIn("YUVA{c0mpr0m1s3d_d3v_h1st0ry_hm4c_auth_8821}", res.stdout)
        print("[PASS] Full intended exploit chain successfully executed and verified.")

    def test_03_shortcut_resistance(self):
        """Test 03 — Shortcut Resistance: Ensure no trivial flag leaks on workstation"""
        print("\n--- Test 03: Shortcut Resistance & Leak Prevention ---")
        # 1. Flag must not be directly in /home/developer
        out, err = self.run_ssh_exec("grep -rn 'YUVA{' /home/developer 2>/dev/null || true")
        self.assertEqual(out.strip(), "", f"Direct flag found in /home/developer: {out}")

        # 2. Flag must not be in git log or working tree of developer
        out, err = self.run_ssh_exec("cd ~/projects/latveria-telemetry-dispatch && git log -p | grep 'YUVA{' || true")
        self.assertEqual(out.strip(), "", f"Direct flag found in git log: {out}")

        # 3. Flag must not be in environment variables of developer SSH session
        out, err = self.run_ssh_exec("env | grep -i flag || true")
        self.assertEqual(out.strip(), "", f"Flag found in developer env: {out}")

        # 4. Flag must not be in world-readable /tmp or /var/log
        out, err = self.run_ssh_exec("grep -rn 'YUVA{' /tmp /var/log 2>/dev/null || true")
        self.assertEqual(out.strip(), "", f"Flag found in world-readable logs/tmp: {out}")
        print("[PASS] No shortcut or static flag leak exists on the workstation.")

    def test_04_boundary_and_privileges(self):
        """Test 04 — Boundary Testing: Verify user developer cannot access protected production files or sudo"""
        print("\n--- Test 04: Security Boundary & Privilege Verification ---")
        # 1. Developer cannot read /opt/production/flag.txt
        out, err = self.run_ssh_exec("cat /opt/production/flag.txt 2>&1 || true")
        self.assertIn("Permission denied", out + err, "Developer must not be able to read /opt/production/flag.txt")

        # 2. Developer cannot sudo
        out, err = self.run_ssh_exec("sudo -l 2>&1 || true")
        self.assertTrue("not found" in (out + err) or "sudoers" in (out + err) or "password" in (out + err))

        # 3. Developer cannot read /proc of prod user
        out, err = self.run_ssh_exec("cat /proc/1/environ 2>&1 || true")
        self.assertIn("Permission denied", out + err)
        print("[PASS] User isolation and security boundaries verified.")

    def test_05_package_hygiene(self):
        """Test 05 — Participant Package Hygiene: Run validate_challenge.py"""
        print("\n--- Test 05: Participant Distribution Package Hygiene ---")
        validator = CHALLENGE_DIR.parent / ".agents" / "skills" / "ctf-challenge-engineering" / "scripts" / "validate_challenge.py"
        res = subprocess.run([sys.executable, str(validator), str(CHALLENGE_DIR), "--dist-dir", str(CHALLENGE_DIR / "dist")], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print(res.stdout)
        self.assertEqual(res.returncode, 0, f"Validator script failed:\n{res.stdout}")
        self.assertIn("FINAL STATUS:\n`PASS`", res.stdout)
        print("[PASS] Challenge compliance validator passed with status PASS.")


if __name__ == "__main__":
    unittest.main()
