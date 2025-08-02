"""
Simple test script to validate Task 12 categorization accuracy fix.
Tests URS-003 for proper categorization without false ambiguity.
"""

import os
import sys
from pathlib import Path
import asyncio
from dotenv import load_dotenv

# Add main directory to path
sys.path.insert(0, str(Path(__file__).parent / "main"))

# Load environment variables
load_dotenv()

# Set required environment variables
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
os.environ["LLM_MODEL"] = "gpt-4.1-mini-2025-04-14"

# Now import after setting up the environment
from src.agents.categorization.tools import categorize_requirement_tool
from src.core.models.requirement import UserRequirement

# Test URS-003 case specifically
test_requirement = UserRequirement(
    id="URS-003",
    title="Automated Test Report Generation with Custom Templates",
    description="The system shall provide automated generation of test execution reports using customizable templates that comply with regulatory requirements for pharmaceutical validation documentation.",
    rationale="Standardized reporting ensures consistent documentation across all test executions while allowing flexibility for project-specific requirements.",
    acceptance_criteria=[
        "System generates reports in multiple formats (PDF, Word, HTML)",
        "Templates support dynamic data insertion from test results", 
        "Reports include all required regulatory compliance fields",
        "Custom templates can be created and saved for reuse",
        "Report generation completes within 60 seconds for standard test suites"
    ]
)

async def test_urs003():
    """Test URS-003 categorization specifically."""
    print("\n" + "="*80)
    print("TASK 12 - URS-003 CATEGORIZATION TEST")
    print("="*80 + "\n")
    
    print(f"Testing: {test_requirement.id} - {test_requirement.title}")
    print("-" * 60)
    
    try:
        # Call the categorization tool directly
        print("Running categorization tool...")
        result = await categorize_requirement_tool(
            requirement_id=test_requirement.id,
            title=test_requirement.title,
            description=test_requirement.description,
            rationale=test_requirement.rationale,
            acceptance_criteria=test_requirement.acceptance_criteria
        )
        
        print(f"\n✓ Categorization completed successfully")
        print(f"  Category: {result['category']}")
        print(f"  Confidence: {result['confidence']:.2f}")
        print(f"  Rationale: {result['rationale']}")
        print(f"  Evidence: {result['evidence']}")
        
        # Check results
        success = True
        if result['category'] == 5:
            print(f"\n✅ PASS: Correct Category 5 identified")
        else:
            print(f"\n❌ FAIL: Wrong category {result['category']} (expected 5)")
            success = False
            
        if result['confidence'] >= 0.7:
            print(f"✅ PASS: High confidence {result['confidence']:.2f} (no false ambiguity)")
        else:
            print(f"❌ FAIL: Low confidence {result['confidence']:.2f} indicates false ambiguity detection")
            success = False
            
        if "custom" in result['rationale'].lower():
            print(f"✅ PASS: Rationale correctly identifies custom development")
        else:
            print(f"⚠️  WARNING: Rationale doesn't mention custom development")
        
        return success
        
    except Exception as e:
        print(f"\n❌ EXCEPTION: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Run the test
    success = asyncio.run(test_urs003())
    
    if success:
        print("\n✅ Task 12 implementation is working correctly for URS-003!")
    else:
        print("\n❌ Task 12 implementation has issues - needs debugging")
    
    sys.exit(0 if success else 1)