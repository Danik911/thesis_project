"""
Cross-Validation Execution Script

This script demonstrates how to run the complete cross-validation framework
for the pharmaceutical test generation system.

Usage:
    python run_cross_validation.py [--experiment-id EXPERIMENT_ID] [--dry-run]
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime, UTC
from pathlib import Path

# Add main directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "main"))

from src.cross_validation.execution_harness import run_cross_validation_experiment


async def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Run cross-validation experiment")
    parser.add_argument("--experiment-id", help="Unique experiment identifier")
    parser.add_argument("--dry-run", action="store_true", help="Test setup without running full experiment")
    parser.add_argument("--max-parallel", type=int, default=2, help="Maximum parallel document processing")
    parser.add_argument("--timeout", type=int, default=3600, help="Timeout in seconds (default: 1 hour)")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    parser.add_argument("--disable-phoenix", action="store_true", help="Disable Phoenix monitoring")
    
    args = parser.parse_args()
    
    # Set up experiment parameters
    experiment_id = args.experiment_id or f"cv_exp_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"
    
    print(f"Starting Cross-Validation Experiment: {experiment_id}")
    print("=" * 60)
    print(f"Configuration:")
    print(f"  - Experiment ID: {experiment_id}")
    print(f"  - Max Parallel Docs: {args.max_parallel}")
    print(f"  - Timeout: {args.timeout}s")
    print(f"  - Log Level: {args.log_level}")
    print(f"  - Phoenix Monitoring: {not args.disable_phoenix}")
    print(f"  - Dry Run: {args.dry_run}")
    print()
    
    if args.dry_run:
        print("DRY RUN MODE - Testing setup only")
        print("=" * 60)
        
        # Test component initialization
        try:
            from src.cross_validation.fold_manager import FoldManager
            from src.cross_validation.metrics_collector import MetricsCollector
            from src.cross_validation.cross_validation_workflow import CrossValidationWorkflow
            
            # Test paths
            fold_path = Path("datasets/cross_validation/fold_assignments.json")
            corpus_path = Path("datasets/urs_corpus")
            output_path = Path("main/output/cross_validation")
            
            print(f"[CHECK] Fold assignments path: {fold_path} ({'exists' if fold_path.exists() else 'MISSING'})")
            print(f"[CHECK] URS corpus path: {corpus_path} ({'exists' if corpus_path.exists() else 'MISSING'})")
            print(f"[CHECK] Output directory: {output_path}")
            
            if not fold_path.exists() or not corpus_path.exists():
                print("\n[FAIL] Required paths missing - cannot proceed")
                return 1
            
            # Test component initialization
            fold_manager = FoldManager(fold_path, corpus_path)
            print(f"[PASS] FoldManager: {fold_manager.get_fold_count()} folds, {len(fold_manager.get_document_inventory())} documents")
            
            metrics_collector = MetricsCollector(experiment_id, output_path)
            print("[PASS] MetricsCollector initialized")
            
            workflow = CrossValidationWorkflow(timeout=60, enable_phoenix=False)
            print("[PASS] CrossValidationWorkflow initialized")
            
            print("\n[SUCCESS] Dry run successful - all components ready!")
            return 0
            
        except Exception as e:
            print(f"\n[FAIL] Dry run failed: {e}")
            return 1
    
    # Run full experiment
    try:
        print("Starting full cross-validation experiment...")
        print("=" * 60)
        
        results = await run_cross_validation_experiment(
            fold_assignments_path="datasets/cross_validation/fold_assignments.json",
            urs_corpus_path="datasets/urs_corpus",
            output_directory="main/output/cross_validation",
            experiment_id=experiment_id,
            random_seed=42,
            max_parallel_documents=args.max_parallel,
            timeout_seconds=args.timeout,
            enable_phoenix=not args.disable_phoenix,
            log_level=args.log_level
        )
        
        # Print results summary
        print("\n" + "=" * 60)
        print("EXPERIMENT COMPLETED SUCCESSFULLY")
        print("=" * 60)
        
        summary = results.get("summary", {})
        print(f"Experiment ID: {results.get('experiment_id', 'unknown')}")
        print(f"Total Folds: {summary.get('total_folds', 0)}")
        print(f"Total Documents: {summary.get('total_documents', 0)}")
        print(f"Overall Success Rate: {summary.get('overall_success_rate', 0):.1f}%")
        print(f"Total Cost: ${summary.get('total_cost_usd', 0):.2f}")
        print(f"Metrics File: {summary.get('metrics_file', 'Not saved')}")
        
        execution_meta = results.get("execution_metadata", {})
        if execution_meta.get("total_duration_seconds"):
            duration_min = execution_meta["total_duration_seconds"] / 60
            print(f"Total Duration: {duration_min:.1f} minutes")
        
        # Save summary to file
        summary_file = Path("main/output/cross_validation") / f"{experiment_id}_summary.json"
        summary_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"Summary saved to: {summary_file}")
        
        return 0
        
    except Exception as e:
        print(f"\n[FAIL] Experiment failed: {e}")
        print("\nCheck the log files for detailed error information.")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))