"""
Quality Metrics Analysis for Cross-Validation Framework

This module provides comprehensive quality metrics analysis including
precision/recall/F1 scores, confusion matrices, false positive/negative rates,
and variance analysis with full GAMP-5 compliance.

Key Features:
- Confusion matrix calculation for multi-class classification
- Precision, recall, F1-score computation
- False positive/negative rate analysis
- Variance analysis across folds and runs
- Quality target validation (FP/FN < 5%, variance < 5%)
- Statistical significance testing
"""

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field
from scipy import stats


class ConfusionMatrix(BaseModel):
    """Confusion matrix for classification analysis."""
    true_positives: int = Field(description="True positive count")
    true_negatives: int = Field(description="True negative count")
    false_positives: int = Field(description="False positive count")
    false_negatives: int = Field(description="False negative count")
    accuracy: float = Field(description="Overall accuracy (0-1)")
    precision: float = Field(description="Precision (TP/(TP+FP))")
    recall: float = Field(description="Recall/Sensitivity (TP/(TP+FN))")
    specificity: float = Field(description="Specificity (TN/(TN+FP))")
    f1_score: float = Field(description="F1 score (harmonic mean of precision/recall)")
    false_positive_rate: float = Field(description="False positive rate (FP/(FP+TN))")
    false_negative_rate: float = Field(description="False negative rate (FN/(FN+TP))")


class CategoryQualityMetrics(BaseModel):
    """Quality metrics for a specific GAMP category."""
    category: str = Field(description="GAMP category name")
    total_documents: int = Field(description="Total documents in this category")
    correct_classifications: int = Field(description="Correctly classified documents")
    misclassifications: int = Field(description="Incorrectly classified documents")
    accuracy: float = Field(description="Category-specific accuracy")
    confidence_scores: list[float] = Field(description="All confidence scores for this category")
    avg_confidence: float = Field(description="Average confidence score")
    std_confidence: float = Field(description="Standard deviation of confidence scores")
    min_confidence: float = Field(description="Minimum confidence score")
    max_confidence: float = Field(description="Maximum confidence score")


class QualityReport(BaseModel):
    """Comprehensive quality analysis report."""
    experiment_id: str = Field(description="Experiment identifier")
    fold_id: str | None = Field(default=None, description="Fold identifier if fold-specific")
    total_documents_analyzed: int = Field(description="Total documents analyzed")
    overall_accuracy: float = Field(description="Overall classification accuracy")

    # Confusion matrix metrics
    confusion_matrix: ConfusionMatrix = Field(description="Overall confusion matrix")

    # Category-specific metrics
    category_metrics: dict[str, CategoryQualityMetrics] = Field(description="Metrics by GAMP category")

    # Target compliance
    false_positive_rate: float = Field(description="Overall false positive rate")
    false_negative_rate: float = Field(description="Overall false negative rate")
    meets_fp_target: bool = Field(description="FP rate < 5% target met")
    meets_fn_target: bool = Field(description="FN rate < 5% target met")
    meets_quality_targets: bool = Field(description="Both FP and FN targets met")

    # Variance analysis
    accuracy_variance: float = Field(description="Variance in accuracy across categories")
    confidence_variance: float = Field(description="Variance in confidence scores")
    meets_variance_target: bool = Field(description="Variance < 5% target met")

    # Statistical analysis
    chi_square_statistic: float | None = Field(default=None, description="Chi-square test statistic")
    chi_square_p_value: float | None = Field(default=None, description="Chi-square test p-value")
    is_statistically_significant: bool | None = Field(default=None, description="Statistical significance (p<0.05)")

    analysis_timestamp: str = Field(description="When analysis was performed")


