#!/usr/bin/env python3
"""
Test script to verify the OQ generation configuration mismatch fix.

This script tests that the templates.py and models.py configurations are now aligned
for GAMP Category 5, and that the generator can request the correct test count.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'main'))

from src.core.events import GAMPCategory
from src.agents.oq_generator.templates import GAMPCategoryConfig
from src.agents.oq_generator.models import OQGenerationConfig, OQTestSuite

def test_configuration_alignment():
    """Test that templates.py and models.py have aligned configurations."""
    print("Testing GAMP Category configuration alignment...")
    
    # Test all categories
    categories_to_test = [
        GAMPCategory.CATEGORY_1,
        GAMPCategory.CATEGORY_3, 
        GAMPCategory.CATEGORY_4,
        GAMPCategory.CATEGORY_5
    ]
    
    for category in categories_to_test:
        print(f"\nTesting GAMP Category {category.value}:")
        
        # Get config from templates.py
        template_config = GAMPCategoryConfig.get_category_config(category)
        min_tests = template_config["min_tests"]
        max_tests = template_config["max_tests"]
        
        print(f"  Templates.py: {min_tests}-{max_tests} tests")
        
        # Test with OQGenerationConfig (uses models.py validation)
        try:
            # Test minimum count
            config_min = OQGenerationConfig(
                gamp_category=category.value,
                document_name="Test Document",
                target_test_count=min_tests
            )
            print(f"  ✅ Minimum test count ({min_tests}) accepted by models.py")
            
            # Test maximum count  
            config_max = OQGenerationConfig(
                gamp_category=category.value,
                document_name="Test Document", 
                target_test_count=max_tests
            )
            print(f"  ✅ Maximum test count ({max_tests}) accepted by models.py")
            
        except ValueError as e:
            print(f"  ❌ Configuration mismatch: {e}")
            return False
            
    print(f"\n✅ All GAMP category configurations are aligned!")
    return True

def test_category_5_specific():
    """Test Category 5 specific requirements."""
    print("\nTesting GAMP Category 5 specific fixes...")
    
    category_5_config = GAMPCategoryConfig.get_category_config(GAMPCategory.CATEGORY_5)
    print(f"Category 5 config: {category_5_config['min_tests']}-{category_5_config['max_tests']} tests")
    
    # Test that 25 tests (new minimum) is accepted
    try:
        config = OQGenerationConfig(
            gamp_category=5,
            document_name="Custom Application URS",
            target_test_count=25  # New minimum
        )
        print("✅ Category 5 minimum (25 tests) is now accepted")
    except ValueError as e:
        print(f"❌ Category 5 minimum test count still rejected: {e}")
        return False
        
    # Test that 20 tests (old maximum) is now rejected  
    try:
        config = OQGenerationConfig(
            gamp_category=5,
            document_name="Custom Application URS", 
            target_test_count=20  # Old maximum that caused the issue
        )
        print("❌ Category 5 with 20 tests should be rejected but was accepted")
        return False
    except ValueError as e:
        print(f"✅ Category 5 with 20 tests correctly rejected: {e}")
        
    return True

def main():
    """Run all configuration tests."""
    print("=" * 60)
    print("OQ Generation Configuration Fix Verification")
    print("=" * 60)
    
    try:
        # Test configuration alignment
        alignment_ok = test_configuration_alignment()
        
        # Test Category 5 specific fixes
        category_5_ok = test_category_5_specific()
        
        if alignment_ok and category_5_ok:
            print("\n" + "=" * 60)
            print("🎉 ALL TESTS PASSED - Configuration fix is successful!")
            print("The OQ generation workflow should now work correctly for Category 5")
            print("=" * 60)
            return 0
        else:
            print("\n" + "=" * 60)
            print("❌ TESTS FAILED - Configuration issues remain")
            print("=" * 60)
            return 1
            
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())