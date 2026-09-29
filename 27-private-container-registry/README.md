# D27 — Private Container Registry

## Challenge Identity
* **Challenge ID:** D27
* **Name:** Private Container Registry
* **Difficulty:** Very Hard
* **Primary Concepts:** OCI / Docker Registry v2 API, Image Layer Forensics, Historical Secret Recovery, Internal Vault Authentication
* **External Interface:** TCP/80 (HTTP Registry Gateway) & TCP/22 (SSH Workstation)

---

## Overview
D27 is an authentic container registry forensic and exploitation challenge. The scenario models a sanitized production deployment where developers purged a sensitive credential file (`orbital_vault.conf`) from later image versions (`v2.1.0`, `v3.0.0`, `v3.0.1`, `latest`), but left historical layer blobs in earlier releases (`v1.0.0`) within the private container registry.

The player must:
1. Access the container registry or SSH workstation.
2. Query the Docker Registry v2 API catalog (`/v2/_catalog`) and list tags for `latveria/orbital-sentinel`.
3. Inspect image manifests and historical image configs across different tags.
4. Identify that `v1.0.0` contains a historical layer with `orbital_vault.conf` added in an earlier commit.
5. Download the specific layer blob via `/v2/latveria/orbital-sentinel/blobs/<digest>`.
6. Extract the layer tarball and recover `LATVERIAN_INTERNAL_TOKEN=latv_vault_sec_89f2a481c90e37b2d5140e678a119c8f`.
7. Authenticate against the isolated internal Orbital Vault service daemon (`http://127.0.0.1:8080/api/v1/vault/override`) to retrieve the flag.

---

## Quick Start (Local Testing)

```bash
docker-compose up --build -d
```

* Registry Web & API: `http://127.0.0.1:8080/` (or `http://127.0.0.1:8080/v2/_catalog`)
* SSH Workstation: `ssh developer@127.0.0.1 -p 2222` (Password: `developer`)

To run the automated solver:
```bash
python3 organizer/solve.py --port 2222
```

To run the pre-event adversarial validation test suite:
```bash
python3 organizer/test_challenge.py
```
