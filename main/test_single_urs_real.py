#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Single URS Document Cross-Validation Test

Tests the complete cross-validation workflow with a real URS document (URS-001)
to validate the testing framework before processing all 17 documents.

This script:
1. Loads URS-001.md from the corpus
2. Executes the complete UnifiedTestGenerationWorkflow  
3. Captures all outputs, metrics, and traces
4. Generates a results.json file with execution metrics
5. Validates GAMP-5 compliance and test generation

Usage:
    uv run python test_single_urs_real.py [--urs-id URS-001] [--skip-confirm]

Requirements:
    - DeepSeek V3 via OpenRouter (OPENROUTER_API_KEY)
    - Phoenix monitoring running (Docker)
    - ChromaDB with embedded regulatory documents
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

# Configure UTF-8 for Windows console
import sys
if sys.platform == "win32":
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except:
            pass

# Load environment first
from dotenv import load_dotenv
load_dotenv()

# Add main directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config.llm_config import LLMConfig
from src.core.unified_workflow import UnifiedTestGenerationWorkflow
from src.shared.output_manager import safe_print


def validate_environment() -> bool:
    """Validate environment setup and configuration."""
    
    safe_print("=" * 60)
    safe_print("[VALIDATION] Environment Setup Check")
    safe_print("=" * 60)
    
    errors = []
    warnings = []
    
    # Check API keys
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if not openrouter_key:
        errors.append("OPENROUTER_API_KEY environment variable missing")
    else:
        safe_print(f"[OK] OPENROUTER_API_KEY: {'*' * 20}...{openrouter_key[-4:]}")
    
    # Verify DeepSeek model configuration
    try:
        provider = LLMConfig.PROVIDER.value
        model = LLMConfig.MODELS[LLMConfig.PROVIDER]['model']
        safe_print(f"[OK] Model Provider: {provider}")
        safe_print(f"[OK] Model: {model}")
        
        # CRITICAL: Ensure only DeepSeek is used
        if model != "deepseek/deepseek-chat":
            errors.append(f"CRITICAL: Wrong model configured - {model}. Must use deepseek/deepseek-chat")
    except Exception as e:
        errors.append(f"Model configuration error: {e}")
    
    # Check Phoenix availability
    phoenix_port = os.getenv("PHOENIX_PORT", "6006")
    safe_print(f"[OK] Phoenix monitoring port: {phoenix_port}")
    
    # Check for critical paths
    main_dir = Path(__file__).parent
    urs_corpus = main_dir.parent / "datasets" / "urs_corpus"
    if not urs_corpus.exists():
        errors.append(f"URS corpus directory not found: {urs_corpus}")
    else:
        safe_print(f"[OK] URS corpus: {urs_corpus}")
    
    # Display results
    for warning in warnings:
        safe_print(f"[WARN] WARNING: {warning}")
    
    if errors:
        safe_print(f"\n[FAIL] VALIDATION FAILED:")
        for error in errors:
            safe_print(f"    - {error}")
        return False
    
    safe_print(f"\n[PASS] ENVIRONMENT VALIDATION PASSED")
    return True


def find_urs_document(urs_id: str) -> Optional[Path]:
    """Find the specified URS document in the corpus."""
    
    main_dir = Path(__file__).parent
    urs_corpus = main_dir.parent / "datasets" / "urs_corpus"
    
    # Search in all category folders
    for category_dir in urs_corpus.iterdir():
        if category_dir.is_dir():
            urs_file = category_dir / f"{urs_id}.md"
            if urs_file.exists():
                return urs_file
    
    return None


def create_output_directory(urs_id: str) -> Path:
    """Create timestamped output directory for test results."""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(__file__).parent / "output" / "cross_validation" / f"cv_test_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    return output_dir


