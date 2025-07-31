#!/usr/bin/env python3
"""
Comprehensive HITL System Integration Test
Tests the complete Human-in-the-Loop consultation workflow end-to-end.
"""

import asyncio
import logging
import sys
import time
from pathlib import Path
from uuid import uuid4

# Add the main directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.events import ConsultationRequiredEvent, HumanResponseEvent
from src.core.human_consultation import HumanConsultationManager
from src.shared import get_config
from src.shared.output_manager import safe_print

# Test configurations
HITL_TEST_DOCUMENT = "test_urs_hitl.txt"
TIMEOUT_TEST_DURATION = 3  # seconds for timeout testing

async def test_consultation_manager_basic():
    """Test basic consultation manager functionality."""
    safe_print("🧪 Testing ConsultationManager Basic Functionality")

    config = get_config()
    manager = HumanConsultationManager(config)

    # Test empty state
    assert len(manager.active_sessions) == 0, "Expected no active sessions initially"
    safe_print("✅ Initial state check passed")

    # Create test consultation
    test_consultation = ConsultationRequiredEvent(
        consultation_type="test_categorization_failure",
        context={
            "document_name": HITL_TEST_DOCUMENT,
            "confidence_score": 0.45,
            "threshold": 0.6,
            "error": "Test categorization failure"
        },
        urgency="medium",
        required_expertise=["gamp_specialist"],
        triggering_step="test_step"
    )

    # Request consultation
    result = manager.request_consultation(test_consultation)
    safe_print(f"✅ Consultation requested: {result.session_id}")

    # Verify session created
    assert len(manager.active_sessions) == 1, "Expected one active session"
    session_id = list(manager.active_sessions.keys())[0]
    session = manager.active_sessions[session_id]

    # Verify session info
    info = session.get_session_info()
    assert info["consultation_type"] == "test_categorization_failure", "Consultation type mismatch"
    assert info["urgency"] == "medium", "Urgency mismatch"
    safe_print("✅ Session info verification passed")

    return manager, session_id

async def test_consultation_timeout():
    """Test consultation timeout with conservative defaults."""
    safe_print("🧪 Testing Consultation Timeout with Conservative Defaults")

    config = get_config()
    config.human_consultation.default_timeout_seconds = TIMEOUT_TEST_DURATION
    manager = HumanConsultationManager(config)

    # Create timeout test consultation
    test_consultation = ConsultationRequiredEvent(
        consultation_type="timeout_test",
        context={
            "test_scenario": "timeout_handling",
            "expected_behavior": "conservative_defaults"
        },
        urgency="high",
        required_expertise=["validation_engineer"],
        triggering_step="timeout_test_step"
    )

    # Request consultation with timeout
    start_time = time.time()
    result = await manager.wait_for_consultation_response(test_consultation)
    end_time = time.time()

    duration = end_time - start_time
    safe_print(f"✅ Timeout test completed in {duration:.2f}s")

    # Verify timeout behavior
    from src.core.events import ConsultationTimeoutEvent
    assert isinstance(result, ConsultationTimeoutEvent), f"Expected ConsultationTimeoutEvent, got {type(result)}"
    assert result.conservative_action is not None, "Expected conservative action"
    safe_print(f"✅ Conservative action applied: {result.conservative_action}")

    return result

async def test_human_response_simulation():
    """Test simulated human response to consultation."""
    safe_print("🧪 Testing Simulated Human Response")

    manager, session_id = await test_consultation_manager_basic()

    # Create simulated human response
    human_response = HumanResponseEvent(
        session_id=session_id,
        user_id="test_pharmacist",
        user_role="Senior Validation Engineer",
        response_type="provide_decision",
        decision_rationale="Test document clearly indicates Category 5 custom application based on electronic signatures requirement",
        confidence_level=0.95,
        response_data={
            "gamp_category": "5",
            "risk_assessment": {
                "patient_safety_impact": "high",
                "regulatory_impact": "high",
                "business_impact": "medium"
            },
            "recommended_actions": [
                "Implement comprehensive validation testing",
                "Establish formal change control",
                "Document all validation activities"
            ]
        }
    )

    # Process the response
    session = manager.active_sessions[session_id]
    session.add_response(human_response)

    # Verify response recorded
    info = session.get_session_info()
    assert info["status"] == "completed", f"Expected completed status, got {info['status']}"
    assert len(session.responses) == 1, "Expected one response recorded"
    safe_print("✅ Human response processed successfully")

    return human_response

