#!/bin/bash

# --- DYNAMIC FLAG INJECTION ---
STATIC_FLAG="YUVA{d3f3ns1v3_ch1_d3ad10ck_d3f3at3d_l4unch_9902}"
FINAL_FLAG="${FLAG:-$STATIC_FLAG}"

mkdir -p /opt/c2
echo "$FINAL_FLAG" > /opt/c2/flag.txt
chmod 400 /opt/c2/flag.txt
chown root:root /opt/c2/flag.txt

# 1. Start main daemon (VFS enforced by daemon.json)
dockerd -H unix:///var/run/docker.sock > /var/log/dockerd.log 2>&1 &
sleep 5
chmod 666 /var/run/docker.sock 2>/dev/null || true

# Load offline web-c2 image into dockerd if present
if [ -f /opt/c2/web-c2.tar ]; then
    docker load -i /opt/c2/web-c2.tar > /dev/null 2>&1 || true
fi

# 2. Start the broken Web C2 dashboard
cd /home/player
docker-compose up -d > /dev/null 2>&1 || true

# 3. Start the APT Backdoor Daemon on port 2375
mkdir -p /var/lib/rogue-docker
dockerd -H tcp://0.0.0.0:2375 -H unix:///var/run/rogue.sock \
  --pidfile /var/run/rogue.pid \
  --data-root /var/lib/rogue-docker \
  --exec-root /var/run/rogue-exec \
  --bip="172.20.0.1/16" \
  --iptables=false > /var/log/rogue-dockerd.log 2>&1 &

# 4. Start SSH daemon
exec /usr/sbin/sshd -D -e
