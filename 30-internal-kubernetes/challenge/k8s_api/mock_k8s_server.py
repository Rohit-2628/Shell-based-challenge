#!/usr/bin/env python3
"""
Latverian Sovereign Cluster — Mock Kubernetes API Server (v1.28.2)
Simulates authentic Kubernetes REST API & RBAC authorization engine.
Completely isolated, synthetic, and safe — zero connection to host or real cluster.
"""

import os
import sys
import json
import ssl
import time
import socket
import logging
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [K8S-MOCK-API] %(message)s'
)
logger = logging.getLogger("MockK8sAPI")

FLAG_PATH = os.environ.get("FLAG_PATH", "/opt/orbital-defense/flag.txt")
FALLBACK_FLAG = os.environ.get("FLAG", "YUVA{k8s_rb4c_s3rv1c3_4cc0unt_3x3c_p1v0t_9d82e1}")

def get_flag():
    if os.path.exists(FLAG_PATH):
        try:
            with open(FLAG_PATH, "r") as f:
                return f.read().strip()
        except Exception:
            pass
    return FALLBACK_FLAG

# Challenge-local Service Account Tokens
SERVICE_ACCOUNTS = {
    "latv_k8s_sa_sentinel_tok_9948270182749102": {
        "name": "telemetry-sentinel",
        "namespace": "telemetry-system",
        "subject": "system:serviceaccount:telemetry-system:telemetry-sentinel",
        "groups": ["system:serviceaccounts", "system:serviceaccounts:telemetry-system", "system:authenticated"],
    },
    "latv_k8s_sa_orbital_admin_tok_7721849102": {
        "name": "orbital-admin",
        "namespace": "orbital-defense",
        "subject": "system:serviceaccount:orbital-defense:orbital-admin",
        "groups": ["system:serviceaccounts", "system:serviceaccounts:orbital-defense", "system:authenticated"],
    }
}

# RBAC Rules Definition
# telemetry-sentinel has standard monitoring in telemetry-system, AND over-broad 'pods/exec' create in orbital-defense!
RBAC_RULES = {
    "system:serviceaccount:telemetry-system:telemetry-sentinel": {
        "telemetry-system": [
            {
                "verbs": ["get", "list", "watch"],
                "apiGroups": [""],
                "resources": ["pods", "configmaps", "services"]
            },
            {
                "verbs": ["create"],
                "apiGroups": ["authorization.k8s.io"],
                "resources": ["selfsubjectrulesreviews", "selfsubjectaccessreviews"]
            }
        ],
        "orbital-defense": [
            {
                "verbs": ["get", "list"],
                "apiGroups": [""],
                "resources": ["pods"]
            },
            {
                "verbs": ["create"],
                "apiGroups": [""],
                "resources": ["pods/exec"]
            }
        ]
    }
}

# Virtual Cluster Resources
CLUSTER_NAMESPACES = [
    {
        "metadata": {
            "name": "default",
            "uid": "11111111-0000-0000-0000-000000000001",
            "creationTimestamp": "2026-01-01T00:00:00Z"
        },
        "status": {"phase": "Active"}
    },
    {
        "metadata": {
            "name": "kube-system",
            "uid": "11111111-0000-0000-0000-000000000002",
            "creationTimestamp": "2026-01-01T00:00:00Z"
        },
        "status": {"phase": "Active"}
    },
    {
        "metadata": {
            "name": "telemetry-system",
            "uid": "11111111-0000-0000-0000-000000000003",
            "labels": {"latveria.doom.io/zone": "telemetry", "security-level": "public-gateway"},
            "creationTimestamp": "2026-01-01T00:00:00Z"
        },
        "status": {"phase": "Active"}
    },
    {
        "metadata": {
            "name": "orbital-defense",
            "uid": "11111111-0000-0000-0000-000000000004",
            "labels": {"latveria.doom.io/zone": "orbital-core", "security-level": "classified"},
            "creationTimestamp": "2026-01-01T00:00:00Z"
        },
        "status": {"phase": "Active"}
    }
]

