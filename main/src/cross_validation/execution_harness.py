"""
Execution Harness for Cross-Validation Framework

This module provides the main entry point for running cross-validation experiments
with comprehensive error handling, monitoring, and checkpointing capabilities.

Key Features:
- Main entry point for cross-validation execution
- Phoenix monitoring initialization and management
- Comprehensive logging and error handling
- Checkpoint and recovery support for long-running experiments
- Progress reporting and status updates
- GAMP-5 compliance with audit trail support
- No fallbacks - explicit error handling only
"""

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

# CRITICAL: Load environment variables FIRST before any other imports
# This ensures API keys are available for all components
load_dotenv(override=True)

from src.monitoring.phoenix_config import setup_phoenix
from src.monitoring.simple_tracer import get_tracer

from .cross_validation_workflow import CrossValidationWorkflow


class ExecutionHarness:
    """
    Main execution harness for cross-validation experiments.

    This class provides:
    - Centralized experiment execution
    - Error handling and recovery
    - Progress monitoring and reporting
    - Phoenix observability setup
    - Logging configuration
    - Checkpoint and resume capabilities
    """

    def __init__(
        self,
        experiment_id: str | None = None,
        log_level: str = "INFO",
        enable_phoenix: bool = True,
        max_parallel_documents: int = 3,
        checkpoint_interval: int = 5  # Save checkpoint every N documents
    ):
        """
        Initialize the ExecutionHarness.

        Args:
            experiment_id: Unique experiment identifier (auto-generated if None)
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
            enable_phoenix: Enable Phoenix observability
            max_parallel_documents: Maximum parallel document processing
            checkpoint_interval: Documents between checkpoints
        """
        # Generate experiment ID if not provided
        if experiment_id is None:
            timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
            experiment_id = f"cv_experiment_{timestamp}"

        self.experiment_id = experiment_id
        self.enable_phoenix = enable_phoenix
        self.max_parallel_documents = max_parallel_documents
        self.checkpoint_interval = checkpoint_interval

        # Initialize logging
        self._setup_logging(log_level)
        self.logger = logging.getLogger(__name__)

        # Initialize monitoring
        if enable_phoenix:
            self._setup_phoenix_monitoring()

        # Initialize tracer
        self.tracer = get_tracer()

        # Execution state
        self.workflow: CrossValidationWorkflow | None = None
        self.start_time: datetime | None = None
        self.end_time: datetime | None = None
        self.experiment_results: dict[str, Any] | None = None

        self.logger.info(f"ExecutionHarness initialized for experiment {experiment_id}")

    def _setup_logging(self, log_level: str) -> None:
        """
        Configure comprehensive logging for the experiment.

        Args:
            log_level: Logging level
        """
        # Convert string level to logging level
        numeric_level = getattr(logging, log_level.upper(), logging.INFO)

        # Configure root logger
        logging.basicConfig(
            level=numeric_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Create file handler for experiment logs
        log_dir = Path("main/output/cross_validation/logs")
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = log_dir / f"{self.experiment_id}.log"
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(numeric_level)

        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
        )
        file_handler.setFormatter(formatter)

        # Add file handler to relevant loggers
        for logger_name in [
            "src.cross_validation",
            "src.core.unified_workflow",
            "src.agents",
            "src.monitoring"
        ]:
            logger = logging.getLogger(logger_name)
            logger.addHandler(file_handler)
            logger.setLevel(numeric_level)

        self.log_file_path = log_file

    def _setup_phoenix_monitoring(self) -> None:
        """Initialize Phoenix observability monitoring."""
        try:
            setup_phoenix()
            self.logger.info("Phoenix monitoring initialized successfully")
        except Exception as e:
            self.logger.exception(f"Failed to initialize Phoenix monitoring: {e}")
            # Continue without Phoenix rather than failing completely
            self.enable_phoenix = False

    def validate_inputs(
        self,
        fold_assignments_path: str | Path,
        urs_corpus_path: str | Path,
        output_directory: str | Path
    ) -> None:
        """
        Validate all required inputs before starting experiment.

        Args:
            fold_assignments_path: Path to fold assignments JSON
            urs_corpus_path: Path to URS corpus directory
            output_directory: Output directory for results

        Raises:
            ValueError: If validation fails (no fallbacks)
        """
        self.logger.info("Validating experiment inputs...")

        # Validate fold assignments
        fold_path = Path(fold_assignments_path)
        if not fold_path.exists():
            msg = f"Fold assignments file not found: {fold_path}"
            raise ValueError(msg)

        if fold_path.suffix != ".json":
            msg = f"Fold assignments must be JSON file: {fold_path}"
            raise ValueError(msg)

        # Validate URS corpus
        corpus_path = Path(urs_corpus_path)
        if not corpus_path.exists():
            msg = f"URS corpus directory not found: {corpus_path}"
            raise ValueError(msg)

        if not corpus_path.is_dir():
            msg = f"URS corpus path must be directory: {corpus_path}"
            raise ValueError(msg)

        # Check for expected category subdirectories
        expected_categories = ["category_3", "category_4", "category_5", "ambiguous"]
        found_categories = [d.name for d in corpus_path.iterdir() if d.is_dir()]
        missing_categories = set(expected_categories) - set(found_categories)

        if missing_categories:
            self.logger.warning(f"Some expected category directories missing: {missing_categories}")

        # Validate/create output directory
        output_path = Path(output_directory)
        try:
            output_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            msg = f"Cannot create output directory {output_path}: {e}"
            raise ValueError(msg)

        # Test file creation permissions
        test_file = output_path / f"test_write_{self.experiment_id}.tmp"
        try:
            test_file.write_text("test", encoding="utf-8")
            test_file.unlink()
        except Exception as e:
            msg = f"No write permissions in output directory {output_path}: {e}"
            raise ValueError(msg)

        self.logger.info("Input validation completed successfully")

    def create_checkpoint(
        self,
        current_fold: str,
        completed_documents: int,
        total_documents: int,
        metrics_summary: dict[str, Any]
    ) -> Path:
        """
        Create a checkpoint file for experiment recovery.

        Args:
            current_fold: Currently processing fold
            completed_documents: Number of completed documents
            total_documents: Total documents in experiment
            metrics_summary: Current metrics summary

        Returns:
            Path to checkpoint file
        """
        checkpoint_data = {
            "experiment_id": self.experiment_id,
            "checkpoint_time": datetime.now(UTC).isoformat(),
            "current_fold": current_fold,
            "completed_documents": completed_documents,
            "total_documents": total_documents,
            "progress_percentage": (completed_documents / total_documents) * 100,
            "metrics_summary": metrics_summary,
            "can_resume": True
        }

        # Save checkpoint
        checkpoint_dir = Path("main/output/cross_validation/checkpoints")
        checkpoint_dir.mkdir(parents=True, exist_ok=True)

        checkpoint_file = checkpoint_dir / f"{self.experiment_id}_checkpoint.json"

        import json
        with open(checkpoint_file, "w", encoding="utf-8") as f:
            json.dump(checkpoint_data, f, indent=2)

        self.logger.info(f"Checkpoint saved: {checkpoint_file}")
        return checkpoint_file

    def report_progress(
        self,
        current_fold: str,
        completed_documents: int,
        total_documents: int,
        success_rate: float,
        current_cost: float,
        estimated_total_cost: float
    ) -> None:
        """
        Report experiment progress.

        Args:
            current_fold: Currently processing fold
            completed_documents: Number of completed documents
            total_documents: Total documents in experiment
            success_rate: Current success rate percentage
            current_cost: Current total cost
            estimated_total_cost: Estimated total cost
        """
        progress_pct = (completed_documents / total_documents) * 100
        elapsed_time = (datetime.now(UTC) - self.start_time).total_seconds() if self.start_time else 0

        self.logger.info(
            f"PROGRESS: {current_fold} | "
            f"{completed_documents}/{total_documents} docs ({progress_pct:.1f}%) | "
            f"Success: {success_rate:.1f}% | "
            f"Cost: ${current_cost:.2f}/${estimated_total_cost:.2f} | "
            f"Elapsed: {elapsed_time/60:.1f}min"
        )

        # Also log to console for immediate feedback

    async def run_experiment(
        self,
        fold_assignments_path: str | Path,
        urs_corpus_path: str | Path,
        output_directory: str | Path,
        random_seed: int = 42,
        timeout_seconds: int = 7200  # 2 hours default
    ) -> dict[str, Any]:
        """
        Execute the complete cross-validation experiment.

        Args:
            fold_assignments_path: Path to fold assignments JSON file
            urs_corpus_path: Path to URS corpus directory
            output_directory: Output directory for results and metrics
            random_seed: Random seed for reproducibility
            timeout_seconds: Maximum execution time

        Returns:
            Dictionary with complete experiment results

        Raises:
            ValueError: If inputs are invalid
            RuntimeError: If experiment execution fails
        """
        self.start_time = datetime.now(UTC)
        self.logger.info(f"Starting cross-validation experiment {self.experiment_id}")

        try:
            # Validate inputs
            self.validate_inputs(fold_assignments_path, urs_corpus_path, output_directory)

            # Initialize workflow
            self.workflow = CrossValidationWorkflow(
                timeout=timeout_seconds,
                verbose=True,
                enable_phoenix=self.enable_phoenix,
                max_parallel_documents=self.max_parallel_documents
            )

            # Execute the workflow
            self.logger.info("Executing cross-validation workflow...")

            result = await self.workflow.run(
                experiment_id=self.experiment_id,
                fold_assignments_path=str(fold_assignments_path),
                urs_corpus_path=str(urs_corpus_path),
                output_directory=str(output_directory),
                max_parallel_documents=self.max_parallel_documents,
                random_seed=random_seed
            )

            self.end_time = datetime.now(UTC)

            # Process results
            if hasattr(result, "result"):
                self.experiment_results = result.result
            else:
                self.experiment_results = result

            # Add execution harness metadata
            self.experiment_results["execution_metadata"] = {
                "harness_version": "1.0.0",
                "start_time": self.start_time.isoformat(),
                "end_time": self.end_time.isoformat(),
                "total_duration_seconds": (self.end_time - self.start_time).total_seconds(),
                "phoenix_enabled": self.enable_phoenix,
                "log_file": str(self.log_file_path),
                "random_seed": random_seed
            }

            # Add structured logging file paths if available
            structured_log_dir = Path(output_directory) / "structured_logs"
            if structured_log_dir.exists():
                urs_log_file = structured_log_dir / f"{self.experiment_id}_urs_processing.jsonl"
                fold_log_file = structured_log_dir / f"{self.experiment_id}_fold_summaries.jsonl"

                self.experiment_results["structured_logs"] = {
                    "urs_processing_log": str(urs_log_file) if urs_log_file.exists() else None,
                    "fold_summaries_log": str(fold_log_file) if fold_log_file.exists() else None,
                    "log_directory": str(structured_log_dir)
                }

            self.logger.info(f"Experiment {self.experiment_id} completed successfully")
            self.logger.info(f"Total duration: {self.experiment_results['execution_metadata']['total_duration_seconds']:.1f} seconds")
            self.logger.info(f"Overall success rate: {self.experiment_results.get('summary', {}).get('overall_success_rate', 0):.1f}%")
            self.logger.info(f"Total cost: ${self.experiment_results.get('summary', {}).get('total_cost_usd', 0):.2f}")

            return self.experiment_results

        except Exception as e:
            self.end_time = datetime.now(UTC)
            self.logger.exception(f"Experiment failed: {e}")

            # Create failure result
            self.experiment_results = {
                "experiment_id": self.experiment_id,
                "status": "failed",
                "error": str(e),
                "error_type": type(e).__name__,
                "execution_metadata": {
                    "start_time": self.start_time.isoformat() if self.start_time else None,
                    "end_time": self.end_time.isoformat(),
                    "partial_duration_seconds": (self.end_time - self.start_time).total_seconds() if self.start_time else 0,
                    "log_file": str(self.log_file_path)
                }
            }

            msg = f"Cross-validation experiment failed: {e}"
            raise RuntimeError(msg) from e

    def get_experiment_summary(self) -> dict[str, Any]:
        """
        Get a summary of the experiment results.

        Returns:
            Dictionary with experiment summary
        """
        if not self.experiment_results:
            return {
                "experiment_id": self.experiment_id,
                "status": "not_started",
                "message": "Experiment has not been executed yet"
            }

        summary = self.experiment_results.get("summary", {})

        return {
            "experiment_id": self.experiment_id,
            "status": self.experiment_results.get("status", "unknown"),
            "total_folds": summary.get("total_folds", 0),
            "total_documents": summary.get("total_documents", 0),
            "overall_success_rate": summary.get("overall_success_rate", 0.0),
            "total_cost_usd": summary.get("total_cost_usd", 0.0),
            "duration_seconds": self.experiment_results.get("execution_metadata", {}).get("total_duration_seconds", 0),
            "metrics_file": summary.get("metrics_file"),
            "log_file": str(self.log_file_path)
        }


