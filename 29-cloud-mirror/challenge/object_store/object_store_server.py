#!/usr/bin/env python3
"""
Mock Object Storage Server for D29 — Cloud Mirror
Implements S3 / REST object storage simulation accepting temporary challenge credentials.
"""

import argparse
import datetime
import json
import mimetypes
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

VALID_TOKEN = "latv_sess_tok_d29_cloud_mirror_88f9104c2b9a7d3e"
VALID_ACCESS_KEY = "LATV_MIRROR_TEMP_8a92f0c7e1"

PUBLIC_BUCKETS = {"public-assets"}

class ObjectStoreHTTPHandler(BaseHTTPRequestHandler):
    server_version = "LatveriaMockObjectStore/1.0"

    @property
    def storage_dir(self) -> Path:
        return Path(self.server.storage_dir)

    def get_flag(self) -> str:
        flag_file = Path("/opt/storage/flag.txt")
        if flag_file.exists():
            return flag_file.read_text().strip()
        return os.environ.get("FLAG", "YUVA{cl0ud_m1rr0r_ssrf_m3t4d4t4_0bj_st0r3_7a9e2f}")

    def send_json(self, data: dict, status: int = 200):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Server", self.server_version)
        self.send_header("X-Latveria-Storage-Region", "latv-central-1")
        self.end_headers()
        self.wfile.write(body)

    def send_bytes(self, data: bytes, content_type: str = "application/octet-stream", status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Server", self.server_version)
        self.send_header("X-Latveria-Storage-Region", "latv-central-1")
        self.end_headers()
        self.wfile.write(data)

    def authenticate(self) -> tuple[bool, str]:
        """
        Check Authorization header, X-Latveria-Token, X-Amz-Security-Token, or query param.
        Returns (is_authenticated, token_found)
        """
        auth_header = self.headers.get("Authorization", "")
        token = ""

        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
        elif auth_header.startswith("AWS ") or auth_header.startswith("AWS4-HMAC-SHA256 "):
            token = self.headers.get("X-Amz-Security-Token", "").strip()
        elif "X-Latveria-Token" in self.headers:
            token = self.headers.get("X-Latveria-Token", "").strip()
        elif "X-Amz-Security-Token" in self.headers:
            token = self.headers.get("X-Amz-Security-Token", "").strip()
        
        # Check query string if header wasn't present
        if not token:
            parsed = urlparse(self.path)
            qs = parse_qs(parsed.query)
            if "token" in qs:
                token = qs["token"][0]
            elif "auth_token" in qs:
                token = qs["auth_token"][0]

        if not token:
            return False, "MISSING_TOKEN"

        if token == VALID_TOKEN:
            return True, "VALID"

        return False, "INVALID_TOKEN"

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        
        # Normalize paths
        # Examples:
        # /
        # /api/v1/storage
        # /api/v1/storage/buckets
        # /api/v1/storage/buckets/<bucket>/objects
        # /api/v1/storage/buckets/<bucket>/objects/<key>
        # /api/v1/storage/<bucket>/<key>
        # /<bucket>/<key>

        clean_path = path
        if clean_path.startswith("/api/v1/storage"):
            clean_path = clean_path[len("/api/v1/storage"):]

        clean_path = clean_path.rstrip("/")

        # Root / List Buckets
        if clean_path in ["", "/buckets"]:
            is_auth, auth_status = self.authenticate()
            buckets = []
            for b in sorted(self.storage_dir.glob("*")):
                if b.is_dir():
                    is_public = b.name in PUBLIC_BUCKETS
                    buckets.append({
                        "name": b.name,
                        "creation_date": "2026-09-26T00:00:00Z",
                        "access_policy": "PublicRead" if is_public else "PrivateIAMRestricted",
                        "requires_token": not is_public
                    })
            self.send_json({
                "service": "Latveria Mock Object Storage",
                "authenticated": is_auth,
                "buckets_count": len(buckets),
                "buckets": buckets
            })
            return

        # Handle bucket and object paths
        parts = [p for p in clean_path.split("/") if p and p != "buckets" and p != "objects"]
        if not parts:
            self.send_json({"error": "NotFound", "message": "Invalid storage path"}, 404)
            return

        bucket_name = parts[0]
        object_key = "/".join(parts[1:]) if len(parts) > 1 else ""

        bucket_dir = self.storage_dir / bucket_name
        if not bucket_dir.exists() or not bucket_dir.is_dir():
            self.send_json({"error": "NoSuchBucket", "message": f"Bucket '{bucket_name}' not found"}, 404)
            return

        is_public = bucket_name in PUBLIC_BUCKETS

        # Check authentication if private bucket
        if not is_public:
            is_auth, auth_status = self.authenticate()
            if not is_auth:
                if auth_status == "MISSING_TOKEN":
                    self.send_json({
                        "error": "AccessDenied",
                        "message": "Authorization required for private bucket. Provide temporary session token via 'Authorization: Bearer <Token>' or 'X-Latveria-Token: <Token>'."
                    }, 401)
                else:
                    self.send_json({
                        "error": "InvalidCredentials",
                        "message": "The provided security token is invalid or expired."
                    }, 403)
                return

        # List objects in bucket
        if not object_key:
            objects = []
            for obj in sorted(bucket_dir.glob("**/*")):
                if obj.is_file():
                    rel_key = obj.relative_to(bucket_dir).as_posix()
                    objects.append({
                        "key": rel_key,
                        "size_bytes": obj.stat().st_size if rel_key != "classified_mirror_master_key.dat" else 256,
                        "last_modified": "2026-09-26T06:00:00Z",
                        "storage_class": "STANDARD"
                    })
            self.send_json({
                "bucket": bucket_name,
                "object_count": len(objects),
                "objects": objects
            })
            return

        # Get specific object
        # Special handling for classified flag object
        if bucket_name == "classified-orbital-mirror" and object_key == "classified_mirror_master_key.dat":
            flag = self.get_flag()
            data = {
                "classification": "TOP SECRET // LATVERIA ORBITAL DEFENSE",
                "asset_id": "ORBITAL-MIRROR-DEFENSE-KEY-01",
                "status": "VALID",
                "description": "Master Mirror Defense Emergency Recovery Data",
                "issued_to": "LatveriaCloudMirrorRole",
                "flag": flag
            }
            self.send_json(data)
            return

        obj_file = bucket_dir / object_key
        # Prevent path traversal
        try:
            obj_file = obj_file.resolve()
            if not str(obj_file).startswith(str(bucket_dir.resolve())):
                self.send_json({"error": "AccessDenied", "message": "Path traversal detected"}, 403)
                return
        except Exception:
            self.send_json({"error": "InvalidPath", "message": "Invalid object path"}, 400)
            return

        if not obj_file.exists() or not obj_file.is_file():
            self.send_json({"error": "NoSuchKey", "message": f"Object '{object_key}' not found in bucket '{bucket_name}'"}, 404)
            return

        content = obj_file.read_bytes()
        content_type, _ = mimetypes.guess_type(str(obj_file))
        if not content_type:
            if obj_file.suffix == ".json":
                content_type = "application/json"
            else:
                content_type = "application/octet-stream"

        self.send_bytes(content, content_type=content_type)

    def log_message(self, format, *args):
        sys.stdout.write(f"[ObjectStore] {self.address_string()} - {format % args}\n")
        sys.stdout.flush()


def run_server(host: str = "127.0.0.1", port: int = 9000, storage_dir: str = "/var/lib/latveria-storage"):
    server_address = (host, port)
    httpd = HTTPServer(server_address, ObjectStoreHTTPHandler)
    httpd.storage_dir = storage_dir
    print(f"[*] Mock Object Store Service listening on http://{host}:{port} (storage: {storage_dir})")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mock Object Store Daemon")
    parser.add_argument("--host", default="127.0.0.1", help="Binding host")
    parser.add_argument("--port", type=int, default=9000, help="Binding port")
    parser.add_argument("--storage", default="/var/lib/latveria-storage", help="Storage base path")
    args = parser.parse_args()
    run_server(args.host, args.port, args.storage)
