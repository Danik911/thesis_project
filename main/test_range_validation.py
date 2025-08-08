#!/usr/bin/env python3
"""
Test that the system now accepts test counts within GAMP ranges (not just exactly 25).
This verifies the fix for the unreasonable "exactly 25" constraint.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "."))

from src.agents.oq_generator.yaml_parser import validate_yaml_data

def test_range_validation():
    """Test that various test counts are properly validated."""
    
    print("\n" + "="*80)
    print("TESTING: GAMP Category Range Validation (25-30 for Category 5)")
    print("="*80)
    
    # Test data with different test counts
    test_cases = []
    
    # Generate test case data (need at least 36 for our test scenarios)
    for i in range(1, 37):  # Generate 36 tests
        test_cases.append({
            "test_id": f"OQ-{i:03d}",
            "test_name": f"Test {i}",
            "test_category": "functional",
            "objective": f"Test objective {i}",
            "test_steps": [{"step": 1, "action": "test"}],
            "acceptance_criteria": ["Pass"],
            "gamp_category": 5
        })
    
    test_data = {
        "suite_id": "OQ-SUITE-0001",  # Must match pattern
        "gamp_category": 5,
        "document_name": "Test Document",
        "test_cases": test_cases,
        "version": "1.0",
        "generation_timestamp": "2025-01-01T00:00:00",
        "total_test_count": 27,  # Will be updated per scenario
        "pharmaceutical_compliance": {
            "gamp5_compliant": True,
            "cfr_part11_compliant": True
        }
    }
    
    # Test different counts
    # Acceptable range is 23-35, recommended is 25-30
    test_scenarios = [
        (22, False, "Below acceptable minimum (22 < 23)"),
        (23, True, "Minimum acceptable (23) - outside recommended"),
        (24, True, "Acceptable (24) - outside recommended"),
        (25, True, "Minimum recommended (25)"),
        (27, True, "Within recommended range (27)"),  # This was previously rejected!
        (30, True, "Maximum recommended (30)"),
        (31, True, "Acceptable (31) - outside recommended"),
        (35, True, "Maximum acceptable (35) - outside recommended"),
        (36, False, "Above acceptable maximum (36 > 35)")
    ]
    
    print("\nTest Results:")
    print("-" * 50)
    
    all_passed = True
    
    for count, should_pass, description in test_scenarios:
        # Adjust test case count
        test_data["test_cases"] = test_cases[:count]
        test_data["total_test_count"] = count
        
        try:
            validated_data = validate_yaml_data(test_data.copy())
            if should_pass:
                print(f"PASS: {count} tests - {description}")
            else:
                print(f"FAIL: {count} tests - Should have been rejected but passed!")
                all_passed = False
        except ValueError as e:
            if not should_pass:
                print(f"PASS: {count} tests CORRECTLY REJECTED - {description}")
            else:
                print(f"FAIL: {count} tests - Should have passed but was rejected!")
                print(f"  Error: {e}")
                all_passed = False
    
    print("-" * 50)
    
    if all_passed:
        print("\nSUCCESS: Range validation working correctly!")
        print("SUCCESS: The system now accepts 23-35 tests for Category 5")
        print("SUCCESS: Recommended range is 25-30 (with warnings)")
        print("SUCCESS: DeepSeek's 27 tests are perfectly valid!")
    else:
        print("\nFAILURE: Some test scenarios failed")
    
    print("="*80)
    
    return all_passed

if __name__ == "__main__":
    success = test_range_validation()
    sys.exit(0 if success else 1)