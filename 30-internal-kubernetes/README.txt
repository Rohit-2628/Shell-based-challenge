# D30 – Internal Kubernetes
================================================================================
Category:   Kubernetes Security / RBAC Exploitation / Service Account Pivoting
Difficulty: Very Hard+
Interface:  HTTP Gateway (TCP/80)

MISSION BRIEFING:
Doctor Doom's Latverian Cybernetic Defense Grid operates an in-cluster telemetry and workload diagnostic sentinel gateway on TCP/80.
Exploit the diagnostic probe system to gain an execution foothold within the unprivileged pod environment. Locate the challenge-local Kubernetes ServiceAccount credentials, audit the RBAC permission model across cluster namespaces, identify the over-broad permission granting unexpected operational capabilities, and execute against the target defense controller pod to extract the sovereign defense grid key.

CONNECTION DETAILS:
- Web Dashboard:    http://<TARGET_IP>/
- Health Status:    GET http://<TARGET_IP>/api/v1/status
- Diagnostic Probe: POST http://<TARGET_IP>/api/v1/diagnostics/probe

RULES & GUIDANCE:
1. All challenge interactions take place exclusively through the documented public HTTP interface on TCP/80.
2. The entire attack chain is isolated within the synthetic challenge environment.
================================================================================
