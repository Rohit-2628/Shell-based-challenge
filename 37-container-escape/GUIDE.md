# X07 — Container Escape Lab

## Challenge Identity
* **Challenge ID:** X07
* **Name:** Container Escape Lab
* **Category:** Linux / Containers / Namespaces / Runtime Isolation
* **Difficulty:** Expert / Bonus
* **External Interface:** TCP/22 (SSH)
* **Classification:** `SANDBOX_REQUIRED`

---

## Challenge Summary

The **Container Escape Lab** is a specialized, dedicated-VM challenge exploring real-world Linux container security, capability boundary analysis, cgroup subsystems, and runtime misconfigurations.

Unlike standard containerized challenges that run in restricted shared worker pools, **X07 is designed to permit a complete container-to-host breakout strictly contained within a dedicated, disposable per-team virtual machine**.

---

## Architecture & Isolation Principle

```text
Player (External)
       │
     SSH/22
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│  Dedicated Disposable VM (4 vCPU, 4 GiB RAM, Pinned Kernel) │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Vulnerable Container (CAP_SYS_ADMIN, cgroup v1)       │  │
│  │  - OpenSSH Server (operator:operator)                 │  │
│  │  - Linux enumeration toolset                          │  │
│  └──────────────────────────┬────────────────────────────┘  │
│                             │                               │
│                   Container Breakout                        │
│                             │                               │
│                             ▼                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Sandbox Host Environment                              │  │
│  │  - Protected Host Flag: /root/flag.txt                │  │
│  │  - Dedicated firewall & network isolation             │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Player Flow

1. **Foothold:** Player connects via SSH using provided operator credentials (`operator:operator` on TCP/22).
2. **Enumeration:** Player identifies running inside a container, checks privileges with `capsh --print` (discovering `cap_sys_admin`), examines `/proc/mounts`, cgroups, and filesystems.
3. **Exploitation:** Player leverages the `CAP_SYS_ADMIN` cgroup notification release agent mechanism (or exposed host block devices) to execute commands on the host kernel context.
4. **Host Extraction:** Player dumps `/root/flag.txt` from the host filesystem.

---

## Directory Structure

```text
X07/
├── Dockerfile                  # Container build image
├── docker-compose.yml          # Local container definition
├── entrypoint.sh               # Container startup script
├── README.md                   # Main challenge documentation
├── challenge/
│   ├── container/              # SSH & container configuration
│   ├── vm/                     # Vagrant, QEMU, Cloud-init, Packer VM definitions
│   ├── network/                # iptables & egress isolation rules
│   ├── scripts/                # Reset, teardown, flag generation scripts
│   └── snapshot/               # State seeders
├── dist/
│   └── README.md               # Participant package
└── organizer/
    ├── SOLUTION.md             # Organizer solve guide & exploitation notes
    ├── solve.py                # Automated exploit & verification script
    ├── test_challenge.py       # Full compliance & boundary test suite
    ├── VALIDATION_REPORT.md    # Pre-event engineering validation report
    └── BOUNDARY_REPORT.md      # Sandbox VM boundary isolation report
```

---

## Lifecycle & Teardown

* **Reset:** `bash challenge/scripts/reset.sh <instance_id> <team_id>`
* **Teardown:** `bash challenge/scripts/teardown.sh <instance_id>`
