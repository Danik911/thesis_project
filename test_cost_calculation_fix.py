#!/usr/bin/env python3
"""
Test script to validate the cost calculation bug fix.

This script verifies that the cost calculation now produces the correct
values after fixing the pricing constants in cross_validation_workflow.py.
"""

import sys
from pathlib import Path

# Add the main source directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "main" / "src"))

def test_pricing_constants():
    """Test the centralized pricing constants module."""
    from cross_validation.pricing_constants import (
        calculate_deepseek_v3_cost,
        validate_pricing_consistency,
        DEEPSEEK_V3_INPUT_COST_PER_1M,
        DEEPSEEK_V3_OUTPUT_COST_PER_1M
    )
    
    print("Testing centralized pricing constants...")
    
    # Verify correct pricing constants
    assert DEEPSEEK_V3_INPUT_COST_PER_1M == 0.14, f"Expected 0.14, got {DEEPSEEK_V3_INPUT_COST_PER_1M}"
    assert DEEPSEEK_V3_OUTPUT_COST_PER_1M == 0.28, f"Expected 0.28, got {DEEPSEEK_V3_OUTPUT_COST_PER_1M}"
    
    # Test the problematic case
    prompt_tokens = 2000
    completion_tokens = 1000
    expected_cost = 0.00056
    
    actual_cost = calculate_deepseek_v3_cost(prompt_tokens, completion_tokens)
    
    print(f"Test case: {prompt_tokens} prompt + {completion_tokens} completion tokens")
    print(f"Expected cost: ${expected_cost:.6f}")
    print(f"Actual cost:   ${actual_cost:.6f}")
    print(f"Difference:    ${abs(actual_cost - expected_cost):.8f}")
    
    # Verify the calculation is correct
    assert abs(actual_cost - expected_cost) < 0.000001, f"Cost calculation still incorrect: {actual_cost} != {expected_cost}"
    
    # Run validation
    validate_pricing_consistency()
    
    print("✅ Cost calculation fix validated successfully!")
    return True


def test_metrics_collector_consistency():
    """Test that MetricsCollector uses correct pricing."""
    from cross_validation.metrics_collector import MetricsCollector
    
    print("\nTesting MetricsCollector pricing consistency...")
    
    # Check that constants are correct
    assert MetricsCollector.DEEPSEEK_V3_PROMPT_COST_PER_1M == 0.14
    assert MetricsCollector.DEEPSEEK_V3_COMPLETION_COST_PER_1M == 0.28
    
    print("✅ MetricsCollector uses correct pricing constants!")
    return True


def main():
    """Run all cost calculation tests."""
    print("🔧 Testing Cost Calculation Bug Fix")
    print("=" * 50)
    
    try:
        test_pricing_constants()
        test_metrics_collector_consistency()
        
        print("\n" + "=" * 50)
        print("🎉 ALL TESTS PASSED - Cost calculation bug fixed!")
        print("\nKey improvements:")
        print("• Fixed incorrect pricing constants (0.27→0.14, 1.10→0.28)")
        print("• Added centralized pricing module for consistency")
        print("• Added defensive validation to catch future errors")
        print("• Test case now calculates correct $0.00056 cost")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)