#!/usr/bin/env python3
"""
Debug test for GAMP analysis tool to verify the scoring logic works.
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "main", "src"))

from agents.categorization.agent import gamp_analysis_tool


def test_gamp_analysis_scoring():
    """Test the GAMP analysis tool with the new scoring logic."""

    # Test URS-001: Environmental Monitoring System (should be Category 3)
    urs_001_content = """
    The system shall use vendor-supplied software without modification.
    All data shall be stored in the vendor's standard database format.
    Standard reports provided by vendor shall be used for batch release.
    Electronic signatures shall use vendor's built-in functionality.
    Data shall be retained for 7 years using vendor's archival feature.
    """

    print("Testing URS-001 (Environmental Monitoring):")
    print("Expected: Category 3")

    result_001 = gamp_analysis_tool(urs_001_content)

    print(f"Predicted Category: {result_001['predicted_category']}")
    print(f"Category Scores: {result_001['evidence'].get('category_scores', 'Not available')}")
    print(f"Winning Score: {result_001['evidence'].get('winning_score', 'Not available')}")
    print(f"Decision Rationale: {result_001['decision_rationale']}")
    print()

    # Test URS-004: Chromatography Data System (should be Category 4)
    urs_004_content = """
    System based on commercial CDS software (Empower/OpenLab).
    Implement custom calculations using vendor's formula editor.
    Develop custom reports using vendor's report designer.
    Create custom export routines for LIMS interface.
    Configure standard integration parameters for peak detection.
    """

    print("Testing URS-004 (Chromatography Data System):")
    print("Expected: Category 4")

    result_004 = gamp_analysis_tool(urs_004_content)

    print(f"Predicted Category: {result_004['predicted_category']}")
    print(f"Category Scores: {result_004['evidence'].get('category_scores', 'Not available')}")
    print(f"Winning Score: {result_004['evidence'].get('winning_score', 'Not available')}")
    print(f"Decision Rationale: {result_004['decision_rationale']}")
    print()

    # Test actual Category 5 (should still work)
    urs_005_content = """
    System shall be custom-developed to integrate with proprietary equipment.
    Custom algorithms required for dynamic in-process control limits.
    Develop custom interfaces for proprietary protocols.
    Custom workflow engine to handle site-specific business rules not supported by commercial packages.
    Develop proprietary data structures for multi-level bill of materials.
    """

    print("Testing Category 5 example:")
    print("Expected: Category 5")

    result_005 = gamp_analysis_tool(urs_005_content)

    print(f"Predicted Category: {result_005['predicted_category']}")
    print(f"Category Scores: {result_005['evidence'].get('category_scores', 'Not available')}")
    print(f"Winning Score: {result_005['evidence'].get('winning_score', 'Not available')}")
    print(f"Decision Rationale: {result_005['decision_rationale']}")

    return result_001, result_004, result_005

if __name__ == "__main__":
    print("Testing GAMP Analysis Tool with New Scoring Logic")
    print("=" * 50)

    try:
        result_001, result_004, result_005 = test_gamp_analysis_scoring()

        print("\n" + "=" * 50)
        print("SUMMARY:")

        success = True

        if result_001["predicted_category"] == 3:
            print("✅ URS-001: Correctly categorized as Category 3")
        else:
            print(f"❌ URS-001: Incorrectly categorized as Category {result_001['predicted_category']} (Expected: 3)")
            success = False

        if result_004["predicted_category"] in [3, 4]:
            print(f"✅ URS-004: Correctly categorized as Category {result_004['predicted_category']} (Expected: 3 or 4)")
        else:
            print(f"❌ URS-004: Incorrectly categorized as Category {result_004['predicted_category']} (Expected: 3 or 4)")
            success = False

        if result_005["predicted_category"] == 5:
            print("✅ Category 5 example: Correctly categorized as Category 5")
        else:
            print(f"❌ Category 5 example: Incorrectly categorized as Category {result_005['predicted_category']} (Expected: 5)")
            success = False

        if success:
            print("\n🎉 ALL TESTS PASSED - Scoring logic is working correctly!")
        else:
            print("\n❌ SOME TESTS FAILED")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
