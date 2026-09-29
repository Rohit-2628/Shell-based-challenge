# X07 — Container Escape Lab

## Challenge Information
* **Challenge ID:** X07
* **Name:** Container Escape Lab
* **Category:** Linux / Containers / Namespaces / Runtime Isolation
* **Difficulty:** Expert / Bonus
* **External Interface:** TCP/22 (SSH)

---

## Mission Briefing

You have been granted SSH access into a containerized deployment node within the sovereign infrastructure. 

Your mission:
1. Connect via SSH to the container environment.
2. Enumerate system configuration, kernel metadata, mounts, namespaces, and security attributes.
3. Identify the isolation misconfiguration.
4. Escape the container environment to gain execution on the underlying sandbox host.
5. Locate and retrieve the host flag.

---

## Connection Details

* **Protocol:** SSH
* **Default Port:** 22 (or assigned gateway port)
* **Username:** `operator`
* **Password:** `operator`

Example connection:
```bash
ssh -p 22 operator@<TARGET_HOST>
```

---

## Rules of Engagement

* The entire challenge is hosted inside a dedicated, disposable sandbox VM assigned uniquely to your team.
* Do not attempt to attack other teams or platform infrastructure outside of your assigned VM.
* If your instance enters an unrecoverable state, request an environment reset from the platform portal.
