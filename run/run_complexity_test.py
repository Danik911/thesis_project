#!/usr/bin/env python3
"""
Execute the complexity calculator test to generate missing dataset files.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "datasets"))

# Test if we can import the fixed complexity calculator
try:
    from datasets.metrics.complexity_calculator import (
        URSComplexityCalculator,
        analyze_urs_corpus,
    )
    print("✓ Successfully imported fixed complexity calculator")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# Test single document analysis
try:
    calculator = URSComplexityCalculator()
    test_file = os.path.join(os.path.dirname(__file__), "datasets", "urs_corpus", "category_3", "URS-001.md")

    print(f"Testing: {test_file}")
    result = calculator.analyze_urs_document(test_file)

    print("✓ Document analysis successful")
    print(f"  - Document ID: {result['document_id']}")
    print(f"  - Complexity Score: {result['composite_complexity_score']:.4f}")
    print(f"  - Readability Score: {result['readability_score']:.2f}")
    print(f"  - Total Requirements: {result['requirement_counts']['total']}")

except Exception as e:
    print(f"✗ Single document test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*50)
print("BASIC TEST PASSED - Ready to generate full dataset")
print("="*50)
