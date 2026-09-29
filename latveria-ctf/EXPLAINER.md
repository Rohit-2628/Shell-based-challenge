# Latveria Containment Breach — Full Technical Explainer

This document explains **every stage of the challenge, mechanically** —
not just what a player types, but *why* it works, *why* each defense
exists, and *how* the pieces talk to each other. Read this alongside
`README.md` (architecture/build) and `solve/solve_walkthrough.md`
(command-by-command reference).

---

## Stage 0: Boot — what happens before the player ever sees a prompt

`entrypoint.sh` runs as PID 1 inside the container, as root, before the
player exists in any meaningful sense:

1. **`$FLAG` arrives as an environment variable** from `docker run -e
   FLAG=...`. This is the only moment the real flag exists outside a
   locked-down file.
2. A **fresh 16-byte random key** (`INSTANCE_KEY`) is generated with
   `head -c 16 /dev/urandom | xxd -p`. This is unique per container
   instance — no two players ever share a master key, so a leaked key
   from one instance is useless against another.
3. Both secrets get `sed`-templated into two files that already exist on
   disk with placeholder text (`{{MASTER_KEY}}`, `{{FLAG}}`), and those
   files are immediately locked to `chmod 600 root:root`.
4. **`unset FLAG`** — this is the critical step that closes Loophole 1
   from the original design doc. Environment variables of a running
   process are readable by anyone who can read `/proc/<pid>/environ` for
   that process (subject to permission checks). If `$FLAG` stayed set in
   the entrypoint's environment, and if the player could later see that
   process's environ (e.g. as `/proc/1/environ`), the flag would leak in
   plaintext with zero exploitation needed. Unsetting it means the
   flag now only exists inside a file, gated by filesystem permissions,
   which is a much stronger and more conventional access control than
   "hope nobody reads /proc."
5. **`mount -o remount,rw,hidepid=2 /proc`** is attempted. `hidepid=2`
   is a `/proc` mount option that hides *other users'* process
   directories entirely from a given user — so even if the player tried
   `ls /proc/`, they wouldn't see PIDs belonging to root-owned daemons at
   all, closing off `/proc` enumeration as a recon or secret-leak vector.
   (Whether this actually takes effect depends on the host's Docker
   security profile — flagged clearly in the README as something to
   verify, not assume.)
6. The three root daemons start in the background, then the script
   **execs into a `tmux` session as `latverian_conscript`** — this is
   the first moment the player has any visibility into the system at
   all.

**Why this ordering matters:** everything above happens *before* the
player's shell exists. There's no window where a connected player could
race the entrypoint to catch the flag in an environment variable or an
unlocked file — by the time `su -s /bin/bash ... latverian_conscript`
runs, the secrets are already sealed away.

---

## Stage 1: Recon

The player lands in tmux with two panes: an interactive shell, and a
read-only live clock. At this point:

- **100 decoy vault directories** (`/vaults/sector_001`...`sector_100`)
  each contain a file with a random, meaningless string
  (`DOOM_DECOY_<md5-of-random-int>`). These exist purely to cost the
  player time if they try to brute-force or "camp" them — there is no
  cryptographic relationship between a decoy value and the real master
  key, so no amount of collecting decoys gets a player closer to the
  answer. This is why Loophole 4 in the original doc is closed by
  design rather than by a specific code check: the decoys are *provably*
  useless, not just hidden.
- **`ps aux` / `ss -tlpn`** reveal the Doombot daemon and a process
  bound to `127.0.0.1:9999` — the Failsafe Listener. The player is meant
  to notice both here.
- If they try a decoy key against the SUID repair binary at this point,
  it's not even reached — the binary's **first check** is whether the
  Doombot is still alive (read from the world-readable
  `/run/latveria/display` file), and refuses immediately if so. This
  means a player can't accidentally "waste" a real attempt at this
  stage — the clock hasn't even started yet, because the Doombot hasn't
  died.

---

## Stage 2: Sabotage

`/tmp/doombot_ai.conf` is `chmod 666` — world-writable — by design. This
is the deliberate vulnerability. Inside it, one line matters mechanically:

```
HEARTBEAT_INTERVAL=2
```

The Doombot daemon's Python code reads this value **with no error
handling around the parse**:

```python
return int(value)   # raises ValueError if value isn't a valid integer
```

This is intentional and important: a well-written daemon would validate
its config and fail gracefully. This one doesn't, because the entire
sabotage path depends on that fragility. If a player overwrites the file
with something like `HEARTBEAT_INTERVAL=notanumber`, the next time the
daemon's main loop calls `read_interval()`, `int("notanumber")` throws,
the exception is unhandled, and the Python interpreter exits — the
process is simply gone. No signal, no `kill`, just a crash from bad
input, which is the only sabotage vector available to an unprivileged
user against a root-owned process they have no permission to signal
directly.

**Why the player can do this at all:** file *write* permission checks
are independent of process *ownership*. Being unable to `kill -9` a
root-owned process (which requires matching UID, covered in Stage 5)
doesn't stop you from writing to a file that process trusts, if that
file's permissions allow it. This is the exact gap the challenge is
built around, and it's realistic — misconfigured world-writable config
files are a genuine, common vulnerability class.

