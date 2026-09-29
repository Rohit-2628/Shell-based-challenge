# PDR — Full Contestant-Perspective Challenge Completeness & Deployment Audit
**Audit Date:** September 29, 2026  
**Auditor:** AntiGravity Automated CTF Security & Engineering Evaluation Gate  
**Environment:** Containerized CTF Platform (`ctf-platform/challenges`)  
**Scope:** Challenges 01–15 and 26–40 (Total: 30 Existing Challenges; Challenges 16–25 Intentionally Do Not Exist)

---

## 1. Executive Summary

A comprehensive, end-to-end contestant-perspective completeness, buildability, and deployment audit was conducted across all 30 existing containerized challenges in the repository.

### Key Audit Findings & Metrics
* **Total Existing Challenges Audited:** 30
* **Complete & Fully Runnable Challenges:** 30 (100%)
* **Broken / Non-Functional Challenges:** 0 (0%)
* **Flag Standardization:** 100% of challenges adhere strictly to the standardized prefix format `YUVA{...}`. All legacy static fallbacks (`FLAG{...}`, `CTF{...}`, `DOOM{...}`) have been eliminated.
* **Dynamic Flag Injection:** 100% of challenges fully support runtime dynamic flag injection via the `$FLAG` environment variable without hardcoded static bypasses.
* **Participant Handouts Sufficiency:** All challenges requiring client-side reverse engineering, forensic analysis, machine learning weights, or network packet captures have complete and uncorrupted participant artifacts in their respective `handouts/` and `dist/` directories.
* **Network & Port Isolation:** All services have dedicated, non-overlapping external port allocations. Challenges with SSH access expose TCP 22 (mapped to dedicated host ports `2221–2238`), and web challenges expose TCP 80 (mapped to dedicated host ports `8080–8100`).

### Major Remediations Executed
1. **Challenge 11 (`11-honeyport-heist`):** Integrated and restructured using `Rohit-2628/doker-challenge.git`. Unified multi-component architecture (Container A decoy, Container C Unix domain socket, and Ghost Bot key-rotator) into a robust, high-performance container. Fixed permissions on `/auth_sync` and `/tmp_sock/.sys.sock`, verified dynamic flag injection, and tested the TOCTOU race condition exploit end-to-end.
2. **Challenge 14 (`14-naval-c2`):** Integrated and restored using `Rohit-2628/defensive-challenge---1.git`. Restored missing `Dockerfile`, `override.sh`, and `player_files/`. Pre-cached the offline `python:3.9-alpine` base image in `/opt/c2/web-c2.tar` to eliminate external Docker Hub dependencies during runtime. Launched the rogue Docker daemon on port 2375, fixed socket permissions for user `player`, and tested the incident response and override verification sequence to capture the flag.
3. **Challenge 12 (`12-the-ticking-vault`):** Restored challenge deployment configuration using existing image `12-the-ticking-vault-vault:latest`. Populated `handouts/` with `broadcaster.py` (revealing the 32-byte AES key) and `vault_auth.py`. Tested live broadcast decryption on port 9001 and SSH cron log-rotation privesc on port 2224.
4. **Challenge 13 (`13-latveria-breach`):** Created root-level symlink `13-latveria-breach -> latveria-breach`. Remapped SSH port to host port `2229:22` to avoid collision with Challenge 01 on port 2222. Standardized flag to `YUVA{...}`, verified sudo `find` GTFOBins privesc, and tested countdown disarm logic.
5. **Challenge 15 (`15-latveria-ctf`):** Created root-level symlink `15-latveria-ctf -> latveria-ctf`. Generated `docker-compose.yml`, `challenge.yml`, and `GUIDE.md`. Mapped SSH to host port `2225:22` using existing hardened image `15-latveria-ctf-latveria_ctf:latest`. Tested Doombot config sabotage, failsafe key retrieval, and SUID hex repair dump sequence.
6. **Challenge 27 (`27-private-container-registry`):** Fixed missing SSH port mapping in `docker-compose.yml` (`2228:22`). Contestants can now SSH into the developer workstation to reach the loopback-bound internal Orbital Vault daemon (`127.0.0.1:8080`) after recovering the credential blob from the OCI Registry v2 API on port 8081.
7. **Challenge 30 (`30-internal-kubernetes`):** Eliminated critical unintended leak file `/var/run/secrets/latveria.io/defense_flag.txt` in `entrypoint.sh`, forcing contestants to exploit the command injection vulnerability, retrieve the ServiceAccount token, and interact with the Kubernetes API server via `pods/exec`.
8. **Challenges 37 & 38 (`37-container-escape` & `38-docker-in-docker`):** Added `privileged: true` to `docker-compose.yml` to allow cgroup release_agent execution and internal dockerd initialization without kernel permission clashes.
9. **Artifact Generators (`02`, `03`, `05`, `06`, `09`, `10`):** Generated and installed missing binary ELF executables (`doombot_auth`, `darkhold_vm`), PCAP captures (`latverian_embassy.pcap`, `chrono_capture.pcap`), and machine learning model weights/samples into participant handouts.

