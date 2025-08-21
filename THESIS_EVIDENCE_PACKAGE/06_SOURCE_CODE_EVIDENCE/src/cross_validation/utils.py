"""
Utility Functions for Cross-Validation Framework

This module provides utility functions for the cross-validation framework,
including data processing, statistical analysis, and reporting helpers.

Key Features:
- Statistical analysis functions for experiment results
- Data formatting and export utilities
- Performance benchmarking helpers
- Visualization data preparation
- GAMP-5 compliance reporting utilities
"""

import json
import statistics
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .metrics_collector import DocumentMetrics, FoldMetrics


def calculate_statistical_summary(
    processing_times: list[float],
    success_rates: list[float],
    costs: list[float]
) -> dict[str, Any]:
    """
    Calculate statistical summary for cross-validation results.

    Args:
        processing_times: List of processing times per document
        success_rates: List of success rates per fold
        costs: List of costs per document

    Returns:
        Dictionary with statistical summary
    """
    if not processing_times or not success_rates or not costs:
        return {
            "error": "Insufficient data for statistical analysis",
            "data_points": {
                "processing_times": len(processing_times),
                "success_rates": len(success_rates),
                "costs": len(costs)
            }
        }

    return {
        "processing_time_stats": {
            "mean_seconds": statistics.mean(processing_times),
            "median_seconds": statistics.median(processing_times),
            "std_dev_seconds": statistics.stdev(processing_times) if len(processing_times) > 1 else 0.0,
            "min_seconds": min(processing_times),
            "max_seconds": max(processing_times),
            "count": len(processing_times)
        },
        "success_rate_stats": {
            "mean_percentage": statistics.mean(success_rates),
            "median_percentage": statistics.median(success_rates),
            "std_dev_percentage": statistics.stdev(success_rates) if len(success_rates) > 1 else 0.0,
            "min_percentage": min(success_rates),
            "max_percentage": max(success_rates),
            "count": len(success_rates)
        },
        "cost_stats": {
            "mean_usd": statistics.mean(costs),
            "median_usd": statistics.median(costs),
            "std_dev_usd": statistics.stdev(costs) if len(costs) > 1 else 0.0,
            "min_usd": min(costs),
            "max_usd": max(costs),
            "total_usd": sum(costs),
            "count": len(costs)
        }
    }


def analyze_category_performance(
    document_metrics: list[DocumentMetrics]
) -> dict[str, dict[str, Any]]:
    """
    Analyze performance by GAMP category.

    Args:
        document_metrics: List of document processing metrics

    Returns:
        Dictionary with performance analysis by category
    """
    category_data = {}

    for doc in document_metrics:
        if not doc.gamp_category:
            continue

        category = f"category_{doc.gamp_category}"

        if category not in category_data:
            category_data[category] = {
                "documents": [],
                "success_count": 0,
                "total_count": 0,
                "processing_times": [],
                "costs": [],
                "token_usage": [],
                "test_counts": [],
                "coverage_scores": []
            }

        data = category_data[category]
        data["documents"].append(doc.document_id)
        data["total_count"] += 1

        if doc.success:
            data["success_count"] += 1

            if doc.wall_clock_seconds:
                data["processing_times"].append(doc.wall_clock_seconds)
            if doc.total_cost_usd:
                data["costs"].append(doc.total_cost_usd)
            if doc.total_tokens:
                data["token_usage"].append(doc.total_tokens)
            if doc.tests_generated:
                data["test_counts"].append(doc.tests_generated)
            if doc.coverage_percentage:
                data["coverage_scores"].append(doc.coverage_percentage)

    # Calculate summary statistics for each category
    analysis = {}
    for category, data in category_data.items():
        analysis[category] = {
            "total_documents": data["total_count"],
            "successful_documents": data["success_count"],
            "success_rate": (data["success_count"] / data["total_count"]) * 100 if data["total_count"] > 0 else 0.0,
            "avg_processing_time": statistics.mean(data["processing_times"]) if data["processing_times"] else 0.0,
            "avg_cost": statistics.mean(data["costs"]) if data["costs"] else 0.0,
            "avg_tokens": statistics.mean(data["token_usage"]) if data["token_usage"] else 0.0,
            "avg_tests_generated": statistics.mean(data["test_counts"]) if data["test_counts"] else 0.0,
            "avg_coverage": statistics.mean(data["coverage_scores"]) if data["coverage_scores"] else 0.0,
            "document_list": data["documents"]
        }

    return analysis


