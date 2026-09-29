#!/usr/bin/env python3
"""
Seed Data Generator for D29 — Mock Object Storage
Creates synthetic buckets and objects for the challenge.
"""

import gzip
import json
import os
import sys
from pathlib import Path

def generate_seed_storage(base_dir: str):
    base_path = Path(base_dir)
    base_path.mkdir(parents=True, exist_ok=True)

    # 1. Bucket: public-assets
    public_dir = base_path / "public-assets"
    public_dir.mkdir(parents=True, exist_ok=True)
    
    # 1x1 transparent PNG / simple PNG
    png_bytes = bytes([
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,
        0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,
        0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
        0x08, 0x06, 0x00, 0x00, 0x00, 0x1F, 0x15, 0xC4,
        0x89, 0x00, 0x00, 0x00, 0x0A, 0x49, 0x44, 0x41,
        0x54, 0x78, 0x9C, 0x63, 0x00, 0x01, 0x00, 0x00,
        0x05, 0x00, 0x01, 0x0D, 0x0A, 0x2D, 0xB4, 0x00,
        0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44, 0xAE,
        0x42, 0x60, 0x82
    ])
    (public_dir / "logo.png").write_bytes(png_bytes)
    
    # Fake JPG banner
    jpg_bytes = bytes([
        0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46,
        0x49, 0x46, 0x00, 0x01, 0x01, 0x01, 0x00, 0x48,
        0x00, 0x48, 0x00, 0x00, 0xFF, 0xDB, 0x00, 0x43,
        0x00, 0x08, 0x06, 0x06, 0x07, 0x06, 0x05, 0x08,
        0xFF, 0xD9
    ])
    (public_dir / "cloud_mirror_banner.jpg").write_bytes(jpg_bytes)
    (public_dir / "theme.css").write_text("/* Latverian Defense System Theme */\n:root { --primary-color: #00ff66; --bg-dark: #0a0e17; }\n")

    # 2. Bucket: archive-backups
    archive_dir = base_path / "archive-backups"
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    sql_dump = "-- Latveria Orbital Telemetry Database Backup 2025-12\nCREATE TABLE satellite_nodes (id INT, name VARCHAR(64), status VARCHAR(16));\nINSERT INTO satellite_nodes VALUES (1, 'ORBITAL-RELAY-ALPHA', 'ACTIVE'), (2, 'ORBITAL-RELAY-BETA', 'STANDBY');\n"
    with gzip.open(archive_dir / "db_dump_202512.sql.gz", "wb") as f:
        f.write(sql_dump.encode("utf-8"))
    
    (archive_dir / "legacy_firmware_v0.9.bin").write_bytes(b"\x7FELF\x02\x01\x01\x00" + b"\x00" * 64 + b"LATV_FW_BUILD_20250912")

    # 3. Bucket: internal-telemetry
    telemetry_dir = base_path / "internal-telemetry"
    telemetry_dir.mkdir(parents=True, exist_ok=True)
    
    telemetry_csv = "timestamp,node,azimuth,elevation,flux_mw,status\n2026-09-26T00:00:00Z,SAT-01,142.5,45.2,850.2,NOMINAL\n2026-09-26T01:00:00Z,SAT-01,143.1,45.8,851.0,NOMINAL\n2026-09-26T02:00:00Z,SAT-01,143.8,46.1,849.7,NOMINAL\n"
    (telemetry_dir / "satellite_telemetry_2026_09.csv").write_text(telemetry_csv)
    
    drift_json = {
        "constellation": "DOOM-ORBITAL-CONSTELLATION-V4",
        "orbital_planes": 6,
        "nodes_per_plane": 4,
        "drift_correction_period_sec": 3600,
        "active_mesh_relays": ["SAT-01", "SAT-02", "SAT-03", "SAT-04"]
    }
    (telemetry_dir / "orbital_drift_logs.json").write_text(json.dumps(drift_json, indent=2))

    # 4. Bucket: classified-orbital-mirror
    classified_dir = base_path / "classified-orbital-mirror"
    classified_dir.mkdir(parents=True, exist_ok=True)
    
    topology_json = {
        "classification": "TOP SECRET // LATVERIAN DEFENSE MINISTRY",
        "cluster_name": "ORBITAL-MIRROR-PRIMARY-GRID",
        "region": "LATV-ORBITAL-SECTOR-7",
        "satellites": [
            {"id": "MIRROR-SAT-ALPHA", "apogee_km": 35786, "laser_link_status": "LOCKED"},
            {"id": "MIRROR-SAT-BRAVO", "apogee_km": 35786, "laser_link_status": "LOCKED"}
        ],
        "notes": "Emergency mirror defense key is stored in classified_mirror_master_key.dat"
    }
    (classified_dir / "mirror_cluster_topology.json").write_text(json.dumps(topology_json, indent=2))
    
    instructions = "LATVERIA ORBITAL DEFENSE // MANUAL OVERRIDE INSTRUCTIONS\n\n1. Authenticate with temporary IAM mirror session token.\n2. Fetch classified_mirror_master_key.dat to extract master authorization payload.\n3. Validate defense checksum.\n"
    (classified_dir / "orbital_override_instructions.pdf").write_text(instructions)
    (classified_dir / "classified_mirror_master_key.dat").write_text("CLASSIFIED_ORBITAL_MIRROR_MASTER_KEY_SEED")

    print(f"[+] Successfully generated mock object store seed data in {base_dir}")

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "/var/lib/latveria-storage"
    generate_seed_storage(target)
