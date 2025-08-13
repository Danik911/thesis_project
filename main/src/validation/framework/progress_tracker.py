#!/usr/bin/env python3
"""
Progress Tracker for Validation Framework

This module provides real-time progress tracking for the validation execution
framework, including document status tracking, fold completion monitoring,
ETA calculation, and comprehensive logging.

CRITICAL REQUIREMENTS:
- Real-time progress logging
- Document-level status tracking
- Fold completion monitoring
- ETA calculation with accuracy
- Integration with logging systems
- NO FALLBACK LOGIC - explicit status reporting only
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import logging
from enum import Enum


class DocumentStatus(str, Enum):
    """Status of document processing."""
    PENDING = "pending"
    PROCESSING = "processing" 
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class FoldStatus(str, Enum):
    """Status of fold processing."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"  # Some documents succeeded, some failed


@dataclass
class DocumentProgress:
    """Progress information for a single document."""
    document_id: str
    document_path: str
    status: DocumentStatus
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    processing_time: Optional[float] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    fold_number: int = 0


@dataclass
class FoldProgress:
    """Progress information for a single fold."""
    fold_number: int
    status: FoldStatus
    total_documents: int
    completed_documents: int
    failed_documents: int
    processing_documents: int
    pending_documents: int
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    document_progress: Dict[str, DocumentProgress] = None
    
    def __post_init__(self):
        if self.document_progress is None:
            self.document_progress = {}


@dataclass
class ExecutionProgress:
    """Overall execution progress across all folds."""
    execution_id: str
    total_folds: int
    completed_folds: int
    failed_folds: int
    in_progress_folds: int
    pending_folds: int
    overall_progress_percent: float
    start_time: datetime
    estimated_completion: Optional[datetime] = None
    fold_progress: Dict[int, FoldProgress] = None
    
    def __post_init__(self):
        if self.fold_progress is None:
            self.fold_progress = {}


