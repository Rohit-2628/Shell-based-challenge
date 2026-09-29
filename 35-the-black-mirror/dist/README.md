# X05 — The Black Mirror

**Category:** SSRF / Internal Protocol / Service Discovery  
**Difficulty:** Expert / Bonus  
**Interface:** TCP/80 (HTTP)

---

## Challenge Briefing

Doctor Doom's sovereign defense network utilizes an internal reflection cluster code-named **THE BLACK MIRROR**. The public perimeter exposes an ingress proxy gateway for remote diagnostic reflection and network telemetry.

Deep inside the sovereign perimeter, internal microservices and custom reflection daemons maintain the Citadel's core security state. 

Your mission:
1. Investigate the public gateway on TCP/80.
2. Exploit the gateway's reflection probe to explore internal services.
3. Discover and fingerprint undocumented internal services.
4. Interact with the internal protocol to unlock the sovereign vault and retrieve the flag.

---

## Interface Details

- **Public Endpoint:** `http://<TARGET_HOST>:80/`
- **Supported Gateway Diagnostics:** Network Telemetry & Reflection Probe API