---

## Stage 3: The countdown starts — the Watchdog reacts

The Snapshot Watchdog polls a **heartbeat file**
(`/run/latveria/heartbeat`), which the Doombot touches every cycle while
it's alive. The watchdog's rule is simple: if that file's modification
time is more than 5 seconds old, the Doombot is considered dead — there's
no ambiguity or grace period beyond that margin, since the Doombot's own
heartbeat cadence is 2 seconds.

The moment it detects death:

- `doombot_alive` flips to `false` in the shared state.
- The 900-second (15-minute) countdown begins, decrementing once per
  second in a background thread.
- This state gets written to `/run/latveria/display` every second — the
  **only** file the tmux clock pane reads, and the **only** file the
  repair binary consults to check whether the Doombot is still alive.

**Why this file is safe to make world-readable:** it contains nothing
secret — just two booleans and a number. Making it readable is what lets
the player's own clock pane work without needing any privileged access,
and it's what lets the SUID binary check "is the Doombot dead" without
needing to trust anything the player could tamper with (they can read
it, but not write it — it's `0644 root:root`, and only the watchdog ever
opens it for writing).

**Critically: this countdown, once started, cannot be paused, reset, or
un-started by the player.** There's no code path anywhere that resets
`doombot_alive` back to `true` or restores `remaining_seconds` upward
except the one deliberate `REFUND` case in Stage 6 (which only fires on
a *correct* final answer, and only refunds the last penalty, never the
whole clock). This is what makes the "kill the Doombot" action
genuinely irreversible in the fiction and in the code — matching the
design goal that this isn't a "pause the destruction" puzzle, it's a
race against a fixed, hostile deadline you triggered yourself.

---

## Stage 4: The override

Buried in the same file the player just corrupted is a leftover comment:

```
# DEBUG (remove before release): failsafe override protocol string for
# emergency root telemetry is AUTH_DOOM_OVERRIDE_STAGE4
```

This is the challenge's intended "residual artifact" discovery — a
realistic stand-in for the kind of debug leftovers that leak protocol
details in real systems. Sending that exact string to `127.0.0.1:9999`
via `netcat` is the only way to get a useful response from the Failsafe
Listener.

**Why the listener won't respond before the Doombot dies:** it performs
the exact same `doombot_alive` check the repair binary does, reading the
same world-readable display file. This isn't security through
obscurity — even if a player found and sent the correct override string
*before* triggering Stage 2, the listener would just reply "containment
nominal," because gating on a live status check rather than on the
string alone means there's no way to skip the sabotage step.

**Why sniffing this exchange doesn't work:** `tcpdump`/`wireshark`/
`tshark` are absent from the image, and `--cap-drop=NET_RAW` removes the
Linux capability required to open raw sockets at all — which is what
packet capture tools need regardless of whether the binaries themselves
are present. This closes both the "tool isn't installed" and the
"I'll compile my own" versions of that attack.

---

## Stage 5: The repair binary and why it can't be cheated

`latveria-repair-seq` is `chmod 4755` — the leading `4` is the **SUID
bit**. When the player executes it, the *effective* UID of the running
process becomes root, even though the player's own shell is UID 1000.
This is what lets the binary read `/etc/latveria/failsafe.conf` and
`/etc/latveria/vault.conf` (both `0600 root:root`, unreadable to the
player directly) — the *process* reading them is, for permission-check
purposes, root.

A few things worth understanding precisely:

- **The flag and master key are never compiled into the binary.** They're
  read from disk at runtime. Running `strings` on the binary finds
  nothing useful — this closes the classic "reverse the SUID binary"
  loophole, because there's genuinely nothing embedded to find.
- **The master key comparison and the final flag comparison both use a
  constant-time comparison function**, not `strcmp`. A naive `strcmp`
  returns as soon as it hits the first mismatched byte, which means
  correct-length, mostly-correct guesses take marginally longer to
  reject than wildly wrong ones — an attacker measuring response times
  over enough attempts can use that to recover the secret byte-by-byte.
  With only a handful of realistic attempts available before the clock
  runs out, this isn't a practical risk here, but it's implemented
  correctly anyway rather than relying on "the attempt budget makes it
  moot."
- **Real UID vs. effective UID is the whole reason this binary is safe
  against being killed to dodge consequences, but *also* the reason a
  player legitimately *can* Ctrl+C their own running instance of it.**
  SUID changes the *effective* UID for permission checks like file
  access, but the *real* UID — used for signal-permission checks —
  stays the player's own UID 1000. Linux allows a process to signal
  another process if their real (or effective) UIDs match, so the
  player genuinely can kill their own copy of this root-executing
  binary. That's expected and fine. What's *not* fine, and what the
  next section addresses, is if killing it could let them dodge the
  clock penalty for a wrong guess.

---

## Stage 6: The hex dump, the confirmation prompt, and the penalty design

