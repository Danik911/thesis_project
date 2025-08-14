#!/usr/bin/env python3
"""
Task 16 Dataset Comprehensive Validation Test
Validates all dataset components and cross-validation integration
"""

import csv
import json
import os
import statistics
import sys
from pathlib import Path
from typing import Any

# Add main source to path for imports
sys.path.append(str(Path(__file__).parent / "main" / "src"))

def test_dataset_loading() -> dict[str, Any]:
    """Test basic dataset loading functionality."""
    results = {
        "test_name": "Dataset Loading",
        "passed": True,
        "errors": [],
        "details": {}
    }

    try:
        # Test metrics.csv loading
        metrics_file = Path("datasets/metrics/metrics.csv")
        if not metrics_file.exists():
            results["errors"].append("metrics.csv not found")
            results["passed"] = False
            return results

        with open(metrics_file, encoding="utf-8") as f:
            csv_reader = csv.DictReader(f)
            metrics_data = list(csv_reader)

        results["details"]["metrics_count"] = len(metrics_data)

        # Validate all required columns exist
        required_columns = [
            "doc_id", "file_path", "gamp_category", "total_requirements",
            "functional_requirements", "performance_requirements", "regulatory_requirements",
            "integration_requirements", "readability_score", "integration_density",
            "dependency_density", "ambiguity_rate", "custom_rate", "composite_complexity_score"
        ]

        if metrics_data:
            missing_columns = [col for col in required_columns if col not in metrics_data[0]]
            if missing_columns:
                results["errors"].append(f"Missing columns in metrics.csv: {missing_columns}")
                results["passed"] = False

        # Test baseline_timings.csv loading
        baseline_file = Path("datasets/baselines/baseline_timings.csv")
        if not baseline_file.exists():
            results["errors"].append("baseline_timings.csv not found")
            results["passed"] = False
            return results

        with open(baseline_file, encoding="utf-8") as f:
            csv_reader = csv.DictReader(f)
            baseline_data = list(csv_reader)

        results["details"]["baseline_count"] = len(baseline_data)

        # Test fold_assignments.json loading
        fold_file = Path("datasets/cross_validation/fold_assignments.json")
        if not fold_file.exists():
            results["errors"].append("fold_assignments.json not found")
            results["passed"] = False
            return results

        with open(fold_file, encoding="utf-8") as f:
            fold_data = json.load(f)

        results["details"]["fold_count"] = len(fold_data.get("folds", {}))

        # Test manifest loading
        manifest_file = Path("datasets/dataset_manifest.json")
        if not manifest_file.exists():
            results["errors"].append("dataset_manifest.json not found")
            results["passed"] = False
            return results

        with open(manifest_file, encoding="utf-8") as f:
            manifest_data = json.load(f)

        results["details"]["manifest_entries"] = len(manifest_data.get("documents", []))

    except Exception as e:
        results["errors"].append(f"Loading error: {e!s}")
        results["passed"] = False

    return results

