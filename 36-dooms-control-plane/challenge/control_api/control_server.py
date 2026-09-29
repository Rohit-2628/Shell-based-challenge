#!/usr/bin/env python3
"""
Challenge X06 - Synthetic Control Plane API
Simulates a lightweight orchestration control plane (Latveria Doom Control Plane / DCP-v1).
Enforces scoped RBAC permissions on challenge-local credentials.
"""

import json
import logging
import requests
from flask import Flask, jsonify, request

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [CONTROL_API] %(message)s")
app = Flask(__name__)

WMS_URL = "http://127.0.0.1:8082"

# Challenge-local scoped token registry
TOKENS = {
    "dcp_tok_maint_9a8f4c2e1b7d5e6a3c8f": {
        "identity": "maintenance-bot-042",
        "role": "telemetry-operator",
        "allowed_scopes": [
            "workloads:list",
            "workloads:inspect",
            "workloads:transition:prepare_maintenance",
            "workloads:scale",
            "workloads:activate:mesh"
        ],
        "denied_scopes": [
            "cluster:admin",
            "secrets:read",
            "flag:direct_access",
            "system:destroy"
        ]
    }
}


def get_authenticated_token():
    auth_header = request.headers.get("Authorization", "")
    token = ""
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
    elif request.headers.get("X-Control-Token"):
        token = request.headers.get("X-Control-Token").strip()
    elif request.args.get("token"):
        token = request.args.get("token").strip()

    if not token or token not in TOKENS:
        return None, None
    return token, TOKENS[token]


def require_scope(required_scope):
    token, token_info = get_authenticated_token()
    if not token:
        return False, jsonify({
            "status": "UNAUTHORIZED",
            "error": "Missing or invalid control plane token. Provide 'Authorization: Bearer <token>'."
        }), 401

    if required_scope not in token_info.get("allowed_scopes", []):
        return False, jsonify({
            "status": "FORBIDDEN",
            "error": f"Permission denied. Required scope '{required_scope}' is not granted to identity '{token_info.get('identity')}'.",
            "identity": token_info.get("identity"),
            "role": token_info.get("role"),
            "allowed_scopes": token_info.get("allowed_scopes", [])
        }), 403

    return True, token_info, 200


@app.route("/", methods=["GET"])
@app.route("/api/v1", methods=["GET"])
def index():
    return jsonify({
        "service": "Latveria Synthetic Control Plane API",
        "version": "v1.4.0",
        "endpoints": [
            "GET  /api/v1/auth/introspect",
            "GET  /api/v1/workloads",
            "GET  /api/v1/workloads/<name>",
            "POST /api/v1/workloads/<name>/transition",
            "POST /api/v1/workloads/<name>/scale",
            "POST /api/v1/workloads/<name>/activate",
            "POST /api/v1/system/reset"
        ],
        "auth_format": "Authorization: Bearer <token>"
    }), 200


@app.route("/api/v1/auth/introspect", methods=["GET", "POST"])
@app.route("/api/v1/capabilities", methods=["GET", "POST"])
def introspect():
    token, token_info = get_authenticated_token()
    if not token:
        return jsonify({
            "status": "UNAUTHORIZED",
            "authenticated": False,
            "error": "No valid control token provided."
        }), 401

    return jsonify({
        "status": "AUTHENTICATED",
        "authenticated": True,
        "identity": token_info["identity"],
        "role": token_info["role"],
        "allowed_scopes": token_info["allowed_scopes"],
        "denied_scopes": token_info["denied_scopes"],
        "token_prefix": token[:12] + "..."
    }), 200


@app.route("/api/v1/workloads", methods=["GET"])
def list_workloads():
    ok, resp_or_info, code = require_scope("workloads:list")
    if not ok:
        return resp_or_info, code

    try:
        r = requests.get(f"{WMS_URL}/wms/workloads", timeout=2)
        return jsonify(r.json()), r.status_code
    except Exception as e:
        return jsonify({"status": "ERROR", "error": f"WMS unreachable: {e}"}), 502


@app.route("/api/v1/workloads/<name>", methods=["GET"])
def get_workload(name):
    ok, resp_or_info, code = require_scope("workloads:inspect")
    if not ok:
        return resp_or_info, code

    try:
        r = requests.get(f"{WMS_URL}/wms/workloads/{name}", timeout=2)
        return jsonify(r.json()), r.status_code
    except Exception as e:
        return jsonify({"status": "ERROR", "error": f"WMS unreachable: {e}"}), 502


@app.route("/api/v1/workloads/<name>/transition", methods=["POST"])
def transition_workload(name):
    data = request.get_json(force=True, silent=True) or {}
    action = data.get("action", "").strip()

    required_scope = f"workloads:transition:{action}"
    ok, resp_or_info, code = require_scope(required_scope)
    if not ok:
        return resp_or_info, code

    try:
        r = requests.post(f"{WMS_URL}/wms/workloads/{name}/transition", json=data, timeout=2)
        return jsonify(r.json()), r.status_code
    except Exception as e:
        return jsonify({"status": "ERROR", "error": f"WMS unreachable: {e}"}), 502


@app.route("/api/v1/workloads/<name>/scale", methods=["POST"])
def scale_workload(name):
    ok, resp_or_info, code = require_scope("workloads:scale")
    if not ok:
        return resp_or_info, code

    data = request.get_json(force=True, silent=True) or {}
    try:
        r = requests.post(f"{WMS_URL}/wms/workloads/{name}/scale", json=data, timeout=2)
        return jsonify(r.json()), r.status_code
    except Exception as e:
        return jsonify({"status": "ERROR", "error": f"WMS unreachable: {e}"}), 502


@app.route("/api/v1/workloads/<name>/activate", methods=["POST"])
def activate_workload(name):
    ok, resp_or_info, code = require_scope("workloads:activate:mesh")
    if not ok:
        return resp_or_info, code

    data = request.get_json(force=True, silent=True) or {}
    try:
        r = requests.post(f"{WMS_URL}/wms/workloads/{name}/activate", json=data, timeout=2)
        return jsonify(r.json()), r.status_code
    except Exception as e:
        return jsonify({"status": "ERROR", "error": f"WMS unreachable: {e}"}), 502


@app.route("/api/v1/system/reset", methods=["POST"])
def reset_system():
    # Anyone or operator can reset
    try:
        r = requests.post(f"{WMS_URL}/wms/reset", timeout=2)
        return jsonify(r.json()), r.status_code
    except Exception as e:
        return jsonify({"status": "ERROR", "error": f"WMS unreachable: {e}"}), 502


@app.route("/healthz", methods=["GET"])
def health():
    return jsonify({"status": "OK", "service": "control_api"}), 200


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8081, debug=False)
