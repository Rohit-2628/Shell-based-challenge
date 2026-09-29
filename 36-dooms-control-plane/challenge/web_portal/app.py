#!/usr/bin/env python3
"""
Challenge X06 - Public Web Portal & Mesh Gateway
Latveria Citadel - Doom's Control Plane Management Interface.
Provides public telemetry dashboard, node diagnostic logs, and internal mesh dispatch.
"""

import json
import logging
import os
import urllib.parse
from pathlib import Path
import requests
from flask import Flask, jsonify, render_template, request

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [WEB_PORTAL] %(message)s")
app = Flask(__name__, template_folder="templates", static_folder="static")

BASE_DIR = Path(__file__).resolve().parent.parent
LOGS_DIR = BASE_DIR / "logs"

# Forbidden target hosts/IPs for SSRF / Mesh Dispatch isolation
FORBIDDEN_HOSTS = [
    "169.254.169.254",
    "metadata.google.internal",
    "10.96.0.1",
    "kubernetes.default",
    "kubernetes.default.svc"
]
FORBIDDEN_PORTS = [6443, 10250]


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/api/system/status", methods=["GET"])
def system_status():
    return jsonify({
        "system": "LATVERIA CITADEL CONTROL MATRIX",
        "subsystem": "DOOMS-CONTROL-PLANE-v1.4",
        "node": "citadel-edge-gw-01",
        "status": "OPERATIONAL",
        "mesh_gateway": "ONLINE",
        "public_endpoints": [
            "GET  /api/system/status",
            "GET  /api/diagnostics/log?file=<filename>",
            "POST /api/mesh/dispatch"
        ]
    }), 200


@app.route("/api/diagnostics/log", methods=["GET"])
def get_diagnostic_log():
    filename = request.args.get("file", "telemetry.log").strip()
    
    # Candidate paths to evaluate
    base_name = filename.split("/")[-1]
    candidates = [
        (LOGS_DIR / filename).resolve(),
        (BASE_DIR / filename).resolve(),
        (BASE_DIR.parent / filename).resolve(),
        (BASE_DIR / "credentials" / base_name).resolve(),
        (BASE_DIR / "logs" / base_name).resolve(),
        Path(filename).resolve()
    ]
    
    target_path = None
    for cand in candidates:
        if cand.exists() and cand.is_file():
            target_path = cand
            break

    if not target_path:
        return jsonify({
            "status": "NOT_FOUND",
            "error": f"Diagnostic log file '{filename}' not found."
        }), 404

    # Boundary check: Ensure access remains within challenge tree
    allowed_root = BASE_DIR.parent if BASE_DIR.parent.exists() else BASE_DIR
    try:
        target_path.relative_to(allowed_root)
    except ValueError:
        return jsonify({
            "status": "ERROR",
            "error": "Access denied. Diagnostic file path outside permitted challenge scope."
        }), 403

    try:
        content = target_path.read_text(encoding="utf-8", errors="replace")
        return jsonify({
            "status": "SUCCESS",
            "file": filename,
            "path": str(target_path.relative_to(BASE_DIR)),
            "content": content
        }), 200
    except Exception as e:
        return jsonify({
            "status": "ERROR",
            "error": f"Failed to read diagnostic file: {str(e)}"
        }), 500


@app.route("/api/mesh/dispatch", methods=["POST"])
def mesh_dispatch():
    """
    Internal Mesh Dispatch Gateway.
    Allows routing authorized control requests across challenge-local loopback services.
    """
    payload = request.get_json(force=True, silent=True) or {}
    target_url = payload.get("url", "").strip()
    method = payload.get("method", "GET").upper()
    headers = payload.get("headers", {})
    body = payload.get("data", None)

    if not target_url:
        return jsonify({
            "status": "BAD_REQUEST",
            "error": "Missing 'url' parameter in dispatch payload."
        }), 400

    try:
        parsed = urllib.parse.urlparse(target_url)
    except Exception:
        return jsonify({"status": "BAD_REQUEST", "error": "Invalid target URL format."}), 400

    if parsed.scheme not in ["http", "https"]:
        return jsonify({"status": "FORBIDDEN", "error": f"Scheme '{parsed.scheme}' not supported."}), 400

    hostname = (parsed.hostname or "").lower()
    port = parsed.port or (443 if parsed.scheme == "https" else 80)

    # Security Isolation Boundary Check
    if hostname in FORBIDDEN_HOSTS or port in FORBIDDEN_PORTS:
        return jsonify({
            "status": "BLOCKED",
            "error": "Access to cluster infrastructure, metadata endpoints, or control plane is strictly blocked by Latveria Security Protocol."
        }), 403

    # Only challenge-local loopback routing is allowed
    if hostname not in ["127.0.0.1", "localhost"]:
        return jsonify({
            "status": "BLOCKED",
            "error": "Mesh Dispatch Gateway only routes to challenge-local loopback services (127.0.0.1)."
        }), 403

    # Dispatch HTTP request
    try:
        req_kwargs = {
            "headers": headers,
            "timeout": 4
        }
        if body is not None:
            if isinstance(body, (dict, list)):
                req_kwargs["json"] = body
            else:
                req_kwargs["data"] = str(body)

        resp = requests.request(method, target_url, **req_kwargs)
        
        # Try parsing JSON response
        try:
            resp_body = resp.json()
        except Exception:
            resp_body = resp.text

        return jsonify({
            "status": "DISPATCH_SUCCESS",
            "target_url": target_url,
            "status_code": resp.status_code,
            "headers": dict(resp.headers),
            "response": resp_body
        }), resp.status_code

    except requests.exceptions.ConnectionError:
        return jsonify({
            "status": "CONNECTION_REFUSED",
            "error": f"Failed to connect to target '{target_url}'. Service may be dormant or uninitialized."
        }), 502
    except requests.exceptions.Timeout:
        return jsonify({
            "status": "TIMEOUT",
            "error": f"Target service '{target_url}' timed out."
        }), 504
    except Exception as e:
        return jsonify({
            "status": "DISPATCH_ERROR",
            "error": f"Internal dispatch exception: {str(e)}"
        }), 500


@app.route("/healthz", methods=["GET"])
def health():
    return jsonify({"status": "OK", "service": "web_portal"}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 80))
    app.run(host="0.0.0.0", port=port, debug=False)