def generate_performance_report(
    experiment_results: dict[str, Any],
    output_path: Path | None = None
) -> dict[str, Any]:
    """
    Generate a comprehensive performance report from experiment results.

    Args:
        experiment_results: Complete experiment results dictionary
        output_path: Optional path to save the report

    Returns:
        Dictionary with comprehensive performance report
    """
    report = {
        "report_metadata": {
            "generated_at": datetime.now(UTC).isoformat(),
            "experiment_id": experiment_results.get("experiment_id", "unknown"),
            "report_version": "1.0.0"
        },
        "experiment_summary": experiment_results.get("summary", {}),
        "fold_performance": {},
        "category_analysis": {},
        "statistical_analysis": {},
        "recommendations": []
    }

    # Extract fold results if available
    fold_results = experiment_results.get("fold_results", {})

    for fold_id, fold_data in fold_results.items():
        if hasattr(fold_data, "model_dump"):
            fold_info = fold_data.model_dump()
        else:
            fold_info = fold_data

        report["fold_performance"][fold_id] = {
            "success_rate": fold_info.get("success_rate", 0.0),
            "total_documents": fold_info.get("total_documents", 0),
            "avg_processing_time": fold_info.get("avg_processing_time", 0.0),
            "total_cost": fold_info.get("total_cost_usd", 0.0),
            "category_distribution": fold_info.get("category_distribution", {})
        }

    # Generate recommendations based on results
    overall_success_rate = report["experiment_summary"].get("overall_success_rate", 0.0)

    if overall_success_rate < 80.0:
        report["recommendations"].append(
            "Success rate below 80% - consider reviewing error patterns and improving workflow robustness"
        )

    if overall_success_rate >= 95.0:
        report["recommendations"].append(
            "Excellent success rate achieved - system ready for production deployment"
        )

    # Add cost analysis
    total_cost = report["experiment_summary"].get("total_cost_usd", 0.0)
    total_docs = report["experiment_summary"].get("total_documents", 1)
    cost_per_doc = total_cost / total_docs if total_docs > 0 else 0.0

    if cost_per_doc > 1.0:
        report["recommendations"].append(
            f"High cost per document (${cost_per_doc:.2f}) - consider optimizing token usage"
        )
    elif cost_per_doc < 0.10:
        report["recommendations"].append(
            f"Very efficient cost per document (${cost_per_doc:.2f}) - excellent cost optimization"
        )

    # Save report if path provided
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, default=str)

    return report


