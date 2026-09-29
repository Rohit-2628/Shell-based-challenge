# D31 — Shadow Cron

**Category:** Linux / Cron / Privilege Escalation  
**Difficulty:** Intermediate  
**External Interface:** TCP/22 (SSH)  
**Classification:** STANDARD  

---

## 1. Challenge Summary

D31 simulates an improperly secured Latverian border telemetry relay node (`relay-node-epsilon`). A participant connects via SSH as unprivileged operator `operator`, investigates the automated maintenance cron scheduler, and discovers that the root-executed health-check script at `/opt/latveria-relay/scripts/relay_health_check.sh` was left world-writable during an emergency patch.

The participant overwrites the maintenance script with a payload that copies the root-protected sovereign defense relay key (`/opt/latveria-relay/defense_key.txt`, mode `0400`, root-owned) to a world-readable location. Within 60 seconds, the cron daemon executes the injected script as `root`, writing the flag to `/tmp/.relay_out`. The participant reads the output and submits the flag.

```text
PLAYER (SSH TCP/22)
  |
  v
OPERATOR WORKSTATION (operator, uid 1001)
  |
  v
CRON SCHEDULE DISCOVERY (/etc/cron.d/relay-maintenance)
  |
  v
WORLD-WRITABLE SCRIPT IDENTIFIED (/opt/latveria-relay/scripts/relay_health_check.sh, 0777)
  |
  v
PAYLOAD INJECTION (cp defense_key.txt → /tmp/.relay_out via cron root exec)
  |
  v
CRON EXECUTION AS ROOT (every 60 seconds)
  |
  v
FLAG READ: YUVA{cr0n_wr1t3_t0_r00t_l4tv3r14_r3l4y_7f3a2c}
```

---

## 2. Directory Structure

```text
D31/
├── challenge/
│   └── deployment/
│       ├── deployment.yaml      # Kubernetes Deployment (Restricted Pod Security)
│       ├── service.yaml         # Kubernetes ClusterIP Service (Port 22)
│       ├── networkpolicy.yaml   # Default-Deny Ingress/Egress NetworkPolicy
│       └── resourcequota.yaml   # Team Namespace ResourceQuota and LimitRange
├── dist/                        # Clean participant package (hygienic, leak-free)
│   └── README.md                # Participant briefing & connection details
├── organizer/                   # Organizer-only material (outside participant package)
│   ├── SOLUTION.md              # Comprehensive organizer documentation & walk-through
│   ├── solve.py                 # Clean-room automated solve script
│   └── test_challenge.py        # 10-step adversarial validation & test suite
├── Dockerfile                   # Hardened container image definition
├── docker-compose.yml           # Local testing & platform compose deployment
├── entrypoint.sh                # Container initialization, environment setup & service start
├── README.md                    # Top-level challenge documentation (this file)
└── README.txt                   # Participant briefing (dist-ready plain-text)
```

---

## 3. Quickstart & Verification

### Local Docker Compose
```bash
docker compose up -d --build
```
Connect via SSH:
```bash
ssh operator@127.0.0.1 -p 2222
# Password: operator
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
