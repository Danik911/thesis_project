"""
Structured Logging System for Cross-Validation Framework

This module provides JSONL structured logging capabilities for cross-validation
experiments, ensuring complete traceability and reproducibility of all operations.

Key Features:
- JSONL format logging for machine readability
- Per-URS and per-fold structured logs
- Run IDs, fold indices, seeds, model versions for reproducibility
- Raw predictions, labels, and metadata capture
- GAMP-5 compliance with audit trail support
"""

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class URSProcessingLog(BaseModel):
    """Structured log entry for individual URS processing."""
    # Identifiers
    run_id: str = Field(description="Unique run identifier")
    experiment_id: str = Field(description="Experiment identifier")
    fold_id: str = Field(description="Fold identifier (e.g., 'fold_1')")
    fold_index: int = Field(description="Zero-based fold index")
    document_id: str = Field(description="URS document identifier")
    processing_timestamp: str = Field(description="ISO timestamp of processing start")

    # Configuration
    random_seed: int = Field(description="Random seed used")
    model_name: str = Field(default="deepseek/deepseek-chat", description="LLM model name")
    model_temperature: float = Field(default=0.0, description="Model temperature")
    config_snapshot: dict[str, Any] = Field(default_factory=dict, description="Configuration snapshot")

    # Processing Results
    success: bool = Field(description="Whether processing succeeded")
    processing_time_seconds: float = Field(description="Wall-clock processing time")

    # Input Data
    input_metadata: dict[str, Any] = Field(default_factory=dict, description="Input document metadata")

    # Raw Predictions
    raw_predictions: dict[str, Any] = Field(default_factory=dict, description="Raw model predictions")

    # Labels/Ground Truth (for validation documents)
    expected_gamp_category: int | None = Field(default=None, description="Expected GAMP category")
    expected_test_count: int | None = Field(default=None, description="Expected test count")

    # Metrics
    token_usage: dict[str, int] = Field(default_factory=dict, description="Token consumption details")
    cost_usd: float = Field(default=0.0, description="Processing cost")

    # Output Results
    generated_tests_count: int = Field(default=0, description="Number of tests generated")
    coverage_percentage: float = Field(default=0.0, description="Requirements coverage")
    gamp_category_detected: int | None = Field(default=None, description="Detected GAMP category")
    confidence_score: float = Field(default=0.0, description="Categorization confidence")

    # Error Information
    error_message: str | None = Field(default=None, description="Error message if failed")
    error_type: str | None = Field(default=None, description="Error type classification")
    error_traceback: str | None = Field(default=None, description="Full error traceback")

    # Compliance
    phoenix_trace_id: str | None = Field(default=None, description="Phoenix observability trace ID")
    workflow_session_id: str | None = Field(default=None, description="Workflow session identifier")


class FoldSummaryLog(BaseModel):
    """Structured log entry for fold-level summary."""
    # Identifiers
    run_id: str = Field(description="Unique run identifier")
    experiment_id: str = Field(description="Experiment identifier")
    fold_id: str = Field(description="Fold identifier")
    fold_index: int = Field(description="Zero-based fold index")
    summary_timestamp: str = Field(description="ISO timestamp of summary generation")

    # Configuration
    random_seed: int = Field(description="Random seed used")
    model_name: str = Field(default="deepseek/deepseek-chat", description="LLM model name")

    # Fold Statistics
    total_documents: int = Field(description="Total documents in validation set")
    successful_documents: int = Field(description="Successfully processed documents")
    failed_documents: int = Field(description="Failed document processing")
    success_rate_percentage: float = Field(description="Success rate percentage")

    # Performance Metrics
    total_processing_time_seconds: float = Field(description="Total fold processing time")
    average_processing_time_seconds: float = Field(description="Average processing time per document")
    total_tokens: int = Field(description="Total tokens consumed")
    total_cost_usd: float = Field(description="Total processing cost")

    # Quality Metrics
    average_tests_per_document: float = Field(description="Average tests generated per document")
    average_coverage_percentage: float = Field(description="Average requirements coverage")

    # Category Analysis
    category_distribution: dict[str, int] = Field(default_factory=dict, description="GAMP category distribution")
    category_performance: dict[str, dict[str, float]] = Field(default_factory=dict, description="Performance by category")

    # Error Analysis
    error_summary: dict[str, int] = Field(default_factory=dict, description="Error type frequency")

    # Document Lists
    successful_documents_list: list[str] = Field(default_factory=list, description="List of successful document IDs")
    failed_documents_list: list[str] = Field(default_factory=list, description="List of failed document IDs")


