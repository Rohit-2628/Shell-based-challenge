# X05 — The Black Mirror

**Category:** SSRF / Internal Protocol / Service Discovery  
**Difficulty:** Expert / Bonus  
**External Interface:** TCP/80 (Web Gateway & SSRF Proxy)  
**Classification:** STANDARD (Restricted Pod Security Standard)

---

## Architectural Overview

```
Player
  │
  ▼ (TCP/80)
Web Proxy (Public Ingress & Mirror Probe)
  │
  ▼ (SSRF via gopher:// or http://)
Internal Protocol Service (SRP/1.0 on 127.0.0.1:9099)
  │
  ▼ (SRP Authorization Ticket: SRP_AUTH_...)
Next Stage (Citadel Vault Controller on 127.0.0.1:8088)
  │
  ▼ (Internal Secret Token)
Isolated Flag Vault (127.0.0.1:8089)
  │
  ▼
Flag
```

---

## Components

1. **Web Proxy (`challenge/web_proxy/app.py`)**:
   - Listens on `0.0.0.0:80`.
   - Exposes web dashboard and reflection probe endpoint (`POST /api/probe`).
   - Supports `http://`, `https://`, `gopher://`, `tcp://`.
   - Enforces challenge boundaries by blocking cloud metadata (`169.254.169.254`) and Kubernetes API ports.

2. **Internal Protocol Service (`challenge/internal_protocol/daemon.py`)**:
   - Listens on `127.0.0.1:9099` (ClusterIP only).
   - Speaks custom line-based **Sovereign Reflection Protocol (SRP/1.0)**.
   - Non-HTTP protocol. Provides interactive banner, command discovery, session nonces, and HMAC-backed stage-2 ticket derivation (`MIRROR <nonce> <node_id>`).

3. **Next Stage Vault Controller (`challenge/next_stage/vault.py`)**:
   - Listens on `127.0.0.1:8088` (ClusterIP only).
   - Validates SRP authorization tickets derived from protocol interaction.
   - Unlocks the vault upon verification.

4. **Isolated Flag Service (`challenge/flag_service/flag_server.py`)**:
   - Listens on `127.0.0.1:8089`.
   - Returns dynamic or team-scoped flag to authenticated stage-2 vault controller.

---

## Quick Start (Docker)

```bash
docker compose up --build
```
