#!/bin/bash
sleep 5
while true; do
    if [ -f /shared/bot_broadcast.txt ]; then
        ENCRYPTED=$(cat /shared/bot_broadcast.txt)
        echo "[$(date)] [INTERCEPTED TRANSMISSION] KEY ROTATED -> $ENCRYPTED" > /var/log/latveria_intercept.log
    fi
    sleep 30
done
