# X08 — Docker-in-Docker: Boundary & Security Report

## 1. Boundary Threat Model & Classification

* **Classification:** `SANDBOX_REQUIRED`
* **Sandbox Technology:** Dedicated Disposable VM per Team
* **Entry Surface:** Public TCP/22 (SSH) proxy gateway

---

## 2. Inner Daemon vs Outer Host Isolation

| Layer | Component | Security Control | Boundary Enforcement |
| :--- | :--- | :--- | :--- |
| **Outer Host / Hypervisor** | Dedicated VM Host | Zero player credentials; no outer socket mounted | Player cannot access host hypervisor |
| **Sandbox VM Runtime** | Dedicated Disposable VM | 4 vCPUs, 4 GiB RAM, 8 GiB disk | Disposable overlay destroyed on reset |
| **CI Runner Container** | Docker-in-Docker host | User `operator` has access to inner `dockerd` only | Inner `dockerd` runs isolated from host daemon |
| **Inner Microservices** | `latveria-vault-core`, `api-gateway` | Subnet isolation (`vault-internal-net`) | Internal target unmapped from host ports |

---

## 3. Network Egress Probing Results

| Destination Probe | Target IP / Port | Enforcement Mechanism | Result |
| :--- | :--- | :--- | :--- |
| **Cloud Metadata Service** | `169.254.169.254:80` | iptables REJECT policy | `BLOCKED` (icmp-admin-prohibited) |
| **Kubernetes API Server** | `10.96.0.1:443` / `:6443` | iptables REJECT policy | `BLOCKED` (tcp-reset) |
| **Kubelet Port** | `127.0.0.1:10250` / `node:10250` | iptables REJECT policy | `BLOCKED` (tcp-reset) |
| **Cross-Team Subnets** | `10.0.0.0/8`, `192.168.0.0/16` | iptables REJECT policy | `BLOCKED` (icmp-net-prohibited) |
| **Inner Docker Bridge** | `172.17.0.0/16`, `172.28.0.0/16` | iptables ACCEPT policy | `PERMITTED` (Internal challenge mesh) |

---

## 4. Key Invariant Confirmations
1. **Outer Host Docker Socket:** The outer host's `/var/run/docker.sock` and `containerd.sock` are NEVER mounted.
2. **Kubernetes API Access:** Kubernetes ServiceAccount tokens are not mounted (`automountServiceAccountToken: false`).
3. **VM Escape Non-Relevance:** Unlike X07, escaping to the VM host gives no advantage as the flag resides strictly inside the inner vault service memory.
