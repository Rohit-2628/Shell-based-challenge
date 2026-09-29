# Latveria Breach — Doctor Doom CTF Challenge

**Premise:** the player thinks they're breaching a government server
(Latveria). It's a honeypot. Cracking the "classified vault" springs a
trap: a 20-minute defense grid countdown. They have to escalate to root,
find the override flag, and disarm it before time runs out.

## Full rebuild notes — what changed and why

### Real bug fixed: the countdown could be killed without root
Previously, the countdown timer was a background process spawned *by the
player's own vault session* — meaning it ran under the player's own UID,
and they could kill it directly (`kill $(cat /tmp/.destruct_pid)`) without
ever escalating privileges or finding the flag. That fully broke the
challenge's core mechanic.

**Fix:** the countdown now lives in `watchdog.sh`, a persistent process
started by `entrypoint.sh` at container boot, running as **root** for the
container's entire lifetime. A non-root user fundamentally cannot signal
(`kill`) a process owned by a different UID — Linux enforces this at the
kernel level, it's not something our code can be tricked around. `vault`
only *requests* arming by touching a file; `abort_destruct` only *requests*
disarming by writing a flag guess to a file. The watchdog is the sole
authority that actually starts/stops the timer, and it independently
verifies the flag hash itself before ever honoring a disarm request — so
even directly editing files by hand (bypassing `abort_destruct` entirely)
still requires knowing the real flag.

### "exit doesn't work" after privesc — not a bug, explained + hinted
`sudo find . -exec /bin/sh \;` spawns a new shell for *every* file `find`
matches — typing `exit` just closes the current one and drops into the
next match. This is standard `find` behavior (it's why GTFOBins' own
documented payload includes `-quit`: `sudo find . -exec /bin/sh \; -quit`).
We didn't silently patch around it — `./hint` explains it in-world without
spoiling the whole exploit, and the intruder's home directory is kept
sparse so there are few matches to begin with.

### Source-hiding: vault / abort_destruct compiled from C, not shc-wrapped scripts
Shell scripts can't be truly execute-only — the interpreter has to read
them, so any user who can run a `.sh` can also `cat` it. Since reading `vault.c`'s source directly reveals the exact plaintext key
format
(letting a player skip the entire cipher-decoding puzzle), that counts as
a real exploit.

**Note:** the first version of this fix used `shc` to wrap the scripts
into ELF binaries. In testing, the compiled binary produced garbage
output at runtime (`shc`'s RC4-based obfuscation is known to be flaky
across versions) — a real, reproducible failure, not a one-off. `vault`
and `abort_destruct` are now plain **C programs** (`vault.c`, `abort.c`),
compiled directly with `gcc` at build time — no third-party wrapper, no
shell interpreter involved at runtime at all. `chown root:root` +
`chmod 710` (the intruder's primary group is `root`) still applies: the
intruder can execute them but has no read permission — `cat ~/vault`
fails outright, and since there's no separate script file to fall back
to, there's nothing to leak.

The flag-hashing in `abort.c` writes the player's guess to a fixed,
non-attacker-controlled temp path before shelling out to `sha256sum` on
that path — the guess itself is never interpolated into a shell command
string, so there's no injection surface from what the player types.

### Art — constructed in the terminal, not converted from a photo
Both visuals are built algorithmically from shape/color logic (a small
Python generator computes the geometry, then emits it as 24-bit-color
ANSI text) rather than typed character-by-character *or* converted
pixel-for-pixel from a reference image. Two pieces, one per moment:
- `login_banner.ansi` — an original Latverian flag: bordered rectangle,
  green field, gold diamond emblem, shown once at login
- `vault_reveal.ansi` — a hooded figure silhouette (hood taper, flared
  shoulders, angular eye-slit cutouts), shown only when the vault trap
  actually springs

The armed-grid and win-screen moments intentionally stay text/typewriter
only, so the two art pieces don't get diluted across every screen.

Requires a 24-bit-color-capable terminal (virtually all modern SSH
clients qualify).

## The 9 aesthetic changes, all included
1. **Renamed throughout** to the breach narrative (`intruder` login,
   "Latverian State Archive" vault, "Latverian Defense Grid" countdown)
2. **Color scheme** — green/gold (Doom's actual palette) instead of plain
   red/green terminal defaults, red reserved for the trap-spring moment
3. **Animated boot sequence** — staggered breach-narrative lines on login
4. **Hidden diary/flavor easter egg** — `/opt/.intercepted_transmission.txt`
5. **Typewriter effect** — used on the big reveal lines in `vault.c`
6. **Live countdown** — `./status` shows armed/disarmed state and time left
7. **Randomized taunts** — wrong-key and wrong-flag responses vary
8. **Latverian flag** at login instead of a generic crest — algorithmically
   constructed in-terminal, not derived from any image
9. **Re-flavored sudoers entry** — in-world comment, discoverable after
   rooting the box

## Layout

```
latveria-breach/
├── docker-compose.yml
├── README.md
├── inner/
│   ├── Dockerfile
│   ├── entrypoint.sh         # boot sequence, flag/pass injection, starts watchdog
│   ├── watchdog.sh           # root-owned, authoritative timer + disarm check
│   ├── broadcaster.sh        # hidden cipher log
│   ├── vault.c               # compiled -> ~intruder/vault (execute-only)
│   ├── abort.c               # compiled -> ~intruder/abort_destruct (execute-only)
│   ├── status.sh             # -> ~intruder/status
│   ├── hint.sh                # -> ~intruder/hint
│   ├── intercepted_note.txt  # easter egg flavor text
│   └── assets/
│       ├── login_banner.ansi   # Latverian flag, shown at login
│       └── vault_reveal.ansi   # hooded figure, shown when the trap springs
└── outer/
    ├── Dockerfile
    └── watcher.sh
```

## Run it

```bash
cd latveria-breach
sudo docker compose up -d --build
ssh -p 2222 intruder@localhost
```

Your CTF platform overrides `FLAG` and `SSH_PASS` in `inner_core`'s
`environment:` block per-instance. Static fallbacks keep it playable
standalone.

## Gameplay flow

1. `intruder` logs in, sees the breach-narrative boot sequence + Latverian
   flag banner.
2. A rotating cipher (reversed Base64 of `doom_MM`) is quietly logged to
   `/var/log/latveria_intercept.log` every 30s — has to be found.
3. Decode it (`rev | base64 -d`), run `./vault`, enter the decoded
   plaintext (`doom_45`, not the cipher itself).
4. Correct key: reveal art plays, defense grid arms (root-owned timer
   starts, `vault` itself gets locked out by the watchdog).
5. `sudo -l` reveals passwordless `find`. `sudo find . -exec /bin/sh \;`
   works but re-spawns per match — `./hint` explains why and nudges
   toward `-quit`.
6. Root shell reads `/root/flag.txt`, exits back to the normal shell, runs
   `./abort_destruct`, pastes the flag in.
7. `abort_destruct` hands the guess to the root watchdog, which
   independently verifies it and is the only thing that actually stops
   the kill. Success prints the flag back for scoreboard submission.

## Terminal compatibility

The `.ansi` art needs 24-bit color support, which is the default for
essentially every modern SSH client. Older 256-color-only terminals will
still render it, just with slightly flattened colors.