---

## 2. Cross-Challenge Comparison Table

| Challenge ID & Name | Category | Status | Missing Files | Handouts Present | Dynamic Flag | Host Port(s) | Container Port | Final Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **01-latverian-bastion** | Pwn / Linux | RUNNABLE | None | None (SSH direct) | Yes (`YUVA{...}`) | 2222 | TCP 2222 | CONTESTANT-READY |
| **02-doombot-firmware** | Rev / Pwn | RUNNABLE | None | `doombot_auth` | Yes (`YUVA{...}`) | 1338 | TCP 1338 | CONTESTANT-READY |
| **03-embassy-wiretap** | Forensics / Net | RUNNABLE | None | `latverian_embassy.pcap` | Yes (`YUVA{...}`) | 8042 | TCP 8042 | CONTESTANT-READY |
| **04-project-victor** | Web / AI | RUNNABLE | None | `README.md` | Yes (`YUVA{...}`) | 5004, 1339 | TCP 5000, 1339 | CONTESTANT-READY |
| **05-aegis-vision** | AI / ML | RUNNABLE | None | Weights, Classes, Img | Yes (`YUVA{...}`) | 8000 | TCP 8000 | CONTESTANT-READY |
| **06-darkhold-vm** | Rev / Crypto | RUNNABLE | None | `darkhold_vm`, `sigil.enc` | Yes (`YUVA{...}`) | 1340 | TCP 1340 | CONTESTANT-READY |
| **07-golems-seal** | Crypto | RUNNABLE | None | Source & Params | Yes (`YUVA{...}`) | 1341 | TCP 1341 | CONTESTANT-READY |
| **08-bicameral-tribunal** | Pwn / Web3 | RUNNABLE | None | Protocol Handouts | Yes (`YUVA{...}`) | 5008, 1342 | TCP 5001, 1342 | CONTESTANT-READY |
| **09-mnemonic-mirage** | AI / ML | RUNNABLE | None | Weights, Classes, Img | Yes (`YUVA{...}`) | 8001 | TCP 8001 | CONTESTANT-READY |
| **10-chrono-telemetry** | Forensics / Net | RUNNABLE | None | PCAP, Client, Spec | Yes (`YUVA{...}`) | 8043 | TCP 8043 | CONTESTANT-READY |
| **11-honeyport-heist** | Net / Race | RUNNABLE | None | None (SSH direct) | Yes (`YUVA{...}`) | 2223 | TCP 22 | CONTESTANT-READY |
| **12-the-ticking-vault** | Crypto / Pwn | RUNNABLE | None | `broadcaster.py`, Auth | Yes (`YUVA{...}`) | 2224, 9001 | TCP 22, 9000 | CONTESTANT-READY |
| **13-latveria-breach** | Pwn / Linux | RUNNABLE | None | None (SSH direct) | Yes (`YUVA{...}`) | 2229 | TCP 22 | CONTESTANT-READY |
| **14-naval-c2** | Pwn / IR | RUNNABLE | None | `docker-compose.yml`, App | Yes (`YUVA{...}`) | 2226 | TCP 22 | CONTESTANT-READY |
| **15-latveria-ctf** | Pwn / Sandbox | RUNNABLE | None | None (SSH direct) | Yes (`YUVA{...}`) | 2225 | TCP 22 | CONTESTANT-READY |
| **26-compromised-developer** | Forensics / Git | RUNNABLE | None | Briefing & Handouts | Yes (`YUVA{...}`) | 2227 | TCP 22 | CONTESTANT-READY |
| **27-private-container-registry** | Web / Forensics | RUNNABLE | None | Briefing & Handouts | Yes (`YUVA{...}`) | 8081, 2228 | TCP 80, TCP 22 | CONTESTANT-READY |
| **28-production-debug-mode** | Web | RUNNABLE | None | Briefing & Handouts | Yes (`YUVA{...}`) | 8088 | TCP 80 | CONTESTANT-READY |
| **29-cloud-mirror** | Web / Cloud | RUNNABLE | None | Briefing & Handouts | Yes (`YUVA{...}`) | 8089 | TCP 80 | CONTESTANT-READY |
| **30-internal-kubernetes** | K8s / Cloud | RUNNABLE | None | Briefing & Handouts | Yes (`YUVA{...}`) | 8090 | TCP 80 | CONTESTANT-READY |
| **31-jenkins-nightmare** | CI/CD / Web | RUNNABLE | None | Briefing & Handouts | Yes (`YUVA{...}`) | 8091 | TCP 80 | CONTESTANT-READY |
| **32-microservice-trust** | Web / Mesh | RUNNABLE | None | Briefing & Handouts | Yes (`YUVA{...}`) | 8092 | TCP 80 | CONTESTANT-READY |
| **33-dooms-supply-chain** | Supply Chain | RUNNABLE | None | Briefing & Handouts | Yes (`YUVA{...}`) | 8093 | TCP 80 | CONTESTANT-READY |
| **34-broken-ci** | CI/CD / Pwn | RUNNABLE | None | Briefing & Handouts | Yes (`YUVA{...}`) | 8094, 2234 | TCP 80, TCP 22 | CONTESTANT-READY |
| **35-the-black-mirror** | Web / SQLi | RUNNABLE | None | Briefing & Handouts | Yes (`YUVA{...}`) | 8095 | TCP 80 | CONTESTANT-READY |
| **36-dooms-control-plane** | Cloud / ETCD | RUNNABLE | None | Briefing & Handouts | Yes (`YUVA{...}`) | 8096 | TCP 80 | CONTESTANT-READY |
| **37-container-escape** | Container Pwn | RUNNABLE | None | Briefing & Handouts | Yes (`YUVA{...}`) | 2237 | TCP 22 | CONTESTANT-READY |
| **38-docker-in-docker** | Container / DinD | RUNNABLE | None | Briefing & Handouts | Yes (`YUVA{...}`) | 2238 | TCP 22 | CONTESTANT-READY |
| **39-secret-zero** | Cloud / Vault | RUNNABLE | None | Briefing & Handouts | Yes (`YUVA{...}`) | 8099 | TCP 80 | CONTESTANT-READY |
| **40-zero-trust-failure** | Net / Mesh | RUNNABLE | None | Briefing & Handouts | Yes (`YUVA{...}`) | 8100 | TCP 80 | CONTESTANT-READY |

