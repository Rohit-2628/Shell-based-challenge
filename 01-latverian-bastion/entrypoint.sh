#!/bin/bash
set -e

# Dynamic flag handling with static fallback
DEFAULT_FLAG="YUVA{d00m_d03s_n0t_t0l3r4t3_1ntrud3rs_7491}"
CHALLENGE_FLAG="${FLAG:-$DEFAULT_FLAG}"

# Place the flag securely
echo "$CHALLENGE_FLAG" > /flag.txt
echo "$CHALLENGE_FLAG" > /root/flag.txt
chmod 400 /flag.txt /root/flag.txt
chown root:root /flag.txt /root/flag.txt

# Reset the telemetry spool directory
mkdir -p /var/log/latveria/telemetry
rm -rf /var/log/latveria/telemetry/*
echo "[$(date)] Sensor status nominal. No Richards intrusions detected." > /var/log/latveria/telemetry/sensor_01.log
echo "[$(date)] Defense perimeter active." > /var/log/latveria/telemetry/perimeter.log
chown -R root:guard /var/log/latveria/telemetry
chmod 775 /var/log/latveria/telemetry
chown root:root /usr/local/bin/doom-monitor
chmod 4755 /usr/local/bin/doom-monitor

echo "[+] Latverian Bastion initialized. Starting SSH daemon on port 2222..."
exec /usr/sbin/sshd -D -e
