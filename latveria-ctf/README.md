# Latveria Containment Breach — Operator Manual

## 1. Story / Theme

Doctor Doom's mountain fortress has locked itself into a **Pre-Destruct
Containment Cycle**. The fortress's autonomous defense mind, the **Doombot
Daemon**, is holding the line — it heartbeats to a **Failsafe Listener** every
few seconds and keeps 100 decoy vault sectors cycling fake keys to mislead
intruders. As long as the Doombot lives, the fortress is stable and nothing
of value is reachable.

The player connects as **`latverian_conscript`**, a disposable low-privilege
grunt with shell access, dropped into the fortress's internal network.

The intended path:

1. Recon the environment — decoys, processes, ports.
2. Find and corrupt the Doombot's world-writable runtime config, killing its
   process.
3. Killing the Doombot is **permanent and irreversible** — this is not a
   "pause" the player can undo. The **Snapshot Watchdog** detects the death
   and starts a hard, unstoppable **15-minute countdown** to a full snapshot
   revert. When it hits zero, the instance is destroyed and the player must
   start completely over on a fresh instance. Nothing the player does can
   pause or pad this clock except beating it.
4. The Doombot's death also opens the only path forward: the Failsafe
   Listener now accepts a manual override string on `127.0.0.1:9999`, which
   the player must discover from residual config/comments and send via
   `netcat`. This returns the instance-unique **Master Key**.
5. The player runs the SUID root binary `latveria-repair-seq` with that key.
   It prints a garbled "emergency diagnostic dump" — a hex-encoded string —
   framed as a side effect of the authenticated dump, not as an intentional
   flag reveal.
6. The player decodes the hex to ASCII and **feeds it back in** as a
   "confirm systems nominal" input. This confirmation step is the actual
   win condition — decoding the hex alone does not solve the challenge,
   because the flag only ever exists inside this ephemeral, per-instance
   container. There's no external scoring system that remembers a dynamic
   flag once the container is gone, so the challenge itself must verify
   the answer and log success before it can be destroyed.
7. Every wrong confirmation attempt immediately docks 60 seconds off the
   clock — no separate attempt cap, just clock pressure. A correct
   confirmation immediately and permanently halts the countdown and marks
   the instance solved.

This produces two honest failure modes and one honest success mode, with no
narrative claim that's mechanically false: nothing in the fiction promises
the player they're "saving" the fortress — they're racing a fixed, hostile
clock to extract and prove a secret before an irreversible reset.

## 2. Architecture

