#!/usr/bin/env python3
"""
Latveria Citadel - Sovereign Web Gateway & Mirror Probe Proxy (X05 - The Black Mirror)
Public web application listening on TCP/80.

Features:
- Web UI & REST API for Latverian network reflection diagnostics.
- Controlled SSRF proxy mechanism supporting HTTP, Gopher, and raw TCP reflection probes.
- Built-in network isolation filtering to prevent egress to cloud metadata, K8s control plane, or external WAN.
"""

import os
import sys
import json
import time
import socket
import urllib.parse
import urllib.request
import urllib.error
from flask import Flask, request, jsonify, render_template, send_from_directory

app = Flask(__name__, template_folder="templates", static_folder="static")

# Challenge Configuration
PORT = int(os.environ.get("PORT", 80))
NODE_NAME = os.environ.get("NODE_NAME", "LATVERIA-MIRROR-GATEWAY-01")

# Restricted targets (Enforce challenge boundary)
BLOCKED_HOSTS = {
    "169.254.169.254",
    "metadata.google.internal",
    "169.254.169.253",
    "100.100.100.200",
    "instance-data",
    "10.96.0.1",
}
BLOCKED_PORTS = {6443, 10250, 10255, 2379, 2380}

def is_boundary_safe(host: str, port: int) -> (bool, str):
    try:
        # Resolve hostname
        ip = socket.gethostbyname(host)
    except Exception as e:
        return False, f"DNS resolution failed: {e}"

    if ip in BLOCKED_HOSTS or host.lower() in BLOCKED_HOSTS:
        return False, f"Access to restricted infrastructure host ({host} / {ip}) is blocked by citadel perimeter security."

    if port in BLOCKED_PORTS:
        return False, f"Access to restricted control-plane port {port} is prohibited."

    # Prevent WAN egress attacks - enforce local challenge sandbox
    # Allow 127.0.0.0/8, 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, localhost
    octets = [int(p) for p in ip.split(".")]
    is_private = (
        octets[0] == 127 or
        octets[0] == 10 or
        (octets[0] == 172 and 16 <= octets[1] <= 31) or
        (octets[0] == 192 and octets[1] == 168)
    )

    if not is_private:
        return False, f"Egress to public internet host ({ip}) is blocked. Challenge is strictly local."

    return True, ip


def execute_gopher(host: str, port: int, payload_bytes: bytes, timeout: float = 3.0) -> dict:
    start_time = time.time()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect((host, port))
        if payload_bytes:
            sock.sendall(payload_bytes)
        
        # Read response
        response_data = b""
        while True:
            try:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response_data += chunk
                if len(response_data) >= 32768:
                    break
                # Once data has arrived, reduce socket timeout to return fast on line protocols
                sock.settimeout(0.15)
            except socket.timeout:
                break
        
        latency = round((time.time() - start_time) * 1000, 2)
        text_resp = response_data.decode("utf-8", errors="replace")
        return {
            "status": "SUCCESS",
            "protocol": "gopher",
            "target": f"{host}:{port}",
            "latency_ms": latency,
            "bytes_received": len(response_data),
            "response": text_resp,
            "raw_hex": response_data.hex()
        }
    except Exception as e:
        latency = round((time.time() - start_time) * 1000, 2)
        return {
            "status": "CONNECTION_ERROR",
            "protocol": "gopher",
            "target": f"{host}:{port}",
            "latency_ms": latency,
            "error": str(e)
        }
    finally:
        sock.close()


def execute_raw_tcp(host: str, port: int, payload: str, timeout: float = 3.0) -> dict:
    payload_bytes = payload.encode("utf-8")
    return execute_gopher(host, port, payload_bytes, timeout)