def test_metrics_calculation() -> dict[str, Any]:
    """Test metrics calculation accuracy and consistency."""
    results = {
        "test_name": "Metrics Calculation",
        "passed": True,
        "errors": [],
        "details": {}
    }

    try:
        # Load metrics data
        with open("datasets/metrics/metrics.csv", encoding="utf-8") as f:
            csv_reader = csv.DictReader(f)
            metrics_data = list(csv_reader)

        # Validate numeric ranges
        for row in metrics_data:
            doc_id = row["doc_id"]

            # Check complexity score range (0.0 to 1.0)
            complexity = float(row["composite_complexity_score"])
            if not (0.0 <= complexity <= 1.0):
                results["errors"].append(f"{doc_id}: complexity score {complexity} out of range [0.0, 1.0]")
                results["passed"] = False

            # Check requirement counts are positive integers
            req_fields = ["total_requirements", "functional_requirements", "performance_requirements",
                         "regulatory_requirements", "integration_requirements"]
            for field in req_fields:
                try:
                    count = int(row[field])
                    if count < 0:
                        results["errors"].append(f"{doc_id}: {field} is negative: {count}")
                        results["passed"] = False
                except ValueError:
                    results["errors"].append(f"{doc_id}: {field} is not a valid integer: {row[field]}")
                    results["passed"] = False

            # Check rates are proportions (0.0 to 1.0)
            rate_fields = ["integration_density", "dependency_density", "ambiguity_rate", "custom_rate"]
            for field in rate_fields:
                try:
                    rate = float(row[field])
                    if not (0.0 <= rate <= 1.0):
                        results["errors"].append(f"{doc_id}: {field} rate {rate} out of range [0.0, 1.0]")
                        results["passed"] = False
                except ValueError:
                    results["errors"].append(f"{doc_id}: {field} is not a valid float: {row[field]}")
                    results["passed"] = False

        # Calculate statistics
        complexities = [float(row["composite_complexity_score"]) for row in metrics_data]
        results["details"]["complexity_stats"] = {
            "mean": statistics.mean(complexities),
            "median": statistics.median(complexities),
            "min": min(complexities),
            "max": max(complexities),
            "stdev": statistics.stdev(complexities) if len(complexities) > 1 else 0.0
        }

        # Check GAMP category distribution
        gamp_distribution = {}
        for row in metrics_data:
            gamp_cat = row["gamp_category"]
            if gamp_cat not in gamp_distribution:
                gamp_distribution[gamp_cat] = 0
            gamp_distribution[gamp_cat] += 1

        results["details"]["gamp_distribution"] = gamp_distribution

        # Verify expected GAMP categories exist
        if "3" not in gamp_distribution or "4" not in gamp_distribution or "5" not in gamp_distribution:
            results["errors"].append("Missing core GAMP categories (3, 4, 5)")
            results["passed"] = False

    except Exception as e:
        results["errors"].append(f"Metrics calculation test error: {e!s}")
        results["passed"] = False

    return results

def test_baseline_timing_estimates() -> dict[str, Any]:
    """Test baseline timing estimates for consistency and realism."""
    results = {
        "test_name": "Baseline Timing Estimates",
        "passed": True,
        "errors": [],
        "details": {}
    }

    try:
        # Load both metrics and baseline data
        with open("datasets/metrics/metrics.csv", encoding="utf-8") as f:
            csv_reader = csv.DictReader(f)
            metrics_data = {row["doc_id"]: row for row in csv_reader}

        with open("datasets/baselines/baseline_timings.csv", encoding="utf-8") as f:
            csv_reader = csv.DictReader(f)
            baseline_data = list(csv_reader)

        # Verify all documents have baseline timings
        baseline_doc_ids = {row["doc_id"] for row in baseline_data}
        metrics_doc_ids = set(metrics_data.keys())

        missing_baselines = metrics_doc_ids - baseline_doc_ids
        if missing_baselines:
            results["errors"].append(f"Missing baseline timings for: {missing_baselines}")
            results["passed"] = False

        extra_baselines = baseline_doc_ids - metrics_doc_ids
        if extra_baselines:
            results["errors"].append(f"Extra baseline timings for: {extra_baselines}")
            results["passed"] = False

        # Test timing formula consistency
        expected_formula = "10 base hours + 30 hours per complexity point"
        timing_errors = []

        for row in baseline_data:
            doc_id = row["doc_id"]
            if doc_id in metrics_data:
                complexity = float(metrics_data[doc_id]["composite_complexity_score"])
                expected_hours = 10 + (30 * complexity)
                actual_hours = float(row["estimated_baseline_hours"])

                # Allow small floating point differences
                if abs(expected_hours - actual_hours) > 0.1:
                    timing_errors.append(f"{doc_id}: expected {expected_hours:.1f}h, got {actual_hours:.1f}h")

        if timing_errors:
            results["errors"].extend(timing_errors[:5])  # Show first 5 errors
            if len(timing_errors) > 5:
                results["errors"].append(f"... and {len(timing_errors) - 5} more timing errors")
            results["passed"] = False

        # Calculate timing statistics
        timings = [float(row["estimated_baseline_hours"]) for row in baseline_data]
        results["details"]["timing_stats"] = {
            "mean": statistics.mean(timings),
            "median": statistics.median(timings),
            "min": min(timings),
            "max": max(timings),
            "stdev": statistics.stdev(timings) if len(timings) > 1 else 0.0
        }

        # Verify reasonable timing range (should be around target 40h average)
        mean_timing = statistics.mean(timings)
        if not (10 <= mean_timing <= 60):  # Reasonable bounds around 40h target
            results["errors"].append(f"Mean timing {mean_timing:.1f}h outside reasonable range [10-60h]")
            results["passed"] = False

        # Check timing method consistency
        methods = {row["estimation_method"] for row in baseline_data}
        if len(methods) > 1:
            results["errors"].append(f"Inconsistent estimation methods: {methods}")
            results["passed"] = False

        if "synthetic_complexity_based" not in methods:
            results["errors"].append("Expected 'synthetic_complexity_based' estimation method")
            results["passed"] = False

    except Exception as e:
        results["errors"].append(f"Baseline timing test error: {e!s}")
        results["passed"] = False

    return results

