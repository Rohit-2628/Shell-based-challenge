#!/usr/bin/env python3
"""
Public Image Fetcher & Cloud Mirror Gateway Application for D29 — Cloud Mirror
Provides the public web interface on TCP/80 (via Nginx proxy) and the URL fetching SSRF primitive.
"""

import argparse
import base64
import collections
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

# Rate limiting storage (Sliding window / Token bucket)
RATE_LIMIT_BUCKETS = collections.defaultdict(list)
RATE_LIMIT_WINDOW = 1.0  # 1 second window
RATE_LIMIT_MAX_REQUESTS = 10  # max 10 requests per second per IP

# Security Boundary: Blocked hosts / subnets
BLOCKED_PATTERNS = [
    r"^kubernetes(\..*)?$",
    r"^10\.96\..*$",
    r"^10\.244\..*$",
    r"^172\.(1[6-9]|2[0-9]|3[0-1])\..*$",
]

BLOCKED_PORTS = {6443, 10250, 10255, 2379, 2380}

APP_DIR = Path(__file__).resolve().parent

class CloudMirrorHTTPHandler(BaseHTTPRequestHandler):
    server_version = "LatveriaCloudMirror/2.4"

    def check_rate_limit(self) -> bool:
        client_ip = self.client_address[0]
        now = time.time()
        
        # Prune old timestamps
        RATE_LIMIT_BUCKETS[client_ip] = [t for t in RATE_LIMIT_BUCKETS[client_ip] if now - t < RATE_LIMIT_WINDOW]
        
        if len(RATE_LIMIT_BUCKETS[client_ip]) >= RATE_LIMIT_MAX_REQUESTS:
            return False
            
        RATE_LIMIT_BUCKETS[client_ip].append(now)
        return True

    def send_json(self, data: dict, status: int = 200, extra_headers: dict = None):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Server", self.server_version)
        if extra_headers:
            for k, v in extra_headers.items():
                self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def send_html(self, html: str, status: int = 200):
        body = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Server", self.server_version)
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, file_path: Path, content_type: str = "text/plain"):
        if not file_path.exists() or not file_path.is_file():
            self.send_json({"error": "NotFound"}, 404)
            return
        content = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Server", self.server_version)
        self.end_headers()
        self.wfile.write(content)

    def resolve_and_fetch_url(self, target_url: str, custom_headers: dict = None) -> tuple[int, dict]:
        """
        SSRF Fetcher Engine
        Resolves cloud-like hostnames to challenge-local daemons, applies security boundaries,
        and executes the HTTP request.
        """
        if not target_url:
            return 200, {"status": "error", "message": "Missing 'url' parameter", "http_status": 400}

        # Normalize URL scheme
        if not target_url.startswith("http://") and not target_url.startswith("https://"):
            target_url = "http://" + target_url

        try:
            parsed = urllib.parse.urlsplit(target_url)
        except Exception as e:
            return 200, {"status": "error", "message": f"Malformed URL: {str(e)}", "http_status": 400}

        hostname = (parsed.hostname or "").lower()
        port = parsed.port

        # 1. Check Security Boundary (Prevent escape to K8s API or other cluster infrastructure)
        for pattern in BLOCKED_PATTERNS:
            if re.match(pattern, hostname):
                return 200, {
                    "status": "blocked",
                    "http_status": 403,
                    "error": "SecurityBoundaryEnforced",
                    "message": f"Destination host '{hostname}' is blocked by platform isolation policies."
                }

        if port and port in BLOCKED_PORTS:
            return 200, {
                "status": "blocked",
                "http_status": 403,
                "error": "SecurityBoundaryEnforced",
                "message": f"Target port {port} is restricted by internal firewall."
            }

        # 2. Challenge Internal Routing / Mock Cloud Interception
        actual_url = target_url

        # Mock Metadata Destinations
        if hostname in ["169.254.169.254", "metadata.internal", "instance-data", "metadata.google.internal"]:
            actual_url = f"http://127.0.0.1:8181{parsed.path}"
            if parsed.query:
                actual_url += f"?{parsed.query}"

        # Mock Object Storage Destinations
        elif hostname in ["storage.internal", "object-store.internal", "s3.internal"]:
            actual_url = f"http://127.0.0.1:9000{parsed.path}"
            if parsed.query:
                actual_url += f"?{parsed.query}"

        # Local direct ports
        elif hostname in ["127.0.0.1", "localhost"]:
            if port in [8181, 9000, 8000, 80]:
                actual_url = target_url
            else:
                return 200, {
                    "status": "blocked",
                    "http_status": 403,
                    "error": "PortRestricted",
                    "message": f"Port {port} on loopback is not a permitted mirror target."
                }

        # 3. Perform the HTTP Fetch
        req_headers = {
            "User-Agent": "Latveria-Cloud-Mirror-Fetcher/2.4 (compatible; AssetProcessor/1.0)",
            "Accept": "*/*"
        }
        if custom_headers and isinstance(custom_headers, dict):
            for k, v in custom_headers.items():
                if isinstance(k, str) and isinstance(v, str):
                    req_headers[k] = v

        try:
            req = urllib.request.Request(actual_url, headers=req_headers, method="GET")
            with urllib.request.urlopen(req, timeout=5) as response:
                status_code = response.status
                resp_headers = dict(response.headers)
                content_type = resp_headers.get("Content-Type", "application/octet-stream")
                body_bytes = response.read(1024 * 512)  # Cap preview at 512KB

                is_json = False
                json_data = None
                body_text = None
                image_data_uri = None

                # Detect text / json
                if "application/json" in content_type:
                    try:
                        json_data = json.loads(body_bytes.decode("utf-8", errors="ignore"))
                        is_json = True
                        body_text = json.dumps(json_data, indent=2)
                    except Exception:
                        body_text = body_bytes.decode("utf-8", errors="ignore")
                elif "image/" in content_type:
                    b64 = base64.b64encode(body_bytes).decode("ascii")
                    image_data_uri = f"data:{content_type};base64,{b64}"
                    body_text = f"[Binary Image Data: {len(body_bytes)} bytes]"
                else:
                    body_text = body_bytes.decode("utf-8", errors="ignore")

                return 200, {
                    "status": "success",
                    "requested_url": target_url,
                    "resolved_url": actual_url if actual_url != target_url else None,
                    "http_status": status_code,
                    "content_type": content_type,
                    "headers": resp_headers,
                    "body": body_text,
                    "is_json": is_json,
                    "json_data": json_data,
                    "image_preview": image_data_uri,
                    "size_bytes": len(body_bytes)
                }

        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            try:
                err_json = json.loads(err_body)
            except Exception:
                err_json = None

            return 200, {
                "status": "upstream_http_error",
                "requested_url": target_url,
                "http_status": e.code,
                "content_type": e.headers.get("Content-Type", "text/plain"),
                "headers": dict(e.headers),
                "body": err_body,
                "json_data": err_json,
                "error": f"HTTP {e.code}: {e.reason}"
            }

        except urllib.error.URLError as e:
            return 200, {
                "status": "fetch_failed",
                "requested_url": target_url,
                "error": f"Connection error: {str(e.reason)}"
            }

        except Exception as e:
            return 200, {
                "status": "internal_error",
                "requested_url": target_url,
                "error": f"Fetch error: {str(e)}"
            }

    def do_GET(self):
        parsed = urllib.parse.urlsplit(self.path)
        path = parsed.path

        # Static assets
        if path.startswith("/static/"):
            rel_path = path[len("/static/"):]
            file_path = APP_DIR / "static" / rel_path
            ext = file_path.suffix.lower()
            ct = "text/plain"
            if ext == ".css":
                ct = "text/css"
            elif ext == ".js":
                ct = "application/javascript"
            elif ext == ".png":
                ct = "image/png"
            elif ext == ".jpg" or ext == ".jpeg":
                ct = "image/jpeg"
            self.send_file(file_path, ct)
            return

        # Health check
        if path == "/api/v1/health":
            self.send_json({"status": "OK", "service": "Latveria Cloud Mirror Gateway", "version": "2.4.0"})
            return

        # GET fetch endpoint
        if path == "/api/v1/fetch":
            if not self.check_rate_limit():
                self.send_json({"error": "RateLimitExceeded", "message": "Rate limit exceeded (~10 req/s). Please throttle requests."}, 429, {"Retry-After": "1"})
                return

            qs = urllib.parse.parse_qs(parsed.query)
            target_url = qs.get("url", [""])[0]
            status_code, result = self.resolve_and_fetch_url(target_url)
            self.send_json(result, status_code)
            return

        # Index page
        if path in ["", "/", "/index.html"]:
            index_path = APP_DIR / "templates" / "index.html"
            if index_path.exists():
                self.send_html(index_path.read_text(encoding="utf-8"))
            else:
                self.send_html("<h1>Latveria Cloud Mirror</h1><p>Service Active.</p>")
            return

        self.send_json({"error": "NotFound", "path": path}, 404)

    def do_POST(self):
        parsed = urllib.parse.urlsplit(self.path)
        path = parsed.path

        if path == "/api/v1/fetch":
            if not self.check_rate_limit():
                self.send_json({"error": "RateLimitExceeded", "message": "Rate limit exceeded (~10 req/s). Please throttle requests."}, 429, {"Retry-After": "1"})
                return

            content_length = int(self.headers.get("Content-Length", 0))
            if content_length > 1024 * 1024:
                self.send_json({"error": "PayloadTooLarge"}, 413)
                return

            body_bytes = self.rfile.read(content_length)
            content_type = self.headers.get("Content-Type", "")

            target_url = ""
            custom_headers = {}

            if "application/json" in content_type:
                try:
                    payload = json.loads(body_bytes.decode("utf-8"))
                    target_url = payload.get("url", "")
                    custom_headers = payload.get("headers", {})
                except Exception:
                    self.send_json({"error": "InvalidJson", "message": "Malformed JSON payload"}, 400)
                    return
            else:
                # Form encoded
                try:
                    form_data = urllib.parse.parse_qs(body_bytes.decode("utf-8"))
                    target_url = form_data.get("url", [""])[0]
                    headers_raw = form_data.get("headers", [""])[0]
                    if headers_raw:
                        custom_headers = json.loads(headers_raw)
                except Exception:
                    pass

            status_code, result = self.resolve_and_fetch_url(target_url, custom_headers)
            self.send_json(result, status_code)
            return

        self.send_json({"error": "NotFound", "path": path}, 404)

    def log_message(self, format, *args):
        sys.stdout.write(f"[MirrorApp] {self.address_string()} - {format % args}\n")
        sys.stdout.flush()


def run_server(host: str = "127.0.0.1", port: int = 8000):
    server_address = (host, port)
    httpd = HTTPServer(server_address, CloudMirrorHTTPHandler)
    print(f"[*] Cloud Mirror Web App listening on http://{host}:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cloud Mirror Web Application")
    parser.add_argument("--host", default="127.0.0.1", help="Binding host")
    parser.add_argument("--port", type=int, default=8000, help="Binding port")
    args = parser.parse_args()
    run_server(args.host, args.port)