```
                     [ Player SSH/socat : 1337 ]
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────────┐
│ Docker container (--memory=250m --pids-limit=100                      │
│                    --cap-drop=NET_RAW --cap-drop=KILL)                │
│                                                                        │
│  latverian_conscript (uid 1000) lands in tmux:                        │
│    ┌─────────────────────────┬──────────────────────────────────┐    │
│    │ pane 0: interactive     │ pane 1: live clock (read-only,    │    │
│    │ shell                   │ refreshes every 1s from           │    │
│    │                         │ /run/latveria/display)            │    │
│    └─────────────────────────┴──────────────────────────────────┘    │
│                                                                        │
│  doombot-daemon.py (uid 0)                                            │
│    - rotates decoy keys in /vaults/sector_001..100/                   │
│    - reads /tmp/doombot_ai.conf (WORLD-WRITABLE — the sabotage point) │
│    - heartbeats over a local pipe/state check every 2s                │
│    - crashes if its config is corrupted (unhandled parse failure)     │
│                                                                        │
│  latveria-failsafe.py (uid 0)                                         │
│    - binds 127.0.0.1:9999                                             │
│    - refuses connections while Doombot is alive                       │
│    - once Doombot is dead: accepts the override auth string once,     │
│      replies with the instance's Master Key                           │
│                                                                        │
│  snapshot-watchdog.py (uid 0)  ← sole authority over the clock         │
│    - polls Doombot liveness                                           │
│    - on death: starts 900s countdown, writes /run/latveria/display    │
│      (0644, root:root — world READABLE only) once per second          │
│    - listens on /run/latveria/ctl.sock (0600, root:root — reachable   │
│      only by processes with effective uid 0)                          │
│      • "PENALTY" → -60s, applied immediately                          │
│      • "DISARM"  → stop timer, mark solved, log success               │
│    - on remaining_seconds <= 0: terminates the player's session and   │
│      the container exits (platform reprovisions a fresh instance)     │
│                                                                        │
│  /usr/sbin/latveria-repair-seq (SUID root, 4755, owned root:root,     │
│  executable but NOT readable/writable by latverian_conscript)         │
│    - rejects if Doombot is still alive                                │
│    - validates the supplied Master Key against                        │
│      /etc/latveria/failsafe.conf (0600 root:root) — constant-time     │
│    - on success: prints the hex-encoded flag, then reads one line of  │
│      "confirmation" input                                             │
│    - sends "PENALTY" to the watchdog BEFORE sleeping/comparing, so a  │
│      killed process can't dodge the clock cost                        │
│    - sleeps 3s (throttle), then constant-time compares input against  │
│      the real flag in /etc/latveria/vault.conf (0600 root:root)       │
│    - match → sends "DISARM", prints success, exits 0                  │
│    - no match → prints remaining clock, exits 1                       │
└───────────────────────────────────────────────────────────────────────┘
```

### Why this closes the loopholes from the original design doc

| # | Loophole | Mitigation actually implemented |
|---|---|---|
| 1 | Reading secrets from `/proc` | `$FLAG` unset immediately after templating; `/proc` mounted `hidepid=2`; secrets live only in root-only 0600 config files. |
| 2 | `strings` on the SUID binary | Flag/key never compiled in; binary reads `/etc/latveria/{failsafe,vault}.conf` at runtime, both 0600 root:root, unreadable to the conscript even though the binary itself is world-executable. |
| 3 | Sniffing the override string in transit | `--cap-drop=NET_RAW` prevents raw sockets/`tcpdump`; the image ships without packet-capture tools. |
| 4 | Camping decoy vault sectors | Decoys are cryptographically unrelated random values; the repair binary only ever compares against the real 16-byte instance key, so decoys fail immediately and obviously. |
| 5 | Killing/pausing the Watchdog to freeze or stop the clock | Watchdog runs as uid 0; the conscript's SUID child processes still have **real** uid 1000, and Linux signal-permission checks allow a sender to signal a process only if real/effective uids match — so the conscript cannot signal a process whose real uid is 0. `CAP_KILL` is additionally dropped as defense in depth. |
| 6 (new) | Reading or writing the shared clock/control state directly | `/run/latveria/display` is read-only to the conscript (0644, informational only, contains no secrets). `/run/latveria/ctl.sock` is 0600 root:root — a Unix domain socket's permission bits gate `connect()`, so the conscript cannot reach it at all, even knowing its path. |
| 7 (new) | Killing the SUID binary mid-attempt to dodge the -60s penalty | The binary reports the attempt to the watchdog **first**, before the throttle sleep and before the comparison runs. The penalty is committed the instant an attempt begins, not after it's evaluated. |
| 8 (new) | Racing two parallel sessions against the counter | The watchdog is a single-threaded consumer of `ctl.sock` — every PENALTY/DISARM request is serialized, so there's no read-modify-write race even with concurrent shells. |
| 9 (new) | Timing side-channel on the final flag comparison | Constant-time (fixed-iteration) comparison used for both the master-key check and the final flag confirmation. |

## 3. Difficulty Rating

**Overall: Hard (CTF-style, ~4.5/5)** — this is a multi-stage privilege/IPC
chain, not a single bug.

