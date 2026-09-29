# 15-latveria-ctf - Testing & Solve Guide

## 1. Challenge setup
- **Start**: `cd ctf-platform/challenges/15-latveria-ctf && docker build -t 15-latveria-ctf . && docker run -d --name latveria-ctf-containment -p 2225:22 15-latveria-ctf`
- **Ports**: 2225
- **Protocol**: SSH
- **Credentials**: Username: `latverian_conscript` | Password: `doom_rules_all`

## 2. How to access it
```bash
ssh latverian_conscript@127.0.0.1 -p 2225
# (Password: doom_rules_all)
```

## 3. Intended solve path
1. SSH into the fortress node: `ssh -p 2225 latverian_conscript@127.0.0.1`.
2. Inspect `/tmp/doombot_ai.conf`. Note the comment revealing `AUTH_DOOM_OVERRIDE_STAGE4`.
3. Sabotage the Doombot:
   ```bash
   echo "HEARTBEAT_INTERVAL=corrupted" > /tmp/doombot_ai.conf
   ```
   The Doombot dies and the 15-minute countdown begins.
4. Request the Master Authorization Key from the local failsafe daemon:
   ```bash
   echo "AUTH_DOOM_OVERRIDE_STAGE4" | nc 127.0.0.1 9999
   ```
5. Run the repair sequence with the returned Master Key:
   ```bash
   /usr/sbin/latveria-repair-seq <MASTER_KEY>
   ```
6. The binary dumps the hex-encoded diagnostic core signature. Decode it and submit it to confirm systems nominal:
   ```bash
   echo -n '<HEX_SIGNATURE>' | xxd -r -p
   ```
7. On verification, the countdown disarms and the sector is secured.

**Expected Flag**: `YUVA{d00m_m4st3r_c0nt41nm3nt_s3qu3nc3_d1s4rm3d_2026}`
