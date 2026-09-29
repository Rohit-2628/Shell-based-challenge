#!/usr/bin/env python3
"""
solve.py — Automated Solver for Challenge 14: Naval C2
"""
import re
import sys
import time
import pexpect

def solve(host="127.0.0.1", port=2226, user="player", password="ctf_password"):
    print(f"[*] Connecting to {host}:{port} as {user}...")
    child = pexpect.spawn(
        f"ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p {port} {user}@{host}",
        timeout=25
    )
    child.expect("password:")
    child.sendline(password)
    child.expect(r"player@[a-zA-Z0-9]+:[^#\$]*[\$#]")
    print("[+] SSH login successful!")

    # 1. Terminate rogue backdoor daemon on port 2375
    print("[*] Terminating Cobalt Mirage backdoor daemon on port 2375...")
    child.sendline('sudo /usr/bin/pkill -9 -f "dockerd.*2375"')
    child.expect(r"player@[a-zA-Z0-9]+:[^#\$]*[\$#]")

    # 2. Repair missile guidance docker socket mount
    print("[*] Repairing Docker socket mount in docker-compose.yml...")
    child.sendline("sed -i 's/wrong.sock/docker.sock/g' /home/player/docker-compose.yml")
    child.expect(r"player@[a-zA-Z0-9]+:[^#\$]*[\$#]")

    # 3. Recreate web-c2 container
    print("[*] Recreating and starting Web C2 container...")
    child.sendline("cd /home/player && docker-compose down && docker-compose up -d")
    child.expect(r"player@[a-zA-Z0-9]+:[^#\$]*[\$#]", timeout=30)

    # 4. Verify health endpoint
    print("[*] Verifying health endpoint...")
    for _ in range(10):
        time.sleep(1)
        child.sendline("curl -s http://localhost:8080/health")
        child.expect(r"player@[a-zA-Z0-9]+:[^#\$]*[\$#]")
        health_resp = child.before.decode(errors="ignore")
        if "ONLINE" in health_resp:
            print("[+] Web C2 dashboard is ONLINE!")
            break

    # 5. Execute emergency override script
    print("[*] Executing Emergency Override protocol (/opt/c2/override.sh)...")
    child.sendline("/opt/c2/override.sh")
    child.expect(r"player@[a-zA-Z0-9]+:[^#\$]*[\$#]", timeout=30)
    override_output = child.before.decode(errors="ignore")

    match = re.search(r"(YUVA\{[^}]+\})", override_output)
    if match:
        flag = match.group(1)
        print(f"[+] OVERRIDE SUCCESS! RECOVERED FLAG: {flag}")
        child.sendline("exit")
        return flag
    else:
        print("[-] Override execution did not yield flag. Output:")
        print(override_output)
        child.sendline("exit")
        sys.exit(1)

if __name__ == "__main__":
    solve()
