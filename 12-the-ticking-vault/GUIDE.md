# 12-the-ticking-vault - Testing & Solve Guide

## 1. Challenge setup
- **Start**: `cd ctf-platform/challenges/12-the-ticking-vault && docker build -t 12-the-ticking-vault . && docker run -d --name the-ticking-vault -p 2224:22 12-the-ticking-vault`
- **Ports**: 2224 (SSH)
- **Protocol**: SSH
- **Credentials**: Username: `player` | Password: (Decrypted from SSH pre-login broadcast banner)

## 2. How to access it
```bash
# Connect to SSH (pre-login banner displays encrypted vault broadcast)
ssh player@127.0.0.1 -p 2224
```

## 3. Intended solve path
1. Connect to SSH port 2224: the pre-login banner displays `ENCRYPTED_VAULT_CODE:<HEX_DATA>`.
2. Decrypt AES-256-CBC ciphertext using key `C7F_3ncrypt10n_K3y_N3v3r_G3u3s3d` (from handout `broadcaster.py`, first 16 bytes = IV).
3. Authenticate to `player@127.0.0.1 -p 2224` with the decrypted password.
4. Exploit the misconfigured cron job in `/etc/cron.d/vault-cron` running `/opt/vault/rotate_logs.sh` (world-writable) as root.
5. Retrieve flag from `/root/flag.txt`.

## 4. Expected solution
**⚠️ SPOILER — INTENDED SOLUTION**

### Python Decryption Script
```python
import sys, re, pexpect
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding

KEY = b"C7F_3ncrypt10n_K3y_N3v3r_G3u3s3d"

# Connect via SSH to receive pre-login banner
child = pexpect.spawn("ssh -o StrictHostKeyChecking=no -p 2224 player@127.0.0.1", timeout=10)
child.expect("password:")
banner = child.before.decode(errors="ignore")

hex_data = re.search(r"ENCRYPTED_VAULT_CODE:([0-9a-fA-F]+)", banner).group(1)
raw_bytes = bytes.fromhex(hex_data)
iv = raw_bytes[:16]
ct = raw_bytes[16:]

cipher = Cipher(algorithms.AES(KEY), modes.CBC(iv), backend=default_backend())
decryptor = cipher.decryptor()
padded = decryptor.update(ct) + decryptor.finalize()
unpadder = padding.PKCS7(128).unpadder()
password = (unpadder.update(padded) + unpadder.finalize()).decode()
print("[+] Decrypted SSH Password:", password)
```

**Expected Flag**: `YUVA{t1ck1ng_v4ult_c0r3_s3cur1ty_d3fus3d_9842}`
