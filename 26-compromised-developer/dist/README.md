# D26 — Compromised Developer

**Difficulty:** Very Hard  
**Category:** Developer Workstation / Git / Credential Chaining  
**Author:** Latveria Cyber-Range Engineering  

---

## 1. Scenario & Intelligence Briefing

An unprivileged developer workstation inside Doctor Doom's internal engineering network was recently compromised during an initial intrusion. The intruder obtained access to the workstation account but terminated their session before completing their mission.

You have inherited direct SSH access to the compromised developer workstation.

Your objective is to investigate the workstation environment, reconstruct the developer's project trust relationships, navigate their internal development pipeline, and retrieve the sovereign defense telemetry flag from the production deployment stage.

---

## 2. Connection Details

Connect to the compromised developer workstation via SSH using the provided credentials:

```bash
ssh developer@<HOST> -p <PORT>
```

* **Username:** `developer`
* **Password:** `developer`

*(If running locally via Docker Compose, the port is `2222`: `ssh developer@127.0.0.1 -p 2222`)*

---

## 3. Objective & Flag Format

Investigate the system using standard Linux tools, follow the local trust chain, and retrieve the flag.

* **Flag Format:** `YUVA{...}`
