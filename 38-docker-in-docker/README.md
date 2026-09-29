# X08 — Docker-in-Docker

## Challenge Identity
* **Challenge ID:** X08
* **Name:** Docker-in-Docker
* **Category:** DinD / Docker Daemon / Nested Containers / Container Lifecycle
* **Difficulty:** Expert / Bonus
* **External Interface:** TCP/22 (SSH)
* **Classification:** `SANDBOX_REQUIRED`

---

## Challenge Summary

**Docker-in-Docker (X08)** is an advanced container architecture challenge focused on nested container runtimes, Docker daemon lifecycle manipulation, multi-tier network topologies, and microservice discovery.

Unlike container escape challenges (such as X07), **X08 is not an escape challenge**. The intended goal is to explore, enumerate, and pivot through a real nested Docker environment using legitimate Docker daemon controls and container management primitives. The dedicated VM sandbox acts as a firm isolation boundary.

---

## Architecture & Isolation Principle

```text
Player (External)
       │
     SSH/22
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│  Dedicated Disposable VM Sandbox (4 vCPU, 4 GiB, ≤8 GiB)    │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ CI Runner Node (operator:operator)                    │  │
│  │  - OpenSSH Server on TCP/22                           │  │
│  │  - Local Docker CLI & Unix Socket                     │  │
│  └──────────────────────────┬────────────────────────────┘  │
│                             │                               │
│                   Inner Docker Daemon                       │
│                             │                               │
│          ┌──────────────────┼──────────────────┐            │
│          ▼                  ▼                  ▼            │
│  ┌───────────────┐  ┌───────────────┐  ┌────────────────┐   │
│  │ ci-pipeline-  │  │ latveria-api- │  │ latveria-vault-│   │
│  │ worker        │  │ gateway       │  │ core           │   │
│  └───────┬───────┘  └───────┬───────┘  └───────┬────────┘   │
│          │                  │                  │            │
│          ▼                  ▼                  │            │
│  [ ci-frontend-net: 172.28.10.0/24 ]           │            │
│                                                ▼            │
│                          [ vault-internal-net: 172.28.20.0 ]│
│                                                │            │
│                                                ▼            │
│                                              FLAG           │
└─────────────────────────────────────────────────────────────┘
```

---

## Player Solve Chain

1. **Foothold:** Player connects via SSH using operator credentials (`operator:operator` on TCP/22).
2. **Inner Docker Discovery:** Player discovers access to the nested Docker daemon (`docker ps`, `docker images`, `docker network ls`, `docker volume ls`).
3. **Topology Mapping & Enumeration:**
   - Discovers two internal network segments: `ci-frontend-net` (public proxy) and `vault-internal-net` (isolated microservice mesh).
   - Identifies containers `ci-pipeline-worker`, `latveria-api-gateway`, and `latveria-vault-core`.
   - Inspects `ci-pipeline-worker` logs and mounted secret volume `deploy-secrets-vol` to locate deployment configs and the vault access token (`X-Vault-Access-Token`).
   - Identifies that `latveria-vault-core` is located strictly on `vault-internal-net:8443` and is not exposed to the host.
4. **Pivot & Target Access:**
   - Player uses Docker daemon control to pivot into `vault-internal-net` (e.g. running a container on `vault-internal-net` with `docker run --network vault-internal-net ...`, attaching an existing container via `docker network connect`, or executing inside `latveria-vault-core`).
5. **Flag Retrieval:**
   - Player queries `GET /api/v1/vault/flag` with the extracted `X-Vault-Access-Token` header to receive the dynamic flag.

---

## Directory Structure

```text
X08/
├── Dockerfile                  # Container build image with inner dockerd
├── docker-compose.yml          # Local container compose definition
├── entrypoint.sh               # Startup script initializing dockerd & inner mesh
├── README.md                   # Main challenge documentation
├── challenge/
│   ├── container/              # SSH & runner user configuration
│   ├── deployment/             # Kubernetes NetworkPolicy & ResourceQuota
│   ├── inner_services/         # Source code & Dockerfiles for inner containers
│   │   ├── admin_cli/          # Inner admin toolkit image
│   │   ├── api_gateway/        # Inner API gateway microservice
│   │   ├── ci_agent/           # Inner CI pipeline worker & deployment logs
│   │   └── vault_core/         # Inner target vault HTTP microservice
│   ├── network/                # iptables & boundary rules
│   ├── scripts/                # Reset, teardown, flag generation scripts
│   ├── snapshot/               # State seeders (seed_state.py)
│   └── vm/                     # Vagrant, QEMU, Cloud-init, Packer VM definitions
├── dist/
│   └── README.md               # Participant package
└── organizer/
    ├── SOLUTION.md             # Organizer solve guide & exploitation notes
    ├── solve.py                # Automated exploit & verification script
    └── test_challenge.py       # Full compliance & boundary test suite
```

---

## Lifecycle & Teardown

* **Reset:** `bash challenge/scripts/reset.sh <instance_id> <team_id>`
* **Teardown:** `bash challenge/scripts/teardown.sh <instance_id>`
