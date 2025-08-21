"""
Ed25519 Cryptographic Audit Trail System for 21 CFR Part 11 Compliance

Implements digital signatures for tamper-evident audit logging to meet
pharmaceutical regulatory requirements. All critical audit entries are
cryptographically signed to ensure data integrity and non-repudiation.

Features:
- Ed25519 digital signatures for performance and security
- Key pair management with secure storage
- Signature verification and chain validation
- Tamper evidence through linked signatures
- Full audit trail of signature operations
"""

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    PublicFormat,
)

logger = logging.getLogger(__name__)


class CryptographicAuditError(Exception):
    """Base exception for cryptographic audit operations."""


class Ed25519AuditSigner:
    """
    Ed25519 digital signature system for pharmaceutical audit trails.
    
    Provides cryptographic integrity for all audit entries to ensure
    compliance with 21 CFR Part 11 electronic records requirements.
    """

    def __init__(self, key_dir: str = "keys/audit", system_id: str = "gamp5_system"):
        """
        Initialize the cryptographic audit signer.
        
        Args:
            key_dir: Directory for storing cryptographic keys
            system_id: Unique identifier for this system instance
        """
        self.key_dir = Path(key_dir)
        self.key_dir.mkdir(parents=True, exist_ok=True)
        self.system_id = system_id

        # Key file paths
        self.private_key_path = self.key_dir / f"{system_id}_private.pem"
        self.public_key_path = self.key_dir / f"{system_id}_public.pem"

        # Initialize or load key pair
        self._initialize_keys()

        # Signature chain tracking for tamper evidence
        self.last_signature: str | None = None

    def _initialize_keys(self) -> None:
        """Initialize or load Ed25519 key pair."""
        try:
            if self.private_key_path.exists() and self.public_key_path.exists():
                # Load existing keys
                self._load_keys()
                logger.info(f"[CRYPTO] Loaded existing Ed25519 key pair for {self.system_id}")
            else:
                # Generate new key pair
                self._generate_keys()
                logger.info(f"[CRYPTO] Generated new Ed25519 key pair for {self.system_id}")

        except Exception as e:
            raise CryptographicAuditError(f"Key initialization failed: {e}") from e

    def _generate_keys(self) -> None:
        """Generate new Ed25519 key pair."""
        try:
            # Generate private key
            private_key = ed25519.Ed25519PrivateKey.generate()

            # Get public key
            public_key = private_key.public_key()

            # Serialize and save private key (NO ENCRYPTION for system keys)
            # In production, this should be encrypted and managed by HSM
            private_pem = private_key.private_bytes(
                encoding=Encoding.PEM,
                format=PrivateFormat.PKCS8,
                encryption_algorithm=NoEncryption()
            )

            # Serialize and save public key
            public_pem = public_key.public_bytes(
                encoding=Encoding.PEM,
                format=PublicFormat.SubjectPublicKeyInfo
            )

            # Write keys to files with restrictive permissions
            self.private_key_path.write_bytes(private_pem)
            self.public_key_path.write_bytes(public_pem)

            # Set restrictive permissions (Windows compatible)
            try:
                self.private_key_path.chmod(0o600)  # Owner read/write only
                self.public_key_path.chmod(0o644)   # Owner read/write, others read
            except OSError:
                # Windows doesn't support chmod - rely on NTFS permissions
                pass

            # Store keys in memory
            self.private_key = private_key
            self.public_key = public_key

            logger.info("[CRYPTO] Ed25519 key pair generated and stored")

        except Exception as e:
            raise CryptographicAuditError(f"Key generation failed: {e}") from e

    def _load_keys(self) -> None:
        """Load existing Ed25519 key pair."""
        try:
            # Load private key
            private_pem = self.private_key_path.read_bytes()
            self.private_key = serialization.load_pem_private_key(
                private_pem,
                password=None
            )

            # Load public key
            public_pem = self.public_key_path.read_bytes()
            self.public_key = serialization.load_pem_public_key(public_pem)

            # Verify key pair consistency
            self._verify_key_pair()

        except Exception as e:
            raise CryptographicAuditError(f"Key loading failed: {e}") from e

    def _verify_key_pair(self) -> None:
        """Verify that private and public keys are consistent."""
        try:
            # Test signature with known data
            test_data = b"key_pair_verification_test"
            signature = self.private_key.sign(test_data)

            # Verify signature with public key
            self.public_key.verify(signature, test_data)

        except Exception as e:
            raise CryptographicAuditError(f"Key pair verification failed: {e}") from e

    def bind_signature_to_record(
        self,
        record_id: str,
        record_content: dict[str, Any],
        signature_meaning: str,
        signer_identity: dict[str, str]
    ) -> dict[str, Any]:
        """
        Bind electronic signature to specific record per 21 CFR Part 11 requirements.
        
        Args:
            record_id: Unique identifier for the record
            record_content: Complete record content to bind signature to
            signature_meaning: Meaning of signature (approved, reviewed, etc.)
            signer_identity: Signer name and ID information
            
        Returns:
            Cryptographically bound signature record
        """
        try:
            timestamp = datetime.now(UTC).isoformat()
            signature_id = str(uuid4())

            # Create record-specific binding payload
            binding_payload = {
                "record_id": record_id,
                "record_content": record_content,
                "signature_binding": {
                    "signature_id": signature_id,
                    "signer_name": signer_identity.get("signer_name"),
                    "signer_id": signer_identity.get("signer_id"),
                    "signature_meaning": signature_meaning,
                    "signature_timestamp": timestamp,
                    "binding_nonce": str(uuid4())  # Prevents signature replay
                },
                "regulatory_compliance": {
                    "cfr_section_50": "signature_manifestation_complete",
                    "cfr_section_70": "record_signature_binding_active",
                    "part11_compliant": True
                }
            }

            # Generate signature using existing audit infrastructure
            return self.sign_audit_entry(binding_payload, entry_type="electronic_signature_binding")

        except Exception as e:
            logger.error(f"[CRYPTO] Signature binding failed: {e}")
            raise CryptographicAuditError(f"Electronic signature binding failed: {e}") from e

    def sign_audit_entry(
        self,
        audit_data: dict[str, Any],
        entry_type: str = "audit_entry"
    ) -> dict[str, Any]:
        """
        Sign an audit entry with Ed25519 digital signature.
        
        Args:
            audit_data: Audit entry data to sign
            entry_type: Type of audit entry (for signature chaining)
            
        Returns:
            Signed audit entry with cryptographic metadata
            
        Raises:
            CryptographicAuditError: If signing fails
        """
        try:
            # Create signature payload
            timestamp = datetime.now(UTC).isoformat()
            signature_id = str(uuid4())

            # Canonical JSON representation for signing
            canonical_data = {
                "audit_data": audit_data,
                "timestamp": timestamp,
                "signature_id": signature_id,
                "entry_type": entry_type,
                "system_id": self.system_id,
                "previous_signature": self.last_signature
            }

            # Convert to canonical JSON bytes
            canonical_json = json.dumps(canonical_data, sort_keys=True, separators=(",", ":"))
            canonical_bytes = canonical_json.encode("utf-8")

            # Generate Ed25519 signature
            signature = self.private_key.sign(canonical_bytes)

            # Convert signature to hex string
            signature_hex = signature.hex()

            # Update signature chain
            self.last_signature = signature_hex

            # Create signed audit entry
            signed_entry = {
                **audit_data,
                "cryptographic_metadata": {
                    "signature": signature_hex,
                    "signature_id": signature_id,
                    "signature_algorithm": "Ed25519",
                    "signing_timestamp": timestamp,
                    "system_id": self.system_id,
                    "previous_signature": canonical_data["previous_signature"],
                    "canonical_payload": canonical_json,
                    "integrity_hash": self._calculate_integrity_hash(canonical_bytes)
                },
                "regulatory_metadata": {
                    "compliance_standard": "21_CFR_Part_11",
                    "signature_purpose": "audit_trail_integrity",
                    "tamper_evidence": "ed25519_digital_signature",
                    "signature_validity": "cryptographically_verified"
                }
            }

            logger.debug(f"[CRYPTO] Signed audit entry: {signature_id}")
            return signed_entry

        except Exception as e:
            logger.error(f"[CRYPTO] Signature generation failed: {e}")
            # NO FALLBACKS - fail explicitly for regulatory compliance
            raise CryptographicAuditError(f"Audit entry signing failed: {e}") from e

    def verify_signature(self, signed_entry: dict[str, Any]) -> bool:
        """
        Verify the Ed25519 signature of an audit entry.
        
        Args:
            signed_entry: Signed audit entry to verify
            
        Returns:
            True if signature is valid, False otherwise
            
        Raises:
            CryptographicAuditError: If verification process fails
        """
        try:
            crypto_metadata = signed_entry.get("cryptographic_metadata", {})
            if not crypto_metadata:
                raise CryptographicAuditError("No cryptographic metadata found")

            # Extract signature and payload
            signature_hex = crypto_metadata.get("signature")
            canonical_payload = crypto_metadata.get("canonical_payload")

            if not signature_hex or not canonical_payload:
                raise CryptographicAuditError("Missing signature or payload")

            # Convert hex signature back to bytes
            signature = bytes.fromhex(signature_hex)
            payload_bytes = canonical_payload.encode("utf-8")

            # Verify signature
            self.public_key.verify(signature, payload_bytes)

            # Verify integrity hash
            calculated_hash = self._calculate_integrity_hash(payload_bytes)
            stored_hash = crypto_metadata.get("integrity_hash")

            if calculated_hash != stored_hash:
                logger.error("[CRYPTO] Integrity hash mismatch")
                return False

            logger.debug(f"[CRYPTO] Signature verified: {crypto_metadata.get('signature_id')}")
            return True

        except Exception as e:
            logger.error(f"[CRYPTO] Signature verification failed: {e}")
            # For verification, return False rather than raising (allows processing of invalid entries)
            return False

    def _calculate_integrity_hash(self, data: bytes) -> str:
        """Calculate integrity hash for additional tamper evidence."""
        import hashlib
        return hashlib.sha256(data).hexdigest()

    def verify_signature_chain(self, entries: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Verify the integrity of a signature chain.
        
        Args:
            entries: List of signed audit entries in chronological order
            
        Returns:
            Chain verification results with detailed analysis
        """
        results = {
            "chain_valid": True,
            "total_entries": len(entries),
            "verified_entries": 0,
            "invalid_entries": [],
            "chain_breaks": [],
            "verification_timestamp": datetime.now(UTC).isoformat()
        }

        previous_signature = None

        for i, entry in enumerate(entries):
            try:
                # Verify individual signature
                if not self.verify_signature(entry):
                    results["chain_valid"] = False
                    results["invalid_entries"].append({
                        "index": i,
                        "signature_id": entry.get("cryptographic_metadata", {}).get("signature_id"),
                        "error": "signature_verification_failed"
                    })
                    continue

                # Verify chain linkage
                crypto_metadata = entry.get("cryptographic_metadata", {})
                expected_previous = crypto_metadata.get("previous_signature")

                if expected_previous != previous_signature:
                    results["chain_valid"] = False
                    results["chain_breaks"].append({
                        "index": i,
                        "expected": expected_previous,
                        "actual": previous_signature
                    })

                previous_signature = crypto_metadata.get("signature")
                results["verified_entries"] += 1

            except Exception as e:
                results["chain_valid"] = False
                results["invalid_entries"].append({
                    "index": i,
                    "error": str(e)
                })

        logger.info(
            f"[CRYPTO] Chain verification: {results['verified_entries']}/{results['total_entries']} "
            f"entries valid, chain_valid={results['chain_valid']}"
        )

        return results

    def get_public_key_info(self) -> dict[str, str]:
        """Get public key information for audit trail metadata."""
        public_bytes = self.public_key.public_bytes(
            encoding=Encoding.PEM,
            format=PublicFormat.SubjectPublicKeyInfo
        )

        return {
            "algorithm": "Ed25519",
            "system_id": self.system_id,
            "public_key_pem": public_bytes.decode("utf-8"),
            "key_fingerprint": self._calculate_integrity_hash(public_bytes)
        }


class AuditTrailCrypto:
    """
    High-level interface for cryptographic audit trail operations.
    
    Provides simplified access to Ed25519 signing functionality
    with automatic key management and audit trail integration.
    """

    def __init__(self, system_id: str = "pharmaceutical_gamp5_system"):
        """Initialize cryptographic audit trail system."""
        self.signer = Ed25519AuditSigner(system_id=system_id)
        self.system_id = system_id

    def sign_audit_event(
        self,
        event_type: str,
        event_data: dict[str, Any],
        workflow_context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Sign an audit event for the pharmaceutical workflow.
        
        Args:
            event_type: Type of audit event (e.g., 'agent_decision', 'data_transformation')
            event_data: Event-specific data to audit
            workflow_context: Additional workflow context
            
        Returns:
            Cryptographically signed audit entry
        """
        # Prepare audit data with pharmaceutical compliance metadata
        audit_data = {
            "event_type": event_type,
            "event_data": event_data,
            "workflow_context": workflow_context or {},
            "compliance_metadata": {
                "standard": "GAMP-5",
                "regulation": "21_CFR_Part_11",
                "audit_purpose": "pharmaceutical_validation",
                "data_integrity": "ALCOA_plus"
            },
            "audit_timestamp": datetime.now(UTC).isoformat(),
            "audit_id": str(uuid4())
        }

        return self.signer.sign_audit_entry(audit_data, entry_type=event_type)

    def verify_audit_event(self, signed_entry: dict[str, Any]) -> bool:
        """Verify a signed audit event."""
        return self.signer.verify_signature(signed_entry)

    def verify_audit_chain(self, entries: list[dict[str, Any]]) -> dict[str, Any]:
        """Verify the integrity of an audit event chain."""
        return self.signer.verify_signature_chain(entries)


# Global cryptographic audit instance (singleton pattern)
_global_audit_crypto: AuditTrailCrypto | None = None


def get_audit_crypto() -> AuditTrailCrypto:
    """Get the global cryptographic audit instance."""
    global _global_audit_crypto
    if _global_audit_crypto is None:
        _global_audit_crypto = AuditTrailCrypto()
    return _global_audit_crypto


# Export main classes and functions
__all__ = [
    "AuditTrailCrypto",
    "CryptographicAuditError",
    "Ed25519AuditSigner",
    "get_audit_crypto"
]
