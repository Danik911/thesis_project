"""
Critical validation of Task 12 - Real test with actual LLM categorization.
"""

import os
import sys
from pathlib import Path
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up environment
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
os.environ["LLM_MODEL"] = "gpt-4.1-mini-2025-04-14"

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent / "main"))

from src.agents.categorization.agent import categorize_with_pydantic_structured_output
from src.agents.categorization.error_handler import CategorizationErrorHandler

def test_urs003_real_categorization():
    """Test URS-003 with actual LLM-based categorization."""
    
    # URS-003 from the test data file
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
    
    print("CRITICAL VALIDATION: Task 12 Real Test")
    print("=" * 80)
    print("Testing URS-003 with actual LLM categorization...")
    print("-" * 60)
    
    try:
        # Initialize error handler
        error_handler = CategorizationErrorHandler()
        
        # Run actual LLM-based categorization
        print("Calling LLM-based categorization...")
        result = categorize_with_pydantic_structured_output(
            requirement_id="URS-003",
            urs_content=urs003_content,
            error_handler=error_handler
        )
        
        print(f"\n✓ Categorization completed")
        print(f"Category: {result.category}")
        print(f"Confidence: {result.confidence:.3f}")
        print(f"Rationale: {result.rationale}")
        print(f"Evidence: {result.evidence}")
        
        # Validate results
        success = True
        issues = []
        
        # Check category
        if result.category != 5:
            issues.append(f"Wrong category: {result.category} (expected 5)")
            success = False
        else:
            print(f"\n✅ PASS: Correct Category 5 identified")
            
        # Check confidence
        if result.confidence < 0.7:
            issues.append(f"Low confidence: {result.confidence:.3f} (expected >0.7)")
            success = False
        else:
            print(f"✅ PASS: High confidence {result.confidence:.3f}")
            
        # Check for proper categorization reasoning
        if "custom" in result.rationale.lower():
            print(f"✅ PASS: Rationale mentions custom development")
        else:
            issues.append("Rationale doesn't mention custom development")
            
        # Final verdict
        print("\n" + "="*80)
        if success:
            print("✅ TASK 12 VALIDATED: URS-003 categorizes correctly as Category 5")
            print("   No false ambiguity, high confidence achieved")
        else:
            print("❌ TASK 12 FAILED VALIDATION:")
            for issue in issues:
                print(f"   - {issue}")
                
        return success
        
    except Exception as e:
        print(f"\n❌ EXCEPTION: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Check API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ ERROR: OPENAI_API_KEY not found in environment")
        sys.exit(1)
        
    # Run the real test
    success = test_urs003_real_categorization()
    
    print("\n" + "="*80)
    print("CRITICAL EVALUATION COMPLETE")
    print("="*80)
    
    if success:
        print("✅ Task 12 is ACTUALLY working correctly")
    else:
        print("❌ Task 12 has REAL issues that need fixing")
        
    sys.exit(0 if success else 1)