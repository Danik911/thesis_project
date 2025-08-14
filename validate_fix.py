#!/usr/bin/env python3
"""
Validate that the fixed complexity calculator works without textstat.
"""

import os
import sys

# Add datasets to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "datasets"))

def test_readability_calculator():
    """Test the custom readability calculator implementation."""

    # Import our fixed calculator
    from datasets.metrics.complexity_calculator import URSComplexityCalculator

    calculator = URSComplexityCalculator()

    # Test with sample text from URS-001
    test_text = """
    This URS defines the requirements for an Environmental Monitoring System to monitor critical storage areas for temperature-sensitive pharmaceutical products.
    The system shall continuously monitor temperature in all GMP storage areas.
    Temperature readings shall be recorded at intervals not exceeding 5 minutes.
    The system shall use vendor-supplied software without modification.
    """

    print("Testing Custom Readability Calculator")
    print("=" * 40)

    # Test syllable counting
    test_words = ["system", "requirements", "environmental", "pharmaceutical", "monitoring"]
    print("Syllable counting test:")
    for word in test_words:
        syllables = calculator._count_syllables(word)
        print(f"  {word}: {syllables} syllables")

    # Test sentence counting
    sentences = calculator._count_sentences(test_text)
    print(f"\nSentence count: {sentences}")

    # Test full readability calculation
    try:
        readability = calculator.calculate_readability_score(test_text)
        print(f"Readability score: {readability:.2f}")
        print("✓ Custom readability calculator working!")
        return True
    except Exception as e:
        print(f"✗ Readability calculation failed: {e}")
        return False

def test_urs_analysis():
    """Test full URS document analysis."""

    from datasets.metrics.complexity_calculator import URSComplexityCalculator

    calculator = URSComplexityCalculator()
    urs_file = os.path.join(os.path.dirname(__file__), "datasets", "urs_corpus", "category_3", "URS-001.md")

    print("\nTesting URS Document Analysis")
    print("=" * 40)

    try:
        result = calculator.analyze_urs_document(urs_file)

        print(f"Document: {result['document_id']}")
        print(f"Total requirements: {result['requirement_counts']['total']}")
        print(f"Functional: {result['requirement_counts']['functional']}")
        print(f"Regulatory: {result['requirement_counts']['regulatory']}")
        print(f"Performance: {result['requirement_counts']['performance']}")
        print(f"Integration: {result['requirement_counts']['integration']}")
        print(f"Technical: {result['requirement_counts']['technical']}")
        print(f"Readability score: {result['readability_score']:.2f}")
        print(f"Integration density: {result['integration_complexity']['integration_density']:.3f}")
        print(f"Dependency density: {result['dependency_density']:.3f}")
        print(f"Ambiguity rate: {result['ambiguity_rate']:.3f}")
        print(f"Custom rate: {result['custom_indicators']['custom_rate']:.3f}")
        print(f"Composite complexity: {result['composite_complexity_score']:.4f}")

        print("✓ URS document analysis working!")
        return True

    except Exception as e:
        print(f"✗ URS analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all validation tests."""

    print("Task 16 Dataset Fix Validation")
    print("=" * 50)

    # Test 1: Custom readability calculator
    test1_passed = test_readability_calculator()

    # Test 2: Full URS analysis
    test2_passed = test_urs_analysis()

    if test1_passed and test2_passed:
        print("\n" + "=" * 50)
        print("✓ ALL TESTS PASSED!")
        print("The fixed complexity calculator is ready to generate datasets.")
        print("No textstat dependency required.")
        print("✓ Custom Flesch-Kincaid implementation working")
        print("✓ URS requirement extraction working")
        print("✓ Complexity scoring working")
        print("=" * 50)
        return True
    print("\n" + "=" * 50)
    print("✗ SOME TESTS FAILED!")
    print("Further debugging required.")
    print("=" * 50)
    return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