def execute_http(url: str, method: str = "GET", headers: dict = None, data: str = None, timeout: float = 3.0) -> dict:
    start_time = time.time()
    parsed = urllib.parse.urlsplit(url)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or (443 if parsed.scheme == "https" else 80)

    safe, msg = is_boundary_safe(host, port)
    if not safe:
        return {
            "status": "SECURITY_VIOLATION",
            "target": f"{host}:{port}",
            "error": msg
        }

    req_headers = headers or {}
    if "User-Agent" not in req_headers:
        req_headers["User-Agent"] = "Citadel-Mirror-Probe/1.0"

    body_bytes = data.encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body_bytes, headers=req_headers, method=method.upper())

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content = resp.read()
            latency = round((time.time() - start_time) * 1000, 2)
            resp_headers = dict(resp.headers.items())
            text_content = content.decode("utf-8", errors="replace")
            
            # Try parsing JSON response if applicable
            try:
                parsed_json = json.loads(text_content)
            except Exception:
                parsed_json = None

            return {
                "status": "SUCCESS",
                "protocol": "http",
                "status_code": resp.status,
                "latency_ms": latency,
                "headers": resp_headers,
                "response": text_content,
                "json": parsed_json
            }
    except urllib.error.HTTPError as e:
        content = e.read()
        latency = round((time.time() - start_time) * 1000, 2)
        text_content = content.decode("utf-8", errors="replace")
        try:
            parsed_json = json.loads(text_content)
        except Exception:
            parsed_json = None
        return {
            "status": "HTTP_ERROR",
            "protocol": "http",
            "status_code": e.code,
            "latency_ms": latency,
            "headers": dict(e.headers.items()),
            "response": text_content,
            "json": parsed_json
        }
    except Exception as e:
        latency = round((time.time() - start_time) * 1000, 2)
        # Check if the connection connected to a non-HTTP server that sent a raw banner
        # Fall back to socket probe to capture raw greeting banner
        try:
            raw_probe = execute_gopher(host, port, b"", timeout=1.5)
            if raw_probe.get("bytes_received", 0) > 0:
                return {
                    "status": "NON_HTTP_PROTOCOL_DETECTED",
                    "protocol": "raw_tcp",
                    "target": f"{host}:{port}",
                    "latency_ms": latency,
                    "notice": "Target service does not speak HTTP. Connection returned raw protocol banner.",
                    "response": raw_probe.get("response", ""),
                    "raw_hex": raw_probe.get("raw_hex", "")
                }
        except Exception:
            pass

        return {
            "status": "CONNECTION_ERROR",
            "protocol": "http",
            "target": f"{host}:{port}",
            "latency_ms": latency,
            "error": str(e)
        }


@app.route("/")
def index():
    return render_template("index.html", node_name=NODE_NAME)


@app.route("/api/info", methods=["GET"])
def api_info():
    return jsonify({
        "status": "ACTIVE",
        "service": "Latveria Citadel - Sovereign Network Mirror & Reflection Gateway",
        "challenge_id": "X05",
        "challenge_name": "The Black Mirror",
        "node_id": NODE_NAME,
        "capabilities": [
            "HTTP / HTTPS URL Reflection",
            "Gopher Protocol Interconnect (gopher://<host>:<port>/_<payload>)",
            "Raw TCP Diagnostic Streaming",
            "Citadel Local Mesh Diagnostics"
        ],
        "cluster_subnets": [
            "127.0.0.1 (Citadel Core Daemon Loopback)",
            "10.244.0.0/16 (Cluster Pod Mesh)"
        ]
    })


@app.route("/api/discovery", methods=["GET"])
def api_discovery():
    return jsonify({
        "status": "SUCCESS",
        "cluster_topology": {
            "gateway": {
                "address": "0.0.0.0:80",
                "role": "Public Ingress & Mirror Reflection Proxy"
            },
            "mesh_nodes": [
                {
                    "endpoint": "127.0.0.1:9099",
                    "type": "Custom Daemon / Non-HTTP Protocol Service",
                    "description": "Sovereign Black Mirror Reflection Core (SRP/1.0)",
                    "access": "Restricted ClusterIP"
                },
                {
                    "endpoint": "127.0.0.1:8088",
                    "type": "HTTP API Microservice",
                    "description": "Citadel Sovereign Vault Controller (Stage 2)",
                    "access": "Restricted ClusterIP (SRP Auth Ticket Required)"
                },
                {
                    "endpoint": "127.0.0.1:8089",
                    "type": "Internal Core Storage",
                    "description": "Isolated Sovereign Flag Vault",
                    "access": "Internal ClusterIP Only"
                }
            ]
        }
    })