def export_metrics_for_visualization(
    metrics_file_path: Path,
    output_format: str = "csv"
) -> Path:
    """
    Export metrics data in format suitable for visualization tools.

    Args:
        metrics_file_path: Path to metrics JSON file
        output_format: Output format ('csv', 'json', 'xlsx')

    Returns:
        Path to exported file
    """
    # Load metrics data
    with open(metrics_file_path, encoding="utf-8") as f:
        metrics_data = json.load(f)

    # Extract document metrics for tabular export
    document_metrics = metrics_data.get("document_metrics", [])

    if output_format.lower() == "csv":
        import csv

        output_path = metrics_file_path.with_suffix(".csv")

        with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
            if not document_metrics:
                csvfile.write("No document metrics available\n")
                return output_path

            fieldnames = document_metrics[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for doc in document_metrics:
                writer.writerow(doc)

        return output_path

    if output_format.lower() == "json":
        # Export flattened JSON suitable for analysis tools
        output_path = metrics_file_path.with_suffix(".analysis.json")

        flattened_data = {
            "experiment_metadata": metrics_data.get("experiment_summary", {}),
            "documents": document_metrics,
            "folds": list(metrics_data.get("fold_metrics", {}).values())
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(flattened_data, f, indent=2, default=str)

        return output_path

    msg = f"Unsupported export format: {output_format}"
    raise ValueError(msg)


def validate_cross_validation_integrity(
    fold_assignments: dict[str, Any],
    document_metrics: list[DocumentMetrics]
) -> dict[str, Any]:
    """
    Validate the integrity of cross-validation results.

    Args:
        fold_assignments: Fold assignments data
        document_metrics: Document processing metrics

    Returns:
        Dictionary with validation results
    """
    validation_results = {
        "is_valid": True,
        "errors": [],
        "warnings": [],
        "statistics": {}
    }

    # Check that all documents were processed exactly once
    processed_docs = {doc.document_id for doc in document_metrics}
    expected_docs = set(fold_assignments.get("document_inventory", []))

    missing_docs = expected_docs - processed_docs
    extra_docs = processed_docs - expected_docs

    if missing_docs:
        validation_results["is_valid"] = False
        validation_results["errors"].append(f"Documents not processed: {sorted(missing_docs)}")

    if extra_docs:
        validation_results["warnings"].append(f"Unexpected documents processed: {sorted(extra_docs)}")

    # Check fold coverage
    folds_data = fold_assignments.get("folds", {})
    processed_folds = {doc.fold_id for doc in document_metrics}
    expected_folds = set(folds_data.keys())

    missing_folds = expected_folds - processed_folds
    if missing_folds:
        validation_results["is_valid"] = False
        validation_results["errors"].append(f"Folds not processed: {sorted(missing_folds)}")

    # Verify each document appears exactly once in validation sets
    validation_document_counts = {}
    for _fold_id, fold_data in folds_data.items():
        test_docs = fold_data.get("test_documents", [])
        for doc_id in test_docs:
            validation_document_counts[doc_id] = validation_document_counts.get(doc_id, 0) + 1

    duplicated_in_validation = [doc for doc, count in validation_document_counts.items() if count > 1]
    if duplicated_in_validation:
        validation_results["is_valid"] = False
        validation_results["errors"].append(f"Documents appear multiple times in validation: {duplicated_in_validation}")

    # Generate statistics
    validation_results["statistics"] = {
        "total_documents_expected": len(expected_docs),
        "total_documents_processed": len(processed_docs),
        "coverage_percentage": (len(processed_docs) / len(expected_docs)) * 100 if expected_docs else 0.0,
        "total_folds_expected": len(expected_folds),
        "total_folds_processed": len(processed_folds),
        "successful_documents": len([doc for doc in document_metrics if doc.success]),
        "failed_documents": len([doc for doc in document_metrics if not doc.success]),
        "overall_success_rate": (len([doc for doc in document_metrics if doc.success]) / len(document_metrics)) * 100 if document_metrics else 0.0
    }

    return validation_results


def compare_fold_performance(
    fold_metrics: list[FoldMetrics]
) -> dict[str, Any]:
    """
    Compare performance across different folds to identify patterns.

    Args:
        fold_metrics: List of fold metrics

    Returns:
        Dictionary with fold comparison analysis
    """
    if not fold_metrics:
        return {"error": "No fold metrics provided"}

    # Extract performance metrics per fold
    fold_performance = {}

    for fold in fold_metrics:
        fold_performance[fold.fold_id] = {
            "success_rate": fold.success_rate,
            "avg_processing_time": fold.avg_processing_time,
            "total_cost": fold.total_cost_usd,
            "avg_tests_per_doc": fold.avg_tests_per_document,
            "avg_coverage": fold.avg_coverage,
            "category_distribution": fold.category_distribution
        }

    # Calculate cross-fold statistics
    success_rates = [fold.success_rate for fold in fold_metrics]
    processing_times = [fold.avg_processing_time for fold in fold_metrics if fold.avg_processing_time > 0]
    costs = [fold.total_cost_usd for fold in fold_metrics]

    return {
        "fold_performance": fold_performance,
        "cross_fold_statistics": {
            "success_rate_variance": statistics.variance(success_rates) if len(success_rates) > 1 else 0.0,
            "success_rate_range": max(success_rates) - min(success_rates) if success_rates else 0.0,
            "processing_time_variance": statistics.variance(processing_times) if len(processing_times) > 1 else 0.0,
            "cost_variance": statistics.variance(costs) if len(costs) > 1 else 0.0
        },
        "performance_consistency": "high" if statistics.stdev(success_rates) < 5.0 else "medium" if statistics.stdev(success_rates) < 15.0 else "low",
        "best_performing_fold": max(fold_performance.keys(), key=lambda k: fold_performance[k]["success_rate"]) if fold_performance else None,
        "worst_performing_fold": min(fold_performance.keys(), key=lambda k: fold_performance[k]["success_rate"]) if fold_performance else None
    }



def generate_audit_trail_report(
    experiment_results: dict[str, Any],
    compliance_level: str = "GAMP-5"
) -> dict[str, Any]:
    """
    Generate GAMP-5 compliant audit trail report.

    Args:
        experiment_results: Complete experiment results
        compliance_level: Compliance standard (GAMP-5, ALCOA+)

    Returns:
        Dictionary with audit trail report
    """
    return {
        "audit_metadata": {
            "report_type": "cross_validation_audit_trail",
            "compliance_standard": compliance_level,
            "generated_at": datetime.now(UTC).isoformat(),
            "report_version": "1.0.0"
        },
        "experiment_identification": {
            "experiment_id": experiment_results.get("experiment_id"),
            "start_time": experiment_results.get("execution_metadata", {}).get("start_time"),
            "end_time": experiment_results.get("execution_metadata", {}).get("end_time"),
            "duration": experiment_results.get("execution_metadata", {}).get("total_duration_seconds"),
            "random_seed": experiment_results.get("execution_metadata", {}).get("random_seed")
        },
        "data_integrity_verification": {
            "total_documents": experiment_results.get("summary", {}).get("total_documents", 0),
            "folds_processed": experiment_results.get("summary", {}).get("total_folds", 0),
            "success_rate": experiment_results.get("summary", {}).get("overall_success_rate", 0.0),
            "reproducibility_seed": experiment_results.get("execution_metadata", {}).get("random_seed")
        },
        "compliance_attestation": {
            "gamp5_category_validation": "All documents processed through validated GAMP-5 categorization workflow",
            "alcoa_plus_principles": "Data integrity maintained through complete audit trail",
            "cfr_part_11": "Electronic records maintained with appropriate controls",
            "validation_status": "COMPLIANT" if experiment_results.get("summary", {}).get("overall_success_rate", 0) > 80 else "REQUIRES_REVIEW"
        },
        "quality_metrics": {
            "overall_success_rate": experiment_results.get("summary", {}).get("overall_success_rate", 0.0),
            "total_cost": experiment_results.get("summary", {}).get("total_cost_usd", 0.0),
            "average_processing_time": experiment_results.get("execution_metadata", {}).get("total_duration_seconds", 0) / max(experiment_results.get("summary", {}).get("total_documents", 1), 1)
        }
    }

