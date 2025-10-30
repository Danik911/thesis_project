#!/usr/bin/env python3
"""
Cross-Validation Execution Script for GAMP-5 Pharmaceutical Test Generation System

This script provides the main entry point for running cross-validation experiments
using the ExecutionHarness with proper error handling and comprehensive reporting.

Usage:
    python run_cross_validation.py [options]

Example:
    python run_cross_validation.py --experiment-id CV_TASK31_FINAL --folds 5 --documents 17 --verbose

Requirements:
    - OPENROUTER_API_KEY environment variable (for DeepSeek V3)
    - OPENAI_API_KEY environment variable (for embeddings)
    - Phoenix monitoring (optional, PHOENIX_PORT=6006)
"""

import argparse
import asyncio
import logging
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Add main directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.cross_validation.execution_harness import ExecutionHarness, run_cross_validation_experiment
from src.shared.output_manager import safe_print


def validate_environment():
    """
    Validate that all required environment variables and dependencies are available.
    
    Returns:
        bool: True if environment is valid
        
    Raises:
        RuntimeError: If critical dependencies are missing (no fallbacks)
    """
    errors = []
    warnings = []
    
    # Check API keys
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if not openrouter_key:
        errors.append("OPENROUTER_API_KEY environment variable not set (required for DeepSeek V3)")
    elif not openrouter_key.startswith("sk-or-v1-"):
        warnings.append(f"OPENROUTER_API_KEY format unexpected: {openrouter_key[:20]}...")
    
    openai_key = os.getenv("OPENAI_API_KEY") 
    if not openai_key:
        errors.append("OPENAI_API_KEY environment variable not set (required for embeddings)")
    elif not openai_key.startswith("sk-proj-"):
        warnings.append(f"OPENAI_API_KEY format unexpected: {openai_key[:20]}...")
    
    # Check Phoenix configuration
    phoenix_port = os.getenv("PHOENIX_PORT")
    if phoenix_port:
        safe_print(f"[CHECK] Phoenix monitoring configured on port {phoenix_port}")
    else:
        warnings.append("PHOENIX_PORT not set - Phoenix monitoring disabled")
    
    # Print warnings
    for warning in warnings:
        safe_print(f"[WARNING] {warning}")
    
    # Handle errors
    if errors:
        safe_print("[ERROR] Environment validation failed:")
        for error in errors:
            safe_print(f"  - {error}")
        raise RuntimeError("Critical environment variables missing - cannot proceed")
    
    safe_print("[SUCCESS] Environment validation passed")
    return True


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="GAMP-5 Cross-Validation Experiment Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Run full 5-fold cross-validation with 17 documents
    python run_cross_validation.py --folds 5 --documents 17
    
    # Run with custom experiment ID and increased parallelism
    python run_cross_validation.py --experiment-id CV_DEEPSEEK_TEST --parallel 2
    
    # Run single document test first
    python run_cross_validation.py --test-single-doc --verbose
    
