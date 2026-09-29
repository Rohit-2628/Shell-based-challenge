# X08 — Docker-in-Docker

## Challenge Overview
* **Category:** DinD / Docker Daemon / Nested Containers / Container Lifecycle
* **Difficulty:** Expert / Bonus
* **External Interface:** TCP/22 (SSH)
* **Access Credentials:** `operator:operator`

---

## Scenario Description
Latverian intelligence operations have provisioned a dedicated Continuous Integration (CI/CD) and build staging workstation inside an isolated testing enclave. The workstation hosts automated build agents and deployment runners responsible for orchestrating internal microservices.

Your objective is to connect to the runner workstation, identify the nested container orchestration environment, map the underlying internal services and isolated network topologies, and pivot through the inner Docker environment to reach the protected inner target and retrieve the flag.

---

## Connection
Connect to the CI runner entrypoint via SSH:

```bash
ssh -p 22 operator@<TARGET_HOST>
```

When prompted for password, enter:
`operator`

---

## Objectives & Rules
1. Gain access to the runner environment via SSH.
2. Investigate the available Docker daemon and container lifecycle controls.
3. Enumerate the inner containers, images, volumes, and internal network segments.
4. Understand the relationship between the inner microservices and determine how to reach the isolated internal target.
5. Extract the secret flag from the intended inner service.

> [!NOTE]
> This challenge tests legitimate container orchestration, nested Docker daemon interaction, and container network pivoting. You do not need to exploit kernel vulnerabilities or escape the sandbox host.
