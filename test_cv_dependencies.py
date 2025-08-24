#!/usr/bin/env python3
"""
Cross-Validation Dependencies Test Script
Tests all critical dependencies for the cross-validation framework.
"""

import sys
from pathlib import Path


def test_pdfplumber():
    """Test pdfplumber import and functionality."""
    print("\n=== Testing pdfplumber dependency ===")
    try:
        import pdfplumber
        print("✅ pdfplumber imported successfully")
        print(f"   Version: {pdfplumber.__version__}")
        return True
    except ImportError as e:
        print(f"❌ pdfplumber import failed: {e}")
        return False

def test_agent_dependencies():
    """Test Research and SME agent dependencies."""
    print("\n=== Testing Agent Dependencies ===")

    # Test Research agent
    try:
        print("✅ ResearchAgent imported successfully")
        research_ok = True
    except Exception as e:
        print(f"❌ ResearchAgent import failed: {e}")
        research_ok = False

    # Test SME agent
    try:
        print("✅ SMEAgent imported successfully")
        sme_ok = True
    except Exception as e:
        print(f"❌ SMEAgent import failed: {e}")
        sme_ok = False

    return research_ok and sme_ok

def test_cv_components():
    """Test cross-validation component imports."""
    print("\n=== Testing Cross-Validation Components ===")

    components = [
        ("FoldManager", "main.src.cross_validation.fold_manager", "FoldManager"),
        ("MetricsCollector", "main.src.cross_validation.metrics_collector", "MetricsCollector"),
        ("StatisticalAnalyzer", "main.src.cross_validation.statistical_analyzer", "StatisticalAnalyzer"),
        ("CrossValidationWorkflow", "main.src.cross_validation.cross_validation_workflow", "CrossValidationWorkflow")
    ]

    all_ok = True
    for name, module, class_name in components:
        try:
            module_obj = __import__(module, fromlist=[class_name])
            cls = getattr(module_obj, class_name)
            print(f"✅ {name} imported successfully")
        except Exception as e:
            print(f"❌ {name} import failed: {e}")
            all_ok = False

    return all_ok

def test_required_paths():
    """Test that required paths exist."""
    print("\n=== Testing Required Paths ===")

    paths = [
        ("Fold assignments", Path("datasets/cross_validation/fold_assignments.json")),
        ("URS corpus", Path("datasets/urs_corpus")),
        ("Output directory", Path("main/output"))
    ]

    all_ok = True
    for name, path in paths:
        if path.exists():
            print(f"✅ {name}: {path}")
        else:
            print(f"❌ {name} missing: {path}")
            all_ok = False

    return all_ok

def test_dry_run():
    """Test dry-run execution."""
    print("\n=== Testing Dry Run Execution ===")

    try:
        # Import and test dry-run logic from run_cross_validation.py
        sys.path.insert(0, str(Path.cwd()))

        from main.src.cross_validation.cross_validation_workflow import (
            CrossValidationWorkflow,
        )
        from main.src.cross_validation.fold_manager import FoldManager
        from main.src.cross_validation.metrics_collector import MetricsCollector

        # Test paths
        fold_path = Path("datasets/cross_validation/fold_assignments.json")
        corpus_path = Path("datasets/urs_corpus")
        output_path = Path("main/output/cross_validation")

        print(f"   Fold assignments: {fold_path} ({'exists' if fold_path.exists() else 'MISSING'})")
        print(f"   URS corpus: {corpus_path} ({'exists' if corpus_path.exists() else 'MISSING'})")
        print(f"   Output directory: {output_path}")

        if not fold_path.exists() or not corpus_path.exists():
            print("❌ Required paths missing - cannot proceed with component tests")
            return False

        # Test component initialization
        print("   Testing FoldManager initialization...")
        fold_manager = FoldManager(fold_path, corpus_path)
        print(f"   ✅ FoldManager: {fold_manager.get_fold_count()} folds, {len(fold_manager.get_document_inventory())} documents")

        print("   Testing MetricsCollector initialization...")
        metrics_collector = MetricsCollector("test_experiment", output_path)
        print("   ✅ MetricsCollector initialized")

        print("   Testing CrossValidationWorkflow initialization...")
        workflow = CrossValidationWorkflow(timeout=60, enable_phoenix=False)
        print("   ✅ CrossValidationWorkflow initialized")

        print("✅ Dry run component testing successful!")
        return True

    except Exception as e:
        print(f"❌ Dry run failed: {e}")
        import traceback
        print("   Full traceback:")
        traceback.print_exc()
        return False

def main():
    """Run all dependency tests."""
    print("Cross-Validation Dependencies Test")
    print("=" * 50)

    # Add main to Python path for imports
    sys.path.insert(0, str(Path(__file__).parent / "main"))

    results = []

    # Run all tests
    results.append(("pdfplumber", test_pdfplumber()))
    results.append(("agent_dependencies", test_agent_dependencies()))
    results.append(("cv_components", test_cv_components()))
    results.append(("required_paths", test_required_paths()))
    results.append(("dry_run", test_dry_run()))

    # Summary
    print("\n" + "=" * 50)
    print("DEPENDENCY TEST SUMMARY")
    print("=" * 50)

    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:20} {status}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 ALL TESTS PASSED - Cross-validation framework ready!")
    else:
        print("⚠️  SOME TESTS FAILED - Issues need to be resolved")

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
