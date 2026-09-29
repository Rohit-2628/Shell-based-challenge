# D31 — Shadow Cron

**Difficulty:** Intermediate  
**Category:** Linux / Cron / Privilege Escalation  
**Author:** Latveria Cyber-Range Engineering  

---

## 1. Scenario & Intelligence Briefing

Latverian border node `relay-node-epsilon` runs a periodic automated maintenance scheduler. An internal ops note from the last emergency patch cycle hints that maintenance script permissions were left too permissive. Your task is to investigate the scheduled jobs, identify the misconfigured script, and leverage it to extract the sovereign defense relay key.

---

## 2. Connection Details

Connect to the relay node via SSH using the provided credentials:

```bash
ssh operator@<HOST> -p <PORT>
```

* **Username:** `operator`  
* **Password:** `operator`

*(If running locally via Docker Compose, the port is `2222`: `ssh operator@127.0.0.1 -p 2222`)*

---

## 3. Objective & Flag Format

Investigate the node using standard Linux tools, locate the automated maintenance job, exploit the permission oversight, and retrieve the flag.

* **Flag Format:** `YUVA{...}`
