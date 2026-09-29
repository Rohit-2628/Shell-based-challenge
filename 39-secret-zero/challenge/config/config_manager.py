#!/usr/bin/env python3
"""
Configuration & State Management for Secret Zero Challenge (X09)
Generates team-specific or instance-scoped state, rotating on reset.
"""

import os
import json
import secrets
from pathlib import Path
from typing import Dict, Any

CONFIG_DIR = Path(__file__).resolve().parent
STATE_FILE = CONFIG_DIR / "state.json"
AGENT_CONF_FILE = CONFIG_DIR / "bootstrap_agent.conf"

DEFAULT_FLAG = "YUVA{s3cr3t_z3r0_m4ch1n3_1d3nt1ty_b00tstr4p_pki_x09}"

class ChallengeStateManager:
    def __init__(self):
        self.state: Dict[str, Any] = {}
        self.last_load_mtime: float = 0
        self.load_or_initialize_state()

    def load_or_initialize_state(self, force_reset: bool = False):
        if force_reset or not STATE_FILE.exists():
            self.generate_new_state()
        else:
            try:
                mtime = STATE_FILE.stat().st_mtime
                if mtime > self.last_load_mtime or not self.state:
                    self.state = json.loads(STATE_FILE.read_text())
                    self.last_load_mtime = mtime
            except Exception:
                self.generate_new_state()

    def generate_new_state(self):
        bootstrap_secret = f"latveria_boot_secret_{secrets.token_hex(8)}"
        secret_zero_key = f"SZ_KEY_{secrets.token_hex(16)}"
        flag = os.environ.get("FLAG", DEFAULT_FLAG)
        target_token = f"TARGET_AUTH_{secrets.token_hex(12)}"

        self.state = {
            "bootstrap_secret": bootstrap_secret,
            "secret_zero_key": secret_zero_key,
            "target_token": target_token,
            "flag": flag,
            "node_id": f"aegis-edge-{secrets.token_hex(4)}",
            "allowed_roles": {
                "telemetry-worker": {
                    "spiffe_id": "spiffe://latveria.local/ns/edge/sa/telemetry-worker",
                    "access_level": "LOW_TRUST",
                    "description": "Standard diagnostic telemetry agent with read-only metrics access"
                },
                "vault-operator": {
                    "spiffe_id": "spiffe://latveria.local/ns/core/sa/vault-operator",
                    "access_level": "AUTHORIZED_SECRET_ZERO",
                    "description": "High-trust machine identity authorized to retrieve Secret Zero unseal keys"
                }
            }
        }

        STATE_FILE.write_text(json.dumps(self.state, indent=2))

        # Write the public agent conf (inspectable via bootstrap diagnostic log / view)
        agent_conf = {
            "version": "v2.4-AegisZero",
            "node_id": self.state["node_id"],
            "bootstrap_authority": "http://127.0.0.1:8081/api/v1/ca/issue",
            "secret_service_url": "http://127.0.0.1:8082/api/v1/vault/secret-zero",
            "target_service_url": "http://127.0.0.1:8083/api/v1/doomsday/unseal",
            "bootstrap_hmac_secret": bootstrap_secret,
            "default_identity": "spiffe://latveria.local/ns/edge/sa/telemetry-worker",
            "authorized_machine_identities": [
                "spiffe://latveria.local/ns/edge/sa/telemetry-worker",
                "spiffe://latveria.local/ns/core/sa/vault-operator"
            ],
            "security_policy": {
                "require_pki_signature": True,
                "san_spiffe_validation": True,
                "minimum_trust_tier": "AUTHORIZED_SECRET_ZERO"
            }
        }
        AGENT_CONF_FILE.write_text(json.dumps(agent_conf, indent=2))

    def get_bootstrap_secret(self) -> str:
        self.load_or_initialize_state()
        return self.state.get("bootstrap_secret", "")

    def get_secret_zero_key(self) -> str:
        self.load_or_initialize_state()
        return self.state.get("secret_zero_key", "")

    def get_flag(self) -> str:
        self.load_or_initialize_state()
        return self.state.get("flag", os.environ.get("FLAG", DEFAULT_FLAG))

    def get_target_token(self) -> str:
        self.load_or_initialize_state()
        return self.state.get("target_token", "")

state_manager = ChallengeStateManager()
