# D31 – Shadow Cron
================================================================================
Category:   Linux / Cron / Privilege Escalation
Difficulty: Intermediate
Interface:  SSH (TCP/22)

MISSION BRIEFING:
A Latverian border telemetry relay node (relay-node-epsilon) was left in a
degraded operational state after an emergency maintenance patch. An unprivileged
operator account has persistent SSH access to the node.

Internal audit notes hint that the automated maintenance scheduler is running
routine health-check scripts under elevated authority — and that the script
permissions were left too broad during the last emergency patch cycle.

Your mission: investigate the node's scheduled maintenance jobs, identify the
permission oversight, and leverage it to extract the sovereign defense relay key.

INSTRUCTIONS:
1. Connect to the relay node terminal via SSH.
2. Investigate the active cron scheduler configuration.
3. Identify the maintenance script being executed automatically under root.
4. Exploit the misconfigured script permissions to escalate your privilege.
5. Recover the classified defense key in format YUVA{...}.

CONNECTION DETAILS:
- SSH:      ssh operator@<TARGET_IP> -p <PORT>
- Username: operator
- Password: operator

RULES & GUIDANCE:
1. All interactions take place exclusively through the SSH interface on TCP/22.
2. The entire attack chain is isolated within the synthetic challenge environment.
3. No external network connectivity is required or available.
================================================================================
