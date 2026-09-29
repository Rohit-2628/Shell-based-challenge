#!/usr/bin/env bash
set -euo pipefail

# Dynamic Flag Generator for X07
TEAM_ID="${1:-default_team}"
SALT="latveria_cgroup_isolation_2026"

HASH=$(echo -n "${TEAM_ID}_${SALT}" | sha256sum | cut -c 1-16)
echo "DOOM{c0nt41n3r_3sc4p3_${HASH}_x07}"
