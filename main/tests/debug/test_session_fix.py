#!/usr/bin/env python3
"""
Quick test script to verify session ID fix works.
"""

import asyncio
import sys
import os
from uuid import uuid4
from unittest.mock import AsyncMock

# Add the src directory to Python path
sys.path.insert(0, '/home/anteb/thesis_project/main/src')

from core.events import ConsultationRequiredEvent, HumanResponseEvent
from core.human_consultation import ConsultationSession
from shared.config import Config, HumanConsultationConfig

async def test_session_id_fix():
    """Test that session ID mismatch is handled correctly."""
    
    print("🧪 Testing Session ID Fix...")
    
    # Create test config
    consultation_config = HumanConsultationConfig(
        default_timeout_seconds=2,
        conservative_gamp_category=5,
        authorized_roles=["validation_engineer"],
    )
    config = Config()
    config.human_consultation = consultation_config
    
    # Create consultation event
    consultation_event = ConsultationRequiredEvent(
        consultation_type="test_consultation",
        context={"test": "data"},
        urgency="medium",
        required_expertise=["test_expert"],
        triggering_step="test_step"
    )
    
    # Create mock compliance logger
    mock_logger = AsyncMock()
    mock_logger.log_audit_event = AsyncMock()
    
    try:
        # Create session
        session = ConsultationSession(
            consultation_event,
            config,
            mock_logger
        )
        
        print(f"✅ Session created with ID: {session.session_id}")
        
        # Create response with DIFFERENT session ID (simulating the bug)
        wrong_session_id = uuid4()
        human_response = HumanResponseEvent(
            response_type="decision",
            response_data={"test": "response"},
            user_id="test_user",
            user_role="validation_engineer",
            decision_rationale="Test decision",
            confidence_level=0.8,
            consultation_id=consultation_event.consultation_id,
            session_id=wrong_session_id,  # WRONG session ID
            approval_level="user"
        )
        
        print(f"📝 Response created with WRONG session ID: {wrong_session_id}")
        print(f"🔍 Session expects ID: {session.session_id}")
        
        # Try to add response - this should work now with the fix
        await session.add_response(human_response)
        
        print("✅ Response added successfully - session ID fix is working!")
        print(f"📊 Session has {len(session.responses)} response(s)")
        print(f"👥 Session participants: {session.participants}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test runner."""
    
    print("🚀 Session ID Fix Test")
    print("=" * 30)
    
    success = await test_session_id_fix()
    
    if success:
        print("\n✅ All tests passed! Session ID fix is working.")
    else:
        print("\n❌ Tests failed. Session ID fix needs more work.")
    
    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)