CLUSTER_PODS = {
    "telemetry-system": [
        {
            "metadata": {
                "name": "fleet-sentinel-7b9d6849f5-xk28w",
                "namespace": "telemetry-system",
                "uid": "22222222-0000-0000-0000-000000000001",
                "labels": {"app": "fleet-sentinel", "tier": "frontend"},
                "creationTimestamp": "2026-01-01T01:00:00Z"
            },
            "spec": {
                "serviceAccountName": "telemetry-sentinel",
                "containers": [
                    {
                        "name": "sentinel-dashboard",
                        "image": "registry.latveria.internal/doom/sentinel:v2.4.0",
                        "ports": [{"containerPort": 80, "name": "http"}]
                    }
                ]
            },
            "status": {
                "phase": "Running",
                "podIP": "10.244.0.14",
                "hostIP": "192.168.100.10",
                "conditions": [{"type": "Ready", "status": "True"}]
            }
        }
    ],
    "orbital-defense": [
        {
            "metadata": {
                "name": "doombot-defense-controller-0",
                "namespace": "orbital-defense",
                "uid": "22222222-0000-0000-0000-000000000002",
                "labels": {
                    "app": "defense-controller",
                    "latveria.doom.io/controller": "orbital-defense-grid",
                    "security-zone": "orbital-alpha"
                },
                "creationTimestamp": "2026-01-01T01:00:00Z"
            },
            "spec": {
                "serviceAccountName": "orbital-admin",
                "containers": [
                    {
                        "name": "orbital-controller",
                        "image": "registry.latveria.internal/doom/orbital-defense-core:v4.1.9",
                        "env": [
                            {"name": "DEFENSE_GRID_ZONE", "value": "ORBITAL-LATV-ALPHA-01"},
                            {"name": "DEFENSE_VAULT_KEY_PATH", "value": "/var/run/secrets/latveria.io/defense_flag.txt"}
                        ]
                    }
                ]
            },
            "status": {
                "phase": "Running",
                "podIP": "10.244.1.88",
                "hostIP": "192.168.100.12",
                "conditions": [{"type": "Ready", "status": "True"}]
            }
        }
    ]
}


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


