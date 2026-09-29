# D26 – Compromised Developer Workstation
================================================================================
Category:   Developer Workstation / Git / Credential Chaining
Difficulty: Very Hard
Interface:  TCP/2227 (SSH)

MISSION BRIEFING:
SSH into the unprivileged developer workstation, recover historical CI signing secrets purged from the local Git working tree, reconstruct the HMAC-SHA256 signature scheme, and dispatch authorized telemetry payload to unlock the production flag.

CONNECTION DETAILS:
ssh developer@<TARGET_IP> -p 2227
Password: developer

RULES & GUIDANCE:
1. You have unprivileged access to the developer workstation.
2. Investigate developer artifacts, local git repositories, and project configurations.
3. Dispatch authorized production telemetry to retrieve the challenge flag.
================================================================================
