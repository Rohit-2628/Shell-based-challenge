# D27 – Private Container Registry
================================================================================
Category:   Cloud / OCI Registry / Layer Forensics
Difficulty: Very Hard
Interface:  HTTP Gateway (TCP/8081)

MISSION BRIEFING:
Enumerate the private Docker/OCI v2 registry catalog, inspect historical image manifests and layer digests for latveria/orbital-sentinel:v1.0.0, extract purged vault credentials, and authenticate against the vault API to retrieve the flag.

REGISTRY ENDPOINTS:
- Catalog:  http://<TARGET_IP>:8081/v2/_catalog
- Tags:     http://<TARGET_IP>:8081/v2/<name>/tags/list
- Manifest: http://<TARGET_IP>:8081/v2/<name>/manifests/<tag>
- Blobs:    http://<TARGET_IP>:8081/v2/<name>/blobs/<digest>

VAULT ENDPOINT:
- POST http://<TARGET_IP>:8081/api/v1/vault/override

RULES & GUIDANCE:
1. Query the private registry API and inspect image metadata and layer histories.
2. Extract required authorization credentials and unlock the vault to capture the flag.
================================================================================
