#!/usr/bin/env python3
"""
Quick validation of ConsultationBypassedEvent creation and audit trail
"""

import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent / "main" / "src"))

from src.core.events import ConsultationBypassedEvent, ConsultationRequiredEvent


def test_bypass_event_creation():
    """Test that bypass events are created correctly with audit trail."""
    print("🧪 Testing ConsultationBypassedEvent Creation")

    # Create original consultation event
    original_consultation = ConsultationRequiredEvent(
        consultation_type="categorization_review",
        context={"gamp_category": 5, "confidence": 0.65},
        urgency="normal",
        required_expertise=["gamp_specialist", "validation_engineer"],
        triggering_step="check_consultation_required"
    )

    print(f"✅ Original consultation created: {original_consultation.consultation_type}")
    print(f"   ID: {original_consultation.consultation_id}")
    print(f"   Context: {original_consultation.context}")

    # Create bypass event
    bypass_event = ConsultationBypassedEvent(
        original_consultation=original_consultation,
        bypass_reason="validation_mode_enabled",
        consultation_type=original_consultation.consultation_type,
        triggering_step=original_consultation.triggering_step,
        original_context=original_consultation.context,
        confidence_score=0.65,
        gamp_category=5,
        quality_metrics={
            "original_confidence": 0.65,
            "gamp_category": 5,
            "bypass_threshold": 0.7,
            "validation_mode_active": True
        },
        audit_trail_preserved=True,
        regulatory_compliance_notes="Bypassed for validation testing - complete audit trail maintained"
    )

    print(f"✅ Bypass event created: {bypass_event.bypass_reason}")
    print(f"   Bypass ID: {bypass_event.consultation_id}")
    print(f"   Original consultation preserved: {bypass_event.original_consultation is not None}")
    print(f"   Audit trail preserved: {bypass_event.audit_trail_preserved}")

    # Validate audit trail completeness
    audit_complete = all([
        bypass_event.original_consultation == original_consultation,
        bypass_event.consultation_type == original_consultation.consultation_type,
        bypass_event.triggering_step == original_consultation.triggering_step,
        bypass_event.original_context == original_consultation.context,
        bypass_event.audit_trail_preserved == True
    ])

    print("\n📋 Audit Trail Validation:")
    print(f"   Original consultation ID: {original_consultation.consultation_id}")
    print(f"   Bypass event consultation ID: {bypass_event.consultation_id}")
    print(f"   Consultation types match: {bypass_event.consultation_type == original_consultation.consultation_type}")
    print(f"   Context preserved: {bypass_event.original_context == original_consultation.context}")
    print(f"   Triggering step preserved: {bypass_event.triggering_step == original_consultation.triggering_step}")
    print(f"   Quality metrics captured: {len(bypass_event.quality_metrics)} fields")

    print(f"\n🎯 Audit Trail Completeness: {'✅ COMPLETE' if audit_complete else '❌ INCOMPLETE'}")

    # Test event serialization (for logging)
    try:
        import json

        # Convert to dict for JSON serialization test
        bypass_dict = {
            "event_type": "ConsultationBypassedEvent",
            "consultation_id": str(bypass_event.consultation_id),
            "bypass_reason": bypass_event.bypass_reason,
            "bypass_timestamp": bypass_event.bypass_timestamp.isoformat(),
            "original_consultation": {
                "consultation_id": str(bypass_event.original_consultation.consultation_id),
                "consultation_type": bypass_event.original_consultation.consultation_type,
                "context": bypass_event.original_consultation.context
            },
            "quality_metrics": bypass_event.quality_metrics,
            "audit_trail_preserved": bypass_event.audit_trail_preserved,
            "regulatory_compliance_notes": bypass_event.regulatory_compliance_notes
        }

        json_str = json.dumps(bypass_dict, indent=2)
        print("\n💾 JSON Serialization Test: ✅ SUCCESS")
        print(f"   Serialized size: {len(json_str)} characters")

    except Exception as e:
        print(f"\n💾 JSON Serialization Test: ❌ FAILED - {e}")
        audit_complete = False

    return audit_complete

if __name__ == "__main__":
    success = test_bypass_event_creation()

    if success:
        print("\n🎉 ConsultationBypassedEvent implementation: ✅ VALIDATED")
    else:
        print("\n❌ ConsultationBypassedEvent implementation: ❌ NEEDS FIXES")

    sys.exit(0 if success else 1)