async def execute_single_urs_test(urs_path: Path, output_dir: Path, verbose: bool = True) -> Dict[str, Any]:
    """
    Execute the complete workflow test on a single URS document.
    
    Args:
        urs_path: Path to the URS document
        output_dir: Output directory for results
        verbose: Enable verbose logging
        
    Returns:
        Dict containing execution results and metrics
    """
    
    safe_print("=" * 60)
    safe_print(f"[EXECUTION] Single URS Document Test: {urs_path.name}")
    safe_print("=" * 60)
    
    start_time = time.time()
    execution_start = datetime.now(timezone.utc)
    
    results = {
        "test_metadata": {
            "document_path": str(urs_path),
            "document_name": urs_path.name,
            "execution_start": execution_start.isoformat(),
            "output_directory": str(output_dir),
            "model_used": "deepseek/deepseek-chat",
            "test_type": "single_document_validation"
        },
        "execution_metrics": {},
        "workflow_results": {},
        "errors": [],
        "success": False
    }
    
    try:
        # Initialize the workflow
        safe_print(f"[INIT] Initializing UnifiedTestGenerationWorkflow...")
        
        workflow = UnifiedTestGenerationWorkflow(
            timeout=600,  # 10 minutes for single document
            verbose=verbose,
            enable_phoenix=True,  # Always enable Phoenix monitoring
            enable_parallel_coordination=True,  # Enable parallel agents
            enable_human_consultation=False  # Disable HITL for automated testing
        )
        
        safe_print(f"[INIT] Workflow initialized successfully")
        safe_print(f"[DOC] Processing document: {urs_path}")
        safe_print(f"[TIME] Start time: {execution_start.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        # Execute the workflow
        safe_print(f"\n[WORKFLOW] Starting document processing...")
        workflow_start = time.time()
        
        # Use document_path parameter as required by workflow
        workflow_result = await workflow.run(document_path=str(urs_path))
        
        workflow_end = time.time()
        workflow_duration = workflow_end - workflow_start
        
        safe_print(f"[WORKFLOW] Completed in {workflow_duration:.1f} seconds")
        
        # Process and analyze results
        if hasattr(workflow_result, 'result'):
            actual_result = workflow_result.result
        else:
            actual_result = workflow_result
            
        safe_print(f"[RESULT] Result type: {type(actual_result)}")
        
        # Extract meaningful metrics
        success = False
        categorization_info = {}
        oq_generation_info = {}
        error_details = None
        
        if isinstance(actual_result, dict):
            success = actual_result.get("status") != "failed"
            
            # Extract categorization results
            if "categorization" in actual_result:
                cat_result = actual_result["categorization"]
                categorization_info = {
                    "category": cat_result.get("category", "Unknown"),
                    "confidence": cat_result.get("confidence", 0.0),
                    "reasoning": cat_result.get("reasoning", ""),
                    "compliant": cat_result.get("gamp_compliant", False)
                }
                
            # Extract OQ generation results  
            if "oq_generation" in actual_result:
                oq_result = actual_result["oq_generation"]
                oq_generation_info = {
                    "total_tests": oq_result.get("total_tests", 0),
                    "coverage_percentage": oq_result.get("coverage_percentage", 0.0),
                    "test_suite_id": oq_result.get("suite_id", ""),
                    "generated_successfully": oq_result.get("total_tests", 0) > 0
                }
            
            # Check for errors
            if "error" in actual_result:
                error_details = actual_result["error"]
                
        else:
            success = actual_result is not None
            error_details = "Unexpected result format" if not success else None
        
        # Calculate final metrics
        execution_end = datetime.now(timezone.utc)
        total_duration = time.time() - start_time
        
        results.update({
            "execution_metrics": {
                "total_duration_seconds": round(total_duration, 2),
                "workflow_duration_seconds": round(workflow_duration, 2),
                "execution_end": execution_end.isoformat(),
                "peak_memory_usage": "Not measured",  # Could add memory monitoring
                "api_calls_made": "Not counted"  # Could add API call counting
            },
            "workflow_results": {
                "categorization": categorization_info,
                "oq_generation": oq_generation_info,
                "raw_result": actual_result if isinstance(actual_result, dict) else str(actual_result)
            },
            "success": success
        })
        
        if error_details:
            results["errors"].append(error_details)
        
        # Print execution summary
        safe_print("\n" + "=" * 60)
        safe_print("[SUMMARY] Execution Results")
        safe_print("=" * 60)
        safe_print(f"[STATUS] Success: {success}")
        safe_print(f"[TIMING] Total Duration: {total_duration:.1f} seconds")
        
        if categorization_info:
            safe_print(f"[GAMP] Category: {categorization_info.get('category', 'Unknown')}")
            safe_print(f"[GAMP] Confidence: {categorization_info.get('confidence', 0):.1%}")
            
        if oq_generation_info:
            safe_print(f"[TESTS] Generated: {oq_generation_info.get('total_tests', 0)}")
            safe_print(f"[TESTS] Coverage: {oq_generation_info.get('coverage_percentage', 0):.1%}")
            
        if error_details:
            safe_print(f"[ERROR] {error_details}")
            
        return results
        
    except Exception as e:
        execution_end = datetime.now(timezone.utc)
        total_duration = time.time() - start_time
        
        error_msg = str(e)
        safe_print(f"\n[ERROR] Workflow execution failed: {error_msg}")
        
        results.update({
            "execution_metrics": {
                "total_duration_seconds": round(total_duration, 2),
                "execution_end": execution_end.isoformat(),
                "failed": True
            },
            "errors": [error_msg],
            "success": False
        })
        
        if verbose:
            import traceback
            tb_str = traceback.format_exc()
            safe_print(f"[TRACEBACK]\n{tb_str}")
            results["errors"].append(f"Full traceback: {tb_str}")
        
        return results


def save_results(results: Dict[str, Any], output_dir: Path) -> Path:
    """Save execution results to JSON file."""
    
    results_file = output_dir / "results.json"
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    
    safe_print(f"[SAVE] Results saved to: {results_file}")
    return results_file


def print_final_summary(results: Dict[str, Any], results_file: Path):
    """Print final test summary."""
    
    safe_print("\n" + "=" * 60)
    safe_print("[FINAL] Cross-Validation Test Summary")
    safe_print("=" * 60)
    
    success = results.get("success", False)
    duration = results.get("execution_metrics", {}).get("total_duration_seconds", 0)
    
    if success:
        safe_print("[PASS] EXECUTION SUCCESS")
        
        categorization = results.get("workflow_results", {}).get("categorization", {})
        oq_generation = results.get("workflow_results", {}).get("oq_generation", {})
        
        if categorization:
            safe_print(f"[PASS] GAMP-5 Categorization: Category {categorization.get('category', '?')}")
            safe_print(f"[PASS] Confidence Level: {categorization.get('confidence', 0):.1%}")
            
        if oq_generation:
            test_count = oq_generation.get('total_tests', 0)
            safe_print(f"[PASS] OQ Tests Generated: {test_count}")
            safe_print(f"[PASS] Coverage Achieved: {oq_generation.get('coverage_percentage', 0):.1%}")
        else:
            safe_print("[WARN] No OQ tests generated")
            
    else:
        safe_print("[FAIL] EXECUTION FAILED")
        errors = results.get("errors", [])
        for error in errors[:3]:  # Show first 3 errors
            safe_print(f"[FAIL] Error: {error}")
    
    safe_print(f"[TIME] Duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")
    safe_print(f"[FILE] Results: {results_file}")
    
    safe_print("\n" + "=" * 60)
    
    if success:
        safe_print("[READY] Cross-validation framework is working - ready for full test")
    else:
        safe_print("[BLOCKED] Fix issues before running full cross-validation")


def parse_args():
    """Parse command line arguments."""
    
    parser = argparse.ArgumentParser(
        description="Single URS Document Cross-Validation Test",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Test with URS-001 (default)
    uv run python test_single_urs_real.py
    
    # Test with different URS document
    uv run python test_single_urs_real.py --urs-id URS-003
    
    # Skip confirmation prompt
    uv run python test_single_urs_real.py --skip-confirm
    
    # Quiet mode
    uv run python test_single_urs_real.py --quiet

Environment Requirements:
    OPENROUTER_API_KEY    - DeepSeek V3 API access
    PHOENIX_PORT         - Phoenix monitoring (default: 6006)
        """
    )
    
    parser.add_argument(
        "--urs-id", 
        default="URS-001",
        help="URS document ID to test (default: URS-001)"
    )
    
    parser.add_argument(
        "--skip-confirm",
        action="store_true", 
        help="Skip confirmation prompt and proceed directly"
    )
    
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Reduce output verbosity"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )
    
    return parser.parse_args()


async def main():
    """Main execution function."""
    
    args = parse_args()
    
    # Configure logging
    log_level = getattr(logging, args.log_level)
    logging.basicConfig(level=log_level, format="%(asctime)s - %(levelname)s - %(message)s")
    
    # Print header
    if not args.quiet:
        safe_print("GAMP-5 Cross-Validation Framework Test")
        safe_print(f"Testing with document: {args.urs_id}")
        safe_print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Validate environment
        if not validate_environment():
            safe_print("[ABORT] Environment validation failed")
            return 1
        
        # Find URS document
        urs_path = find_urs_document(args.urs_id)
        if not urs_path:
            safe_print(f"[ERROR] URS document not found: {args.urs_id}")
            safe_print(f"[HINT] Check that {args.urs_id}.md exists in the URS corpus")
            return 1
        
        safe_print(f"[FOUND] Document: {urs_path}")
        
        # Confirmation prompt (unless skipped)
        if not args.skip_confirm:
            response = input(f"\nProceed with test execution? This will make API calls (~$0.05). [y/N]: ")
            if response.lower() not in ['y', 'yes']:
                safe_print("[ABORT] Test cancelled by user")
                return 0
        
        # Create output directory
        output_dir = create_output_directory(args.urs_id)
        safe_print(f"[OUTPUT] Results will be saved to: {output_dir}")
        
        # Execute the test
        results = await execute_single_urs_test(
            urs_path=urs_path,
            output_dir=output_dir,
            verbose=not args.quiet
        )
        
        # Save results
        results_file = save_results(results, output_dir)
        
        # Print summary
        if not args.quiet:
            print_final_summary(results, results_file)
        
        # Return appropriate exit code
        return 0 if results.get("success", False) else 1
        
    except KeyboardInterrupt:
        safe_print("\n[INTERRUPT] Test cancelled by user")
        return 1
    except Exception as e:
        safe_print(f"\n[ERROR] Unexpected error: {e}")
        if not args.quiet:
            import traceback
            safe_print(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))