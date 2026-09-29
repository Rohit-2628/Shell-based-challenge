#!/usr/bin/env python3
"""
Doombot Daemon (runs as root).

Responsibilities:
  - Every 2s, shuffle decoy keys across /vaults/sector_001..100/.
  - Every N seconds (read from /tmp/doombot_ai.conf, WORLD-WRITABLE by
    design), send a heartbeat pulse to the Failsafe Listener by touching
    a heartbeat file it watches.
  - If /tmp/doombot_ai.conf is corrupted (non-numeric interval, missing
    key, etc.) this process raises an unhandled exception and dies -- this
    is the intended sabotage vector. We deliberately do NOT wrap the
    config parse in a broad try/except, because the whole point of the
    challenge is that a corrupted config kills the daemon.
"""
import hashlib
import os
import random
import time

CONF_PATH = "/tmp/doombot_ai.conf"
VAULT_ROOT = "/vaults"
HEARTBEAT_FILE = "/run/latveria/heartbeat"


def read_interval():
    """Reads HEARTBEAT_INTERVAL=<seconds> from the world-writable config.
    Deliberately fragile: no error handling here. A corrupted or
    non-numeric value raises, killing the process -- exactly the sabotage
    path the challenge wants to exist."""
    with open(CONF_PATH) as f:
        for line in f:
            line = line.strip()
            if line.startswith("HEARTBEAT_INTERVAL="):
                value = line.split("=", 1)[1].strip()
                # int() on a corrupted value (empty, letters, etc.) raises
                # ValueError here, which is unhandled -> process exits.
                return int(value)
    # Missing key entirely also blows up the daemon (unhandled) rather
    # than silently defaulting -- another valid sabotage path (deleting
    # the line, truncating the file, etc.)
    raise RuntimeError("HEARTBEAT_INTERVAL missing from config")


def rotate_decoys():
    for i in range(1, 101):
        sector = os.path.join(VAULT_ROOT, f"sector_{i:03d}")
        os.makedirs(sector, exist_ok=True)
        junk = hashlib.md5(str(random.randint(0, 10**9)).encode()).hexdigest()
        with open(os.path.join(sector, "active_key.txt"), "w") as f:
            f.write(f"DOOM_DECOY_{junk}\n")


def beat():
    with open(HEARTBEAT_FILE, "w") as f:
        f.write(str(time.time()))


def main():
    os.makedirs("/run/latveria", exist_ok=True)
    last_rotate = 0
    while True:
        interval = read_interval()   # will raise & kill process if corrupted
        beat()
        now = time.time()
        if now - last_rotate >= 2:
            rotate_decoys()
            last_rotate = now
        time.sleep(interval)


if __name__ == "__main__":
    main()
