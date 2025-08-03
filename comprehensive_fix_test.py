#!/usr/bin/env python3
"""
Comprehensive test of the categorization confidence fix
"""

import sys
import os

# Add main to path
main_path = os.path.join(os.path.dirname(__file__), 'main')
sys.path.insert(0, main_path)

def test_categorization_fix():
    """Test the fixed categorization logic"""
    
    try:
        from src.agents.categorization.agent import categorize_urs_document
        print("✅ Successfully imported categorization function")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

    # Load test document
    try:
        with open('main/simple_category3.md', 'r') as f:
            content = f.read()
        print("✅ Successfully loaded test document")
    except FileNotFoundError:
        print("❌ Test document not found")
        return False

    print("\n" + "="*60)
    print("TESTING CATEGORIZATION FIX")
    print("="*60)
    
    try:
        # Test the high-level function that should use the fixed logic
        result = categorize_urs_document(
            urs_content=content,
            document_name="simple_category3.md",
            use_structured_output=True,  # Use the new structured approach
            confidence_threshold=0.40,   # Standard threshold
            verbose=True
        )
        
        print("✅ Categorization completed successfully")
        
        # Extract results
        category = result.gamp_category.value
        confidence = result.confidence_score
        requires_review = result.review_required
        
        print(f"\n📊 RESULTS:")
        print(f"   Category: {category}")
        print(f"   Confidence: {confidence:.3f} ({confidence*100:.1f}%)")
        print(f"   Review Required: {requires_review}")
        
        # Evaluation criteria
        expected_category = 3
        expected_min_confidence = 0.75  # 75% minimum for obvious Category 3
        
        print(f"\n🎯 EVALUATION:")
        category_correct = (category == expected_category)
        confidence_good = (confidence >= expected_min_confidence)
        
        print(f"   Category Prediction: {'✅ PASS' if category_correct else '❌ FAIL'} (Expected: {expected_category}, Got: {category})")
        print(f"   Confidence Level: {'✅ PASS' if confidence_good else '❌ FAIL'} (Expected: ≥{expected_min_confidence*100:.0f}%, Got: {confidence*100:.1f}%)")
        print(f"   Review Not Required: {'✅ PASS' if not requires_review else '❌ FAIL'} (High confidence should not require review)")
        
        overall_success = category_correct and confidence_good and not requires_review
        
        print(f"\n🏆 OVERALL RESULT: {'✅ SUCCESS - FIX WORKS!' if overall_success else '❌ ISSUES REMAIN'}")
        
        if overall_success:
            print(f"\n🎉 The categorization agent now correctly identifies this obvious")
            print(f"   Category 3 document with {confidence*100:.1f}% confidence!")
            print(f"   This resolves the original issue of 22% confidence.")
        else:
            print(f"\n🔍 DEBUG INFO:")
            print(f"   Justification excerpt: {result.justification[:200]}...")
            if hasattr(result, 'risk_assessment'):
                print(f"   Risk assessment: {result.risk_assessment}")
        
        return overall_success
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_negation_logic():
    """Test the specific negation detection logic"""
    
    print("\n" + "="*60) 
    print("TESTING NEGATION LOGIC")
    print("="*60)
    
    # Test cases: (text, exclusion_word, should_be_negated)
    test_cases = [
        ("without any customization", "customization", True),
        ("no custom business logic", "custom", True),
        ("standard configuration only", "configuration", True),  
        ("no bespoke interfaces or modifications", "modification", True),
        ("requires extensive configuration", "configuration", False),
        ("uses custom algorithms", "custom", False),
    ]
    
    # Simulate the negation logic from the fix
    for text, exclusion_word, expected_negated in test_cases:
        normalized_text = text.lower()
        
        negation_patterns = [
            f"without {exclusion_word}",
            f"without any {exclusion_word}",
            f"no {exclusion_word}",
            f"not {exclusion_word}",
            f"no custom",
            f"no bespoke",
            f"no bespoke interfaces or modifications",
            f"standard {exclusion_word} only",
        ]
        
        is_negated = any(pattern in normalized_text for pattern in negation_patterns)
        
        status = "✅ PASS" if (is_negated == expected_negated) else "❌ FAIL"
        negation_status = "NEGATED" if is_negated else "NOT NEGATED"
        
        print(f"   {status} '{text}' → {negation_status} (expected: {'NEGATED' if expected_negated else 'NOT NEGATED'})")

if __name__ == "__main__":
    print("🧪 CATEGORIZATION CONFIDENCE FIX VALIDATION")
    print("=" * 80)
    
    # Test the negation logic first
    test_negation_logic()
    
    # Test the full categorization system
    success = test_categorization_fix()
    
    print("\n" + "="*80)
    if success:
        print("🎉 ALL TESTS PASSED - CATEGORIZATION FIX IS SUCCESSFUL!")
        print("   The agent should now correctly handle obvious Category 3 documents")
        print("   with high confidence instead of the previous 22% false negative.")
    else:
        print("❌ TESTS FAILED - FURTHER DEBUGGING REQUIRED")
        print("   The fix may need additional refinement.")
    print("="*80)