Environment Variables Required:
    OPENROUTER_API_KEY    - DeepSeek V3 API key (sk-or-v1-...)
    OPENAI_API_KEY        - OpenAI API key for embeddings (sk-proj-...)
    PHOENIX_PORT          - Phoenix monitoring port (optional, default: 6006)
        """
    )
    
    # Experiment configuration
    parser.add_argument(
        "--experiment-id",
        type=str,
        help="Unique experiment identifier (auto-generated if not provided)"
    )
    
    parser.add_argument(
        "--folds",
        type=int,
        default=5,
        help="Number of folds for cross-validation (default: 5)"
    )
    
    parser.add_argument(
        "--documents",
        type=int,
        default=17,
        help="Expected number of documents to process (default: 17)"
    )
    
    parser.add_argument(
        "--parallel",
        type=int,
        default=1,
        help="Maximum parallel document processing (default: 1, max: 3)"
    )
    
    parser.add_argument(
        "--timeout",
        type=int,
        default=7200,
        help="Maximum execution time in seconds (default: 7200 = 2 hours)"
    )
    
    parser.add_argument(
        "--random-seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)"
    )
    
    # Testing options
    parser.add_argument(
        "--test-single-doc",
        action="store_true",
        help="Test with a single document first before full cross-validation"
    )
    
    parser.add_argument(
        "--disable-phoenix",
        action="store_true",
        help="Disable Phoenix observability monitoring"
    )
    
    # Paths (with defaults)
    parser.add_argument(
        "--fold-assignments",
        type=str,
        default="../datasets/cross_validation/fold_assignments.json",
        help="Path to fold assignments JSON file"
    )
    
    parser.add_argument(
        "--urs-corpus",
        type=str,
        default="../datasets/urs_corpus",
        help="Path to URS corpus directory"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default="output/cross_validation",
        help="Output directory for results"
    )
    
    # Logging
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )
    
    return parser.parse_args()


async def run_single_document_test(args):
    """
    Run a test with a single document to validate the system works.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        bool: True if test passed
    """
    safe_print("=" * 60)
    safe_print("[TEST] SINGLE DOCUMENT TEST")
    safe_print("=" * 60)
    
    try:
        # Use the unified workflow directly with a single test document
        from src.core.unified_workflow import UnifiedTestGenerationWorkflow
        
        test_doc_path = Path("tests/test_data/gamp5_test_data/testing_data.md")
        if not test_doc_path.exists():
            safe_print(f"[ERROR] Test document not found: {test_doc_path}")
            return False
        
        safe_print(f"[DOC] Testing with document: {test_doc_path}")
        
        # Initialize workflow
        workflow = UnifiedTestGenerationWorkflow(
            timeout=600,  # 10 minutes for single test
            verbose=args.verbose,
            enable_phoenix=not args.disable_phoenix,
            enable_parallel_coordination=True,
            enable_human_consultation=False
        )
        
        start_time = datetime.now(UTC)
        safe_print(f"[TIME] Starting single document test at {start_time.strftime('%H:%M:%S')}")
        
        # Run the workflow
        result = await workflow.run(document_path=str(test_doc_path))
        
        end_time = datetime.now(UTC)
        duration = (end_time - start_time).total_seconds()
        
        # Analyze results
        if hasattr(result, "result"):
            result = result.result
            
        success = isinstance(result, dict) and result.get("status") != "failed"
        
        safe_print(f"[TIME] Test completed in {duration:.1f} seconds")
        safe_print(f"[RESULT] Success: {success}")
        
        if success:
            categorization = result.get("categorization", {})
            if categorization:
                safe_print(f"[METRICS] GAMP Category: {categorization.get('category', 'Unknown')}")
                safe_print(f"[METRICS] Confidence: {categorization.get('confidence', 0):.1%}")
            
            oq_generation = result.get("oq_generation", {})
            if oq_generation:
                safe_print(f"[METRICS] Tests Generated: {oq_generation.get('total_tests', 0)}")
                safe_print(f"[METRICS] Coverage: {oq_generation.get('coverage_percentage', 0):.1%}")
        else:
            error_msg = result.get("error", "Unknown error") if isinstance(result, dict) else "Workflow failed"
            safe_print(f"[ERROR] Test failed: {error_msg}")
        
        safe_print("=" * 60)
        
        if success:
            safe_print("[SUCCESS] SINGLE DOCUMENT TEST PASSED - System is working")
            safe_print("[INFO] Proceeding to full cross-validation...")
        else:
            safe_print("[FAILURE] SINGLE DOCUMENT TEST FAILED")
            safe_print("[INFO] Fix issues before running full cross-validation")
        
        return success
        
    except Exception as e:
        safe_print(f"[ERROR] Single document test failed with exception: {e}")
        if args.verbose:
            import traceback
            safe_print(traceback.format_exc())
        return False


async def run_full_cross_validation(args):
    """
    Run the complete cross-validation experiment.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        dict: Experiment results
    """
    safe_print("=" * 60)
    safe_print("[EXPERIMENT] FULL CROSS-VALIDATION EXPERIMENT")
    safe_print("=" * 60)
    
    # Validate paths exist
    fold_assignments_path = Path(args.fold_assignments)
    urs_corpus_path = Path(args.urs_corpus)
    output_dir = Path(args.output_dir)
    
    if not fold_assignments_path.exists():
        raise FileNotFoundError(f"Fold assignments not found: {fold_assignments_path}")
    if not urs_corpus_path.exists():
        raise FileNotFoundError(f"URS corpus not found: {urs_corpus_path}")
    
    safe_print(f"[PATH] Fold assignments: {fold_assignments_path}")
    safe_print(f"[PATH] URS corpus: {urs_corpus_path}")
    safe_print(f"[PATH] Output directory: {output_dir}")
    safe_print(f"[CONFIG] Expected {args.documents} documents across {args.folds} folds")
    safe_print(f"[CONFIG] Parallel processing: {args.parallel} documents")
    safe_print(f"[CONFIG] Timeout: {args.timeout/60:.0f} minutes")
    
    # Run the experiment using ExecutionHarness
    experiment_results = await run_cross_validation_experiment(
        fold_assignments_path=fold_assignments_path,
        urs_corpus_path=urs_corpus_path,
        output_directory=output_dir,
        experiment_id=args.experiment_id,
        random_seed=args.random_seed,
        max_parallel_documents=args.parallel,
        timeout_seconds=args.timeout,
        enable_phoenix=not args.disable_phoenix,
        log_level=args.log_level if args.verbose else "WARNING"
    )
    
    return experiment_results


def print_final_results(results: dict, start_time: datetime):
    """
    Print comprehensive final results.
    
    Args:
        results: Experiment results dictionary
        start_time: Experiment start time
    """
    safe_print("=" * 60)
    safe_print("[RESULTS] FINAL CROSS-VALIDATION RESULTS")
    safe_print("=" * 60)
    
    end_time = datetime.now(UTC)
    total_duration = (end_time - start_time).total_seconds()
    
    status = results.get("status", "unknown")
    if status == "completed":
        safe_print("[SUCCESS] EXPERIMENT COMPLETED SUCCESSFULLY")
    elif status == "failed":
        safe_print("[FAILURE] EXPERIMENT FAILED")
        error = results.get("error", "Unknown error")
        safe_print(f"[ERROR] Error: {error}")
    else:
        safe_print(f"[STATUS] EXPERIMENT STATUS: {status}")
    
    # Summary metrics
    summary = results.get("summary", {})
    if summary:
        safe_print(f"\n[METRICS] Summary Metrics:")
        safe_print(f"   - Total Folds: {summary.get('total_folds', 0)}")
        safe_print(f"   - Total Documents: {summary.get('total_documents', 0)}")
        safe_print(f"   - Success Rate: {summary.get('overall_success_rate', 0):.1f}%")
        safe_print(f"   - Total Cost: ${summary.get('total_cost_usd', 0):.2f}")
        
        if summary.get('metrics_file'):
            safe_print(f"   - Metrics File: {summary['metrics_file']}")
    
    # Timing information
    execution_meta = results.get("execution_metadata", {})
    if execution_meta:
        experiment_duration = execution_meta.get("total_duration_seconds", 0)
        safe_print(f"\n[TIMING] Timing:")
        safe_print(f"   - Experiment Duration: {experiment_duration/60:.1f} minutes")
        safe_print(f"   - Total Script Duration: {total_duration/60:.1f} minutes")
        
        if execution_meta.get("log_file"):
            safe_print(f"   - Log File: {execution_meta['log_file']}")
    
    # Fold breakdown
    fold_results = results.get("fold_results", {})
    if fold_results:
        safe_print(f"\n[FOLDS] Per-Fold Results:")
        for fold_id, fold_result in fold_results.items():
            success_rate = (fold_result.successful_documents / fold_result.total_documents * 100) if fold_result.total_documents > 0 else 0
            safe_print(f"   - {fold_id}: {fold_result.successful_documents}/{fold_result.total_documents} docs ({success_rate:.1f}%)")
    
    # Files generated
    structured_logs = results.get("structured_logs", {})
    if structured_logs:
        safe_print(f"\n[FILES] Generated Files:")
        for log_type, log_path in structured_logs.items():
            if log_path:
                safe_print(f"   - {log_type}: {log_path}")
    
    safe_print("=" * 60)
    
    # Final recommendations
    if status == "completed":
        success_rate = summary.get("overall_success_rate", 0)
        if success_rate >= 80:
            safe_print("[EXCELLENT] Cross-validation completed with high success rate!")
        elif success_rate >= 60:
            safe_print("[GOOD] Cross-validation completed with acceptable success rate")
        else:
            safe_print("[WARNING] Low success rate - system may need improvements")
    else:
        safe_print("[RECOMMENDATION] Check logs for detailed error analysis")


async def main():
    """Main entry point for cross-validation execution."""
    args = parse_arguments()
    start_time = datetime.now(UTC)
    
    # Configure logging
    log_level = getattr(logging, args.log_level)
    logging.basicConfig(level=log_level, format="%(asctime)s - %(levelname)s - %(message)s")
    
    # Print header
    safe_print("GAMP-5 Pharmaceutical Cross-Validation System")
    safe_print(f"Starting experiment at {start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    safe_print("=" * 60)
    
    try:
        # Validate environment
        validate_environment()
        
        # Run single document test first if requested
        if args.test_single_doc:
            single_test_passed = await run_single_document_test(args)
            if not single_test_passed:
                safe_print("[ABORT] Single document test failed - aborting cross-validation")
                return 1
            safe_print()
        
        # Run full cross-validation
        results = await run_full_cross_validation(args)
        
        # Print final results
        print_final_results(results, start_time)
        
        # Determine exit code
        status = results.get("status", "failed")
        if status == "completed":
            success_rate = results.get("summary", {}).get("overall_success_rate", 0)
            return 0 if success_rate > 0 else 1
        else:
            return 1
    
    except KeyboardInterrupt:
        safe_print("\n[INTERRUPT] Cross-validation interrupted by user")
        return 1
    except Exception as e:
        safe_print(f"\n[ERROR] Cross-validation failed: {e}")
        if args.verbose:
            import traceback
            safe_print(traceback.format_exc())
        return 1
    finally:
        end_time = datetime.now(UTC)
        total_time = (end_time - start_time).total_seconds()
        safe_print(f"\n[TIMING] Total execution time: {total_time/60:.1f} minutes")


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))