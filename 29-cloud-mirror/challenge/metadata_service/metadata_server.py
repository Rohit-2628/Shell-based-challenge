#!/usr/bin/env python3
"""
Mock Cloud Metadata Service for D29 — Cloud Mirror
Simulates cloud instance metadata endpoints (AWS IMDSv1/v2, GCP, Azure styles)
serving synthetic, challenge-local temporary credentials.
"""

import argparse
import datetime
import json
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler

# Challenge-local synthetic credentials
CREDENTIALS = {
    "Code": "Success",
    "LastUpdated": "2026-09-26T06:00:00Z",
    "Type": "AWS-HMAC-LATVERIA-MOCK",
    "AccessKeyId": "LATV_MIRROR_TEMP_8a92f0c7e1",
    "SecretAccessKey": "latv_sec_mirror_7b3d91a45c08e2f11904a",
    "Token": "latv_sess_tok_d29_cloud_mirror_88f9104c2b9a7d3e",
    "Expiration": "2026-09-27T06:00:00Z",
    "StorageService": {
        "Endpoint": "http://127.0.0.1:9000/api/v1/storage",
        "InternalDNS": "http://storage.internal/api/v1/storage",
        "AuthHeader": "Authorization: Bearer <Token> (or X-Latveria-Token: <Token>)",
        "Description": "Latveria Orbital Defense Mock Object Storage"
    },
    "RoleArn": "arn:latveria:iam::992019482019:role/LatveriaCloudMirrorRole"
}

STORAGE_SERVICE_INFO = {
    "service": "Latveria Object Storage Simulator (S3-compatible)",
    "endpoint": "http://127.0.0.1:9000/api/v1/storage",
    "internal_host": "http://storage.internal/api/v1/storage",
    "buckets_url": "/api/v1/storage/buckets",
    "authentication": {
        "scheme": "Bearer Token or X-Latveria-Token",
        "token_source": "Instance metadata LatveriaCloudMirrorRole.Token",
        "header_example": "Authorization: Bearer latv_sess_tok_d29_cloud_mirror_88f9104c2b9a7d3e"
    },
    "buckets": [
        "public-assets",
        "archive-backups",
        "internal-telemetry",
        "classified-orbital-mirror"
    ]
}

INSTANCE_IDENTITY = {
    "accountId": "992019482019",
    "architecture": "x86_64",
    "availabilityZone": "latv-central-1a",
    "imageId": "ami-09a8f2194e81b3720",
    "instanceId": "i-088f1a29d47c92b01",
    "instanceType": "cm.large",
    "privateIp": "10.142.0.42",
    "region": "latv-central-1",
    "version": "2026-09-26"
}


class MetadataHTTPHandler(BaseHTTPRequestHandler):
    server_version = "LatveriaMockMetadata/2.0"

    def send_text(self, text: str, status: int = 200, content_type: str = "text/plain"):
        body = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Server", self.server_version)
        self.send_header("X-Latveria-Metadata-Scope", "CHALLENGE-LOCAL-SYNTHETIC")
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, data: dict, status: int = 200):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Server", self.server_version)
        self.send_header("X-Latveria-Metadata-Scope", "CHALLENGE-LOCAL-SYNTHETIC")
        self.end_headers()
        self.wfile.write(body)

    def do_PUT(self):
        # AWS IMDSv2 Token acquisition
        if self.path in ["/latest/api/token", "/api/token"]:
            ttl = self.headers.get("X-aws-ec2-metadata-token-ttl-seconds", "21600")
            imds_token = "AQAAAH-latv-imds2-token-mock-99f8e21a"
            self.send_text(imds_token)
            return
        self.send_text("Method Not Allowed", 405)

    def do_GET(self):
        path = self.path.split("?")[0].rstrip("/")

        # Top-level paths
        if path in ["", "/"]:
            self.send_text("latest/\n")
            return
        if path == "/latest":
            self.send_text("dynamic/\nmeta-data/\napi/\nuser-data/\n")
            return
        if path == "/latest/meta-data":
            self.send_text("ami-id\nami-launch-index\nhostname\niam/\ninstance-action\ninstance-id\ninstance-type\nlocal-ipv4\nmac\nplacement/\npublic-keys/\nservices/\n")
            return

        # Specific metadata items
        if path == "/latest/meta-data/instance-id":
            self.send_text("i-088f1a29d47c92b01\n")
            return
        if path == "/latest/meta-data/hostname":
            self.send_text("latveria-cloud-mirror-01.internal\n")
            return
        if path == "/latest/meta-data/ami-id":
            self.send_text("ami-09a8f2194e81b3720\n")
            return
        if path == "/latest/meta-data/instance-type":
            self.send_text("cm.large\n")
            return
        if path == "/latest/meta-data/local-ipv4":
            self.send_text("10.142.0.42\n")
            return
        if path == "/latest/meta-data/mac":
            self.send_text("02:42:0a:8e:00:2a\n")
            return
        if path == "/latest/meta-data/placement":
            self.send_text("availability-zone\nregion\n")
            return
        if path == "/latest/meta-data/placement/availability-zone":
            self.send_text("latv-central-1a\n")
            return
        if path == "/latest/meta-data/placement/region":
            self.send_text("latv-central-1\n")
            return

        # IAM metadata
        if path == "/latest/meta-data/iam":
            self.send_text("security-credentials/\n")
            return
        if path == "/latest/meta-data/iam/security-credentials":
            self.send_text("LatveriaCloudMirrorRole\n")
            return
        if path == "/latest/meta-data/iam/security-credentials/LatveriaCloudMirrorRole":
            self.send_json(CREDENTIALS)
            return

        # Services metadata
        if path == "/latest/meta-data/services":
            self.send_text("object-storage/\n")
            return
        if path == "/latest/meta-data/services/object-storage":
            self.send_json(STORAGE_SERVICE_INFO)
            return

        # Dynamic identity document
        if path in ["/latest/dynamic/instance-identity/document", "/dynamic/instance-identity/document"]:
            self.send_json(INSTANCE_IDENTITY)
            return

        # GCP-style metadata compatibility
        if path == "/computeMetadata/v1/instance/service-accounts/default/token":
            self.send_json({
                "access_token": CREDENTIALS["Token"],
                "expires_in": 86400,
                "token_type": "Bearer",
                "storage_endpoint": "http://127.0.0.1:9000/api/v1/storage"
            })
            return
        if path == "/computeMetadata/v1/instance/service-accounts/default/email":
            self.send_text("cloud-mirror-sa@latveria-cloud-range.iam.gserviceaccount.internal\n")
            return

        # Azure-style metadata compatibility
        if path == "/metadata/instance":
            self.send_json({
                "compute": INSTANCE_IDENTITY,
                "security": {
                    "role": "LatveriaCloudMirrorRole",
                    "token": CREDENTIALS["Token"],
                    "storage_endpoint": "http://127.0.0.1:9000/api/v1/storage"
                }
            })
            return

        self.send_text("Not Found\n", 404)

    def log_message(self, format, *args):
        # Concise logging to stdout/stderr
        sys.stdout.write(f"[Metadata] {self.address_string()} - {format % args}\n")
        sys.stdout.flush()


def run_server(host: str = "127.0.0.1", port: int = 8181):
    server_address = (host, port)
    httpd = HTTPServer(server_address, MetadataHTTPHandler)
    print(f"[*] Mock Metadata Service listening on http://{host}:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mock Metadata Daemon")
    parser.add_argument("--host", default="127.0.0.1", help="Binding host")
    parser.add_argument("--port", type=int, default=8181, help="Binding port")
    args = parser.parse_args()
    run_server(args.host, args.port)
