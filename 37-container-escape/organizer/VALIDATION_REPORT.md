# Challenge Compliance & Validation Report: X07

## Challenge Identity
* **Challenge ID:** X07
* **Challenge Name:** Container Escape Lab
* **Category:** Linux / Containers / Namespaces / Runtime Isolation
* **Difficulty:** Expert / Bonus
* **Classification:** `SANDBOX_REQUIRED`
* **External Interface:** TCP/22 (SSH)

---

### A. Architecture
`PASS`
* Only documented port (TCP/22 for SSH) is exposed through the platform gateway.
* Backend services and host systems are shielded behind dedicated per-team sandbox VM boundaries.

### B. Security
`PASS`
* Challenge intentionally involves container-to-host privilege escalation and is correctly designated as `SANDBOX_REQUIRED`.
* Dedicated VM isolates host kernel, devices, and memory from any shared worker nodes or cluster control planes.

### C. Network Isolation
`PASS`
* Strict default-deny egress enforced by VM host iptables firewall.
* Explicit blocks on AWS/GCP/Azure cloud metadata (`169.254.169.254`), Kubernetes API (`10.96.0.1`, port 6443), Kubelet (`:10250`), and inter-VM / team subnets.

### D. Resource Controls
`PASS`
* Dedicated masterbook allocations enforced: 4 vCPUs, 4096 MiB RAM, 20 GiB qcow2 storage overlay.
* Max process table limit of 4096 PIDs configured.

### E. Secrets & Flag Hygiene
`PASS`
* Protected host flag located exclusively on sandbox VM host at `/root/flag.txt`.
* Zero static flags or private signing keys embedded inside container images, Dockerfiles, or git trees.

### F. Participant Package
`PASS`
* Distribution package (`dist/`) contains exclusively `dist/README.md`.
* Zero leaks of solutions, escape scripts, host credentials, or secret keys.

### G. Intended Solve
`PASS`
* Exploit path: SSH connection -> Privilege enumeration -> CAP_SYS_ADMIN identification -> cgroup release_agent / mount escape -> Host flag extraction.
* Verified deterministically by `solve.py` and pre-event test suite.

### H. Boundary Testing
`PASS`
* In-VM container breakout is strictly confined to the dedicated virtual machine sandbox.
* Outer host, cluster nodes, and other teams are completely unreachable.

### I. Reset & Lifecycle
`PASS`
* Deterministic teardown and recreation via `challenge/scripts/reset.sh` and `teardown.sh`.
* Wipes container runtime, purges qcow2 overlays, and seeds fresh dynamic instance flags.

### J. Monitoring
`PASS`
* Platform health check monitors TCP/22 SSH daemon availability and instance resource utilization.

### K. Emergency Controls
`PASS`
* Instant VM destruction hook via platform hypervisor API / `teardown.sh`.

### L. Adversarial Testing
`PASS`
* 100% pass across all 10 adversarial security checks.

### M. Organizer Approval
`READY FOR EVENT`

---

## Challenge Approval Record

```text
Challenge ID: X07
Challenge Name: Container Escape Lab
Difficulty: Expert / Bonus
Classification: SANDBOX_REQUIRED
External Protocol: SSH
External Port: 22
Expected Solve Time: 90m
Initial Foothold: SSH shell (operator:operator)
Intended Pivot: CAP_SYS_ADMIN cgroup release_agent container breakout to VM host
Internal Services: OpenSSH Server, Containerd/Docker runtime, Linux cgroups v1
Flag Generation: Dynamic / Instance-scoped (DOOM{c0nt41n3r_3sc4p3_<hash>_x07})
Required Resources: CPU: 4 vCPU / Mem: 4096Mi / Disk: 20GiB
Required Egress: None (default deny)
Required Ingress: TCP/22 via Gateway
Reset Method: Full VM destruction, disk overlay purge, and fresh VM provisioning
Known Unsafe Operations: Intentional Container -> Host Escape (Strictly confined to Disposable VM)
Sandbox Required: Yes (Dedicated disposable VM per team)
Owner: CTF Challenge Engineering Team
Image Digest: sha256:local
Date Tested: 2026-09-26
```