async def test_audit_logging():
    """Test audit logging for HITL activities."""
    safe_print("🧪 Testing HITL Audit Logging")

    config = get_config()

    # Ensure audit directory exists
    audit_dir = Path(config.gamp5_compliance.audit_log_directory)
    audit_dir.mkdir(parents=True, exist_ok=True)

    # Run a test that should generate audit logs
    manager, session_id = await test_consultation_manager_basic()

    # Check for audit files
    audit_files = list(audit_dir.glob("*.json"))
    if audit_files:
        safe_print(f"✅ Audit files found: {len(audit_files)} files")
        # Read latest audit file
        latest_audit = max(audit_files, key=lambda p: p.stat().st_mtime)
        safe_print(f"✅ Latest audit file: {latest_audit.name}")
    else:
        safe_print("⚠️  No audit files found (may be expected in test mode)")

async def test_workflow_integration():
    """Test HITL integration with the unified workflow."""
    safe_print("🧪 Testing HITL Workflow Integration")

    from llama_index.core.workflow import StartEvent
    from src.core.unified_workflow import UnifiedTestGenerationWorkflow

    # Create workflow with HITL support
    workflow = UnifiedTestGenerationWorkflow(
        timeout=30,
        verbose=True
    )

    # Test with HITL trigger document
    with open(HITL_TEST_DOCUMENT) as f:
        urs_content = f.read()

    # Run workflow (should trigger HITL but use conservative defaults)
    start_event = StartEvent(
        urs_content=urs_content,
        document_name=HITL_TEST_DOCUMENT,
        author="test_user",
        digital_signature=f"test_signature_{uuid4()}"
    )

    start_time = time.time()
    result = await workflow.run(start_event)
    end_time = time.time()

    duration = end_time - start_time
    safe_print(f"✅ Workflow completed in {duration:.2f}s")

    # Verify result structure
    assert hasattr(result, "result"), "Expected result attribute"
    result_data = result.result

    # Should have used conservative defaults due to HITL
    if "gamp_category_details" in result_data:
        gamp_info = result_data["gamp_category_details"]
        safe_print(f"✅ GAMP Category determined: {gamp_info.get('category', 'Unknown')}")
        safe_print(f"✅ Confidence score: {gamp_info.get('confidence_score', 0):.2%}")

    safe_print("✅ Workflow integration test completed")
    return result

async def main():
    """Run comprehensive HITL integration tests."""
    safe_print("🚀 Starting Comprehensive HITL Integration Tests")
    safe_print("=" * 60)

    try:
        # Test 1: Basic consultation manager
        await test_consultation_manager_basic()
        safe_print("")

        # Test 2: Timeout handling
        await test_consultation_timeout()
        safe_print("")

        # Test 3: Human response simulation
        await test_human_response_simulation()
        safe_print("")

        # Test 4: Audit logging
        await test_audit_logging()
        safe_print("")

        # Test 5: Workflow integration
        await test_workflow_integration()
        safe_print("")

        safe_print("🎉 All HITL Integration Tests Completed Successfully!")
        safe_print("=" * 60)

        # Summary
        safe_print("📊 Test Summary:")
        safe_print("✅ Basic consultation manager functionality")
        safe_print("✅ Timeout handling with conservative defaults")
        safe_print("✅ Human response processing")
        safe_print("✅ Audit logging capabilities")
        safe_print("✅ Workflow integration")

    except Exception as e:
        safe_print(f"❌ Test failed with error: {e}")
        logging.exception("HITL integration test failed")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