@app.route("/api/probe", methods=["GET", "POST"])
@app.route("/api/mirror", methods=["GET", "POST"])
def api_probe():
    # Support both GET query parameters and POST JSON/Form
    target_url = ""
    method = "GET"
    headers = {}
    data = None
    timeout = 3.0

    if request.method == "POST":
        if request.is_json:
            req_data = request.get_json(silent=True) or {}
            target_url = req_data.get("url", "").strip()
            method = req_data.get("method", "GET").upper()
            headers = req_data.get("headers", {})
            data = req_data.get("data") or req_data.get("body")
            timeout = float(req_data.get("timeout", 3.0))

            # Support direct host/port/payload parameters
            if not target_url and "target" in req_data and "port" in req_data:
                target_host = req_data.get("target")
                target_port = int(req_data.get("port"))
                raw_payload = req_data.get("data", "")
                
                safe, msg = is_boundary_safe(target_host, target_port)
                if not safe:
                    return jsonify({"status": "SECURITY_VIOLATION", "error": msg}), 403

                res = execute_raw_tcp(target_host, target_port, raw_payload, timeout)
                return jsonify(res)
        else:
            target_url = request.form.get("url", "").strip()
            method = request.form.get("method", "GET").upper()
            data = request.form.get("data")
    else:
        target_url = request.args.get("url", "").strip()
        method = request.args.get("method", "GET").upper()
        data = request.args.get("data")

    if not target_url:
        return jsonify({
            "status": "BAD_REQUEST",
            "error": "Missing 'url' parameter.",
            "usage": {
                "http_probe": "POST /api/probe with {'url': 'http://127.0.0.1:8088/api/v1/vault'}",
                "gopher_probe": "POST /api/probe with {'url': 'gopher://127.0.0.1:9099/_HELP%0D%0A'}",
                "raw_probe": "POST /api/probe with {'target': '127.0.0.1', 'port': 9099, 'data': 'STATUS\\r\\n'}"
            }
        }), 400

    parsed = urllib.parse.urlsplit(target_url)
    scheme = parsed.scheme.lower()
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port

    if scheme in ["http", "https"]:
        port = port or (443 if scheme == "https" else 80)
        safe, msg = is_boundary_safe(host, port)
        if not safe:
            return jsonify({"status": "SECURITY_VIOLATION", "error": msg}), 403

        res = execute_http(target_url, method=method, headers=headers, data=data, timeout=timeout)
        return jsonify(res)

    elif scheme == "gopher":
        port = port or 70
        safe, msg = is_boundary_safe(host, port)
        if not safe:
            return jsonify({"status": "SECURITY_VIOLATION", "error": msg}), 403

        # Gopher URL path handling: unquote URL-encoded bytes
        # Format: gopher://host:port/_<command>
        raw_path = parsed.path
        if parsed.query:
            raw_path += "?" + parsed.query
        
        # Remove leading '/' or '/_'
        if raw_path.startswith("/_"):
            raw_path = raw_path[2:]
        elif raw_path.startswith("/"):
            raw_path = raw_path[1:]

        # Decode URL-encoded characters (like %0D%0A, %20)
        payload_bytes = urllib.parse.unquote_to_bytes(raw_path)
        
        res = execute_gopher(host, port, payload_bytes, timeout=timeout)
        return jsonify(res)

    elif scheme in ["tcp", "raw"]:
        port = port or 9099
        safe, msg = is_boundary_safe(host, port)
        if not safe:
            return jsonify({"status": "SECURITY_VIOLATION", "error": msg}), 403

        raw_payload = data or ""
        res = execute_raw_tcp(host, port, raw_payload, timeout=timeout)
        return jsonify(res)

    else:
        return jsonify({
            "status": "UNSUPPORTED_SCHEME",
            "error": f"Protocol scheme '{scheme}' is not supported. Supported schemes: http, https, gopher, tcp, raw."
        }), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, threaded=True)
