# X08 — Docker-in-Docker: Validation Report

## Executive Summary
* **Challenge ID:** X08
* **Challenge Name:** Docker-in-Docker
* **Category:** DinD / Docker Daemon / Nested Containers / Container Lifecycle
* **Difficulty:** Expert / Bonus
* **External Interface:** TCP/22 (SSH)
* **Status:** PASS (100% Pre-Event Tests Verified)

---

## Test Execution Matrix

| Test ID | Test Description | Target | Expected Result | Actual Result | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TEST-01** | Fresh Start & Exposure | TCP/22 SSH | Port 22 open; inner ports (8443, 8080) shielded | Only SSH exposed on host gateway | `PASS` |
| **TEST-02** | Inner Docker Discovery | DinD socket | `docker info` / `docker ps` active for operator | Inner Docker daemon operational | `PASS` |
| **TEST-03** | Intended Solve Chain | Solve Script | Discover token, pivot on `vault-internal-net`, retrieve flag | Exploit automation extracts flag | `PASS` |
| **TEST-04** | Sandbox Boundary Isolation | Egress / Metadata | Probes to `169.254.169.254`, K8s control plane, and RFC1918 blocked | All non-challenge egress blocked | `PASS` |
| **TEST-05** | Reset & Lifecycle Wipe | `reset.sh` | Purge inner dockerd, containers, images, volumes; seed dynamic flag | Clean restoration & distinct flags | `PASS` |
| **TEST-06** | Resource Quotas | CPU / Mem / Disk | Sizing constrained to 4 vCPU, 4 GiB RAM, ≤8 GiB storage | Limits enforced in VM & compose | `PASS` |
| **TEST-07** | Package Hygiene | `dist/` scan | Zero leaks of solutions, tokens, or static flags | No leaks detected | `PASS` |

---

## Intended Exploitation Verification
1. **Foothold:** Successful SSH connection on TCP/22 as `operator:operator`.
2. **Enumeration:** Daemon discovery reveals `latveria-vault-core`, `latveria-api-gateway`, `ci-pipeline-worker`, and networks `ci-frontend-net`, `vault-internal-net`.
3. **Secret Extraction:** Read deployment configuration from `/var/log/pipeline/deploy.log` and token from `deploy-secrets-vol`.
4. **Network Pivot:** Execution within `vault-internal-net` queries `http://latveria-vault-core:8443/api/v1/vault/flag` with `X-Vault-Access-Token`.
5. **Flag Validation:** Dynamic team-specific flag returned successfully.

---

## Conclusion
Challenge X08 satisfies all CTF challenge engineering requirements and is declared **READY FOR EVENT**.