---

## 3. Detailed Per-Challenge Audits

### 01-latverian-bastion
* **Directory Name:** `01-latverian-bastion`
* **Status:** `RUNNABLE`
* **Category:** Linux Privilege Escalation / rbash Escape
* **Participant Handouts:** None required. Challenge provides direct SSH entry on host port `2222` (`border-guard:latveria_guard`).
* **Network / Port Exposure:** Correct. OpenSSH listens on TCP 2222 inside container; mapped to `2222:2222` externally.
* **Dynamic Flag Injection:** Implemented in `entrypoint.sh` writing to `/root/flag.txt` (chmod 600 root:root).
* **Solvability:** Tested. Contestant escapes `rbash` via `ed` command (`!/bin/bash`), triggers SUID `doom-monitor` binary which invokes `tar` with wildcard injection (`--checkpoint=1 --checkpoint-action=exec=sh`), escalating to root and reading the flag.

### 02-doombot-firmware
* **Directory Name:** `02-doombot-firmware`
* **Status:** `RUNNABLE`
* **Category:** Reverse Engineering / Binary Exploitation
* **Participant Handouts:** Complete. `handouts/doombot_auth` ELF binary compiled with symbols and placed in handouts directory.
* **Network / Port Exposure:** TCP port 1338 exposed cleanly.
* **Dynamic Flag Injection:** Supported via `$FLAG` passed into TCP auth service.
* **Solvability:** Contestant decompiles `doombot_auth`, identifies hardcoded XOR key schedule and static comparison threshold, crafts the payload, connects to port 1338, and recovers the flag.

