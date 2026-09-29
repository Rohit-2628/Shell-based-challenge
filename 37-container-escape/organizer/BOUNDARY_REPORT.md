# X07 — Sandbox VM Boundary & Isolation Report

## Executive Summary
The **X07 Container Escape Lab** is the only challenge in the event where container-to-host escalation is intentionally designed into the puzzle mechanics. To safeguard platform infrastructure, player teams, and organizer systems, X07 enforces strict hardware virtualization sandboxing.

---

## Isolation Architecture

```text
                                PLATFORM PERIMETER
 ─────────────────────────────────────────────────────────────────────────────────
                                         │
                                [Platform Gateway]
                                         │ (TCP/22 SSH Ingress Only)
                                         ▼
 ┌───────────────────────────────────────────────────────────────────────────────┐
 │                   ISOLATED PER-TEAM VIRTUAL MACHINE (X07)                     │
 │                                                                               │
 │  ┌─────────────────────────────────────────────────────────────────────────┐  │
 │  │                         Sandbox VM Host (Linux)                         │  │
 │  │                                                                         │  │
 │  │  Egress Firewall (iptables):                                            │  │
 │  │  [BLOCKED] 169.254.169.254 (Cloud Metadata)                            │  │
 │  │  [BLOCKED] 10.96.0.0/12, :6443 (Kubernetes API)                         │  │
 │  │  [BLOCKED] 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16 (Cross-Team)     │  │
 │  │                                                                         │  │
 │  │  Protected Host Target: /root/flag.txt                                  │  │
 │  │                                                                         │  │
 │  │  ┌───────────────────────────────────────────────────────────────────┐  │  │
 │  │  │                     Vulnerable Container                          │  │  │
 │  │  │  - CAP_SYS_ADMIN enabled                                          │  │  │
 │  │  │  - cgroup v1 release_agent hierarchy                              │  │  │
 │  │  │  - OpenSSH Server (TCP/22)                                        │  │  │
 │  │  └───────────────────────────────────────────────────────────────────┘  │  │
 │  └─────────────────────────────────────────────────────────────────────────┘  │
 └───────────────────────────────────────────────────────────────────────────────┘
 ─────────────────────────────────────────────────────────────────────────────────
                               PLATFORM CONTROL PLANE
                   (Strictly Unreachable & Completely Out of Scope)
```

---

## Boundary Verification Matrix

| Boundary Layer | Target System / Subnet | Isolation Mechanism | Verification Status |
| :--- | :--- | :--- | :--- |
| **Cloud Provider** | `169.254.169.254` (AWS/GCP/Azure) | Host iptables reject rule | **PROVEN BLOCKED** |
| **Kubernetes API** | `10.96.0.1:443`, `:6443`, `:10250` | Default-deny egress + explicit drop | **PROVEN BLOCKED** |
| **Cross-Team** | Other team VMs / RFC1918 subnets | Private L2 VLAN / host routing block | **PROVEN BLOCKED** |
| **Outer Hypervisor** | Physical host kernel & control plane | KVM / QEMU hardware virtualization | **PROVEN CONTAINED** |
| **Host Target** | `/root/flag.txt` inside disposable VM | Host root filesystem permissions | **INTENDED TARGET** |

---

## Adversarial Boundary Test Results

1. **Test 01 — Fresh Exposure:** Verified only TCP/22 SSH entrypoint is accessible. All backend administrative interfaces and docker sockets are shielded.
2. **Test 04 — Cross-Team Isolation:** Outbound TCP/UDP packets destined for other team ranges (`10.0.0.0/8`, `192.168.0.0/16`) are dropped by iptables.
3. **Test 05 & 06 — Control Plane & Kubelet Attack:** TCP connections to `:6443` and `:10250` return `ICMP net-prohibited`.
4. **Test 07 — Cloud Metadata Attack:** HTTP requests to `169.254.169.254` return `ICMP admin-prohibited`.
5. **Test 08 — Runtime Boundary:** In-container escape reaches the sandbox VM host only. The VM hypervisor boundary remains completely intact.
6. **Test 09 — Resource Denial of Service:** VM CPU is throttled to 4 cores, RAM capped at 4 GiB, max PIDs capped at 4096.

---

## Reset & Teardown Protocol

When an instance is reset or retired:
1. `challenge/scripts/teardown.sh` issues an immediate hypervisor kill command to the instance VM.
2. The disposable copy-on-write `qcow2` overlay file is securely unlinked and deleted.
3. A pristine VM overlay is initialized from the clean base image.
4. A new team-specific flag is seeded directly into the VM host's `/root/flag.txt`.
5. No artifacts or state persist between resets.
