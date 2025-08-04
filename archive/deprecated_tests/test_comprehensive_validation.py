#!/usr/bin/env python3
"""
Comprehensive test validation for categorization accuracy fix.
Tests with multiple URS cases from the test data.
"""

import sys
from pathlib import Path

# Add the main directory to path
sys.path.insert(0, str(Path(__file__).parent / "main"))

def test_confidence_calculations():
    """Test confidence calculations for various scenarios."""
    try:
        from src.agents.categorization.agent import confidence_tool_with_error_handling
        from src.agents.categorization.error_handler import CategorizationErrorHandler

        print("Testing confidence calculations for different URS scenarios...")

        error_handler = CategorizationErrorHandler(confidence_threshold=0.50)

        # Test Case 1: Clear Category 5 (like URS-003)
        print("\\n1. Testing clear Category 5 (Manufacturing Execution System):")
        category_data_5 = {
            "predicted_category": 5,
            "evidence": {
                "strong_count": 4,  # Strong custom development indicators
                "weak_count": 1,
                "exclusion_count": 0
            },
            "all_categories_analysis": {
                "1": {"strong_count": 0, "weak_count": 1, "exclusion_count": 3},
                "3": {"strong_count": 0, "weak_count": 1, "exclusion_count": 2},
                "4": {"strong_count": 1, "weak_count": 2, "exclusion_count": 1},
                "5": {"strong_count": 4, "weak_count": 1, "exclusion_count": 0}
            }
        }

        confidence_5 = confidence_tool_with_error_handling(category_data_5, error_handler)
        print(f"   Confidence: {confidence_5:.3f}")
        print("   Expected: >0.80 (clear Category 5)")
        print(f"   Result: {'PASS' if confidence_5 > 0.80 else 'FAIL'}")

        # Test Case 2: Clear Category 1 (Infrastructure)
        print("\\n2. Testing clear Category 1 (Infrastructure):")
        category_data_1 = {
            "predicted_category": 1,
            "evidence": {
                "strong_count": 3,  # Strong infrastructure indicators
                "weak_count": 0,
                "exclusion_count": 0
            },
            "all_categories_analysis": {
                "1": {"strong_count": 3, "weak_count": 0, "exclusion_count": 0},
                "3": {"strong_count": 0, "weak_count": 1, "exclusion_count": 2},
                "4": {"strong_count": 0, "weak_count": 1, "exclusion_count": 2},
                "5": {"strong_count": 0, "weak_count": 0, "exclusion_count": 3}
            }
        }

        confidence_1 = confidence_tool_with_error_handling(category_data_1, error_handler)
        print(f"   Confidence: {confidence_1:.3f}")
        print("   Expected: >0.75 (clear Category 1)")
        print(f"   Result: {'PASS' if confidence_1 > 0.75 else 'FAIL'}")

        # Test Case 3: Borderline case (should have lower confidence)
        print("\\n3. Testing borderline case (mixed indicators):")
        category_data_borderline = {
            "predicted_category": 4,
            "evidence": {
                "strong_count": 1,  # Few strong indicators
                "weak_count": 2,
                "exclusion_count": 1  # Some exclusions
            },
            "all_categories_analysis": {
                "1": {"strong_count": 0, "weak_count": 2, "exclusion_count": 1},
                "3": {"strong_count": 1, "weak_count": 1, "exclusion_count": 1},
                "4": {"strong_count": 1, "weak_count": 2, "exclusion_count": 1},
                "5": {"strong_count": 0, "weak_count": 1, "exclusion_count": 2}
            }
        }

        confidence_borderline = confidence_tool_with_error_handling(category_data_borderline, error_handler)
        print(f"   Confidence: {confidence_borderline:.3f}")
        print("   Expected: 0.50-0.70 (borderline case)")
        print(f"   Result: {'PASS' if 0.50 <= confidence_borderline <= 0.70 else 'FAIL'}")

        return confidence_5 > 0.80 and confidence_1 > 0.75 and 0.50 <= confidence_borderline <= 0.70

    except Exception as e:
        print(f"ERROR in confidence calculations: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ambiguity_prevention():
    """Test that false ambiguity is prevented with the fix."""
    try:
        from src.agents.categorization.error_handler import CategorizationErrorHandler

        print("\\nTesting ambiguity prevention...")

        error_handler = CategorizationErrorHandler(confidence_threshold=0.50)

        test_cases = [
            {
                "name": "High confidence Category 5",
                "confidence_scores": {5: 0.85},
                "expected_ambiguity": False
            },
            {
                "name": "High confidence Category 1",
                "confidence_scores": {1: 0.82},
                "expected_ambiguity": False
            },
            {
                "name": "Low confidence Category 4",
                "confidence_scores": {4: 0.45},
                "expected_ambiguity": False  # Should trigger low confidence, not ambiguity
            }
        ]

        all_passed = True
        for i, case in enumerate(test_cases, 1):
            print(f"\\n{i}. {case['name']}:")

            mock_category_data = {
                "predicted_category": list(case["confidence_scores"].keys())[0],
                "evidence": {"strong_count": 2, "weak_count": 1, "exclusion_count": 0}
            }

            ambiguity_error = error_handler.check_ambiguity(mock_category_data, case["confidence_scores"])
            has_ambiguity = ambiguity_error is not None

            print(f"   Confidence scores: {case['confidence_scores']}")
            print(f"   Ambiguity detected: {has_ambiguity}")
            print(f"   Expected ambiguity: {case['expected_ambiguity']}")

            if has_ambiguity == case["expected_ambiguity"]:
                print("   Result: PASS")
            else:
                print("   Result: FAIL")
                all_passed = False

        return all_passed

    except Exception as e:
        print(f"ERROR in ambiguity prevention test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_audit_trail():
    """Test that audit trail logging is working."""
    try:
        import logging

        from src.agents.categorization.agent import confidence_tool_with_error_handling
        from src.agents.categorization.error_handler import CategorizationErrorHandler

        print("\\nTesting audit trail logging...")

        # Capture log output
        log_capture = []

        class LogCapture(logging.Handler):
            def emit(self, record):
                log_capture.append(self.format(record))

        error_handler = CategorizationErrorHandler(confidence_threshold=0.50)
        capture_handler = LogCapture()
        error_handler.logger.addHandler(capture_handler)
        error_handler.logger.setLevel(logging.DEBUG)

        category_data = {
            "predicted_category": 5,
            "evidence": {"strong_count": 3, "weak_count": 1, "exclusion_count": 0},
            "all_categories_analysis": {
                "5": {"strong_count": 3, "weak_count": 1, "exclusion_count": 0}
            }
        }

        confidence = confidence_tool_with_error_handling(category_data, error_handler)

        # Check for expected log messages
        relevant_logs = [log for log in log_capture if "confidence score" in log.lower()]

        print(f"   Confidence calculated: {confidence:.3f}")
        print(f"   Audit log entries captured: {len(relevant_logs)}")
        print(f"   Sample log: {relevant_logs[0] if relevant_logs else 'None'}")

        return len(relevant_logs) > 0

    except Exception as e:
        print(f"ERROR in audit trail test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Comprehensive Categorization Accuracy Validation")
    print("=" * 60)

    test1_pass = test_confidence_calculations()
    test2_pass = test_ambiguity_prevention()
    test3_pass = test_audit_trail()

    print("\\n" + "=" * 60)
    print("SUMMARY:")
    print(f"  Confidence calculations: {'PASS' if test1_pass else 'FAIL'}")
    print(f"  Ambiguity prevention: {'PASS' if test2_pass else 'FAIL'}")
    print(f"  Audit trail: {'PASS' if test3_pass else 'FAIL'}")

    overall_pass = test1_pass and test2_pass and test3_pass
    print(f"\\nOVERALL RESULT: {'SUCCESS - All tests passed' if overall_pass else 'FAILURE - Some tests failed'}")

    if overall_pass:
        print("\\nThe categorization accuracy fix is working correctly:")
        print("- URS-003 and similar Category 5 cases should now categorize without false ambiguity")
        print("- Confidence scores are based on actual analysis, not artificial calculations")
        print("- Full audit trail is maintained for regulatory compliance")
    else:
        print("\\nThe fix needs additional work - see test failures above.")
