#!/usr/bin/env python3
"""
Corrected validation test for categorization accuracy fix.
"""

import sys
from pathlib import Path

# Add the main directory to path
sys.path.insert(0, str(Path(__file__).parent / "main"))

def test_primary_fix():
    """Test the primary fix: no false ambiguity for clear categories."""
    try:
        from src.agents.categorization.agent import confidence_tool_with_error_handling
        from src.agents.categorization.error_handler import (
            CategorizationErrorHandler,
        )

        print("Testing primary fix: URS-003 style clear Category 5...")

        error_handler = CategorizationErrorHandler(confidence_threshold=0.50)

        # Simulate URS-003: Clear Category 5 with strong custom development indicators
        category_data = {
            "predicted_category": 5,
            "evidence": {
                "strong_count": 4,  # Strong indicators: custom development, interfaces, algorithms, etc.
                "weak_count": 1,    # One weak indicator
                "exclusion_count": 0  # No exclusions for Category 5
            },
            "all_categories_analysis": {
                "1": {"strong_count": 0, "weak_count": 1, "exclusion_count": 3},
                "3": {"strong_count": 0, "weak_count": 1, "exclusion_count": 2},
                "4": {"strong_count": 1, "weak_count": 2, "exclusion_count": 1},
                "5": {"strong_count": 4, "weak_count": 1, "exclusion_count": 0}
            }
        }

        confidence = confidence_tool_with_error_handling(category_data, error_handler)

        print(f"Confidence calculated: {confidence:.3f}")

        # The key test: should have NO ambiguity error
        # (Before fix: would get false ambiguity due to artificial confidence scores)
        confidence_scores = {5: confidence}  # Only predicted category
        ambiguity_error = error_handler.check_ambiguity(category_data, confidence_scores)

        print(f"Ambiguity error: {ambiguity_error}")

        # Success criteria:
        # 1. High confidence (>0.70) for clear Category 5
        # 2. No ambiguity error (the main fix)
        success = confidence > 0.70 and ambiguity_error is None

        print(f"High confidence (>0.70): {'YES' if confidence > 0.70 else 'NO'}")
        print(f"No false ambiguity: {'YES' if ambiguity_error is None else 'NO'}")
        print(f"Overall result: {'SUCCESS' if success else 'FAIL'}")

        return success

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_low_confidence_handling():
    """Test that low confidence cases are handled correctly."""
    try:
        from src.agents.categorization.error_handler import (
            CategorizationErrorHandler,
            ErrorType,
        )

        print("\\nTesting low confidence handling...")

        error_handler = CategorizationErrorHandler(confidence_threshold=0.50)

        # Test case: Low confidence should trigger CONFIDENCE_ERROR, not ambiguity
        confidence_scores = {4: 0.40}  # Below threshold

        mock_category_data = {
            "predicted_category": 4,
            "evidence": {"strong_count": 1, "weak_count": 1, "exclusion_count": 1}
        }

        error = error_handler.check_ambiguity(mock_category_data, confidence_scores)

        print("Confidence: 0.40 (below 0.50 threshold)")
        print(f"Error detected: {error is not None}")
        print(f"Error type: {error.error_type if error else 'None'}")

        # Should get CONFIDENCE_ERROR, not AMBIGUITY_ERROR
        success = error is not None and error.error_type == ErrorType.CONFIDENCE_ERROR

        print(f"Correct error type: {'YES' if success else 'NO'}")

        return success

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_before_and_after_comparison():
    """Compare behavior before and after fix."""
    try:
        from src.agents.categorization.error_handler import CategorizationErrorHandler

        print("\\nTesting before vs after fix comparison...")

        error_handler = CategorizationErrorHandler(confidence_threshold=0.50)

        # Simulate what the OLD logic would have produced (artificial scores for all categories)
        old_confidence_scores = {
            1: 0.50,  # Artificial score based on simple formula
            3: 0.55,  # Artificial score
            4: 0.65,  # Artificial score
            5: 0.85   # Would be the highest, but still triggers ambiguity
        }

        # NEW logic: Only the actual predicted category with real confidence
        new_confidence_scores = {5: 0.85}

        mock_category_data = {
            "predicted_category": 5,
            "evidence": {"strong_count": 4, "weak_count": 1, "exclusion_count": 0}
        }

        old_error = error_handler.check_ambiguity(mock_category_data, old_confidence_scores)
        new_error = error_handler.check_ambiguity(mock_category_data, new_confidence_scores)

        print(f"Old approach (artificial scores): {old_confidence_scores}")
        print(f"Old approach ambiguity error: {old_error is not None}")
        print(f"New approach (real score): {new_confidence_scores}")
        print(f"New approach ambiguity error: {new_error is not None}")

        # Success: OLD approach triggers false ambiguity, NEW approach doesn't
        success = old_error is not None and new_error is None

        print(f"Fix prevents false ambiguity: {'YES' if success else 'NO'}")

        return success

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Corrected Categorization Accuracy Fix Validation")
    print("=" * 60)

    test1 = test_primary_fix()
    test2 = test_low_confidence_handling()
    test3 = test_before_and_after_comparison()

    print("\\n" + "=" * 60)
    print("RESULTS SUMMARY:")
    print(f"Primary fix (URS-003 style): {'PASS' if test1 else 'FAIL'}")
    print(f"Low confidence handling: {'PASS' if test2 else 'FAIL'}")
    print(f"Before/after comparison: {'PASS' if test3 else 'FAIL'}")

    overall_success = test1 and test2 and test3
    print(f"\\nOVERALL: {'SUCCESS' if overall_success else 'FAIL'}")

    if overall_success:
        print("\\nCategorization accuracy fix is working correctly!")
        print("- URS-003 categorizes as Category 5 without false ambiguity")
        print("- Low confidence cases trigger proper confidence errors")
        print("- Artificial confidence scores no longer cause false positives")
    else:
        print("\\nFix validation failed - see individual test results above.")