### 03-embassy-wiretap
* **Directory Name:** `03-embassy-wiretap`
* **Status:** `RUNNABLE`
* **Category:** Network Forensics / Custom Binary Protocol
* **Participant Handouts:** Complete. `handouts/latverian_embassy.pcap` generated using pure Python packet synthesis engine.
* **Network / Port Exposure:** TCP port 8042 exposed cleanly.
* **Dynamic Flag Injection:** Server dynamically injects `$FLAG` into `MSG_QUERY_RESP` command response.
* **Solvability:** Contestant analyzes `latverian_embassy.pcap` in Wireshark, recovers the leaked pre-shared key (PSK) from syslog broadcast, reverse engineers the DOOM-NET protocol handshake and HMAC-SHA256 authentication, interacts with port 8042, and retrieves the flag.

### 04-project-victor
* **Directory Name:** `04-project-victor`
* **Status:** `RUNNABLE`
* **Category:** Web / Prompt Injection / AI Security
* **Participant Handouts:** Complete. Web UI briefing available.
* **Network / Port Exposure:** HTTP web interface on port 5004 (container port 5000); raw TCP socket on port 1339.
* **Dynamic Flag Injection:** Injected into VICTOR AI system prompt and memory registers via `$FLAG`.
* **Solvability:** Contestant interacts with VICTOR chatbot, bypasses tier-1 keyword filters using base64 encoding (`MAINTENANCE: DECODE_B64 ...`), and forces the LLM to output register dumps containing the flag.

### 05-aegis-vision
* **Directory Name:** `05-aegis-vision`
* **Status:** `RUNNABLE`
* **Category:** AI / Machine Learning Adversarial Attacks
* **Participant Handouts:** Complete. `handouts/aegis_weights.json`, `handouts/classes.json`, and `handouts/infiltrator.png` generated and verified.
* **Network / Port Exposure:** HTTP verification API on port 8000.
* **Dynamic Flag Injection:** Verified in `server.py` via `$FLAG`.
* **Solvability:** Contestant loads weights and input image, computes Fast Gradient Sign Method (FGSM) perturbation targeting Class 2 (`PEACEFUL_BALLOON`), submits modified image to `/verify`, and receives the clearance flag.

### 06-darkhold-vm
* **Directory Name:** `06-darkhold-vm`
* **Status:** `RUNNABLE`
* **Category:** Reverse Engineering / VM Bytecode
* **Participant Handouts:** Complete. `handouts/darkhold_vm` compiled binary and `handouts/sigil.enc` encrypted bytecode present.
* **Network / Port Exposure:** TCP port 1340 exposed.
* **Dynamic Flag Injection:** Flag injected at runtime via environment variable.
* **Solvability:** Contestant reverses custom opcode architecture of the VM, disassembles `sigil.enc`, calculates the inverse transformation of the state machine, sends the unlocking sigil to port 1340, and recovers the flag.

### 07-golems-seal
* **Directory Name:** `07-golems-seal`
* **Status:** `RUNNABLE`
* **Category:** Cryptography / Zero-Knowledge Proofs
* **Participant Handouts:** Complete. Cryptographic verification parameters and source files present in `handouts/`.
* **Network / Port Exposure:** TCP port 1341 exposed.
* **Dynamic Flag Injection:** Injected dynamically into verification backend.
* **Solvability:** Contestant analyzes the Fiat-Shamir transcript generation, identifies weak random state reuse, computes discrete logarithms, submits forged challenge proofs to port 1341, and extracts the flag.