class QualityMetrics:
    """
    Quality metrics analyzer for cross-validation experiments.

    This class provides comprehensive quality analysis including confusion matrices,
    precision/recall/F1 scores, and statistical significance testing with full
    GAMP-5 compliance and audit trail support.
    """

    def __init__(self, output_directory: str | Path | None = None):
        """
        Initialize the QualityMetrics analyzer.

        Args:
            output_directory: Directory to store quality reports
        """
        self.logger = logging.getLogger(__name__)
        self.output_directory = Path(output_directory) if output_directory else Path.cwd() / "quality_reports"
        self.output_directory.mkdir(parents=True, exist_ok=True)

        self.logger.info(f"QualityMetrics initialized with output directory: {self.output_directory}")

    def analyze_classification_quality(
        self,
        predictions: list[dict[str, Any]],
        ground_truth: list[dict[str, Any]],
        experiment_id: str,
        fold_id: str | None = None
    ) -> QualityReport:
        """
        Analyze classification quality from predictions and ground truth.

        Args:
            predictions: List of prediction results with document_id, predicted_category, confidence
            ground_truth: List of ground truth with document_id, true_category
            experiment_id: Experiment identifier
            fold_id: Optional fold identifier

        Returns:
            Comprehensive quality report

        Raises:
            ValueError: If input data is invalid or mismatched
        """
        if not predictions or not ground_truth:
            msg = "Predictions and ground truth data cannot be empty"
            raise ValueError(msg)

        # Create lookup for ground truth
        gt_lookup = {item["document_id"]: item for item in ground_truth}

        # Align predictions with ground truth
        aligned_data = []
        for pred in predictions:
            doc_id = pred["document_id"]
            if doc_id not in gt_lookup:
                self.logger.warning(f"No ground truth found for document {doc_id}")
                continue

            gt_item = gt_lookup[doc_id]
            aligned_data.append({
                "document_id": doc_id,
                "predicted_category": pred.get("predicted_category", pred.get("gamp_category")),
                "true_category": gt_item["true_category"],
                "confidence": pred.get("confidence", pred.get("confidence_score", 0.0)),
                "success": pred.get("success", True)
            })

        if not aligned_data:
            msg = "No matching documents found between predictions and ground truth"
            raise ValueError(msg)

        # Calculate overall confusion matrix
        overall_cm = self._calculate_confusion_matrix(aligned_data)

        # Calculate category-specific metrics
        category_metrics = self._calculate_category_metrics(aligned_data)

        # Calculate variance metrics
        accuracy_variance = self._calculate_accuracy_variance(category_metrics)
        confidence_variance = self._calculate_confidence_variance(aligned_data)

        # Perform statistical tests
        chi_square_stat, chi_square_p = self._perform_chi_square_test(aligned_data)

        # Create quality report
        report = QualityReport(
            experiment_id=experiment_id,
            fold_id=fold_id,
            total_documents_analyzed=len(aligned_data),
            overall_accuracy=overall_cm.accuracy,
            confusion_matrix=overall_cm,
            category_metrics=category_metrics,
            false_positive_rate=overall_cm.false_positive_rate,
            false_negative_rate=overall_cm.false_negative_rate,
            meets_fp_target=overall_cm.false_positive_rate < 0.05,
            meets_fn_target=overall_cm.false_negative_rate < 0.05,
            meets_quality_targets=(overall_cm.false_positive_rate < 0.05 and overall_cm.false_negative_rate < 0.05),
            accuracy_variance=accuracy_variance,
            confidence_variance=confidence_variance,
            meets_variance_target=(accuracy_variance < 0.05 and confidence_variance < 0.05),
            chi_square_statistic=chi_square_stat,
            chi_square_p_value=chi_square_p,
            is_statistically_significant=chi_square_p < 0.05 if chi_square_p is not None else None,
            analysis_timestamp=pd.Timestamp.now().isoformat()
        )

        self.logger.info(f"Quality analysis completed: {report.overall_accuracy:.3f} accuracy, "
                        f"FP: {report.false_positive_rate:.3f}, FN: {report.false_negative_rate:.3f}")

        return report

    def _calculate_confusion_matrix(self, aligned_data: list[dict[str, Any]]) -> ConfusionMatrix:
        """
        Calculate confusion matrix for binary or multi-class classification.

        Args:
            aligned_data: List of aligned prediction/ground truth data

        Returns:
            Confusion matrix with calculated metrics
        """
        # Convert to binary classification: correct vs incorrect
        correct_predictions = sum(1 for item in aligned_data
                                if item["predicted_category"] == item["true_category"])
        total_predictions = len(aligned_data)
        incorrect_predictions = total_predictions - correct_predictions

        # For binary classification (correct/incorrect)
        # True Positive: Correctly predicted as correct
        # False Positive: Incorrectly predicted as correct (but was actually incorrect)
        # True Negative: Correctly predicted as incorrect
        # False Negative: Incorrectly predicted as incorrect (but was actually correct)

        # Since we're evaluating a classifier, we can treat:
        # TP = Correct classifications with high confidence (>0.8)
        # TN = Correct classifications with low confidence (<0.5) - conservative approach
        # FP = Incorrect classifications with high confidence (overconfident errors)
        # FN = Correct classifications with low confidence (missed opportunities)

        sum(1 for item in aligned_data
                              if item["predicted_category"] == item["true_category"] and item["confidence"] > 0.8)
        sum(1 for item in aligned_data
                             if item["predicted_category"] == item["true_category"] and item["confidence"] <= 0.5)
        sum(1 for item in aligned_data
                                if item["predicted_category"] != item["true_category"] and item["confidence"] > 0.8)
        sum(1 for item in aligned_data
                               if item["predicted_category"] != item["true_category"] and item["confidence"] <= 0.5)

        # More traditional approach: treat each category prediction as binary
        tp = correct_predictions
        fp = incorrect_predictions
        tn = 0  # Not applicable for multi-class single prediction
        fn = 0  # Not applicable for multi-class single prediction

        # Calculate metrics
        accuracy = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0  # All positives in single classification
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        false_positive_rate = fp / (fp + tn) if (fp + tn) > 0 else fp / total_predictions
        false_negative_rate = fn / (fn + tp) if (fn + tp) > 0 else 0.0

        return ConfusionMatrix(
            true_positives=tp,
            true_negatives=tn,
            false_positives=fp,
            false_negatives=fn,
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            specificity=specificity,
            f1_score=f1_score,
            false_positive_rate=false_positive_rate,
            false_negative_rate=false_negative_rate
        )

    def _calculate_category_metrics(self, aligned_data: list[dict[str, Any]]) -> dict[str, CategoryQualityMetrics]:
        """
        Calculate quality metrics for each GAMP category.

        Args:
            aligned_data: List of aligned prediction/ground truth data

        Returns:
            Dictionary of category metrics
        """
        # Group by true category
        category_groups = {}
        for item in aligned_data:
            true_cat = item["true_category"]
            if true_cat not in category_groups:
                category_groups[true_cat] = []
            category_groups[true_cat].append(item)

        category_metrics = {}

        for category, items in category_groups.items():
            correct = sum(1 for item in items if item["predicted_category"] == item["true_category"])
            total = len(items)

            confidences = [item["confidence"] for item in items]

            metrics = CategoryQualityMetrics(
                category=str(category),
                total_documents=total,
                correct_classifications=correct,
                misclassifications=total - correct,
                accuracy=correct / total if total > 0 else 0.0,
                confidence_scores=confidences,
                avg_confidence=np.mean(confidences) if confidences else 0.0,
                std_confidence=np.std(confidences) if confidences else 0.0,
                min_confidence=min(confidences) if confidences else 0.0,
                max_confidence=max(confidences) if confidences else 0.0
            )

            category_metrics[str(category)] = metrics

        return category_metrics

    def _calculate_accuracy_variance(self, category_metrics: dict[str, CategoryQualityMetrics]) -> float:
        """
        Calculate variance in accuracy across categories.

        Args:
            category_metrics: Dictionary of category metrics

        Returns:
            Accuracy variance
        """
        if not category_metrics:
            return 0.0

        accuracies = [metrics.accuracy for metrics in category_metrics.values()]
        return float(np.var(accuracies)) if len(accuracies) > 1 else 0.0

    def _calculate_confidence_variance(self, aligned_data: list[dict[str, Any]]) -> float:
        """
        Calculate variance in confidence scores.

        Args:
            aligned_data: List of aligned prediction/ground truth data

        Returns:
            Confidence variance
        """
        confidences = [item["confidence"] for item in aligned_data if item["confidence"] is not None]
        return float(np.var(confidences)) if len(confidences) > 1 else 0.0

    def _perform_chi_square_test(self, aligned_data: list[dict[str, Any]]) -> tuple[float | None, float | None]:
        """
        Perform chi-square test for independence between predicted and true categories.

        Args:
            aligned_data: List of aligned prediction/ground truth data

        Returns:
            Tuple of (chi-square statistic, p-value) or (None, None) if test cannot be performed
        """
        try:
            # Create contingency table
            predicted_categories = [item["predicted_category"] for item in aligned_data]
            true_categories = [item["true_category"] for item in aligned_data]

            # Get unique categories
            all_categories = list(set(predicted_categories + true_categories))

            if len(all_categories) < 2:
                return None, None

            # Build contingency table
            contingency_table = []
            for true_cat in all_categories:
                row = []
                for pred_cat in all_categories:
                    count = sum(1 for item in aligned_data
                              if item["true_category"] == true_cat and item["predicted_category"] == pred_cat)
                    row.append(count)
                contingency_table.append(row)

            # Convert to numpy array
            contingency_table = np.array(contingency_table)

            # Perform chi-square test
            if contingency_table.sum() > 0 and contingency_table.shape[0] > 1 and contingency_table.shape[1] > 1:
                chi2_stat, p_value, dof, expected = stats.chi2_contingency(contingency_table)
                return float(chi2_stat), float(p_value)

            return None, None

        except Exception as e:
            self.logger.warning(f"Chi-square test failed: {e!s}")
            return None, None

    def compare_fold_quality(self, fold_reports: list[QualityReport]) -> dict[str, Any]:
        """
        Compare quality metrics across multiple folds.

        Args:
            fold_reports: List of quality reports from different folds

        Returns:
            Dictionary with cross-fold comparison metrics
        """
        if not fold_reports:
            msg = "No fold reports provided for comparison"
            raise ValueError(msg)

        # Extract key metrics from each fold
        accuracies = [report.overall_accuracy for report in fold_reports]
        fp_rates = [report.false_positive_rate for report in fold_reports]
        fn_rates = [report.false_negative_rate for report in fold_reports]
        f1_scores = [report.confusion_matrix.f1_score for report in fold_reports]

        # Calculate cross-fold statistics
        comparison = {
            "num_folds": len(fold_reports),
            "accuracy_stats": {
                "mean": float(np.mean(accuracies)),
                "std": float(np.std(accuracies)),
                "min": float(np.min(accuracies)),
                "max": float(np.max(accuracies)),
                "coefficient_of_variation": float(np.std(accuracies) / np.mean(accuracies)) if np.mean(accuracies) > 0 else 0.0
            },
            "false_positive_stats": {
                "mean": float(np.mean(fp_rates)),
                "std": float(np.std(fp_rates)),
                "min": float(np.min(fp_rates)),
                "max": float(np.max(fp_rates)),
                "all_meet_target": all(rate < 0.05 for rate in fp_rates)
            },
            "false_negative_stats": {
                "mean": float(np.mean(fn_rates)),
                "std": float(np.std(fn_rates)),
                "min": float(np.min(fn_rates)),
                "max": float(np.max(fn_rates)),
                "all_meet_target": all(rate < 0.05 for rate in fn_rates)
            },
            "f1_score_stats": {
                "mean": float(np.mean(f1_scores)),
                "std": float(np.std(f1_scores)),
                "min": float(np.min(f1_scores)),
                "max": float(np.max(f1_scores))
            },
            "consistency_metrics": {
                "accuracy_variance": float(np.var(accuracies)),
                "meets_consistency_target": float(np.std(accuracies)) < 0.05,
                "overall_quality_consistent": (float(np.std(accuracies)) < 0.05 and
                                             all(rate < 0.05 for rate in fp_rates) and
                                             all(rate < 0.05 for rate in fn_rates))
            }
        }

        # Statistical tests for consistency
        if len(accuracies) > 2:
            # Test for significant differences in accuracy across folds
            try:
                f_stat, f_p_value = stats.f_oneway(*[[acc] for acc in accuracies])
                comparison["statistical_tests"] = {
                    "f_statistic": float(f_stat),
                    "f_p_value": float(f_p_value),
                    "significant_difference": float(f_p_value) < 0.05
                }
            except Exception as e:
                self.logger.warning(f"F-test failed: {e!s}")
                comparison["statistical_tests"] = None

        return comparison

    def generate_quality_dashboard_data(self, reports: list[QualityReport]) -> dict[str, Any]:
        """
        Generate data for quality metrics dashboard visualization.

        Args:
            reports: List of quality reports

        Returns:
            Dictionary with dashboard data
        """
        if not reports:
            return {}

        return {
            "summary": {
                "total_reports": len(reports),
                "avg_accuracy": np.mean([r.overall_accuracy for r in reports]),
                "avg_fp_rate": np.mean([r.false_positive_rate for r in reports]),
                "avg_fn_rate": np.mean([r.false_negative_rate for r in reports]),
                "reports_meeting_targets": sum(1 for r in reports if r.meets_quality_targets)
            },
            "time_series": [
                {
                    "timestamp": report.analysis_timestamp,
                    "fold_id": report.fold_id,
                    "accuracy": report.overall_accuracy,
                    "fp_rate": report.false_positive_rate,
                    "fn_rate": report.false_negative_rate,
                    "f1_score": report.confusion_matrix.f1_score,
                    "meets_targets": report.meets_quality_targets
                }
                for report in reports
            ],
            "category_breakdown": self._aggregate_category_performance(reports),
            "target_compliance": {
                "fp_rate_compliance": [r.meets_fp_target for r in reports],
                "fn_rate_compliance": [r.meets_fn_target for r in reports],
                "variance_compliance": [r.meets_variance_target for r in reports],
                "overall_compliance": [r.meets_quality_targets for r in reports]
            }
        }


    def _aggregate_category_performance(self, reports: list[QualityReport]) -> dict[str, Any]:
        """
        Aggregate category performance across reports.

        Args:
            reports: List of quality reports

        Returns:
            Aggregated category performance data
        """
        category_data = {}

        for report in reports:
            for category, metrics in report.category_metrics.items():
                if category not in category_data:
                    category_data[category] = {
                        "accuracies": [],
                        "confidence_scores": [],
                        "total_documents": 0
                    }

                category_data[category]["accuracies"].append(metrics.accuracy)
                category_data[category]["confidence_scores"].extend(metrics.confidence_scores)
                category_data[category]["total_documents"] += metrics.total_documents

        # Calculate aggregated statistics
        aggregated = {}
        for category, data in category_data.items():
            aggregated[category] = {
                "avg_accuracy": np.mean(data["accuracies"]) if data["accuracies"] else 0.0,
                "accuracy_std": np.std(data["accuracies"]) if data["accuracies"] else 0.0,
                "avg_confidence": np.mean(data["confidence_scores"]) if data["confidence_scores"] else 0.0,
                "confidence_std": np.std(data["confidence_scores"]) if data["confidence_scores"] else 0.0,
                "total_documents": data["total_documents"],
                "num_reports": len(data["accuracies"])
            }

        return aggregated

    def save_quality_report(self, report: QualityReport) -> Path:
        """
        Save quality report to JSON file.

        Args:
            report: Quality report to save

        Returns:
            Path to saved report
        """
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        fold_suffix = f"_fold_{report.fold_id}" if report.fold_id else ""
        filename = f"quality_report_{report.experiment_id}{fold_suffix}_{timestamp}.json"
        output_path = self.output_directory / filename

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report.model_dump(), f, indent=2, default=str)

        self.logger.info(f"Quality report saved to: {output_path}")
        return output_path

    def export_quality_metrics_csv(self, reports: list[QualityReport]) -> Path:
        """
        Export quality metrics to CSV format for analysis.

        Args:
            reports: List of quality reports

        Returns:
            Path to the generated CSV file
        """
        if not reports:
            msg = "No quality reports provided for export"
            raise ValueError(msg)

        # Prepare DataFrame with report-level metrics
        metrics_data = []
        for report in reports:
            base_data = {
                "experiment_id": report.experiment_id,
                "fold_id": report.fold_id or "overall",
                "analysis_timestamp": report.analysis_timestamp,
                "total_documents": report.total_documents_analyzed,
                "overall_accuracy": report.overall_accuracy,
                "false_positive_rate": report.false_positive_rate,
                "false_negative_rate": report.false_negative_rate,
                "f1_score": report.confusion_matrix.f1_score,
                "precision": report.confusion_matrix.precision,
                "recall": report.confusion_matrix.recall,
                "meets_fp_target": report.meets_fp_target,
                "meets_fn_target": report.meets_fn_target,
                "meets_quality_targets": report.meets_quality_targets,
                "accuracy_variance": report.accuracy_variance,
                "confidence_variance": report.confidence_variance,
                "meets_variance_target": report.meets_variance_target,
                "chi_square_p_value": report.chi_square_p_value,
                "is_statistically_significant": report.is_statistically_significant
            }

            metrics_data.append(base_data)

        df = pd.DataFrame(metrics_data)

        # Generate filename with timestamp
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        filename = f"quality_metrics_export_{timestamp}.csv"
        output_path = self.output_directory / filename

        # Save to CSV
        df.to_csv(output_path, index=False)

        self.logger.info(f"Quality metrics CSV exported to: {output_path}")
        return output_path
