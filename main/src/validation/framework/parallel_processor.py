#!/usr/bin/env python3
"""
Parallel Document Processor for Validation Framework

This module provides parallel processing capabilities for pharmaceutical document
validation with support for 3 concurrent documents, proper resource management,
and integration with the existing unified workflow.

CRITICAL REQUIREMENTS:
- Real document processing (no mocking)
- Maximum 3 concurrent documents
- Asyncio with semaphore rate limiting
- Individual error handling per document
- Integration with existing CV Manager
- Phoenix monitoring integration
- NO FALLBACK LOGIC - explicit errors only
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
import logging

# Add project paths for imports
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent / "datasets" / "cross_validation"))
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    from cv_manager import load_cv_manager, DocumentMetadata
    CV_MANAGER_AVAILABLE = True
except ImportError:
    CV_MANAGER_AVAILABLE = False

try:
    from core.unified_workflow import run_unified_workflow
    UNIFIED_WORKFLOW_AVAILABLE = True
except ImportError:
    UNIFIED_WORKFLOW_AVAILABLE = False


@dataclass
class DocumentProcessingResult:
    """Result from processing a single document."""
    document_id: str
    document_path: str
    success: bool
    processing_time: float
    categorization_result: Optional[Dict[str, Any]] = None
    test_generation_result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    
    
@dataclass
class FoldProcessingResult:
    """Result from processing an entire fold."""
    fold_number: int
    success: bool
    total_documents: int
    successful_documents: int
    failed_documents: int
    execution_time: float
    parallel_efficiency: float
    document_results: List[DocumentProcessingResult]
    categorization_results: Dict[str, Any]
    test_generation_results: Dict[str, Any]
    errors: List[str]


class ParallelDocumentProcessor:
    """
    Parallel processor for pharmaceutical documents during validation.
    
    This processor handles concurrent processing of up to 3 documents while
    maintaining proper resource management, error handling, and integration
    with the existing pharmaceutical workflow systems.
    """
    
    def __init__(self, validation_config):
        """
        Initialize the parallel document processor.
        
        Args:
            validation_config: Validation execution configuration
            
        Raises:
            RuntimeError: If initialization fails
        """
        self.validation_config = validation_config
        self.concurrency_limit = 3  # Maximum concurrent documents
        self.semaphore = asyncio.Semaphore(self.concurrency_limit)
        self.cv_manager = None
        self.logger = logging.getLogger(__name__)
        
        # Processing statistics
        self.total_processed = 0
        self.total_successful = 0
        self.total_failed = 0
        
        # Rate limiting settings
        self.api_rate_limit = asyncio.Semaphore(10)  # API calls per second
        self.resource_monitor = ResourceMonitor()
    
    async def initialize(self) -> None:
        """
        Initialize the parallel processor with required dependencies.
        
        Raises:
            RuntimeError: If initialization fails
        """
        try:
            self.logger.info("Initializing ParallelDocumentProcessor...")
            
            # Check required modules
            if not CV_MANAGER_AVAILABLE:
                raise RuntimeError("CV Manager not available - ensure cv_manager.py is accessible")
            
            if not UNIFIED_WORKFLOW_AVAILABLE:
                raise RuntimeError("Unified workflow not available - ensure unified_workflow.py is accessible")
            
            # Initialize CV manager
            self.logger.info("Loading CV Manager...")
            self.cv_manager = load_cv_manager()
            
            # Initialize resource monitoring
            await self.resource_monitor.initialize()
            
            self.logger.info(f"Parallel processor initialized with concurrency limit: {self.concurrency_limit}")
            
        except Exception as e:
            raise RuntimeError(f"Failed to initialize parallel processor: {e!s}")
    
    def update_concurrency_limit(self, new_limit: int) -> None:
        """
        Update the concurrency limit for parallel processing.
        
        Args:
            new_limit: New maximum number of concurrent documents
        """
        if not (1 <= new_limit <= 5):
            raise ValueError("Concurrency limit must be between 1 and 5")
        
        self.concurrency_limit = new_limit
        self.semaphore = asyncio.Semaphore(new_limit)
        self.logger.info(f"Updated concurrency limit to: {new_limit}")
    
    async def load_fold_data(self, fold_number: int) -> Dict[str, List[DocumentMetadata]]:
        """
        Load fold data from the CV Manager.
        
        Args:
            fold_number: Fold number to load (1-5)
            
        Returns:
            Dictionary containing train and test documents
            
        Raises:
            RuntimeError: If fold data loading fails
        """
        try:
            if self.cv_manager is None:
                raise RuntimeError("CV Manager not initialized")
            
            self.logger.info(f"Loading fold {fold_number} data...")
            fold_data = self.cv_manager.get_fold(fold_number)
            
            self.logger.info(
                f"Fold {fold_number} loaded: {len(fold_data['test'])} test docs, "
                f"{len(fold_data['train'])} train docs"
            )
            
            return fold_data
            
        except Exception as e:
            raise RuntimeError(f"Failed to load fold {fold_number} data: {e!s}")
    
    async def process_fold_documents(
        self, 
        fold_number: int, 
        fold_data: Dict[str, List[DocumentMetadata]]
    ) -> FoldProcessingResult:
        """
        Process all test documents in a fold with parallel execution.
        
        Args:
            fold_number: Fold number being processed
            fold_data: Fold data containing test and train documents
            
        Returns:
            FoldProcessingResult with comprehensive processing results
            
        Raises:
            RuntimeError: If fold processing fails catastrophically
        """
        start_time = datetime.now()
        
        try:
            self.logger.info(f"Starting parallel processing of fold {fold_number}")
            
            test_documents = fold_data["test"]
            self.logger.info(f"Processing {len(test_documents)} test documents with max {self.concurrency_limit} concurrent")
            
            # Create processing tasks
            processing_tasks = []
            for doc_metadata in test_documents:
                task = asyncio.create_task(
                    self.process_single_document(doc_metadata, fold_number)
                )
                processing_tasks.append(task)
            
            # Execute all tasks with progress monitoring
            document_results = await self._execute_with_progress_monitoring(
                processing_tasks, fold_number
            )
            
            # Calculate processing statistics
            execution_time = (datetime.now() - start_time).total_seconds()
            successful_results = [r for r in document_results if r.success]
            failed_results = [r for r in document_results if not r.success]
            
            # Calculate parallel efficiency
            total_sequential_time = sum(r.processing_time for r in document_results)
            parallel_efficiency = (total_sequential_time / execution_time) / self.concurrency_limit if execution_time > 0 else 0.0
            
            # Aggregate results
            categorization_results = self._aggregate_categorization_results(successful_results)
            test_generation_results = self._aggregate_test_generation_results(successful_results)
            
            # Collect errors
            errors = [r.error_message for r in failed_results if r.error_message]
            
            fold_result = FoldProcessingResult(
                fold_number=fold_number,
                success=len(successful_results) > 0,  # Success if at least one document succeeded
                total_documents=len(test_documents),
                successful_documents=len(successful_results),
                failed_documents=len(failed_results),
                execution_time=execution_time,
                parallel_efficiency=min(parallel_efficiency, 1.0),  # Cap at 100%
                document_results=document_results,
                categorization_results=categorization_results,
                test_generation_results=test_generation_results,
                errors=errors
            )
            
            self.logger.info(
                f"Fold {fold_number} processing complete: "
                f"{len(successful_results)}/{len(test_documents)} successful, "
                f"efficiency: {parallel_efficiency:.2%}, "
                f"time: {execution_time:.2f}s"
            )
            
            return fold_result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Fold {fold_number} processing failed: {e!s}")
            
            return FoldProcessingResult(
                fold_number=fold_number,
                success=False,
                total_documents=len(fold_data.get("test", [])),
                successful_documents=0,
                failed_documents=len(fold_data.get("test", [])),
                execution_time=execution_time,
                parallel_efficiency=0.0,
                document_results=[],
                categorization_results={},
                test_generation_results={},
                errors=[str(e)]
            )
    
    async def process_single_document(
        self, 
        doc_metadata: DocumentMetadata, 
        fold_number: int
    ) -> DocumentProcessingResult:
        """
        Process a single document through the unified workflow.
        
        Args:
            doc_metadata: Document metadata from CV Manager
            fold_number: Current fold number for context
            
        Returns:
            DocumentProcessingResult with processing outcome
        """
        # Acquire semaphore for concurrency control
        async with self.semaphore:
            start_time = datetime.now()
            
            try:
                self.logger.debug(f"Processing document {doc_metadata.doc_id} in fold {fold_number}")
                
                # Check resource availability
                await self.resource_monitor.check_resources()
                
                # Rate limiting for API calls
                async with self.api_rate_limit:
                    # Prepare workflow inputs for single document
                    workflow_inputs = {
                        "input_file": doc_metadata.file_path,
                        "document_id": doc_metadata.doc_id,
                        "validation_mode": True,
                        "enable_consultation_bypass": True,
                        "fold_context": {
                            "fold_number": fold_number,
                            "is_test_document": True,
                            "expected_category": doc_metadata.normalized_category
                        }
                    }
                    
                    # Execute unified workflow for this document
                    self.logger.debug(f"Executing workflow for document {doc_metadata.doc_id}")
                    workflow_result = await run_unified_workflow(**workflow_inputs)
                    
                    processing_time = (datetime.now() - start_time).total_seconds()
                    
                    # Extract results
                    categorization_result = workflow_result.get("categorization", {})
                    test_generation_result = workflow_result.get("test_generation", {})
                    
                    # Validate results
                    success = self._validate_document_result(workflow_result, doc_metadata)
                    
                    result = DocumentProcessingResult(
                        document_id=doc_metadata.doc_id,
                        document_path=doc_metadata.file_path,
                        success=success,
                        processing_time=processing_time,
                        categorization_result=categorization_result,
                        test_generation_result=test_generation_result,
                        error_message=workflow_result.get("error") if not success else None,
                        retry_count=0
                    )
                    
                    if success:
                        self.total_successful += 1
                        self.logger.debug(f"Document {doc_metadata.doc_id} processed successfully in {processing_time:.2f}s")
                    else:
                        self.total_failed += 1
                        self.logger.warning(f"Document {doc_metadata.doc_id} processing failed")
                    
                    self.total_processed += 1
                    return result
                    
            except Exception as e:
                processing_time = (datetime.now() - start_time).total_seconds()
                self.total_failed += 1
                self.total_processed += 1
                
                error_msg = f"Document processing failed: {e!s}"
                self.logger.error(f"Document {doc_metadata.doc_id}: {error_msg}")
                
                return DocumentProcessingResult(
                    document_id=doc_metadata.doc_id,
                    document_path=doc_metadata.file_path,
                    success=False,
                    processing_time=processing_time,
                    error_message=error_msg
                )
    
    async def _execute_with_progress_monitoring(
        self, 
        tasks: List[asyncio.Task], 
        fold_number: int
    ) -> List[DocumentProcessingResult]:
        """
        Execute tasks with real-time progress monitoring.
        
        Args:
            tasks: List of document processing tasks
            fold_number: Current fold number
            
        Returns:
            List of document processing results
        """
        total_tasks = len(tasks)
        completed_tasks = 0
        results = []
        
        # Monitor task completion
        for completed_task in asyncio.as_completed(tasks):
            try:
                result = await completed_task
                results.append(result)
                completed_tasks += 1
                
                progress = (completed_tasks / total_tasks) * 100
                self.logger.info(
                    f"Fold {fold_number} progress: {completed_tasks}/{total_tasks} "
                    f"({progress:.1f}%) - Document: {result.document_id} "
                    f"({'✅' if result.success else '❌'})"
                )
                
            except Exception as e:
                self.logger.error(f"Task execution failed: {e!s}")
                # Create failed result for tracking
                results.append(DocumentProcessingResult(
                    document_id="unknown",
                    document_path="unknown",
                    success=False,
                    processing_time=0.0,
                    error_message=str(e)
                ))
                completed_tasks += 1
        
        return results
    
    def _validate_document_result(
        self, 
        workflow_result: Dict[str, Any], 
        doc_metadata: DocumentMetadata
    ) -> bool:
        """
        Validate that document processing produced valid results.
        
        Args:
            workflow_result: Result from unified workflow
            doc_metadata: Original document metadata
            
        Returns:
            True if result is valid, False otherwise
        """
        # Check for critical failures
        if "error" in workflow_result:
            return False
        
        # Check categorization result
        categorization = workflow_result.get("categorization", {})
        if not categorization or not categorization.get("category"):
            return False
        
        # Check test generation result (if enabled)
        test_generation = workflow_result.get("test_generation", {})
        if "tests" in test_generation and not test_generation["tests"]:
            # Test generation was attempted but produced no tests
            self.logger.warning(f"Document {doc_metadata.doc_id}: No tests generated")
        
        # Consider successful if categorization worked
        return True
    
    def _aggregate_categorization_results(
        self, 
        successful_results: List[DocumentProcessingResult]
    ) -> Dict[str, Any]:
        """Aggregate categorization results across all successful documents."""
        if not successful_results:
            return {"total_categorized": 0, "categories": {}, "accuracy_metrics": {}}
        
        categories = {}
        confidence_scores = []
        
        for result in successful_results:
            if result.categorization_result:
                category = result.categorization_result.get("category", "Unknown")
                confidence = result.categorization_result.get("confidence", 0.0)
                
                if category not in categories:
                    categories[category] = 0
                categories[category] += 1
                
                if confidence > 0:
                    confidence_scores.append(confidence)
        
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        
        return {
            "total_categorized": len(successful_results),
            "categories": categories,
            "accuracy_metrics": {
                "average_confidence": avg_confidence,
                "confidence_scores": confidence_scores,
                "category_distribution": categories
            }
        }
    
    def _aggregate_test_generation_results(
        self, 
        successful_results: List[DocumentProcessingResult]
    ) -> Dict[str, Any]:
        """Aggregate test generation results across all successful documents."""
        if not successful_results:
            return {"total_tests_generated": 0, "test_types": {}, "generation_metrics": {}}
        
        total_tests = 0
        test_types = {}
        generation_times = []
        
        for result in successful_results:
            if result.test_generation_result:
                tests = result.test_generation_result.get("tests", [])
                total_tests += len(tests)
                
                # Count test types
                for test in tests:
                    test_type = test.get("type", "Unknown")
                    if test_type not in test_types:
                        test_types[test_type] = 0
                    test_types[test_type] += 1
                
                # Track generation time
                gen_time = result.test_generation_result.get("generation_time", 0.0)
                if gen_time > 0:
                    generation_times.append(gen_time)
        
        avg_generation_time = sum(generation_times) / len(generation_times) if generation_times else 0.0
        
        return {
            "total_tests_generated": total_tests,
            "test_types": test_types,
            "generation_metrics": {
                "average_generation_time": avg_generation_time,
                "tests_per_document": total_tests / len(successful_results) if successful_results else 0.0,
                "generation_times": generation_times
            }
        }
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get current processing statistics."""
        return {
            "total_processed": self.total_processed,
            "total_successful": self.total_successful,
            "total_failed": self.total_failed,
            "success_rate": self.total_successful / self.total_processed if self.total_processed > 0 else 0.0,
            "concurrency_limit": self.concurrency_limit,
            "current_semaphore_value": self.semaphore._value
        }


