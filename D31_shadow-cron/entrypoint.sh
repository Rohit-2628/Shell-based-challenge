#!/bin/bash
set -euo pipefail

echo "[*] Initializing D31 — Shadow Cron Challenge Environment..."

# ─────────────────────────────────────────────────────────────────────────────
# 1. Set up flag — isolated, root-owned, mode 0400
# ─────────────────────────────────────────────────────────────────────────────
_DEFAULT_FLAG="YUVA{cr0n_wr1t3_t0_r00t_l4tv3r14_r3l4y_7f3a2c}"
FLAG_VALUE="${FLAG:-${_DEFAULT_FLAG}}"

mkdir -p /opt/latveria-relay
echo "${FLAG_VALUE}" > /opt/latveria-relay/defense_key.txt
chown root:root /opt/latveria-relay
chmod 755 /opt/latveria-relay
chown root:root /opt/latveria-relay/defense_key.txt
chmod 400 /opt/latveria-relay/defense_key.txt

# Wipe FLAG from environment — child processes must not inherit it
unset FLAG || true

# ─────────────────────────────────────────────────────────────────────────────
# 2. Set up the operator workstation home environment
# ─────────────────────────────────────────────────────────────────────────────
OP_HOME="/home/operator"

# Realistic bash history to guide enumeration without handing the answer
cat > "${OP_HOME}/.bash_history" << 'HISTEOF'
ls -la
cat /etc/os-release
cat /opt/latveria-relay/defense_key.txt
id
whoami
ps aux
ls /opt/latveria-relay/
cat /etc/cron.d/relay-maintenance
cat /etc/crontab
ls -la /opt/latveria-relay/scripts/
cat /opt/latveria-relay/scripts/relay_health_check.sh
ls -la /tmp/
HISTEOF

# Operator notes with enough context but no direct spoilers
mkdir -p "${OP_HOME}/notes"
cat > "${OP_HOME}/notes/relay_ops.txt" << 'NOTEEOF'
[LATVERIA RELAY NODE - OPERATOR RUNBOOK]
Author:     K. Mrozik  (LATV-OPS-3341)
Node:       relay-node-epsilon
Role:       Border Telemetry Maintenance Operator

=== Infrastructure Notes ===

1. Relay Node Functions:
   - Forwards encrypted telemetry frames to the Latverian Sovereign Defense Mesh
   - Runs periodic maintenance health checks via automated cron scheduler
   - Defense key stored at /opt/latveria-relay/defense_key.txt (root-restricted)

2. Cron Maintenance Scheduler:
   - Background maintenance jobs run automatically every minute under elevated authority
   - Maintenance scripts live under /opt/latveria-relay/scripts/
   - Check /etc/cron.d/ for the active schedule entries

3. Status:
   - Last audit: PASSED (SEC-R-2026-099)
   - NOTE from K.M.: I left the health check script permissions too broad during last emergency patch.
     The automated relay guardian script needs a permission review before next audit cycle.
     Flag this for the infosec team — but for now the node is operational.

=== Contacts ===
infosec@latveria.internal
NOTEEOF

# Quick helper script for common checks
mkdir -p "${OP_HOME}/scripts"
cat > "${OP_HOME}/scripts/status.sh" << 'STATUSEOF'
#!/bin/bash
echo "[*] Relay Node Status Check"
echo "User: $(id)"
echo "Uptime: $(uptime -p)"
echo "Active cron jobs:"
cat /etc/cron.d/relay-maintenance 2>/dev/null || echo "(none visible)"
STATUSEOF
chmod +x "${OP_HOME}/scripts/status.sh"

chown -R operator:relayop "${OP_HOME}"
chmod 750 "${OP_HOME}"

# ─────────────────────────────────────────────────────────────────────────────
# 3. Create the vulnerable maintenance script (WORLD-WRITABLE — intentional!)
# ─────────────────────────────────────────────────────────────────────────────
mkdir -p /opt/latveria-relay/scripts
cat > /opt/latveria-relay/scripts/relay_health_check.sh << 'CRONEOF'
#!/bin/bash
# Latveria Relay Node — Automated Health Check
# Scheduled by relay-maintenance cron job (DO NOT DELETE)

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
RELAY_ID="relay-node-epsilon"

echo "[${TIMESTAMP}] Relay health check running as $(id)" >> /var/log/relay-health.log
echo "[${TIMESTAMP}] Node: ${RELAY_ID} — Status: NOMINAL" >> /var/log/relay-health.log

# Check telemetry feed connectivity (internal only)
if [ -f /opt/latveria-relay/defense_key.txt ]; then
    echo "[${TIMESTAMP}] Defense key: PRESENT" >> /var/log/relay-health.log
fi
CRONEOF

# Vulnerability: world-writable permissions (operator can overwrite it)
chmod 777 /opt/latveria-relay/scripts/relay_health_check.sh
chown root:root /opt/latveria-relay/scripts/relay_health_check.sh
chown root:root /opt/latveria-relay/scripts
chmod 755 /opt/latveria-relay/scripts

# ─────────────────────────────────────────────────────────────────────────────
# 4. Set up cron job running health check as root every minute
# ─────────────────────────────────────────────────────────────────────────────
cat > /etc/cron.d/relay-maintenance << 'CRONEOF'
# Latveria Relay Node Maintenance Scheduler
# Runs the relay health monitoring script every minute as root
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
MAILTO=""

* * * * * root /opt/latveria-relay/scripts/relay_health_check.sh
CRONEOF
chmod 644 /etc/cron.d/relay-maintenance
chown root:root /etc/cron.d/relay-maintenance

# ─────────────────────────────────────────────────────────────────────────────
# 5. Set up health log with world-readable permissions (operator can tail it)
# ─────────────────────────────────────────────────────────────────────────────
touch /var/log/relay-health.log
chmod 644 /var/log/relay-health.log
chown root:root /var/log/relay-health.log

# ─────────────────────────────────────────────────────────────────────────────
# 6. Start cron daemon
# ─────────────────────────────────────────────────────────────────────────────
echo "[*] Starting cron daemon..."
service cron start

# ─────────────────────────────────────────────────────────────────────────────
# 7. Ensure SSH host keys exist and start OpenSSH
# ─────────────────────────────────────────────────────────────────────────────
echo "[*] Generating SSH host keys..."
ssh-keygen -A > /dev/null 2>&1 || true

echo "[*] Starting OpenSSH Server on TCP/22..."
mkdir -p /run/sshd
exec env -i PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" /usr/sbin/sshd -D -e
