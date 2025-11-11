#!/usr/bin/env python3
"""
Automated test script to validate the human consultation fix components.

This script tests the consultation system architecture without requiring
interactive input, validating that the terminal blocking issue is resolved.
"""

import asyncio
import logging
import sys
from datetime import UTC, datetime
from unittest.mock import patch

from src.core.consultation_handler import ConsultationEventHandler
from src.core.events import ConsultationInputEvent, HumanResponseEvent


def test_consultation_event_creation():
    """Test that ConsultationInputEvent can be created properly."""
    print("TEST 1: ConsultationInputEvent Creation")

    try:
        test_context = {
            "reason": "Test: Low confidence categorization",
            "confidence_score": 0.35,
            "gamp_category": 4,
            "document_name": "test_urs_document.pdf"
        }

        consultation_event = ConsultationInputEvent(
            consultation_context=test_context,
            prompt_text="Test consultation prompt",
            timeout_seconds=300,
            consultation_type="test_gamp_categorization",
            urgency="normal"
        )

        print(f"   Consultation ID: {consultation_event.consultation_id}")
        print(f"   Event ID: {consultation_event.event_id}")
        print(f"   Timestamp: {consultation_event.timestamp}")
        print("   PASS: ConsultationInputEvent created successfully")
        return True

    except Exception as e:
        print(f"   FAIL: Error creating ConsultationInputEvent: {e}")
        return False


def test_human_response_event_creation():
    """Test that HumanResponseEvent can be created properly."""
    print("\nTEST 2: HumanResponseEvent Creation")

    try:
        from uuid import uuid4

        response_event = HumanResponseEvent(
            response_type="gamp_categorization_decision",
            response_data={
                "gamp_category": 5,
                "category_justification": "Custom application requiring full validation",
                "consultation_context": {"reason": "Low confidence"},
                "original_confidence": 0.35,
                "decision_timestamp": datetime.now(UTC).isoformat(),
            },
            user_id="Test_Operator",
            user_role="validation_engineer",
            decision_rationale="Test decision for validation",
            confidence_level=1.0,
            consultation_id=uuid4(),
            session_id=uuid4(),
            digital_signature="Test_Operator_TO001_20250829_082100",
            approval_level="validation_engineer",
            regulatory_impact="high"
        )

        print(f"   User ID: {response_event.user_id}")
        print(f"   Category: {response_event.response_data['gamp_category']}")
        print(f"   Confidence: {response_event.confidence_level}")
        print("   PASS: HumanResponseEvent created successfully")
        return True

    except Exception as e:
        print(f"   FAIL: Error creating HumanResponseEvent: {e}")
        return False


def test_consultation_handler_initialization():
    """Test that ConsultationEventHandler can be initialized."""
    print("\nTEST 3: ConsultationEventHandler Initialization")

    try:
        handler = ConsultationEventHandler()
        print(f"   Active consultations: {len(handler.active_consultations)}")
        print("   PASS: ConsultationEventHandler initialized successfully")
        return True

    except Exception as e:
        print(f"   FAIL: Error initializing ConsultationEventHandler: {e}")
        return False


async def test_consultation_handler_mock_input():
    """Test consultation handler with mocked input to avoid terminal blocking."""
    print("\nTEST 4: ConsultationEventHandler with Mocked Input")

    try:
        handler = ConsultationEventHandler()

        # Create test consultation event
        test_context = {
            "reason": "Test: Low confidence categorization",
            "confidence_score": 0.35,
            "gamp_category": 4,
            "document_name": "test_urs_document.pdf"
        }

        consultation_event = ConsultationInputEvent(
            consultation_context=test_context,
            prompt_text="Test consultation prompt",
            timeout_seconds=300,
            consultation_type="test_gamp_categorization",
            urgency="normal"
        )

        # Mock all input calls to simulate user responses
        mock_inputs = [
            "Test_Operator",           # Name
            "TO001",                   # Employee ID
            "1",                       # Role (Validation Engineer)
            "5",                       # GAMP Category (Custom Applications)
            "This is a custom developed pharmaceutical system requiring Category 5 validation"  # Justification
        ]

        with patch("builtins.input", side_effect=mock_inputs):
            # Test the consultation handler
            response = await handler.handle_consultation_input(consultation_event)

            print(f"   User ID: {response.user_id}")
            print(f"   User Role: {response.user_role}")
            print(f"   Selected Category: {response.response_data['gamp_category']}")
            print(f"   Digital Signature: {response.digital_signature}")
            print("   PASS: Consultation handler processed successfully without blocking")
            return True

    except Exception as e:
        print(f"   FAIL: Error in consultation handler: {e}")
        return False


def test_imports_and_dependencies():
    """Test that all required imports are available."""
    print("\nTEST 5: Import and Dependency Check")

    try:
        from llama_index.core.workflow import InputRequiredEvent
        from src.core.consultation_handler import (
            ConsultationEventHandler,
            process_consultation_input,
        )
        from src.core.events import ConsultationInputEvent, HumanResponseEvent
        print("   PASS: All required imports successful")

        # Test that ConsultationInputEvent extends InputRequiredEvent
        if issubclass(ConsultationInputEvent, InputRequiredEvent):
            print("   PASS: ConsultationInputEvent correctly extends InputRequiredEvent")
        else:
            print("   FAIL: ConsultationInputEvent does not extend InputRequiredEvent")
            return False

        return True

    except ImportError as e:
        print(f"   FAIL: Import error: {e}")
        return False


async def run_all_tests():
    """Run all consultation system tests."""
    print("="*60)
    print("AUTOMATED CONSULTATION SYSTEM VALIDATION")
    print("="*60)

    tests = [
        test_consultation_event_creation,
        test_human_response_event_creation,
        test_consultation_handler_initialization,
        test_consultation_handler_mock_input,
        test_imports_and_dependencies
    ]

    results = []
    for test in tests:
        if asyncio.iscoroutinefunction(test):
            result = await test()
        else:
            result = test()
        results.append(result)

    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(results)
    total = len(results)

    print(f"Tests Passed: {passed}/{total}")

    if passed == total:
        print("OVERALL RESULT: ALL TESTS PASSED")
        print("The consultation system is properly implemented and should work without terminal blocking.")
    else:
        print("OVERALL RESULT: SOME TESTS FAILED")
        print("Check the failed tests above for issues.")

    return passed == total


if __name__ == "__main__":
    # Set up basic logging
    logging.basicConfig(level=logging.INFO)

    # Run automated tests
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        sys.exit(1)
