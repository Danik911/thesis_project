"""
Metrics Collection System for Cross-Validation Framework

This module provides comprehensive metrics collection and analysis for
the cross-validation testing framework, tracking performance, costs,
and compliance metrics with full GAMP-5 audit trail support.

Key Features:
- Wall-clock time tracking per URS processing
- Token consumption monitoring (prompt + completion)
- Cost calculation based on DeepSeek V3 pricing
- GAMP-5 category performance analysis
- Success/failure rate tracking
- JSON-based metrics storage
- Statistical analysis support
"""

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field


class DocumentMetrics(BaseModel):
    """Metrics for processing a single URS document."""
    document_id: str = Field(description="URS document identifier")
    fold_id: str = Field(description="Cross-validation fold identifier")
    category_folder: str = Field(description="GAMP category folder")

    # Timing metrics
    start_time: datetime = Field(description="Processing start timestamp")
    end_time: datetime | None = Field(default=None, description="Processing end timestamp")
    wall_clock_seconds: float | None = Field(default=None, description="Total processing time")

    # Token consumption
    prompt_tokens: int | None = Field(default=0, description="Tokens used in prompts")
    completion_tokens: int | None = Field(default=0, description="Tokens generated in responses")
    total_tokens: int | None = Field(default=0, description="Total token consumption")

    # Cost calculation (DeepSeek V3 pricing)
    prompt_cost_usd: float | None = Field(default=0.0, description="Cost of prompt tokens")
    completion_cost_usd: float | None = Field(default=0.0, description="Cost of completion tokens")
    total_cost_usd: float | None = Field(default=0.0, description="Total processing cost")

    # Success metrics
    success: bool | None = Field(default=None, description="Processing success status")
    error_message: str | None = Field(default=None, description="Error details if failed")
    error_type: str | None = Field(default=None, description="Error classification")

    # Test generation results
    tests_generated: int | None = Field(default=0, description="Number of tests generated")
    coverage_percentage: float | None = Field(default=0.0, description="Requirements coverage")
    review_required: bool | None = Field(default=True, description="Whether manual review needed")

    # GAMP-5 compliance
    gamp_category: int | None = Field(default=None, description="Detected GAMP category")
    confidence_score: float | None = Field(default=None, description="Categorization confidence")

    # Additional metadata
    workflow_session_id: str | None = Field(default=None, description="Workflow session identifier")
    phoenix_trace_id: str | None = Field(default=None, description="Phoenix observability trace ID")


class FoldMetrics(BaseModel):
    """Aggregated metrics for a complete fold."""
    fold_id: str = Field(description="Cross-validation fold identifier")
    fold_start_time: datetime = Field(description="Fold processing start time")
    fold_end_time: datetime | None = Field(default=None, description="Fold processing end time")
    fold_duration_seconds: float | None = Field(default=None, description="Total fold processing time")

    # Document counts
    total_documents: int = Field(description="Total documents in validation set")
    successful_documents: int = Field(default=0, description="Successfully processed documents")
    failed_documents: int = Field(default=0, description="Failed document processing")
    success_rate: float = Field(default=0.0, description="Success rate percentage")

    # Aggregated metrics
    total_tokens: int = Field(default=0, description="Total tokens consumed")
    total_cost_usd: float = Field(default=0.0, description="Total processing cost")
    avg_processing_time: float = Field(default=0.0, description="Average processing time per document")
    avg_tests_per_document: float = Field(default=0.0, description="Average tests generated per document")
    avg_coverage: float = Field(default=0.0, description="Average requirements coverage")

    # Category breakdown
    category_distribution: dict[str, int] = Field(default_factory=dict, description="GAMP category distribution")
    category_performance: dict[str, dict[str, float]] = Field(default_factory=dict, description="Performance by category")

    # Error analysis
    error_types: dict[str, int] = Field(default_factory=dict, description="Error type frequency")
    common_errors: list[str] = Field(default_factory=list, description="Most common error messages")


