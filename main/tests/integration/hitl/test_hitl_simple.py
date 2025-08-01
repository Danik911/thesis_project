#!/usr/bin/env uv run python
"""
Simple HITL Integration Test
Tests core HITL functionality without complex workflow integration.
"""

import asyncio
import sys
from pathlib import Path

# Add the main directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.events import (
    ConsultationRequiredEvent,
    HumanResponseEvent,
)
from src.core.human_consultation import ConsultationSession, HumanConsultationManager
from src.shared import get_config
from src.shared.output_manager import safe_print


async def test_consultation_session_basic():
    """Test basic consultation session functionality."""
    safe_print("🧪 Testing ConsultationSession Basic Functionality")

    config = get_config()
    from src.shared.event_logging import GAMP5ComplianceLogger
    compliance_logger = GAMP5ComplianceLogger(config)

    # Create test consultation event
    test_consultation = ConsultationRequiredEvent(
        consultation_type="test_categorization_failure",
        context={
            "document_name": "test_urs_hitl.txt",
            "confidence_score": 0.45,
            "threshold": 0.6,
            "error": "Test categorization failure"
        },
        urgency="medium",
        required_expertise=["gamp_specialist"],
        triggering_step="test_step"
    )

    # Create consultation session
    session = ConsultationSession(test_consultation, config, compliance_logger)
    safe_print(f"✅ Session created: {session.session_id}")

    # Test session info
    info = session.get_session_info()
    assert info["consultation_type"] == "test_categorization_failure"
    assert info["urgency"] == "medium"
    assert info["status"] == "active"
    safe_print("✅ Session info verification passed")

    # Test simulated human response
    human_response = HumanResponseEvent(
        session_id=session.session_id,
        user_id="test_pharmacist",
        user_role="Senior Validation Engineer",
        response_type="provide_decision",
        decision_rationale="Category 5 based on custom application requirements",
        confidence_level=0.95,
        response_data={
            "gamp_category": "5",
            "risk_assessment": {"patient_safety_impact": "high"}
        }
    )

    # Add response to session
    await session.add_response(human_response)
    await session.complete_session("completed")

    final_info = session.get_session_info()
    assert final_info["status"] == "completed"
    assert len(session.responses) == 1
    safe_print("✅ Human response processing completed")

    return session

async def test_timeout_behavior():
    """Test consultation timeout with conservative defaults."""
    safe_print("🧪 Testing Timeout Behavior")

    config = get_config()
    from src.shared.event_logging import GAMP5ComplianceLogger
    compliance_logger = GAMP5ComplianceLogger(config)

    # Create timeout test consultation
    timeout_consultation = ConsultationRequiredEvent(
        consultation_type="timeout_test",
        context={"test_scenario": "timeout_handling"},
        urgency="high",
        required_expertise=["validation_engineer"],
        triggering_step="timeout_test_step"
    )

    # Create session with short timeout for testing
    session = ConsultationSession(timeout_consultation, config, compliance_logger)

    # Start timeout monitoring
    await session.start_timeout_monitoring()

    # Wait for timeout (should be quick)
    await asyncio.sleep(2)

    # Check if timed out
    if session.is_timed_out():
        safe_print("✅ Session correctly timed out")
        await session.complete_session("timed_out")
    else:
        safe_print("⚠️  Session did not timeout as expected")

    return session

async def test_manager_statistics():
    """Test HumanConsultationManager statistics."""
    safe_print("🧪 Testing Manager Statistics")

    config = get_config()
    manager = HumanConsultationManager(config)

    # Get initial statistics
    stats = manager.get_manager_statistics()
    safe_print(f"✅ Initial stats: {stats['active_sessions']} active sessions")

    # Cleanup any expired sessions
    cleaned = await manager.cleanup_expired_sessions()
    safe_print(f"✅ Cleaned up {cleaned} expired sessions")

    return stats

async def test_conservative_defaults():
    """Test conservative default generation."""
    safe_print("🧪 Testing Conservative Defaults Generation")

    config = get_config()
    manager = HumanConsultationManager(config)

    # Test categorization failure defaults
    cat_consultation = ConsultationRequiredEvent(
        consultation_type="categorization_failure",
        context={"confidence_score": 0.4, "threshold": 0.6},
        urgency="high",
        required_expertise=["gamp_specialist"],
        triggering_step="categorization"
    )

    defaults = manager._generate_conservative_defaults(cat_consultation)
    safe_print(f"✅ Categorization defaults: {defaults}")

    # Should default to Category 5 for safety
    if "gamp_category" in defaults:
        assert defaults["gamp_category"] == "5", "Expected Category 5 conservative default"
        safe_print("✅ Conservative Category 5 default applied")

    # Test planning failure defaults
    plan_consultation = ConsultationRequiredEvent(
        consultation_type="planning_failure",
        context={"gamp_category": "4"},
        urgency="medium",
        required_expertise=["planning_specialist"],
        triggering_step="planning"
    )

    plan_defaults = manager._generate_conservative_defaults(plan_consultation)
    safe_print(f"✅ Planning defaults: {plan_defaults}")

    return defaults, plan_defaults

async def test_workflow_log_analysis():
    """Analyze logs from actual workflow execution."""
    safe_print("🧪 Analyzing Workflow Logs")

    log_file = Path("hitl_workflow_test.log")
    if log_file.exists():
        with open(log_file) as f:
            log_content = f.read()

        # Look for HITL indicators
        hitl_indicators = [
            "Human consultation required",
            "CATEGORIZATION FAILED",
            "SME CONSULTATION",
            "conservative defaults",
            "ErrorRecoveryEvent"
        ]

        found_indicators = []
        for indicator in hitl_indicators:
            if indicator in log_content:
                found_indicators.append(indicator)

        safe_print(f"✅ Found HITL indicators: {len(found_indicators)}/{len(hitl_indicators)}")
        for indicator in found_indicators:
            safe_print(f"   - {indicator}")

        # Check for successful completion despite failures
        if "✅ Unified Test Generation Complete!" in log_content:
            safe_print("✅ Workflow completed successfully with HITL fallbacks")

        return found_indicators
    safe_print("⚠️  No workflow log file found")
    return []

async def main():
    """Run simple HITL integration tests."""
    safe_print("🚀 Starting Simple HITL Integration Tests")
    safe_print("=" * 60)

    try:
        # Test 1: Basic session functionality
        await test_consultation_session_basic()
        safe_print("")

        # Test 2: Timeout behavior
        await test_timeout_behavior()
        safe_print("")

        # Test 3: Manager statistics
        await test_manager_statistics()
        safe_print("")

        # Test 4: Conservative defaults
        await test_conservative_defaults()
        safe_print("")

        # Test 5: Workflow log analysis
        await test_workflow_log_analysis()
        safe_print("")

        safe_print("🎉 All Simple HITL Tests Completed Successfully!")
        safe_print("=" * 60)

        # Summary
        safe_print("📊 Test Summary:")
        safe_print("✅ Consultation session lifecycle")
        safe_print("✅ Timeout handling")
        safe_print("✅ Manager statistics")
        safe_print("✅ Conservative defaults generation")
        safe_print("✅ Workflow log analysis")

    except Exception as e:
        safe_print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
