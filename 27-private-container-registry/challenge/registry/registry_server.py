#!/usr/bin/env python3
"""
Latverian Defense Mesh - Private Container Registry v2 Daemon
Standards-compliant OCI / Docker Registry v2 HTTP server with web UI.
Enforces read-only player access, bounded storage, and structured logging.
"""

import argparse
import hashlib
import json
import os
import sys
from http import HTTPStatus
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

REGISTRY_STORAGE = Path(os.environ.get("REGISTRY_STORAGE", "/var/lib/latveria-registry"))
WEB_DIR = Path(__file__).resolve().parent / "web"

class RegistryHandler(BaseHTTPRequestHandler):
    server_version = "Latveria-ContainerRegistry/2.4.0"
    
    def log_message(self, format, *args):
        # Structured single-line access logs
        sys.stderr.write(f"[{self.log_date_time_string()}] {self.client_address[0]} {format % args}\n")
        sys.stderr.flush()

    def send_registry_headers(self, content_type="application/json", content_length=None, digest=None, status=200):
        self.send_response(status)
        self.send_header("Server", self.server_version)
        self.send_header("Docker-Distribution-Api-Version", "registry/2.0")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, HEAD, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type, Accept")
        self.send_header("Content-Type", content_type)
        if content_length is not None:
            self.send_header("Content-Length", str(content_length))
        if digest:
            self.send_header("Docker-Content-Digest", digest)
        self.end_headers()

    def do_OPTIONS(self):
        self.send_registry_headers(status=200)

    def do_POST(self):
        self.send_error_response(HTTPStatus.METHOD_NOT_ALLOWED, "DENIED", "Registry is configured in read-only mode for audit compliance.")

    def do_PUT(self):
        self.send_error_response(HTTPStatus.METHOD_NOT_ALLOWED, "DENIED", "Registry is configured in read-only mode for audit compliance.")

    def do_DELETE(self):
        self.send_error_response(HTTPStatus.METHOD_NOT_ALLOWED, "DENIED", "Registry is configured in read-only mode for audit compliance.")

    def send_error_response(self, status_code, error_code, message):
        body = json.dumps({
            "errors": [
                {
                    "code": error_code,
                    "message": message,
                    "detail": None
                }
            ]
        }, indent=2).encode("utf-8")
        self.send_registry_headers("application/json", len(body), status=status_code)
        self.wfile.write(body)

    def do_HEAD(self):
        self.handle_request(is_head=True)

    def do_GET(self):
        self.handle_request(is_head=False)

    def handle_request(self, is_head=False):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        if not path:
            path = "/"

        # -----------------------------------------------------------------
        # Web UI and Documentation Endpoints
        # -----------------------------------------------------------------
        if path == "/" or path == "/index.html":
            index_file = WEB_DIR / "index.html"
            if index_file.exists():
                content = index_file.read_bytes()
                self.send_registry_headers("text/html; charset=utf-8", len(content), status=200)
                if not is_head:
                    self.wfile.write(content)
                return
            else:
                body = b"Latveria Private Container Registry v2 - Online"
                self.send_registry_headers("text/plain", len(body), status=200)
                if not is_head:
                    self.wfile.write(body)
                return

        if path == "/style.css":
            css_file = WEB_DIR / "style.css"
            if css_file.exists():
                content = css_file.read_bytes()
                self.send_registry_headers("text/css", len(content), status=200)
                if not is_head:
                    self.wfile.write(content)
                return

        # -----------------------------------------------------------------
        # Docker Registry v2 Base Check: GET /v2/
        # -----------------------------------------------------------------
        if path == "/v2":
            body = b"{}\n"
            self.send_registry_headers("application/json", len(body), status=200)
            if not is_head:
                self.wfile.write(body)
            return

        # -----------------------------------------------------------------
        # Catalog: GET /v2/_catalog
        # -----------------------------------------------------------------
        if path == "/v2/_catalog":
            repos = []
            repos_dir = REGISTRY_STORAGE / "repositories"
            if repos_dir.exists():
                for org_path in sorted(repos_dir.iterdir()):
                    if org_path.is_dir():
                        for repo_path in sorted(org_path.iterdir()):
                            if repo_path.is_dir():
                                repo_name = f"{org_path.name}/{repo_path.name}"
                                repos.append(repo_name)
            
            payload = json.dumps({"repositories": repos}, indent=2).encode("utf-8")
            self.send_registry_headers("application/json", len(payload), status=200)
            if not is_head:
                self.wfile.write(payload)
            return

        # -----------------------------------------------------------------
        # Tags List: GET /v2/<name>/tags/list
        # -----------------------------------------------------------------
        if path.startswith("/v2/") and path.endswith("/tags/list"):
            # Extract repository name between /v2/ and /tags/list
            repo_name = path[len("/v2/"): -len("/tags/list")]
            manifests_dir = REGISTRY_STORAGE / "repositories" / repo_name / "manifests"
            if not manifests_dir.exists():
                self.send_error_response(HTTPStatus.NOT_FOUND, "NAME_UNKNOWN", f"Repository {repo_name} not found.")
                return
            
            tags = []
            for item in sorted(manifests_dir.iterdir()):
                # Exclude raw 64-char sha256 filenames that are digest copies
                if item.is_file() and len(item.name) != 64:
                    tags.append(item.name)
                    
            payload = json.dumps({"name": repo_name, "tags": tags}, indent=2).encode("utf-8")
            self.send_registry_headers("application/json", len(payload), status=200)
            if not is_head:
                self.wfile.write(payload)
            return

        # -----------------------------------------------------------------
        # Manifests: GET /v2/<name>/manifests/<reference>
        # -----------------------------------------------------------------
        if "/manifests/" in path and path.startswith("/v2/"):
            parts = path[len("/v2/"):].split("/manifests/")
            if len(parts) == 2:
                repo_name, reference = parts
                clean_ref = reference.replace("sha256:", "")
                manifest_file = REGISTRY_STORAGE / "repositories" / repo_name / "manifests" / clean_ref
                
                if not manifest_file.exists():
                    self.send_error_response(HTTPStatus.NOT_FOUND, "MANIFEST_UNKNOWN", f"Manifest reference {reference} not found in {repo_name}.")
                    return
                
                manifest_bytes = manifest_file.read_bytes()
                manifest_digest = "sha256:" + hashlib.sha256(manifest_bytes).hexdigest()
                
                self.send_registry_headers(
                    content_type="application/vnd.docker.distribution.manifest.v2+json",
                    content_length=len(manifest_bytes),
                    digest=manifest_digest,
                    status=200
                )
                if not is_head:
                    self.wfile.write(manifest_bytes)
                return

        # -----------------------------------------------------------------
        # Blobs: GET /v2/<name>/blobs/<digest>
        # -----------------------------------------------------------------
        if "/blobs/" in path and path.startswith("/v2/"):
            parts = path[len("/v2/"):].split("/blobs/")
            if len(parts) == 2:
                repo_name, digest = parts
                clean_digest = digest.replace("sha256:", "")
                blob_file = REGISTRY_STORAGE / "blobs" / clean_digest
                
                if not blob_file.exists():
                    self.send_error_response(HTTPStatus.NOT_FOUND, "BLOB_UNKNOWN", f"Blob {digest} not found.")
                    return
                
                blob_bytes = blob_file.read_bytes()
                # Determine content type based on content inspection or generic octet-stream
                ctype = "application/octet-stream"
                if blob_bytes.startswith(b"\x1f\x8b"):
                    ctype = "application/vnd.docker.image.rootfs.diff.tar.gzip"
                elif blob_bytes.startswith(b"{"):
                    ctype = "application/vnd.docker.container.image.v1+json"

                self.send_registry_headers(
                    content_type=ctype,
                    content_length=len(blob_bytes),
                    digest=f"sha256:{clean_digest}",
                    status=200
                )
                if not is_head:
                    self.wfile.write(blob_bytes)
                return

        # Fallback 404
        self.send_error_response(HTTPStatus.NOT_FOUND, "NOT_FOUND", "Endpoint not found on Latverian Registry Gateway.")


def run_server(host="0.0.0.0", port=5000):
    server_address = (host, port)
    httpd = HTTPServer(server_address, RegistryHandler)
    print(f"[*] Latveria Private Container Registry v2 listening on http://{host}:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Shutting down registry server.")
        httpd.server_close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Latveria Private Container Registry Daemon")
    parser.add_argument("--host", default="0.0.0.0", help="Binding interface")
    parser.add_argument("--port", type=int, default=5000, help="Port to listen on")
    parser.add_argument("--storage", default="/var/lib/latveria-registry", help="Registry storage root")
    args = parser.parse_args()
    
    REGISTRY_STORAGE = Path(args.storage)
    run_server(args.host, args.port)