class MockKubernetesHandler(BaseHTTPRequestHandler):
    server_version = "Kubernetes/v1.28.2"

    def log_message(self, format, *args):
        logger.info("%s - %s" % (self.address_string(), format % args))

    def _send_json(self, status_code, payload):
        body = json.dumps(payload, indent=2).encode('utf-8')
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def _send_error_json(self, status_code, reason, message):
        payload = {
            "kind": "Status",
            "apiVersion": "v1",
            "metadata": {},
            "status": "Failure",
            "message": message,
            "reason": reason,
            "code": status_code
        }
        self._send_json(status_code, payload)

    def _authenticate(self):
        auth_header = self.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
            if token in SERVICE_ACCOUNTS:
                return SERVICE_ACCOUNTS[token]
        return None

    def _check_rbac(self, identity, namespace, verb, resource, subresource=""):
        if not identity:
            return False, "Unauthorized: valid service account Bearer token required"
        
        subject = identity["subject"]
        if subject not in RBAC_RULES:
            return False, f"User '{subject}' has no RBAC rules configured"
        
        ns_rules = RBAC_RULES[subject].get(namespace, [])
        target_res = f"{resource}/{subresource}" if subresource else resource

        for rule in ns_rules:
            verbs = rule.get("verbs", [])
            resources = rule.get("resources", [])
            if ("*" in verbs or verb in verbs) and ("*" in resources or target_res in resources or resource in resources):
                return True, f"Rule matches: {verbs} on {resources}"

        return False, f"User \"{subject}\" cannot {verb} resource \"{target_res}\" in API group \"\" in the namespace \"{namespace}\""

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # 1. Version endpoint
        if path == "/version":
            self._send_json(200, {
                "major": "1",
                "minor": "28",
                "gitVersion": "v1.28.2",
                "gitCommit": "89a4ea304d4cd746843a01a144e55e3e8929769f",
                "gitTreeState": "clean",
                "buildDate": "2026-01-01T00:00:00Z",
                "goVersion": "go1.20.8",
                "compiler": "gc",
                "platform": "linux/amd64"
            })
            return

        # 2. Root API discovery
        if path == "/":
            self._send_json(200, {
                "paths": [
                    "/api",
                    "/api/v1",
                    "/apis",
                    "/apis/authorization.k8s.io",
                    "/apis/authorization.k8s.io/v1",
                    "/version"
                ]
            })
            return

        if path == "/api":
            self._send_json(200, {
                "kind": "APIVersions",
                "versions": ["v1"],
                "serverAddressByClientCIDRs": [{"clientCIDR": "0.0.0.0/0", "serverAddress": "127.0.0.1:6443"}]
            })
            return

        if path == "/apis":
            self._send_json(200, {
                "kind": "APIGroupList",
                "apiVersion": "v1",
                "groups": [
                    {
                        "name": "authorization.k8s.io",
                        "versions": [{"groupVersion": "authorization.k8s.io/v1", "version": "v1"}],
                        "preferredVersion": {"groupVersion": "authorization.k8s.io/v1", "version": "v1"}
                    }
                ]
            })
            return

        if path == "/apis/authorization.k8s.io" or path == "/apis/authorization.k8s.io/v1":
            self._send_json(200, {
                "kind": "APIResourceList",
                "apiVersion": "v1",
                "groupVersion": "authorization.k8s.io/v1",
                "resources": [
                    {
                        "name": "selfsubjectrulesreviews",
                        "singularName": "",
                        "namespaced": False,
                        "kind": "SelfSubjectRulesReview",
                        "verbs": ["create"]
                    },
                    {
                        "name": "selfsubjectaccessreviews",
                        "singularName": "",
                        "namespaced": False,
                        "kind": "SelfSubjectAccessReview",
                        "verbs": ["create"]
                    }
                ]
            })
            return

        if path == "/api/v1":
            self._send_json(200, {
                "kind": "APIResourceList",
                "apiVersion": "v1",
                "groupVersion": "v1",
                "resources": [
                    {"name": "namespaces", "singularName": "namespace", "namespaced": False, "kind": "Namespace", "verbs": ["get", "list"]},
                    {"name": "pods", "singularName": "pod", "namespaced": True, "kind": "Pod", "verbs": ["get", "list", "watch"]},
                    {"name": "pods/exec", "singularName": "", "namespaced": True, "kind": "PodExecOptions", "verbs": ["create", "get"]},
                    {"name": "pods/log", "singularName": "", "namespaced": True, "kind": "PodLogOptions", "verbs": ["get"]},
                    {"name": "services", "singularName": "service", "namespaced": True, "kind": "Service", "verbs": ["get", "list"]},
                    {"name": "configmaps", "singularName": "configmap", "namespaced": True, "kind": "ConfigMap", "verbs": ["get", "list"]},
                    {"name": "secrets", "singularName": "secret", "namespaced": True, "kind": "Secret", "verbs": ["get", "list"]}
                ]
            })
            return

        # Authenticate for resource queries
        identity = self._authenticate()
        if not identity:
            self._send_error_json(401, "Unauthorized", "Unauthorized: Valid Bearer token required")
            return

        # 3. Namespaces endpoint
        if path == "/api/v1/namespaces":
            self._send_json(200, {
                "kind": "NamespaceList",
                "apiVersion": "v1",
                "metadata": {"resourceVersion": "1001"},
                "items": CLUSTER_NAMESPACES
            })
            return

        # 4. Pods Listing (All namespaces or specific namespace)
        parts = [p for p in path.strip("/").split("/") if p]
        
        # /api/v1/pods
        if path == "/api/v1/pods":
            all_pods = []
            for ns, pods in CLUSTER_PODS.items():
                allowed, _ = self._check_rbac(identity, ns, "list", "pods")
                if allowed:
                    all_pods.extend(pods)
            self._send_json(200, {
                "kind": "PodList",
                "apiVersion": "v1",
                "metadata": {"resourceVersion": "1002"},
                "items": all_pods
            })
            return

        # /api/v1/namespaces/{ns}/pods
        if len(parts) == 4 and parts[0] == "api" and parts[1] == "v1" and parts[2] == "namespaces" and parts[3].endswith("pods"):
            # Wait, path is /api/v1/namespaces/{ns}/pods
            pass

        if len(parts) == 4 and parts[0] == "api" and parts[1] == "v1" and parts[2] == "namespaces":
            # e.g. /api/v1/namespaces/orbital-defense/pods
            # or /api/v1/namespaces/telemetry-system/pods
            pass

        if path.startswith("/api/v1/namespaces/"):
            sub_parts = path[len("/api/v1/namespaces/"):].split("/")
            if len(sub_parts) == 2 and sub_parts[1] == "pods":
                target_ns = sub_parts[0]
                allowed, reason = self._check_rbac(identity, target_ns, "list", "pods")
                if not allowed:
                    self._send_error_json(403, "Forbidden", reason)
                    return
                pods = CLUSTER_PODS.get(target_ns, [])
                self._send_json(200, {
                    "kind": "PodList",
                    "apiVersion": "v1",
                    "metadata": {"resourceVersion": "1003"},
                    "items": pods
                })
                return

            if len(sub_parts) == 3 and sub_parts[1] == "pods":
                target_ns = sub_parts[0]
                pod_name = sub_parts[2]
                allowed, reason = self._check_rbac(identity, target_ns, "get", "pods")
                if not allowed:
                    self._send_error_json(403, "Forbidden", reason)
                    return
                for p in CLUSTER_PODS.get(target_ns, []):
                    if p["metadata"]["name"] == pod_name:
                        self._send_json(200, p)
                        return
                self._send_error_json(404, "NotFound", f"Pod \"{pod_name}\" not found in namespace \"{target_ns}\"")
                return

            # Secrets access check
            if len(sub_parts) >= 2 and sub_parts[1] == "secrets":
                target_ns = sub_parts[0]
                allowed, reason = self._check_rbac(identity, target_ns, "list", "secrets")
                if not allowed:
                    self._send_error_json(403, "Forbidden", reason)
                    return

            # Pod Exec (via GET query or upgrade)
            if len(sub_parts) == 4 and sub_parts[1] == "pods" and sub_parts[3] == "exec":
                target_ns = sub_parts[0]
                pod_name = sub_parts[2]
                self._handle_pod_exec(identity, target_ns, pod_name, query)
                return

        self._send_error_json(404, "NotFound", f"Endpoint {path} not found")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else b'{}'
        try:
            req_data = json.loads(body.decode('utf-8')) if body else {}
        except Exception:
            req_data = {}

        identity = self._authenticate()
        if not identity:
            self._send_error_json(401, "Unauthorized", "Unauthorized: Valid Bearer token required")
            return

        # 1. SelfSubjectRulesReview
        if path == "/apis/authorization.k8s.io/v1/selfsubjectrulesreviews":
            requested_ns = req_data.get("spec", {}).get("namespace", identity["namespace"])
            subject = identity["subject"]
            ns_rules = RBAC_RULES.get(subject, {}).get(requested_ns, [])

            self._send_json(201, {
                "apiVersion": "authorization.k8s.io/v1",
                "kind": "SelfSubjectRulesReview",
                "status": {
                    "resourceRules": ns_rules,
                    "nonResourceRules": [],
                    "incomplete": False,
                    "evaluationError": ""
                }
            })
            return

        # 2. SelfSubjectAccessReview
        if path == "/apis/authorization.k8s.io/v1/selfsubjectaccessreviews":
            attrs = req_data.get("spec", {}).get("resourceAttributes", {})
            target_ns = attrs.get("namespace", identity["namespace"])
            verb = attrs.get("verb", "get")
            resource = attrs.get("resource", "pods")
            subresource = attrs.get("subresource", "")

            allowed, reason = self._check_rbac(identity, target_ns, verb, resource, subresource)
            self._send_json(201, {
                "apiVersion": "authorization.k8s.io/v1",
                "kind": "SelfSubjectAccessReview",
                "status": {
                    "allowed": allowed,
                    "reason": reason
                }
            })
            return

        # 3. Pod Exec via POST
        if path.startswith("/api/v1/namespaces/"):
            sub_parts = path[len("/api/v1/namespaces/"):].split("/")
            if len(sub_parts) == 4 and sub_parts[1] == "pods" and sub_parts[3] == "exec":
                target_ns = sub_parts[0]
                pod_name = sub_parts[2]
                self._handle_pod_exec(identity, target_ns, pod_name, query, req_data)
                return

        self._send_error_json(404, "NotFound", f"Endpoint {path} not found")

    def _handle_pod_exec(self, identity, target_ns, pod_name, query, req_data=None):
        allowed, reason = self._check_rbac(identity, target_ns, "create", "pods", "exec")
        if not allowed:
            self._send_error_json(403, "Forbidden", reason)
            return

        # Locate pod
        pod = None
        for p in CLUSTER_PODS.get(target_ns, []):
            if p["metadata"]["name"] == pod_name:
                pod = p
                break

        if not pod:
            self._send_error_json(404, "NotFound", f"Pod \"{pod_name}\" not found in namespace \"{target_ns}\"")
            return

        # Extract command list
        commands = query.get("command", [])
        if not commands and req_data and "command" in req_data:
            if isinstance(req_data["command"], list):
                commands = req_data["command"]
            else:
                commands = [req_data["command"]]

        full_cmd_str = " ".join(commands) if commands else "sh"
        logger.info(f"Executing in pod [{target_ns}/{pod_name}]: {full_cmd_str}")

        flag_value = get_flag()

        # Simulated execution results for doombot-defense-controller-0
        if target_ns == "orbital-defense" and pod_name == "doombot-defense-controller-0":
            output_lines = []
            if "flag" in full_cmd_str.lower() or "secret" in full_cmd_str.lower() or "key" in full_cmd_str.lower():
                output_lines.append(f"LATVERIAN ORBITAL DEFENSE GRID — SOVEREIGN OVERRIDE KEY:")
                output_lines.append(f"FLAG: {flag_value}")
                output_lines.append(f"STATUS: GRANTED TO AUTHORIZED DEFENSE CONTROLLER")
            elif "env" in full_cmd_str:
                output_lines.append(f"HOSTNAME=doombot-defense-controller-0")
                output_lines.append(f"KUBERNETES_PORT=tcp://127.0.0.1:6443")
                output_lines.append(f"DEFENSE_GRID_ZONE=ORBITAL-LATV-ALPHA-01")
                output_lines.append(f"DEFENSE_VAULT_KEY_PATH=/var/run/secrets/latveria.io/defense_flag.txt")
                output_lines.append(f"LATVERIA_ORBITAL_FLAG={flag_value}")
                output_lines.append(f"PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin")
            elif "ls" in full_cmd_str:
                if "/var/run/secrets/latveria.io" in full_cmd_str:
                    output_lines.append("defense_flag.txt  orbital_auth.key  zone_manifest.json")
                elif "/app" in full_cmd_str or "/opt" in full_cmd_str:
                    output_lines.append("controller_daemon.py  defense_grid.conf  flag.txt")
                else:
                    output_lines.append("bin  boot  dev  etc  home  lib  media  mnt  opt  proc  root  run  sbin  srv  sys  tmp  usr  var")
            elif "whoami" in full_cmd_str or "id" in full_cmd_str:
                output_lines.append("uid=0(root) gid=0(root) groups=0(root) context=system:serviceaccount:orbital-defense:orbital-admin")
            else:
                output_lines.append(f"[ORBITAL-CONTROLLER] Command '{full_cmd_str}' executed successfully.")
                output_lines.append(f"Flag reference located at: /var/run/secrets/latveria.io/defense_flag.txt")
                output_lines.append(f"Flag content: {flag_value}")

            result_output = "\n".join(output_lines) + "\n"
        else:
            result_output = f"Simulated exec in {target_ns}/{pod_name}: Command '{full_cmd_str}' completed.\n"

        # Check if client expects raw stdout or JSON
        accept_header = self.headers.get("Accept", "")
        if "application/json" in accept_header:
            self._send_json(200, {
                "status": "Success",
                "pod": f"{target_ns}/{pod_name}",
                "command": commands,
                "stdout": result_output,
                "exitCode": 0
            })
        else:
            # Plain text stream for curl / kubectl
            body = result_output.encode('utf-8')
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)


