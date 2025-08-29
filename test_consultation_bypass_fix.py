#!/usr/bin/env python3
"""
Test script to validate the human consultation bypass fix.

This test simulates the critical scenario where:
1. Initial categorization fails with 20% confidence
2. SME consultation recovers to 90% confidence  
3. System should still require human consultation based on ORIGINAL 20% confidence

EXPECTED RESULT: Consultation should be required despite SME recovery to 90%
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, UTC
from uuid import uuid4

# Add project root to Python path
project_root = Path(__file__).parent / "main"
sys.path.insert(0, str(project_root))

from src.core.unified_workflow import UnifiedWorkflow
from src.shared.models import GAMPCategory, GAMPCategorizationEvent, ConsultationRequiredEvent
from src.shared.config import config
from llamaindex.core.workflow import Context

async def test_consultation_bypass_fix():
    """Test that SME recovery doesn't bypass required human consultation."""
    
    print("🧪 Testing Human Consultation Bypass Fix")
    print("=" * 60)
    
    # Create workflow instance
    workflow = UnifiedWorkflow(
        timeout=120,
        enable_human_consultation=True  # Ensure consultation is enabled
    )
    
    # Create test event simulating SME consultation recovery
    # This simulates what the error_handler returns after SME consultation
    test_event = GAMPCategorizationEvent(
        gamp_category=GAMPCategory.CATEGORY_4,
        confidence_score=0.90,  # HIGH confidence from SME recovery
        justification="SME Consultation Result: Category 4 recommended based on expert analysis",
        risk_assessment={
            "category": 4,
            "sme_validated": True,
            "consultation_successful": True,
            "original_confidence": 0.20,  # CRITICAL: Original LOW confidence preserved
            "sme_confidence": 0.90,
            "regulatory_impact": "SME-validated Category 4"
        },
        event_id=uuid4(),
        timestamp=datetime.now(UTC),
        categorized_by="SMEAgent",
        review_required=False
    )
    
    print(f"📊 Test Event Created:")
    print(f"   Category: {test_event.gamp_category.value}")
    print(f"   Current Confidence: {test_event.confidence_score:.2f} (90% - SME recovery)")
    print(f"   Original Confidence: {test_event.risk_assessment['original_confidence']:.2f} (20% - initial failure)")
    print(f"   SME Validated: {test_event.risk_assessment['sme_validated']}")
    print()
    
    # Test the fixed method
    try:
        # Create context
        ctx = Context()
        
        # Call the fixed method
        print("🔍 Calling check_consultation_required...")
        result = await workflow.check_consultation_required(ctx, test_event)
        
        print(f"📋 Result Type: {type(result).__name__}")
        
        if isinstance(result, ConsultationRequiredEvent):
            print("✅ SUCCESS: Consultation correctly required!")
            print(f"   Consultation Type: {result.consultation_type}")
            print(f"   Reason: {result.context['reason']}")
            print(f"   Original Confidence Used: {result.context['original_confidence']:.2f}")
            print(f"   SME Recovery Detected: {result.context['sme_recovery']}")
            print(f"   Current Confidence: {result.context['confidence_score']:.2f}")
            
            # Verify the fix worked correctly
            if result.context['original_confidence'] == 0.20:
                print("✅ VALIDATION: Original confidence (20%) correctly used for decision")
            else:
                print(f"❌ ERROR: Wrong confidence used - expected 0.20, got {result.context['original_confidence']}")
                
        else:
            print(f"❌ FAILURE: Expected ConsultationRequiredEvent, got {type(result).__name__}")
            print("   This indicates the fix did not work - consultation was bypassed!")
            
    except Exception as e:
        print(f"❌ ERROR: Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        
    print()
    print("🧪 Test Complete")
    print("=" * 60)

async def test_normal_high_confidence():
    """Test that normal high-confidence categorizations still work correctly."""
    
    print("🧪 Testing Normal High-Confidence Path (Should NOT require consultation)")
    print("=" * 70)
    
    workflow = UnifiedWorkflow(
        timeout=120,
        enable_human_consultation=True
    )
    
    # Create normal high-confidence event (no SME recovery)
    test_event = GAMPCategorizationEvent(
        gamp_category=GAMPCategory.CATEGORY_3,
        confidence_score=0.85,  # High confidence, no recovery
        justification="Direct categorization with high confidence",
        risk_assessment={
            "category": 3,
            "regulatory_impact": "Standard Category 3 classification"
            # No "original_confidence" - this is a normal successful categorization
        },
        event_id=uuid4(),
        timestamp=datetime.now(UTC),
        categorized_by="CategorizationAgent",
        review_required=False
    )
    
    print(f"📊 Normal Event Created:")
    print(f"   Category: {test_event.gamp_category.value}")
    print(f"   Confidence: {test_event.confidence_score:.2f} (85% - direct success)")
    print(f"   No SME Recovery: {'original_confidence' not in test_event.risk_assessment}")
    print()
    
    try:
        ctx = Context()
        result = await workflow.check_consultation_required(ctx, test_event)
        
        print(f"📋 Result Type: {type(result).__name__}")
        
        if isinstance(result, ConsultationRequiredEvent):
            print("❌ UNEXPECTED: Consultation required for high-confidence categorization")
            print("   This may indicate the fix broke normal operation")
        else:
            print("✅ SUCCESS: No consultation required for high-confidence categorization")
            print("   Normal operation preserved")
            
    except Exception as e:
        print(f"❌ ERROR: Normal test failed: {e}")
        
    print()
    print("🧪 Normal Test Complete")
    print("=" * 70)

if __name__ == "__main__":
    print("🚀 Starting Human Consultation Bypass Fix Validation")
    print("=" * 80)
    print()
    
    # Run both tests
    asyncio.run(test_consultation_bypass_fix())
    print()
    asyncio.run(test_normal_high_confidence())
    
    print()
    print("💡 How to interpret results:")
    print("   ✅ SUCCESS: SME recovery test requires consultation (original 20% confidence)")
    print("   ✅ SUCCESS: Normal high-confidence test skips consultation (85% confidence)")
    print("   ❌ FAILURE: Either test produces unexpected results")
    print()
    print("🎯 If both tests pass, the fix correctly addresses the consultation bypass bug!")