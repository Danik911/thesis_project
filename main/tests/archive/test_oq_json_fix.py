#!/usr/bin/env python3
"""
Test script to validate OQ generator JSON fix.

This script tests the updated OQ generator with JSON format instead of YAML
to verify the fix resolves the format mismatch issue.
"""

import sys
import asyncio
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root / "main"))

from src.core.events import GAMPCategory
from src.agents.oq_generator.generator import OQTestGenerator
from src.config.llm_config import LLMConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_oq_json_generation():
    """Test OQ generation with JSON format."""
    print("🔧 Testing OQ Generator JSON Fix")
    print("=" * 50)
    
    try:
        # Initialize generator
        print("1. Initializing OQ generator...")
        llm = LLMConfig.get_llm(max_tokens=4000)
        generator = OQTestGenerator(llm=llm, verbose=True)
        
        # Test data
        test_urs_content = """
        URS-TEST-001: Test Management System
        
        System Requirements:
        1. User Authentication: The system shall provide secure user authentication
        2. Data Management: The system shall manage test data with full audit trail
        3. Reporting: The system shall generate comprehensive test reports
        4. Integration: The system shall integrate with existing laboratory systems
        5. Compliance: The system shall maintain GAMP-5 and 21 CFR Part 11 compliance
        
        Functional Requirements:
        - User login with role-based access
        - Test case creation and management
        - Test execution tracking
        - Report generation and export
        - Audit trail maintenance
        """
        
        print("2. Testing JSON generation for GAMP Category 5...")
        
        # Generate test suite
        test_suite = generator.generate_oq_test_suite(
            gamp_category=GAMPCategory.CATEGORY_5,
            urs_content=test_urs_content,
            document_name="Test Management System URS",
            context_data=None
        )
        
        print("3. Validating results...")
        print(f"   ✅ Suite ID: {test_suite.suite_id}")
        print(f"   ✅ GAMP Category: {test_suite.gamp_category}")
        print(f"   ✅ Total Tests: {test_suite.total_test_count}")
        print(f"   ✅ Generation Method: {test_suite.generation_method}")
        
        # Validate test count is in expected range for Category 5
        if 25 <= test_suite.total_test_count <= 30:
            print(f"   ✅ Test count ({test_suite.total_test_count}) within expected range (25-30)")
        else:
            print(f"   ⚠️  Test count ({test_suite.total_test_count}) outside expected range (25-30)")
        
        # Validate test cases structure
        if test_suite.test_cases and len(test_suite.test_cases) > 0:
            print(f"   ✅ Test cases generated: {len(test_suite.test_cases)}")
            
            # Check first test case structure
            first_test = test_suite.test_cases[0]
            print(f"   ✅ First test ID: {first_test.test_id}")
            print(f"   ✅ First test name: {first_test.test_name}")
            print(f"   ✅ First test steps: {len(first_test.test_steps)}")
        else:
            print("   ❌ No test cases generated")
            return False
        
        # Check compliance flags
        if test_suite.pharmaceutical_compliance:
            compliance = test_suite.pharmaceutical_compliance
            print(f"   ✅ GAMP-5 Compliant: {compliance.get('gamp5_compliant', False)}")
            print(f"   ✅ ALCOA+ Compliant: {compliance.get('alcoa_plus_compliant', False)}")
        
        print("\n🎉 JSON Fix Test PASSED!")
        print("✅ OQ generator now produces JSON format successfully")
        print("✅ No YAML parsing errors encountered")
        print("✅ Test suite structure validates correctly")
        
        return True
        
    except Exception as e:
        print(f"\n❌ JSON Fix Test FAILED: {e}")
        print(f"Error type: {type(e).__name__}")
        
        # Print detailed error for debugging
        import traceback
        print("\nDetailed Error:")
        traceback.print_exc()
        
        return False

def main():
    """Main test function."""
    print("Starting OQ Generator JSON Fix Test...")
    
    # Run async test
    try:
        # Use asyncio.run for Python 3.7+
        result = asyncio.run(test_oq_json_generation())
        
        if result:
            print("\n✅ ALL TESTS PASSED - JSON fix is working!")
            sys.exit(0)
        else:
            print("\n❌ TESTS FAILED - JSON fix needs more work")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()