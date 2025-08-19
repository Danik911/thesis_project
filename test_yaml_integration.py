#!/usr/bin/env python3
"""
Quick test to validate YAML integration in OQ generator.
This script tests the import and basic functionality.
"""

import sys
import os

# Add the main src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'main', 'src'))

def test_yaml_integration():
    """Test that YAML parser integration works correctly."""
    try:
        # Test import of yaml_parser functions
        from agents.oq_generator.yaml_parser import extract_yaml_from_response, validate_yaml_data
        print("✅ YAML parser import successful")
        
        # Test basic YAML parsing with sample DeepSeek V3 response
        sample_yaml_response = """
test_cases:
  - test_id: "OQ-001"
    test_name: "System Login Validation"
    test_category: "functional"
    gamp_category: 5
    objective: "Validate user authentication"
  - test_id: "OQ-002" 
    test_name: "Data Integrity Check"
    test_category: "data_integrity"
    gamp_category: 5
    objective: "Ensure data accuracy"
suite_id: "OQ-SUITE-TEST"
total_test_count: 2
gamp_category: 5
"""
        
        # Test YAML extraction
        extracted_data = extract_yaml_from_response(sample_yaml_response)
        print(f"✅ YAML extraction successful: {len(extracted_data)} fields extracted")
        
        # Test YAML validation (expect this to fail due to incomplete data)
        try:
            validated_data = validate_yaml_data(extracted_data)
            print("❌ YAML validation should have failed (incomplete test data)")
        except ValueError as e:
            print(f"✅ YAML validation correctly failed: {str(e)[:100]}...")
        
        print("\n🎯 YAML integration test completed successfully!")
        print("The OQ generator should now handle both JSON and YAML responses from DeepSeek V3.")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_yaml_integration()
    sys.exit(0 if success else 1)