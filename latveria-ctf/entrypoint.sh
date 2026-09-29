#!/bin/bash
set -e

FLAG="${FLAG:-YUVA{d00m_m4st3r_c0nt41nm3nt_s3qu3nc3_d1s4rm3d_2026}}"

# 1. Generate a unique 16-byte Master Key for this instance.
INSTANCE_KEY=$(head -c 16 /dev/urandom | xxd -p)

# 2. Inject the instance key and the real flag into root-only configs.
sed -i "s/{{MASTER_KEY}}/${INSTANCE_KEY}/g" /etc/latveria/failsafe.conf
sed -i "s/{{FLAG}}/${FLAG}/g" /etc/latveria/vault.conf
chmod 600 /etc/latveria/failsafe.conf /etc/latveria/vault.conf
chown root:root /etc/latveria/failsafe.conf /etc/latveria/vault.conf

# 3. Scrub the flag from the environment so it can't be read via
#    /proc/<pid>/environ.
unset FLAG

# 4. Attempt hidepid=2. This generally requires the *host*/orchestrator to
#    grant the container permission to remount /proc; if it's not already
#    mounted with hidepid at container start, this remount will silently
#    fail under a default Docker security profile. Document this to
#    operators — see README section 5.
mount -o remount,rw,hidepid=2 /proc 2>/dev/null || \
    echo "[entrypoint] WARNING: could not remount /proc with hidepid=2; set this at the docker run / orchestrator level instead." >&2

# 5. Generate the 100 decoy vault sectors.
/usr/local/bin/gen-vaults

# 6. Initialize the shared display state (world-readable, root-owned).
cat > /run/latveria/display <<EOF
{"doombot_alive": true, "remaining_seconds": 900, "solved": false}
EOF
chmod 644 /run/latveria/display
chown root:root /run/latveria/display

# 7. Start internal daemons (all root).
/usr/local/bin/snapshot-watchdog &
/usr/local/bin/latveria-failsafe &
/usr/local/bin/doombot-daemon &

# 8. Configure SSH credentials and permissions
DYNAMIC_PASS=${CTF_PASSWORD:-"doom_rules_all"}
echo "latverian_conscript:$DYNAMIC_PASS" | chpasswd
mkdir -p /var/run/sshd /run/sshd

# Setup interactive shell hook to attach tmux if interactive TTY
cat >> /home/latverian_conscript/.bashrc <<'EOF'
if [ -t 1 ] && [ -z "$TMUX" ] && tmux has-session -t main 2>/dev/null; then
    tmux attach -t main
fi
EOF
chown latverian_conscript:latverian_conscript /home/latverian_conscript/.bashrc

# 9. Pre-seed the tmux session: pane 0 = interactive shell, pane 1 = pinned live clock ticker
su -s /bin/bash -c '
    tmux new-session -d -s main -n containment
    tmux send-keys -t main "clear; cat /etc/motd; bash --login; tmux kill-session -t main" C-m
    tmux split-window -h -t main "/usr/local/bin/clock-pane"
    tmux select-pane -t main:0.0
' latverian_conscript 2>/dev/null || true

# 10. Start the SSH Server in the foreground
exec /usr/sbin/sshd -D
