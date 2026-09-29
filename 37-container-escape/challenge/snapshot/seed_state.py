#!/usr/bin/env python3
"""
X07 Challenge State Seeder & Snapshot Initializer
Sets up the sandbox host files, container configuration, and dynamic team flag.
"""

import os
import sys
import hashlib
from pathlib import Path

def generate_flag(team_id: str) -> str:
    salt = "latveria_cgroup_isolation_2026"
    h = hashlib.sha256(f"{team_id}_{salt}".encode()).hexdigest()[:16]
    return f"YUVA{{c0nt41n3r_3sc4p3_{h}_x07}}"

def seed_host_state(flag_value: str, host_flag_path: str = "/root/flag.txt"):
    target = Path(host_flag_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(flag_value + "\n")
    try:
        os.chmod(target, 0o600)
    except Exception:
        pass
    print(f"[+] Seeded host flag at {host_flag_path}")

def main():
    team_id = sys.argv[1] if len(sys.argv) > 1 else "team_default"
    flag = generate_flag(team_id)
    print(f"[*] Generated flag for team '{team_id}'")
    
    # In sandbox VM, host flag goes to /root/flag.txt
    # In local testing environment, mock path can be passed via env
    host_flag_path = os.environ.get("HOST_FLAG_PATH", "/root/flag.txt")
    seed_host_state(flag, host_flag_path)

if __name__ == "__main__":
    main()
