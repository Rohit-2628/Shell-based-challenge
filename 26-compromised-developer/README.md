# D26 — Compromised Developer

**Category:** Developer Workstation / Git / Credential Chaining  
**Difficulty:** Very Hard  
**External Interface:** TCP/22 (SSH)  
**Classification:** STANDARD  

---

## 1. Challenge Summary

D26 simulates an intrusion scenario against an unprivileged developer workstation belonging to Doctor Doom's internal engineering corps. The participant connects to the compromised developer environment via SSH, reconstructs local trust relationships across developer artifacts, extracts historical CI release secrets purged from the active working tree, validates the CI pipeline HMAC-SHA256 signature scheme, and executes an authorized production telemetry dispatch to unlock the challenge flag.

```text
PLAYER
  |
  | TCP/22 (SSH)
  v
DEVELOPER WORKSTATION
  |
  v
LOCAL GIT REPOSITORY (~/projects/latveria-telemetry-dispatch/)
  |
  v
GIT HISTORY & DELETED SECRETS INVESTIGATION
  |
  v
RECOVERED CI SIGNING SECRET & DEPLOY TOKEN
  |
  v
CI PIPELINE SPECIFICATION (HMAC-SHA256 request signing)
  |
  v
PRODUCTION MOCK (http://127.0.0.1:8080)
  |
  v
FLAG
```

---

## 2. Directory Structure

```text
D26/
├── challenge/
│   ├── workstation/
│   │   └── setup_workstation.sh      # Developer workstation environment & Git history builder
│   ├── production/
│   │   └── server.py                 # Isolated Production Mock Gateway (HMAC-SHA256 verified)
│   └── deployment/
│       ├── deployment.yaml           # Kubernetes Deployment (Restricted Pod Security)
│       ├── service.yaml              # Kubernetes ClusterIP Service (Port 22)
│       ├── networkpolicy.yaml        # Kubernetes NetworkPolicy (Default Deny Ingress/Egress)
│       └── resourcequota.yaml        # Kubernetes ResourceQuota and LimitRange
├── dist/                             # Participant distribution package (hygienic, leak-free)
│   └── README.md                     # Participant instructions, scenario briefing & credentials
├── organizer/                        # Organizer-only material (outside participant package)
│   ├── SOLUTION.md                   # Full 16-point organizer runbook & solution guide
│   ├── solve.py                      # Automated solve script
│   └── test_challenge.py             # 10-step adversarial test & validation suite
├── Dockerfile                        # Multi-user container image definition
├── docker-compose.yml                # Local testing & platform compose deployment
├── entrypoint.sh                     # Container initialization & process runner
└── README.md                         # Top-level challenge documentation
```

---

## 3. Quickstart & Deployment

### Local Docker Compose
```bash
docker compose up -d --build
```
Connect via SSH:
```bash
ssh developer@127.0.0.1 -p 2222
# Password: developer
```

### Automated Solve & Verification
```bash
python3 organizer/solve.py --host 127.0.0.1 --port 2222
```

### Full Adversarial & Compliance Test Suite
```bash
python3 organizer/test_challenge.py
```

### Compliance Gate Validation
```bash
python3 ../.agents/skills/ctf-challenge-engineering/scripts/validate_challenge.py . --dist-dir ./dist
```
