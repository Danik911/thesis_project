"""
Cross-Validation Workflow for Pharmaceutical Test Generation System

This module implements a LlamaIndex workflow that orchestrates cross-validation
testing across multiple URS documents and folds, integrating with the existing
UnifiedTestGenerationWorkflow to evaluate system performance and reliability.

Key Features:
- 5-fold cross-validation execution
- Integration with UnifiedTestGenerationWorkflow
- Parallel processing of validation documents
- Comprehensive metrics collection
- Phoenix observability integration
- GAMP-5 compliance with audit trails
- Error handling with explicit failures (no fallbacks)
"""

import os
import asyncio
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from dotenv import load_dotenv

# CRITICAL: Load environment variables FIRST before any other imports
# This ensures API keys are available for all workflow components
load_dotenv(override=True)

from llama_index.core.workflow import (
    Context,
    Event,
    StartEvent,
    StopEvent,
    Workflow,
    step,
)
from pydantic import Field
# TEMPORARILY DISABLED to fix circular import for Task 30
# from src.core.unified_workflow import UnifiedTestGenerationWorkflow

from .fold_manager import FoldManager, URSDocument
from .metrics_collector import MetricsCollector
from .structured_logger import StructuredLogger


class CrossValidationStartEvent(Event):
    """Event to start cross-validation experiment."""
    experiment_id: str = Field(description="Unique experiment identifier")
    fold_assignments_path: str = Field(description="Path to fold assignments JSON")
    urs_corpus_path: str = Field(description="Path to URS corpus directory")
    output_directory: str = Field(description="Output directory for results")
    max_parallel_documents: int = Field(default=3, description="Maximum parallel document processing")
    random_seed: int = Field(default=42, description="Random seed for reproducibility")


class FoldStartEvent(Event):
    """Event to start processing a specific fold."""
    fold_id: str = Field(description="Fold identifier")
    train_documents: list[URSDocument] = Field(description="Training documents")
    validation_documents: list[URSDocument] = Field(description="Validation documents")

    class Config:
        arbitrary_types_allowed = True


class DocumentProcessingEvent(Event):
    """Event for processing a single validation document."""
    document: URSDocument = Field(description="Document to process")
    fold_id: str = Field(description="Source fold identifier")
    timer_key: str = Field(description="Metrics timer key")

    class Config:
        arbitrary_types_allowed = True


class DocumentResultEvent(Event):
    """Event with results from processing a single document."""
    document_id: str = Field(description="Document identifier")
    fold_id: str = Field(description="Source fold identifier")
    timer_key: str = Field(description="Metrics timer key")
    success: bool = Field(description="Processing success status")

    # Workflow results
    workflow_result: dict[str, Any] | None = Field(default=None, description="Complete workflow result")

    # Error information
    error_message: str | None = Field(default=None, description="Error message if failed")
    error_type: str | None = Field(default=None, description="Error classification")

    # Metrics
    prompt_tokens: int = Field(default=0, description="Prompt tokens consumed")
    completion_tokens: int = Field(default=0, description="Completion tokens generated")
    tests_generated: int = Field(default=0, description="Number of tests generated")
    coverage_percentage: float = Field(default=0.0, description="Requirements coverage")
    gamp_category: int | None = Field(default=None, description="Detected GAMP category")
    confidence_score: float | None = Field(default=None, description="Categorization confidence")


class FoldCompleteEvent(Event):
    """Event when a fold is completed."""
    fold_id: str = Field(description="Completed fold identifier")
    total_documents: int = Field(description="Total documents in fold")
    successful_documents: int = Field(description="Successfully processed documents")
    failed_documents: int = Field(description="Failed document processing")
    fold_results: list[DocumentResultEvent] = Field(description="Results for all documents in fold")


class CrossValidationCompleteEvent(Event):
    """Event when entire cross-validation experiment is complete."""
    experiment_id: str = Field(description="Experiment identifier")
    total_folds: int = Field(description="Number of folds processed")
    total_documents: int = Field(description="Total documents processed")
    overall_success_rate: float = Field(description="Overall success rate")
    total_cost_usd: float = Field(description="Total experiment cost")
    metrics_file_path: str = Field(description="Path to saved metrics file")


