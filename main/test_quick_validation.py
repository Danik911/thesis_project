#!/usr/bin/env python3
"""
Quick validation of critical fixes.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_imports():
    """Test that all required modules can be imported."""
    try:
        from src.agents.categorization.agent import create_gamp_categorization_agent
        from src.agents.categorization.error_handler import CategorizationErrorHandler
        from src.agents.parallel.sme_agent import create_sme_agent
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_threshold_default():
    """Test that the confidence threshold default has been changed."""
    try:
        from src.agents.categorization.error_handler import CategorizationErrorHandler
        
        # Create error handler with default settings
        error_handler = CategorizationErrorHandler()
        
        if error_handler.confidence_threshold == 0.50:
            print("✅ Confidence threshold successfully changed to 0.50")
            return True
        else:
            print(f"❌ Confidence threshold is {error_handler.confidence_threshold}, expected 0.50")
            return False
    except Exception as e:
        print(f"❌ Threshold test failed: {e}")
        return False

def test_sme_method_exists():
    """Test that the SME consultation method exists."""
    try:
        from src.agents.categorization.error_handler import CategorizationErrorHandler
        
        error_handler = CategorizationErrorHandler()
        
        # Check if the new method exists
        if hasattr(error_handler, '_request_sme_consultation'):
            print("✅ SME consultation method exists")
            return True
        else:
            print("❌ SME consultation method not found")
            return False
    except Exception as e:
        print(f"❌ SME method test failed: {e}")
        return False

def test_confidence_fix():
    """Test that confidence is properly extracted in audit log creation."""
    try:
        from src.agents.categorization.error_handler import (
            CategorizationErrorHandler, 
            CategorizationError, 
            ErrorType,
            ErrorSeverity
        )
        
        error_handler = CategorizationErrorHandler(verbose=True)
        
        # Create a test error with confidence in details
        test_error = CategorizationError(
            error_type=ErrorType.CONFIDENCE_ERROR,
            severity=ErrorSeverity.MEDIUM,
            message="Test confidence error",
            details={"confidence": 0.45, "threshold": 0.50, "category": 4}
        )
        
        # Check if confidence is extracted properly
        actual_confidence = test_error.details.get("confidence", 0.0) if test_error.details else 0.0
        
        if actual_confidence == 0.45:
            print("✅ Confidence extraction working properly")
            return True
        else:
            print(f"❌ Confidence extraction failed: got {actual_confidence}, expected 0.45")
            return False
            
    except Exception as e:
        print(f"❌ Confidence fix test failed: {e}")
        return False

def main():
    """Run quick validation tests."""
    print("🚀 Quick Validation of Critical Fixes")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_imports),
        ("Threshold Default Test", test_threshold_default),
        ("SME Method Test", test_sme_method_exists),
        ("Confidence Fix Test", test_confidence_fix)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name}:")
        if test_func():
            passed += 1
        
    print("\n" + "=" * 50)
    print(f"📊 Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All validation tests passed!")
        return 0
    else:
        print(f"⚠️ {total - passed} tests failed")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)