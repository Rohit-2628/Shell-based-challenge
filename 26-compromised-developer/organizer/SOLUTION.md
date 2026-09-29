# D26 — Compromised Developer: Organizer Solution & Engineering Runbook

## 1. Challenge Overview
* **Challenge ID:** D26
* **Name:** Compromised Developer
* **Difficulty:** Very Hard
* **Category:** Developer Workstation / Git / Credential Chaining
* **External Interface:** TCP/22 (SSH)
* **Author / Team:** Latveria Cyber-Range Engineering Team

---

## 2. Architecture
The challenge architecture models an unprivileged Linux workstation that connects into an internal CI/CD trust chain and production deployment mock:

```text
PLAYER
  |
  | TCP/22 (SSH Gateway)
  v
SSH WORKSTATION (Linux unprivileged developer environment)
  |
  v
LOCAL GIT REPOSITORY (~/projects/latveria-telemetry-dispatch/)
  |
  v
GIT COMMIT HISTORY / DELETED SECRET INVESTIGATION
  |
  v
RECOVERED CI SIGNING SECRET & DEPLOY TOKEN
  |
  v
CI PIPELINE CONFIGURATION (HMAC-SHA256 request signing)
  |
  v
INTERNAL PRODUCTION MOCK (http://127.0.0.1:8080)
  |
  v
FLAG
```

All services are self-contained. The production gateway service is bound internally and executes as an isolated unprivileged user (`prod`, uid 1002). The workstation runs as unprivileged user `developer` (uid 1001).

---

## 3. Starting State
The participant connects via SSH as `developer` with password `developer`.

Initial workstation state:
* `/home/developer/`:
  * `.bash_history`: Realistic commands indicating past enumeration and testing.
  * `notes/pipeline_notes.txt`: Developer notes detailing architecture, production gateway endpoints, deployment header requirements, and an audit notice referencing deleted keys.
  * `scripts/check_health.sh`: Utility script testing internal service connectivity.
  * `projects/latveria-telemetry-dispatch/`: Local Git repository of the telemetry project.

---

## 4. Intended Discovery Path
1. **Initial Enumeration:** Inspect home directory, notes, bash history, and running services.
2. **Repository Discovery:** Navigate to `~/projects/latveria-telemetry-dispatch` and examine git status, log, and branches.
3. **Git History Investigation:** Analyze commit log across all branches (`git log --all -p` or `git log --all --stat`).
4. **Credential Recovery:** Discover commit `feat(ci): implement HMAC-SHA256 production deployment authentication and local backup keys` and its subsequent purge commit. Extract the deleted `ci/release_keys.env` file content from git history:
   * `DOOM_CI_SIGNING_KEY=latv_ci_sec_984f8a32b91c49e7b1a0d8f3319082ec`
   * `DOOM_DEPLOY_TOKEN=DOOM_PROD_DEPLOY_TOKEN_v4.2.9812`
   * `DOOM_CALLER_ID=latveria_ci_agent_99`
   * `DOOM_DISPATCH_ACTION=PROD_DISPATCH_RELEASE`
5. **CI Pipeline Discovery:** Inspect `ci/pipeline.py` and `.gitlab-ci.yml` to understand the HMAC-SHA256 signing scheme and how requests are dispatched.
6. **Production Pivot:** Use the recovered credentials to execute `ci/pipeline.py` with `--key` and `--token` or craft a signed HTTP POST request to `http://127.0.0.1:8080/api/v1/telemetry/deploy`.
7. **Flag Retrieval:** The production mock validates the CI trust chain and returns the flag.

---

## 5. Exact Commands Used During Solve

### Step 1: Connect to the Workstation
```bash
ssh developer@<HOST> -p <PORT>
# Enter password: developer
```

### Step 2: Enumerate Workstation
```bash
ls -la
cat notes/pipeline_notes.txt
cd projects/latveria-telemetry-dispatch
git status
```

### Step 3: Investigate Git History
```bash
git log --all --oneline --graph
git log -p -n 5
```

Inspect the commit where `release_keys.env` was added and subsequently purged:
```bash
git show v1.2.0:ci/release_keys.env
# OR
git log -p -S "DOOM_CI_SIGNING_KEY"
```

