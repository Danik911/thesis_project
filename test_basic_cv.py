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


def test_environment_loading():
    """Test that environment variables are loaded correctly."""
    try:
        import os
        from dotenv import load_dotenv
        
        # Load environment variables first
        load_dotenv()
        
        # Test direct environment access
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            print("FAIL: OPENROUTER_API_KEY not found in environment")
            return False
        
        print(f"PASS: OPENROUTER_API_KEY found: {api_key[:10]}...{api_key[-4:]}")
        
        # Test LLMConfig import and initialization (should trigger dotenv loading)
        from src.config.llm_config import LLMConfig
        
        provider_info = LLMConfig.get_provider_info()
        if not provider_info['api_key_present']:
            print("FAIL: LLMConfig reports API key not present")
            return False
        
        print(f"PASS: LLMConfig provider: {provider_info['provider']}, API key present: {provider_info['api_key_present']}")
        
        # Test configuration validation
        is_valid, message = LLMConfig.validate_configuration()
        if not is_valid:
            print(f"FAIL: LLMConfig validation failed: {message}")
            return False
        
        print("PASS: LLMConfig validation successful")
        
        # Test LLM instance creation (this is where the original error occurred)
        try:
            llm = LLMConfig.get_llm()
            print(f"PASS: LLM instance created successfully: {type(llm).__name__}")
        except Exception as e:
            print(f"FAIL: LLM instance creation failed: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"FAIL: Environment loading test - {e}")
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
    total_tests = 4
    
    # Test environment loading FIRST (most critical for cross-validation)
    print("\n1. Testing Environment Variable Loading...")
    if test_environment_loading():
        tests_passed += 1
    
    print("\n2. Testing FoldManager...")
    if test_fold_manager():
        tests_passed += 1
    
    print("\n3. Testing MetricsCollector...")
    if test_metrics_collector():
        tests_passed += 1
    
    print("\n4. Testing Workflow Imports...")
    if await test_workflow_imports():
        tests_passed += 1
    
    print("\n" + "=" * 40)
    print(f"Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("✅ SUCCESS: All basic tests passed!")
        print("✅ Cross-validation environment fix is working correctly!")
        return True
    else:
        print("❌ FAILURE: Some tests failed")
        return False


if __name__ == "__main__":
    result = asyncio.run(main())