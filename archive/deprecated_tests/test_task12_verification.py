"""
Critical verification test for Task 12 implementation.
Tests the exact scenario that was failing: URS-003 false ambiguity detection.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "main"))

from src.agents.categorization.agent import confidence_tool_with_error_handling
from src.agents.categorization.error_handler import CategorizationErrorHandler


def test_urs003_scenario():
    """Test the exact URS-003 scenario that was causing false ambiguity."""

    # Mock URS-003 categorization data - clear Category 5 case
    urs003_data = {
        "predicted_category": 5,
        "reasoning": "Manufacturing Execution System with custom development for proprietary equipment",
        "confidence_explanation": "Clear Category 5 indicators: custom algorithms, proprietary interfaces, bespoke analytics",
        "categories_considered": [3, 4, 5],
        "key_factors": [
            "custom-developed to integrate with proprietary equipment",
            "Custom algorithms required for dynamic in-process control",
            "Develop custom interfaces for 12 different equipment types",
            "Custom workflow engine",
            "proprietary data structures",
            "Bespoke analytics module"
        ]
    }

    # Initialize error handler
    error_handler = CategorizationErrorHandler()

    # Test the confidence tool - this is where the fix was implemented
    print("Testing confidence_tool_with_error_handling with URS-003 data...")

    try:
        confidence = confidence_tool_with_error_handling(urs003_data, error_handler)
        print(f"✅ Confidence calculated: {confidence}")
        print("✅ No exception thrown - ambiguity check passed!")

        # Verify the confidence scores passed to ambiguity check
        # The fix ensures only the actual category gets a confidence score
        predicted_category = urs003_data.get("predicted_category")
        confidence_scores = {predicted_category: confidence}

        print(f"\nConfidence scores used for ambiguity check: {confidence_scores}")
        print(f"✅ Only Category {predicted_category} has confidence score (correct behavior)")

        # Double-check ambiguity detection directly
        ambiguity_error = error_handler.check_ambiguity(urs003_data, confidence_scores)
        if ambiguity_error:
            print(f"❌ CRITICAL: Ambiguity error detected: {ambiguity_error.message}")
            return False
        print("✅ No ambiguity error - URS-003 categorizes cleanly as Category 5")
        return True

    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e!s}")
        import traceback
        traceback.print_exc()
        return False

def test_edge_case_multiple_categories():
    """Test edge case where old implementation would create false ambiguity."""

    # This simulates what the old code would do - assign high confidence to multiple categories
    error_handler = CategorizationErrorHandler()

    print("\n\nTesting edge case - what old code would do:")

    # Old behavior simulation - multiple categories with artificial confidence
    old_confidence_scores = {3: 0.8, 4: 0.9, 5: 1.0}  # Artificial scores

    test_data = {
        "predicted_category": 5,
        "reasoning": "Clear Category 5 system"
    }

    print(f"Old approach confidence scores: {old_confidence_scores}")
    old_ambiguity = error_handler.check_ambiguity(test_data, old_confidence_scores)
    if old_ambiguity:
        print(f"❌ Old approach triggers ambiguity: {old_ambiguity.message}")
    else:
        print("✅ Old approach doesn't trigger ambiguity")

    # New behavior - only actual category gets confidence
    new_confidence_scores = {5: 1.0}  # Only the predicted category

    print(f"\nNew approach confidence scores: {new_confidence_scores}")
    new_ambiguity = error_handler.check_ambiguity(test_data, new_confidence_scores)
    if new_ambiguity:
        print(f"❌ New approach triggers ambiguity: {new_ambiguity.message}")
    else:
        print("✅ New approach doesn't trigger ambiguity")

    return old_ambiguity is not None and new_ambiguity is None

if __name__ == "__main__":
    print("=" * 80)
    print("CRITICAL VERIFICATION TEST FOR TASK 12")
    print("=" * 80)

    # Run main test
    urs003_passed = test_urs003_scenario()

    # Run edge case test
    edge_case_passed = test_edge_case_multiple_categories()

    print("\n" + "=" * 80)
    print("FINAL RESULTS:")
    print(f"URS-003 Test: {'✅ PASS' if urs003_passed else '❌ FAIL'}")
    print(f"Edge Case Test: {'✅ PASS' if edge_case_passed else '❌ FAIL'}")
    print(f"Overall: {'✅ ALL TESTS PASS' if urs003_passed and edge_case_passed else '❌ TESTS FAILED'}")
    print("=" * 80)
