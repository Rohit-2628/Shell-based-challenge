#!/usr/bin/env python3
"""
Generate synthetic OCI / Docker Registry v2 repositories, image layers, configs, and manifests for D27.
This script produces authentic Docker v2 Schema 2 / OCI compliant layer blobs (tar.gz),
image config blobs (json), and manifests with realistic Latverian build history.
"""

import gzip
import hashlib
import io
import json
import os
import shutil
import tarfile
import time
from pathlib import Path

REGISTRY_ROOT = Path("/var/lib/latveria-registry")

def create_tar_gz_blob(files_dict: dict) -> tuple[bytes, str, int, str]:
    """
    Creates a tar.gz archive from a dictionary of {file_path: file_content_str_or_bytes}.
    Returns (gzipped_bytes, sha256_digest, size, diff_id_uncompressed_sha256).
    """
    tar_buffer = io.BytesIO()
    with tarfile.open(fileobj=tar_buffer, mode="w") as tar:
        for fpath, content in files_dict.items():
            if isinstance(content, str):
                data = content.encode("utf-8")
            else:
                data = content
            
            tarinfo = tarfile.TarInfo(name=fpath.lstrip("/"))
            tarinfo.size = len(data)
            tarinfo.mtime = int(time.time()) - 86400 * 30  # realistic past date
            tarinfo.mode = 0o644
            tarinfo.uname = "root"
            tarinfo.gname = "root"
            tar.addfile(tarinfo, io.BytesIO(data))
            
    uncompressed_bytes = tar_buffer.getvalue()
    diff_id = "sha256:" + hashlib.sha256(uncompressed_bytes).hexdigest()
    
    gz_buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=gz_buffer, mode="wb", mtime=0) as gz:
        gz.write(uncompressed_bytes)
        
    gzipped_bytes = gz_buffer.getvalue()
    blob_digest = "sha256:" + hashlib.sha256(gzipped_bytes).hexdigest()
    blob_size = len(gzipped_bytes)
    
    return gzipped_bytes, blob_digest, blob_size, diff_id

def create_image_config(history: list, diff_ids: list, env: list = None, cmd: list = None) -> tuple[bytes, str, int]:
    """
    Creates an OCI / Docker Container Image Config JSON.
    Returns (config_bytes, sha256_digest, size).
    """
    config_dict = {
        "architecture": "amd64",
        "os": "linux",
        "config": {
            "Env": env or [
                "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
                "LATVERIA_ENV=production"
            ],
            "Cmd": cmd or ["python3", "/app/main.py"],
            "WorkingDir": "/app"
        },
        "rootfs": {
            "type": "layers",
            "diff_ids": diff_ids
        },
        "history": history
    }
    
    config_json = json.dumps(config_dict, indent=2).encode("utf-8")
    config_digest = "sha256:" + hashlib.sha256(config_json).hexdigest()
    config_size = len(config_json)
    
    return config_json, config_digest, config_size

def create_manifest(config_digest: str, config_size: int, layers_info: list) -> tuple[bytes, str, int]:
    """
    Creates a Docker Image Manifest v2, Schema 2.
    Returns (manifest_bytes, sha256_digest, size).
    """
    manifest_dict = {
        "schemaVersion": 2,
        "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
        "config": {
            "mediaType": "application/vnd.docker.container.image.v1+json",
            "size": config_size,
            "digest": config_digest
        },
        "layers": [
            {
                "mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
                "size": l_size,
                "digest": l_digest
            }
            for l_digest, l_size in layers_info
        ]
    }
    
    manifest_json = json.dumps(manifest_dict, indent=2).encode("utf-8")
    manifest_digest = "sha256:" + hashlib.sha256(manifest_json).hexdigest()
    manifest_size = len(manifest_json)
    
    return manifest_json, manifest_digest, manifest_size

