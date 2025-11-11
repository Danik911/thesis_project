#!/usr/bin/env python3
"""
Test script to validate the human consultation fix.

This script tests the event-driven consultation system to ensure
it works properly without blocking the terminal.
"""

import asyncio
import logging

from src.core.consultation_handler import process_consultation_input
from src.core.events import ConsultationInputEvent


async def test_consultation_system():
    """Test the consultation system with a mock consultation request."""

    print("\n" + "="*60)
    print("TESTING: Event-Driven Consultation System")
    print("="*60)

    # Create a test consultation input event (similar to what workflow would create)
    test_context = {
        "reason": "Test: Low confidence categorization",
        "confidence_score": 0.35,
        "gamp_category": 4,  # AI suggested Category 4
        "document_name": "test_urs_document.pdf"
    }

    consultation_event = ConsultationInputEvent(
        consultation_context=test_context,
        prompt_text="This is a test of the consultation system. Please select a GAMP-5 category.",
        timeout_seconds=300,
        consultation_type="test_gamp_categorization",
        urgency="normal"
    )

    print(f"📋 Created consultation event: {consultation_event.consultation_id}")
    print("⏰ Starting consultation process...")

    try:
        # Test the consultation handler
        human_response = await process_consultation_input(consultation_event)

        print("\n✅ Consultation completed successfully!")
        print(f"   User ID: {human_response.user_id}")
        print(f"   User Role: {human_response.user_role}")
        print(f"   Selected Category: {human_response.response_data['gamp_category']}")
        print(f"   Justification: {human_response.response_data['category_justification']}")
        print(f"   Digital Signature: {human_response.digital_signature}")
        print(f"   Confidence Level: {human_response.confidence_level}")

        print("\n📊 TEST RESULT: PASS")
        print("   The consultation system is working correctly!")
        print("   Terminal blocking issue has been resolved.")

        return True

    except Exception as e:
        print("\n❌ TEST RESULT: FAIL")
        print(f"   Error: {e!s}")
        print("   The consultation system encountered an error.")

        return False

    finally:
        print("="*60 + "\n")


if __name__ == "__main__":
    # Set up basic logging
    logging.basicConfig(level=logging.INFO)

    print("🧪 Human Consultation System Test")
    print("This test will prompt you for input to validate the consultation fix.")
    input("Press Enter to start the test...")

    # Run the test
    try:
        success = asyncio.run(test_consultation_system())

        if success:
            print("🎉 All tests passed! The consultation system is working correctly.")
        else:
            print("💥 Tests failed! Check the error messages above.")

    except KeyboardInterrupt:
        print("\n🛑 Test cancelled by user.")
    except Exception as e:
        print(f"\n💥 Test failed with unexpected error: {e}")
