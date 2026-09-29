#!/usr/bin/env python3
"""
Latveria Citadel Secret Distribution Engine — Secret Service
Listens exclusively on 127.0.0.1:8082.
Requires Challenge-Local Machine Identity Certificate (mTLS / Client Cert) to issue Secret Zero.
Enforces multi-tier trust validation:
- Unauthenticated (401)
- Low-Trust Identity: telemetry-worker (403)
- Authorized Identity: vault-operator (200 + Secret Zero Key)
"""

import os
import sys
import base64
import urllib.parse
from pathlib import Path
from flask import Flask, request, jsonify

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ca.pki_manager import pki_manager
from config.config_manager import state_manager

app = Flask(__name__)

AUTHORIZED_SAN = "spiffe://latveria.local/ns/core/sa/vault-operator"

@app.route("/api/v1/vault/info", methods=["GET"])
def vault_info():
    return jsonify({
        "service": "latveria-secret-service",
        "description": "Zero-Trust Machine Secret Distribution Engine",
        "authentication_method": "X.509 Client Certificate (Challenge CA)",
        "authorized_spiffe_id": AUTHORIZED_SAN,
        "status": "OPERATIONAL"
    }), 200

@app.route("/api/v1/vault/secret-zero", methods=["POST", "GET"])
def get_secret_zero():
    cert_pem = ""
    signature_b64 = None
    challenge_payload = None

    # Check header or body for client certificate
    raw_cert_header = request.headers.get("X-Client-Cert", "")
    if raw_cert_header:
        # Check if URL-encoded or base64 or raw
        try:
            decoded = urllib.parse.unquote(raw_cert_header)
            if "BEGIN CERTIFICATE" in decoded:
                cert_pem = decoded
            else:
                cert_pem = base64.b64decode(raw_cert_header).decode("utf-8")
        except Exception:
            cert_pem = raw_cert_header
    elif request.is_json:
        cert_pem = request.json.get("client_certificate", "")
        signature_b64 = request.json.get("signature")
        challenge_payload = request.json.get("challenge", "").encode("utf-8") if request.json.get("challenge") else None

    if not cert_pem:
        return jsonify({
            "status": "UNAUTHENTICATED",
            "error": "Missing client certificate. You must present an X.509 machine certificate issued by the Latveria Challenge Root CA.",
            "hint": "Pass certificate via 'X-Client-Cert' header or JSON 'client_certificate' field."
        }), 401

    # Validate certificate against Challenge CA
    is_valid, reason, cert_info = pki_manager.verify_client_certificate(
        cert_pem=cert_pem,
        signature_b64=signature_b64,
        challenge_data=challenge_payload
    )

    if not is_valid:
        return jsonify({
            "status": "INVALID_CERTIFICATE",
            "error": f"Certificate verification failed: {reason}",
            "hint": "Certificate must be signed by Latveria Root CA (Identity Service on port 8081)."
        }), 401

    # Check identity trust tier via SAN URIs
    san_uris = cert_info.get("san_uris", [])
    subject = cert_info.get("subject", "")

    if AUTHORIZED_SAN in san_uris or f"CN=vault-operator" in subject:
        # High-Trust Authorized Identity
        secret_zero_key = state_manager.get_secret_zero_key()
        return jsonify({
            "status": "AUTHORIZED",
            "access_tier": "AUTHORIZED_SECRET_ZERO",
            "identity": AUTHORIZED_SAN,
            "certificate_serial": cert_info.get("serial_number"),
            "secret_zero_key": secret_zero_key,
            "target_service": "http://127.0.0.1:8083/api/v1/doomsday/unseal",
            "instructions": "Present this Secret Zero key as Bearer token to the Protected Target Service to unseal the Sovereign Core."
        }), 200
    else:
        # Low-Trust / Telemetry Identity
        current_identity = san_uris[0] if san_uris else subject
        return jsonify({
            "status": "FORBIDDEN",
            "access_tier": "LOW_TRUST",
            "identity": current_identity,
            "error": f"Machine identity '{current_identity}' is not authorized to retrieve Secret Zero.",
            "required_identity": AUTHORIZED_SAN,
            "hint": "Obtain a high-trust machine certificate for 'vault-operator' from the Identity Service (port 8081) using the bootstrap mechanism."
        }), 403

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8082, debug=False)