def test_cross_validation_integration() -> dict[str, Any]:
    """Test cross-validation fold integration and stratification."""
    results = {
        "test_name": "Cross-Validation Integration",
        "passed": True,
        "errors": [],
        "details": {}
    }

    try:
        # Load fold assignments
        with open("datasets/cross_validation/fold_assignments.json", encoding="utf-8") as f:
            fold_data = json.load(f)

        # Load metrics for stratification analysis
        with open("datasets/metrics/metrics.csv", encoding="utf-8") as f:
            csv_reader = csv.DictReader(f)
            metrics_data = {row["doc_id"]: row for row in csv_reader}

        folds = fold_data.get("folds", {})

        # Test fold structure
        if len(folds) != 5:
            results["errors"].append(f"Expected 5 folds, found {len(folds)}")
            results["passed"] = False

        # Collect all documents from folds
        all_fold_docs = set()
        fold_stats = []

        for fold_name, fold_info in folds.items():
            train_docs = fold_info.get("train_documents", [])
            test_docs = fold_info.get("test_documents", [])

            # Extract document IDs (handle both string and dict formats)
            train_ids = []
            test_ids = []

            for doc in train_docs:
                doc_id = doc.get("document_id") if isinstance(doc, dict) else doc
                if doc_id:
                    train_ids.append(doc_id)
                    all_fold_docs.add(doc_id)

            for doc in test_docs:
                doc_id = doc.get("document_id") if isinstance(doc, dict) else doc
                if doc_id:
                    test_ids.append(doc_id)
                    all_fold_docs.add(doc_id)

            # Analyze GAMP distribution in this fold
            train_gamp = [metrics_data[doc_id]["gamp_category"] for doc_id in train_ids if doc_id in metrics_data]
            test_gamp = [metrics_data[doc_id]["gamp_category"] for doc_id in test_ids if doc_id in metrics_data]

            fold_stat = {
                "fold": fold_name,
                "train_count": len(train_ids),
                "test_count": len(test_ids),
                "train_gamp_dist": {cat: train_gamp.count(cat) for cat in set(train_gamp)},
                "test_gamp_dist": {cat: test_gamp.count(cat) for cat in set(test_gamp)}
            }
            fold_stats.append(fold_stat)

        results["details"]["fold_statistics"] = fold_stats

        # Verify all documents appear in folds
        expected_docs = set(metrics_data.keys())
        missing_docs = expected_docs - all_fold_docs
        extra_docs = all_fold_docs - expected_docs

        if missing_docs:
            results["errors"].append(f"Documents missing from folds: {missing_docs}")
            results["passed"] = False

        if extra_docs:
            results["errors"].append(f"Unknown documents in folds: {extra_docs}")
            results["passed"] = False

        # Check stratification quality
        # Each fold should have reasonable GAMP distribution
        for fold_stat in fold_stats:
            gamp_categories = list(fold_stat["train_gamp_dist"].keys())
            if len(gamp_categories) < 2:  # Should have at least 2 GAMP categories per fold
                results["errors"].append(f"Fold {fold_stat['fold']} has poor GAMP stratification: {gamp_categories}")
                results["passed"] = False

        # Verify approximately equal fold sizes
        fold_sizes = [stat["train_count"] + stat["test_count"] for stat in fold_stats]
        if max(fold_sizes) - min(fold_sizes) > 2:  # Allow 2 document difference
            results["errors"].append(f"Unbalanced fold sizes: {fold_sizes}")
            results["passed"] = False

    except Exception as e:
        results["errors"].append(f"Cross-validation integration test error: {e!s}")
        results["passed"] = False

    return results

