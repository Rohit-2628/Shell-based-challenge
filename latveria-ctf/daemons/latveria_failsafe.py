#!/usr/bin/env python3
"""
Latveria Failsafe Listener (runs as root).

Binds 127.0.0.1:9999. While the Doombot is alive, refuses connections with
a generic "containment nominal" message. Only once the Doombot has died
(as reported by the shared display file, which is non-secret) does it
accept the override auth string and, on a correct match, reply with the
instance's Master Key -- read at request time from the root-only
/etc/latveria/failsafe.conf, never held hardcoded or in argv/environ.
"""
import json
import socket
import threading

DISPLAY_PATH = "/run/latveria/display"
FAILSAFE_CONF = "/etc/latveria/failsafe.conf"
OVERRIDE_AUTH = "AUTH_DOOM_OVERRIDE_STAGE4"


def doombot_alive():
    try:
        with open(DISPLAY_PATH) as f:
            return json.load(f).get("doombot_alive", True)
    except Exception:
        # fail safe: if we can't read state, assume still alive (don't
        # leak the key on an error condition)
        return True


def read_master_key():
    with open(FAILSAFE_CONF) as f:
        for line in f:
            line = line.strip()
            if line.startswith("MASTER_KEY="):
                return line.split("=", 1)[1].strip()
    return None


def handle(conn, addr):
    with conn:
        try:
            data = conn.recv(256).decode("utf-8", errors="replace").strip()
        except Exception:
            return

        if doombot_alive():
            conn.sendall(b"[FAILSAFE] Containment nominal. No override accepted.\n")
            return

        if data == OVERRIDE_AUTH:
            key = read_master_key()
            if key:
                conn.sendall(
                    f"[+] Heartbeat bypass validated. Master Authorization Key: {key}\n".encode()
                )
            else:
                conn.sendall(b"[FAILSAFE] Internal error retrieving key.\n")
        else:
            conn.sendall(b"[FAILSAFE] Invalid override sequence.\n")


def main():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", 9999))
    srv.listen(8)
    while True:
        conn, addr = srv.accept()
        threading.Thread(target=handle, args=(conn, addr), daemon=True).start()


if __name__ == "__main__":
    main()
