"""
broadcaster.py — broadcasts an AES-256-CBC encrypted vault password
in the SSH pre-login banner. The player must decrypt this code
to obtain the current password.
"""

import os
import secrets
import socket
import threading
import time

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend

PASS_FILE = "/tmp/current_vault_pass"
KEY = b"C7F_3ncrypt10n_K3y_N3v3r_G3u3s3d"  # 32 bytes AES-256 key
# VAULT_PASSWORD rotates and is encrypted before being broadcast

clients = []
clients_lock = threading.Lock()


def write_password_atomic(path: str, value: str) -> None:
    """Atomic write so a reader (vault_auth.py) never sees a half-written file."""
    tmp_path = path + ".tmp"
    with open(tmp_path, "w") as f:
        f.write(value + "\n")
    os.chmod(tmp_path, 0o600)
    os.replace(tmp_path, path)  # atomic on Linux


def encrypt_payload(plaintext: str) -> bytes:
    iv = secrets.token_bytes(16)
    cipher = Cipher(algorithms.AES(KEY), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    padder = padding.PKCS7(128).padder()
    padded = padder.update(plaintext.encode()) + padder.finalize()
    ct = encryptor.update(padded) + encryptor.finalize()
    return iv + ct


def broadcast(line: str) -> None:
    with clients_lock:
        dead = []
        for conn in clients:
            try:
                conn.sendall((line + "\n").encode())
            except OSError:
                dead.append(conn)
        for conn in dead:
            clients.remove(conn)


def broadcast_loop() -> None:
    while True:
        write_password_atomic(PASS_FILE, VAULT_PASSWORD)
        payload = encrypt_payload(VAULT_PASSWORD).hex()
        broadcast(f"ENCRYPTED_VAULT_CODE:{payload}")
        time.sleep(BROADCAST_INTERVAL)


def handle_client(conn: socket.socket) -> None:
    with clients_lock:
        clients.append(conn)
    try:
        # send password immediately on connect
        write_password_atomic(PASS_FILE, VAULT_PASSWORD)
        payload = encrypt_payload(VAULT_PASSWORD).hex()
        conn.sendall(f"ENCRYPTED_VAULT_CODE:{payload}\n".encode())
        # keep connection open to receive future broadcasts
        while True:
            data = conn.recv(1024)
            if not data:
                break
    except OSError:
        pass
    finally:
        with clients_lock:
            if conn in clients:
                clients.remove(conn)
        conn.close()


def server_loop() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen(5)
        print(f"[broadcaster] Listening on {HOST}:{PORT}")
        while True:
            conn, _addr = s.accept()
            threading.Thread(target=handle_client, args=(conn,), daemon=True).start()


def main() -> None:
    write_password_atomic(PASS_FILE, VAULT_PASSWORD)
    threading.Thread(target=broadcast_loop, daemon=True).start()
    server_loop()


if __name__ == "__main__":
    main()
