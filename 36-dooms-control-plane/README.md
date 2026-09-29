# X06 — Doom's Control Plane

## Challenge Identity
- **Challenge ID**: X06
- **Name**: Doom's Control Plane
- **Category**: Internal Orchestration / API Authorization / Workload Management
- **Difficulty**: Expert / Bonus
- **External Interface**: TCP/80 (HTTP Web Portal & Mesh Gateway)

## Primary Concepts
- Internal orchestration and synthetic workload lifecycle
- Scoped challenge-local API authorization (RBAC)
- Workload manager state transitions and scaling
- Internal loopback mesh routing and service unsealing
- Synthetic control plane isolation

## Architecture
```text
Player (TCP/80)
   │
   ▼
Public Web Portal (0.0.0.0:80)
   │
   ▼ (Loopback Mesh Dispatch)
Synthetic Control API (127.0.0.1:8081)
   │
   ▼ (Workload State Transitions & Scaling)
Workload Manager Simulator (127.0.0.1:8082)
   │
   ▼ (Activation & Route Binding)
Sovereign Core Service (127.0.0.1:8083)
   │
   ▼ (Mutual Secret Auth)
Isolated Flag Vault (127.0.0.1:8084)
```

## Intended Solve Chain
1. **Compromise / Credential Recovery**:
   - Access public web portal on port 80.
   - Use `/api/diagnostics/log?file=operator.log` and navigate to `/app/challenge/credentials/operator_credentials.json` (or `?file=../../credentials/operator_credentials.json`) to recover the scoped control plane token:
     `dcp_tok_maint_9a8f4c2e1b7d5e6a3c8f`.
2. **API Discovery & Capability Enumeration**:
   - Dispatch `GET http://127.0.0.1:8081/api/v1/auth/introspect` via `/api/mesh/dispatch`.
   - Enumerate allowed scopes: `workloads:list`, `workloads:inspect`, `workloads:transition:prepare_maintenance`, `workloads:scale`, `workloads:activate:mesh`.
3. **Workload Inspection**:
   - Dispatch `GET http://127.0.0.1:8081/api/v1/workloads` to discover `sovereign-core-gateway` (quarantined in `ISOLATED` state).
4. **Trigger Workload Transitions**:
   - Step 1: Transition `sovereign-core-gateway` from `ISOLATED` -> `STANDBY`:
     `POST http://127.0.0.1:8081/api/v1/workloads/sovereign-core-gateway/transition` with `{"action": "prepare_maintenance"}`.
   - Step 2: Scale replica count to 1:
     `POST http://127.0.0.1:8081/api/v1/workloads/sovereign-core-gateway/scale` with `{"replicas": 1}`.
   - Step 3: Activate service route:
     `POST http://127.0.0.1:8081/api/v1/workloads/sovereign-core-gateway/activate` with `{"target_state": "ACTIVE", "route": "internal_mesh"}`.
5. **Access Sovereign Core Service**:
   - Dispatch `GET http://127.0.0.1:8083/core/status` -> confirms `ONLINE`.
   - Dispatch `GET http://127.0.0.1:8083/core/vault` -> retrieves flag.

## Flag
`YUVA{synthet1c_c0ntr0l_pl4n3_sc0p3d_0rch3str4t10n_x06}`
