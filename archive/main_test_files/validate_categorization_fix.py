#!/usr/bin/env python3
"""Validate the categorization fix for URS-003"""

import os
import sys
from pathlib import Path

# Set up environment
sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault("OPENAI_API_KEY", "dummy")

def test_complete_solution():
    """Test the complete categorization solution"""

    # URS-003 content
    urs003_content = """
## URS-003: Manufacturing Execution System (MES)
**Target Category**: 5 (Clear)
**System Type**: Custom Batch Record Management System

### 1. Introduction
This URS defines requirements for a custom MES to manage electronic batch records for sterile injectable products.

### 2. Functional Requirements
- **URS-MES-001**: System shall be custom-developed to integrate with proprietary equipment.
- **URS-MES-002**: Custom algorithms required for:
  - Dynamic in-process control limits based on multivariate analysis
  - Real-time batch genealogy tracking across multiple unit operations
  - Proprietary yield optimization calculations
- **URS-MES-003**: Develop custom interfaces for:
  - 12 different equipment types with proprietary protocols
  - Integration with custom warehouse management system
  - Real-time data exchange with proprietary PAT systems
- **URS-MES-004**: Custom workflow engine to handle:
  - Parallel processing paths unique to our manufacturing process
  - Complex exception handling for deviations
  - Site-specific business rules not supported by commercial packages
- **URS-MES-005**: Develop proprietary data structures for:
  - Multi-level bill of materials with conditional components
  - Process parameters with complex interdependencies
- **URS-MES-006**: Custom mobile application for shop floor data entry.
- **URS-MES-007**: Bespoke analytics module for real-time process monitoring.

### 3. Regulatory Requirements
- **URS-MES-008**: Custom audit trail implementation with enhanced metadata.
- **URS-MES-009**: Develop proprietary electronic signature workflow.
- **URS-MES-010**: Custom data integrity checks beyond standard validations.
"""

    print("🔧 TESTING CATEGORIZATION FIX FOR URS-003")
    print("=" * 60)

    try:
        from src.agents.categorization.agent import confidence_tool, gamp_analysis_tool

        # Step 1: Test GAMP Analysis
        print("\n1️⃣ GAMP ANALYSIS TEST")
        print("-" * 30)

        result = gamp_analysis_tool(urs003_content)
        predicted_category = result["predicted_category"]

        print(f"Predicted Category: {predicted_category}")
        print("Expected Category: 5")

        category_correct = predicted_category == 5
        if category_correct:
            print("✅ CATEGORY PREDICTION: CORRECT")
        else:
            print("❌ CATEGORY PREDICTION: WRONG")

        # Show evidence for Category 5
        cat5_evidence = result["all_categories_analysis"][5]
        print("\nCategory 5 Evidence:")
        print(f"  Strong Indicators: {cat5_evidence['strong_count']} found")
        print(f"  Found: {cat5_evidence['strong_indicators'][:5]}...")  # Show first 5
        print(f"  Weak Indicators: {cat5_evidence['weak_count']} found")

        # Step 2: Test Confidence Calculation
        print("\n2️⃣ CONFIDENCE CALCULATION TEST")
        print("-" * 30)

        confidence = confidence_tool(result)
        print(f"Confidence Score: {confidence:.3f} ({confidence:.1%})")

        confidence_good = confidence > 0.0
        confidence_threshold = confidence >= 0.6

        if confidence_good:
            print("✅ CONFIDENCE: Non-zero (good)")
        else:
            print("❌ CONFIDENCE: Zero (bad)")

        if confidence_threshold:
            print("✅ THRESHOLD: Above 60% threshold")
        else:
            print("⚠️ THRESHOLD: Below 60% threshold")

        # Step 3: Overall Assessment
        print("\n3️⃣ OVERALL ASSESSMENT")
        print("-" * 30)

        all_tests_passed = category_correct and confidence_good

        if all_tests_passed:
            print("🎉 SUCCESS: All core issues resolved!")
            print("  - URS-003 correctly categorized as Category 5")
            print("  - Confidence calculation returns non-zero value")
            if confidence_threshold:
                print("  - Confidence above threshold (no human consultation needed)")
            else:
                print("  - Confidence below threshold (human consultation triggered)")
        else:
            print("❌ FAILURE: Issues remain")
            if not category_correct:
                print("  - Category prediction still wrong")
            if not confidence_good:
                print("  - Confidence calculation still returns zero")

        # Step 4: Detailed Analysis
        print("\n4️⃣ DETAILED ANALYSIS")
        print("-" * 30)

        print("Decision Logic Flow:")

        # Check Category 1
        cat1 = result["all_categories_analysis"][1]
        print(f"1. Category 1 check: {cat1['strong_count']} strong, {cat1['exclusion_count']} exclusions")
        if cat1["strong_count"] > 0 and cat1["exclusion_count"] == 0:
            print("   → Would select Category 1 (infrastructure)")
        else:
            print("   → Category 1 rejected")

        # Check Category 5
        cat5 = result["all_categories_analysis"][5]
        print(f"2. Category 5 check: {cat5['strong_count']} strong indicators")
        if cat5["strong_count"] > 0:
            print("   → Would select Category 5 (custom applications)")
        else:
            print("   → Category 5 rejected")

        # Check Category 4
        cat4 = result["all_categories_analysis"][4]
        print(f"3. Category 4 check: {cat4['strong_count']} strong, {cat4['exclusion_count']} exclusions")
        if cat4["strong_count"] > 0 and cat4["exclusion_count"] == 0:
            print("   → Would select Category 4 (configured)")
        else:
            print("   → Category 4 rejected")

        print("4. Default: Category 3 (non-configured)")

        print(f"\nActual Decision: Category {predicted_category}")
        print(f"Decision Rationale: {result['decision_rationale']}")

        return {
            "category_correct": category_correct,
            "confidence_good": confidence_good,
            "confidence_threshold": confidence_threshold,
            "all_tests_passed": all_tests_passed,
            "predicted_category": predicted_category,
            "confidence_score": confidence,
            "strong_indicators_found": cat5_evidence["strong_count"]
        }

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    result = test_complete_solution()

    if result:
        print("\n" + "=" * 60)
        print("📊 SUMMARY RESULTS:")
        print(f"✅ Category Correct: {result['category_correct']}")
        print(f"✅ Confidence Non-Zero: {result['confidence_good']}")
        print(f"✅ Above Threshold: {result['confidence_threshold']}")
        print(f"🎯 Overall Success: {result['all_tests_passed']}")

        if result["all_tests_passed"]:
            print("\n🎉 FIX VALIDATED - Ready for integration testing!")
        else:
            print("\n⚠️ PARTIAL SUCCESS - May need additional fixes")
    else:
        print("\n❌ VALIDATION FAILED - Check errors above")
