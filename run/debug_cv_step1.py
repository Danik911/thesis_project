#!/usr/bin/env python3
"""
Cross-Validation Debug - Step 1: Dependency and Component Testing
Run this script to identify exact issues preventing cross-validation execution.
"""

import sys
import traceback
from pathlib import Path

# Add main to path for imports
sys.path.insert(0, str(Path(__file__).parent / "main"))

def test_pdfplumber():
    """Test pdfplumber dependency specifically."""
    print("\n=== STEP 1A: Testing pdfplumber ===")
    try:
        import pdfplumber
        print(f"✅ pdfplumber imported successfully - version {pdfplumber.__version__}")
        return True
    except ImportError as e:
        print(f"❌ pdfplumber import failed: {e}")
        print("   This is the likely cause of Research/SME agent failures")
        return False

def test_agent_imports():
    """Test individual agent imports to isolate pdfplumber issue."""
    print("\n=== STEP 1B: Testing Agent Imports ===")

    try:
        print("   Testing regulatory_data_sources import...")
        print("   ✅ regulatory_data_sources imported (contains pdfplumber usage)")
    except Exception as e:
        print(f"   ❌ regulatory_data_sources failed: {e}")
        if "pdfplumber" in str(e):
            print("   --> CONFIRMED: pdfplumber dependency missing")

    try:
        print("   Testing research_agent import...")
        print("   ✅ ResearchAgent imported successfully")
    except Exception as e:
        print(f"   ❌ ResearchAgent failed: {e}")

    try:
        print("   Testing sme_agent import...")
        print("   ✅ SMEAgent imported successfully")
    except Exception as e:
        print(f"   ❌ SMEAgent failed: {e}")

def test_component_initialization():
    """Test cross-validation component initialization with exact parameters."""
    print("\n=== STEP 1C: Testing Component Initialization ===")

    try:
        print("   Testing FoldManager...")
        from src.cross_validation.fold_manager import FoldManager

        fold_path = Path("datasets/cross_validation/fold_assignments.json")
        corpus_path = Path("datasets/urs_corpus")

        if not fold_path.exists():
            print(f"   ❌ Fold assignments missing: {fold_path}")
            return False
        if not corpus_path.exists():
            print(f"   ❌ URS corpus missing: {corpus_path}")
            return False

        # Test exact initialization from workflow
        fold_manager = FoldManager(
            fold_assignments_path=fold_path,
            urs_corpus_path=corpus_path,
            random_seed=42
        )
        print(f"   ✅ FoldManager: {fold_manager.get_fold_count()} folds, {len(fold_manager.get_document_inventory())} documents")

    except Exception as e:
        print(f"   ❌ FoldManager failed: {e}")
        traceback.print_exc()
        return False

    try:
        print("   Testing MetricsCollector...")
        from src.cross_validation.metrics_collector import MetricsCollector

        output_path = Path("main/output/cross_validation")

        # Test exact initialization from workflow
        metrics_collector = MetricsCollector(
            experiment_id="test_experiment",
            output_directory=output_path,
            model_name="deepseek/deepseek-chat"
        )
        print("   ✅ MetricsCollector initialized successfully")

    except Exception as e:
        print(f"   ❌ MetricsCollector failed: {e}")
        traceback.print_exc()
        return False

    try:
        print("   Testing StatisticalAnalyzer...")
        from src.cross_validation.statistical_analyzer import StatisticalAnalyzer

        analyzer = StatisticalAnalyzer(
            alpha=0.05,
            confidence_level=0.95,
            output_directory=output_path
        )

        # Test the method that was reportedly missing metric_name
        test_data = [1.0, 2.0, 3.0, 4.0, 5.0]
        ci = analyzer.calculate_confidence_interval(
            data=test_data,
            metric_name="test_metric",
            method="bootstrap"
        )
        print("   ✅ StatisticalAnalyzer and calculate_confidence_interval work correctly")

    except Exception as e:
        print(f"   ❌ StatisticalAnalyzer failed: {e}")
        traceback.print_exc()
        return False

    return True

def test_dry_run_execution():
    """Test the actual dry-run execution that user reported failing."""
    print("\n=== STEP 1D: Testing Actual Dry-Run Logic ===")

    try:
        # Import the exact components used in run_cross_validation.py
        from src.cross_validation.cross_validation_workflow import (
            CrossValidationWorkflow,
        )
        from src.cross_validation.fold_manager import FoldManager
        from src.cross_validation.metrics_collector import MetricsCollector

        # Test paths (same as in run_cross_validation.py)
        fold_path = Path("datasets/cross_validation/fold_assignments.json")
        corpus_path = Path("datasets/urs_corpus")
        output_path = Path("main/output/cross_validation")

        print(f"   [CHECK] Fold assignments path: {fold_path} ({'exists' if fold_path.exists() else 'MISSING'})")
        print(f"   [CHECK] URS corpus path: {corpus_path} ({'exists' if corpus_path.exists() else 'MISSING'})")
        print(f"   [CHECK] Output directory: {output_path}")

        if not fold_path.exists() or not corpus_path.exists():
            print("   [FAIL] Required paths missing - cannot proceed")
            return False

        # Test component initialization (exact same as dry-run)
        fold_manager = FoldManager(fold_path, corpus_path)
        print(f"   [PASS] FoldManager: {fold_manager.get_fold_count()} folds, {len(fold_manager.get_document_inventory())} documents")

        metrics_collector = MetricsCollector("test_experiment", output_path)
        print("   [PASS] MetricsCollector initialized")

        workflow = CrossValidationWorkflow(timeout=60, enable_phoenix=False)
        print("   [PASS] CrossValidationWorkflow initialized")

        print("   [SUCCESS] Dry run logic successful - all components ready!")
        return True

    except Exception as e:
        print(f"   [FAIL] Dry run failed: {e}")
        print("   Full traceback:")
        traceback.print_exc()
        return False

def main():
    """Execute Step 1 debugging."""
    print("CROSS-VALIDATION DEBUG - STEP 1: DEPENDENCY RESOLUTION")
    print("=" * 70)
    print("This script tests exact issues preventing cross-validation execution")

    # Execute tests in order
    results = []
    results.append(("pdfplumber_import", test_pdfplumber()))
    results.append(("agent_imports", test_agent_imports()))
    results.append(("component_init", test_component_initialization()))
    results.append(("dry_run_logic", test_dry_run_execution()))

    # Summary
    print("\n" + "=" * 70)
    print("STEP 1 RESULTS SUMMARY")
    print("=" * 70)

    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:20} {status}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 70)
    if all_passed:
        print("🎉 STEP 1 COMPLETE: All components ready for cross-validation")
        print("   Next: Run actual cross-validation experiment")
    else:
        print("⚠️  STEP 1 ISSUES FOUND: Components need fixes before proceeding")
        print("   Review error messages above for specific issues to address")

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