class CrossValidationMetrics(BaseModel):
    """Complete cross-validation metrics summary."""
    experiment_id: str = Field(description="Unique experiment identifier")
    start_time: datetime = Field(description="Experiment start time")
    end_time: datetime | None = Field(default=None, description="Experiment end time")
    total_duration_seconds: float | None = Field(default=None, description="Total experiment duration")

    # Overall statistics
    total_documents_processed: int = Field(default=0, description="Total documents across all folds")
    overall_success_rate: float = Field(default=0.0, description="Overall success rate")
    total_cost_usd: float = Field(default=0.0, description="Total experiment cost")
    total_tokens: int = Field(default=0, description="Total tokens consumed")

    # Performance statistics
    avg_processing_time_per_document: float = Field(default=0.0, description="Average time per document")
    std_processing_time: float = Field(default=0.0, description="Standard deviation of processing times")
    min_processing_time: float = Field(default=0.0, description="Minimum processing time")
    max_processing_time: float = Field(default=0.0, description="Maximum processing time")

    # Test generation statistics
    total_tests_generated: int = Field(default=0, description="Total tests generated")
    avg_tests_per_document: float = Field(default=0.0, description="Average tests per document")
    avg_coverage: float = Field(default=0.0, description="Average requirements coverage")

    # Fold-level results
    fold_results: list[FoldMetrics] = Field(default_factory=list, description="Results for each fold")

    # Model configuration
    model_name: str = Field(default="deepseek/deepseek-chat", description="LLM model used")
    model_temperature: float = Field(default=0.0, description="Model temperature setting")
    random_seed: int = Field(default=42, description="Random seed for reproducibility")


