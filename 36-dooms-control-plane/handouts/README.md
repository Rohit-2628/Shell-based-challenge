# Doom's Control Plane (Challenge X06)

## Overview
Doctor Doom's autonomous infrastructure in Latveria is governed by an internal synthetic orchestration control plane known as **Doom's Control Plane**.

A public telemetry and node management dashboard is reachable on HTTP port 80. Your objective is to investigate the public gateway, inspect available telemetry and credentials, interact with the internal control plane API, manage synthetic workload states, and unlock the Sovereign Core Vault to retrieve the flag.

## Target
- **Protocol**: HTTP
- **Port**: TCP 80
- **Format**: `http://<TARGET_HOST>:80`

## Scope & Boundaries
- All operations must remain challenge-local.
- The challenge runs a synthetic workload control plane.
- Real Kubernetes APIs, cloud metadata, and event infrastructure are not part of the challenge scope.

Good luck!
