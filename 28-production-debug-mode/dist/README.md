# D28 — Production Debug Mode

**Difficulty:** Very Hard  
**Category:** Web / Debug Disclosure / Service Discovery  
**Author:** Latveria Cyber-Range Engineering  

---

## 1. Scenario & Intelligence Briefing

Intelligence reports indicate that Doctor Doom's engineering corps has recently deployed a new high-throughput telemetry gateway for the Latverian Defense Nexus. 

The public entry point is exposed as a web interface and HTTP API on TCP/80. While the system appears operational, field operatives report that recent high-priority updates were rushed directly into production.

Your mission is to interact with the public production API, investigate system responses and behavior, discover internal service architecture, and reach the final executive core flag.

---

## 2. Connection Details

Access the public production web service on TCP/80:

```bash
http://<TARGET_HOST>:<PORT>/
```

*(If testing locally via Docker Compose, access `http://127.0.0.1:8080/`)*

---

## 3. Objective & Flag Format

* Analyze the public API endpoints.
* Leverage discovered information to interface with internal services.
* Retrieve the executive defense grid flag.
* **Flag Format:** `YUVA{...}`