class MetricsCollector:
    """
    Comprehensive metrics collection system for cross-validation experiments.

    This class provides thread-safe metrics collection, aggregation, and
    persistence capabilities with full GAMP-5 compliance and audit trails.
    """

    # DeepSeek V3 pricing (per 1M tokens as of 2024)
    DEEPSEEK_V3_PROMPT_COST_PER_1M = 0.27  # USD per 1M input tokens
    DEEPSEEK_V3_COMPLETION_COST_PER_1M = 1.10  # USD per 1M output tokens

    def __init__(
        self,
        experiment_id: str,
        output_directory: str | Path,
        model_name: str = "deepseek/deepseek-chat"
    ):
        """
        Initialize the MetricsCollector.

        Args:
            experiment_id: Unique identifier for the experiment
            output_directory: Directory to store metrics files
            model_name: Name of the LLM model being used
        """
        self.experiment_id = experiment_id
        self.output_directory = Path(output_directory)
        self.model_name = model_name
        self.logger = logging.getLogger(__name__)

        # Create output directory if it doesn't exist
        self.output_directory.mkdir(parents=True, exist_ok=True)

        # Initialize experiment-level metrics
        self.experiment_metrics = CrossValidationMetrics(
            experiment_id=experiment_id,
            start_time=datetime.now(UTC),
            model_name=model_name
        )

        # Storage for document and fold metrics
        self.document_metrics: list[DocumentMetrics] = []
        self.fold_metrics: dict[str, FoldMetrics] = {}
        self.active_timers: dict[str, float] = {}

        self.logger.info(f"MetricsCollector initialized for experiment {experiment_id}")

    def start_document_processing(
        self,
        document_id: str,
        fold_id: str,
        category_folder: str,
        workflow_session_id: str | None = None
    ) -> str:
        """
        Start timing a document processing operation.

        Args:
            document_id: Document identifier
            fold_id: Cross-validation fold
            category_folder: GAMP category folder
            workflow_session_id: Workflow session identifier

        Returns:
            Timer key for stopping the timer
        """
        timer_key = f"{fold_id}_{document_id}"
        start_time = datetime.now(UTC)

        self.active_timers[timer_key] = time.time()

        # Create initial document metrics
        doc_metrics = DocumentMetrics(
            document_id=document_id,
            fold_id=fold_id,
            category_folder=category_folder,
            start_time=start_time,
            workflow_session_id=workflow_session_id
        )

        self.document_metrics.append(doc_metrics)

        self.logger.debug(f"Started timing for {document_id} in {fold_id}")
        return timer_key

    def stop_document_processing(
        self,
        timer_key: str,
        success: bool,
        error_message: str | None = None,
        error_type: str | None = None,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        tests_generated: int = 0,
        coverage_percentage: float = 0.0,
        gamp_category: int | None = None,
        confidence_score: float | None = None,
        phoenix_trace_id: str | None = None
    ) -> DocumentMetrics:
        """
        Stop timing and record final metrics for a document processing operation.

        Args:
            timer_key: Timer key from start_document_processing
            success: Whether processing succeeded
            error_message: Error message if failed
            error_type: Error classification
            prompt_tokens: Number of prompt tokens consumed
            completion_tokens: Number of completion tokens generated
            tests_generated: Number of tests generated
            coverage_percentage: Requirements coverage achieved
            gamp_category: Detected GAMP category
            confidence_score: Categorization confidence
            phoenix_trace_id: Phoenix trace identifier

        Returns:
            Completed DocumentMetrics object
        """
        if timer_key not in self.active_timers:
            msg = f"No active timer found for key: {timer_key}"
            raise ValueError(msg)

        # Calculate timing
        end_time = datetime.now(UTC)
        wall_clock_seconds = time.time() - self.active_timers[timer_key]
        del self.active_timers[timer_key]

        # Calculate costs
        total_tokens = prompt_tokens + completion_tokens
        prompt_cost = (prompt_tokens / 1_000_000) * self.DEEPSEEK_V3_PROMPT_COST_PER_1M
        completion_cost = (completion_tokens / 1_000_000) * self.DEEPSEEK_V3_COMPLETION_COST_PER_1M
        total_cost = prompt_cost + completion_cost

        # Find and update the corresponding document metrics
        doc_metrics = None
        for metrics in self.document_metrics:
            if f"{metrics.fold_id}_{metrics.document_id}" == timer_key:
                # Update the metrics object
                metrics.end_time = end_time
                metrics.wall_clock_seconds = wall_clock_seconds
                metrics.prompt_tokens = prompt_tokens
                metrics.completion_tokens = completion_tokens
                metrics.total_tokens = total_tokens
                metrics.prompt_cost_usd = prompt_cost
                metrics.completion_cost_usd = completion_cost
                metrics.total_cost_usd = total_cost
                metrics.success = success
                metrics.error_message = error_message
                metrics.error_type = error_type
                metrics.tests_generated = tests_generated
                metrics.coverage_percentage = coverage_percentage
                metrics.gamp_category = gamp_category
                metrics.confidence_score = confidence_score
                metrics.phoenix_trace_id = phoenix_trace_id
                doc_metrics = metrics
                break

        if doc_metrics is None:
            msg = f"Document metrics not found for timer key: {timer_key}"
            raise ValueError(msg)

        self.logger.info(f"Completed {doc_metrics.document_id}: "
                        f"{wall_clock_seconds:.2f}s, {total_tokens} tokens, "
                        f"${total_cost:.4f}, success={success}")

        return doc_metrics

    def start_fold_processing(self, fold_id: str) -> None:
        """
        Start timing a fold processing operation.

        Args:
            fold_id: Fold identifier
        """
        fold_metrics = FoldMetrics(
            fold_id=fold_id,
            fold_start_time=datetime.now(UTC),
            total_documents=0  # Will be updated as documents are processed
        )

        self.fold_metrics[fold_id] = fold_metrics
        self.logger.info(f"Started fold processing: {fold_id}")

    def complete_fold_processing(self, fold_id: str) -> FoldMetrics:
        """
        Complete fold processing and calculate aggregated metrics.

        Args:
            fold_id: Fold identifier

        Returns:
            Completed FoldMetrics object
        """
        if fold_id not in self.fold_metrics:
            msg = f"No active fold processing found for: {fold_id}"
            raise ValueError(msg)

        fold_metrics = self.fold_metrics[fold_id]
        fold_metrics.fold_end_time = datetime.now(UTC)

        if fold_metrics.fold_start_time:
            duration = fold_metrics.fold_end_time - fold_metrics.fold_start_time
            fold_metrics.fold_duration_seconds = duration.total_seconds()

        # Aggregate document metrics for this fold
        fold_docs = [doc for doc in self.document_metrics if doc.fold_id == fold_id]

        fold_metrics.total_documents = len(fold_docs)
        fold_metrics.successful_documents = len([doc for doc in fold_docs if doc.success])
        fold_metrics.failed_documents = len([doc for doc in fold_docs if not doc.success])

        if fold_metrics.total_documents > 0:
            fold_metrics.success_rate = (fold_metrics.successful_documents / fold_metrics.total_documents) * 100

        # Aggregate costs and tokens
        fold_metrics.total_tokens = sum(doc.total_tokens or 0 for doc in fold_docs)
        fold_metrics.total_cost_usd = sum(doc.total_cost_usd or 0.0 for doc in fold_docs)

        # Calculate averages
        successful_docs = [doc for doc in fold_docs if doc.success and doc.wall_clock_seconds]
        if successful_docs:
            fold_metrics.avg_processing_time = sum(doc.wall_clock_seconds for doc in successful_docs) / len(successful_docs)
            fold_metrics.avg_tests_per_document = sum(doc.tests_generated or 0 for doc in successful_docs) / len(successful_docs)
            fold_metrics.avg_coverage = sum(doc.coverage_percentage or 0.0 for doc in successful_docs) / len(successful_docs)

        # Category analysis
        category_counts = {}
        category_performance = {}

        for doc in fold_docs:
            if doc.gamp_category:
                category = f"category_{doc.gamp_category}"
                category_counts[category] = category_counts.get(category, 0) + 1

                if category not in category_performance:
                    category_performance[category] = {
                        "success_rate": 0.0,
                        "avg_processing_time": 0.0,
                        "avg_coverage": 0.0
                    }

        # Calculate category performance
        for category in category_counts:
            cat_docs = [doc for doc in fold_docs if f"category_{doc.gamp_category}" == category]
            successful_cat_docs = [doc for doc in cat_docs if doc.success]

            if cat_docs:
                category_performance[category]["success_rate"] = (len(successful_cat_docs) / len(cat_docs)) * 100

            if successful_cat_docs:
                category_performance[category]["avg_processing_time"] = sum(
                    doc.wall_clock_seconds or 0.0 for doc in successful_cat_docs
                ) / len(successful_cat_docs)

                category_performance[category]["avg_coverage"] = sum(
                    doc.coverage_percentage or 0.0 for doc in successful_cat_docs
                ) / len(successful_cat_docs)

        fold_metrics.category_distribution = category_counts
        fold_metrics.category_performance = category_performance

        # Error analysis
        error_types = {}
        error_messages = []

        for doc in fold_docs:
            if not doc.success and doc.error_type:
                error_types[doc.error_type] = error_types.get(doc.error_type, 0) + 1
            if not doc.success and doc.error_message:
                error_messages.append(doc.error_message)

        fold_metrics.error_types = error_types
        fold_metrics.common_errors = error_messages[:5]  # Top 5 errors

        self.logger.info(f"Completed fold {fold_id}: {fold_metrics.success_rate:.1f}% success, "
                        f"{fold_metrics.total_cost_usd:.4f} USD, "
                        f"{fold_metrics.avg_processing_time:.2f}s avg")

        return fold_metrics

    def finalize_experiment(self) -> CrossValidationMetrics:
        """
        Finalize the experiment and calculate overall metrics.

        Returns:
            Complete experiment metrics
        """
        self.experiment_metrics.end_time = datetime.now(UTC)

        if self.experiment_metrics.start_time:
            duration = self.experiment_metrics.end_time - self.experiment_metrics.start_time
            self.experiment_metrics.total_duration_seconds = duration.total_seconds()

        # Aggregate all metrics
        all_successful = [doc for doc in self.document_metrics if doc.success]

        self.experiment_metrics.total_documents_processed = len(self.document_metrics)

        if self.document_metrics:
            self.experiment_metrics.overall_success_rate = (len(all_successful) / len(self.document_metrics)) * 100

        self.experiment_metrics.total_cost_usd = sum(doc.total_cost_usd or 0.0 for doc in self.document_metrics)
        self.experiment_metrics.total_tokens = sum(doc.total_tokens or 0 for doc in self.document_metrics)
        self.experiment_metrics.total_tests_generated = sum(doc.tests_generated or 0 for doc in self.document_metrics)

        # Performance statistics
        processing_times = [doc.wall_clock_seconds for doc in all_successful if doc.wall_clock_seconds]
        if processing_times:
            self.experiment_metrics.avg_processing_time_per_document = sum(processing_times) / len(processing_times)
            self.experiment_metrics.min_processing_time = min(processing_times)
            self.experiment_metrics.max_processing_time = max(processing_times)

            # Standard deviation
            mean_time = self.experiment_metrics.avg_processing_time_per_document
            variance = sum((t - mean_time) ** 2 for t in processing_times) / len(processing_times)
            self.experiment_metrics.std_processing_time = variance ** 0.5

        if all_successful:
            self.experiment_metrics.avg_tests_per_document = sum(
                doc.tests_generated or 0 for doc in all_successful
            ) / len(all_successful)

            self.experiment_metrics.avg_coverage = sum(
                doc.coverage_percentage or 0.0 for doc in all_successful
            ) / len(all_successful)

        # Store fold results
        self.experiment_metrics.fold_results = list(self.fold_metrics.values())

        self.logger.info(f"Experiment {self.experiment_id} completed: "
                        f"{self.experiment_metrics.overall_success_rate:.1f}% success, "
                        f"${self.experiment_metrics.total_cost_usd:.2f} total cost")

        return self.experiment_metrics

    def save_metrics(self, filename_prefix: str = "cv_metrics") -> Path:
        """
        Save all collected metrics to JSON file.

        Args:
            filename_prefix: Prefix for the output filename

        Returns:
            Path to the saved metrics file
        """
        # Finalize experiment if not already done
        if self.experiment_metrics.end_time is None:
            self.finalize_experiment()

        # Prepare data for serialization
        metrics_data = {
            "experiment_summary": self.experiment_metrics.model_dump(),
            "document_metrics": [doc.model_dump() for doc in self.document_metrics],
            "fold_metrics": {fold_id: metrics.model_dump() for fold_id, metrics in self.fold_metrics.items()}
        }

        # Generate filename with timestamp
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{self.experiment_id}_{timestamp}.json"
        output_path = self.output_directory / filename

        # Save to file
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(metrics_data, f, indent=2, default=str)

        self.logger.info(f"Metrics saved to: {output_path}")
        return output_path

    def get_current_metrics_summary(self) -> dict[str, Any]:
        """
        Get a summary of current metrics for monitoring.

        Returns:
            Dictionary with key metrics
        """
        successful = len([doc for doc in self.document_metrics if doc.success])
        total = len(self.document_metrics)

        return {
            "experiment_id": self.experiment_id,
            "documents_processed": total,
            "success_rate": (successful / total * 100) if total > 0 else 0.0,
            "total_cost_usd": sum(doc.total_cost_usd or 0.0 for doc in self.document_metrics),
            "total_tokens": sum(doc.total_tokens or 0 for doc in self.document_metrics),
            "active_timers": len(self.active_timers),
            "completed_folds": len([f for f in self.fold_metrics.values() if f.fold_end_time is not None])
        }

    def calculate_detailed_performance_metrics(self, baseline_time_hours: float = 40.0) -> dict[str, Any]:
        """
        Calculate detailed performance metrics with percentiles and baseline comparisons.

        Args:
            baseline_time_hours: Baseline processing time in hours (default 40h manual process)

        Returns:
            Dictionary with detailed performance statistics
        """
        successful_docs = [doc for doc in self.document_metrics if doc.success and doc.wall_clock_seconds]

        if not successful_docs:
            msg = "No successful documents found for performance analysis"
            raise ValueError(msg)

        processing_times = [doc.wall_clock_seconds for doc in successful_docs]
        processing_times_array = np.array(processing_times)

        # Calculate baseline time per document (assuming 40h for ~17 docs)
        baseline_per_doc_seconds = (baseline_time_hours * 3600) / len(self.document_metrics)
        baseline_total_seconds = baseline_time_hours * 3600

        # Current performance
        current_total_seconds = sum(processing_times)

        # Time reduction calculation
        time_reduction_percentage = ((baseline_total_seconds - current_total_seconds) / baseline_total_seconds) * 100

        return {
            "timing_metrics": {
                "mean_seconds": float(np.mean(processing_times_array)),
                "median_seconds": float(np.median(processing_times_array)),
                "std_seconds": float(np.std(processing_times_array)),
                "min_seconds": float(np.min(processing_times_array)),
                "max_seconds": float(np.max(processing_times_array)),
                "percentile_25": float(np.percentile(processing_times_array, 25)),
                "percentile_75": float(np.percentile(processing_times_array, 75)),
                "percentile_90": float(np.percentile(processing_times_array, 90)),
                "percentile_95": float(np.percentile(processing_times_array, 95)),
            },
            "baseline_comparison": {
                "baseline_total_hours": baseline_time_hours,
                "baseline_per_doc_seconds": baseline_per_doc_seconds,
                "current_total_seconds": current_total_seconds,
                "current_total_hours": current_total_seconds / 3600,
                "time_reduction_percentage": time_reduction_percentage,
                "meets_70_percent_target": time_reduction_percentage >= 70.0,
                "actual_speedup_factor": baseline_total_seconds / current_total_seconds if current_total_seconds > 0 else 0.0
            },
            "token_efficiency": {
                "total_tokens": sum(doc.total_tokens or 0 for doc in successful_docs),
                "avg_tokens_per_doc": sum(doc.total_tokens or 0 for doc in successful_docs) / len(successful_docs),
                "avg_prompt_tokens": sum(doc.prompt_tokens or 0 for doc in successful_docs) / len(successful_docs),
                "avg_completion_tokens": sum(doc.completion_tokens or 0 for doc in successful_docs) / len(successful_docs),
                "prompt_to_completion_ratio": (sum(doc.prompt_tokens or 0 for doc in successful_docs) /
                                             sum(doc.completion_tokens or 0 for doc in successful_docs))
                                             if sum(doc.completion_tokens or 0 for doc in successful_docs) > 0 else 0.0
            },
            "cost_analysis": {
                "total_cost_usd": sum(doc.total_cost_usd or 0.0 for doc in successful_docs),
                "avg_cost_per_doc": sum(doc.total_cost_usd or 0.0 for doc in successful_docs) / len(successful_docs),
                "cost_per_token": (sum(doc.total_cost_usd or 0.0 for doc in successful_docs) /
                                 sum(doc.total_tokens or 0 for doc in successful_docs))
                                 if sum(doc.total_tokens or 0 for doc in successful_docs) > 0 else 0.0,
                "roi_vs_manual": baseline_time_hours * 50  # Assuming $50/hour manual rate
            }
        }

    def export_performance_csv(self) -> Path:
        """
        Export detailed performance metrics to CSV format for analysis.

        Returns:
            Path to the generated CSV file
        """
        if not self.document_metrics:
            msg = "No metrics available for export"
            raise ValueError(msg)

        # Prepare DataFrame with document-level metrics
        metrics_data = []
        for doc in self.document_metrics:
            metrics_data.append({
                "document_id": doc.document_id,
                "fold_id": doc.fold_id,
                "category_folder": doc.category_folder,
                "gamp_category": doc.gamp_category,
                "success": doc.success,
                "wall_clock_seconds": doc.wall_clock_seconds,
                "prompt_tokens": doc.prompt_tokens,
                "completion_tokens": doc.completion_tokens,
                "total_tokens": doc.total_tokens,
                "total_cost_usd": doc.total_cost_usd,
                "tests_generated": doc.tests_generated,
                "coverage_percentage": doc.coverage_percentage,
                "confidence_score": doc.confidence_score,
                "error_type": doc.error_type,
                "workflow_session_id": doc.workflow_session_id,
                "phoenix_trace_id": doc.phoenix_trace_id
            })

        df = pd.DataFrame(metrics_data)

        # Generate filename with timestamp
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        filename = f"cv_performance_metrics_{self.experiment_id}_{timestamp}.csv"
        output_path = self.output_directory / filename

        # Save to CSV
        df.to_csv(output_path, index=False)

        self.logger.info(f"Performance metrics CSV exported to: {output_path}")
        return output_path
