#!/usr/bin/env python3
"""
Latveria Citadel Aegis-Zero Node Provisioning & Bootstrap Gateway
Public HTTP Interface listening on 0.0.0.0:80.
Provides the machine identity bootstrap gateway, diagnostic inspection, and loopback mesh dispatcher.
"""

import os
import sys
import json
import re
import urllib.parse
from pathlib import Path
import requests
from flask import Flask, request, jsonify, render_template_string

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ca.pki_manager import pki_manager
from config.config_manager import state_manager

app = Flask(__name__)
APP_ROOT = Path(__file__).resolve().parents[1]

# Blocked SSRF targets
BLOCKED_PATTERNS = [
    r"169\.254\.",
    r"metadata\.google",
    r"metadata\.azure",
    r"100\.100\.100\.200",
    r"10\.96\.",
    r":6443",
    r":10250",
    r":10255",
    r"kubernetes",
]

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Latveria Citadel // Aegis-Zero Machine Identity Portal</title>
    <style>
        :root {
            --bg-primary: #0a0e17;
            --bg-secondary: #121824;
            --bg-card: #182234;
            --accent-green: #00ff88;
            --accent-cyan: #00d2ff;
            --accent-red: #ff3366;
            --accent-amber: #ffbb00;
            --text-main: #e2e8f0;
            --text-dim: #94a3b8;
            --border: #24344d;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'JetBrains Mono', 'Fira Code', monospace; }
        body { background: var(--bg-primary); color: var(--text-main); min-height: 100vh; padding: 2rem; }
        .container { max-width: 1200px; margin: 0 auto; }
        header { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid var(--border); padding-bottom: 1rem; margin-bottom: 2rem; }
        .logo { font-size: 1.5rem; font-weight: bold; color: var(--accent-green); letter-spacing: 2px; }
        .badge { padding: 4px 12px; border-radius: 4px; font-size: 0.8rem; text-transform: uppercase; }
        .badge-live { background: rgba(0,255,136,0.2); color: var(--accent-green); border: 1px solid var(--accent-green); }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }
        .card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 8px; padding: 1.5rem; }
        .card h2 { color: var(--accent-cyan); font-size: 1.1rem; margin-bottom: 1rem; display: flex; align-items: center; gap: 8px; }
        .card pre { background: var(--bg-secondary); padding: 1rem; border-radius: 6px; overflow-x: auto; color: #a5f3fc; font-size: 0.85rem; border: 1px solid #1e293b; }
        .btn { background: var(--accent-green); color: #000; border: none; padding: 8px 16px; border-radius: 4px; font-weight: bold; cursor: pointer; transition: 0.2s; }
        .btn:hover { opacity: 0.9; box-shadow: 0 0 10px rgba(0,255,136,0.5); }
        .status-dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; background: var(--accent-green); }
        table { width: 100%; border-collapse: collapse; margin-top: 1rem; font-size: 0.85rem; }
        th, td { text-align: left; padding: 8px; border-bottom: 1px solid var(--border); }
        th { color: var(--accent-cyan); }
        .chain-diagram { display: flex; align-items: center; justify-content: space-between; margin: 1.5rem 0; padding: 1rem; background: var(--bg-secondary); border-radius: 6px; border: 1px dashed var(--border); font-size: 0.8rem; }
        .chain-node { text-align: center; padding: 8px; background: var(--bg-card); border: 1px solid var(--border); border-radius: 4px; }
        .chain-arrow { color: var(--accent-amber); font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <div class="logo">⚡ LATVERIA AEGIS-ZERO CITADEL</div>
                <p style="color: var(--text-dim); font-size: 0.9rem; margin-top: 4px;">Zero-Trust Machine Identity Bootstrap & Secret Provisioning Engine</p>
            </div>
            <span class="badge badge-live"><span class="status-dot"></span> SECURE-BOOTSTRAP ONLINE</span>
        </header>

        <div class="card" style="margin-bottom: 1.5rem;">
            <h2>🏛️ Sovereign PKI & Machine Identity Architecture</h2>
            <div class="chain-diagram">
                <div class="chain-node">
                    <strong>1. Public Gateway</strong><br>
                    <span style="color: var(--text-dim);">TCP/80 Bootstrap</span>
                </div>
                <div class="chain-arrow">➔</div>
                <div class="chain-node">
                    <strong>2. Identity Authority</strong><br>
                    <span style="color: var(--text-dim);">Port 8081 (Local CA)</span>
                </div>
                <div class="chain-arrow">➔</div>
                <div class="chain-node">
                    <strong>3. Secret Service</strong><br>
                    <span style="color: var(--text-dim);">Port 8082 (Secret Zero)</span>
                </div>
                <div class="chain-arrow">➔</div>
                <div class="chain-node">
                    <strong>4. Protected Target</strong><br>
                    <span style="color: var(--text-dim);">Port 8083 (Doomsday Core)</span>
                </div>
                <div class="chain-arrow">➔</div>
                <div class="chain-node">
                    <strong>5. Flag Vault</strong><br>
                    <span style="color: var(--accent-green);">Port 8084 (Isolated)</span>
                </div>
            </div>
            <p style="color: var(--text-dim); font-size: 0.85rem;">
                All edge nodes must establish a cryptographically verifiable machine identity using the challenge-local Identity Authority. Secret Zero is protected by multi-tier SPIFFE machine credentials.
            </p>
        </div>

        <div class="grid">
            <div class="card">
                <h2>🔍 Diagnostic & Config Inspector</h2>
                <p style="color: var(--text-dim); font-size: 0.85rem; margin-bottom: 1rem;">
                    Query edge provisioning configurations and PKI status.
                </p>
                <div style="display: flex; gap: 8px; margin-bottom: 1rem;">
                    <input type="text" id="diag-item" value="bootstrap_agent.conf" style="flex: 1; background: var(--bg-secondary); border: 1px solid var(--border); color: #fff; padding: 6px 12px; border-radius: 4px;">
                    <button class="btn" onclick="fetchDiagnostic()">Inspect</button>
                </div>
                <pre id="diag-output">// Output will appear here...</pre>
            </div>

            <div class="card">
                <h2>🚀 Loopback Mesh Dispatcher</h2>
                <p style="color: var(--text-dim); font-size: 0.85rem; margin-bottom: 1rem;">
                    Proxy authenticated requests to internal microservices (Ports 8081, 8082, 8083).
                </p>
                <pre id="mesh-example">POST /api/mesh/dispatch
{
  "target_url": "http://127.0.0.1:8081/api/v1/ca/info",
  "method": "GET"
}</pre>
                <div style="margin-top: 1rem;">
                    <button class="btn" onclick="testMesh()">Test CA Endpoint</button>
                </div>
            </div>
        </div>

        <div class="card">
            <h2>📜 Machine Identity Trust Tiers</h2>
            <table>
                <thead>
                    <tr>
                        <th>Trust Tier</th>
                        <th>SPIFFE Machine Identity</th>
                        <th>Authorized Scope</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>LOW_TRUST</td>
                        <td>spiffe://latveria.local/ns/edge/sa/telemetry-worker</td>
                        <td>Read-only metrics & diagnostics</td>
                        <td style="color: var(--accent-cyan);">ACTIVE</td>
                    </tr>
                    <tr>
                        <td>AUTHORIZED_SECRET_ZERO</td>
                        <td>spiffe://latveria.local/ns/core/sa/vault-operator</td>
                        <td>Secret Zero retrieval & Doomsday unseal</td>
                        <td style="color: var(--accent-amber);">RESTRICTED (PKI-ENFORCED)</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>

    <script>
        async function fetchDiagnostic() {
            const item = document.getElementById('diag-item').value;
            try {
                const res = await fetch(`/api/diagnostics/view?item=${encodeURIComponent(item)}`);
                const data = await res.json();
                document.getElementById('diag-output').textContent = JSON.stringify(data, null, 2);
            } catch(e) {
                document.getElementById('diag-output').textContent = "Error: " + e;
            }
        }

        async function testMesh() {
            try {
                const res = await fetch('/api/mesh/dispatch', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        target_url: 'http://127.0.0.1:8081/api/v1/ca/info',
                        method: 'GET'
                    })
                });
                const data = await res.json();
                document.getElementById('diag-output').textContent = JSON.stringify(data, null, 2);
            } catch(e) {
                document.getElementById('diag-output').textContent = "Error: " + e;
            }
        }
        fetchDiagnostic();
    </script>
