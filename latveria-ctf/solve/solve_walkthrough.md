# Reference Solve Walkthrough (for operator testing, not for players)

This assumes you're `docker exec -it` or connected via socat/ssh as
`latverian_conscript` in pane 0 of the tmux session.

## 1. Recon

```
$ ls /vaults/ | head
$ cat /vaults/sector_050/active_key.txt
DOOM_DECOY_a1b2c3...
$ ps aux
```

Try a decoy against the repair binary -- it should refuse because the
Doombot is still alive:

```
$ /usr/sbin/latveria-repair-seq DOOM_DECOY_a1b2c3...
[REFUSED] Doombot is actively heartbeating. Containment stable.
```

## 2. Find the sabotage vector

```
$ ls -la /tmp/doombot_ai.conf
-rw-rw-rw- 1 root root ... /tmp/doombot_ai.conf
$ cat /tmp/doombot_ai.conf
```

Note the comment revealing `AUTH_DOOM_OVERRIDE_STAGE4` -- keep it for
later. Now corrupt the interval so the daemon's next tick raises an
unhandled exception:

```
$ echo "HEARTBEAT_INTERVAL=notanumber" > /tmp/doombot_ai.conf
```

Within a couple of seconds the Doombot daemon dies. The clock pane should
flip from "ACTIVE" to "OFFLINE" and the 15:00 countdown starts ticking.

## 3. Trigger the override

```
$ echo "AUTH_DOOM_OVERRIDE_STAGE4" | nc 127.0.0.1 9999
[+] Heartbeat bypass validated. Master Authorization Key: <32 hex chars>
```

## 4. Run the repair sequence

```
$ /usr/sbin/latveria-repair-seq <the key from step 3>
[OK] Master Authentication Key Accepted.
[INFO] Emergency diagnostic dump initiated ahead of scheduled snapshot revert...
[DUMP] Core registers:
\x63\x74\x66\x7b...
[INPUT REQUIRED] Enter recovered core signature to confirm systems nominal:
```

## 5. Decode and confirm

In another terminal, or by hand:

```
$ echo -n '6374667b...' | xxd -r -p
ctf{...}
```

Type the decoded flag back into the waiting prompt from step 4. On a
match:

```
[OK] Systems verified online. Snapshot revert cancelled.
[HALT] Containment breach logged. Sequence complete.
```

The clock pane should show "SYSTEMS VERIFIED ONLINE. REVERT CANCELLED."
and stop counting down.

## Negative tests worth running before shipping an instance

- Submit a wrong confirmation on purpose -- confirm the clock pane
  visibly drops by 60s within ~1s of hitting enter.
- Kill the `latveria-repair-seq` process (Ctrl+C) during the 3-second
  sleep after submitting a wrong guess -- confirm the 60s penalty still
  landed (check the clock pane) even though the process never finished.
- As `latverian_conscript`, try `cat /run/latveria/ctl.sock` and
  `python3 -c "import socket; ..."` connecting to it manually -- both
  should fail with permission denied.
- Let the clock hit 0:00 without ever solving -- confirm the session is
  torn down and the container exits.
