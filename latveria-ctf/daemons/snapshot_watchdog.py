#!/usr/bin/env python3
"""
Snapshot Watchdog (runs as root). Sole authority over the countdown clock
and the only writer of /run/latveria/display.

- Polls Doombot heartbeat freshness. On death (heartbeat stale > 5s),
  flips doombot_alive=false and starts a 900s (15 min) countdown.
- Serves /run/latveria/ctl.sock (0600 root:root, unix domain socket) for
  three commands, handled single-threaded to avoid any read-modify-write
  race between concurrent player sessions. Protocol is "pessimistic
  penalty with refund" so that killing the SUID client mid-attempt can
  never dodge the 60s cost of a wrong guess, while a *correct* guess pays
  nothing:
    BEGIN    -> subtract 60s immediately (assume the worst), before the
                client has even evaluated the guess
    REFUND   -> add the 60s back (client sends this only after confirming
                the guess was actually correct)
    DISARM   -> stop the countdown permanently, mark solved
  Only a process with effective uid 0 can ever connect to this socket
  (enforced by filesystem permissions on the socket path), so only the
  SUID repair binary -- never the player directly -- can reach it.
- On remaining_seconds hitting 0 without a DISARM: kills the player's
  session and exits, which brings the container down (the platform is
  expected to reprovision a fresh instance for a restart).
"""
import json
import os
import socket
import subprocess
import threading
import time

DISPLAY_PATH = "/run/latveria/display"
HEARTBEAT_FILE = "/run/latveria/heartbeat"
CTL_SOCK = "/run/latveria/ctl.sock"
COUNTDOWN_SECONDS = 900          # 15 minutes
HEARTBEAT_STALE_AFTER = 5        # seconds without a beat = Doombot is dead

_lock = threading.Lock()
state = {"doombot_alive": True, "remaining_seconds": COUNTDOWN_SECONDS, "solved": False}


def write_display():
    tmp = DISPLAY_PATH + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f)
    os.replace(tmp, DISPLAY_PATH)   # atomic on same filesystem
    os.chmod(DISPLAY_PATH, 0o644)


def heartbeat_is_stale():
    try:
        mtime = os.path.getmtime(HEARTBEAT_FILE)
    except FileNotFoundError:
        return True
    return (time.time() - mtime) > HEARTBEAT_STALE_AFTER


def trigger_revert_and_die():
    print("[WATCHDOG] Countdown expired. Reverting to last snapshot.", flush=True)
    # Best-effort: broadcast to any attached tty, then bring the whole
    # container down so the platform reprovisions a clean instance.
    try:
        subprocess.run(["wall", "[BROADCAST] Snapshot revert executing. Session terminated."],
                        timeout=2)
    except Exception:
        pass
    os._exit(1)


def clock_loop():
    global state
    while True:
        time.sleep(1)
        with _lock:
            if state["solved"]:
                continue
            if not state["doombot_alive"]:
                if heartbeat_is_stale() is False:
                    # shouldn't happen once dead, but guard anyway
                    pass
                state["remaining_seconds"] -= 1
                if state["remaining_seconds"] <= 0:
                    state["remaining_seconds"] = 0
                    write_display()
                    trigger_revert_and_die()
            else:
                if heartbeat_is_stale():
                    state["doombot_alive"] = False
                    print("[WATCHDOG] Doombot heartbeat lost. Countdown started.", flush=True)
            write_display()


def handle_ctl_conn(conn):
    global state
    try:
        data = conn.recv(64).decode("utf-8", errors="replace").strip()
    except Exception:
        conn.close()
        return

    with _lock:
        if data == "BEGIN":
            if not state["solved"]:
                state["remaining_seconds"] = max(0, state["remaining_seconds"] - 60)
            write_display()
            conn.sendall(json.dumps({"remaining_seconds": state["remaining_seconds"]}).encode())
            if state["remaining_seconds"] <= 0 and not state["solved"]:
                conn.close()
                trigger_revert_and_die()
        elif data == "REFUND":
            if not state["solved"]:
                state["remaining_seconds"] = min(COUNTDOWN_SECONDS, state["remaining_seconds"] + 60)
            write_display()
            conn.sendall(b'{"ok": true}')
        elif data == "DISARM":
            state["solved"] = True
            write_display()
            print("[WATCHDOG] DISARM received. Challenge solved. Countdown halted.", flush=True)
            conn.sendall(b'{"ok": true}')
        else:
            conn.sendall(b'{"error": "unknown command"}')
    conn.close()


def ctl_server():
    if os.path.exists(CTL_SOCK):
        os.remove(CTL_SOCK)
    srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    srv.bind(CTL_SOCK)
    os.chmod(CTL_SOCK, 0o600)   # root:root, unreachable to uid 1000
    srv.listen(8)
    while True:
        conn, _ = srv.accept()
        # handled synchronously/single-threaded on purpose: no race
        # between concurrent PENALTY/DISARM requests
        handle_ctl_conn(conn)


def main():
    os.makedirs("/run/latveria", exist_ok=True)
    write_display()
    t = threading.Thread(target=clock_loop, daemon=True)
    t.start()
    ctl_server()   # blocks forever


if __name__ == "__main__":
    main()
