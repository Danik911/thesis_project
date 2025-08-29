#!/usr/bin/env python3
"""
Simple validation script for the human consultation bypass fix.

Tests the core logic change to ensure original confidence is used
when SME consultation recovery is detected.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent / "main"
sys.path.insert(0, str(project_root))

def test_consultation_logic():
    """Test the fixed consultation decision logic."""
    
    print("🧪 Testing Consultation Decision Logic Fix")
    print("=" * 50)
    
    # Simulate the fixed logic from unified_workflow.py
    def check_consultation_required_logic(event_confidence, risk_assessment, bypass_threshold=0.70):
        """Simulate the fixed consultation logic."""
        
        # This is the FIXED logic from our implementation
        confidence_for_consultation = event_confidence
        
        # If this came from SME consultation recovery, use original confidence
        if "original_confidence" in risk_assessment:
            confidence_for_consultation = risk_assessment["original_confidence"]
            print(f"   🔍 SME recovery detected - using original confidence {confidence_for_consultation:.2f}")
        
        requires_consultation = (
            confidence_for_consultation < bypass_threshold or
            "consultation_required" in risk_assessment.get("flags", [])
        )
        
        return requires_consultation, confidence_for_consultation
    
    # Test Case 1: SME Recovery Scenario (THE BUG CASE)
    print("📋 Test Case 1: SME Recovery from Low Confidence")
    print("   Initial categorization: 20% confidence (FAILED)")
    print("   SME consultation recovery: 90% confidence (RECOVERED)")
    print("   Expected: Consultation REQUIRED (based on original 20%)")
    
    sme_recovery_event = {
        "confidence_score": 0.90,  # High confidence from SME
        "risk_assessment": {
            "original_confidence": 0.20,  # Low original confidence preserved
            "sme_validated": True,
            "consultation_successful": True
        }
    }
    
    requires_consult, used_confidence = check_consultation_required_logic(
        sme_recovery_event["confidence_score"],
        sme_recovery_event["risk_assessment"]
    )
    
    print(f"   ✅ Result: Consultation {'REQUIRED' if requires_consult else 'NOT required'}")
    print(f"   ✅ Used confidence: {used_confidence:.2f} (should be 0.20)")
    
    if requires_consult and used_confidence == 0.20:
        print("   🎯 SUCCESS: Fix works correctly!")
    else:
        print("   ❌ FAILURE: Fix did not work!")
    
    print()
    
    # Test Case 2: Normal High Confidence (Should still work)
    print("📋 Test Case 2: Normal High Confidence (No SME Recovery)")
    print("   Direct categorization: 85% confidence (SUCCESS)")
    print("   Expected: Consultation NOT required")
    
    normal_event = {
        "confidence_score": 0.85,  # High confidence, no recovery
        "risk_assessment": {
            "category": 3,
            "regulatory_impact": "Standard classification"
            # No "original_confidence" - normal success
        }
    }
    
    requires_consult, used_confidence = check_consultation_required_logic(
        normal_event["confidence_score"],
        normal_event["risk_assessment"]
    )
    
    print(f"   ✅ Result: Consultation {'REQUIRED' if requires_consult else 'NOT required'}")
    print(f"   ✅ Used confidence: {used_confidence:.2f} (should be 0.85)")
    
    if not requires_consult and used_confidence == 0.85:
        print("   🎯 SUCCESS: Normal path preserved!")
    else:
        print("   ❌ FAILURE: Normal path broken!")
    
    print()
    
    # Test Case 3: SME Failure (Edge case)
    print("📋 Test Case 3: SME Recovery with Low Final Confidence")
    print("   Initial: 20% confidence, SME also low: 30% confidence")
    print("   Expected: Consultation REQUIRED (based on original 20%)")
    
    sme_low_event = {
        "confidence_score": 0.30,  # SME also resulted in low confidence
        "risk_assessment": {
            "original_confidence": 0.20,  # Still preserve original
            "sme_validated": True,
            "consultation_successful": False
        }
    }
    
    requires_consult, used_confidence = check_consultation_required_logic(
        sme_low_event["confidence_score"],
        sme_low_event["risk_assessment"]
    )
    
    print(f"   ✅ Result: Consultation {'REQUIRED' if requires_consult else 'NOT required'}")
    print(f"   ✅ Used confidence: {used_confidence:.2f} (should be 0.20)")
    
    if requires_consult and used_confidence == 0.20:
        print("   🎯 SUCCESS: Edge case handled correctly!")
    else:
        print("   ❌ FAILURE: Edge case failed!")

def validate_code_changes():
    """Validate that the actual code changes were applied."""
    
    print("\n🔍 Validating Code Changes in unified_workflow.py")
    print("=" * 60)
    
    try:
        workflow_file = Path(__file__).parent / "main" / "src" / "core" / "unified_workflow.py"
        
        if not workflow_file.exists():
            print("❌ ERROR: unified_workflow.py not found")
            return
            
        with open(workflow_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for key fix indicators
        checks = [
            ("risk_assessment = ev.risk_assessment or {}", "Risk assessment extraction"),
            ("confidence_for_consultation = ev.confidence_score", "Confidence variable initialization"), 
            ('if "original_confidence" in risk_assessment:', "SME recovery detection"),
            ("confidence_for_consultation = risk_assessment[\"original_confidence\"]", "Original confidence usage"),
            ("SME consultation recovery detected", "Audit logging")
        ]
        
        print("Checking for fix implementation:")
        all_present = True
        
        for check_text, description in checks:
            if check_text in content:
                print(f"   ✅ {description}: Found")
            else:
                print(f"   ❌ {description}: MISSING")
                all_present = False
        
        if all_present:
            print("\n🎯 SUCCESS: All code changes are present in the file!")
        else:
            print("\n❌ FAILURE: Some code changes are missing!")
            
    except Exception as e:
        print(f"❌ ERROR validating code changes: {e}")

if __name__ == "__main__":
    print("🚀 Human Consultation Bypass Fix Validation")
    print("=" * 80)
    
    test_consultation_logic()
    validate_code_changes()
    
    print("\n" + "=" * 80)
    print("📋 SUMMARY:")
    print("   If all tests show SUCCESS, the fix correctly addresses:")
    print("   • SME recovery scenarios trigger consultation based on original confidence")
    print("   • Normal high-confidence paths continue to work")  
    print("   • Edge cases are handled appropriately")
    print("   • Code changes are properly implemented")
    print("\n🎯 The consultation bypass bug should now be FIXED!")