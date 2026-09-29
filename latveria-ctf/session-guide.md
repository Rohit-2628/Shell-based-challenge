# Latveria Containment Breach — Session Facilitation Guide

This is for whoever is *running* the event, not for participants. Keep it
off any shared screen.

---

## 1. Pre-Session Checklist (do this the day before, not 10 minutes before)

- [ ] Build the image and run the full verification checklist from
      `README.md` section 5 on a throwaway instance. Don't skip this —
      several mitigations (hidepid, socket permissions) fail silently on
      misconfigured hosts and you want to know that *before* a participant
      finds it for you.
- [ ] Decide instance count: **one container per participant/team.** This
      challenge is not designed for shared instances (see README section 6).
- [ ] Generate a distinct `$FLAG` per instance. Keep a private
      spreadsheet mapping `instance_id -> flag -> participant/team`. This
      matters more here than in a typical CTF: once a container reverts or
      is torn down, the flag is genuinely gone — there is no way to look
      it up after the fact, by design. Your spreadsheet is the only
      durable record, alongside each container's watchdog log (see
      Section 5).
- [ ] Decide and publish a **restart budget** per participant (e.g. "you
      get 2 fresh instances if yours reverts or breaks"). Without a cap,
      a participant who trips the 15-minute clock repeatedly can consume
      disproportionate operator time re-issuing instances.
- [ ] Test the actual connection path (SSH/socat, whatever you're
      fronting it with) end-to-end from an outside network, not just from
      the Docker host.
- [ ] Print or have ready the tiered hint sheet (Section 4) — don't
      improvise hints live, it's easy to over-reveal under time pressure.
- [ ] If several instances are running, keep a terminal open tailing all
      watchdog logs at once (see Section 5) so you have live visibility
      without needing to `exec` into anyone's specific container.

## 2. Kickoff Briefing (read or closely paraphrase to participants)

> You're being dropped into a shell inside a fortress network as a
> disposable conscript. Somewhere in this system is a way to extract a
> secret before an automatic 15-minute snapshot revert wipes your
> instance and starts you over. The revert clock is real — once it
> triggers, nothing brings that instance back, including us. Wrong
> answers at the final confirmation step cost you 60 seconds each, so
> don't guess blind.
>
> Rules for the room: no attacking the Docker host or other
> participants' instances, no denial-of-service against the shared
> infrastructure, and if your instance reverts, come to us for a new one
> rather than trying to work around it — you have [N] restarts.

Explicitly say the restart limit out loud — it's the number people forget
under pressure and then argue about later.

## 3. Suggested Timing

This is rated **Hard** (see README section 3) — budget accordingly. A
reasonable total session window:

| Phase | Suggested length | Notes |
|---|---|---|
| Briefing + connection troubleshooting | 10 min | Most early support load is connectivity, not the challenge itself |
| Working time | 45–60 min | Includes restarts; the 15-min in-challenge clock is separate from this outer session clock |
| Wrap-up / debrief | 10–15 min | See Section 6 |

Give a **10-minute warning** and a **2-minute warning** before the outer
session ends — separate from the in-challenge countdown, which
participants can already see live in their own tmux pane.

## 4. Hint Escalation Tiers

Give the *lowest* tier first and only escalate if someone is genuinely
stuck for several minutes — over-hinting kills the "aha" moments this
challenge is built around (especially the UID-separation insight at the
end).

| Tier | When to give it | Hint |
|---|---|---|
| 1 | Stuck on recon | "Check what's writable that maybe shouldn't be." |
| 2 | Found the writable file, not sure what to change | "What happens to the daemon if the value it reads isn't a number?" |
| 3 | Doombot's dead, no idea what's next | "Something's now listening that wasn't answering before. Check what changed on the loopback interface." |
| 4 | Has the master key, binary rejects it or they're stuck at the prompt | "The dump isn't plain text — decode it before you type anything back." |
| 5 | Trying to kill/pause the process or the watchdog to cheat the clock | "Think about *whose* process that really is, even though it's running as root." |

Never hand out the literal override string, config path, or a working
command — steer, don't solve.

## 5. Monitoring During the Session

Each container's watchdog prints clear log lines you can grep for
without touching anyone's shell:

```
docker logs <container> 2>&1 | grep -E "WATCHDOG|BROADCAST"
```

- `[WATCHDOG] Doombot heartbeat lost. Countdown started.` — they've
  sabotaged the daemon, clock is live.
- `[WATCHDOG] DISARM received. Challenge solved.` — solved. Cross-check
  against your flag spreadsheet, don't just trust a screenshot.
- `[BROADCAST] Snapshot revert executing.` — they ran out the clock;
  the container is about to exit. This is your cue to issue a fresh
  instance against their restart budget.

If someone's tmux clock pane looks frozen or wrong, that's almost always
either (a) their connection stalled, not the container, or (b) `hidepid`
or the display file permissions weren't verified pre-session — check
`docker exec <container> cat /run/latveria/display` from the host side
to see the real state before assuming it's a bug in front of the group.

## 6. Scoring & Wrap-up

- Pull final state from each container's watchdog log rather than
  asking participants to self-report — `DISARM` in the log is your
  source of truth.
- If you want a tiebreaker, the watchdog logs `remaining_seconds` at
  solve time isn't printed directly today, but you can infer relative
  speed from solve-log timestamps against each container's start time.
- For the debrief, walk the room through `solve/solve_walkthrough.md`
  stage by stage, and specifically call out the UID-separation lesson at
  the end (why killing the SUID binary can't dodge the clock, and why
  the watchdog can't be signaled by the conscript) — that's the
  conceptual payoff of the whole exercise, worth spending real time on
  even for people who didn't finish.

## 7. Troubleshooting Table

| Symptom | Likely cause | Fix |
|---|---|---|
| Clock pane stuck / not updating | Connection stall, not the container | Have them reconnect; check `docker logs` for continued watchdog activity |
| Participant killed their own shell weirdly via tmux | `bash --login` in pane 0 exited without the outer session tearing down cleanly | `docker exec` in and check `tmux ls`; restart their session or reissue instance |
| `hidepid=2` didn't take | Host/orchestrator didn't grant the remount | Known limitation, documented in README section 5 — apply at `docker run`/orchestrator level, not fixable at runtime from inside |
| Multiple people in one instance by accident | Instance sharing wasn't blocked at the network layer | Enforce one connection per instance at your proxy/socat layer before the next session |
| Someone insists their solve didn't register | Race between their client and watchdog log flush, or they mistyped and actually failed | Check the watchdog log directly — it's authoritative, screenshots aren't |

## 8. After the Session

- Tear down all containers; don't reuse a `$FLAG` across sessions or
  participants even if convenient.
- Archive the watchdog logs (they're your only durable evidence of who
  solved what and when — the containers themselves won't be around to
  ask again).
- Note anything that came up during hints or troubleshooting that
  suggests a mitigation didn't hold in practice — feed that back into
  the pre-session checklist for next time rather than trusting memory.
