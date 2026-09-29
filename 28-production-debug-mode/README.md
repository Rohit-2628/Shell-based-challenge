# D28 — Production Debug Mode

**Category:** Web / Debug Disclosure / Service Discovery  
**Difficulty:** Very Hard  
**External Interface:** TCP/80 (Web)  
**Classification:** STANDARD  

---

## 1. Challenge Summary

D28 simulates a production telemetry gateway in Doctor Doom's defense infrastructure where debugging mode was accidentally left enabled in production. A participant discovers that submitting malformed telemetry queries or invalid syntax triggers a verbose debug disclosure containing stack traces, frame local variables, synthetic environment parameters, and internal microservice discovery maps. 

Using the discovered challenge-local debug authorization credentials and internal endpoint routes, the participant crafts an authorized executive query through the gateway dispatcher into the private ClusterIP-only executive core service to capture the sovereign defense grid flag.

```text
PLAYER
  |
  | TCP/80 (Web Gateway)
  v
PRODUCTION TELEMETRY GATEWAY (http://<HOST>:80/)
  |
  v
DEBUG HANDLER (Verbose Stack Traces & Runtime Environment Dump)
  |
  v
INTERNAL SERVICE DISCOVERY & CHALLENGE-LOCAL CREDENTIALS
  |
  v
CLUSTERIP INTERNAL EXECUTIVE CORE (http://127.0.0.1:8081)
  |
  v
FLAG
```

---

## 2. Directory Structure

```text
D28/
├── challenge/
│   ├── production/
│   │   ├── app.py                   # Production API server & gateway dispatcher (TCP/80)
│   │   ├── debug_handler.py         # Verbose debug disclosure formatter & stack trace engine
│   │   └── templates/
│   │       └── index.html           # Public web UI dashboard
│   ├── internal/
│   │   └── internal_service.py      # ClusterIP-only Internal Executive Core Daemon (127.0.0.1:8081)
│   └── deployment/
│       ├── deployment.yaml          # Kubernetes Deployment (Restricted Pod Security)
│       ├── service.yaml             # Kubernetes ClusterIP Service (Port 80)
│       ├── networkpolicy.yaml       # Kubernetes NetworkPolicy (Default Deny Ingress/Egress)
│       └── resourcequota.yaml       # Kubernetes ResourceQuota and LimitRange
├── dist/                            # Clean participant package (hygienic, leak-free)
│   └── README.md                    # Participant briefing & connection details
├── organizer/                       # Organizer-only material (outside participant package)
│   ├── SOLUTION.md                  # Comprehensive organizer documentation & walk-through
│   ├── solve.py                     # Clean-room automated solve script
│   └── test_challenge.py            # 10-step adversarial validation & test suite
├── Dockerfile                       # Hardened container image definition
├── docker-compose.yml               # Local testing & platform compose deployment
├── entrypoint.sh                    # Container initialization, flag isolation & service supervisor
└── README.md                        # Top-level challenge documentation
```

---

## 3. Quickstart & Deployment

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
python3 organizer/solve.py --host 127.0.0.1 --port 8080
```

### Full Adversarial & Compliance Test Suite
```bash
python3 organizer/test_challenge.py
```

### Compliance Gate Validation
```bash
python3 ../.agents/skills/ctf-challenge-engineering/scripts/validate_challenge.py . --dist-dir ./dist
```
