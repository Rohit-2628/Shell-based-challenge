# 14-naval-c2 - Testing & Solve Guide

## 1. Challenge setup
- **Start**: `cd ctf-platform/challenges/14-naval-c2 && docker build -t 14-naval-c2 . && docker run -d --privileged --name naval-c2-node -p 2226:22 14-naval-c2`
- **Ports**: 2226
- **Protocol**: SSH
- **Credentials**: Username: `player` | Password: `ctf_password`

## 2. How to access it
```bash
ssh player@127.0.0.1 -p 2226
```

## 3. Intended solve path
1. SSH into the node: `ssh -p 2226 player@127.0.0.1` (Password: `ctf_password`).
2. Identify rogue backdoor daemon listening on `0.0.0.0:2375`:
   ```bash
   ps aux | grep dockerd
   pkill -f "dockerd.*2375"
   ```
3. Fix missile guidance Docker Compose configuration in `/home/player/player_files/docker-compose.yml`:
   - Replace `/var/run/docker.sock:/var/run/wrong.sock` with `/var/run/docker.sock:/var/run/docker.sock`
4. Start the service:
   ```bash
   cd /home/player/player_files && docker-compose up -d
   ```
5. Verify health: `curl http://localhost:8080/health`
6. Execute emergency override:
   ```bash
   /opt/c2/override.sh
   ```

**Expected Flag**: `YUVA{d3f3ns1v3_ch1_d3ad10ck_d3f3at3d_l4unch_9902}`
