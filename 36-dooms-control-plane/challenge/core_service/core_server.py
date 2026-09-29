#!/usr/bin/env python3
"""
Challenge X06 - Sovereign Core Service
Internal core service of Doctor Doom's Control Plane.
Only becomes reachable and functional once the synthetic workload manager has transitioned
the 'sovereign-core-gateway' workload to ACTIVE state with at least 1 replica and route bound.
"""

import logging
import requests
from flask import Flask, jsonify, request

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [CORE] %(message)s")
app = Flask(__name__)

WMS_URL = "http://127.0.0.1:8082"
FLAG_SERVICE_URL = "http://127.0.0.1:8084"
INTERNAL_SECRET = "DOOM_INTERNAL_SOVEREIGN_CORE_MUTUAL_SECRET_9872"


def check_workload_active():
    try:
        r = requests.get(f"{WMS_URL}/wms/core-status", timeout=2)
        if r.status_code == 200:
            data = r.json()
            return data.get("active", False), data.get("state", "UNKNOWN")
    except Exception as e:
        logging.error(f"Error communicating with WMS: {e}")
    return False, "OFFLINE"


@app.route("/core/status", methods=["GET"])
def core_status():
    is_active, state = check_workload_active()
    if not is_active:
        return jsonify({
            "status": "SERVICE_UNAVAILABLE",
            "code": "CORE_GATEWAY_DORMANT",
            "message": f"Sovereign Core Service is currently in state [{state}]. Workload transition and mesh activation required in Control Plane API.",
            "instructions": "Use Control API on 127.0.0.1:8081 to prepare maintenance, scale replicas, and activate mesh route."
        }), 503

    return jsonify({
        "status": "ONLINE",
        "code": "CORE_GATEWAY_ACTIVE",
        "message": "Sovereign Core Gateway is ACTIVE. Mesh route synchronized.",
        "endpoints": [
            "/core/status",
            "/core/vault"
        ]
    }), 200


@app.route("/core/vault", methods=["GET", "POST"])
def core_vault():
    is_active, state = check_workload_active()
    if not is_active:
        return jsonify({
            "status": "FORBIDDEN",
            "code": "WORKLOAD_INACTIVE",
            "error": f"Access to Sovereign Core Vault denied. Workload state is [{state}]. Must be ACTIVE."
        }), 503

    # Workload is active; request the flag from isolated Flag Service
    try:
        resp = requests.get(
            f"{FLAG_SERVICE_URL}/api/flag",
            headers={"X-Core-Workload-Auth": INTERNAL_SECRET},
            timeout=3
        )
        if resp.status_code == 200:
            flag_data = resp.json()
            return jsonify({
                "status": "SUCCESS",
                "message": "Sovereign Core Vault unlocked successfully.",
                "core_identity": "LATVERIA-PRIME-CORE-WORKLOAD-001",
                "workload_status": "ACTIVE",
                "flag": flag_data.get("flag", "")
            }), 200
        else:
            return jsonify({
                "status": "ERROR",
                "error": "Failed to authenticate with isolated Flag Service."
            }), 500
    except Exception as e:
        return jsonify({
            "status": "ERROR",
            "error": f"Internal communication error: {str(e)}"
        }), 500


@app.route("/healthz", methods=["GET"])
def health():
    return jsonify({"status": "OK", "service": "sovereign_core_service"}), 200


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8083, debug=False)
