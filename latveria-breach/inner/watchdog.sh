#!/bin/bash
# Runs as root, started by entrypoint.sh. The player (pre-privesc) cannot
# signal this process since it's a different UID - this is what actually
# prevents someone from just `ps aux | kill`-ing their way past the timer.

ARM_FILE="/tmp/.armed"
END_FILE="/tmp/.destruct_end"
DISARM_ATTEMPT="/tmp/.disarm_attempt"
DISARMED_FILE="/tmp/.disarmed"
SECRET_HASH="/etc/.doom_secret"
DURATION=1200

armed=false
end_time=0

while true; do
    if [ "$armed" = false ] && [ -f "$ARM_FILE" ]; then
        armed=true
        end_time=$(( $(date +%s) + DURATION ))
        echo "$end_time" > "$END_FILE"
        chmod 644 "$END_FILE"
        # Lock the vault out now that it's served its purpose - only root
        # can do this since the binary is root-owned.
        chmod 000 /home/intruder/vault 2>/dev/null
    fi

    if [ "$armed" = true ]; then
        now=$(date +%s)

        if [ -f "$DISARM_ATTEMPT" ]; then
            # disarm_attempt contains the raw flag guess - hash it and compare
            GUESS_HASH=$(sha256sum < "$DISARM_ATTEMPT" | awk '{print $1}')
            EXPECTED_HASH=$(cat "$SECRET_HASH" 2>/dev/null)
            if [ -n "$GUESS_HASH" ] && [ "$GUESS_HASH" == "$EXPECTED_HASH" ]; then
                touch "$DISARMED_FILE"
                chmod 644 "$DISARMED_FILE"
                rm -f "$END_FILE" "$ARM_FILE" "$DISARM_ATTEMPT"
                armed=false
            else
                rm -f "$DISARM_ATTEMPT"
            fi
        fi

        if [ "$armed" = true ] && [ "$now" -ge "$end_time" ]; then
            kill -9 -1
        fi
    fi

    sleep 1
done
