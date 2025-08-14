#!/usr/bin/env python3
"""
Test script to verify the categorization accuracy fixes work for failed cases.
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "main", "src"))

from agents.categorization.agent import categorize_urs_document
from agents.categorization.error_handler import CategorizationErrorHandler


def test_urs_001_categorization():
    """Test that URS-001 is correctly categorized as Category 3."""

    # URS-001 content - should be clear Category 3 (unmodified vendor software)
    urs_001_content = """
## URS-001: Environmental Monitoring System (EMS)
**Target Category**: 3 (Clear)
**System Type**: Continuous Temperature and Humidity Monitoring

### 1. Introduction
This URS defines the requirements for an Environmental Monitoring System to monitor critical storage areas for temperature-sensitive pharmaceutical products.

### 2. Functional Requirements
- **URS-EMS-001**: The system shall continuously monitor temperature in all GMP storage areas.
- **URS-EMS-002**: Temperature readings shall be recorded at intervals not exceeding 5 minutes.
- **URS-EMS-003**: The system shall use vendor-supplied software without modification.
- **URS-EMS-004**: Temperature range: -80°C to +50°C with accuracy of ±0.5°C.
- **URS-EMS-005**: The system shall generate alerts when temperature deviates ±2°C from setpoint.
- **URS-EMS-006**: All data shall be stored in the vendor's standard database format.
- **URS-EMS-007**: Standard reports provided by vendor shall be used for batch release.

### 3. Regulatory Requirements
- **URS-EMS-008**: System shall maintain an audit trail per 21 CFR Part 11.
- **URS-EMS-009**: Electronic signatures shall use vendor's built-in functionality.
- **URS-EMS-010**: Data shall be retained for 7 years using vendor's archival feature.
"""

    print("🧪 Testing URS-001 categorization fix...")
    print("Expected: Category 3 (was incorrectly Category 5)")
    print()

    try:
        # Test categorization
        result = categorize_urs_document(
            urs_content=urs_001_content,
            document_name="URS-001-EMS",
            use_structured_output=True,
            confidence_threshold=0.50,
            verbose=True
        )

        print("✅ CATEGORIZATION SUCCESSFUL")
        print(f"Category: {result.gamp_category.value}")
        print(f"Confidence: {result.confidence_score:.1%}")
        print(f"Review Required: {result.review_required}")
        print()

        # Verify it's Category 3
        if result.gamp_category.value == 3:
            print("\n✅ CORRECT CATEGORY: 3 (Non-Configured Products)")
            return True
        print(f"\n❌ INCORRECT CATEGORY: {result.gamp_category.value} (Expected: 3)")
        return False

    except Exception as e:
        print(f"❌ CATEGORIZATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_urs_004_categorization():
    """Test that URS-004 is correctly categorized as Category 4."""

    # URS-004 content - should be Category 4 (vendor-supported customization)
    urs_004_content = """
## URS-004: Chromatography Data System (CDS)
**Target Category**: Ambiguous 3/4
**System Type**: Analytical Instrument Control and Data Analysis

### 1. Introduction
This URS defines requirements for a CDS to control HPLC/GC instruments and process chromatographic data.

### 2. Functional Requirements
- **URS-CDS-001**: System based on commercial CDS software (Empower/OpenLab).
- **URS-CDS-002**: Use vendor's standard instrument control for Waters/Agilent equipment.
- **URS-CDS-003**: Minor configuration of acquisition methods within vendor parameters.
- **URS-CDS-004**: Implement custom calculations using vendor's formula editor:
  - Non-standard impurity calculations
  - Proprietary relative response factor adjustments
  - Complex bracketing schemes beyond vendor defaults
- **URS-CDS-005**: Develop custom reports using vendor's report designer.
- **URS-CDS-006**: Configure standard integration parameters for peak detection.
- **URS-CDS-007**: Create custom export routines for LIMS interface.
- **URS-CDS-008**: Implement site-specific naming conventions via configuration.

### 3. Ambiguous Requirements
- **URS-CDS-009**: System shall support "enhanced" system suitability calculations (Note: unclear if vendor's standard SST is sufficient or custom development needed).
- **URS-CDS-010**: Implement "advanced" trending capabilities for method performance.
- **URS-CDS-011**: System shall handle "complex" multi-dimensional chromatography.
"""

    print("🧪 Testing URS-004 categorization fix...")
    print("Expected: Category 3 or 4 (was incorrectly Category 5)")
    print()

    try:
        # Test categorization
        result = categorize_urs_document(
            urs_content=urs_004_content,
            document_name="URS-004-CDS",
            use_structured_output=True,
            confidence_threshold=0.50,
            verbose=True
        )

        print("✅ CATEGORIZATION SUCCESSFUL")
        print(f"Category: {result.gamp_category.value}")
        print(f"Confidence: {result.confidence_score:.1%}")
        print(f"Review Required: {result.review_required}")
        print()

        # Verify it's Category 3 or 4
        if result.gamp_category.value in [3, 4]:
            print(f"\n✅ CORRECT CATEGORY: {result.gamp_category.value} (Expected: 3 or 4)")
            return True
        print(f"\n❌ INCORRECT CATEGORY: {result.gamp_category.value} (Expected: 3 or 4)")
        return False

    except Exception as e:
        print(f"❌ CATEGORIZATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ambiguity_detection_improvement():
    """Test the improved ambiguity detection logic directly."""
    print("\n🧪 Testing improved ambiguity detection logic...")

    error_handler = CategorizationErrorHandler(confidence_threshold=0.50)

    # Test case 1: Clear dominant category (should NOT trigger ambiguity)
    confidence_scores_clear = {
        1: 0.30,
        3: 0.25,
        4: 0.45,
        5: 0.85  # Clear winner with gap > 0.20
    }

    ambiguity_error = error_handler.check_ambiguity({}, confidence_scores_clear)
    if ambiguity_error is None:
        print("✅ CLEAR CASE: No ambiguity detected for dominant Category 5 (0.85 vs 0.45)")
    else:
        print(f"❌ FALSE POSITIVE: Ambiguity detected when shouldn't be: {ambiguity_error.message}")
        return False

    # Test case 2: Truly ambiguous case (should trigger ambiguity)
    confidence_scores_ambiguous = {
        1: 0.30,
        3: 0.25,
        4: 0.78,
        5: 0.80  # Very close, should trigger ambiguity
    }

    ambiguity_error = error_handler.check_ambiguity({}, confidence_scores_ambiguous)
    if ambiguity_error is not None:
        print("✅ AMBIGUOUS CASE: Correctly detected ambiguity for close scores (0.80 vs 0.78)")
    else:
        print("❌ FALSE NEGATIVE: Failed to detect true ambiguity")
        return False

    return True

if __name__ == "__main__":
    print("🚀 Starting categorization accuracy fix validation...")
    print("=" * 60)

    success = True

    # Test 1: URS-001 categorization (previously failed)
    if not test_urs_001_categorization():
        success = False

    print("\n" + "-" * 40)

    # Test 2: URS-004 categorization (previously failed)
    if not test_urs_004_categorization():
        success = False

    print("\n" + "-" * 40)

    # Test 3: Ambiguity detection logic
    if not test_ambiguity_detection_improvement():
        success = False

    print("\n" + "=" * 60)

    if success:
        print("🎉 ALL TESTS PASSED - Categorization accuracy fixes are working!")
        print("✅ URS-001 now correctly categorized as Category 3")
        print("✅ URS-004 now correctly categorized as Category 3/4")
        print("✅ Over-classification to Category 5 issue resolved")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED - Review the fixes")
        sys.exit(1)