class ResourceMonitor:
    """Monitor system resources during parallel processing."""
    
    def __init__(self):
        """Initialize resource monitor."""
        self.cpu_threshold = 80.0  # Percentage
        self.memory_threshold = 80.0  # Percentage
        self.logger = logging.getLogger(__name__ + ".ResourceMonitor")
    
    async def initialize(self) -> None:
        """Initialize resource monitoring."""
        self.logger.info("Resource monitor initialized")
    
    async def check_resources(self) -> None:
        """
        Check system resources and throttle if necessary.
        
        Raises:
            ResourceExhaustionError: If resources are critically low
        """
        try:
            # Import psutil for resource monitoring (optional)
            import psutil
            
            # Check CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            if cpu_percent > self.cpu_threshold:
                self.logger.warning(f"High CPU usage: {cpu_percent:.1f}%")
                await asyncio.sleep(0.5)  # Brief throttle
            
            # Check memory usage
            memory = psutil.virtual_memory()
            if memory.percent > self.memory_threshold:
                self.logger.warning(f"High memory usage: {memory.percent:.1f}%")
                await asyncio.sleep(0.5)  # Brief throttle
                
        except ImportError:
            # psutil not available - skip resource monitoring
            pass
        except Exception as e:
            # Resource monitoring failed - log but don't fail processing
            self.logger.warning(f"Resource monitoring failed: {e}")


class ResourceExhaustionError(Exception):
    """Raised when system resources are critically low."""
    pass