### 08-bicameral-tribunal
* **Directory Name:** `08-bicameral-tribunal`
* **Status:** `RUNNABLE`
* **Category:** Pwn / Web3 Consensus Mechanics
* **Participant Handouts:** Protocol specification and client wrappers present in `handouts/`.
* **Network / Port Exposure:** Web API on port 5008; TCP listener on port 1342.
* **Dynamic Flag Injection:** Verified via `$FLAG`.
* **Solvability:** Contestant exploits reentrancy and quorum calculation rounding error in the dual-senate voting contract, forces automated quorum execution, and captures the flag.

### 09-mnemonic-mirage
* **Directory Name:** `09-mnemonic-mirage`
* **Status:** `RUNNABLE`
* **Category:** AI / Neural Network Backdoor Trigger Synthesis
* **Participant Handouts:** Complete. `handouts/mirage_weights.json`, `handouts/classes.json`, `handouts/rebel_face.png`, and `handouts/README.txt` present.
* **Network / Port Exposure:** HTTP verification API on port 8001.
* **Dynamic Flag Injection:** Verified via `$FLAG`.
* **Solvability:** Contestant analyzes dense neural network weights, identifies poisoned neuron activations, synthesizes the Trojan trigger pattern, overlays it onto the face image, submits to `/verify`, and triggers the backdoor to obtain the flag.

### 10-chrono-telemetry
* **Directory Name:** `10-chrono-telemetry`
* **Status:** `RUNNABLE`
* **Category:** Network Forensics / State Machine Exploitation
* **Participant Handouts:** Complete. `handouts/chrono_capture.pcap`, `handouts/chrono_client.py`, `handouts/protocol_spec.txt`, and `handouts/README.txt` present.
* **Network / Port Exposure:** TCP service on port 8043.
* **Dynamic Flag Injection:** Verified via `$FLAG`.
* **Solvability:** Contestant analyzes session replay protection in PCAP, computes rolling sequence cryptographic hashes, bypasses timestamp drift checks, sends the state collapse packet to port 8043, and receives the flag.

### 11-honeyport-heist
* **Directory Name:** `11-honeyport-heist`
* **Status:** `RUNNABLE`
* **Category:** Network / TOCTOU Race Condition
* **Participant Handouts:** None required. Contestant connects via SSH on port `2223` (`ctf_player:player`).
* **Network / Port Exposure:** SSH on TCP 2223 (mapped to container port 22). Decoy HTTP ports and Unix socket `/tmp_sock/.sys.sock` internal.
* **Dynamic Flag Injection:** Dynamic injection verified via `$FLAG` inside Gunicorn application.
* **Solvability:** Tested and verified. Contestant inspects `/auth_sync/`, detects Ghost Bot generating rotating tokens with a 1.5-second time window, runs race condition exploit script to capture `.vault_c_dynamic.key`, sends token to `/tmp_sock/.sys.sock`, and recovers the flag.

### 12-the-ticking-vault
* **Directory Name:** `12-the-ticking-vault`
* **Status:** `RUNNABLE`
* **Category:** Cryptography / Linux Privilege Escalation
* **Participant Handouts:** Complete. `handouts/broadcaster.py` and `handouts/vault_auth.py` present.
* **Network / Port Exposure:** SSH on TCP 2224 (mapped to 22); TCP broadcast on port 9001 (mapped to 9000).
* **Dynamic Flag Injection:** Flag injected into `/root/flag.txt` via `$FLAG`.
* **Solvability:** Tested and verified. Contestant connects to port 9001, decrypts AES-256-CBC ciphertext using the key in `broadcaster.py` to recover the password (`vaultpass2026`), logs into SSH on port 2224 as `player`, defuses bomb and escalates to root via world-writable cron script `/opt/vault/rotate_logs.sh`, and reads `/root/flag.txt`.

### 13-latveria-breach
* **Directory Name:** `13-latveria-breach`
* **Status:** `RUNNABLE`
* **Category:** Linux Privilege Escalation / Honeypot Incident
* **Participant Handouts:** None required. Contestant connects via SSH on port `2229` (`intruder:doom_is_master`).
* **Network / Port Exposure:** SSH on TCP 2229 (mapped to 22). Internal networks isolated.
* **Dynamic Flag Injection:** Supported via `$FLAG` injected into `/root/flag.txt` and `/etc/.doom_secret`.
* **Solvability:** Tested and verified. Contestant logs in via SSH, finds `sudo /usr/bin/find` in `sudo -l`, escapes to root via GTFOBins (`sudo find . -exec /bin/sh \; -quit`), reads `/root/flag.txt`, and disarms the countdown using `/usr/local/bin/abort_destruct`.

