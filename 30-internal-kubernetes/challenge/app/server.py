#!/usr/bin/env python3
"""
Latveria Sovereign Defense Grid — Cluster Fleet Sentinel Web Gateway (v2.4.0)
Public Web Dashboard & Diagnostic Probe System (TCP/80)
"""

import os
import sys
import json
import logging
import subprocess
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [SENTINEL-APP] %(message)s'
)
logger = logging.getLogger("FleetSentinelApp")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

class SentinelWebHandler(BaseHTTPRequestHandler):
    server_version = "Latveria-Sentinel-Gateway/2.4.0"

    def log_message(self, format, *args):
        logger.info("%s - %s" % (self.address_string(), format % args))

    def _send_response_bytes(self, status_code, content_type, body_bytes):
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body_bytes)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.end_headers()
        self.wfile.write(body_bytes)

    def _send_json(self, status_code, payload):
        body = json.dumps(payload, indent=2).encode('utf-8')
        self._send_response_bytes(status_code, "application/json", body)

    def _send_file(self, file_path, content_type):
        if not os.path.exists(file_path):
            self._send_json(404, {"error": "Resource not found"})
            return
        with open(file_path, "rb") as f:
            data = f.read()
        self._send_response_bytes(200, content_type, data)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            index_file = os.path.join(TEMPLATES_DIR, "index.html")
            self._send_file(index_file, "text/html; charset=utf-8")
            return

        if path.startswith("/static/"):
            filename = os.path.basename(path)
            static_file = os.path.join(STATIC_DIR, filename)
            content_type = "text/css" if filename.endswith(".css") else "application/javascript"
            self._send_file(static_file, content_type)
            return

        if path == "/api/v1/health" or path == "/api/v1/status":
            self._send_json(200, {
                "status": "OPERATIONAL",
                "system": "Latveria Sovereign Defense Grid — Cluster Fleet Sentinel",
                "version": "2.4.0-k8s-integrated",
                "zone": "ORBITAL-LATV-ALPHA",
                "nodes": [
                    {"name": "latv-node-01.internal", "status": "Ready", "role": "control-plane", "k8s_version": "v1.28.2"},
                    {"name": "latv-node-02.internal", "status": "Ready", "role": "telemetry-worker", "k8s_version": "v1.28.2"},
                    {"name": "latv-node-03.internal", "status": "Ready", "role": "orbital-defense-worker", "k8s_version": "v1.28.2"}
                ],
                "active_namespace": "telemetry-system",
                "service_account": "system:serviceaccount:telemetry-system:telemetry-sentinel"
            })
            return

        if path == "/api/v1/workload/summary":
            self._send_json(200, {
                "cluster": "latveria-sovereign-fleet-01",
                "total_namespaces": 4,
                "namespaces": ["default", "kube-system", "telemetry-system", "orbital-defense"],
                "telemetry_pods": 1,
                "orbital_pods": 1,
                "gateway_uptime": "99.999%",
                "diagnostic_probe_status": "ENABLED"
            })
            return

        self._send_json(404, {"error": "Endpoint not found"})

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else b'{}'
        try:
            req_data = json.loads(body.decode('utf-8')) if body else {}
        except Exception:
            req_data = {}

        # 1. Diagnostic Probe API (Vulnerability: Unsanitized command execution / probe target)
        if path == "/api/v1/diagnostics/probe":
            target = req_data.get("target", "").strip()
            probe_type = req_data.get("probe_type", "ping").lower()

            if not target:
                self._send_json(400, {"status": "error", "message": "Missing 'target' parameter in request payload."})
                return

            if probe_type == "ping":
                cmd = f"ping -c 1 -W 2 {target}"
            elif probe_type == "dns":
                cmd = f"getent hosts {target}"
            elif probe_type == "route":
                cmd = f"ip route get {target}"
            elif probe_type == "exec":
                cmd = f"sh -c {target}"
            else:
                cmd = f"ping -c 1 -W 2 {target}"

            logger.info(f"Executing diagnostic probe command: {cmd}")

            try:
                # Intended vulnerability: Shell execution of unescaped command string
                proc = subprocess.Popen(
                    cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                stdout, stderr = proc.communicate(timeout=10)
                exit_code = proc.returncode

                output = stdout if stdout else stderr
                self._send_json(200, {
                    "status": "success" if exit_code == 0 else "error",
                    "probe_type": probe_type,
                    "target": target,
                    "executed_command": cmd,
                    "exit_code": exit_code,
                    "output": output
                })
            except subprocess.TimeoutExpired:
                proc.kill()
                self._send_json(504, {"status": "timeout", "message": "Probe execution timed out."})
            except Exception as e:
                self._send_json(500, {"status": "error", "message": str(e)})
            return

        # 2. Interactive Terminal Console API
        if path == "/api/v1/diagnostics/terminal" or path == "/api/v1/cluster/exec":
            command = req_data.get("command", "").strip()
            if not command:
                self._send_json(400, {"status": "error", "message": "Missing 'command' parameter."})
                return

            logger.info(f"Executing terminal command: {command}")
            try:
                proc = subprocess.Popen(
                    command,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                stdout, stderr = proc.communicate(timeout=10)
                exit_code = proc.returncode

                self._send_json(200, {
                    "status": "success" if exit_code == 0 else "error",
                    "command": command,
                    "exit_code": exit_code,
                    "stdout": stdout,
                    "stderr": stderr
                })
            except subprocess.TimeoutExpired:
                proc.kill()
                self._send_json(504, {"status": "timeout", "message": "Command execution timed out."})
            except Exception as e:
                self._send_json(500, {"status": "error", "message": str(e)})
            return

        self._send_json(404, {"error": "Endpoint not found"})


def main():
    host = os.environ.get("APP_HOST", "127.0.0.1")
    port = int(os.environ.get("APP_PORT", "8000"))

    server = ThreadedHTTPServer((host, port), SentinelWebHandler)
    logger.info(f"Fleet Sentinel Web Application running on http://{host}:{port}/")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down Fleet Sentinel Web Application...")
        server.server_close()


if __name__ == "__main__":
    main()
