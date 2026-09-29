# D27 — Private Container Registry

## Challenge Briefing

**Difficulty:** Very Hard  
**Category:** Container Security / Image Layer Forensics / Cloud-Native  
**Flag Format:** `YUVA{...}`

---

### Scenario

Following Security Incident `SEC-2026-9901`, Latveria Cybernetic Command initiated a sweeping audit and sanitization protocol across all mission-critical orbital defense container workloads.

The primary production container images running in the orbital constellation have supposedly been scrubbed, rebuilt, and deployed under updated tags. However, intelligence indicates that the migration and cleanup process failed to account for historical image layer persistence within the state's private container registry.

An unprivileged security auditor workstation has been provisioned for your team, with access to the local container registry gateway and the internal defense vault daemon.

---

### Access Information

* **HTTP Gateway:** `http://<HOST>:8081/` (Docker / OCI Registry v2 API, Web Portal & Vault Gateway)
  *(If testing locally via Docker Compose, access `http://127.0.0.1:8081/`)*

---

### Challenge Objective

1. Enumerate the private container registry repositories and tags via `http://<HOST>:8081/v2/`.
2. Investigate image version histories, manifests, and historical layer blobs.
3. Locate and extract the historical developer configuration secret that was purged from current builds.
4. Authenticate against the Orbital Vault service endpoint (`http://<HOST>:8081/api/v1/vault/override`) using the recovered credentials.
5. Disengage the defense grid lock and retrieve the flag.

---

### Notes & API Reference

The local registry implements the standard **Docker / OCI Distribution Registry v2 HTTP API**:
* `GET /v2/` — Check Registry API availability
* `GET /v2/_catalog` — List repositories
* `GET /v2/<name>/tags/list` — List tags for a repository
* `GET /v2/<name>/manifests/<tag>` — Fetch manifest JSON
* `GET /v2/<name>/blobs/<digest>` — Download layer blob or config JSON

Good luck, Agent. Victor von Doom expects thoroughness.
