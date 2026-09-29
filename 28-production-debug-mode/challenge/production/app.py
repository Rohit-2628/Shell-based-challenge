#!/usr/bin/env python3
"""
Latveria Central Telemetry Gateway Production API
Public TCP/80 Web Interface
"""

import argparse
import collections
import json
import os
import sys
import time
import urllib.error
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

# Import debug handler
from debug_handler import format_debug_json, format_debug_html, SYNTHETIC_ENV_CONFIG

# In-memory sliding window rate limiter
RATE_LIMIT_WINDOW = 1.0  # seconds
MAX_REQUESTS_PER_WINDOW = 25  # requests per second per IP
_ip_request_history = collections.defaultdict(list)


def check_rate_limit(client_ip: str) -> bool:
    now = time.time()
    timestamps = _ip_request_history[client_ip]
    # Prune timestamps older than window
    _ip_request_history[client_ip] = [t for t in timestamps if now - t < RATE_LIMIT_WINDOW]
    if len(_ip_request_history[client_ip]) >= MAX_REQUESTS_PER_WINDOW:
        return False
    _ip_request_history[client_ip].append(now)
    return True


class TelemetryProcessingException(Exception):
    """Custom exception raised when telemetry processing fails."""
    pass


class UpstreamNexusServiceException(Exception):
    """Exception raised when internal telemetry microservice coordination fails."""
    pass


def dispatch_internal_command(service_url: str, auth_token: str, cmd_payload: dict):
    """
    Subsystem dispatch frame used to route internal cluster commands.
    Disclosed in stack traces during debug disclosure.
    """
    upstream_service = SYNTHETIC_ENV_CONFIG["INTERNAL_CORE_SERVICE_URL"]
    cluster_dns = SYNTHETIC_ENV_CONFIG["INTERNAL_CORE_DISCOVERY_NAME"]
    internal_target_route = SYNTHETIC_ENV_CONFIG["INTERNAL_EXECUTIVE_ROUTE"]
    auth_header_required = SYNTHETIC_ENV_CONFIG["INTERNAL_AUTH_HEADER"]
    debug_credential = SYNTHETIC_ENV_CONFIG["DEBUG_OVERRIDE_KEY"]
    service_scope = "cluster.internal.executive"
    payload_schema_spec = {
        "action": SYNTHETIC_ENV_CONFIG["REQUIRED_ACTION_PAYLOAD"],
        "target": SYNTHETIC_ENV_CONFIG["TARGET_CORE_NODE"],
        "auth_token": SYNTHETIC_ENV_CONFIG["DEBUG_OVERRIDE_KEY"]
    }
    
    # Intentionally raise exception when telemetry query payload is invalid or debug is triggered
    raise UpstreamNexusServiceException(
        f"Subsystem pipeline error: Failed to serialize telemetry vector for {cmd_payload.get('sector', 'unknown')}. "
        f"Invalid filter type or unhandled aggregation argument. Debug inspection enabled."
    )


def forward_to_upstream(target_service: str, route: str, payload: dict):
    """
    Internal gateway proxy dispatch layer.
    """
    dispatch_bridge = SYNTHETIC_ENV_CONFIG["INTERNAL_DISPATCH_GATEWAY"]
    retry_policy = "EXPONENTIAL_BACKOFF"
    max_retries = 3
    return dispatch_internal_command(target_service, SYNTHETIC_ENV_CONFIG["DEBUG_OVERRIDE_KEY"], payload)


