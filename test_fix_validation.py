#!/usr/bin/env python3
"""
Test the categorization fix for URS-003.
"""

import sys
from pathlib import Path

# Add the main directory to path
sys.path.insert(0, str(Path(__file__).parent / "main"))

def test_confidence_tool_fix():
    """Test the confidence tool fix directly."""
    try:
        from src.agents.categorization.agent import confidence_tool_with_error_handling
        from src.agents.categorization.error_handler import CategorizationErrorHandler

        print("Testing confidence tool fix...")

        # Create mock category data similar to what URS-003 would generate
        category_data = {
            "predicted_category": 5,
            "evidence": {
                "strong_count": 3,
                "weak_count": 1,
                "exclusion_count": 0
            },
            "all_categories_analysis": {
                "1": {"strong_count": 0, "weak_count": 1, "exclusion_count": 2},
                "3": {"strong_count": 0, "weak_count": 2, "exclusion_count": 1},
                "4": {"strong_count": 1, "weak_count": 1, "exclusion_count": 1},
                "5": {"strong_count": 3, "weak_count": 1, "exclusion_count": 0}
            }
        }

        error_handler = CategorizationErrorHandler(confidence_threshold=0.50)

        print("Testing with category data:")
        print(f"  Predicted category: {category_data['predicted_category']}")
        print(f"  Strong indicators: {category_data['evidence']['strong_count']}")
        print(f"  Category 5 analysis: {category_data['all_categories_analysis']['5']}")

        confidence = confidence_tool_with_error_handling(category_data, error_handler)

        print("\\nResult:")
        print(f"  Confidence score: {confidence:.3f}")
        print("  Expected: High confidence (>0.70) for clear Category 5")

        if confidence > 0.70:
            print("SUCCESS: High confidence achieved for Category 5")
        else:
            print("ISSUE: Confidence should be higher for clear Category 5")

        return confidence > 0.70

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ambiguity_logic():
    """Test the ambiguity detection logic with fixed confidence scores."""
    try:
        from src.agents.categorization.error_handler import CategorizationErrorHandler

        print("\\nTesting ambiguity detection with fixed confidence scores...")

        error_handler = CategorizationErrorHandler(confidence_threshold=0.50)

        # Test case: Single high-confidence category (no ambiguity)
        confidence_scores_fixed = {5: 0.85}  # Only the predicted category

        mock_category_data = {
            "predicted_category": 5,
            "evidence": {"strong_count": 3, "weak_count": 1, "exclusion_count": 0}
        }

        ambiguity_error = error_handler.check_ambiguity(mock_category_data, confidence_scores_fixed)

        print(f"Confidence scores: {confidence_scores_fixed}")
        print(f"Ambiguity error: {ambiguity_error}")

        if ambiguity_error is None:
            print("SUCCESS: No false ambiguity detected")
            return True
        print(f"ISSUE: False ambiguity detected: {ambiguity_error.message}")
        return False

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Validating categorization accuracy fix...")
    print("=" * 60)

    success1 = test_confidence_tool_fix()
    success2 = test_ambiguity_logic()

    print("\\n" + "=" * 60)
    if success1 and success2:
        print("SUCCESS: ALL TESTS PASSED - Fix appears to be working correctly")
    else:
        print("FAILURE: SOME TESTS FAILED - Fix needs additional work")
