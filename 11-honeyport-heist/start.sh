#!/bin/bash

# Dynamic Credentials & Flag
DYNAMIC_PASS=${CTF_PASSWORD:-"player"}
echo "ctf_player:$DYNAMIC_PASS" | chpasswd

if [ -z "$FLAG" ]; then
    FLAG="YUVA{gh0st_1n_th3_m4ch1n3_d3f34t3d}"
fi
export FLAG

# Prepare shared directories
mkdir -p /auth_sync /tmp_sock /run/sshd
chmod 777 /auth_sync /tmp_sock
rm -f /tmp_sock/.sys.sock

# 1. Start Vault A API in the background
python3 /opt/container_a/server_a.py &

# 2. Start Vault C API bound to unix socket
cd /opt/container_c && gunicorn --bind unix:/tmp_sock/.sys.sock --umask 000 app:app &

# 3. Start the Ghost Bot Engine in the background
python3 /opt/container_bot/start_bots.py &

# Wait for socket initialization
sleep 2
chmod 777 /tmp_sock/.sys.sock 2>/dev/null || true

# 4. Start the SSH Server in the foreground
exec /usr/sbin/sshd -D
