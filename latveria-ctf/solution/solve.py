#!/usr/bin/env python3
"""
solve.py — Automated Solver for Challenge 15: Latveria CTF (Pre-Destruct Containment Cycle)
"""
import re
import sys
import time
import pexpect

def solve(host="127.0.0.1", port=2225, user="latverian_conscript", password="doom_rules_all"):
    print(f"[*] Connecting to {host}:{port} as {user}...")
    child = pexpect.spawn(
        f"ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p {port} {user}@{host}",
        timeout=25
    )
    child.expect("password:")
    child.sendline(password)
    child.expect(r"latverian_conscript@[a-zA-Z0-9]+:[^#\$]*[\$#]")
    print("[+] SSH login successful!")

    # 1. Recover override protocol token from /tmp/doombot_ai.conf
    print("[*] Inspecting /tmp/doombot_ai.conf...")
    child.sendline("cat /tmp/doombot_ai.conf")
    child.expect(r"latverian_conscript@[a-zA-Z0-9]+:[^#\$]*[\$#]")
    conf_out = child.before.decode(errors="ignore")

    match = re.search(r"AUTH_DOOM_OVERRIDE_STAGE[0-9]+", conf_out)
    override_token = match.group(0) if match else "AUTH_DOOM_OVERRIDE_STAGE4"
    print(f"[+] Recovered failsafe override token: {override_token}")

    # 2. Sabotage the Doombot daemon
    print("[*] Sabotaging Doombot daemon by corrupting heartbeat configuration...")
    child.sendline('echo "HEARTBEAT_INTERVAL=corrupted" > /tmp/doombot_ai.conf')
    child.expect(r"latverian_conscript@[a-zA-Z0-9]+:[^#\$]*[\$#]")

    print("[*] Waiting 6 seconds for watchdog to register Doombot death...")
    time.sleep(6)

    # 3. Query the internal failsafe daemon on port 9999
    print("[*] Querying Failsafe Listener on 127.0.0.1:9999...")
    child.sendline(f'echo "{override_token}" | nc 127.0.0.1 9999')
    child.expect(r"latverian_conscript@[a-zA-Z0-9]+:[^#\$]*[\$#]")
    nc_out = child.before.decode(errors="ignore")

    key_match = re.search(r"Master Authorization Key:\s*([0-9a-fA-F]+)", nc_out)
    if not key_match:
        print("[-] Failed to retrieve Master Authorization Key from failsafe daemon.")
        child.sendline("exit")
        sys.exit(1)

    master_key = key_match.group(1).strip()
    print(f"[+] Master Authorization Key obtained: {master_key}")

    # 4. Execute SUID repair binary
    print(f"[*] Executing /usr/sbin/latveria-repair-seq {master_key}...")
    child.sendline(f"/usr/sbin/latveria-repair-seq {master_key}")
    child.expect("Enter recovered core signature to confirm systems nominal:")
    dump_out = child.before.decode(errors="ignore")

    hex_parts = re.findall(r"\\x([0-9a-fA-F]{2})", dump_out)
    raw_hex = "".join(hex_parts)
    flag = bytes.fromhex(raw_hex).decode("utf-8", errors="ignore").strip()
    print(f"[+] Decoded Core Signature (Flag): {flag}")

    # 5. Confirm recovery signature
    print("[*] Submitting signature to disarm containment revert sequence...")
    child.sendline(flag)
    child.expect(r"latverian_conscript@[a-zA-Z0-9]+:[^#\$]*[\$#]", timeout=15)
    result_out = child.before.decode(errors="ignore")

    if "Sequence complete" in result_out:
        print(f"[+] CONTAINMENT DISARMED! FINAL FLAG: {flag}")
        child.sendline("exit")
        return flag
    else:
        print("[-] Sequence confirmation failed.")
        child.sendline("exit")
        sys.exit(1)

if __name__ == "__main__":
    solve()