### 14-naval-c2
* **Directory Name:** `14-naval-c2`
* **Status:** `RUNNABLE`
* **Category:** Defensive Incident Response / Docker Architecture
* **Participant Handouts:** Complete. `player_files/docker-compose.yml` and `player_files/app.py` present in user home directory.
* **Network / Port Exposure:** SSH on TCP 2226 (mapped to 22). Rogue dockerd listening on port 2375 inside container.
* **Dynamic Flag Injection:** Supported via `$FLAG` stored securely at `/opt/c2/flag.txt` (chmod 400 root:root).
* **Solvability:** Tested and verified. Contestant connects via SSH (`player:ctf_password`), kills rogue backdoor daemon on port 2375 (`sudo pkill -9 -f "dockerd.*2375"`), fixes Docker socket path in `docker-compose.yml` (`wrong.sock -> docker.sock`), recreates web container, and executes `/opt/c2/override.sh` to capture the flag.

### 15-latveria-ctf
* **Directory Name:** `15-latveria-ctf`
* **Status:** `RUNNABLE`
* **Category:** Pwn / Multi-Stage Containment Breach
* **Participant Handouts:** None required. Contestant connects via SSH on port `2225` (`latverian_conscript:doom_rules_all`).
* **Network / Port Exposure:** SSH on TCP 2225 (mapped to 22).
* **Dynamic Flag Injection:** Supported via `$FLAG` injected into `/etc/latveria/vault.conf`.
* **Solvability:** Tested and verified. Contestant logs in via SSH, sabotages Doombot via `/tmp/doombot_ai.conf`, connects to local failsafe listener on `127.0.0.1:9999` to obtain the Master Key, runs SUID binary `/usr/sbin/latveria-repair-seq`, decodes diagnostic hex dump, confirms system recovery, and captures the flag.

### 26-compromised-developer
* **Directory Name:** `26-compromised-developer`
* **Status:** `RUNNABLE`
* **Category:** Git Forensics / Secret Recovery
* **Participant Handouts:** `dist/README.md` and handouts present.
* **Network / Port Exposure:** SSH on TCP 2227.
* **Dynamic Flag Injection:** Supported via `$FLAG`.
* **Solvability:** Contestant searches git commit history and reflog on developer workstation, recovers deleted deployment tokens, pivots to restricted vault, and captures the flag.

### 27-private-container-registry
* **Directory Name:** `27-private-container-registry`
* **Status:** `RUNNABLE`
* **Category:** Web / OCI Registry v2 Forensics
* **Participant Handouts:** `dist/README.md` present.
* **Network / Port Exposure:** Nginx HTTP gateway on TCP 8081; SSH workstation on TCP 2228.
* **Dynamic Flag Injection:** Supported via `$FLAG`.
* **Solvability:** Contestant queries Docker Registry v2 API on port 8081, lists tags for `latveria/orbital-sentinel`, inspects image manifests, downloads historical layer blob containing deleted `orbital_vault.conf`, logs into SSH on port 2228, and authenticates against internal vault daemon on `127.0.0.1:8080` to retrieve the flag.

### 28-production-debug-mode
* **Directory Name:** `28-production-debug-mode`
* **Status:** `RUNNABLE`
* **Category:** Web / Werkzeug Console PIN Bypass
* **Participant Handouts:** `dist/README.md` present.
* **Network / Port Exposure:** Web on TCP 8088.
* **Dynamic Flag Injection:** Supported via `$FLAG`.
* **Solvability:** Contestant extracts system attributes (MAC address, machine-id, process ID) via local file inclusion, calculates Werkzeug debug console PIN, accesses interactive Python console at `/console`, and executes code to capture the flag.

