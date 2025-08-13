"""
Simple Audit Coverage Test Script

Tests the comprehensive audit trail system to verify 100% coverage.
"""

import asyncio
import sys
from pathlib import Path

# Add main to Python path
sys.path.insert(0, str(Path(__file__).parent / "main"))

from src.core.audit_trail import get_audit_trail
from src.core.cryptographic_audit import get_audit_crypto

async def test_audit_coverage():
    """Test comprehensive audit trail coverage."""
    print("Testing Comprehensive Audit Trail Coverage")
    print("=" * 50)
    
    # Initialize audit trail
    audit_trail = get_audit_trail()
    crypto_audit = get_audit_crypto()
    
    tests_passed = 0
    total_tests = 5
    
    # Test 1: Agent Decision Logging
    try:
        print("1. Testing Agent Decision Logging...")
        audit_id = audit_trail.log_agent_decision(
            agent_type="test_agent",
            agent_id="test_001",
            decision={"category": 4, "decision_type": "gamp_classification"},
            confidence_score=0.85,
            alternatives_considered=[{"category": 3, "confidence": 0.25}],
            rationale="Test rationale for decision logging",
            input_context={"test": "context"},
            processing_time=1.0
        )
        if audit_id:
            print("   PASS - Agent decision logged")
            tests_passed += 1
        else:
            print("   FAIL - No audit ID returned")
    except Exception as e:
        print(f"   FAIL - Agent decision logging error: {e}")
    
    # Test 2: Data Transformation Tracking
    try:
        print("2. Testing Data Transformation Tracking...")
        audit_id = audit_trail.log_data_transformation(
            transformation_type="test_transformation",
            source_data={"input": "test_data"},
            target_data={"output": "transformed_data"},
            transformation_rules=["test_rule_1", "test_rule_2"],
            transformation_metadata={"method": "test_transform"},
            workflow_step="test_step"
        )
        if audit_id:
            print("   PASS - Data transformation logged")
            tests_passed += 1
        else:
            print("   FAIL - No audit ID returned")
    except Exception as e:
        print(f"   FAIL - Data transformation error: {e}")
    
    # Test 3: State Transition Logging
    try:
        print("3. Testing State Transition Logging...")
        audit_id = audit_trail.log_state_transition(
            from_state="test_state_1",
            to_state="test_state_2",
            transition_trigger="test_trigger",
            transition_metadata={"test": "metadata"},
            workflow_step="test_step"
        )
        if audit_id:
            print("   PASS - State transition logged")
            tests_passed += 1
        else:
            print("   FAIL - No audit ID returned")
    except Exception as e:
        print(f"   FAIL - State transition error: {e}")
    
    # Test 4: Error Recovery Logging
    try:
        print("4. Testing Error Recovery Logging...")
        audit_id = audit_trail.log_error_recovery(
            error_type="test_error",
            error_message="Test error message",
            error_context={"error": "context"},
            recovery_strategy="test_recovery",
            recovery_actions=["action1", "action2"],
            recovery_success=True,
            workflow_step="test_step"
        )
        if audit_id:
            print("   PASS - Error recovery logged")
            tests_passed += 1
        else:
            print("   FAIL - No audit ID returned")
    except Exception as e:
        print(f"   FAIL - Error recovery error: {e}")
    
    # Test 5: Cryptographic Signatures
    try:
        print("5. Testing Cryptographic Signatures...")
        signed_entry = crypto_audit.sign_audit_event(
            event_type="test_signature",
            event_data={"test": "data"},
            workflow_context={"test": "context"}
        )
        
        # Verify signature
        signature_valid = crypto_audit.verify_audit_event(signed_entry)
        if signature_valid:
            print("   PASS - Cryptographic signature valid")
            tests_passed += 1
        else:
            print("   FAIL - Signature verification failed")
    except Exception as e:
        print(f"   FAIL - Cryptographic signatures error: {e}")
    
    # Generate coverage report
    print("\nCOVERAGE REPORT:")
    print("-" * 30)
    
    coverage_percentage = (tests_passed / total_tests) * 100
    print(f"Tests Passed: {tests_passed}/{total_tests}")
    print(f"Coverage: {coverage_percentage:.1f}%")
    
    # Get detailed audit statistics
    try:
        audit_report = audit_trail.get_audit_coverage_report()
        print(f"\nAudit Statistics:")
        print(f"Total Events: {audit_report['audit_statistics']['total_events']}")
        print(f"Cryptographic Signatures: {audit_report['audit_statistics']['cryptographic_signatures']}")
        print(f"Session ID: {audit_report['session_id']}")
        
        # Compliance assessment
        compliance = audit_report['compliance_assessment']
        print(f"\nCompliance Assessment:")
        for standard, compliant in compliance.items():
            status = "COMPLIANT" if compliant else "NON-COMPLIANT"
            print(f"  {standard}: {status}")
            
    except Exception as e:
        print(f"Could not generate detailed report: {e}")
    
    if coverage_percentage >= 100.0:
        print("\nSUCCESS: 100% Audit Trail Coverage Achieved!")
        return True
    else:
        print(f"\nINCOMPLETE: {100 - coverage_percentage:.1f}% coverage gap remaining")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_audit_coverage())
    sys.exit(0 if success else 1)