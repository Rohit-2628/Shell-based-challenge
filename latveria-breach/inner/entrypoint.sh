#!/bin/bash
CURRENT_FLAG=${FLAG:-"YUVA{d00ms_wr4th_4v01d3d}"}
CURRENT_PASS=${SSH_PASS:-"survive"}

echo "intruder:$CURRENT_PASS" | chpasswd

# Real flag - only readable by root, must be escalated to
echo "$CURRENT_FLAG" > /root/flag.txt
chmod 600 /root/flag.txt

# Hash only, so low-priv abort_destruct can verify without needing root
echo -n "$CURRENT_FLAG" | sha256sum | awk '{print $1}' > /etc/.doom_secret
chmod 444 /etc/.doom_secret

# Boot sequence + Latverian flag banner, shown once per interactive login.
# The banner is algorithmically constructed ANSI art (assets/login_banner.ansi)
# - built from shapes/color logic, not converted from any photo.
cat > /etc/profile.d/00-latveria.sh << 'PROFILEEOF'
if [ -n "$PS1" ] && [ -z "$LATVERIA_BOOT_SHOWN" ]; then
    export LATVERIA_BOOT_SHOWN=1
    GOLD="\033[38;5;178m"
    DIM="\033[2m"
    RESET="\033[0m"

    lines=(
      "CONNECTING TO REMOTE HOST..."
      "BYPASSING PERIMETER FIREWALL..."
      "INJECTING PAYLOAD... SUCCESS"
      "ACCESS GRANTED — LOW-PRIVILEGE SHELL"
    )
    for l in "${lines[@]}"; do
        echo -e "${DIM}${l}${RESET}"
        sleep 0.3
    done

    echo ""
    echo -e "${GOLD}TARGET IDENTIFIED: LATVERIAN STATE NETWORK${RESET}"
    echo ""

    cat /opt/latveria_assets/login_banner.ansi
    echo ""
fi
PROFILEEOF
chmod 755 /etc/profile.d/00-latveria.sh

/usr/sbin/sshd

# Root-owned defense grid watchdog - the intruder cannot signal this
# process until they've actually escalated privileges.
/usr/local/sbin/watchdog.sh &

/usr/local/bin/broadcaster.sh &

tail -f /dev/null
