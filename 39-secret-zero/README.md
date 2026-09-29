# X09 — Secret Zero

**Category:** Machine Identity / Certificates / Secret Bootstrap  
**Difficulty:** Expert / Bonus  
**External Interface:** TCP/80 (HTTP)  

---

## 📖 Mission Briefing

Latveria's Citadel has upgraded its sovereign defenses to the **Aegis-Zero Machine Identity Infrastructure**. Under this zero-trust architecture, machines and microservices must prove their cryptographic identity before obtaining any runtime operational secrets—a paradigm known as solving **Secret Zero**.

The Doomsday Core is locked inside the **Protected Target Service**. To unseal it and retrieve the Sovereign Flag, you must obtain the **Secret Zero Master Key** from the internal **Secret Service**. However, the Secret Service requires a machine certificate with an authorized high-trust machine identity (`spiffe://latveria.local/ns/core/sa/vault-operator`) signed by the challenge-local Identity Authority.

Your starting entry point is the **Public Node Provisioning & Bootstrap Gateway** on port 80.

---

## 🎯 Objectives

1. Explore the public Bootstrap Gateway and inspect the machine provisioning mechanics.
2. Uncover the identity bootstrap chain and challenge-local PKI authority.
3. Obtain the necessary identity material to generate and issue an authorized high-trust machine certificate.
4. Authenticate to the internal Secret Service using your issued machine certificate.
5. Retrieve the **Secret Zero Master Key**.
6. Unseal the Protected Target and capture the flag.

---

## 🌐 Public Entry Point

- **Web Gateway:** `http://<TARGET_HOST>:<PORT>/`
- **Diagnostic Inspector:** `http://<TARGET_HOST>:<PORT>/api/diagnostics/view?item=bootstrap_agent.conf`
- **Mesh Dispatcher:** `POST http://<TARGET_HOST>:<PORT>/api/mesh/dispatch`

---

## 🛡️ Identity Trust Model

| Identity / SPIFFE ID | Trust Tier | Permissions |
| :--- | :--- | :--- |
| `spiffe://latveria.local/ns/edge/sa/telemetry-worker` | LOW_TRUST | Diagnostic telemetry & read-only status |
| `spiffe://latveria.local/ns/core/sa/vault-operator` | AUTHORIZED_SECRET_ZERO | Secret Zero issuance & Doomsday vault unsealing |

---

## ⚠️ Notes & Rules of Engagement

- The PKI hierarchy is completely challenge-local and isolated.
- The Kubernetes cluster infrastructure, cloud provider metadata, and event controller are out of bounds.
- All required operations occur through the challenge application interfaces.
