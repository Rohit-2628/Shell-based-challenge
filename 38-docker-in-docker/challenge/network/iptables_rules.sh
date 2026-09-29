#!/usr/bin/env bash
set -euo pipefail

# X08 Network Isolation & Boundary Enforcement Rules

echo "[*] Enforcing Sandbox VM Egress and Ingress Boundaries for X08..."

# Flush existing custom CTF filter chains if any
iptables -F OUTPUT || true

# 1. Allow established and loopback traffic
iptables -A OUTPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

# 2. Strict Block: Cloud Provider Metadata Service
iptables -A OUTPUT -d 169.254.169.254 -j REJECT --reject-with icmp-admin-prohibited

# 3. Strict Block: Kubernetes Control Plane & Node Management
iptables -A OUTPUT -p tcp --dport 6443 -j REJECT --reject-with tcp-reset
iptables -A OUTPUT -p tcp --dport 10250 -j REJECT --reject-with tcp-reset
iptables -A OUTPUT -d 10.96.0.0/12 -j REJECT --reject-with icmp-net-prohibited

# 4. Strict Block: Inter-VM / Neighboring Team Subnets (RFC1918 internal isolation)
iptables -A OUTPUT -d 10.0.0.0/8 -j REJECT --reject-with icmp-net-prohibited
iptables -A OUTPUT -d 172.16.0.0/12 ! -d 172.28.0.0/16 ! -d 172.17.0.0/16 -j REJECT --reject-with icmp-net-prohibited
iptables -A OUTPUT -d 192.168.0.0/16 -j REJECT --reject-with icmp-net-prohibited

# 5. Allow container bridge communications (Inner Docker subnets)
iptables -A OUTPUT -d 172.17.0.0/16 -j ACCEPT
iptables -A OUTPUT -d 172.28.0.0/16 -j ACCEPT

# 6. Default Deny Egress
iptables -A OUTPUT -j REJECT --reject-with icmp-admin-prohibited

echo "[+] Firewall rules successfully applied. Sandbox boundary secured."
