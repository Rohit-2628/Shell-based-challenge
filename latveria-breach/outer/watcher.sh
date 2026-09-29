#!/bin/bash
# The player never reaches this container - no published ports.
sleep 5

while true; do
    CURRENT_MIN=$(date +%M)
    ENCRYPTED=$(echo -n "doom_$CURRENT_MIN" | base64 | rev)
    echo "$ENCRYPTED" > /shared/bot_broadcast.txt

    ping -c 1 inner_core > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo "INNER CORE DESTROYED. SECURING PERIMETER. TERMINATING." > /dev/console 2>/dev/null
        kill -9 -1
    fi

    sleep 10
done
