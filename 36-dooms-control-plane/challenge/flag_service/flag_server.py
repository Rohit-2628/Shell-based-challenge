#!/usr/bin/env python3
"""
Challenge X06 - Flag Service
Isolated Flag Vault for Doctor Doom's Control Plane.
Only accepts authorized requests from Sovereign Core Service with mutual secret.
"""

import os
from flask import Flask, jsonify, request

app = Flask(__name__)

# Flag loaded from environment or default
FLAG = os.environ.get("FLAG", "YUVA{synthet1c_c0ntr0l_pl4n3_sc0p3d_0rch3str4t10n_x06}")
INTERNAL_SECRET = "DOOM_INTERNAL_SOVEREIGN_CORE_MUTUAL_SECRET_9872"


@app.route("/api/flag", methods=["GET", "POST"])
def get_flag():
    auth_header = request.headers.get("X-Core-Workload-Auth", "")
    if auth_header != INTERNAL_SECRET:
        return jsonify({
            "status": "FORBIDDEN",
            "error": "Direct flag access denied. Request must originate from authenticated Sovereign Core Service."
        }), 403

    return jsonify({
        "status": "AUTHORIZATION_GRANTED",
        "message": "Sovereign Citadel Core workload validated.",
        "flag": FLAG
    }), 200


@app.route("/healthz", methods=["GET"])
def health():
    return jsonify({"status": "OK", "service": "flag_vault"}), 200


if __name__ == "__main__":
    # Strictly bind to 127.0.0.1:8084
    app.run(host="127.0.0.1", port=8084, debug=False)
