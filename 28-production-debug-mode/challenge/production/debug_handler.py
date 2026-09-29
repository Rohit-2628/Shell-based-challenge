import os
import json
import traceback
import sys

# Synthetic challenge-local configuration & discovery map
SYNTHETIC_ENV_CONFIG = {
    "LATVERIA_ENV": "production",
    "DEBUG_MODE": True,
    "DEBUG_VERBOSE_ERRORS": True,
    "SERVICE_NAME": "latveria-nexus-telemetry-gateway",
    "SERVICE_VERSION": "v4.19.2-prod-build992",
    "CLUSTER_INTERNAL_DOMAIN": "latveria.svc.cluster.local",
    "INTERNAL_CORE_SERVICE_URL": "http://127.0.0.1:8081",
    "INTERNAL_CORE_DISCOVERY_NAME": "latveria-internal-core.latveria.svc.cluster.local:8081",
    "INTERNAL_EXECUTIVE_ROUTE": "/api/v2/nexus/executive/control",
    "INTERNAL_DISPATCH_GATEWAY": "/api/v1/gateway/dispatch",
    "INTERNAL_AUTH_HEADER": "X-Latveria-Debug-Token",
    "DEBUG_OVERRIDE_KEY": "latveria_dbg_admin_8b91a742cd3f",
    "REQUIRED_ACTION_PAYLOAD": "query_executive_core",
    "TARGET_CORE_NODE": "sentinel_core_01",
    # Harmless synthetic decoys
    "KAFKA_BOOTSTRAP_SERVERS": "10.244.0.42:9092",
    "REDIS_CACHE_URL": "redis://127.0.0.1:6379/0",
    "METRICS_COLLECTOR_PORT": 9100,
    "CIRCUIT_BREAKER_TIMEOUT_SEC": 15,
    "SYNTHETIC_NOTE": "SYNTHETIC CHALLENGE LOCAL DATA - NO REAL CLUSTER SECRETS"
}


def build_stack_trace_info(exc: Exception):
    exc_type, exc_value, exc_tb = sys.exc_info()
    formatted_tb = traceback.format_exception(exc_type, exc_value, exc_tb)
    
    # Extract frame details
    frames = []
    curr_tb = exc_tb
    while curr_tb is not None:
        frame = curr_tb.tb_frame
        filename = frame.f_code.co_filename
        lineno = curr_tb.tb_lineno
        funcname = frame.f_code.co_name
        
        # Local variables snapshot for frame
        locals_sanitized = {}
        for k, v in frame.f_locals.items():
            if not k.startswith("__"):
                locals_sanitized[k] = repr(v)
                
        frames.append({
            "filename": filename,
            "lineno": lineno,
            "function": funcname,
            "locals": locals_sanitized
        })
        curr_tb = curr_tb.tb_next
        
    return {
        "error_type": exc.__class__.__name__,
        "error_message": str(exc),
        "raw_traceback": formatted_tb,
        "frames": frames
    }


def format_debug_json(exc: Exception, context_info: dict = None):
    stack_info = build_stack_trace_info(exc)
    
    response_data = {
        "status": "error",
        "code": 500,
        "error": "UnhandledProductionException",
        "message": f"Server encountered an unhandled exception: {exc.__class__.__name__} ({str(exc)})",
        "debug_mode": True,
        "debug_report": {
            "disclaimer": "CRITICAL: DEBUG_VERBOSE_ERRORS is enabled on production gateway. Inspect stack trace and internal configurations.",
            "exception": stack_info,
            "runtime_environment": SYNTHETIC_ENV_CONFIG,
            "request_context": context_info or {},
            "upstream_microservices": {
                "internal_nexus_core": {
                    "service_host": SYNTHETIC_ENV_CONFIG["INTERNAL_CORE_SERVICE_URL"],
                    "cluster_dns": SYNTHETIC_ENV_CONFIG["INTERNAL_CORE_DISCOVERY_NAME"],
                    "executive_endpoint": SYNTHETIC_ENV_CONFIG["INTERNAL_EXECUTIVE_ROUTE"],
                    "required_auth_header": SYNTHETIC_ENV_CONFIG["INTERNAL_AUTH_HEADER"],
                    "debug_auth_token": SYNTHETIC_ENV_CONFIG["DEBUG_OVERRIDE_KEY"],
                    "target_node": SYNTHETIC_ENV_CONFIG["TARGET_CORE_NODE"],
                    "expected_action": SYNTHETIC_ENV_CONFIG["REQUIRED_ACTION_PAYLOAD"]
                },
                "cache_service": {
                    "url": SYNTHETIC_ENV_CONFIG["REDIS_CACHE_URL"],
                    "status": "ONLINE"
                }
            }
        }
    }
    return response_data


def format_debug_html(exc: Exception, context_info: dict = None):
    data = format_debug_json(exc, context_info)
    json_dump = json.dumps(data, indent=2)
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>500 Internal Server Error — Production Debug Console</title>
    <style>
        body {{
            background-color: #0d1117;
            color: #c9d1d9;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            margin: 0;
            padding: 30px;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.5);
            padding: 24px;
        }}
        .header {{
            border-bottom: 1px solid #30363d;
            padding-bottom: 16px;
            margin-bottom: 20px;
        }}
        .badge {{
            background: #f85149;
            color: #ffffff;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
        }}
        h1 {{
            color: #f85149;
            margin-top: 10px;
            font-size: 24px;
        }}
        .section-title {{
            color: #58a6ff;
            font-size: 18px;
            margin-top: 24px;
            margin-bottom: 12px;
            border-bottom: 1px solid #21262d;
            padding-bottom: 6px;
        }}
        pre {{
            background: #0d1117;
            border: 1px solid #30363d;
            border-radius: 6px;
            padding: 16px;
            overflow-x: auto;
            font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
            font-size: 13px;
            line-height: 1.5;
            color: #7ee787;
        }}
        .frame {{
            background: #0d1117;
            border-left: 3px solid #f85149;
            padding: 10px 14px;
            margin-bottom: 12px;
            border-radius: 0 4px 4px 0;
        }}
        .frame-header {{
            color: #79c0ff;
            font-weight: bold;
            font-size: 14px;
        }}
        .frame-locals {{
            margin-top: 6px;
            font-size: 12px;
            color: #8b949e;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <span class="badge">DEBUG_VERBOSE_ERRORS ENABLED</span>
            <h1>Unhandled Production Exception: {exc.__class__.__name__}</h1>
            <p><strong>Message:</strong> {str(exc)}</p>
            <p><small>Service: <code>{SYNTHETIC_ENV_CONFIG["SERVICE_NAME"]}</code> ({SYNTHETIC_ENV_CONFIG["SERVICE_VERSION"]})</small></p>
        </div>

        <div class="section-title">Stack Trace & Frame Inspection</div>
        {"".join(f'<div class="frame"><div class="frame-header">{f["filename"]}:{f["lineno"]} in <code>{f["function"]}</code></div><div class="frame-locals"><strong>Locals:</strong> {f["locals"]}</div></div>' for f in data["debug_report"]["exception"]["frames"])}

        <div class="section-title">Raw Structured Debug Payload (JSON)</div>
        <pre>{json_dump}</pre>
    </div>
</body>
</html>"""
    return html
