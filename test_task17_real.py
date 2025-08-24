#!/usr/bin/env python3
"""
Test Task 17 Cross-Validation Framework - Real Execution
"""

import json
import sys
from pathlib import Path

# Add main to path
sys.path.insert(0, "main")

print("="*60)
print("TASK 17 REAL VALIDATION TEST")
print("="*60)

# Test 1: Check if cross-validation module exists
print("\n1. Module Import Test:")
try:
    from src.cross_validation import (
        CrossValidationWorkflow,
        FoldManager,
        MetricsCollector,
    )
    print("[PASS] Core cross-validation modules imported successfully")

    # Try importing analysis components directly
    try:
        from src.cross_validation.coverage_analyzer import CoverageAnalyzer
        from src.cross_validation.quality_metrics import QualityMetrics
        from src.cross_validation.results_aggregator import ResultsAggregator
        from src.cross_validation.statistical_analyzer import StatisticalAnalyzer
        print("[PASS] Analysis components imported successfully")
    except ImportError as e:
        print(f"[WARNING] Analysis components not found: {e}")
        CoverageAnalyzer = None
        QualityMetrics = None
        StatisticalAnalyzer = None
        ResultsAggregator = None
except ImportError as e:
    print(f"[FAIL] Core import error: {e}")
    sys.exit(1)

# Test 2: Check fold assignments
print("\n2. Fold Assignments Test:")
fold_file = Path("main/datasets/cross_validation/fold_assignments.json")
if fold_file.exists():
    with open(fold_file) as f:
        fold_data = json.load(f)
    print(f"[PASS] Fold assignments found: {len(fold_data['folds'])} folds")
    for fold_id, fold_info in fold_data["folds"].items():
        train = len(fold_info["train"])
        val = len(fold_info["validation"])
        print(f"   {fold_id}: {train} train, {val} validation")
else:
    print(f"[FAIL] Fold assignments not found at {fold_file}")

# Test 3: Initialize FoldManager
print("\n3. FoldManager Initialization:")
try:
    fold_manager = FoldManager()
    print(f"[PASS] FoldManager initialized with {fold_manager.get_fold_count()} folds")
    print(f"   Total documents: {len(fold_manager.get_document_inventory())}")

    # Test iteration
    fold_count = 0
    for fold_id, train_docs, val_docs in fold_manager.iterate_folds():
        fold_count += 1
        if fold_count == 1:  # Show first fold details
            print(f"   Sample fold '{fold_id}': {len(train_docs)} train, {len(val_docs)} val")
        if fold_count >= 1:  # Only test first fold to avoid full document loading
            break
    print("[PASS] Successfully iterated through 1 fold (testing iteration)")
except Exception as e:
    print(f"[FAIL] FoldManager error: {e}")

# Test 4: Initialize MetricsCollector
print("\n4. MetricsCollector Test:")
try:
    output_dir = Path("main/output/cross_validation/test_task17")
    output_dir.mkdir(parents=True, exist_ok=True)

    metrics_collector = MetricsCollector(
        experiment_id="test_task17",
        output_directory=output_dir
    )
    print("[PASS] MetricsCollector initialized")

    # Test metric recording
    metrics_collector.start_fold_processing("test_fold")
    timer_key = metrics_collector.start_document_processing(
        document_id="test_doc",
        fold_id="test_fold",
        category_folder="category_3"
    )
    import time
    time.sleep(0.1)  # Small delay to simulate processing
    metrics_collector.stop_document_processing(
        timer_key=timer_key,
        success=True,
        prompt_tokens=100,
        completion_tokens=50
    )
    fold_metrics = metrics_collector.complete_fold_processing("test_fold")
    print(f"[PASS] Test metrics recorded: {fold_metrics.success_rate:.0f}% success rate")
except Exception as e:
    print(f"[FAIL] MetricsCollector error: {e}")

# Test 5: Check CrossValidationWorkflow
print("\n5. CrossValidationWorkflow Test:")
try:
    # Check if workflow can be initialized
    cv_workflow = CrossValidationWorkflow()
    print("[PASS] CrossValidationWorkflow initialized")
    print(f"   Event types: {len(cv_workflow._get_steps())}")
except Exception as e:
    print(f"[FAIL] CrossValidationWorkflow error: {e}")

# Test 6: Check statistical analysis components
print("\n6. Statistical Analysis Components:")
if CoverageAnalyzer and QualityMetrics and StatisticalAnalyzer and ResultsAggregator:
    try:
        # Initialize analyzers
        coverage_analyzer = CoverageAnalyzer()
        quality_metrics = QualityMetrics()
        statistical_analyzer = StatisticalAnalyzer()
        results_aggregator = ResultsAggregator(output_dir)

        print("[PASS] All analysis components initialized:")
        print("   - CoverageAnalyzer")
        print("   - QualityMetrics")
        print("   - StatisticalAnalyzer")
        print("   - ResultsAggregator")

        # Test statistical methods
        import numpy as np
        sample_data = np.random.randn(10)
        ci = statistical_analyzer.calculate_confidence_interval(sample_data.tolist(), "test_metric")
        print(f"[PASS] Statistical methods work: CI = [{ci.lower_bound:.2f}, {ci.upper_bound:.2f}]")
    except Exception as e:
        print(f"[FAIL] Statistical components error: {e}")
else:
    print("[WARNING] Statistical components not available for testing")

# Test 7: Check if actual cross-validation has been run
print("\n7. Previous Execution Check:")
cv_output = Path("main/output/cross_validation")
if cv_output.exists():
    experiments = [d for d in cv_output.iterdir() if d.is_dir() and not d.name.startswith("test")]
    print(f"Found {len(experiments)} experiment directories:")
    for exp in experiments[:5]:  # Show first 5
        print(f"   - {exp.name}")
        # Check for results
        results_file = exp / "aggregated_results.json"
        if results_file.exists():
            print("     [PASS] Has aggregated results")
        else:
            print("     [FAIL] No aggregated results found")
else:
    print("[FAIL] No cross-validation output directory found")

# Test 8: Check entry point script
print("\n8. Entry Point Script Test:")
entry_script = Path("run_cross_validation.py")
if entry_script.exists():
    print(f"[PASS] Entry script exists: {entry_script}")
    # Try dry run
    import subprocess
    result = subprocess.run(
        ["python", "run_cross_validation.py", "--dry-run"],
        check=False, capture_output=True,
        text=True,
        timeout=10
    )
    if result.returncode == 0:
        print("[PASS] Dry run successful")
    else:
        print(f"[FAIL] Dry run failed: {result.stderr[:200]}")
else:
    print(f"[FAIL] Entry script not found at {entry_script}")

print("\n" + "="*60)
print("TASK 17 VALIDATION SUMMARY")
print("="*60)

# Summary
print("\nCONCLUSION:")
print("Task 17 implementation appears to be architecturally complete.")
print("However, need to verify if actual cross-validation has been executed")
print("with real data and results generated.")
