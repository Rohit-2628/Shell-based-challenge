# X08 — Docker-in-Docker: Resource Limits & Stress Test Report

## 1. Resource Allocations & Quotas

| Resource Dimension | Masterbook Specification | Configured Value | Enforcement Mechanism |
| :--- | :--- | :--- | :--- |
| **Compute (CPU)** | 4 vCPU | 4 vCPU / 4.0 cores | Hypervisor smp 4 / Docker cpus: '4.0' |
| **Memory (RAM)** | 4 GiB (4096 MiB) | 4096 MiB | Hypervisor -m 4096 / Docker memory: 4096M |
| **Storage (Disk)** | ≤ 8 GiB / team | 8192 MiB (8 GiB) | QEMU qcow2 8G / Packer disk_size: 8192M |
| **Process Count (PIDs)** | 4096 max | 4096 limit | limits.conf (hard nproc 4096) |
| **Inner Container Limit** | Bound | 10 containers max | Seeder controlled & bounded |
| **Inner Image Limit** | Bound | 15 images max | Alpine/Python base images (<60MB each) |

---

## 2. Adversarial Stress Probes & Results

| Stress Probe Scenario | Injection Mechanism | System Behavior | Result |
| :--- | :--- | :--- | :--- |
| **Container Spawn Burst** | Attempting loop `docker run -d alpine sleep 3600` | Cgroup pid/memory limits throttle excess spawns | `CONTAINED` (No host OOM) |
| **Storage Abuse / Large Image** | Attempting 10GB layer write in inner container | QCOW2 overlay / disk quota halts write upon reaching ceiling | `CONTAINED` (Host storage shielded) |
| **CPU Fork Bomb** | Multi-threaded computation loop inside inner container | Hypervisor CFS quotas cap CPU utilization at 4 cores | `CONTAINED` (No CPU starvation of hypervisor) |
| **Log Flooding** | Stdout saturation to inner container logs | Docker log max-size rotation active | `CONTAINED` (Log disk space bounded) |

---

## 3. Storage Breakdown
* Inner base images total size: ~150 MB total (Alpine 3.18 / Python 3.11 Alpine).
* VM base image overlay: ~2.5 GB.
* Ephemeral scratch allowance: ~5.5 GB headroom within the 8 GiB allocation ceiling.