| Stage | Skill tested | Est. difficulty |
|---|---|---|
| Recon (decoys, ports, processes) | Basic Linux enumeration | Easy |
| Corrupting the world-writable config to crash the Doombot | Spotting a permissions misconfig; understanding what will actually crash a daemon vs. just annoy it | Medium |
| Discovering & using the override auth string over `netcat` | Reading leftover comments/config for a hidden protocol string | Medium |
| Racing the 15-minute clock through key retrieval → repair binary → hex decode → confirm | Time pressure, hex/ASCII conversion under a ticking clock, understanding that wrong guesses cost time | Medium–Hard |
| Realizing the SUID binary can't be beaten by killing it or attacking the watchdog directly | Understanding real vs. effective UID and Linux signal permissions (this is the "aha" of the whole challenge) | Hard |

Suggested scoring: 400–500 points on a Jeopardy-style board, or a
"first-blood + time-remaining bonus" if your platform supports it (the
watchdog logs exact `remaining_seconds` at solve time, which you can use
for a leaderboard tiebreaker).

## 4. Files in this package

```
Dockerfile                      — image build
entrypoint.sh                   — boot sequence, secret injection, tmux launch
motd.txt                        — the in-fiction briefing shown on login
daemons/doombot_daemon.py       — decoy rotation + heartbeat + sabotage target
daemons/latveria_failsafe.py    — port 9999 override listener
daemons/snapshot_watchdog.py    — the clock authority + ctl.sock server
bin/repair-seq.c                — SUID binary source
configs/doombot_ai.conf         — initial world-writable daemon config
configs/failsafe.conf.template  — templated with {{MASTER_KEY}} at boot
configs/vault.conf.template     — templated with {{FLAG}} at boot
scripts/gen_vaults.sh           — creates the 100 decoy sectors
scripts/clock_pane.sh           — the tmux pane 1 ticker
solve/solve_walkthrough.md      — full reference solve path for testing
```

## 5. Build & deploy checklist (run this on a real Docker host — not needed
in a sandboxed dev environment)

1. `docker build -t latveria-ctf .`
2. Run with the full flag set — **do not omit any of these**, several are
   load-bearing for the fixes above:
   ```
   docker run -d \
     --name latveria-instance-<id> \
     --memory=250m --memory-swap=250m \
     --pids-limit=100 \
     --cap-drop=NET_RAW --cap-drop=KILL \
     -e FLAG="ctf{...your real flag here...}" \
     -p 1337:1337 \
     latveria-ctf
   ```
3. Verify as a fresh instance, **before** giving it to any player:
   - `docker exec` in as root and confirm `/etc/latveria/failsafe.conf`
     and `/etc/latveria/vault.conf` are `0600 root:root`.
   - Confirm `/run/latveria/ctl.sock` is `0600 root:root` and that
     connecting to it as uid 1000 fails with `Permission denied`.
   - Confirm `/run/latveria/display` is `0644 root:root` and world-readable.
   - Confirm `ps aux` from inside as `latverian_conscript` cannot see other
     users' environ (`hidepid=2` in effect) — `cat /proc/1/environ` should
     fail.
   - Confirm `strings /usr/sbin/latveria-repair-seq` contains no flag-like
     or key-like string.
   - As `latverian_conscript`, try to `cat`, `stat`, or `kill` the watchdog
     process — all should fail.
   - Time a full solve with `solve/solve_walkthrough.md` and confirm the
     clock in pane 1 updates every second and the -60s penalty applies
     immediately on a deliberately wrong confirmation.
4. Only after all of the above pass, template in the real per-instance
   `$FLAG` and hand instances out to players.

## 6. Known intentional constraints / non-goals

- This is designed for **one player per container instance** — it is not
  built to be fair under multiple simultaneous players sharing one instance.
- The 15-minute clock is deliberately unforgiving; if you want a gentler
  onboarding round for beginners, drop `remaining_seconds` initial value
  in `snapshot_watchdog.py` up rather than changing any of the security
  mitigations.
