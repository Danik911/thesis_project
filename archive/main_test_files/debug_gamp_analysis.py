#!/usr/bin/env python3
"""Debug script to test GAMP analysis tool directly"""

import os
import sys
from pathlib import Path

# Add the main directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Set up environment
os.environ.setdefault("OPENAI_API_KEY", "dummy_key_for_testing")

from src.agents.categorization.agent import confidence_tool, gamp_analysis_tool


def debug_urs003():
    """Debug URS-003 categorization"""

    # URS-003 content with strong Category 5 indicators
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

    print("Testing GAMP Analysis Tool with URS-003")
    print("Expected Category: 5")
    print("=" * 60)

    try:
        # Step 1: Run GAMP analysis
        print("\n1. Running GAMP Analysis Tool...")
        analysis_result = gamp_analysis_tool(urs003_content)

        print(f"   Predicted Category: {analysis_result['predicted_category']}")
        print(f"   Decision Rationale: {analysis_result['decision_rationale']}")
        print(f"   Summary: {analysis_result['summary']}")

        # Show evidence details
        evidence = analysis_result["evidence"]
        print(f"\n   Evidence for predicted category {analysis_result['predicted_category']}:")
        print(f"   - Strong indicators: {evidence['strong_count']} -> {evidence['strong_indicators']}")
        print(f"   - Weak indicators: {evidence['weak_count']} -> {evidence['weak_indicators']}")
        print(f"   - Exclusions: {evidence['exclusion_count']} -> {evidence['exclusion_factors']}")

        # Show all categories analysis
        print("\n   All Categories Analysis:")
        for cat_id, cat_data in analysis_result["all_categories_analysis"].items():
            print(f"   Category {cat_id}: Strong={cat_data['strong_count']}, Weak={cat_data['weak_count']}, Exclusions={cat_data['exclusion_count']}")
            if cat_data["strong_count"] > 0:
                print(f"     Strong indicators: {cat_data['strong_indicators']}")

        # Step 2: Calculate confidence
        print("\n2. Calculating Confidence...")
        confidence_score = confidence_tool(analysis_result)
        print(f"   Confidence Score: {confidence_score:.3f} ({confidence_score:.1%})")

        # Analysis
        print("\n3. Analysis:")
        if analysis_result["predicted_category"] == 5:
            print("   ✅ CORRECT: Predicted Category 5 as expected")
        else:
            print(f"   ❌ WRONG: Predicted Category {analysis_result['predicted_category']} instead of 5")

        if confidence_score > 0.0:
            print(f"   ✅ CONFIDENCE: Non-zero confidence score: {confidence_score:.3f}")
        else:
            print("   ❌ CONFIDENCE: Zero confidence score indicates calculation issue")

        # Let's examine the specific Category 5 matches
        cat5_analysis = analysis_result["all_categories_analysis"][5]
        print("\n4. Category 5 Specific Analysis:")
        print(f"   Strong Count: {cat5_analysis['strong_count']}")
        print(f"   Strong Indicators Found: {cat5_analysis['strong_indicators']}")
        print(f"   Weak Count: {cat5_analysis['weak_count']}")
        print(f"   Weak Indicators Found: {cat5_analysis['weak_indicators']}")


    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    debug_urs003()
