"""
Batch Execution Manager for Cross-Validation Framework

This module provides batch processing capabilities to prevent timeouts
during cross-validation of pharmaceutical test generation systems.

Key Features:
- Process documents in configurable batch sizes
- Timeout protection per document
- Checkpoint and resume capability
- Progress tracking with OQ-TRACE logs
- Resource monitoring and cleanup
- No fallbacks - explicit error handling
"""

import asyncio
import logging
import time
from datetime import datetime, UTC
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import psutil
import tracemalloc

from .fold_manager import URSDocument
from .structured_logger import StructuredLogger

logger = logging.getLogger(__name__)


class BatchCrossValidationExecutor:
    """
    Batch executor for cross-validation to prevent timeouts.
    
    Processes documents in batches with comprehensive monitoring
    and checkpoint capabilities for recovery.
    """
    
    def __init__(
        self,
        batch_size: int = 3,
        timeout_per_doc: int = 600,
        checkpoint_dir: Optional[Path] = None,
        enable_monitoring: bool = True
    ):
        """
        Initialize the BatchCrossValidationExecutor.
        
        Args:
            batch_size: Number of documents to process concurrently
            timeout_per_doc: Maximum seconds per document processing
            checkpoint_dir: Directory for saving checkpoints
            enable_monitoring: Enable resource monitoring
        """
        self.batch_size = batch_size
        self.timeout_per_doc = timeout_per_doc
        self.enable_monitoring = enable_monitoring
        
        # Setup checkpoint directory
        if checkpoint_dir:
            self.checkpoint_dir = Path(checkpoint_dir)
            self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        else:
            self.checkpoint_dir = Path("checkpoints")
            self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
            
        # Initialize structured logger
        self.structured_logger = StructuredLogger(
            experiment_id=f"batch_cv_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}",
            output_directory=self.checkpoint_dir / "logs"
        )
        
        # Execution state
        self.current_batch = 0
        self.total_batches = 0
        self.processed_documents = set()
        self.failed_documents = set()
        self.batch_results = []
        
        # Resource monitoring
        if self.enable_monitoring:
            tracemalloc.start()
            self.process = psutil.Process()
            self.initial_memory = self._get_memory_usage()
            
        logger.info(f"[OQ-TRACE] BatchCrossValidationExecutor initialized")
        logger.info(f"[OQ-BATCH] Configuration: batch_size={batch_size}, timeout={timeout_per_doc}s")
        
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        return self.process.memory_info().rss / 1024 / 1024
        
    def _log_resource_usage(self, phase: str) -> None:
        """Log resource usage at different phases."""
        if not self.enable_monitoring:
            return
            
        current_memory = self._get_memory_usage()
        delta = current_memory - self.initial_memory
        logger.info(f"[OQ-RESOURCE] Memory at {phase}: {current_memory:.2f} MB (delta: {delta:+.2f} MB)")
        
    async def execute_fold_in_batches(
        self,
        fold_id: str,
        documents: List[URSDocument],
        workflow_executor: Any,
        resume_from_checkpoint: bool = False
    ) -> Dict[str, Any]:
        """
        Execute a fold's documents in batches to prevent timeouts.
        
        Args:
            fold_id: Identifier for the current fold
            documents: List of URSDocument objects to process
            workflow_executor: The workflow executor to use for processing
            resume_from_checkpoint: Whether to resume from saved checkpoint
            
        Returns:
            Dictionary containing batch execution results
        """
        start_time = time.time()
        
        # Load checkpoint if resuming
        if resume_from_checkpoint:
            self._load_checkpoint(fold_id)
            
        # Calculate batches
        total_docs = len(documents)
        self.total_batches = (total_docs + self.batch_size - 1) // self.batch_size
        
        logger.info(f"[OQ-BATCH] Fold {fold_id}: {total_docs} documents in {self.total_batches} batches")
        logger.info(f"[OQ-BATCH] Batch configuration: {total_docs} documents in batches of {self.batch_size}")
        
        # Process documents in batches
        for batch_num in range(self.current_batch, self.total_batches):
            batch_start = batch_num * self.batch_size
            batch_end = min(batch_start + self.batch_size, total_docs)
            batch_docs = documents[batch_start:batch_end]
            
            # Skip already processed documents
            batch_docs = [
                doc for doc in batch_docs 
                if doc.document_id not in self.processed_documents
            ]
            
            if not batch_docs:
                logger.info(f"[OQ-BATCH] Batch {batch_num + 1}/{self.total_batches} already processed, skipping")
                continue
                
            logger.info(f"[OQ-BATCH] Processing batch {batch_num + 1}/{self.total_batches}...")
            self._log_resource_usage(f"batch_{batch_num + 1}_start")
            
            # Process batch with timeout protection
            batch_result = await self._process_batch_with_timeout(
                fold_id,
                batch_num + 1,
                batch_docs,
                workflow_executor
            )
            
            self.batch_results.append(batch_result)
            
            # Update processed documents
            for doc in batch_docs:
                if doc.document_id in batch_result.get('successful_docs', []):
                    self.processed_documents.add(doc.document_id)
                elif doc.document_id in batch_result.get('failed_docs', []):
                    self.failed_documents.add(doc.document_id)
                    
            # Save checkpoint after each batch
            self.current_batch = batch_num + 1
            self._save_checkpoint(fold_id)
            
            # Log batch completion
            success_count = len(batch_result.get('successful_docs', []))
            fail_count = len(batch_result.get('failed_docs', []))
            logger.info(f"[OQ-BATCH] Batch {batch_num + 1} complete: {success_count} succeeded, {fail_count} failed")
            
            self._log_resource_usage(f"batch_{batch_num + 1}_complete")
            
            # Cleanup after batch
            await self._cleanup_batch_resources()
            
        # Calculate final metrics
        total_time = time.time() - start_time
        total_processed = len(self.processed_documents)
        total_failed = len(self.failed_documents)
        
        logger.info(f"[OQ-BATCH] Fold {fold_id} complete: {total_processed} documents processed in {total_time:.1f}s")
        logger.info(f"[OQ-BATCH] Generation summary: {self.total_batches} batches processed")
        
        if total_failed > 0:
            logger.warning(f"[OQ-BATCH] Failed documents: {total_failed}")
            
        self._log_resource_usage("fold_complete")
        
        return {
            'fold_id': fold_id,
            'total_documents': total_docs,
            'processed_documents': list(self.processed_documents),
            'failed_documents': list(self.failed_documents),
            'batch_results': self.batch_results,
            'total_time_seconds': total_time,
            'batches_processed': self.total_batches
        }
        
    async def _process_batch_with_timeout(
        self,
        fold_id: str,
        batch_num: int,
        documents: List[URSDocument],
        workflow_executor: Any
    ) -> Dict[str, Any]:
        """
        Process a batch of documents with timeout protection.
        
        Args:
            fold_id: Current fold identifier
            batch_num: Batch number for logging
            documents: Documents to process in this batch
            workflow_executor: Workflow executor instance
            
        Returns:
            Dictionary containing batch results
        """
        batch_start_time = time.time()
        successful_docs = []
        failed_docs = []
        
        # Create tasks for parallel processing
        tasks = []
        for doc in documents:
            task = asyncio.create_task(
                self._process_single_document_with_timeout(
                    doc,
                    workflow_executor,
                    fold_id
                )
            )
            tasks.append((doc.document_id, task))
            
        # Wait for all tasks with individual timeouts
        for doc_id, task in tasks:
            try:
                result = await task
                if result['success']:
                    successful_docs.append(doc_id)
                else:
                    failed_docs.append(doc_id)
                    logger.error(f"[OQ-BATCH] Document {doc_id} failed: {result.get('error', 'Unknown error')}")
            except asyncio.TimeoutError:
                failed_docs.append(doc_id)
                logger.error(f"[OQ-BATCH] Document {doc_id} timed out after {self.timeout_per_doc}s")
            except Exception as e:
                failed_docs.append(doc_id)
                logger.error(f"[OQ-BATCH] Document {doc_id} failed with exception: {str(e)}")
                
        batch_time = time.time() - batch_start_time
        
        return {
            'batch_num': batch_num,
            'successful_docs': successful_docs,
            'failed_docs': failed_docs,
            'batch_time_seconds': batch_time,
            'docs_per_second': len(documents) / batch_time if batch_time > 0 else 0
        }
        
    async def _process_single_document_with_timeout(
        self,
        document: URSDocument,
        workflow_executor: Any,
        fold_id: str
    ) -> Dict[str, Any]:
        """
        Process a single document with timeout protection.
        
        Args:
            document: URSDocument to process
            workflow_executor: Workflow executor instance
            fold_id: Current fold identifier
            
        Returns:
            Dictionary with processing results
        """
        try:
            # Add heartbeat logging for long operations
            heartbeat_task = asyncio.create_task(
                self._heartbeat_logger(document.document_id)
            )
            
            # Process document with timeout
            result = await asyncio.wait_for(
                workflow_executor.process_document(document, fold_id),
                timeout=self.timeout_per_doc
            )
            
            # Cancel heartbeat
            heartbeat_task.cancel()
            
            return {
                'success': True,
                'document_id': document.document_id,
                'result': result
            }
            
        except asyncio.TimeoutError:
            return {
                'success': False,
                'document_id': document.document_id,
                'error': f'Timeout after {self.timeout_per_doc}s'
            }
        except Exception as e:
            return {
                'success': False,
                'document_id': document.document_id,
                'error': str(e)
            }
            
    async def _heartbeat_logger(self, document_id: str) -> None:
        """
        Log heartbeat messages during long operations.
        
        Args:
            document_id: Document being processed
        """
        elapsed = 0
        interval = 10  # Log every 10 seconds
        
        try:
            while True:
                await asyncio.sleep(interval)
                elapsed += interval
                logger.info(f"[OQ-TRACE] ⏱️ Processing {document_id}... {elapsed}s elapsed")
        except asyncio.CancelledError:
            logger.info(f"[OQ-TRACE] 🎉 Document {document_id} processing complete!")
            
    async def _cleanup_batch_resources(self) -> None:
        """Clean up resources after batch processing."""
        if self.enable_monitoring:
            # Force garbage collection
            import gc
            gc.collect()
            
            # Log memory after cleanup
            self._log_resource_usage("batch_cleanup")
            
    def _save_checkpoint(self, fold_id: str) -> None:
        """
        Save checkpoint for recovery.
        
        Args:
            fold_id: Current fold identifier
        """
        checkpoint_file = self.checkpoint_dir / f"checkpoint_{fold_id}.json"
        
        checkpoint_data = {
            'fold_id': fold_id,
            'current_batch': self.current_batch,
            'total_batches': self.total_batches,
            'processed_documents': list(self.processed_documents),
            'failed_documents': list(self.failed_documents),
            'batch_results': self.batch_results,
            'timestamp': datetime.now(UTC).isoformat()
        }
        
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint_data, f, indent=2)
            
        logger.info(f"[OQ-BATCH] Checkpoint saved for fold {fold_id}")
        
    def _load_checkpoint(self, fold_id: str) -> bool:
        """
        Load checkpoint if it exists.
        
        Args:
            fold_id: Fold identifier to load checkpoint for
            
        Returns:
            True if checkpoint loaded, False otherwise
        """
        checkpoint_file = self.checkpoint_dir / f"checkpoint_{fold_id}.json"
        
        if not checkpoint_file.exists():
            return False
            
        try:
            with open(checkpoint_file, 'r') as f:
                checkpoint_data = json.load(f)
                
            self.current_batch = checkpoint_data['current_batch']
            self.total_batches = checkpoint_data['total_batches']
            self.processed_documents = set(checkpoint_data['processed_documents'])
            self.failed_documents = set(checkpoint_data['failed_documents'])
            self.batch_results = checkpoint_data['batch_results']
            
            logger.info(f"[OQ-BATCH] Checkpoint loaded for fold {fold_id}")
            logger.info(f"[OQ-BATCH] Resuming from batch {self.current_batch + 1}/{self.total_batches}")
            return True
            
        except Exception as e:
            logger.error(f"[OQ-BATCH] Failed to load checkpoint: {str(e)}")
            return False
            
    def reset(self) -> None:
        """Reset executor state for new fold."""
        self.current_batch = 0
        self.total_batches = 0
        self.processed_documents.clear()
        self.failed_documents.clear()
        self.batch_results.clear()
        
        if self.enable_monitoring:
            self.initial_memory = self._get_memory_usage()
            
        logger.info("[OQ-BATCH] Executor state reset for new fold")