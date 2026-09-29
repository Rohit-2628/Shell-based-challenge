#!/bin/bash
# Read-only ticker for the pinned tmux pane. Reads only the world-readable
# /run/latveria/display (0644 root:root) -- never touches the control
# socket or any 0600 config. This is purely informational for the player.
DISPLAY_FILE="/run/latveria/display"

while true; do
    clear
    echo "=== LATVERIA CONTAINMENT STATUS ==="
    echo
    if [ -r "$DISPLAY_FILE" ]; then
        content=$(cat "$DISPLAY_FILE" 2>/dev/null)
        alive=$(echo "$content" | grep -o '"doombot_alive": *[a-z]*' | grep -o '[a-z]*$')
        remaining=$(echo "$content" | grep -o '"remaining_seconds": *[0-9]*' | grep -o '[0-9]*$')
        solved=$(echo "$content" | grep -o '"solved": *[a-z]*' | grep -o '[a-z]*$')

        if [ "$alive" = "true" ]; then
            echo "Doombot Status : ACTIVE (containment stable)"
            echo "Countdown      : --:-- (not yet started)"
        else
            mins=$((remaining / 60))
            secs=$((remaining % 60))
            printf "Doombot Status : OFFLINE\n"
            printf "Countdown      : %02d:%02d until snapshot revert\n" "$mins" "$secs"
        fi

        if [ "$solved" = "true" ]; then
            echo
            echo ">>> SYSTEMS VERIFIED ONLINE. REVERT CANCELLED. <<<"
        fi
    else
        echo "Status unavailable."
    fi
    echo
    echo "(this pane refreshes every second and is read-only)"
    sleep 1
done
