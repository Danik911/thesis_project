#!/usr/bin/env python3
"""
Simple validation script to test the OQ generation configuration fix.
"""

import os
import sys

# Add the main directory to Python path
main_dir = os.path.join(os.path.dirname(__file__), "main")
sys.path.insert(0, main_dir)

def validate_configurations():
    """Validate that templates.py and models.py are now aligned."""
    try:
        from src.agents.oq_generator.templates import GAMPCategoryConfig
        from src.core.events import GAMPCategory

        print("Testing GAMP Category 5 configuration alignment...")

        # Get Category 5 config from templates.py
        cat5_config = GAMPCategoryConfig.get_category_config(GAMPCategory.CATEGORY_5)
        min_tests = cat5_config["min_tests"]
        max_tests = cat5_config["max_tests"]

        print(f"Templates.py Category 5: {min_tests}-{max_tests} tests")

        # Check if it matches expected values
        if min_tests == 25 and max_tests == 30:
            print("✅ Templates.py Category 5 configuration is correct (25-30 tests)")
        else:
            print(f"❌ Templates.py Category 5 configuration is wrong: expected 25-30, got {min_tests}-{max_tests}")
            return False

        # Test that the updated config works with models.py validation
        try:
            from src.agents.oq_generator.models import OQGenerationConfig

            # Test minimum count (25)
            config = OQGenerationConfig(
                gamp_category=5,
                document_name="Test Document",
                target_test_count=25
            )
            print("✅ Category 5 minimum (25 tests) accepted by models.py validation")

            # Test maximum count (30)
            config = OQGenerationConfig(
                gamp_category=5,
                document_name="Test Document",
                target_test_count=30
            )
            print("✅ Category 5 maximum (30 tests) accepted by models.py validation")

            # Test that old count (20) is now rejected
            try:
                config = OQGenerationConfig(
                    gamp_category=5,
                    document_name="Test Document",
                    target_test_count=20  # This should fail now
                )
                print("❌ Category 5 with 20 tests should be rejected but was accepted")
                return False
            except ValueError as e:
                print(f"✅ Category 5 with 20 tests correctly rejected: {str(e)[:80]}...")

        except ImportError as e:
            print(f"❌ Could not import models: {e}")
            return False

        print("\n🎉 Configuration alignment verification PASSED!")
        print("The OQ generation workflow should now work correctly for GAMP Category 5")
        return True

    except Exception as e:
        print(f"❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("OQ Generation Configuration Fix Validation")
    print("=" * 60)

    success = validate_configurations()

    if success:
        print("\n" + "=" * 60)
        print("✅ VALIDATION SUCCESSFUL - Fix is working correctly!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("❌ VALIDATION FAILED - Issues remain")
        print("=" * 60)
        sys.exit(1)
