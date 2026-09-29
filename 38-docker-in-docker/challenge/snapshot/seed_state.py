#!/usr/bin/env python3
"""
Latverian DinD Environment Seeder
Initializes inner Docker networks, builds/loads images, creates volumes,
and instantiates the inner container mesh with dynamic team flag configuration.
"""

import os
import sys
import time
import subprocess
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
INNER_DIR = BASE_DIR / "inner_services"

def run_cmd(cmd, check=True, capture=True):
    print(f"[*] Executing: {cmd}")
    res = subprocess.run(cmd, shell=True, text=True, capture_output=capture)
    if check and res.returncode != 0:
        print(f"[-] Error executing '{cmd}':\nSTDOUT: {res.stdout}\nSTDERR: {res.stderr}")
        raise RuntimeError(f"Command failed: {cmd}")
    return res.stdout.strip() if capture else ""

def wait_for_docker(max_retries=30, delay=1):
    print("[*] Waiting for inner Docker daemon to become responsive...")
    for i in range(max_retries):
        res = subprocess.run("docker info", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if res.returncode == 0:
            print("[+] Inner Docker daemon is ready!")
            return True
        time.sleep(delay)
    raise TimeoutError("Inner Docker daemon failed to start in time.")

def seed_environment(flag=None, auth_token=None):
    if not flag:
        flag = os.environ.get("FLAG", "YUVA{d1nd_n3st3d_d0ck3r_d43m0n_p1v0t_x08_7f8e9a2b}")
    if not auth_token:
        auth_token = os.environ.get("VAULT_AUTH_TOKEN", "LV-VAULT-TOKEN-9c48e2a1b730f56d")

    print(f"[*] Seeding inner Docker environment with Flag: {flag[:12]}... / Token: {auth_token[:10]}...")

    # 1. Clean up any pre-existing containers/networks/volumes
    print("[*] Cleaning previous state...")
    subprocess.run("docker rm -f $(docker ps -aq) 2>/dev/null || true", shell=True)
    subprocess.run("docker network prune -f 2>/dev/null || true", shell=True)
    subprocess.run("docker volume prune -f 2>/dev/null || true", shell=True)

    # 2. Create inner networks
    print("[*] Creating internal network topologies...")
    run_cmd("docker network create --driver bridge --subnet 172.28.10.0/24 ci-frontend-net")
    # Isolated internal network (no external route)
    run_cmd("docker network create --driver bridge --internal --subnet 172.28.20.0/24 vault-internal-net")

    # 3. Create volumes
    print("[*] Creating pipeline volumes...")
    run_cmd("docker volume create deploy-secrets-vol")

    # 4. Build inner images
    print("[*] Building/loading inner service images...")
    
    # Vault Core Image
    vault_dir = INNER_DIR / "vault_core"
    if vault_dir.exists():
        run_cmd(f"docker build -t latveria/vault-core:v2.5-enterprise '{vault_dir}'")
    
    # API Gateway Image
    gateway_dir = INNER_DIR / "api_gateway"
    if gateway_dir.exists():
        run_cmd(f"docker build -t latveria/api-gateway:v1.1 '{gateway_dir}'")
        
    # CI Agent Image
    ci_dir = INNER_DIR / "ci_agent"
    if ci_dir.exists():
        run_cmd(f"docker build -t latveria/ci-agent:v3.2 '{ci_dir}'")

    # Admin CLI Image
    admin_dir = INNER_DIR / "admin_cli"
    if admin_dir.exists():
        run_cmd(f"docker build -t latveria/admin-cli:v1.0 '{admin_dir}'")

    # 5. Populate volume with auth token secret
    print("[*] Populating deployment configuration and secrets...")
    # Use ephemeral container to write to deploy-secrets-vol
    token_write_cmd = (
        f"docker run --rm -v deploy-secrets-vol:/secrets latveria/admin-cli:v1.0 "
        f"sh -c 'echo \"{auth_token}\" > /secrets/vault_access_token.conf && chmod 0644 /secrets/vault_access_token.conf'"
    )
    run_cmd(token_write_cmd)

    # 6. Instantiate running containers
    print("[*] Starting inner services...")

    # Start Vault Core on isolated network
    run_cmd(
        f"docker run -d --name latveria-vault-core "
        f"--network vault-internal-net --ip 172.28.20.5 "
        f"-e VAULT_AUTH_TOKEN='{auth_token}' "
        f"-e FLAG='{flag}' "
        f"--restart always latveria/vault-core:v2.5-enterprise"
    )

    # Start API Gateway on frontend network
    run_cmd(
        f"docker run -d --name latveria-api-gateway "
        f"--network ci-frontend-net --ip 172.28.10.2 "
        f"-e VAULT_SERVICE_DISCOVERY='latveria-vault-core.vault-internal-net:8443' "
        f"--restart always latveria/api-gateway:v1.1"
    )

    # Start CI Agent Worker on frontend network with mounted secret volume
    run_cmd(
        f"docker run -d --name ci-pipeline-worker "
        f"--network ci-frontend-net --ip 172.28.10.10 "
        f"-v deploy-secrets-vol:/secrets:ro "
        f"-e PIPELINE_STAGE=PRODUCTION_STAGING "
        f"-e TARGET_SERVICE=latveria-vault-core "
        f"--restart always latveria/ci-agent:v3.2"
    )

    print("[+] DinD Environment seeding complete!")
    print("[*] Active Containers:")
    print(run_cmd("docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Networks}}'"))

if __name__ == "__main__":
    wait_for_docker()
    custom_flag = sys.argv[1] if len(sys.argv) > 1 else None
    custom_token = sys.argv[2] if len(sys.argv) > 2 else None
    seed_environment(custom_flag, custom_token)
