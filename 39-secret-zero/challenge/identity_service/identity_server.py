#!/usr/bin/env python3
"""
Latveria Citadel Machine Identity Authority — Identity Service
Listens exclusively on 127.0.0.1:8081.
Issues X.509 Client Certificates signed by the dedicated Challenge-Local Root CA.
Validates bootstrap attestation token and issues requested SPIFFE machine identities.
"""

import os
import sys
from pathlib import Path
from flask import Flask, request, jsonify

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ca.pki_manager import pki_manager
from config.config_manager import state_manager

app = Flask(__name__)

ALLOWED_IDENTITIES = [
    "spiffe://latveria.local/ns/edge/sa/telemetry-worker",
    "spiffe://latveria.local/ns/core/sa/vault-operator"
]

@app.route("/api/v1/ca/info", methods=["GET"])
def ca_info():
    return jsonify({
        "status": "OPERATIONAL",
        "service": "latveria-machine-identity-ca",
        "ca_root_cert": pki_manager.get_root_ca_pem(),
        "allowed_identities": ALLOWED_IDENTITIES,
        "signing_policy": {
            "algorithm": "SHA256withRSA",
            "max_validity_days": 30,
            "requires_bootstrap_secret": True
        }
    }), 200

@app.route("/api/v1/ca/issue", methods=["POST"])
def issue_certificate():
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({
            "status": "ERROR",
            "error": "Invalid request. JSON body required with 'csr', 'bootstrap_secret', and optional 'requested_identity'."
        }), 400

    csr_pem = data.get("csr", "").strip()
    bootstrap_secret = data.get("bootstrap_secret", "").strip()
    requested_identity = data.get("requested_identity", "spiffe://latveria.local/ns/edge/sa/telemetry-worker").strip()

    if not csr_pem:
        return jsonify({
            "status": "ERROR",
            "error": "Missing 'csr' in PEM format."
        }), 400

    expected_bootstrap = state_manager.get_bootstrap_secret()
    if not bootstrap_secret or bootstrap_secret != expected_bootstrap:
        return jsonify({
            "status": "UNAUTHORIZED",
            "error": "Invalid or missing bootstrap attestation secret.",
            "hint": "Check the bootstrap agent configuration on the public node portal."
        }), 401

    if requested_identity not in ALLOWED_IDENTITIES:
        return jsonify({
            "status": "INVALID_IDENTITY",
            "error": f"Requested identity '{requested_identity}' is not permitted by CA policy.",
            "allowed_identities": ALLOWED_IDENTITIES
        }), 400

    role = "vault-operator" if "vault-operator" in requested_identity else "telemetry-worker"

    try:
        cert_pem, metadata = pki_manager.sign_csr(
            csr_pem=csr_pem,
            requested_identity_uri=requested_identity,
            role=role,
            validity_days=30
        )
        return jsonify({
            "status": "ISSUED",
            "message": f"Successfully issued machine certificate for {requested_identity}",
            "certificate": cert_pem,
            "metadata": metadata
        }), 200
    except Exception as e:
        return jsonify({
            "status": "SIGNING_FAILED",
            "error": f"Failed to sign CSR: {str(e)}"
        }), 400

@app.route("/api/v1/ca/rotate", methods=["POST"])
def rotate_ca():
    # Rotate CA and challenge state
    pki_manager.initialize_or_load_ca(force_rotate=True)
    state_manager.load_or_initialize_state(force_reset=True)
    return jsonify({
        "status": "ROTATED",
        "message": "Challenge CA and machine identity material rotated successfully.",
        "new_ca_root": pki_manager.get_root_ca_pem()
    }), 200

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8081, debug=False)
