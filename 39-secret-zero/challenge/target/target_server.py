#!/usr/bin/env python3
"""
Latveria Citadel Protected Target Service — Sovereign Doomsday Vault
Listens exclusively on 127.0.0.1:8083.
Requires Secret Zero unseal key obtained from the Secret Service to unlock and release flag.
"""

import os
import sys
import requests
from pathlib import Path
from flask import Flask, request, jsonify

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config.config_manager import state_manager

app = Flask(__name__)

FLAG_SERVICE_URL = "http://127.0.0.1:8084/api/v1/flag"

@app.route("/api/v1/health", methods=["GET"])
def health():
    return jsonify({
        "status": "HEALTHY",
        "service": "latveria-sovereign-target",
        "vault_state": "SEALED",
        "required_credential": "Secret Zero Master Key"
    }), 200

@app.route("/api/v1/doomsday/unseal", methods=["POST", "GET"])
def unseal_vault():
    auth_header = request.headers.get("Authorization", "")
    secret_key = ""
    if auth_header.startswith("Bearer "):
        secret_key = auth_header[7:].strip()
    elif request.is_json:
        secret_key = request.json.get("secret_zero_key", "")

    expected_secret = state_manager.get_secret_zero_key()

    if not secret_key:
        return jsonify({
            "status": "UNAUTHENTICATED",
            "error": "Missing Secret Zero authorization token.",
            "hint": "Authenticate to the internal Secret Service (port 8082) using an authorized machine certificate to obtain Secret Zero."
        }), 401

    if secret_key != expected_secret:
        return jsonify({
            "status": "FORBIDDEN",
            "error": "Invalid Secret Zero unseal key. Access to Sovereign Target rejected."
        }), 403

    # Forward to isolated flag service
    target_token = state_manager.get_target_token()
    try:
        resp = requests.post(
            FLAG_SERVICE_URL,
            headers={"Authorization": f"Bearer {target_token}"},
            timeout=3
        )
        if resp.status_code == 200:
            flag_data = resp.json()
            return jsonify({
                "status": "UNSEALED",
                "message": "Doomsday Vault unsealed successfully! Sovereign Core online.",
                "target_node": "LATVERIA-DOOMSDAY-CORE-PRIME",
                "flag": flag_data.get("flag")
            }), 200
        else:
            return jsonify({
                "status": "ERROR",
                "error": "Failed to retrieve flag from Flag Service."
            }), 500
    except Exception as e:
        return jsonify({
            "status": "ERROR",
            "error": f"Connection to flag vault failed: {str(e)}"
        }), 500

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8083, debug=False)