class StructuredLogger:
    """
    Structured logger for cross-validation experiments using JSONL format.

    This logger provides machine-readable structured logging for all
    cross-validation operations, ensuring complete traceability and
    reproducibility of experiments.
    """

    def __init__(
        self,
        experiment_id: str,
        output_directory: str | Path,
        run_id: str | None = None
    ):
        """
        Initialize the structured logger.

        Args:
            experiment_id: Unique experiment identifier
            output_directory: Directory for log files
            run_id: Unique run identifier (auto-generated if None)
        """
        self.experiment_id = experiment_id
        self.output_directory = Path(output_directory)
        self.run_id = run_id or str(uuid4())

        # Create log directory
        self.log_directory = self.output_directory / "structured_logs"
        self.log_directory.mkdir(parents=True, exist_ok=True)

        # Log file paths
        self.urs_log_path = self.log_directory / f"{experiment_id}_urs_processing.jsonl"
        self.fold_log_path = self.log_directory / f"{experiment_id}_fold_summaries.jsonl"

        # Initialize Python logger
        self.logger = logging.getLogger(f"structured_logger.{experiment_id}")
        self.logger.setLevel(logging.INFO)

        self.logger.info(f"StructuredLogger initialized for experiment {experiment_id}, run {self.run_id}")

    def log_urs_processing(
        self,
        fold_id: str,
        fold_index: int,
        document_id: str,
        success: bool,
        processing_time_seconds: float,
        random_seed: int = 42,
        model_name: str = "deepseek/deepseek-chat",
        model_temperature: float = 0.0,
        config_snapshot: dict[str, Any] | None = None,
        input_metadata: dict[str, Any] | None = None,
        raw_predictions: dict[str, Any] | None = None,
        expected_gamp_category: int | None = None,
        expected_test_count: int | None = None,
        token_usage: dict[str, int] | None = None,
        cost_usd: float = 0.0,
        generated_tests_count: int = 0,
        coverage_percentage: float = 0.0,
        gamp_category_detected: int | None = None,
        confidence_score: float = 0.0,
        error_message: str | None = None,
        error_type: str | None = None,
        error_traceback: str | None = None,
        phoenix_trace_id: str | None = None,
        workflow_session_id: str | None = None
    ) -> None:
        """
        Log individual URS processing results.

        Args:
            fold_id: Fold identifier
            fold_index: Zero-based fold index
            document_id: Document identifier
            success: Whether processing succeeded
            processing_time_seconds: Processing time
            random_seed: Random seed used
            model_name: LLM model name
            model_temperature: Model temperature
            config_snapshot: Configuration snapshot
            input_metadata: Input document metadata
            raw_predictions: Raw model predictions
            expected_gamp_category: Expected GAMP category
            expected_test_count: Expected test count
            token_usage: Token consumption details
            cost_usd: Processing cost
            generated_tests_count: Number of tests generated
            coverage_percentage: Requirements coverage
            gamp_category_detected: Detected GAMP category
            confidence_score: Categorization confidence
            error_message: Error message if failed
            error_type: Error type classification
            error_traceback: Full error traceback
            phoenix_trace_id: Phoenix trace ID
            workflow_session_id: Workflow session ID
        """
        log_entry = URSProcessingLog(
            run_id=self.run_id,
            experiment_id=self.experiment_id,
            fold_id=fold_id,
            fold_index=fold_index,
            document_id=document_id,
            processing_timestamp=datetime.now(UTC).isoformat(),
            random_seed=random_seed,
            model_name=model_name,
            model_temperature=model_temperature,
            config_snapshot=config_snapshot or {},
            success=success,
            processing_time_seconds=processing_time_seconds,
            input_metadata=input_metadata or {},
            raw_predictions=raw_predictions or {},
            expected_gamp_category=expected_gamp_category,
            expected_test_count=expected_test_count,
            token_usage=token_usage or {},
            cost_usd=cost_usd,
            generated_tests_count=generated_tests_count,
            coverage_percentage=coverage_percentage,
            gamp_category_detected=gamp_category_detected,
            confidence_score=confidence_score,
            error_message=error_message,
            error_type=error_type,
            error_traceback=error_traceback,
            phoenix_trace_id=phoenix_trace_id,
            workflow_session_id=workflow_session_id
        )

        # Write to JSONL file
        with open(self.urs_log_path, "a", encoding="utf-8") as f:
            f.write(log_entry.model_dump_json() + "\n")

        self.logger.debug(f"URS processing logged: {document_id} in {fold_id}")

    def log_fold_summary(
        self,
        fold_id: str,
        fold_index: int,
        total_documents: int,
        successful_documents: int,
        failed_documents: int,
        success_rate_percentage: float,
        total_processing_time_seconds: float,
        average_processing_time_seconds: float,
        total_tokens: int,
        total_cost_usd: float,
        average_tests_per_document: float,
        average_coverage_percentage: float,
        category_distribution: dict[str, int] | None = None,
        category_performance: dict[str, dict[str, float]] | None = None,
        error_summary: dict[str, int] | None = None,
        successful_documents_list: list[str] | None = None,
        failed_documents_list: list[str] | None = None,
        random_seed: int = 42,
        model_name: str = "deepseek/deepseek-chat"
    ) -> None:
        """
        Log fold-level summary results.

        Args:
            fold_id: Fold identifier
            fold_index: Zero-based fold index
            total_documents: Total documents in validation set
            successful_documents: Successfully processed documents
            failed_documents: Failed document processing
            success_rate_percentage: Success rate percentage
            total_processing_time_seconds: Total fold processing time
            average_processing_time_seconds: Average processing time per document
            total_tokens: Total tokens consumed
            total_cost_usd: Total processing cost
            average_tests_per_document: Average tests generated per document
            average_coverage_percentage: Average requirements coverage
            category_distribution: GAMP category distribution
            category_performance: Performance by category
            error_summary: Error type frequency
            successful_documents_list: List of successful document IDs
            failed_documents_list: List of failed document IDs
            random_seed: Random seed used
            model_name: LLM model name
        """
        log_entry = FoldSummaryLog(
            run_id=self.run_id,
            experiment_id=self.experiment_id,
            fold_id=fold_id,
            fold_index=fold_index,
            summary_timestamp=datetime.now(UTC).isoformat(),
            random_seed=random_seed,
            model_name=model_name,
            total_documents=total_documents,
            successful_documents=successful_documents,
            failed_documents=failed_documents,
            success_rate_percentage=success_rate_percentage,
            total_processing_time_seconds=total_processing_time_seconds,
            average_processing_time_seconds=average_processing_time_seconds,
            total_tokens=total_tokens,
            total_cost_usd=total_cost_usd,
            average_tests_per_document=average_tests_per_document,
            average_coverage_percentage=average_coverage_percentage,
            category_distribution=category_distribution or {},
            category_performance=category_performance or {},
            error_summary=error_summary or {},
            successful_documents_list=successful_documents_list or [],
            failed_documents_list=failed_documents_list or []
        )

        # Write to JSONL file
        with open(self.fold_log_path, "a", encoding="utf-8") as f:
            f.write(log_entry.model_dump_json() + "\n")

        self.logger.info(f"Fold summary logged: {fold_id}")

    def read_urs_logs(self) -> list[URSProcessingLog]:
        """
        Read all URS processing logs from file.

        Returns:
            List of URS processing log entries
        """
        logs = []
        if self.urs_log_path.exists():
            with open(self.urs_log_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            log_data = json.loads(line)
                            logs.append(URSProcessingLog(**log_data))
                        except (json.JSONDecodeError, ValueError) as e:
                            self.logger.warning(f"Failed to parse log line: {e}")
        return logs

    def read_fold_logs(self) -> list[FoldSummaryLog]:
        """
        Read all fold summary logs from file.

        Returns:
            List of fold summary log entries
        """
        logs = []
        if self.fold_log_path.exists():
            with open(self.fold_log_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            log_data = json.loads(line)
                            logs.append(FoldSummaryLog(**log_data))
                        except (json.JSONDecodeError, ValueError) as e:
                            self.logger.warning(f"Failed to parse log line: {e}")
        return logs

    def get_log_file_paths(self) -> dict[str, Path]:
        """
        Get paths to all log files.

        Returns:
            Dictionary mapping log type to file path
        """
        return {
            "urs_processing": self.urs_log_path,
            "fold_summaries": self.fold_log_path
        }

    def generate_log_summary(self) -> dict[str, Any]:
        """
        Generate a summary of all logged data.

        Returns:
            Dictionary with log summary statistics
        """
        urs_logs = self.read_urs_logs()
        fold_logs = self.read_fold_logs()

        return {
            "experiment_id": self.experiment_id,
            "run_id": self.run_id,
            "summary_generated": datetime.now(UTC).isoformat(),
            "urs_processing_logs": {
                "total_entries": len(urs_logs),
                "successful_processing": len([log for log in urs_logs if log.success]),
                "failed_processing": len([log for log in urs_logs if not log.success]),
                "unique_documents": len({log.document_id for log in urs_logs}),
                "unique_folds": len({log.fold_id for log in urs_logs})
            },
            "fold_summary_logs": {
                "total_entries": len(fold_logs),
                "folds_completed": len({log.fold_id for log in fold_logs})
            },
            "log_files": {
                "urs_processing": str(self.urs_log_path),
                "fold_summaries": str(self.fold_log_path)
            }
        }
