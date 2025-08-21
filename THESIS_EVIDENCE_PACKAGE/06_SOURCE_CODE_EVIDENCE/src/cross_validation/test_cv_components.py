"""
Test Script for Cross-Validation Components

This script provides basic validation of the cross-validation framework
components to ensure they work correctly before running full experiments.

Usage:
    python -m src.cross_validation.test_cv_components
"""

import asyncio
import logging
from pathlib import Path

from .fold_manager import FoldManager
from .metrics_collector import MetricsCollector


async def test_fold_manager():
    """Test the FoldManager component."""

    try:
        # Initialize with project paths
        fold_assignments_path = Path("datasets/cross_validation/fold_assignments.json")
        urs_corpus_path = Path("datasets/urs_corpus")

        # Check if paths exist
        if not fold_assignments_path.exists():
            return False

        if not urs_corpus_path.exists():
            return False

        # Initialize FoldManager
        fold_manager = FoldManager(
            fold_assignments_path=fold_assignments_path,
            urs_corpus_path=urs_corpus_path,
            random_seed=42
        )

        # Test basic functionality
        fold_manager.get_fold_count()
        fold_manager.get_document_inventory()


        # Test fold iteration
        fold_counter = 0
        total_train_docs = 0
        total_val_docs = 0

        for _fold_id, train_docs, val_docs in fold_manager.iterate_folds():
            fold_counter += 1
            total_train_docs += len(train_docs)
            total_val_docs += len(val_docs)


            # Test document loading
            if val_docs:
                val_docs[0]


        # Verify each document appears exactly once in validation
        all_val_docs = []
        for _fold_id, _, val_docs in fold_manager.iterate_folds():
            all_val_docs.extend([doc.document_id for doc in val_docs])

        unique_val_docs = set(all_val_docs)
        if len(all_val_docs) == len(unique_val_docs):
            pass
        else:
            return False

        return True

    except Exception:
        return False


def test_metrics_collector():
    """Test the MetricsCollector component."""

    try:
        # Initialize MetricsCollector
        output_dir = Path("main/output/cross_validation/test")
        output_dir.mkdir(parents=True, exist_ok=True)

        metrics_collector = MetricsCollector(
            experiment_id="test_experiment",
            output_directory=output_dir,
            model_name="deepseek/deepseek-chat"
        )


        # Test document timing
        timer_key = metrics_collector.start_document_processing(
            document_id="URS-001",
            fold_id="fold_1",
            category_folder="category_3"
        )


        # Simulate processing time
        import time
        time.sleep(0.1)  # 100ms processing time

        # Complete document processing
        metrics_collector.stop_document_processing(
            timer_key=timer_key,
            success=True,
            prompt_tokens=1500,
            completion_tokens=800,
            tests_generated=5,
            coverage_percentage=85.0,
            gamp_category=3,
            confidence_score=0.92
        )


        # Test fold processing
        metrics_collector.start_fold_processing("fold_1")

        # Add another document
        timer_key_2 = metrics_collector.start_document_processing(
            document_id="URS-002",
            fold_id="fold_1",
            category_folder="category_4"
        )

        time.sleep(0.05)

        metrics_collector.stop_document_processing(
            timer_key=timer_key_2,
            success=False,
            error_message="Test error",
            error_type="TestError",
            prompt_tokens=1200,
            completion_tokens=0
        )

        # Complete fold
        metrics_collector.complete_fold_processing("fold_1")

        # Finalize experiment
        metrics_collector.finalize_experiment()

        # Test metrics saving
        metrics_file = metrics_collector.save_metrics("test_metrics")

        # Verify file exists and is valid JSON
        if metrics_file.exists():
            import json
            with open(metrics_file, encoding="utf-8") as f:
                json.load(f)
        else:
            return False

        # Clean up test file
        metrics_file.unlink()

        return True

    except Exception:
        return False


async def test_workflow_integration():
    """Test basic workflow integration."""

    try:
        from .cross_validation_workflow import CrossValidationWorkflow

        # Just test workflow initialization
        CrossValidationWorkflow(
            timeout=60,
            verbose=False,
            enable_phoenix=False,  # Disable for testing
            max_parallel_documents=1
        )


        return True

    except Exception:
        return False


async def main():
    """Run all component tests."""

    # Configure logging for tests
    logging.basicConfig(level=logging.WARNING)

    tests_passed = 0
    total_tests = 3

    # Test FoldManager
    if await test_fold_manager():
        tests_passed += 1

    # Test MetricsCollector
    if test_metrics_collector():
        tests_passed += 1

    # Test workflow integration
    if await test_workflow_integration():
        tests_passed += 1


    return tests_passed == total_tests


if __name__ == "__main__":
    import sys

    result = asyncio.run(main())
    sys.exit(0 if result else 1)
