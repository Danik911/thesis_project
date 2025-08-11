"""Simple test script for cross-validation components."""

import sys
import asyncio
from pathlib import Path

# Add main directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "main"))


def test_fold_manager():
    """Basic test of FoldManager."""
    try:
        from src.cross_validation.fold_manager import FoldManager
        
        fold_path = Path("datasets/cross_validation/fold_assignments.json")
        corpus_path = Path("datasets/urs_corpus")
        
        if not fold_path.exists():
            print(f"FAIL: Fold assignments not found: {fold_path}")
            return False
        
        if not corpus_path.exists():
            print(f"FAIL: URS corpus not found: {corpus_path}")
            return False
        
        # Test FoldManager initialization
        fold_manager = FoldManager(
            fold_assignments_path=fold_path,
            urs_corpus_path=corpus_path,
            random_seed=42
        )
        
        fold_count = fold_manager.get_fold_count()
        inventory = fold_manager.get_document_inventory()
        
        print(f"PASS: FoldManager initialized - {fold_count} folds, {len(inventory)} documents")
        
        # Test iteration
        folds_tested = 0
        for fold_id, train_docs, val_docs in fold_manager.iterate_folds():
            folds_tested += 1
            print(f"  Fold {fold_id}: {len(train_docs)} train, {len(val_docs)} validation")
            if folds_tested >= 2:  # Test first 2 folds
                break
        
        print("PASS: FoldManager basic functionality working")
        return True
        
    except Exception as e:
        print(f"FAIL: FoldManager test - {e}")
        return False


def test_metrics_collector():
    """Basic test of MetricsCollector."""
    try:
        from src.cross_validation.metrics_collector import MetricsCollector
        
        output_dir = Path("main/output/cross_validation/test")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        metrics = MetricsCollector(
            experiment_id="test_basic",
            output_directory=output_dir
        )
        
        # Test timer functionality
        timer_key = metrics.start_document_processing(
            document_id="URS-001",
            fold_id="fold_1",
            category_folder="category_3"
        )
        
        import time
        time.sleep(0.1)
        
        doc_metrics = metrics.stop_document_processing(
            timer_key=timer_key,
            success=True,
            prompt_tokens=1000,
            completion_tokens=500,
            tests_generated=3,
            coverage_percentage=80.0
        )
        
        print(f"PASS: MetricsCollector - {doc_metrics.wall_clock_seconds:.3f}s, ${doc_metrics.total_cost_usd:.4f}")
        
        # Clean up
        try:
            import shutil
            shutil.rmtree(output_dir / "test_basic_*.json", ignore_errors=True)
        except:
            pass
            
        return True
        
    except Exception as e:
        print(f"FAIL: MetricsCollector test - {e}")
        return False


async def test_workflow_imports():
    """Test that workflow can be imported."""
    try:
        from src.cross_validation.cross_validation_workflow import CrossValidationWorkflow
        from src.cross_validation.execution_harness import ExecutionHarness
        
        # Test basic initialization
        workflow = CrossValidationWorkflow(timeout=60, verbose=False, enable_phoenix=False)
        harness = ExecutionHarness(enable_phoenix=False)
        
        print("PASS: Workflow components import and initialize correctly")
        return True
        
    except Exception as e:
        print(f"FAIL: Workflow import test - {e}")
        return False


async def main():
    """Run basic tests."""
    print("Basic Cross-Validation Component Tests")
    print("=" * 40)
    
    tests_passed = 0
    total_tests = 3
    
    if test_fold_manager():
        tests_passed += 1
    
    if test_metrics_collector():
        tests_passed += 1
    
    if await test_workflow_imports():
        tests_passed += 1
    
    print("=" * 40)
    print(f"Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("SUCCESS: All basic tests passed!")
        return True
    else:
        print("FAILURE: Some tests failed")
        return False


if __name__ == "__main__":
    result = asyncio.run(main())