def process_telemetry_request(request_data: dict, headers: dict):
    """
    Validates and processes telemetry queries.
    """
    sector = request_data.get("sector")
    metrics = request_data.get("metrics")
    filter_expr = request_data.get("filter")
    
    # Validation checks that raise safe error conditions when malformed
    if not isinstance(sector, str):
        raise TypeError(f"Invalid sector parameter type '{type(sector).__name__}'. Expected 'str'.")
    
    if not isinstance(metrics, list):
        raise TypeError(f"Invalid metrics parameter type '{type(metrics).__name__}'. Expected 'list[str]'.")
        
    if isinstance(filter_expr, str) and filter_expr == "malformed_syntax":
        raise ValueError(f"Syntax error in filter expression: '{filter_expr}' could not be parsed by vector engine.")

    # Call upstream pipeline (which will fail if debug flag or trigger is set)
    if request_data.get("debug") or headers.get("X-Debug") == "1":
        return forward_to_upstream(SYNTHETIC_ENV_CONFIG["INTERNAL_CORE_SERVICE_URL"], "/api/v1/telemetry", request_data)

    # Return calculated dummy telemetry
    return {
        "status": "success",
        "sector": sector,
        "metrics": {m: f"{42.0 + len(m)} UNIT" for m in metrics},
        "query_timestamp": int(time.time()),
        "node_count": len(metrics) * 2 + 1
    }


class ProductionGatewayHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Structured log output
        sys.stderr.write(f"[ProdGateway] {self.address_string()} - - [{self.log_date_time_string()}] {format % args}\n")

    def send_json(self, status_code: int, data: dict):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Powered-By", "Latveria-Nexus-Gateway/4.19")
        self.end_headers()
        self.wfile.write(body)

    def send_html(self, status_code: int, html_str: str):
        body = html_str.encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Powered-By", "Latveria-Nexus-Gateway/4.19")
        self.end_headers()
        self.wfile.write(body)

    def handle_debug_error(self, exc: Exception, context_info: dict):
        accept_header = self.headers.get("Accept", "")
        content_type = self.headers.get("Content-Type", "")
        
        # If API client or JSON requested, return structured JSON debug payload
        if "application/json" in accept_header or "application/json" in content_type or self.path.startswith("/api/"):
            debug_data = format_debug_json(exc, context_info)
            self.send_json(500, debug_data)
        else:
            debug_html = format_debug_html(exc, context_info)
            self.send_html(500, debug_html)

    def do_GET(self):
        client_ip = self.client_address[0]
        if not check_rate_limit(client_ip):
            self.send_json(429, {"status": "error", "error": "RateLimitExceeded", "message": "Rate limit exceeded (~20 req/sec limit)."})
            return

        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query_params = parse_qs(parsed_url.query)

        if path == "/" or path == "/index.html":
            template_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
            try:
                with open(template_path, "r", encoding="utf-8") as f:
                    content = f.read()
                self.send_html(200, content)
            except Exception as e:
                self.send_json(500, {"status": "error", "message": f"Template error: {e}"})
            return

        elif path == "/api/v1/status":
            self.send_json(200, {
                "status": "ONLINE",
                "cluster": "LATVERIA-CENTRAL-NEXUS-PROD",
                "uptime": "144h 23m 12s",
                "active_sectors": ["dooms-keep", "latveria-perimeter", "orbital-grid", "hydro-plant-01"],
                "gateway_version": "v4.19.2",
                "environment": "production"
            })
            return

        elif path == "/api/v1/telemetry/nodes":
            self.send_json(200, {
                "status": "success",
                "count": 4,
                "nodes": [
                    {"id": "reactor-core-01", "sector": "dooms-keep", "status": "ONLINE", "load": "74%"},
                    {"id": "sentinel-alpha", "sector": "latveria-perimeter", "status": "ONLINE", "load": "42%"},
                    {"id": "orbital-relay-09", "sector": "orbital-grid", "status": "ONLINE", "load": "61%"},
                    {"id": "hydro-turbine-03", "sector": "hydro-plant-01", "status": "ONLINE", "load": "35%"}
                ]
            })
            return

        elif path == "/api/v1/health":
            self.send_json(200, {"status": "UP", "timestamp": int(time.time())})
            return

        # Handle safe error trigger via query parameter ?debug=1
        if "debug" in query_params:
            try:
                raise TelemetryProcessingException(f"Explicit debug parameter requested from client IP {client_ip}.")
            except Exception as exc:
                self.handle_debug_error(exc, {"path": path, "query_params": query_params})
                return

        self.send_json(404, {"status": "error", "message": "Endpoint not found"})

    def do_POST(self):
        client_ip = self.client_address[0]
        if not check_rate_limit(client_ip):
            self.send_json(429, {"status": "error", "error": "RateLimitExceeded", "message": "Rate limit exceeded (~20 req/sec limit)."})
            return

        parsed_url = urlparse(self.path)
        path = parsed_url.path

        content_length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_length).decode("utf-8", errors="ignore") if content_length > 0 else ""
        
        request_data = {}
        if raw_body:
            try:
                request_data = json.loads(raw_body)
            except json.JSONDecodeError as json_err:
                # Malformed JSON triggers debug handler
                self.handle_debug_error(json_err, {"path": path, "raw_body_preview": raw_body[:100]})
                return

        if path == "/api/v1/telemetry/query":
            try:
                # Check for explicit debug trigger in query or headers
                if "debug" in parse_qs(parsed_url.query):
                    request_data["debug"] = True
                result = process_telemetry_request(request_data, dict(self.headers))
                self.send_json(200, result)
            except Exception as exc:
                self.handle_debug_error(exc, {
                    "path": path,
                    "payload_keys": list(request_data.keys()),
                    "request_data": request_data
                })
            return

        elif path == "/api/v1/gateway/dispatch":
            # Upstream microservice bridge
            auth_token = self.headers.get("X-Latveria-Debug-Token") or request_data.get("auth_token")
            expected_token = SYNTHETIC_ENV_CONFIG["DEBUG_OVERRIDE_KEY"]
            
            if auth_token != expected_token:
                self.send_json(403, {
                    "status": "forbidden",
                    "error": "DebugAuthFailed",
                    "message": "Access restricted: valid 'X-Latveria-Debug-Token' header or 'auth_token' credential required."
                })
                return

            # Target internal endpoint
            target_endpoint = request_data.get("endpoint", SYNTHETIC_ENV_CONFIG["INTERNAL_EXECUTIVE_ROUTE"])
            internal_url = f"{SYNTHETIC_ENV_CONFIG['INTERNAL_CORE_SERVICE_URL']}{target_endpoint}"

            # Prepare proxy request to internal service
            proxy_payload = {
                "action": request_data.get("action", ""),
                "target": request_data.get("target", ""),
                "auth_token": auth_token
            }
            req_data_bytes = json.dumps(proxy_payload).encode("utf-8")
            
            req = urllib.request.Request(
                internal_url,
                data=req_data_bytes,
                headers={
                    "Content-Type": "application/json",
                    "X-Latveria-Debug-Token": auth_token
                },
                method="POST"
            )

            try:
                with urllib.request.urlopen(req, timeout=5.0) as resp:
                    resp_data = json.loads(resp.read().decode("utf-8"))
                    self.send_json(resp.status, resp_data)
            except urllib.error.HTTPError as http_err:
                err_body = http_err.read().decode("utf-8", errors="ignore")
                try:
                    err_json = json.loads(err_body)
                except Exception:
                    err_json = {"error": str(http_err), "body": err_body}
                self.send_json(http_err.code, err_json)
            except Exception as conn_err:
                self.send_json(502, {
                    "status": "error",
                    "error": "BadGateway",
                    "message": f"Could not reach internal upstream service at {internal_url}: {conn_err}"
                })
            return

        self.send_json(404, {"status": "error", "message": "Unknown API endpoint"})


def main():
    parser = argparse.ArgumentParser(description="Latveria Central Telemetry Gateway Production API")
    parser.add_argument("--host", default="0.0.0.0", help="Host interface (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=80, help="Port (default: 80)")
    args = parser.parse_args()

    server = HTTPServer((args.host, args.port), ProductionGatewayHandler)
    print(f"[*] Latveria Telemetry Gateway listening on http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
