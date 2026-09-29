#!/usr/bin/env python3
import socket
import sys
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding

def get_ssh_password(host="127.0.0.1", port=9001):
    KEY = b"C7F_3ncrypt10n_K3y_N3v3r_G3u3s3d"
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    data = s.recv(1024).decode().strip()
    s.close()

    prefix, hex_data = data.split(":", 1)
    raw_bytes = bytes.fromhex(hex_data)
    iv = raw_bytes[:16]
    ct = raw_bytes[16:]

    cipher = Cipher(algorithms.AES(KEY), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded = decryptor.update(ct) + decryptor.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    password = (unpadder.update(padded) + unpadder.finalize()).decode()
    return password

if __name__ == "__main__":
    pwd = get_ssh_password()
    print("[+] Decrypted SSH Password:", pwd)
