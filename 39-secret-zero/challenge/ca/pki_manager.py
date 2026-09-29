#!/usr/bin/env python3
"""
Challenge-Local PKI & Certificate Authority Manager
Dedicated challenge-local Root CA independent from Kubernetes cluster PKI and cloud credentials.
Enforces certificate store bounding <= 16 MiB and supports dynamic rotation.
"""

import os
import datetime
import secrets
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from cryptography import x509
from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend

CA_DIR = Path(__file__).resolve().parent
CERT_STORE_DIR = CA_DIR / "cert_store"
CERT_STORE_DIR.mkdir(parents=True, exist_ok=True)

ROOT_CA_KEY_FILE = CA_DIR / "root_ca.key"
ROOT_CA_CERT_FILE = CA_DIR / "root_ca.crt"
CONFIG_FILE = CA_DIR.parent / "config" / "pki_state.json"

MAX_CERT_STORE_BYTES = 16 * 1024 * 1024  # 16 MiB limit

class ChallengePKIManager:
    def __init__(self):
        self.ca_key: Optional[rsa.RSAPrivateKey] = None
        self.ca_cert: Optional[x509.Certificate] = None
        self.last_load_mtime: float = 0
        self.issued_serials: set = set()
        self.initialize_or_load_ca()

    def initialize_or_load_ca(self, force_rotate: bool = False):
        """Initializes or rotates the challenge-local Root CA."""
        if force_rotate or not ROOT_CA_KEY_FILE.exists() or not ROOT_CA_CERT_FILE.exists():
            self.generate_new_root_ca()
        else:
            try:
                mtime = ROOT_CA_CERT_FILE.stat().st_mtime
                if mtime > self.last_load_mtime or self.ca_cert is None:
                    key_pem = ROOT_CA_KEY_FILE.read_bytes()
                    self.ca_key = serialization.load_pem_private_key(
                        key_pem, password=None, backend=default_backend()
                    )
                    cert_pem = ROOT_CA_CERT_FILE.read_bytes()
                    self.ca_cert = x509.load_pem_x509_certificate(cert_pem, backend=default_backend())
                    self.last_load_mtime = mtime
            except Exception:
                self.generate_new_root_ca()

    def generate_new_root_ca(self):
        """Generates a fresh challenge-local Root CA."""
        # Generate private key
        self.ca_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )

        # Subject & Issuer
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "LV"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Doomstadt"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Latveria Cyber Command"),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "Secret Zero PKI Authority"),
            x509.NameAttribute(NameOID.COMMON_NAME, f"Latveria Root CA-{secrets.token_hex(4)}"),
        ])

        now = datetime.datetime.now(datetime.timezone.utc)
        ca_cert_builder = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(self.ca_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - datetime.timedelta(minutes=5))
            .not_valid_after(now + datetime.timedelta(days=365))
            .add_extension(
                x509.BasicConstraints(ca=True, path_length=None),
                critical=True,
            )
            .add_extension(
                x509.KeyUsage(
                    digital_signature=True,
                    content_commitment=False,
                    key_encipherment=False,
                    data_encipherment=False,
                    key_agreement=False,
                    key_cert_sign=True,
                    crl_sign=True,
                    encipher_only=False,
                    decipher_only=False,
                ),
                critical=True,
            )
            .add_extension(
                x509.SubjectKeyIdentifier.from_public_key(self.ca_key.public_key()),
                critical=False,
            )
        )

        self.ca_cert = ca_cert_builder.sign(
            private_key=self.ca_key,
            algorithm=hashes.SHA256(),
            backend=default_backend()
        )

        # Write to files
        ROOT_CA_KEY_FILE.write_bytes(
            self.ca_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )
        ROOT_CA_KEY_FILE.chmod(0o600)

        ROOT_CA_CERT_FILE.write_bytes(
            self.ca_cert.public_bytes(serialization.Encoding.PEM)
        )

        # Clean old cert store
        for old_cert in CERT_STORE_DIR.glob("*.crt"):
            try:
                old_cert.unlink()
            except Exception:
                pass
        self.issued_serials.clear()

    def get_root_ca_pem(self) -> str:
        """Returns the public Root CA certificate PEM string."""
        if not self.ca_cert:
            self.initialize_or_load_ca()
        return self.ca_cert.public_bytes(serialization.Encoding.PEM).decode("utf-8")

    def enforce_store_quota(self):
        """Ensures the cert store directory remains <= 16 MiB."""
        total_size = sum(f.stat().st_size for f in CERT_STORE_DIR.glob("*") if f.is_file())
        if total_size > MAX_CERT_STORE_BYTES:
            # Prune oldest cert files
            files = sorted(CERT_STORE_DIR.glob("*.crt"), key=lambda f: f.stat().st_mtime)
            for f in files[:len(files)//2]:
                try:
                    f.unlink()
                except Exception:
                    pass

    def sign_csr(
        self,
        csr_pem: str,
        requested_identity_uri: Optional[str] = None,
        role: str = "telemetry-worker",
        validity_days: int = 30
    ) -> Tuple[str, Dict[str, Any]]:
        """Signs a Certificate Signing Request (CSR) with Challenge CA."""
        self.enforce_store_quota()

        if not self.ca_key or not self.ca_cert:
            self.initialize_or_load_ca()

        csr = x509.load_pem_x509_csr(csr_pem.encode("utf-8"), backend=default_backend())

        # Validate CSR signature
        if not csr.is_signature_valid:
            raise ValueError("CSR signature verification failed.")

        serial_number = x509.random_serial_number()
        now = datetime.datetime.now(datetime.timezone.utc)

        # Determine Subject Alternative Names (SAN)
        san_list = []
        if requested_identity_uri:
            san_list.append(x509.UniformResourceIdentifier(requested_identity_uri))
        else:
            san_list.append(x509.UniformResourceIdentifier(f"spiffe://latveria.local/ns/edge/sa/{role}"))

        # Build Certificate
        cert_builder = (
            x509.CertificateBuilder()
            .subject_name(csr.subject)
            .issuer_name(self.ca_cert.subject)
            .public_key(csr.public_key())
            .serial_number(serial_number)
            .not_valid_before(now - datetime.timedelta(minutes=5))
            .not_valid_after(now + datetime.timedelta(days=validity_days))
            .add_extension(
                x509.BasicConstraints(ca=False, path_length=None),
                critical=True,
            )
            .add_extension(
                x509.KeyUsage(
                    digital_signature=True,
                    content_commitment=False,
                    key_encipherment=True,
                    data_encipherment=False,
                    key_agreement=False,
                    key_cert_sign=False,
                    crl_sign=False,
                    encipher_only=False,
                    decipher_only=False,
                ),
                critical=True,
            )
            .add_extension(
                x509.ExtendedKeyUsage([
                    ExtendedKeyUsageOID.CLIENT_AUTH,
                    ExtendedKeyUsageOID.SERVER_AUTH
                ]),
                critical=False,
            )
            .add_extension(
                x509.SubjectAlternativeName(san_list),
                critical=False,
            )
            .add_extension(
                x509.AuthorityKeyIdentifier.from_issuer_public_key(self.ca_key.public_key()),
                critical=False,
            )
        )

        signed_cert = cert_builder.sign(
            private_key=self.ca_key,
            algorithm=hashes.SHA256(),
            backend=default_backend()
        )

        cert_pem = signed_cert.public_bytes(serialization.Encoding.PEM).decode("utf-8")
        serial_hex = hex(serial_number)
        self.issued_serials.add(serial_hex)

        # Save to certificate store
        cert_file = CERT_STORE_DIR / f"{serial_hex}.crt"
        cert_file.write_text(cert_pem)

        metadata = {
            "serial_number": serial_hex,
            "subject": csr.subject.rfc4514_string(),
            "issuer": self.ca_cert.subject.rfc4514_string(),
            "not_before": signed_cert.not_valid_before_utc.isoformat(),
            "not_after": signed_cert.not_valid_after_utc.isoformat(),
            "san_uris": [requested_identity_uri or f"spiffe://latveria.local/ns/edge/sa/{role}"],
            "role": role,
            "fingerprint_sha256": signed_cert.fingerprint(hashes.SHA256()).hex(),
        }

        return cert_pem, metadata

    def verify_client_certificate(
        self,
        cert_pem: str,
        signature_b64: Optional[str] = None,
        challenge_data: Optional[bytes] = None
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Validates client certificate against the Challenge-Local Root CA.
        Also optionally verifies proof-of-possession signature.
        """
        self.initialize_or_load_ca()

        try:
            cert = x509.load_pem_x509_certificate(cert_pem.encode("utf-8"), backend=default_backend())
        except Exception as e:
            return False, f"Invalid X.509 certificate PEM: {str(e)}", {}

        # 1. Verify Issuer matches Root CA
        if cert.issuer != self.ca_cert.subject:
            return False, "Certificate was not issued by Latveria Challenge Root CA.", {}

        # 2. Verify signature with Root CA public key
        try:
            ca_pubkey = self.ca_cert.public_key()
            ca_pubkey.verify(
                cert.signature,
                cert.tbs_certificate_bytes,
                padding.PKCS1v15(),
                cert.signature_hash_algorithm,
            )
        except Exception as e:
            return False, f"Certificate cryptographic signature verification failed: {str(e)}", {}

        # 3. Check validity period
        now = datetime.datetime.now(datetime.timezone.utc)
        if now < cert.not_valid_before_utc:
            return False, "Certificate is not yet valid.", {}
        if now > cert.not_valid_after_utc:
            return False, "Certificate has expired.", {}

        # 4. Extract SANs and Subject
        san_uris = []
        try:
            san_ext = cert.extensions.get_extension_for_oid(x509.oid.ExtensionOID.SUBJECT_ALTERNATIVE_NAME)
            for name in san_ext.value:
                if isinstance(name, x509.UniformResourceIdentifier):
                    san_uris.append(name.value)
        except x509.ExtensionNotFound:
            pass

        # 5. Verify Proof-of-Possession Signature if provided
        if signature_b64 and challenge_data:
            import base64
            try:
                sig_bytes = base64.b64decode(signature_b64)
                client_pubkey = cert.public_key()
                client_pubkey.verify(
                    sig_bytes,
                    challenge_data,
                    padding.PKCS1v15(),
                    hashes.SHA256()
                )
            except Exception as e:
                return False, f"Proof-of-possession signature verification failed: {str(e)}", {}

        cert_info = {
            "subject": cert.subject.rfc4514_string(),
            "serial_number": hex(cert.serial_number),
            "san_uris": san_uris,
            "fingerprint_sha256": cert.fingerprint(hashes.SHA256()).hex(),
        }

        return True, "Valid", cert_info


pki_manager = ChallengePKIManager()