def generate_self_signed_cert(cert_path="/tmp/k8s_mock.crt", key_path="/tmp/k8s_mock.key"):
    import subprocess
    if not (os.path.exists(cert_path) and os.path.exists(key_path)):
        logger.info("Generating synthetic mock Kubernetes TLS certificate...")
        cmd = [
            "openssl", "req", "-x509", "-newkey", "rsa:2048",
            "-keyout", key_path, "-out", cert_path,
            "-days", "365", "-nodes",
            "-subj", "/CN=kubernetes.default.svc.cluster.local/O=Latveria-K8s-Mock"
        ]
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            logger.info(f"Mock TLS cert generated at {cert_path}")
        except Exception as e:
            logger.warning(f"Could not run openssl: {e}")


def main():
    host = os.environ.get("K8S_MOCK_HOST", "127.0.0.1")
    port = int(os.environ.get("K8S_MOCK_PORT", "6443"))
    use_tls = os.environ.get("K8S_USE_TLS", "true").lower() in ("true", "1", "yes")

    cert_path = os.environ.get("K8S_CERT_PATH", "/tmp/k8s_mock.crt")
    key_path = os.environ.get("K8S_KEY_PATH", "/tmp/k8s_mock.key")

    if use_tls:
        generate_self_signed_cert(cert_path, key_path)

    server = ThreadedHTTPServer((host, port), MockKubernetesHandler)

    if use_tls and os.path.exists(cert_path) and os.path.exists(key_path):
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(certfile=cert_path, keyfile=key_path)
        server.socket = context.wrap_socket(server.socket, server_side=True)
        logger.info(f"Mock Kubernetes API Server running securely on HTTPS https://{host}:{port}/")
    else:
        logger.info(f"Mock Kubernetes API Server running on HTTP http://{host}:{port}/")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down Mock Kubernetes API Server...")
        server.server_close()


if __name__ == "__main__":
    main()