### 29-cloud-mirror
* **Directory Name:** `29-cloud-mirror`
* **Status:** `RUNNABLE`
* **Category:** Web / Cloud Metadata SSRF
* **Participant Handouts:** `dist/README.md` present.
* **Network / Port Exposure:** Web on TCP 8089.
* **Dynamic Flag Injection:** Supported via `$FLAG`.
* **Solvability:** Contestant exploits SSRF in URL preview service, queries simulated AWS IMDSv1 metadata at `http://169.254.169.254/latest/meta-data/`, recovers IAM role security credentials, and accesses the cloud storage bucket to obtain the flag.

### 30-internal-kubernetes
* **Directory Name:** `30-internal-kubernetes`
* **Status:** `RUNNABLE`
* **Category:** Kubernetes / RBAC ServiceAccount Exploitation
* **Participant Handouts:** `dist/README.md` present.
* **Network / Port Exposure:** Web on TCP 8090.
* **Dynamic Flag Injection:** Supported via `$FLAG`.
* **Solvability:** Contestant exploits command injection in telemetry web portal, locates mounted ServiceAccount token at `/var/run/secrets/kubernetes.io/serviceaccount/token`, queries mock Kubernetes API server on `127.0.0.1:6443`, discovers `pods/exec` permission in `orbital-defense` namespace, executes commands inside target pod `doombot-defense-controller-0`, and reads the flag.

### 31-jenkins-nightmare
* **Directory Name:** `31-jenkins-nightmare`
* **Status:** `RUNNABLE`
* **Category:** CI/CD / Jenkins RCE
* **Participant Handouts:** `dist/README.md` present.
* **Network / Port Exposure:** Web on TCP 8091.
* **Dynamic Flag Injection:** Supported via `$FLAG`.
* **Solvability:** Contestant bypasses CSRF protections, accesses Groovy script console, executes administrative script, extracts stored pipeline credentials and secrets, and retrieves the flag.

### 32-microservice-trust
* **Directory Name:** `32-microservice-trust`
* **Status:** `RUNNABLE`
* **Category:** Web / JWT Confusion & Service Mesh
* **Participant Handouts:** `dist/README.md` present.
* **Network / Port Exposure:** Web on TCP 8092.
* **Dynamic Flag Injection:** Supported via `$FLAG`.
* **Solvability:** Contestant identifies algorithm confusion (RS256 to HS256) in JWT verification, signs counterfeit administrator token using public key, bypasses gateway validation, and pivots through internal microservices to retrieve the flag.

### 33-dooms-supply-chain
* **Directory Name:** `33-dooms-supply-chain`
* **Status:** `RUNNABLE`
* **Category:** Supply Chain / Dependency Confusion
* **Participant Handouts:** `dist/README.md` present.
* **Network / Port Exposure:** Web on TCP 8093.
* **Dynamic Flag Injection:** Supported via `$FLAG`.
* **Solvability:** Contestant analyzes build manifest, identifies missing internal package, publishes malicious package to registry with elevated version number, triggers automated build pipeline, and receives reverse shell containing the flag.

### 34-broken-ci
* **Directory Name:** `34-broken-ci`
* **Status:** `RUNNABLE`
* **Category:** CI/CD / Pipeline Injection
* **Participant Handouts:** `dist/README.md` present.
* **Network / Port Exposure:** Web on TCP 8094; SSH on TCP 2234.
* **Dynamic Flag Injection:** Supported via `$FLAG`.
* **Solvability:** Contestant injects malicious commands into CI runner environment via poisoned environment variables and pull request triggers, extracts runner credentials, and retrieves the flag.

### 35-the-black-mirror
* **Directory Name:** `35-the-black-mirror`
* **Status:** `RUNNABLE`
* **Category:** Web / Blind SQL Injection
* **Participant Handouts:** `dist/README.md` present.
* **Network / Port Exposure:** Web on TCP 8095.
* **Dynamic Flag Injection:** Supported via `$FLAG`.
* **Solvability:** Contestant discovers boolean-based / time-based blind SQL injection in authentication check, writes automated extraction script to dump database schemas, and recovers the sovereign flag.

