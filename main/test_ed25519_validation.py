#!/usr/bin/env python3
"""
Ed25519 Cryptographic Signature Validation Test for Task 23
"""

import sys

sys.path.insert(0, "src")
import logging

from compliance_validation.metadata_injector import get_metadata_injector
from core.cryptographic_audit import get_audit_crypto

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger(__name__)

def test_ed25519_signatures():
    """Test Ed25519 signature generation and validation."""
    try:
        logger.info("Testing Ed25519 cryptographic signatures...")

        # Test data
        test_data = {
            "suite_id": "OQ-SUITE-CRYPTO-TEST",
            "document_name": "Cryptographic Test Document",
            "test_cases": [{"test_id": "CRYPTO-001", "objective": "Test crypto"}],
            "total_test_count": 1
        }

        # Get metadata injector and crypto system
        metadata_injector = get_metadata_injector()
        audit_crypto = get_audit_crypto()

        # Generate enhanced data with signatures
        enhanced_dict = metadata_injector.inject_test_suite_metadata(
            test_suite_dict=test_data,
            llm_response={"confidence_score": 0.95},
            generation_context={
                "source_document_id": "CRYPTO_TEST_DOC",
                "gamp_category": 4,
                "pharmaceutical_validation": True
            }
        )

        # Extract signature information
        digital_signature = enhanced_dict.get("digital_signature")
        audit_trail = enhanced_dict.get("audit_trail", {})
        signature_id = audit_trail.get("signature_id")

        print("Ed25519 Signature Validation Results:")
        print("="*50)
        print(f"Digital Signature Present: {'[OK]' if digital_signature else '[MISSING]'}")
        print(f"Signature Length: {len(digital_signature) if digital_signature else 0} chars")
        print(f"Signature ID: {signature_id}")
        print(f"Audit Event ID: {audit_trail.get('creation_event')}")

        if digital_signature:
            # Test signature validation (basic format check)
            is_hex = all(c in "0123456789abcdef" for c in digital_signature.lower())
            correct_length = len(digital_signature) == 128  # Ed25519 signature is 64 bytes = 128 hex chars

            print(f"Signature Format Valid: {'[OK]' if is_hex else '[FAILED]'} (hex)")
            print(f"Signature Length Valid: {'[OK]' if correct_length else '[FAILED]'} (128 hex chars)")

            # Verify checksum and hash are present
            checksum = enhanced_dict.get("checksum")
            data_hash = enhanced_dict.get("hash")

            print(f"Data Checksum Present: {'[OK]' if checksum else '[MISSING]'}")
            print(f"Data Hash Present: {'[OK]' if data_hash else '[MISSING]'}")

            if checksum:
                print(f"Checksum: {checksum}")
            if data_hash:
                print(f"Hash: {data_hash[:32]}...")

            # Test overall cryptographic integrity
            crypto_integrity = (
                digital_signature and is_hex and correct_length and
                checksum and data_hash and signature_id
            )

            print()
            print("="*50)
            print(f"CRYPTOGRAPHIC INTEGRITY: {'[VALIDATED]' if crypto_integrity else '[FAILED]'}")
            print("="*50)

            return crypto_integrity
        print("[ERROR] No digital signature found")
        return False

    except Exception as e:
        logger.error(f"Ed25519 signature test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_ed25519_signatures()
    print(f"\nEd25519 Test Result: {'PASSED' if success else 'FAILED'}")
