#!/bin/bash
# Creates /vaults/sector_001 .. sector_100 with an initial decoy key each.
# The doombot-daemon continues to rotate these every ~2s at runtime; this
# just ensures they exist and are readable before the daemon's first tick.
set -e
mkdir -p /vaults
for i in $(seq -w 1 100); do
    d="/vaults/sector_${i}"
    mkdir -p "$d"
    junk=$(head -c 16 /dev/urandom | md5sum | cut -d' ' -f1)
    echo "DOOM_DECOY_${junk}" > "$d/active_key.txt"
    chmod 644 "$d/active_key.txt"
done
chmod -R a+rx /vaults