def test_gamp_stratification() -> dict[str, Any]:
    """Test GAMP category stratification and complexity distribution."""
    results = {
        "test_name": "GAMP Stratification Analysis",
        "passed": True,
        "errors": [],
        "details": {}
    }

    try:
        # Load metrics data
        with open("datasets/metrics/metrics.csv", encoding="utf-8") as f:
            csv_reader = csv.DictReader(f)
            metrics_data = list(csv_reader)

        # Analyze complexity by GAMP category
        gamp_complexity = {}
        for row in metrics_data:
            gamp_cat = row["gamp_category"]
            complexity = float(row["composite_complexity_score"])

            if gamp_cat not in gamp_complexity:
                gamp_complexity[gamp_cat] = []
            gamp_complexity[gamp_cat].append(complexity)

        # Calculate statistics per category
        category_stats = {}
        for gamp_cat, complexities in gamp_complexity.items():
            category_stats[gamp_cat] = {
                "count": len(complexities),
                "mean_complexity": statistics.mean(complexities),
                "min_complexity": min(complexities),
                "max_complexity": max(complexities),
                "stdev_complexity": statistics.stdev(complexities) if len(complexities) > 1 else 0.0
            }

        results["details"]["category_statistics"] = category_stats

        # Verify expected complexity progression: Category 3 < 4 < 5
        if "3" in category_stats and "4" in category_stats and "5" in category_stats:
            mean_3 = category_stats["3"]["mean_complexity"]
            mean_4 = category_stats["4"]["mean_complexity"]
            mean_5 = category_stats["5"]["mean_complexity"]

            if not (mean_3 < mean_4 < mean_5):
                results["errors"].append(f"Complexity progression violation: Cat3={mean_3:.3f}, Cat4={mean_4:.3f}, Cat5={mean_5:.3f}")
                results["passed"] = False

            # Check for reasonable separation between categories
            if (mean_4 - mean_3) < 0.05 or (mean_5 - mean_4) < 0.05:
                results["errors"].append("Insufficient complexity separation between GAMP categories")
                results["passed"] = False

        # Verify Category 5 documents have custom indicators
        custom_rates_cat5 = []
        for row in metrics_data:
            if row["gamp_category"] == "5":
                custom_rate = float(row["custom_rate"])
                custom_rates_cat5.append(custom_rate)

        if custom_rates_cat5:
            avg_custom_rate_cat5 = statistics.mean(custom_rates_cat5)
            if avg_custom_rate_cat5 < 0.2:  # Expect at least 20% custom indicators for Cat 5
                results["errors"].append(f"Category 5 documents have low custom rate: {avg_custom_rate_cat5:.3f}")
                results["passed"] = False

        # Check balanced dataset
        total_docs = len(metrics_data)
        results["details"]["total_documents"] = total_docs

        if total_docs < 15:
            results["errors"].append(f"Dataset too small: {total_docs} documents (minimum 15)")
            results["passed"] = False

    except Exception as e:
        results["errors"].append(f"GAMP stratification test error: {e!s}")
        results["passed"] = False

    return results

def run_all_tests() -> bool:
    """Run all validation tests and print results."""
    print("TASK 16 DATASET COMPREHENSIVE VALIDATION")
    print("=" * 50)

    tests = [
        test_dataset_loading,
        test_metrics_calculation,
        test_baseline_timing_estimates,
        test_cross_validation_integration,
        test_gamp_stratification
    ]

    all_passed = True
    test_results = []

    for test_func in tests:
        print(f"\nRunning {test_func.__name__}...")
        result = test_func()
        test_results.append(result)

        if result["passed"]:
            print(f"PASS: {result['test_name']}")
            if result["details"]:
                for key, value in result["details"].items():
                    if isinstance(value, dict):
                        print(f"      {key}: {json.dumps(value, indent=8)}")
                    else:
                        print(f"      {key}: {value}")
        else:
            print(f"FAIL: {result['test_name']}")
            all_passed = False
            for error in result["errors"]:
                print(f"      ERROR: {error}")

    print("\n" + "=" * 50)
    if all_passed:
        print("SUCCESS: All validation tests PASSED!")
        print("Dataset is ready for cross-validation testing.")
    else:
        print("FAILURE: Some validation tests FAILED!")
        print("Please address the issues above before proceeding.")

    # Save detailed results
    results_file = Path("datasets/validation_results.json")
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": "2025-08-12T12:00:00Z",
            "overall_result": "PASS" if all_passed else "FAIL",
            "test_results": test_results
        }, f, indent=2)

    print(f"\nDetailed results saved to: {results_file}")

    return all_passed

if __name__ == "__main__":
    # Change to project root directory
    os.chdir(Path(__file__).parent)

    success = run_all_tests()
    sys.exit(0 if success else 1)
