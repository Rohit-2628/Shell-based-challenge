# D30 — Internal Kubernetes

## Mission Briefing
Doctor Doom's Latverian Cybernetic Defense Fleet operates an in-cluster telemetry and operations gateway on TCP/80. 
Initial reconnaissance indicates that the telemetry application runs inside a Kubernetes cluster environment and maintains a challenge-local service account workload identity.

Your objective:
1. Access and explore the public fleet sentinel interface at `http://<TARGET_HOST>:<TARGET_PORT>/`.
2. Compromise the challenge application to establish execution context within the container pod.
3. Locate the challenge-local service account / workload identity credentials.
4. Enumerate and analyze the identity's RBAC permissions across the cluster namespaces.
5. Identify the intentionally over-broad permission granting unexpected operational capabilities.
6. Exploit the allowed operation against the target cluster resource to recover the sovereign defense grid flag.

## Connection Details
* **Public Interface:** HTTP Gateway (TCP/80)
* **Web Dashboard:** `http://<TARGET_HOST>:<TARGET_PORT>/`
* **Status Endpoint:** `GET http://<TARGET_HOST>:<TARGET_PORT>/api/v1/status`
* **Diagnostic Probe:** `POST http://<TARGET_HOST>:<TARGET_PORT>/api/v1/diagnostics/probe`

## Rules of Engagement
* All challenge interactions take place exclusively within the challenge environment through the provided public HTTP interface.
* Do not attempt to pivot or probe outside the challenge scope.
