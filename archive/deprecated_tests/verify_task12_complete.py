"""
Final verification that Task 12 is complete - test categorization accuracy fix.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "main"))

from src.agents.categorization.agent import gamp_analysis_tool, confidence_tool_with_error_handling
from src.agents.categorization.error_handler import CategorizationErrorHandler

def test_urs003_categorization():
    """Test that URS-003 is correctly categorized as Category 5 with high confidence."""
    
    # URS-003 content
    urs003_content = """
## URS-003: Manufacturing Execution System (MES)

**System Overview**: Manufacturing execution system for biopharmaceutical production facility. The system will be custom-developed to integrate with proprietary equipment and existing enterprise systems. Custom algorithms required for dynamic in-process control adjustments based on real-time quality data.

**Key Requirements**:
- Develop custom interfaces for 12 different equipment types with proprietary protocols
- Custom workflow engine to handle site-specific business rules and exception handling
- Implement proprietary data structures for batch genealogy tracking
- Create custom mobile application for shop floor operators with enhanced metadata capture
- Design custom audit trail with proprietary electronic signature workflows
- Build interfaces to 8 different systems using custom middleware
- Develop bespoke analytics module for predictive maintenance
- Implement custom algorithms for dynamic scheduling optimization
- Create specialized reporting tools for regulatory submissions
- Design proprietary protocols for equipment integration
- Implement custom data validation rules beyond standard checks
- Develop specialized tools for deviation management
- Create custom dashboards for real-time monitoring
- Implement proprietary communication protocols
- Design custom security framework for multi-site operations
"""
    
    print("Testing URS-003 categorization...")
    print("=" * 80)
    
    # Run GAMP analysis
    analysis_result = gamp_analysis_tool(urs003_content)
    
    print(f"Predicted Category: {analysis_result['predicted_category']}")
    print(f"Evidence: {analysis_result['evidence']}")
    print(f"Decision Rationale: {analysis_result['decision_rationale']}")
    
    # Initialize error handler
    error_handler = CategorizationErrorHandler()
    
    # Calculate confidence
    confidence = confidence_tool_with_error_handling(analysis_result, error_handler)
    
    print(f"\nConfidence Score: {confidence:.2f}")
    
    # Check results
    success = True
    
    if analysis_result['predicted_category'] != 5:
        print(f"FAILED: Expected Category 5, got {analysis_result['predicted_category']}")
        success = False
    else:
        print("PASSED: Correctly categorized as Category 5")
        
    if confidence < 0.6:
        print(f"FAILED: Confidence {confidence:.2f} below threshold 0.6")
        success = False
    else:
        print(f"PASSED: Confidence {confidence:.2f} above threshold")
        
    # Check that no ambiguity was detected
    confidence_scores = {analysis_result['predicted_category']: confidence}
    ambiguity_error = error_handler.check_ambiguity(analysis_result, confidence_scores)
    
    if ambiguity_error:
        print(f"FAILED: False ambiguity detected: {ambiguity_error.message}")
        success = False
    else:
        print("PASSED: No false ambiguity detected")
        
    return success

def test_ambiguity_logic():
    """Test that the ambiguity detection logic works correctly."""
    
    print("\n\nTesting ambiguity detection logic...")
    print("=" * 80)
    
    error_handler = CategorizationErrorHandler()
    
    # Test 1: Clear winner (no ambiguity)
    print("\nTest 1: Clear winner with dominance gap > 0.20")
    scores1 = {3: 0.45, 5: 0.85}
    ambiguity1 = error_handler.check_ambiguity({}, scores1)
    if ambiguity1:
        print(f"FAILED: Ambiguity incorrectly detected: {ambiguity1.message}")
        return False
    else:
        print("PASSED: No ambiguity for clear winner")
        
    # Test 2: Close scores (ambiguity)
    print("\nTest 2: Close scores with gap < 0.10")
    scores2 = {4: 0.75, 5: 0.80}
    ambiguity2 = error_handler.check_ambiguity({}, scores2)
    if ambiguity2:
        print(f"PASSED: Ambiguity correctly detected: {ambiguity2.message}")
    else:
        print("FAILED: Ambiguity not detected for close scores")
        return False
        
    # Test 3: Single high score (no ambiguity)
    print("\nTest 3: Single high confidence category")
    scores3 = {5: 0.90}
    ambiguity3 = error_handler.check_ambiguity({}, scores3)
    if ambiguity3:
        print(f"FAILED: Ambiguity incorrectly detected: {ambiguity3.message}")
        return False
    else:
        print("PASSED: No ambiguity for single high score")
        
    return True

if __name__ == "__main__":
    print("TASK 12 VERIFICATION - CATEGORIZATION ACCURACY FIX")
    print("=" * 80)
    
    # Test URS-003 categorization
    urs003_passed = test_urs003_categorization()
    
    # Test ambiguity logic
    ambiguity_passed = test_ambiguity_logic()
    
    print("\n" + "=" * 80)
    print("FINAL RESULTS:")
    print(f"URS-003 Categorization: {'PASS' if urs003_passed else 'FAIL'}")
    print(f"Ambiguity Detection: {'PASS' if ambiguity_passed else 'FAIL'}")
    print(f"\nOverall: {'ALL TESTS PASS - TASK 12 COMPLETE' if urs003_passed and ambiguity_passed else 'TESTS FAILED'}")
    print("=" * 80)