#!/usr/bin/env bash
set -euo pipefail

# Dynamic Flag Generator for X08
TEAM_ID="${1:-default_team}"
SALT="latveria_dind_nested_isolation_2026"

HASH=$(echo -n "${TEAM_ID}_${SALT}" | sha256sum | cut -c 1-16)
echo "DOOM{d1nd_n3st3d_d0ck3r_d43m0n_p1v0t_x08_${HASH}}"
