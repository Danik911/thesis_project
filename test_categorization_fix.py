#!/usr/bin/env python3
"""
Test script to verify the categorization ambiguity fix works for URS-003.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'main', 'src'))

from agents.categorization.agent import categorize_urs_document
from agents.categorization.error_handler import CategorizationErrorHandler

def test_urs_003_categorization():
    """Test that URS-003 is correctly categorized as Category 5 without ambiguity error."""
    
    # URS-003 content - should be clear Category 5
    urs_003_content = """
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

    print("🧪 Testing URS-003 categorization fix...")
    print("Expected: Category 5 without ambiguity error")
    print()
    
    try:
        # Test categorization
        result = categorize_urs_document(
            urs_content=urs_003_content,
            document_name="URS-003-MES",
            use_structured_output=True,
            confidence_threshold=0.50,
            verbose=True
        )
        
        print(f"✅ CATEGORIZATION SUCCESSFUL")
        print(f"Category: {result.gamp_category.value}")
        print(f"Confidence: {result.confidence_score:.1%}")
        print(f"Review Required: {result.review_required}")
        print()
        print("Justification excerpt:")
        print(result.justification[:200] + "..." if len(result.justification) > 200 else result.justification)
        
        # Verify it's Category 5
        if result.gamp_category.value == 5:
            print("\n✅ CORRECT CATEGORY: 5 (Custom Applications)")
        else:
            print(f"\n❌ INCORRECT CATEGORY: {result.gamp_category.value} (Expected: 5)")
            return False
            
        # Verify no ambiguity error (should complete without exception)
        print("✅ NO AMBIGUITY ERROR: Categorization completed successfully")
        
        return True
        
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
    print("🚀 Starting categorization fix validation...")
    print("=" * 60)
    
    success = True
    
    # Test 1: URS-003 categorization
    if not test_urs_003_categorization():
        success = False
    
    # Test 2: Ambiguity detection logic
    if not test_ambiguity_detection_improvement():
        success = False
    
    print("\n" + "=" * 60)
    
    if success:
        print("🎉 ALL TESTS PASSED - Categorization fix is working!")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED - Review the fixes")
        sys.exit(1)