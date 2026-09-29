# D30 — Internal Kubernetes

**Category:** Kubernetes Security / RBAC Exploitation / Service Account Pivoting  
**Difficulty:** Very Hard+  
**External Interface:** TCP/80 (Web)  
**Classification:** STANDARD  

---

## 1. Challenge Summary

D30 simulates an in-cluster telemetry and diagnostic gateway in Doctor Doom's Latverian Cybernetic Defense Grid. A participant discovers a command injection vulnerability in the cluster diagnostic probe API on TCP/80 to establish an initial foothold within the unprivileged application pod.

Inside the container, the participant discovers the mounted Kubernetes ServiceAccount credentials (`system:serviceaccount:telemetry-system:telemetry-sentinel`). By inspecting permissions against the challenge-local mock Kubernetes API (`https://127.0.0.1:6443`), the participant determines that the identity possesses an over-broad permission: `create` on `pods/exec` in the restricted `orbital-defense` namespace.

The participant exploits this permission to execute commands inside the `doombot-defense-controller-0` pod and extract the sovereign defense grid key containing the flag.

```text
PLAYER (HTTP TCP/80)
  |
  v
FLEET SENTINEL WEB APPLICATION (http://<HOST>:80/)
  |
  v
DIAGNOSTIC PROBE COMMAND INJECTION FOOTHOLD (uid 1002 - sentinel)
  |
  v
CHALLENGE-LOCAL SERVICE ACCOUNT TOKEN (/var/run/secrets/kubernetes.io/serviceaccount/token)
  |
  v
MOCK KUBERNETES CONTROL PLANE & RBAC ENGINE (https://127.0.0.1:6443)
  |
  v
OVER-BROAD PERMISSION DISCOVERY (pods/exec in 'orbital-defense')
  |
  v
TARGET DEFENSE CONTROLLER POD (doombot-defense-controller-0)
  |
  v
FLAG: YUVA{k8s_rb4c_s3rv1c3_4cc0unt_3x3c_p1v0t_9d82e1}
```

---

## 2. Directory Structure

```text
D30/
├── challenge/
│   ├── app/
│   │   ├── server.py                # Fleet Sentinel web server & diagnostic probe API
│   │   ├── templates/
│   │   │   └── index.html           # Dashboard & interactive web console UI
│   │   └── static/
│   │       └── style.css            # Sci-fi terminal stylesheet
│   ├── k8s_api/
│   │   └── mock_k8s_server.py       # Deterministic mock Kubernetes API & RBAC engine
│   └── deployment/
│       ├── deployment.yaml          # Kubernetes Deployment (Restricted Pod Security)
│       ├── service.yaml             # Kubernetes ClusterIP Service (Port 80)
│       ├── networkpolicy.yaml       # Default-Deny Ingress/Egress NetworkPolicy
│       └── resourcequota.yaml       # Team Namespace ResourceQuota and LimitRange
├── dist/                            # Clean participant package (hygienic, leak-free)
│   └── README.md                    # Participant briefing & connection details
├── organizer/                       # Organizer-only material (outside participant package)
│   ├── SOLUTION.md                  # Comprehensive organizer documentation & walk-through
│   ├── solve.py                     # Clean-room automated solve script
│   └── test_challenge.py            # 10-step adversarial validation & test suite
├── Dockerfile                       # Hardened container image definition
├── docker-compose.yml               # Local testing & platform compose deployment
├── entrypoint.sh                    # Container initialization, identity setup & supervisor
└── README.md                        # Top-level challenge documentation
```

---

## 3. Quickstart & Verification

### Local Docker Compose
```bash
docker compose up -d --build
```
Access via web browser or curl:
```bash
curl -s http://127.0.0.1:8080/
```

### Automated Solve & Verification
```bash
python3 organizer/solve.py --url http://127.0.0.1:8080
```

### Full Adversarial & Compliance Test Suite
```bash
python3 organizer/test_challenge.py --url http://127.0.0.1:8080
```

### Compliance Gate Validation
```bash
python3 ../.agents/skills/ctf-challenge-engineering/scripts/validate_challenge.py . --dist-dir ./dist
```
