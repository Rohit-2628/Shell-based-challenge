#!/usr/bin/env python3
import subprocess

def solve_commands():
    cmds = [
        'sudo pkill -9 -f "dockerd.*2375" || true',
        'sed -i "s/wrong.sock/docker.sock/g" /home/player/player_files/docker-compose.yml',
        'cd /home/player/player_files && docker-compose down && docker-compose up -d',
        '/opt/c2/override.sh'
    ]
    return cmds

if __name__ == '__main__':
    print("[*] Solve Commands to run inside player session:")
    for cmd in solve_commands():
        print(f"  $ {cmd}")
