"""
Quick Audit Coverage Verification Script

Tests the comprehensive audit trail system to verify 100% coverage
without running the full workflow. Focuses on testing each component
individually to confirm implementation.
"""

import asyncio
import sys
from pathlib import Path

# Add main to Python path
sys.path.insert(0, str(Path(__file__).parent / "main"))

from src.core.audit_trail import get_audit_trail, AuditEventType, AuditSeverity
from src.core.cryptographic_audit import get_audit_crypto

async def test_audit_coverage():
    """Test comprehensive audit trail coverage."""
    print("🔍 Testing Comprehensive Audit Trail Coverage")
    print("=" * 50)
    
    # Initialize audit trail
    audit_trail = get_audit_trail()
    crypto_audit = get_audit_crypto()
    
    coverage_tests = {
        "agent_decision_logging": False,
        "data_transformation_tracking": False,
        "state_transition_logging": False,
        "error_recovery_logging": False,
        "cryptographic_signatures": False
    }
    
    try:
        # Test 1: Agent Decision Logging
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
        coverage_tests["agent_decision_logging"] = audit_id is not None
        print(f"   ✅ Agent decision logged: {audit_id[:8]}...")
        
    except Exception as e:
        print(f"   ❌ Agent decision logging failed: {e}")
    
    try:
        # Test 2: Data Transformation Tracking
        print("2. Testing Data Transformation Tracking...")
        audit_id = audit_trail.log_data_transformation(
            transformation_type="test_transformation",
            source_data={"input": "test_data"},
            target_data={"output": "transformed_data"},
            transformation_rules=["test_rule_1", "test_rule_2"],
            transformation_metadata={"method": "test_transform"},
            workflow_step="test_step"
        )
        coverage_tests["data_transformation_tracking"] = audit_id is not None
        print(f"   ✅ Data transformation logged: {audit_id[:8]}...")
        
    except Exception as e:
        print(f"   ❌ Data transformation tracking failed: {e}")
    
    try:
        # Test 3: State Transition Logging
        print("3. Testing State Transition Logging...")
        audit_id = audit_trail.log_state_transition(
            from_state="test_state_1",
            to_state="test_state_2",
            transition_trigger="test_trigger",
            transition_metadata={"test": "metadata"},
            workflow_step="test_step"
        )
        coverage_tests["state_transition_logging"] = audit_id is not None
        print(f"   ✅ State transition logged: {audit_id[:8]}...")
        
    except Exception as e:
        print(f"   ❌ State transition logging failed: {e}")
    
    try:
        # Test 4: Error Recovery Logging
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
        coverage_tests["error_recovery_logging"] = audit_id is not None
        print(f"   ✅ Error recovery logged: {audit_id[:8]}...")
        
    except Exception as e:
        print(f"   ❌ Error recovery logging failed: {e}")
    
    try:
        # Test 5: Cryptographic Signatures
        print("5. Testing Cryptographic Signatures...")
        signed_entry = crypto_audit.sign_audit_event(
            event_type="test_signature",
            event_data={"test": "data"},
            workflow_context={"test": "context"}
        )
        
        # Verify signature
        signature_valid = crypto_audit.verify_audit_event(signed_entry)
        coverage_tests["cryptographic_signatures"] = signature_valid
        print(f"   ✅ Cryptographic signature valid: {signature_valid}")
        
    except Exception as e:
        print(f"   ❌ Cryptographic signatures failed: {e}")
    
    # Generate coverage report
    print("\n📊 COVERAGE REPORT:")
    print("-" * 30)
    
    total_tests = len(coverage_tests)
    passed_tests = sum(coverage_tests.values())
    coverage_percentage = (passed_tests / total_tests) * 100
    
    for test_name, passed in coverage_tests.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall Coverage: {coverage_percentage:.1f}%")
    print(f"Tests Passed: {passed_tests}/{total_tests}")
    
    # Get detailed audit statistics
    try:
        audit_report = audit_trail.get_audit_coverage_report()
        print(f"\nDetailed Audit Statistics:")
        print(f"Total Events: {audit_report['audit_statistics']['total_events']}")
        print(f"Cryptographic Signatures: {audit_report['audit_statistics']['cryptographic_signatures']}")
        print(f"Coverage Assessment: {audit_report['compliance_assessment']}")
        
    except Exception as e:
        print(f"Could not generate detailed report: {e}")
    
    if coverage_percentage >= 100.0:
        print("\n🎉 SUCCESS: 100% Audit Trail Coverage Achieved!")
        return True
    else:
        print(f"\n⚠️  INCOMPLETE: {100 - coverage_percentage:.1f}% coverage gap remaining")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_audit_coverage())
    sys.exit(0 if success else 1)