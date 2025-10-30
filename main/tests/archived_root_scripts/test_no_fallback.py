"""
Test NO FALLBACK Behavior for Task 22

This test verifies that the audit trail system fails explicitly without
fallbacks when cryptographic operations or audit logging fails, ensuring
regulatory compliance through honest error reporting.
"""

import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

# Add main directory to Python path
sys.path.append(str(Path(__file__).parent))

from src.core.audit_trail import ComprehensiveAuditTrail


def test_no_fallback_cryptographic_failure():
    """Test that cryptographic failures cause explicit failure without fallbacks."""
    print("Testing NO FALLBACK behavior on cryptographic failure...")

    try:
        # Test with invalid key directory (should fail without fallback)
        with tempfile.TemporaryDirectory() as temp_dir:
            invalid_key_dir = Path(temp_dir) / "nonexistent" / "path"

            # This should fail without fallback
            audit_trail = ComprehensiveAuditTrail(
                audit_dir=temp_dir + "/audit",
                enable_cryptographic_signing=True
            )

            # Try to corrupt the private key file and force a signing failure
            signer = audit_trail.crypto_audit.signer

            # Mock the signing method to simulate failure
            with patch.object(signer.private_key, "sign", side_effect=Exception("Simulated crypto failure")):
                try:
                    audit_trail.log_agent_decision(
                        agent_type="test_agent",
                        agent_id="test_001",
                        decision={"test": "decision"},
                        confidence_score=0.8,
                        alternatives_considered=[],
                        rationale="test rationale",
                        input_context={},
                        processing_time=1.0
                    )
                    print("ERROR: Audit system allowed logging despite crypto failure!")
                    return False
                except RuntimeError as e:
                    if "Audit trail integrity failure" in str(e):
                        print("SUCCESS: System failed explicitly on crypto failure")
                        print(f"Error message: {e}")
                        return True
                    print(f"ERROR: Wrong error type: {e}")
                    return False
                except Exception as e:
                    print(f"ERROR: Unexpected error type: {e}")
                    return False

    except Exception as e:
        print(f"Test setup failed: {e}")
        return False


def test_no_fallback_audit_storage_failure():
    """Test that audit storage failures cause explicit failure without fallbacks."""
    print("\nTesting NO FALLBACK behavior on storage failure...")

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            audit_trail = ComprehensiveAuditTrail(
                audit_dir=temp_dir + "/audit",
                enable_cryptographic_signing=True
            )

            # Mock file writing to simulate storage failure
            with patch("builtins.open", side_effect=OSError("Simulated disk full")):
                try:
                    audit_trail.log_agent_decision(
                        agent_type="test_agent",
                        agent_id="test_001",
                        decision={"test": "decision"},
                        confidence_score=0.8,
                        alternatives_considered=[],
                        rationale="test rationale",
                        input_context={},
                        processing_time=1.0
                    )
                    print("ERROR: Audit system allowed logging despite storage failure!")
                    return False
                except RuntimeError as e:
                    if "Audit trail storage failure" in str(e):
                        print("SUCCESS: System failed explicitly on storage failure")
                        print(f"Error message: {e}")
                        return True
                    print(f"ERROR: Wrong error type: {e}")
                    return False
                except Exception as e:
                    print(f"ERROR: Unexpected error type: {e}")
                    return False

    except Exception as e:
        print(f"Test setup failed: {e}")
        return False


def test_no_fallback_invalid_confidence_score():
    """Test that invalid confidence scores cause explicit failure without fallbacks."""
    print("\nTesting NO FALLBACK behavior on invalid confidence score...")

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            audit_trail = ComprehensiveAuditTrail(
                audit_dir=temp_dir + "/audit",
                enable_cryptographic_signing=True
            )

            # Test with invalid confidence score (should fail without fallback)
            try:
                audit_trail.log_agent_decision(
                    agent_type="test_agent",
                    agent_id="test_001",
                    decision={"test": "decision"},
                    confidence_score=1.5,  # Invalid: > 1.0
                    alternatives_considered=[],
                    rationale="test rationale",
                    input_context={},
                    processing_time=1.0
                )
                print("ERROR: System accepted invalid confidence score!")
                return False
            except ValueError as e:
                if "Confidence score must be between 0.0 and 1.0" in str(e):
                    print("SUCCESS: System rejected invalid confidence score")
                    print(f"Error message: {e}")
                    return True
                print(f"ERROR: Wrong error message: {e}")
                return False
            except Exception as e:
                print(f"ERROR: Unexpected error type: {e}")
                return False

    except Exception as e:
        print(f"Test setup failed: {e}")
        return False


def main():
    """Run all NO FALLBACK tests."""
    print("TASK 22 NO FALLBACK VALIDATION TESTS")
    print("=" * 35)

    tests = [
        test_no_fallback_cryptographic_failure,
        test_no_fallback_audit_storage_failure,
        test_no_fallback_invalid_confidence_score
    ]

    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"Test {test_func.__name__} failed with exception: {e}")
            results.append(False)

    successful_tests = sum(results)
    total_tests = len(results)

    print("\nNO FALLBACK TEST RESULTS:")
    print(f"Tests Passed: {successful_tests}/{total_tests}")
    print(f"Success Rate: {successful_tests/total_tests*100:.1f}%")

    if successful_tests == total_tests:
        print("\nSUCCESS: All NO FALLBACK tests passed")
        print("System properly fails explicitly without fallbacks")
        return True
    print(f"\nFAILURE: {total_tests - successful_tests} tests failed")
    return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