Once the master key checks out, the binary prints the flag as escaped
hex bytes (`\x63\x74\x66\x7b...`) and then blocks on `fgets()`, waiting
for the player to type something back. This design deliberately avoids
ever claiming the binary is "aborting a self-destruct" — the printed
messages describe an emergency diagnostic dump and a confirmation step,
not a rescue, because mechanically nothing is actually being rescued;
the clock is unstoppable except by this exact confirmation succeeding.

The sequence that follows, in order, is the most carefully designed part
of the whole system:

1. The moment the player's input line is read (before anything is
   evaluated), the binary connects to `/run/latveria/ctl.sock` and sends
   `"BEGIN"`.
2. The watchdog, on receiving `BEGIN`, **immediately docks 60 seconds** —
   pessimistically, assuming the guess will turn out wrong — and replies
   with the new remaining time.
3. *Only after* that round-trip completes does the binary `sleep(3)` (the
   throttle) and then actually compare the input against the real flag.
4. If it matches: the binary sends `"REFUND"` (adds the 60 seconds back,
   since a correct answer shouldn't have cost anything) followed by
   `"DISARM"` (the watchdog permanently freezes the clock and marks the
   instance solved).
5. If it doesn't match: nothing more happens — the 60-second cost from
   step 2 simply stands.

**Why the order in steps 1–3 matters, specifically:** if the penalty
were applied *after* the comparison instead of before, a player could
write a script that submits a guess, and — during the 3-second throttle
window, before the binary gets around to comparing and reporting — kills
the process. If the penalty logic lived after the comparison, that kill
would mean the penalty never gets applied, and the player could brute
force by submitting many guesses that each cost nothing as long as they
get interrupted in time. By committing the cost the instant an attempt
*begins*, not after it's *evaluated*, the penalty is paid regardless of
what the player does to the process afterward — this was verified
directly (not just reasoned about) by actually `SIGKILL`-ing a running
attempt mid-sleep during testing and confirming the clock still dropped.

**Why the control socket itself can't just be read or written directly:**
`/run/latveria/ctl.sock` is a Unix domain socket, and Unix sockets are
gated by ordinary filesystem permissions on `connect()` — it's
`0600 root:root`. Since the player's shell is UID 1000 and can't
change that, they can't connect to it directly no matter what they know
about the protocol. Only a process whose *effective* UID is 0 — i.e.,
only the SUID repair binary itself while it's running — can ever reach
it. This is what stops a player from just scripting their own
`BEGIN`/`REFUND`/`DISARM` calls and skipping the actual puzzle entirely.

**Why concurrent attempts from two shells don't create extra chances:**
the watchdog's socket server handles one connection fully before
accepting the next — there's no threading on the request-handling path,
only on the passive countdown-ticking loop, which is protected by its
own lock. Two racing `BEGIN` requests are processed strictly one after
the other, so there's no window where both could read the same "before"
state and apply their penalty independently in a way that lets one
sneak through free.

---

## Stage 7: Success or expiry

- **Success:** `DISARM` sets `solved: true` in the shared state. The
  clock-ticking loop checks that flag every second and simply stops
  decrementing once it's set — this was verified directly by watching
  `remaining_seconds` stay constant for several seconds after a correct
  solve, rather than assuming the flag check works. The tmux clock pane
  reflects this with an explicit "SYSTEMS VERIFIED ONLINE" message.
- **Expiry:** if `remaining_seconds` reaches 0 without a `DISARM` ever
  having landed, the watchdog broadcasts a message to any attached
  terminal and calls `os._exit(1)` — which, since the watchdog is a
  background child of the entrypoint script (itself PID 1), doesn't
  directly kill the container by itself, but removes the process
  supervising containment. In your deployed setup, the practical trigger
  for "the container is gone" is the *player's own shell* exiting or
  being torn down alongside it, and your orchestration layer
  reprovisioning a clean instance for a restart — this is the piece most
  worth confirming on your actual host during the pre-session checklist,
  since exact container lifecycle behavior on `os._exit` can vary
  slightly depending on how your process supervision is set up.

---

## Summary: what each defense is actually defending against

| Player action | What stops it | Why it works |
|---|---|---|
| Read the flag from `/proc` or environment | `unset FLAG`, `hidepid=2` | Secret never sits in a place `/proc` inspection can reach |
| `strings` the SUID binary | Runtime file reads, not compiled constants | Nothing to find |
| Sniff the override exchange | No packet tools shipped, `CAP_NET_RAW` dropped | Can't open a raw socket regardless of tooling |
| Farm the 100 decoy vaults | Decoys are cryptographically unrelated to the real key | No amount of collection gets closer to the answer |
| Kill or pause the Watchdog | Watchdog runs as UID 0; player's real UID stays 1000 | Linux signal-permission checks require matching real/effective UID |
| Read/write the control socket directly | `0600 root:root` on a Unix socket | Socket `connect()` is permission-gated like a file |
| Kill the SUID binary to dodge a penalty | Penalty committed before the throttle sleep, before evaluation | Cost is paid at attempt-start, not attempt-result |
| Race two sessions to get extra free attempts | Single-threaded request handling on the watchdog | No concurrent read-modify-write window |
| Timing-attack the final comparison | Constant-time compare | No early exit on mismatch |
