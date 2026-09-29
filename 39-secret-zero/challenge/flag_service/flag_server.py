#!/usr/bin/env python3
"""
Latveria Citadel Isolated Flag Service
Listens exclusively on 127.0.0.1:8084.
Releases flag only to the authorized Sovereign Target upon valid unseal verification.
"""

import os
import sys
from pathlib import Path
from flask import Flask, request, jsonify

# Add parent path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config.config_manager import state_manager

app = Flask(__name__)

@app.route("/api/v1/health", methods=["GET"])
def health():
    return jsonify({"status": "HEALTHY", "service": "latveria-sovereign-flag-vault"}), 200

@app.route("/api/v1/flag", methods=["POST"])
def retrieve_flag():
    auth_header = request.headers.get("Authorization", "")
    target_token = state_manager.get_target_token()

    if not auth_header or auth_header != f"Bearer {target_token}":
        return jsonify({
            "status": "FORBIDDEN",
            "error": "Direct access denied. Flag release requires authorized Target authorization."
        }), 403

    flag = state_manager.get_flag()
    return jsonify({
        "status": "SUCCESS",
        "message": "Doomsday Sovereign Flag Vault unlocked.",
        "flag": flag
    }), 200

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8084, debug=False)
