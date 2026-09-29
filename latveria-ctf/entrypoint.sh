#!/bin/bash
set -e

if [ -z "${FLAG:-}" ]; then
    echo "FATAL: \$FLAG not set at container start." >&2
    exit 1
fi

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

# 8. Give the daemons a moment to bind sockets/files before the player
#    lands in a shell.
sleep 1

# 9. Launch the player into tmux: pane 0 = interactive shell as the
#    conscript, pane 1 = pinned live clock ticker (read-only).
su -s /bin/bash -c '
    tmux new-session -d -s main -n containment
    # pane 0: show the briefing, then hand control to a real login shell.
    # When that shell exits (player types "exit"), tear the whole tmux
    # session down so the connection cleanly closes instead of leaving
    # only the clock pane visible.
    tmux send-keys -t main "clear; cat /etc/motd; bash --login; tmux kill-session -t main" C-m
    tmux split-window -h -t main "/usr/local/bin/clock-pane"
    tmux select-pane -t main:0.0
    tmux attach -t main
' latverian_conscript