class ProgressTracker:
    """
    Real-time progress tracker for validation execution framework.
    
    This tracker provides comprehensive progress monitoring including:
    - Document-level status tracking
    - Fold-level progress monitoring  
    - Overall execution progress
    - ETA calculation and updates
    - Real-time logging and status updates
    """
    
    def __init__(self, validation_config):
        """
        Initialize the progress tracker.
        
        Args:
            validation_config: Validation execution configuration
        """
        self.validation_config = validation_config
        self.logger = logging.getLogger(__name__)
        
        # Progress state
        self.execution_progress = None
        self.last_update_time = None
        self.progress_file_path = None
        
        # ETA calculation
        self.processing_rates = {}  # Documents per second by fold
        self.eta_window_size = 10  # Number of recent completions to use for ETA
        self.recent_completions = []  # Recent completion times for ETA calculation
        
        # Progress update callbacks
        self.progress_callbacks = []
        
        # Statistics
        self.total_documents_processed = 0
        self.total_processing_time = 0.0
    
    async def initialize(self, execution_id: str) -> None:
        """
        Initialize the progress tracker for a new execution.
        
        Args:
            execution_id: Unique identifier for this execution
            
        Raises:
            RuntimeError: If initialization fails
        """
        try:
            self.logger.info(f"Initializing ProgressTracker for execution: {execution_id}")
            
            # Create progress directory
            progress_dir = Path("logs/validation/progress")
            progress_dir.mkdir(parents=True, exist_ok=True)
            
            # Set progress file path
            self.progress_file_path = progress_dir / f"progress_{execution_id}.json"
            
            # Initialize execution progress (will be updated when execution starts)
            self.execution_progress = ExecutionProgress(
                execution_id=execution_id,
                total_folds=0,
                completed_folds=0,
                failed_folds=0,
                in_progress_folds=0,
                pending_folds=0,
                overall_progress_percent=0.0,
                start_time=datetime.now()
            )
            
            # Save initial progress
            await self._save_progress()
            
            self.logger.info(f"Progress tracker initialized - tracking to: {self.progress_file_path}")
            
        except Exception as e:
            raise RuntimeError(f"Failed to initialize progress tracker: {e!s}")
    
    async def start_execution(self, fold_range: List[int]) -> None:
        """
        Start tracking execution for the specified folds.
        
        Args:
            fold_range: List of fold numbers to be processed
        """
        try:
            self.logger.info(f"Starting execution tracking for folds: {fold_range}")
            
            # Update execution progress
            self.execution_progress.total_folds = len(fold_range)
            self.execution_progress.pending_folds = len(fold_range)
            self.execution_progress.start_time = datetime.now()
            
            # Initialize fold progress for each fold
            for fold_num in fold_range:
                self.execution_progress.fold_progress[fold_num] = FoldProgress(
                    fold_number=fold_num,
                    status=FoldStatus.NOT_STARTED,
                    total_documents=0,
                    completed_documents=0,
                    failed_documents=0,
                    processing_documents=0,
                    pending_documents=0
                )
            
            # Save updated progress
            await self._save_progress()
            
            self.logger.info(f"Execution tracking started for {len(fold_range)} folds")
            
        except Exception as e:
            self.logger.error(f"Failed to start execution tracking: {e!s}")
            raise RuntimeError(f"Failed to start execution tracking: {e!s}")
    
    async def start_fold(self, fold_number: int, total_documents: int) -> None:
        """
        Start tracking progress for a specific fold.
        
        Args:
            fold_number: Fold number being started
            total_documents: Total number of documents in this fold
        """
        try:
            self.logger.info(f"Starting fold {fold_number} with {total_documents} documents")
            
            if fold_number not in self.execution_progress.fold_progress:
                raise ValueError(f"Fold {fold_number} not initialized in execution tracking")
            
            # Update fold progress
            fold_progress = self.execution_progress.fold_progress[fold_number]
            fold_progress.status = FoldStatus.IN_PROGRESS
            fold_progress.total_documents = total_documents
            fold_progress.pending_documents = total_documents
            fold_progress.start_time = datetime.now()
            
            # Update execution-level counters
            self.execution_progress.in_progress_folds += 1
            self.execution_progress.pending_folds -= 1
            
            # Update overall progress
            await self._update_overall_progress()
            
            # Save progress
            await self._save_progress()
            
            self.logger.info(f"Fold {fold_number} tracking started")
            
        except Exception as e:
            self.logger.error(f"Failed to start fold tracking: {e!s}")
            raise RuntimeError(f"Failed to start fold tracking: {e!s}")
    
    async def start_document_processing(self, fold_number: int, document_id: str, document_path: str) -> None:
        """
        Mark a document as starting processing.
        
        Args:
            fold_number: Fold number containing the document
            document_id: Document identifier
            document_path: Path to the document
        """
        try:
            fold_progress = self.execution_progress.fold_progress[fold_number]
            
            # Create document progress entry
            doc_progress = DocumentProgress(
                document_id=document_id,
                document_path=document_path,
                status=DocumentStatus.PROCESSING,
                start_time=datetime.now(),
                fold_number=fold_number
            )
            
            fold_progress.document_progress[document_id] = doc_progress
            
            # Update fold counters
            fold_progress.processing_documents += 1
            fold_progress.pending_documents -= 1
            
            # Update overall progress
            await self._update_overall_progress()
            
            self.logger.debug(f"Document {document_id} in fold {fold_number} started processing")
            
        except Exception as e:
            self.logger.warning(f"Failed to track document start: {e}")
    
    async def complete_document_processing(
        self, 
        fold_number: int, 
        document_id: str, 
        success: bool,
        error_message: Optional[str] = None
    ) -> None:
        """
        Mark a document as completed processing.
        
        Args:
            fold_number: Fold number containing the document
            document_id: Document identifier
            success: Whether processing was successful
            error_message: Error message if processing failed
        """
        try:
            fold_progress = self.execution_progress.fold_progress[fold_number]
            
            if document_id not in fold_progress.document_progress:
                self.logger.warning(f"Document {document_id} not found in fold {fold_number} progress")
                return
            
            doc_progress = fold_progress.document_progress[document_id]
            
            # Update document progress
            doc_progress.end_time = datetime.now()
            doc_progress.status = DocumentStatus.COMPLETED if success else DocumentStatus.FAILED
            doc_progress.error_message = error_message
            
            if doc_progress.start_time:
                doc_progress.processing_time = (doc_progress.end_time - doc_progress.start_time).total_seconds()
                
                # Add to recent completions for ETA calculation
                self.recent_completions.append({
                    'completion_time': doc_progress.end_time,
                    'processing_time': doc_progress.processing_time
                })
                
                # Keep only recent completions for ETA
                if len(self.recent_completions) > self.eta_window_size:
                    self.recent_completions = self.recent_completions[-self.eta_window_size:]
            
            # Update fold counters
            fold_progress.processing_documents -= 1
            if success:
                fold_progress.completed_documents += 1
            else:
                fold_progress.failed_documents += 1
            
            # Update statistics
            self.total_documents_processed += 1
            if doc_progress.processing_time:
                self.total_processing_time += doc_progress.processing_time
            
            # Update overall progress and ETA
            await self._update_overall_progress()
            await self._update_eta_estimates()
            
            # Log progress update
            total_docs_in_fold = fold_progress.total_documents
            completed_in_fold = fold_progress.completed_documents + fold_progress.failed_documents
            progress_percent = (completed_in_fold / total_docs_in_fold * 100) if total_docs_in_fold > 0 else 0
            
            status_icon = "✅" if success else "❌"
            self.logger.info(
                f"Fold {fold_number} progress: {completed_in_fold}/{total_docs_in_fold} "
                f"({progress_percent:.1f}%) - Document {document_id} {status_icon}"
            )
            
            # Save progress
            await self._save_progress()
            
            # Notify callbacks
            await self._notify_progress_callbacks()
            
        except Exception as e:
            self.logger.warning(f"Failed to track document completion: {e}")
    
    async def complete_fold(self, fold_number: int, fold_result: Dict[str, Any]) -> None:
        """
        Mark a fold as completed.
        
        Args:
            fold_number: Fold number that completed
            fold_result: Results from fold processing
        """
        try:
            fold_progress = self.execution_progress.fold_progress[fold_number]
            
            # Update fold status
            fold_progress.end_time = datetime.now()
            
            # Determine fold status based on results
            if fold_result.get("success", False):
                fold_progress.status = FoldStatus.COMPLETED
                self.execution_progress.completed_folds += 1
            elif fold_progress.completed_documents > 0:
                fold_progress.status = FoldStatus.PARTIAL
                self.execution_progress.completed_folds += 1  # Count partial as completed
            else:
                fold_progress.status = FoldStatus.FAILED
                self.execution_progress.failed_folds += 1
            
            # Update execution counters
            self.execution_progress.in_progress_folds -= 1
            
            # Update overall progress
            await self._update_overall_progress()
            
            # Calculate fold processing rate
            if fold_progress.start_time and fold_progress.end_time:
                fold_time = (fold_progress.end_time - fold_progress.start_time).total_seconds()
                completed_docs = fold_progress.completed_documents
                if fold_time > 0 and completed_docs > 0:
                    self.processing_rates[fold_number] = completed_docs / fold_time
            
            # Save progress
            await self._save_progress()
            
            # Log fold completion
            self.logger.info(
                f"Fold {fold_number} completed: {fold_progress.status.value} - "
                f"{fold_progress.completed_documents} successful, "
                f"{fold_progress.failed_documents} failed"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to track fold completion: {e}")
            raise RuntimeError(f"Failed to track fold completion: {e!s}")
    
    async def _update_overall_progress(self) -> None:
        """Update overall execution progress percentage."""
        try:
            total_folds = self.execution_progress.total_folds
            if total_folds == 0:
                self.execution_progress.overall_progress_percent = 0.0
                return
            
            # Calculate progress based on fold completion
            completed = self.execution_progress.completed_folds
            failed = self.execution_progress.failed_folds
            in_progress = self.execution_progress.in_progress_folds
            
            # Weight in-progress folds based on document completion
            in_progress_weight = 0.0
            for fold_num, fold_progress in self.execution_progress.fold_progress.items():
                if fold_progress.status == FoldStatus.IN_PROGRESS:
                    if fold_progress.total_documents > 0:
                        fold_completion = (fold_progress.completed_documents + fold_progress.failed_documents) / fold_progress.total_documents
                        in_progress_weight += fold_completion
            
            # Calculate overall progress
            progress = ((completed + failed) + in_progress_weight) / total_folds
            self.execution_progress.overall_progress_percent = min(progress * 100, 100.0)
            
        except Exception as e:
            self.logger.warning(f"Failed to update overall progress: {e}")
    
    async def _update_eta_estimates(self) -> None:
        """Update estimated completion time based on recent processing rates."""
        try:
            if not self.recent_completions:
                return
            
            # Calculate average processing time from recent completions
            recent_times = [comp['processing_time'] for comp in self.recent_completions]
            avg_processing_time = sum(recent_times) / len(recent_times)
            
            # Estimate remaining work
            total_remaining_docs = 0
            for fold_progress in self.execution_progress.fold_progress.values():
                if fold_progress.status in [FoldStatus.NOT_STARTED, FoldStatus.IN_PROGRESS]:
                    remaining_in_fold = fold_progress.total_documents - fold_progress.completed_documents - fold_progress.failed_documents
                    total_remaining_docs += remaining_in_fold
            
            # Estimate completion time (considering parallel processing)
            if total_remaining_docs > 0 and avg_processing_time > 0:
                # Assume 3 documents can be processed in parallel
                parallel_factor = 3
                estimated_remaining_time = (total_remaining_docs * avg_processing_time) / parallel_factor
                
                self.execution_progress.estimated_completion = datetime.now() + timedelta(seconds=estimated_remaining_time)
            
            # Update fold-level ETAs
            for fold_progress in self.execution_progress.fold_progress.values():
                if fold_progress.status == FoldStatus.IN_PROGRESS:
                    remaining_in_fold = fold_progress.total_documents - fold_progress.completed_documents - fold_progress.failed_documents
                    if remaining_in_fold > 0 and avg_processing_time > 0:
                        fold_eta_seconds = (remaining_in_fold * avg_processing_time) / parallel_factor
                        fold_progress.estimated_completion = datetime.now() + timedelta(seconds=fold_eta_seconds)
            
        except Exception as e:
            self.logger.warning(f"Failed to update ETA estimates: {e}")
    
    async def _save_progress(self) -> None:
        """Save current progress to file."""
        try:
            if not self.progress_file_path:
                return
            
            # Convert progress to dict for JSON serialization
            progress_dict = asdict(self.execution_progress)
            
            # Save to file
            with open(self.progress_file_path, 'w', encoding='utf-8') as f:
                json.dump(progress_dict, f, indent=2, ensure_ascii=False, default=str)
            
            self.last_update_time = datetime.now()
            
        except Exception as e:
            self.logger.warning(f"Failed to save progress: {e}")
    
    async def _notify_progress_callbacks(self) -> None:
        """Notify registered progress callbacks."""
        for callback in self.progress_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(self.execution_progress)
                else:
                    callback(self.execution_progress)
            except Exception as e:
                self.logger.warning(f"Progress callback failed: {e}")
    
    def add_progress_callback(self, callback) -> None:
        """
        Add a progress callback function.
        
        Args:
            callback: Function to call with progress updates
        """
        self.progress_callbacks.append(callback)
    
    def get_current_progress(self) -> ExecutionProgress:
        """
        Get current execution progress.
        
        Returns:
            Current ExecutionProgress object
        """
        return self.execution_progress
    
    def get_fold_progress(self, fold_number: int) -> Optional[FoldProgress]:
        """
        Get progress for a specific fold.
        
        Args:
            fold_number: Fold number to get progress for
            
        Returns:
            FoldProgress object or None if not found
        """
        return self.execution_progress.fold_progress.get(fold_number)
    
    def get_document_progress(self, fold_number: int, document_id: str) -> Optional[DocumentProgress]:
        """
        Get progress for a specific document.
        
        Args:
            fold_number: Fold number containing the document
            document_id: Document identifier
            
        Returns:
            DocumentProgress object or None if not found
        """
        fold_progress = self.get_fold_progress(fold_number)
        if not fold_progress:
            return None
        
        return fold_progress.document_progress.get(document_id)
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """
        Get processing statistics.
        
        Returns:
            Dictionary containing processing statistics
        """
        avg_processing_time = self.total_processing_time / self.total_documents_processed if self.total_documents_processed > 0 else 0.0
        
        return {
            "total_documents_processed": self.total_documents_processed,
            "total_processing_time": self.total_processing_time,
            "average_processing_time": avg_processing_time,
            "processing_rates_by_fold": self.processing_rates.copy(),
            "recent_completions_count": len(self.recent_completions),
            "last_update_time": self.last_update_time.isoformat() if self.last_update_time else None
        }
    
    async def generate_progress_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive progress report.
        
        Returns:
            Dictionary containing comprehensive progress information
        """
        if not self.execution_progress:
            return {"error": "No execution in progress"}
        
        # Calculate execution time
        execution_time = (datetime.now() - self.execution_progress.start_time).total_seconds()
        
        # Estimate remaining time
        remaining_time = None
        if self.execution_progress.estimated_completion:
            remaining_time = (self.execution_progress.estimated_completion - datetime.now()).total_seconds()
            remaining_time = max(0, remaining_time)  # Don't show negative time
        
        report = {
            "execution_summary": {
                "execution_id": self.execution_progress.execution_id,
                "overall_progress_percent": self.execution_progress.overall_progress_percent,
                "execution_time_seconds": execution_time,
                "estimated_remaining_seconds": remaining_time,
                "estimated_completion": self.execution_progress.estimated_completion.isoformat() if self.execution_progress.estimated_completion else None
            },
            "fold_summary": {
                "total_folds": self.execution_progress.total_folds,
                "completed_folds": self.execution_progress.completed_folds,
                "failed_folds": self.execution_progress.failed_folds,
                "in_progress_folds": self.execution_progress.in_progress_folds,
                "pending_folds": self.execution_progress.pending_folds
            },
            "document_summary": {
                "total_documents": sum(fp.total_documents for fp in self.execution_progress.fold_progress.values()),
                "completed_documents": sum(fp.completed_documents for fp in self.execution_progress.fold_progress.values()),
                "failed_documents": sum(fp.failed_documents for fp in self.execution_progress.fold_progress.values()),
                "processing_documents": sum(fp.processing_documents for fp in self.execution_progress.fold_progress.values()),
                "pending_documents": sum(fp.pending_documents for fp in self.execution_progress.fold_progress.values())
            },
            "fold_details": {},
            "processing_statistics": self.get_processing_statistics()
        }
        
        # Add detailed fold information
        for fold_num, fold_progress in self.execution_progress.fold_progress.items():
            report["fold_details"][f"fold_{fold_num}"] = {
                "status": fold_progress.status.value,
                "progress_percent": (fold_progress.completed_documents + fold_progress.failed_documents) / fold_progress.total_documents * 100 if fold_progress.total_documents > 0 else 0,
                "completed_documents": fold_progress.completed_documents,
                "failed_documents": fold_progress.failed_documents,
                "total_documents": fold_progress.total_documents,
                "estimated_completion": fold_progress.estimated_completion.isoformat() if fold_progress.estimated_completion else None
            }
        
        return report