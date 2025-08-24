#!/usr/bin/env python3
"""
Test the confidence fix for the categorization agent
"""

import os
import sys

# Add main to path
main_path = os.path.join(os.path.dirname(__file__), "main")
sys.path.insert(0, main_path)

try:
    from src.agents.categorization.agent import confidence_tool, gamp_analysis_tool
    print("✓ Successfully imported categorization tools")
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)

# Read the actual test document
try:
    with open("main/simple_category3.md") as f:
        content = f.read()
    print("✓ Successfully loaded test document")
except FileNotFoundError:
    print("✗ Test document not found")
    sys.exit(1)

print("=== TESTING FIXED CATEGORIZATION ===")

try:
    print("Running analysis...")
    analysis_result = gamp_analysis_tool(content)

    print("✓ Analysis completed")
    print(f"Predicted category: {analysis_result['predicted_category']}")

    # Check Category 3 indicators specifically
    cat3_analysis = analysis_result["all_categories_analysis"][3]
    print("\nCategory 3 Analysis:")
    print(f"  Strong indicators ({cat3_analysis['strong_count']}): {cat3_analysis['strong_indicators']}")
    print(f"  Exclusions ({cat3_analysis['exclusion_count']}): {cat3_analysis['exclusion_factors']}")

    # Check all category scores
    if "category_scores" in analysis_result["evidence"]:
        scores = analysis_result["evidence"]["category_scores"]
        print("\nAll category scores:")
        for cat, score in scores.items():
            print(f"  Category {cat}: {score}")

    print(f"\nDecision rationale: {analysis_result['decision_rationale']}")

    # Test confidence calculation
    print("\n=== TESTING CONFIDENCE ===")
    confidence = confidence_tool(analysis_result)
    print(f"✓ Confidence calculated: {confidence}")
    print(f"Confidence percentage: {confidence * 100:.1f}%")

    # Evaluate result
    expected_category = 3
    expected_min_confidence = 0.75  # 75%

    print("\n=== EVALUATION ===")
    category_correct = analysis_result["predicted_category"] == expected_category
    confidence_good = confidence >= expected_min_confidence

    print(f"Category prediction: {'✓ PASS' if category_correct else '✗ FAIL'} (Expected: {expected_category}, Got: {analysis_result['predicted_category']})")
    print(f"Confidence level: {'✓ PASS' if confidence_good else '✗ FAIL'} (Expected: ≥{expected_min_confidence*100:.0f}%, Got: {confidence*100:.1f}%)")

    if category_correct and confidence_good:
        print("\n🎉 FIX SUCCESSFUL! Categorization working correctly.")
    else:
        print("\n❌ Issues still present - further debugging needed.")

        # Debug exclusions if confidence still low
        if not confidence_good:
            print("\nDEBUG INFO:")
            print(f"Strong count: {cat3_analysis['strong_count']}")
            print(f"Exclusion count: {cat3_analysis['exclusion_count']}")
            print(f"Strong indicators found: {cat3_analysis['strong_indicators']}")
            print(f"Exclusions still triggering: {cat3_analysis['exclusion_factors']}")

except Exception as e:
    print(f"✗ Error during testing: {e}")
    import traceback
    traceback.print_exc()
