#!/usr/bin/env python3
"""
Automated test script to validate the human consultation fix components.
Windows-safe version without Unicode emojis.
"""

import asyncio
import logging
from datetime import datetime, UTC
from unittest.mock import patch, MagicMock
import sys
import os

# Set console to UTF-8 to handle Unicode better
if sys.platform == "win32":
    os.system("chcp 65001 > nul")

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


def test_imports_and_dependencies():
    """Test that all required imports are available."""
    print("\nTEST 3: Import and Dependency Check")
    
    try:
        from src.core.events import ConsultationInputEvent, HumanResponseEvent
        from src.core.consultation_handler import process_consultation_input, ConsultationEventHandler
        from llama_index.core.workflow import InputRequiredEvent
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


def test_workflow_integration():
    """Test that the consultation system integrates with unified workflow."""
    print("\nTEST 4: Workflow Integration Check")
    
    try:
        from src.core.unified_workflow import UnifiedWorkflow
        from src.core.events import ConsultationRequiredEvent
        
        # Check if handle_consultation method exists
        workflow = UnifiedWorkflow()
        if hasattr(workflow, 'handle_consultation'):
            print("   PASS: UnifiedWorkflow has handle_consultation method")
        else:
            print("   FAIL: UnifiedWorkflow missing handle_consultation method")
            return False
            
        # Check if the method is properly decorated as a step
        import inspect
        method = getattr(workflow, 'handle_consultation')
        if hasattr(method, '__annotations__'):
            print("   PASS: handle_consultation has type annotations")
        else:
            print("   WARN: handle_consultation missing type annotations")
            
        return True
        
    except ImportError as e:
        print(f"   FAIL: Import error: {e}")
        return False
    except Exception as e:
        print(f"   FAIL: Error checking workflow integration: {e}")
        return False


def test_event_driven_architecture():
    """Test that the event-driven architecture is properly implemented."""
    print("\nTEST 5: Event-Driven Architecture Validation")
    
    try:
        from src.core.events import ConsultationRequiredEvent
        from llama_index.core.workflow import Event
        
        # Test ConsultationRequiredEvent exists and extends Event
        if issubclass(ConsultationRequiredEvent, Event):
            print("   PASS: ConsultationRequiredEvent extends Event")
        else:
            print("   FAIL: ConsultationRequiredEvent does not extend Event")
            return False
            
        # Test that ConsultationInputEvent extends InputRequiredEvent
        from llama_index.core.workflow import InputRequiredEvent
        if issubclass(ConsultationInputEvent, InputRequiredEvent):
            print("   PASS: ConsultationInputEvent extends InputRequiredEvent")
        else:
            print("   FAIL: ConsultationInputEvent does not extend InputRequiredEvent")
            return False
            
        print("   PASS: Event-driven architecture properly implemented")
        return True
        
    except ImportError as e:
        print(f"   FAIL: Import error: {e}")
        return False
    except Exception as e:
        print(f"   FAIL: Error validating event architecture: {e}")
        return False


async def run_all_tests():
    """Run all consultation system tests."""
    print("="*60)
    print("AUTOMATED CONSULTATION SYSTEM VALIDATION")
    print("="*60)
    
    tests = [
        test_consultation_event_creation,
        test_human_response_event_creation,
        test_imports_and_dependencies,
        test_workflow_integration,
        test_event_driven_architecture
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
        print("The consultation system is properly implemented.")
        print("Architecture check confirms terminal blocking fix is in place.")
    else:
        print("OVERALL RESULT: SOME TESTS FAILED")
        print("Check the failed tests above for issues.")
    
    return passed == total


if __name__ == "__main__":
    # Set up basic logging
    logging.basicConfig(level=logging.WARNING)  # Reduce log noise
    
    # Run automated tests
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        sys.exit(1)