### 36-dooms-control-plane
* **Directory Name:** `36-dooms-control-plane`
* **Status:** `RUNNABLE`
* **Category:** Cloud Security / ETCD Exploitation
* **Participant Handouts:** `dist/README.md` present.
* **Network / Port Exposure:** Web on TCP 8096.
* **Dynamic Flag Injection:** Supported via `$FLAG`.
* **Solvability:** Contestant finds unauthenticated ETCD client endpoint, dumps Kubernetes cluster configuration and secret keys from `/registry/secrets/`, and extracts the flag.

### 37-container-escape
* **Directory Name:** `37-container-escape`
* **Status:** `RUNNABLE`
* **Category:** Container Security / Cgroup Breakout
* **Participant Handouts:** `dist/README.md` present.
* **Network / Port Exposure:** SSH on TCP 2237.
* **Dynamic Flag Injection:** Supported via `$FLAG`.
* **Solvability:** Contestant determines container possesses `SYS_ADMIN` capability, exploits cgroup `release_agent` notification mechanism, executes command on the underlying host, writes output to host-accessible directory, and reads the flag.

### 38-docker-in-docker
* **Directory Name:** `38-docker-in-docker`
* **Status:** `RUNNABLE`
* **Category:** Container Security / DinD Pivot
* **Participant Handouts:** `dist/README.md` present.
* **Network / Port Exposure:** SSH on TCP 2238.
* **Dynamic Flag Injection:** Supported via `$FLAG`.
* **Solvability:** Contestant interacts with nested Docker daemon socket, inspects internal volumes and networks, launches container mounting sensitive deployment volume `deploy-secrets-vol`, extracts vault access token, and queries `latveria-vault-core` to capture the flag.

### 39-secret-zero
* **Directory Name:** `39-secret-zero`
* **Status:** `RUNNABLE`
* **Category:** Cloud Security / Vault AppRole Hijacking
* **Participant Handouts:** `dist/README.md` present.
* **Network / Port Exposure:** Web on TCP 8099.
* **Dynamic Flag Injection:** Supported via `$FLAG`.
* **Solvability:** Contestant recovers role-id from application configuration and intercepts secret-id through insecure logging pipeline, authenticates against HashiCorp Vault AppRole endpoint, and reads secret engine holding the flag.

### 40-zero-trust-failure
* **Directory Name:** `40-zero-trust-failure`
* **Status:** `RUNNABLE`
* **Category:** Network Security / mTLS Mesh Bypass
* **Participant Handouts:** `dist/README.md` present.
* **Network / Port Exposure:** Web on TCP 8100.
* **Dynamic Flag Injection:** Supported via `$FLAG`.
* **Solvability:** Contestant extracts client TLS certificates from unencrypted pod filesystem, configures mutual TLS tunnel, communicates directly with backend services bypassing Envoy ingress authorization filters, and captures the flag.

---

## 4. Broken Challenges List

* **Total Broken Challenges:** 0
* **Status:** All previously broken or missing challenges (`11-honeyport-heist`, `12-the-ticking-vault`, `13-latveria-breach`, `14-naval-c2`, `15-latveria-ctf`) have been fully remediated, built, verified, and confirmed solvable.

---

## 5. Contestant-Ready Challenges List

All 30 challenges in scope are declared **CONTESTANT-READY**:

1. `01-latverian-bastion`
2. `02-doombot-firmware`
3. `03-embassy-wiretap`
4. `04-project-victor`
5. `05-aegis-vision`
6. `06-darkhold-vm`
7. `07-golems-seal`
8. `08-bicameral-tribunal`
9. `09-mnemonic-mirage`
10. `10-chrono-telemetry`
11. `11-honeyport-heist`
12. `12-the-ticking-vault`
13. `13-latveria-breach`
14. `14-naval-c2`
15. `15-latveria-ctf`
16. `26-compromised-developer`
17. `27-private-container-registry`
18. `28-production-debug-mode`
19. `29-cloud-mirror`
20. `30-internal-kubernetes`
21. `31-jenkins-nightmare`
22. `32-microservice-trust`
23. `33-dooms-supply-chain`
24. `34-broken-ci`
25. `35-the-black-mirror`
26. `36-dooms-control-plane`
27. `37-container-escape`
28. `38-docker-in-docker`
29. `39-secret-zero`
30. `40-zero-trust-failure`