def build_all_repositories(target_dir: Path):
    """
    Generates all repositories, blobs, manifests, and catalog files in target_dir.
    """
    blobs_dir = target_dir / "blobs"
    repos_dir = target_dir / "repositories"
    
    blobs_dir.mkdir(parents=True, exist_ok=True)
    repos_dir.mkdir(parents=True, exist_ok=True)
    
    saved_blobs = set()
    
    def save_blob(digest: str, data: bytes):
        clean_name = digest.replace("sha256:", "")
        blob_path = blobs_dir / clean_name
        if not blob_path.exists():
            blob_path.write_bytes(data)
        saved_blobs.add(digest)
        
    def save_manifest(repo_name: str, tag: str, manifest_bytes: bytes, manifest_digest: str):
        manifests_dir = repos_dir / repo_name / "manifests"
        manifests_dir.mkdir(parents=True, exist_ok=True)
        # Save by tag and by digest
        (manifests_dir / tag).write_bytes(manifest_bytes)
        (manifests_dir / manifest_digest.replace("sha256:", "")).write_bytes(manifest_bytes)
        
        # Save in blobs as well
        save_blob(manifest_digest, manifest_bytes)

    # -------------------------------------------------------------
    # 1. Base Linux Layer (shared across versions)
    # -------------------------------------------------------------
    base_files = {
        "/etc/os-release": "NAME=\"Latveria Linux\"\nID=latveria\nVERSION_ID=\"4.2\"\nPRETTY_NAME=\"Latverian State OS v4.2\"\n",
        "/etc/issue": "Latveria Orbital Defense Systems \\n \\l\n",
        "/bin/healthcheck": "#!/bin/sh\necho 'OK'\n",
        "/etc/latveria.conf": "[SYSTEM]\nDOMAIN=latveria.internal\nGOVERNOR=DOOM\n"
    }
    base_blob, base_digest, base_size, base_diff_id = create_tar_gz_blob(base_files)
    save_blob(base_digest, base_blob)

    # -------------------------------------------------------------
    # 2. REPOSITORY: latveria/orbital-sentinel
    # -------------------------------------------------------------
    repo_orbital = "latveria/orbital-sentinel"
    
    # ------------------ VERSION 1.0.0 (INTENDED TARGET WITH HISTORICAL SECRET) ------------------
    app_v1_files = {
        "/app/sentinel_core.py": "# Latveria Orbital Sentinel Core v1.0.0\nimport sys\nprint('Sentinel Core Initialized')\n",
        "/app/requirements.txt": "requests==2.28.1\nurllib3==1.26.12\n",
        "/app/VERSION": "1.0.0-prototype\n"
    }
    app_v1_blob, app_v1_digest, app_v1_size, app_v1_diff_id = create_tar_gz_blob(app_v1_files)
    save_blob(app_v1_digest, app_v1_blob)
    
    # Secret configuration layer in v1.0.0
    secret_v1_files = {
        "/app/config/orbital_vault.conf": """# ==============================================================================
# LATVERIAN ORBITAL DEFENSE MESH - SENTINEL NODE CONFIGURATION
# ENVIRONMENT: STAGING / PROTOTYPE VAULT INTEGRATION
# ==============================================================================

[SENTINEL_NODE]
NODE_ID = DOOM-ORBITAL-ALPHA-01
REGION = GEO-STATIONARY-LATVERIA
DEFENSE_PROTOCOL = ZEPHYR-99

[INTERNAL_VAULT]
VAULT_ENDPOINT = http://127.0.0.1:8080/api/v1/vault/override
LATVERIAN_INTERNAL_TOKEN = latv_vault_sec_89f2a481c90e37b2d5140e678a119c8f
LATVERIAN_CALLER_ID = orbital_defense_service_master
LATVERIAN_GATEWAY_ACTION = OVERRIDE_DEFENSE_GRID

# NOTICE: Do not commit plaintext vault tokens to production releases.
# Deprecated as of Security Audit SEC-2026-9901.
"""
    }
    secret_v1_blob, secret_v1_digest, secret_v1_size, secret_v1_diff_id = create_tar_gz_blob(secret_v1_files)
    save_blob(secret_v1_digest, secret_v1_blob)
    
    history_v1 = [
        {"created": "2026-06-01T10:00:00Z", "created_by": "/bin/sh -c #(nop) ADD file:latveria_base.tar.gz in /"},
        {"created": "2026-06-05T14:22:10Z", "created_by": "COPY app/ /app/"},
        {"created": "2026-06-10T09:15:33Z", "created_by": "COPY config/orbital_vault.conf /app/config/orbital_vault.conf"}
    ]
    diff_ids_v1 = [base_diff_id, app_v1_diff_id, secret_v1_diff_id]
    layers_v1 = [(base_digest, base_size), (app_v1_digest, app_v1_size), (secret_v1_digest, secret_v1_size)]
    
    cfg_v1_json, cfg_v1_digest, cfg_v1_size = create_image_config(history_v1, diff_ids_v1, cmd=["python3", "/app/sentinel_core.py"])
    save_blob(cfg_v1_digest, cfg_v1_json)
    
    man_v1_json, man_v1_digest, man_v1_size = create_manifest(cfg_v1_digest, cfg_v1_size, layers_v1)
    save_manifest(repo_orbital, "v1.0.0", man_v1_json, man_v1_digest)

    # ------------------ VERSION 2.1.0 (MIGRATION BUILD - SECRET PURGED) ------------------
    app_v2_files = {
        "/app/sentinel_core.py": "# Latveria Orbital Sentinel Core v2.1.0\n# Dynamic Vault Integration\nimport os\nprint('Sentinel Core v2 Initialized')\n",
        "/app/VERSION": "2.1.0-release\n",
        "/app/config/sentinel.json": "{\"mode\": \"distributed\", \"vault_enabled\": true}\n"
    }
    app_v2_blob, app_v2_digest, app_v2_size, app_v2_diff_id = create_tar_gz_blob(app_v2_files)
    save_blob(app_v2_digest, app_v2_blob)
    
    # Whiteout layer simulating deletion of old config
    cleanup_v2_files = {
        "/app/config/.wh.orbital_vault.conf": ""
    }
    cleanup_v2_blob, cleanup_v2_digest, cleanup_v2_size, cleanup_v2_diff_id = create_tar_gz_blob(cleanup_v2_files)
    save_blob(cleanup_v2_digest, cleanup_v2_blob)
    
    history_v2 = [
        {"created": "2026-06-01T10:00:00Z", "created_by": "/bin/sh -c #(nop) ADD file:latveria_base.tar.gz in /"},
        {"created": "2026-07-01T11:00:00Z", "created_by": "COPY app/ /app/"},
        {"created": "2026-07-02T16:40:12Z", "created_by": "RUN rm -f /app/config/orbital_vault.conf"}
    ]
    diff_ids_v2 = [base_diff_id, app_v2_diff_id, cleanup_v2_diff_id]
    layers_v2 = [(base_digest, base_size), (app_v2_digest, app_v2_size), (cleanup_v2_digest, cleanup_v2_size)]
    
    cfg_v2_json, cfg_v2_digest, cfg_v2_size = create_image_config(history_v2, diff_ids_v2, cmd=["python3", "/app/sentinel_core.py"])
    save_blob(cfg_v2_digest, cfg_v2_json)
    
    man_v2_json, man_v2_digest, man_v2_size = create_manifest(cfg_v2_digest, cfg_v2_size, layers_v2)
    save_manifest(repo_orbital, "v2.1.0", man_v2_json, man_v2_digest)

    # ------------------ VERSION 3.0.0 (MAJOR RELEASE) ------------------
    app_v3_files = {
        "/app/sentinel_core.py": "# Latveria Orbital Sentinel Core v3.0.0\n# Production Hardened\nprint('Sentinel Production Active')\n",
        "/app/VERSION": "3.0.0-hardened\n",
        "/app/config/runtime.json": "{\"cluster\": \"orbital-mesh\", \"secure_boot\": true}\n"
    }
    app_v3_blob, app_v3_digest, app_v3_size, app_v3_diff_id = create_tar_gz_blob(app_v3_files)
    save_blob(app_v3_digest, app_v3_blob)
    
    history_v3 = [
        {"created": "2026-06-01T10:00:00Z", "created_by": "/bin/sh -c #(nop) ADD file:latveria_base.tar.gz in /"},
        {"created": "2026-08-15T08:30:00Z", "created_by": "COPY app/ /app/"}
    ]
    diff_ids_v3 = [base_diff_id, app_v3_diff_id]
    layers_v3 = [(base_digest, base_size), (app_v3_digest, app_v3_size)]
    
    cfg_v3_json, cfg_v3_digest, cfg_v3_size = create_image_config(history_v3, diff_ids_v3, cmd=["python3", "/app/sentinel_core.py"])
    save_blob(cfg_v3_digest, cfg_v3_json)
    
    man_v3_json, man_v3_digest, man_v3_size = create_manifest(cfg_v3_digest, cfg_v3_size, layers_v3)
    save_manifest(repo_orbital, "v3.0.0", man_v3_json, man_v3_digest)

    # ------------------ VERSION 3.0.1 / LATEST (CURRENT CLEAN PRODUCTION) ------------------
    patch_v301_files = {
        "/app/patch.info": "Patch 3.0.1 applied: Updated orbital telemetry telemetry socket\n"
    }
    patch_blob, patch_digest, patch_size, patch_diff_id = create_tar_gz_blob(patch_v301_files)
    save_blob(patch_digest, patch_blob)
    
    history_v301 = history_v3 + [
        {"created": "2026-09-01T12:00:00Z", "created_by": "RUN echo 'Patch 3.0.1' > /app/patch.info"}
    ]
    diff_ids_v301 = diff_ids_v3 + [patch_diff_id]
    layers_v301 = layers_v3 + [(patch_digest, patch_size)]
    
    cfg_v301_json, cfg_v301_digest, cfg_v301_size = create_image_config(history_v301, diff_ids_v301, cmd=["python3", "/app/sentinel_core.py"])
    save_blob(cfg_v301_digest, cfg_v301_json)
    
    man_v301_json, man_v301_digest, man_v301_size = create_manifest(cfg_v301_digest, cfg_v301_size, layers_v301)
    save_manifest(repo_orbital, "v3.0.1", man_v301_json, man_v301_digest)
    save_manifest(repo_orbital, "latest", man_v301_json, man_v301_digest)

    # -------------------------------------------------------------
    # 3. REPOSITORY: latveria/core-auth (DECOY REPOSITORY)
    # -------------------------------------------------------------
    repo_auth = "latveria/core-auth"
    auth_v231_files = {
        "/opt/auth/server.py": "# Auth service prototype\n",
        "/etc/auth/sample_token.txt": "TEST_TOKEN=latv_test_auth_token_sample_non_functional\n"
    }
    auth_v231_blob, auth_v231_digest, auth_v231_size, auth_v231_diff = create_tar_gz_blob(auth_v231_files)
    save_blob(auth_v231_digest, auth_v231_blob)
    
    cfg_auth_json, cfg_auth_digest, cfg_auth_size = create_image_config(
        [{"created": "2026-05-01T00:00:00Z", "created_by": "ADD /opt/auth"}],
        [base_diff_id, auth_v231_diff]
    )
    save_blob(cfg_auth_digest, cfg_auth_json)
    man_auth_json, man_auth_digest, man_auth_size = create_manifest(cfg_auth_digest, cfg_auth_size, [(base_digest, base_size), (auth_v231_digest, auth_v231_size)])
    save_manifest(repo_auth, "v2.3.1", man_auth_json, man_auth_digest)
    save_manifest(repo_auth, "latest", man_auth_json, man_auth_digest)

    # -------------------------------------------------------------
    # 4. REPOSITORY: latveria/telemetry-relay (DECOY REPOSITORY)
    # -------------------------------------------------------------
    repo_telemetry = "latveria/telemetry-relay"
    telemetry_files = {
        "/opt/relay/metrics.py": "# Latveria Metrics Relay\n",
        "/opt/relay/config.json": "{\"LATVERIAN_TELEMETRY_KEY\": \"latv_telemetry_dummy_debug_key_112\"}\n"
    }
    telemetry_blob, telemetry_digest, telemetry_size, telemetry_diff = create_tar_gz_blob(telemetry_files)
    save_blob(telemetry_digest, telemetry_blob)
    
    cfg_telem_json, cfg_telem_digest, cfg_telem_size = create_image_config(
        [{"created": "2026-07-10T00:00:00Z", "created_by": "ADD /opt/relay"}],
        [base_diff_id, telemetry_diff]
    )
    save_blob(cfg_telem_digest, cfg_telem_json)
    man_telem_json, man_telem_digest, man_telem_size = create_manifest(cfg_telem_digest, cfg_telem_size, [(base_digest, base_size), (telemetry_blob_digest := telemetry_digest, telemetry_size)])
    save_manifest(repo_telemetry, "v1.5.0", man_telem_json, man_telem_digest)
    save_manifest(repo_telemetry, "latest", man_telem_json, man_telem_digest)

    print(f"[+] Successfully generated registry seed store with {len(saved_blobs)} blobs in {target_dir}")

if __name__ == "__main__":
    import sys
    out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else REGISTRY_ROOT
    build_all_repositories(out_dir)