Recovered secrets:
```text
DOOM_CI_SIGNING_KEY=latv_ci_sec_984f8a32b91c49e7b1a0d8f3319082ec
DOOM_DEPLOY_TOKEN=DOOM_PROD_DEPLOY_TOKEN_v4.2.9812
DOOM_CALLER_ID=latveria_ci_agent_99
DOOM_DISPATCH_ACTION=PROD_DISPATCH_RELEASE
```

### Step 4: Execute Signed Production Deployment
Run the CI pipeline deployment script using the recovered keys:
```bash
python3 ci/pipeline.py \
  --key latv_ci_sec_984f8a32b91c49e7b1a0d8f3319082ec \
  --token DOOM_PROD_DEPLOY_TOKEN_v4.2.9812 \
  --caller latveria_ci_agent_99 \
  --action PROD_DISPATCH_RELEASE \
  --endpoint http://127.0.0.1:8080/api/v1/telemetry/deploy
```

Or inject into environment:
```bash
export DOOM_CI_SIGNING_KEY="latv_ci_sec_984f8a32b91c49e7b1a0d8f3319082ec"
export DOOM_DEPLOY_TOKEN="DOOM_PROD_DEPLOY_TOKEN_v4.2.9812"
python3 ci/pipeline.py
```

### Step 5: Read Flag
The production gateway responds with:
```json
{
  "status": "SUCCESS",
  "message": "CI trust chain verified. Production telemetry dispatch mesh unlocked.",
  "authorization": {
    "caller": "latveria_ci_agent_99",
    "action": "PROD_DISPATCH_RELEASE",
    "token_id": "TOKEN-LATV-RELEASE-V4",
    "pipeline_verified": true
  },
  "dispatch_result": {
    "target": "orbital-defense-node-01",
    "state": "DEPLOYED",
    "telemetry_stream": "ACTIVE"
  },
  "flag": "YUVA{c0mpr0m1s3d_d3v_h1st0ry_hm4c_auth_8821}"
}
```

---

## 6. Credential Discovery
The credentials were historically committed to Git in a previous release before a security audit (`SEC-2026-4402`). They were deleted from the current `HEAD` commit but preserved in Git object storage and reachable via commit diffs, tags (`v1.2.0`), or branch `feature/ci-auth-v2`.

---

## 7. Git Investigation
* Branch `main`: Clean tree without plaintext credentials.
* Tag `v1.2.0`: Marks the prototype commit containing `ci/release_keys.env`.
* History diffs (`git log -p`) clearly show the exact diff removing the secrets.

---

## 8. CI Discovery
* `.gitlab-ci.yml` specifies the production deploy stage invoking `ci/pipeline.py`.
* `ci/pipeline.py` implements the HMAC-SHA256 signing calculation.

---

## 9. Production Pivot
The production mock runs locally on `127.0.0.1:8080` as user `prod`. It exposes `/api/v1/telemetry/deploy` and validates the HMAC signature, timestamp drift, caller identity, and deployment token.

---

## 10. Flag Retrieval
The flag is returned in the JSON payload of the authorized production deployment response.

---

## 11. Expected Flag
Default flag:
`YUVA{c0mpr0m1s3d_d3v_h1st0ry_hm4c_auth_8821}`

---

## 12. Reset Procedure
Redeploying the container / Kubernetes pod completely resets the filesystem, workstation state, and production mock.

---

## 13. Known Decoys
* Decoy telemetry configuration: `config/settings.json` contains dummy internal channel names.
* Dummy unit test suite: `tests/test_telemetry.py`.
* Local shell history includes decoy exploratory commands that guide enumeration without skipping steps.

---

## 14. Security Boundaries
* Workstation user `developer` has no sudo privileges.
* `/opt/production` is mode `0700` owned by user `prod`.
* `/opt/production/flag.txt` is mode `0400` owned by user `prod`.
* No Docker socket, no K8s service account token, no host filesystem access.
* Only TCP/22 exposed externally.

---

## 15. Resource Requirements
* CPU: 100m requests, 1000m limits.
* Memory: 128Mi requests, 512Mi limits.
* Storage: Ephemeral container root.

---

## 16. Validation Results
* Clean room solve: PASS
* Boundary check: PASS
* Package hygiene: PASS
