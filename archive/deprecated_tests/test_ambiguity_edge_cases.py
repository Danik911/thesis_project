#!/usr/bin/env python3
"""
Test edge cases to understand ambiguity detection behavior.
"""

import sys
from pathlib import Path

# Add the main directory to path
sys.path.insert(0, str(Path(__file__).parent / "main"))

def test_dominance_gap_analysis():
    """Test the dominance gap analysis in detail."""
    try:
        from src.agents.categorization.error_handler import CategorizationErrorHandler

        print("Testing dominance gap analysis...")

        error_handler = CategorizationErrorHandler(confidence_threshold=0.50)

        test_cases = [
            {
                "name": "Clear dominance (gap > 0.20)",
                "scores": {1: 0.50, 3: 0.55, 4: 0.65, 5: 0.85},  # Gap = 0.20
                "should_trigger": False
            },
            {
                "name": "Very close scores (gap < 0.10)",
                "scores": {4: 0.75, 5: 0.80},  # Gap = 0.05
                "should_trigger": True
            },
            {
                "name": "Moderate gap, high scores",
                "scores": {4: 0.70, 5: 0.85},  # Gap = 0.15, top > 0.75
                "should_trigger": True
            },
            {
                "name": "Single high confidence",
                "scores": {5: 0.85},
                "should_trigger": False
            }
        ]

        for i, case in enumerate(test_cases, 1):
            print(f"\\n{i}. {case['name']}:")
            print(f"   Scores: {case['scores']}")

            # Calculate dominance gap manually
            sorted_scores = sorted(case["scores"].values(), reverse=True)
            dominance_gap = sorted_scores[0] - sorted_scores[1] if len(sorted_scores) >= 2 else 1.0

            print(f"   Dominance gap: {dominance_gap:.3f}")

            mock_data = {"predicted_category": max(case["scores"], key=case["scores"].get)}
            error = error_handler.check_ambiguity(mock_data, case["scores"])

            triggered = error is not None
            print(f"   Ambiguity triggered: {triggered}")
            print(f"   Expected: {case['should_trigger']}")
            print(f"   Result: {'PASS' if triggered == case['should_trigger'] else 'FAIL'}")

        return True

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_actual_urs003_scenario():
    """Test the actual URS-003 scenario that was problematic."""
    try:
        from src.agents.categorization.agent import confidence_tool_with_error_handling
        from src.agents.categorization.error_handler import CategorizationErrorHandler

        print("\\nTesting actual URS-003 problematic scenario...")

        error_handler = CategorizationErrorHandler(confidence_threshold=0.50)

        # This simulates what URS-003 might have looked like before the fix
        category_data = {
            "predicted_category": 5,
            "evidence": {"strong_count": 4, "weak_count": 1, "exclusion_count": 0},
            "all_categories_analysis": {
                "1": {"strong_count": 0, "weak_count": 1, "exclusion_count": 3},
                "3": {"strong_count": 0, "weak_count": 2, "exclusion_count": 2},
                "4": {"strong_count": 2, "weak_count": 1, "exclusion_count": 1},
                "5": {"strong_count": 4, "weak_count": 1, "exclusion_count": 0}
            }
        }

        # Get the real confidence
        real_confidence = confidence_tool_with_error_handling(category_data, error_handler)
        print(f"Real confidence for Category 5: {real_confidence:.3f}")

        # Simulate OLD artificial confidence calculation for each category
        artificial_scores = {}
        for cat_id, analysis in category_data["all_categories_analysis"].items():
            cat_confidence = (
                0.4 * analysis.get("strong_count", 0) +
                0.2 * analysis.get("weak_count", 0) -
                0.3 * analysis.get("exclusion_count", 0)
            )
            artificial_scores[int(cat_id)] = max(0.0, min(1.0, 0.5 + cat_confidence))

        print(f"OLD artificial scores: {artificial_scores}")

        # NEW approach: only real confidence for predicted category
        new_scores = {5: real_confidence}
        print(f"NEW real scores: {new_scores}")

        # Test ambiguity with both approaches
        old_error = error_handler.check_ambiguity(category_data, artificial_scores)
        new_error = error_handler.check_ambiguity(category_data, new_scores)

        print(f"OLD approach ambiguity: {old_error is not None}")
        if old_error:
            print(f"   Error details: {old_error.message}")

        print(f"NEW approach ambiguity: {new_error is not None}")
        if new_error:
            print(f"   Error details: {new_error.message}")

        # The fix should prevent false ambiguity
        fix_working = (old_error is not None) and (new_error is None)
        print(f"Fix prevents false ambiguity: {'YES' if fix_working else 'NO'}")

        return True

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Ambiguity Detection Edge Case Analysis")
    print("=" * 50)

    test_dominance_gap_analysis()
    test_actual_urs003_scenario()

    print("\\n" + "=" * 50)
    print("Analysis complete. Check results above to understand fix behavior.")