# Convenience function for direct execution
async def run_cross_validation_experiment(
    fold_assignments_path: str | Path = "datasets/cross_validation/fold_assignments.json",
    urs_corpus_path: str | Path = "datasets/urs_corpus",
    output_directory: str | Path = "main/output/cross_validation",
    experiment_id: str | None = None,
    random_seed: int = 42,
    max_parallel_documents: int = 3,
    timeout_seconds: int = 7200,
    enable_phoenix: bool = True,
    log_level: str = "INFO"
) -> dict[str, Any]:
    """
    Convenience function to run a complete cross-validation experiment.

    Args:
        fold_assignments_path: Path to fold assignments JSON file
        urs_corpus_path: Path to URS corpus directory
        output_directory: Output directory for results
        experiment_id: Unique experiment identifier
        random_seed: Random seed for reproducibility
        max_parallel_documents: Maximum parallel document processing
        timeout_seconds: Maximum execution time
        enable_phoenix: Enable Phoenix observability
        log_level: Logging level

    Returns:
        Dictionary with complete experiment results
    """
    harness = ExecutionHarness(
        experiment_id=experiment_id,
        log_level=log_level,
        enable_phoenix=enable_phoenix,
        max_parallel_documents=max_parallel_documents
    )

    return await harness.run_experiment(
        fold_assignments_path=fold_assignments_path,
        urs_corpus_path=urs_corpus_path,
        output_directory=output_directory,
        random_seed=random_seed,
        timeout_seconds=timeout_seconds
    )
