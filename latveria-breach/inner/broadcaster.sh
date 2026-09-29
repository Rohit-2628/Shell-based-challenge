#!/bin/bash
sleep 2
while true; do
    CURRENT_MIN=$(date +%M)
    ENCRYPTED=$(echo -n "doom_$CURRENT_MIN" | base64 | rev)
    echo "[$(date)] [INTERCEPTED TRANSMISSION] KEY ROTATED -> $ENCRYPTED" > /var/log/latveria_intercept.log
    sleep 10
done