class CrossValidationWorkflow(Workflow):
    """
    Cross-validation workflow that orchestrates evaluation of the test generation system.

    This workflow provides:
    1. Systematic evaluation across all URS documents
    2. 5-fold cross-validation with proper train/test splits
    3. Parallel processing of validation documents
    4. Comprehensive metrics collection and analysis
    5. Integration with existing UnifiedTestGenerationWorkflow
    6. Phoenix observability and GAMP-5 compliance
    """

    def __init__(
        self,
        timeout: int = 7200,  # 2 hours for complete cross-validation
        verbose: bool = False,
        enable_phoenix: bool = True,
        max_parallel_documents: int = 3
    ):
        """
        Initialize the CrossValidationWorkflow.

        Args:
            timeout: Maximum time for complete experiment (seconds)
            verbose: Enable verbose logging
            enable_phoenix: Enable Phoenix observability
            max_parallel_documents: Maximum parallel document processing
        """
        super().__init__(timeout=timeout, verbose=verbose)

        self.verbose = verbose
        self.enable_phoenix = enable_phoenix
        self.max_parallel_documents = max_parallel_documents
        self.logger = logging.getLogger(__name__)

        # Workflow state
        self.fold_manager: FoldManager | None = None
        self.metrics_collector: MetricsCollector | None = None
        self.structured_logger: StructuredLogger | None = None

        self.logger.info("CrossValidationWorkflow initialized")

    @step
    async def start_cross_validation(
        self,
        ctx: Context,
        ev: StartEvent
    ) -> CrossValidationStartEvent:
        """
        Initialize cross-validation experiment.

        Args:
            ctx: Workflow context
            ev: Start event with experiment parameters

        Returns:
            CrossValidationStartEvent to begin processing
        """
        self.logger.info("Starting cross-validation experiment")

        # Extract parameters from start event
        experiment_id = ev.get("experiment_id") or f"cv_experiment_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"
        fold_assignments_path = ev.get("fold_assignments_path")
        urs_corpus_path = ev.get("urs_corpus_path")
        output_directory = ev.get("output_directory")
        max_parallel_documents = ev.get("max_parallel_documents", 3)
        random_seed = ev.get("random_seed", 42)

        # Validate required parameters
        if not fold_assignments_path:
            msg = "fold_assignments_path is required"
            raise ValueError(msg)
        if not urs_corpus_path:
            msg = "urs_corpus_path is required"
            raise ValueError(msg)
        if not output_directory:
            msg = "output_directory is required"
            raise ValueError(msg)

        # Store in context
        await ctx.store.set("experiment_id", experiment_id)
        await ctx.store.set("fold_assignments_path", fold_assignments_path)
        await ctx.store.set("urs_corpus_path", urs_corpus_path)
        await ctx.store.set("output_directory", output_directory)
        await ctx.store.set("max_parallel_documents", max_parallel_documents)
        await ctx.store.set("random_seed", random_seed)

        return CrossValidationStartEvent(
            experiment_id=experiment_id,
            fold_assignments_path=fold_assignments_path,
            urs_corpus_path=urs_corpus_path,
            output_directory=output_directory,
            max_parallel_documents=max_parallel_documents,
            random_seed=random_seed
        )

    @step
    async def initialize_experiment(
        self,
        ctx: Context,
        ev: CrossValidationStartEvent
    ) -> FoldStartEvent:
        """
        Initialize experiment components and start first fold.

        Args:
            ctx: Workflow context
            ev: Cross-validation start event

        Returns:
            FoldStartEvent for the first fold
        """
        self.logger.info(f"Initializing experiment {ev.experiment_id}")

        # Initialize fold manager
        self.fold_manager = FoldManager(
            fold_assignments_path=ev.fold_assignments_path,
            urs_corpus_path=ev.urs_corpus_path,
            random_seed=ev.random_seed
        )

        # Initialize metrics collector
        self.metrics_collector = MetricsCollector(
            experiment_id=ev.experiment_id,
            output_directory=ev.output_directory,
            model_name="deepseek/deepseek-chat"
        )

        # Initialize structured logger
        self.structured_logger = StructuredLogger(
            experiment_id=ev.experiment_id,
            output_directory=ev.output_directory
        )

        # Store components in context
        await ctx.store.set("fold_manager", self.fold_manager)
        await ctx.store.set("metrics_collector", self.metrics_collector)
        await ctx.store.set("structured_logger", self.structured_logger)

        # Initialize fold tracking
        await ctx.store.set("current_fold_index", 0)
        await ctx.store.set("completed_folds", [])
        await ctx.store.set("fold_results", {})

        # Get first fold
        fold_iterator = self.fold_manager.iterate_folds()
        fold_id, train_docs, val_docs = next(fold_iterator)

        # Store iterator state (we'll handle this differently)
        all_folds = list(self.fold_manager.iterate_folds())
        await ctx.store.set("all_folds", all_folds)

        self.logger.info(f"Starting fold {fold_id}: {len(train_docs)} train, {len(val_docs)} validation docs")

        return FoldStartEvent(
            fold_id=fold_id,
            train_documents=train_docs,
            validation_documents=val_docs
        )

    @step
    async def process_fold(
        self,
        ctx: Context,
        ev: FoldStartEvent
    ) -> DocumentProcessingEvent:
        """
        Start processing documents in a fold.

        Args:
            ctx: Workflow context
            ev: Fold start event

        Returns:
            DocumentProcessingEvent for the first validation document
        """
        self.logger.info(f"Processing fold {ev.fold_id} with {len(ev.validation_documents)} validation documents")

        # Get metrics collector
        metrics_collector = await ctx.store.get("metrics_collector")
        if not metrics_collector:
            msg = "MetricsCollector not found in context"
            raise ValueError(msg)

        # Start fold metrics collection
        metrics_collector.start_fold_processing(ev.fold_id)

        # Store fold information in context
        await ctx.store.set("current_fold_id", ev.fold_id)
        await ctx.store.set("current_validation_docs", ev.validation_documents)
        await ctx.store.set("current_doc_index", 0)
        await ctx.store.set("current_fold_results", [])

        # Start processing first validation document
        if ev.validation_documents:
            first_doc = ev.validation_documents[0]

            # Start metrics timer
            timer_key = metrics_collector.start_document_processing(
                document_id=first_doc.document_id,
                fold_id=ev.fold_id,
                category_folder=first_doc.category_folder
            )

            return DocumentProcessingEvent(
                document=first_doc,
                fold_id=ev.fold_id,
                timer_key=timer_key
            )
        # No validation documents - should not happen but handle gracefully
        msg = f"No validation documents found for fold {ev.fold_id}"
        raise ValueError(msg)

    @step(num_workers=3)  # Allow parallel processing
    async def process_document(
        self,
        ctx: Context,
        ev: DocumentProcessingEvent
    ) -> DocumentResultEvent:
        """
        Process a single validation document through the UnifiedTestGenerationWorkflow.

        Args:
            ctx: Workflow context
            ev: Document processing event

        Returns:
            DocumentResultEvent with processing results
        """
        self.logger.info(f"Processing document {ev.document.document_id} in fold {ev.fold_id}")

        # Get structured logger
        structured_logger = await ctx.store.get("structured_logger")
        fold_index = await ctx.store.get("current_fold_index", 0)

        start_time = asyncio.get_event_loop().time()

        try:
            # Create temporary file for the document
            output_directory = await ctx.store.get("output_directory")
            temp_dir = Path(output_directory) / "temp_documents"
            temp_dir.mkdir(parents=True, exist_ok=True)

            temp_doc_path = temp_dir / f"{ev.document.document_id}_{ev.fold_id}.md"
            temp_doc_path.write_text(ev.document.content, encoding="utf-8")

            # Dynamic import to avoid circular dependency
            from src.core.unified_workflow import UnifiedTestGenerationWorkflow
            
            # Initialize UnifiedTestGenerationWorkflow
            unified_workflow = UnifiedTestGenerationWorkflow(
                timeout=1800,  # 30 minutes per document
                verbose=self.verbose,
                enable_phoenix=self.enable_phoenix,
                enable_parallel_coordination=True,
                enable_human_consultation=False  # Disable for automated evaluation
            )

            # Run the workflow
            workflow_result = await unified_workflow.run(document_path=str(temp_doc_path))

            # Clean up temporary file
            temp_doc_path.unlink(missing_ok=True)

            # Extract metrics from result
            success = True
            error_message = None
            error_type = None

            # Check if workflow completed successfully
            if hasattr(workflow_result, 'result'):
                workflow_result = workflow_result.result

            # Calculate processing time
            end_time = asyncio.get_event_loop().time()
            processing_time = end_time - start_time

            # Extract workflow metrics
            prompt_tokens = 0
            completion_tokens = 0
            tests_generated = 0
            coverage_percentage = 0.0
            gamp_category = None
            confidence_score = None
            raw_predictions = {}

            if isinstance(workflow_result, dict):
                if workflow_result.get("status") == "failed":
                    success = False
                    error_message = workflow_result.get("error", "Unknown error")
                    error_type = "workflow_execution_error"
                else:
                    # Extract success metrics
                    if "categorization" in workflow_result:
                        cat = workflow_result["categorization"]
                        gamp_category = cat.get("gamp_category") or cat.get("category")
                        confidence_score = cat.get("confidence_score") or cat.get("confidence")
                        # Store raw categorization predictions
                        raw_predictions["categorization"] = cat

                    if "oq_generation" in workflow_result:
                        oq = workflow_result["oq_generation"]
                        tests_generated = oq.get("total_tests", 0)
                        coverage_percentage = oq.get("coverage_percentage", 0.0)
                        # Store raw OQ generation results
                        raw_predictions["oq_generation"] = oq

                    # Store complete workflow result as raw prediction
                    raw_predictions["complete_workflow"] = workflow_result

                    # Extract token metrics (if available from Phoenix traces)
                    # For now, use placeholder values
                    prompt_tokens = 2000  # Estimated
                    completion_tokens = 1000  # Estimated

            # Log structured data
            if structured_logger:
                config_snapshot = {
                    "model_name": "deepseek/deepseek-chat",
                    "model_temperature": 0.0,
                    "enable_phoenix": self.enable_phoenix,
                    "max_parallel_documents": self.max_parallel_documents
                }

                input_metadata = {
                    "document_id": ev.document.document_id,
                    "category_folder": ev.document.category_folder,
                    "file_size_bytes": ev.document.file_size_bytes,
                    "content_length": len(ev.document.content)
                }

                token_usage = {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": prompt_tokens + completion_tokens
                }

                # Calculate cost using centralized pricing constants
                from .pricing_constants import calculate_deepseek_v3_cost
                cost_usd = calculate_deepseek_v3_cost(prompt_tokens, completion_tokens)

                structured_logger.log_urs_processing(
                    fold_id=ev.fold_id,
                    fold_index=fold_index,
                    document_id=ev.document.document_id,
                    success=success,
                    processing_time_seconds=processing_time,
                    config_snapshot=config_snapshot,
                    input_metadata=input_metadata,
                    raw_predictions=raw_predictions,
                    expected_gamp_category=None,  # Could be derived from category_folder
                    token_usage=token_usage,
                    cost_usd=cost_usd,
                    generated_tests_count=tests_generated,
                    coverage_percentage=coverage_percentage,
                    gamp_category_detected=gamp_category,
                    confidence_score=confidence_score or 0.0
                )

            return DocumentResultEvent(
                document_id=ev.document.document_id,
                fold_id=ev.fold_id,
                timer_key=ev.timer_key,
                success=success,
                workflow_result=workflow_result if success else None,
                error_message=error_message,
                error_type=error_type,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                tests_generated=tests_generated,
                coverage_percentage=coverage_percentage,
                gamp_category=gamp_category,
                confidence_score=confidence_score
            )

        except Exception as e:
            # Calculate processing time for failed case
            end_time = asyncio.get_event_loop().time()
            processing_time = end_time - start_time

            self.logger.exception(f"Document processing failed for {ev.document.document_id}: {e}")

            # Log structured data for failure
            if structured_logger:
                config_snapshot = {
                    "model_name": "deepseek/deepseek-chat",
                    "model_temperature": 0.0,
                    "enable_phoenix": self.enable_phoenix,
                    "max_parallel_documents": self.max_parallel_documents
                }

                input_metadata = {
                    "document_id": ev.document.document_id,
                    "category_folder": ev.document.category_folder,
                    "file_size_bytes": ev.document.file_size_bytes,
                    "content_length": len(ev.document.content)
                }

                structured_logger.log_urs_processing(
                    fold_id=ev.fold_id,
                    fold_index=fold_index,
                    document_id=ev.document.document_id,
                    success=False,
                    processing_time_seconds=processing_time,
                    config_snapshot=config_snapshot,
                    input_metadata=input_metadata,
                    error_message=str(e),
                    error_type=type(e).__name__,
                    error_traceback=str(e) if self.verbose else None
                )

            return DocumentResultEvent(
                document_id=ev.document.document_id,
                fold_id=ev.fold_id,
                timer_key=ev.timer_key,
                success=False,
                error_message=str(e),
                error_type=type(e).__name__,
                prompt_tokens=0,
                completion_tokens=0
            )

    @step
    async def collect_document_result(
        self,
        ctx: Context,
        ev: DocumentResultEvent
    ) -> DocumentProcessingEvent | FoldCompleteEvent:
        """
        Collect document processing results and emit next document or complete fold.

        Args:
            ctx: Workflow context
            ev: Document result event

        Returns:
            DocumentProcessingEvent for next document or FoldCompleteEvent when fold complete
        """
        self.logger.info(f"Collecting result for {ev.document_id}: success={ev.success}")

        # Get metrics collector and record results
        metrics_collector = await ctx.store.get("metrics_collector")
        metrics_collector.stop_document_processing(
            timer_key=ev.timer_key,
            success=ev.success,
            error_message=ev.error_message,
            error_type=ev.error_type,
            prompt_tokens=ev.prompt_tokens,
            completion_tokens=ev.completion_tokens,
            tests_generated=ev.tests_generated,
            coverage_percentage=ev.coverage_percentage,
            gamp_category=ev.gamp_category,
            confidence_score=ev.confidence_score
        )

        # Store result
        fold_results = await ctx.store.get("current_fold_results", [])
        fold_results.append(ev)
        await ctx.store.set("current_fold_results", fold_results)

        # Check if we have more documents to process
        validation_docs = await ctx.store.get("current_validation_docs", [])
        current_index = await ctx.store.get("current_doc_index", 0)
        next_index = current_index + 1

        if next_index < len(validation_docs):
            # Process next document
            await ctx.store.set("current_doc_index", next_index)
            next_doc = validation_docs[next_index]
            fold_id = await ctx.store.get("current_fold_id")

            # Start timer for next document
            timer_key = metrics_collector.start_document_processing(
                document_id=next_doc.document_id,
                fold_id=fold_id,
                category_folder=next_doc.category_folder
            )

            return DocumentProcessingEvent(
                document=next_doc,
                fold_id=fold_id,
                timer_key=timer_key
            )
        # Fold is complete
        fold_id = await ctx.store.get("current_fold_id")

        # Complete fold metrics
        fold_metrics = metrics_collector.complete_fold_processing(fold_id)

        successful_docs = len([r for r in fold_results if r.success])
        failed_docs = len([r for r in fold_results if not r.success])

        # Log structured fold summary
        structured_logger = await ctx.store.get("structured_logger")
        if structured_logger:
            # Extract performance metrics from fold results
            processing_times = [r.processing_time_seconds for r in fold_results if r.success and hasattr(r, "processing_time_seconds")]
            avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0.0

            total_tokens = sum(r.prompt_tokens + r.completion_tokens for r in fold_results)
            # Calculate total cost using centralized pricing function
            from .pricing_constants import calculate_deepseek_v3_cost
            total_cost = sum(calculate_deepseek_v3_cost(r.prompt_tokens, r.completion_tokens) for r in fold_results)

            avg_tests = sum(r.tests_generated for r in fold_results if r.success) / max(successful_docs, 1)
            avg_coverage = sum(r.coverage_percentage for r in fold_results if r.success) / max(successful_docs, 1)

            # Category distribution
            category_dist = {}
            for r in fold_results:
                if r.gamp_category:
                    cat_key = f"category_{r.gamp_category}"
                    category_dist[cat_key] = category_dist.get(cat_key, 0) + 1

            # Error summary
            error_summary = {}
            for r in fold_results:
                if not r.success and r.error_type:
                    error_summary[r.error_type] = error_summary.get(r.error_type, 0) + 1

            success_rate = (successful_docs / len(fold_results)) * 100 if fold_results else 0.0

            current_fold_index = await ctx.store.get("current_fold_index", 0)

            structured_logger.log_fold_summary(
                fold_id=fold_id,
                fold_index=current_fold_index,
                total_documents=len(fold_results),
                successful_documents=successful_docs,
                failed_documents=failed_docs,
                success_rate_percentage=success_rate,
                total_processing_time_seconds=fold_metrics.fold_duration_seconds or 0.0,
                average_processing_time_seconds=avg_processing_time,
                total_tokens=total_tokens,
                total_cost_usd=total_cost,
                average_tests_per_document=avg_tests,
                average_coverage_percentage=avg_coverage,
                category_distribution=category_dist,
                error_summary=error_summary,
                successful_documents_list=[r.document_id for r in fold_results if r.success],
                failed_documents_list=[r.document_id for r in fold_results if not r.success]
            )

        self.logger.info(f"Fold {fold_id} complete: {successful_docs}/{len(fold_results)} successful")

        return FoldCompleteEvent(
            fold_id=fold_id,
            total_documents=len(fold_results),
            successful_documents=successful_docs,
            failed_documents=failed_docs,
            fold_results=fold_results
        )

    @step
    async def handle_fold_completion(
        self,
        ctx: Context,
        ev: FoldCompleteEvent
    ) -> FoldStartEvent | CrossValidationCompleteEvent:
        """
        Handle fold completion and start next fold or complete experiment.

        Args:
            ctx: Workflow context
            ev: Fold complete event

        Returns:
            FoldStartEvent for next fold or CrossValidationCompleteEvent when done
        """
        self.logger.info(f"Fold {ev.fold_id} completed: {ev.successful_documents}/{ev.total_documents} successful")

        # Store fold results
        fold_results = await ctx.store.get("fold_results", {})
        fold_results[ev.fold_id] = ev
        await ctx.store.set("fold_results", fold_results)

        completed_folds = await ctx.store.get("completed_folds", [])
        completed_folds.append(ev.fold_id)
        await ctx.store.set("completed_folds", completed_folds)

        # Check if we have more folds to process
        current_fold_index = await ctx.store.get("current_fold_index", 0)
        fold_manager = await ctx.store.get("fold_manager")
        next_fold_index = current_fold_index + 1

        if next_fold_index < fold_manager.get_fold_count():
            # Start next fold
            await ctx.store.set("current_fold_index", next_fold_index)

            # Get next fold data
            all_folds = list(fold_manager.iterate_folds())
            fold_id, train_docs, val_docs = all_folds[next_fold_index]

            self.logger.info(f"Starting fold {fold_id}: {len(train_docs)} train, {len(val_docs)} validation docs")

            return FoldStartEvent(
                fold_id=fold_id,
                train_documents=train_docs,
                validation_documents=val_docs
            )
        # All folds complete - finalize experiment
        metrics_collector = await ctx.store.get("metrics_collector")
        experiment_metrics = metrics_collector.finalize_experiment()

        # Save metrics to file
        metrics_file_path = metrics_collector.save_metrics()

        total_docs = sum(fold_result.total_documents for fold_result in fold_results.values())
        successful_docs = sum(fold_result.successful_documents for fold_result in fold_results.values())

        self.logger.info(f"Cross-validation complete: {len(completed_folds)} folds, "
                       f"{successful_docs}/{total_docs} documents successful, "
                       f"${experiment_metrics.total_cost_usd:.2f} total cost")

        return CrossValidationCompleteEvent(
            experiment_id=experiment_metrics.experiment_id,
            total_folds=len(completed_folds),
            total_documents=total_docs,
            overall_success_rate=experiment_metrics.overall_success_rate,
            total_cost_usd=experiment_metrics.total_cost_usd,
            metrics_file_path=str(metrics_file_path)
        )

    @step
    async def complete_cross_validation(
        self,
        ctx: Context,
        ev: CrossValidationCompleteEvent
    ) -> StopEvent:
        """
        Complete the cross-validation experiment.

        Args:
            ctx: Workflow context
            ev: Cross-validation complete event

        Returns:
            StopEvent with comprehensive experiment results
        """
        self.logger.info(f"Cross-validation experiment {ev.experiment_id} completed successfully")

        # Prepare comprehensive results
        final_results = {
            "experiment_id": ev.experiment_id,
            "status": "completed",
            "summary": {
                "total_folds": ev.total_folds,
                "total_documents": ev.total_documents,
                "overall_success_rate": ev.overall_success_rate,
                "total_cost_usd": ev.total_cost_usd,
                "metrics_file": ev.metrics_file_path
            },
            "fold_results": await ctx.store.get("fold_results", {}),
            "completion_time": datetime.now(UTC).isoformat()
        }

        return StopEvent(result=final_results)