</body>
</html>
"""

@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/api/system/status", methods=["GET"])
def system_status():
    return jsonify({
        "system": "LATVERIA-AEGIS-ZERO-BOOTSTRAP",
        "version": "v2.4",
        "status": "OPERATIONAL",
        "services": {
            "gateway": "0.0.0.0:80 (Public)",
            "identity_authority": "127.0.0.1:8081 (Internal)",
            "secret_service": "127.0.0.1:8082 (Internal)",
            "target_vault": "127.0.0.1:8083 (Internal)",
            "flag_vault": "127.0.0.1:8084 (Isolated)"
        }
    }), 200

@app.route("/api/diagnostics/view", methods=["GET"])
def view_diagnostics():
    item = request.args.get("item", "bootstrap_agent.conf")

    # Handle known diagnostic items
    if item in ["bootstrap_agent.conf", "agent.conf", "config"]:
        conf_path = APP_ROOT / "config" / "bootstrap_agent.conf"
        if conf_path.exists():
            return jsonify(json.loads(conf_path.read_text())), 200

    if item in ["pki_chain.pem", "ca.crt", "root_ca.crt"]:
        return jsonify({
            "item": "pki_chain.pem",
            "certificate_pem": pki_manager.get_root_ca_pem()
        }), 200

    if item in ["boot_log.txt", "boot.log"]:
        return jsonify({
            "item": "boot.log",
            "logs": [
                "[00.010] [BOOTSTRAP-AGENT] Latveria Aegis-Zero runtime initialization.",
                "[00.045] [BOOTSTRAP-AGENT] Identity CA registered at http://127.0.0.1:8081/api/v1/ca/issue",
                "[00.080] [BOOTSTRAP-AGENT] Secret Service registered at http://127.0.0.1:8082/api/v1/vault/secret-zero",
                "[00.120] [BOOTSTRAP-AGENT] Target Service registered at http://127.0.0.1:8083/api/v1/doomsday/unseal",
                "[00.150] [BOOTSTRAP-AGENT] Loaded provisioning HMAC token from bootstrap_agent.conf.",
                "[00.200] [BOOTSTRAP-AGENT] Ready for node identity enrollment."
            ]
        }), 200

    # Safe file resolution within challenge directory
    try:
        clean_path = (APP_ROOT / "config" / item).resolve()
        if str(clean_path).startswith(str(APP_ROOT)) and clean_path.exists() and clean_path.is_file():
            content = clean_path.read_text(errors="ignore")
            try:
                return jsonify(json.loads(content)), 200
            except Exception:
                return jsonify({"item": item, "content": content}), 200
    except Exception:
        pass

    return jsonify({"error": f"Diagnostic item '{item}' not found."}), 404

@app.route("/api/mesh/dispatch", methods=["POST"])
def mesh_dispatch():
    """
    Loopback Mesh Dispatcher: Forward requests to internal microservices (Ports 8081, 8082, 8083, 8084).
    Enforces security boundary checks against external networks and cloud metadata.
    """
    data = request.get_json(force=True, silent=True)
    if not data or "target_url" not in data:
        return jsonify({
            "status": "ERROR",
            "error": "Missing 'target_url' in request body."
        }), 400

    target_url = data.get("target_url", "")
    method = data.get("method", "GET").upper()
    headers = data.get("headers", {})
    body = data.get("body", None)

    # Security check: Block metadata and k8s control-plane
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, target_url, re.IGNORECASE):
            return jsonify({
                "status": "BLOCKED",
                "error": "Boundary Violation: Probes to cloud metadata and cluster infrastructure are blocked."
            }), 403

    parsed = urllib.parse.urlparse(target_url)
    allowed_hosts = ["127.0.0.1", "localhost"]
    if parsed.hostname not in allowed_hosts:
        return jsonify({
            "status": "FORBIDDEN",
            "error": f"Mesh dispatcher only routes to internal loopback hosts (127.0.0.1)."
        }), 403

    allowed_ports = [8081, 8082, 8083, 8084]
    if parsed.port not in allowed_ports:
        return jsonify({
            "status": "FORBIDDEN",
            "error": f"Port {parsed.port} is not an authorized internal mesh port."
        }), 403

    try:
        resp = requests.request(
            method=method,
            url=target_url,
            headers=headers,
            json=body if isinstance(body, dict) else None,
            data=body if isinstance(body, str) else None,
            timeout=5
        )
        try:
            resp_json = resp.json()
            return jsonify({
                "status_code": resp.status_code,
                "data": resp_json
            }), resp.status_code
        except Exception:
            return jsonify({
                "status_code": resp.status_code,
                "text": resp.text
            }), resp.status_code
    except Exception as e:
        return jsonify({
            "status": "ERROR",
            "error": f"Mesh dispatch failure: {str(e)}"
        }), 502

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 80))
    app.run(host="0.0.0.0", port=port, debug=False)
