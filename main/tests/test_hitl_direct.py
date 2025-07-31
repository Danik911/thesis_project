#!/usr/bin/env python3
"""
Direct test of HITL consultation system.
This bypasses the workflow to test consultation directly.
"""

import asyncio
import sys
from pathlib import Path

# Add main directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.human_consultation import HumanConsultationManager
from src.core.events import ConsultationRequiredEvent
from src.shared.config import get_config
from uuid import uuid4

class TestContext:
    """Simple test context that simulates real consultation interaction."""
    
    def __init__(self):
        self.data = {}
        self.events = []
        self.response_future = None
    
    async def set(self, key, value):
        self.data[key] = value
    
    async def get(self, key, default=None):
        return self.data.get(key, default)
    
    def send_event(self, event):
        print(f"📨 Event sent: {type(event).__name__}")
        self.events.append(event)
    
    async def wait_for_event(self, event_type):
        print(f"⏳ Waiting for {event_type.__name__}...")
        
        # Create a future that will be resolved when user provides input
        if not self.response_future:
            self.response_future = asyncio.Future()
        
        # Prompt user for input
        await self.prompt_user_consultation()
        
        # Wait for the response
        response = await self.response_future
        return response
    
    async def prompt_user_consultation(self):
        """Prompt user for consultation input and create response event."""
        from src.core.events import HumanResponseEvent
        from datetime import datetime, timezone
        
        print("\n" + "="*60)
        print("🧑‍⚕️ HUMAN CONSULTATION REQUIRED")
        print("="*60)
        print("Consultation Type: GAMP Categorization Failure")
        print("Context: Confidence 50% below threshold 60%")
        print("Document: test_urs_hitl.txt")
        print("\nPlease provide GAMP categorization decision:")
        print("Available categories:")
        print("  1 - Infrastructure Software")
        print("  3 - Non-configured Products") 
        print("  4 - Configured Products")
        print("  5 - Custom Applications")
        print()
        
        try:
            # Get user input
            category_input = input("Enter GAMP category (1, 3, 4, 5): ").strip()
            
            if category_input not in ['1', '3', '4', '5']:
                print("❌ Invalid category. Using conservative default: Category 5")
                category_input = '5'
            
            rationale = input("Enter rationale for decision: ").strip() or "User decision"
            confidence_input = input("Enter confidence level (0.0-1.0) [0.8]: ").strip() or "0.8"
            
            try:
                confidence = float(confidence_input)
                confidence = max(0.0, min(1.0, confidence))
            except ValueError:
                confidence = 0.8
                print(f"Invalid confidence, using default: {confidence}")
            
            # Get the consultation ID from the stored consultation event
            consultation_id = getattr(self, 'consultation_id', uuid4())
            session_id = getattr(self, 'session_id', uuid4())
            
            # Create response event
            response = HumanResponseEvent(
                consultation_id=consultation_id,  # Use the actual consultation ID
                session_id=session_id,           # Use the actual session ID
                response_type="categorization_decision",
                user_id="test_user",
                user_role="validation_engineer",
                response_data={
                    "gamp_category": int(category_input),
                    "rationale": rationale,
                    "confidence": confidence
                },
                decision_rationale=rationale,
                confidence_level=confidence
            )
            
            print(f"\n✅ Response recorded: Category {category_input} (confidence: {confidence:.1%})")
            
            # Resolve the future with the response
            if self.response_future and not self.response_future.done():
                self.response_future.set_result(response)
                
        except (EOFError, KeyboardInterrupt):
            print("\n👋 Consultation cancelled")
            # Create timeout event instead
            from src.core.events import ConsultationTimeoutEvent
            timeout_event = ConsultationTimeoutEvent(
                consultation_id=uuid4(),
                timeout_duration_seconds=0,
                conservative_action="Applied Category 5 (highest validation rigor)",
                escalation_required=True
            )
            if self.response_future and not self.response_future.done():
                self.response_future.set_result(timeout_event)

async def test_direct_consultation():
    """Test the consultation system directly."""
    print("🧪 Testing HITL Consultation System Directly")
    print("="*50)
    
    # Setup
    config = get_config()
    manager = HumanConsultationManager(config)
    ctx = TestContext()
    
    # Create consultation event
    consultation = ConsultationRequiredEvent(
        consultation_type="categorization_failure",
        context={
            "document_name": "test_urs_hitl.txt",
            "confidence": 0.50,
            "threshold": 0.60,
            "error": "Confidence below threshold"
        },
        urgency="high",
        required_expertise=["gamp_specialist"],
        triggering_step="categorization"
    )
    
    print(f"📋 Created consultation: {consultation.consultation_type}")
    print(f"📋 Consultation ID: {consultation.consultation_id}")
    
    # Store the consultation ID in context for the prompt
    ctx.consultation_id = consultation.consultation_id
    
    try:
        # Request consultation
        print("\n🔄 Requesting human consultation...")
        
        # Start the consultation to get the session ID
        consultation_task = asyncio.create_task(
            manager.request_consultation(
                ctx, 
                consultation, 
                timeout_seconds=60  # 60 second timeout
            )
        )
        
        # Wait briefly for session to be created
        await asyncio.sleep(0.1)
        
        # Get the session ID from the manager
        if manager.active_sessions:
            session_id = next(iter(manager.active_sessions.keys()))
            ctx.session_id = session_id
            print(f"📋 Session ID: {session_id}")
        
        # Wait for the consultation to complete
        result = await consultation_task
        
        print(f"\n✅ Consultation completed!")
        print(f"Result type: {type(result).__name__}")
        
        if hasattr(result, 'response_data'):
            print(f"Response data: {result.response_data}")
        if hasattr(result, 'conservative_action'):
            print(f"Conservative action: {result.conservative_action}")
            
    except Exception as e:
        print(f"\n❌ Error during consultation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_direct_consultation())