#!/usr/bin/env python3
"""
Single URS Document Real API Test

This script tests the cross-validation framework with a single real URS document,
making actual API calls to validate the complete pipeline integration.

Usage:
    python test_single_urs_real.py [--urs-id URS-001]

This will cost approximately $0.01-0.05 in API calls.
"""

import asyncio
import json
import logging
import sys
import time
from datetime import datetime, UTC
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables FIRST
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

# Add main directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "main"))

from src.core.unified_workflow import UnifiedTestGenerationWorkflow
from src.cross_validation.metrics_collector import MetricsCollector
from src.cross_validation.coverage_analyzer import CoverageAnalyzer
from src.cross_validation.quality_metrics import QualityMetrics
from src.monitoring.phoenix_config import setup_phoenix

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SingleDocumentTester:
    """Test harness for single document validation with real API calls."""
    
    def __init__(self, urs_id: str = "URS-001"):
        """Initialize the tester with a specific URS document."""
        self.urs_id = urs_id
        self.urs_path = self._find_urs_document(urs_id)
        self.output_dir = Path("main/output/single_doc_test")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.metrics_collector = MetricsCollector(
            experiment_id=f"single_test_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}",
            output_directory=self.output_dir
        )
        self.coverage_analyzer = CoverageAnalyzer()
        self.quality_metrics = QualityMetrics()
        
        logger.info(f"Initialized SingleDocumentTester for {urs_id}")
        logger.info(f"URS Path: {self.urs_path}")
        logger.info(f"Output Directory: {self.output_dir}")
    
    def _find_urs_document(self, urs_id: str) -> Path:
        """Find the URS document in the corpus."""
        corpus_path = Path("datasets/urs_corpus")
        
        # Search in all category folders
        for category_dir in corpus_path.iterdir():
            if category_dir.is_dir():
                urs_file = category_dir / f"{urs_id}.md"
                if urs_file.exists():
                    return urs_file
        
        raise FileNotFoundError(f"URS document {urs_id} not found in corpus")
    
    async def run_test(self) -> Dict[str, Any]:
        """
        Run the complete test with real API call.
        
        Returns:
            Test results including metrics, timing, and validation status
        """
        logger.info("=" * 60)
        logger.info("STARTING SINGLE DOCUMENT REAL API TEST")
        logger.info("=" * 60)
        
        results = {
            "urs_id": self.urs_id,
            "timestamp": datetime.now(UTC).isoformat(),
            "status": "unknown",
            "metrics": {},
            "validation": {},
            "errors": []
        }
        
        try:
            # Step 1: Load URS document
            logger.info(f"\n[1/5] Loading URS document: {self.urs_id}")
            with open(self.urs_path, 'r', encoding='utf-8') as f:
                urs_content = f.read()
            logger.info(f"✅ Loaded {len(urs_content)} characters")
            
            # Step 2: Initialize workflow with Phoenix monitoring
            logger.info("\n[2/5] Initializing UnifiedTestGenerationWorkflow")
            setup_phoenix()  # Enable observability
            workflow = UnifiedTestGenerationWorkflow(timeout=300)
            logger.info("✅ Workflow initialized with 5-minute timeout")
            
            # Step 3: Start metrics collection
            logger.info("\n[3/5] Starting metrics collection")
            timer_key = self.metrics_collector.start_document_processing(
                document_id=self.urs_id,
                fold_id="test_fold",
                category_folder=self.urs_path.parent.name
            )
            start_time = time.perf_counter()
            
            # Step 4: Run workflow with REAL API CALL
            logger.info("\n[4/5] 🚀 EXECUTING WORKFLOW WITH REAL API CALL")
            logger.info("This will call DeepSeek API and incur costs...")
            
            # The workflow expects document_path in the start event
            result = await workflow.run(
                document_path=str(self.urs_path)
            )
            
            end_time = time.perf_counter()
            processing_time = end_time - start_time
            
            logger.info(f"✅ Workflow completed in {processing_time:.2f} seconds")
            
            # Step 5: Validate results
            logger.info("\n[5/5] Validating results")
            
            # Check if we got a test suite
            if hasattr(result, 'test_suite') and result.test_suite:
                test_suite = result.test_suite
                num_tests = len(test_suite.get('test_cases', []))
                logger.info(f"✅ Generated {num_tests} test cases")
                
                # Save test suite
                test_suite_path = self.output_dir / f"test_suite_{self.urs_id}_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.json"
                with open(test_suite_path, 'w', encoding='utf-8') as f:
                    json.dump(test_suite, f, indent=2, default=str)
                logger.info(f"✅ Test suite saved to {test_suite_path}")
                
                results["validation"]["test_count"] = num_tests
                results["validation"]["test_suite_path"] = str(test_suite_path)
            else:
                logger.warning("⚠️ No test suite generated")
                results["errors"].append("No test suite in result")
            
            # Check GAMP category
            if hasattr(result, 'gamp_category'):
                logger.info(f"✅ GAMP Category: {result.gamp_category}")
                results["validation"]["gamp_category"] = result.gamp_category
            
            # Check confidence score
            if hasattr(result, 'confidence_score'):
                logger.info(f"✅ Confidence Score: {result.confidence_score:.2f}")
                results["validation"]["confidence_score"] = result.confidence_score
            
            # End metrics collection
            doc_metrics = self.metrics_collector.end_document_processing(
                timer_key=timer_key,
                success=True,
                prompt_tokens=getattr(result, 'prompt_tokens', 0),
                completion_tokens=getattr(result, 'completion_tokens', 0),
                gamp_category=getattr(result, 'gamp_category', 'unknown'),
                confidence_score=getattr(result, 'confidence_score', 0.0),
                test_count=len(test_suite.get('test_cases', [])) if 'test_suite' in locals() else 0
            )
            
            # Calculate cost (DeepSeek V3 pricing)
            total_tokens = doc_metrics.prompt_tokens + doc_metrics.completion_tokens
            cost_usd = self.metrics_collector.calculate_cost(total_tokens)
            
            # Populate results
            results["metrics"] = {
                "processing_time_seconds": processing_time,
                "prompt_tokens": doc_metrics.prompt_tokens,
                "completion_tokens": doc_metrics.completion_tokens,
                "total_tokens": total_tokens,
                "cost_usd": cost_usd,
                "tokens_per_second": total_tokens / processing_time if processing_time > 0 else 0
            }
            
            results["status"] = "success"
            
            # Performance analysis
            logger.info("\n" + "=" * 60)
            logger.info("PERFORMANCE METRICS")
            logger.info("=" * 60)
            logger.info(f"Processing Time: {processing_time:.2f} seconds")
            logger.info(f"Total Tokens: {total_tokens:,}")
            logger.info(f"Cost: ${cost_usd:.4f}")
            logger.info(f"Tokens/Second: {results['metrics']['tokens_per_second']:.1f}")
            
            # Coverage analysis (if requirements can be extracted)
            if 'test_suite' in locals():
                logger.info("\n" + "=" * 60)
                logger.info("COVERAGE ANALYSIS")
                logger.info("=" * 60)
                
                # Extract requirements from URS
                requirements = self.coverage_analyzer.extract_requirements(urs_content)
                logger.info(f"Requirements Found: {len(requirements)}")
                
                # Map tests to requirements
                if requirements and test_suite:
                    mapping = self.coverage_analyzer.map_tests_to_requirements(
                        test_suite.get('test_cases', []),
                        requirements
                    )
                    coverage = self.coverage_analyzer.calculate_coverage(mapping)
                    logger.info(f"Coverage: {coverage:.1f}% (Target: ≥90%)")
                    
                    results["validation"]["requirements_count"] = len(requirements)
                    results["validation"]["coverage_percentage"] = coverage
                    
                    if coverage >= 90:
                        logger.info("✅ Coverage target MET")
                    else:
                        logger.warning(f"⚠️ Coverage below target: {coverage:.1f}% < 90%")
            
        except Exception as e:
            logger.error(f"❌ Test failed: {str(e)}")
            results["status"] = "failed"
            results["errors"].append(str(e))
            
            # Log full traceback for debugging
            import traceback
            logger.error(traceback.format_exc())
        
        finally:
            # Save final results
            results_path = self.output_dir / f"test_results_{self.urs_id}_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.json"
            with open(results_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, default=str)
            
            logger.info("\n" + "=" * 60)
            logger.info("TEST COMPLETE")
            logger.info("=" * 60)
            logger.info(f"Status: {results['status'].upper()}")
            logger.info(f"Results saved to: {results_path}")
            
            if results["status"] == "success":
                logger.info(f"✅ REAL API TEST PASSED - Cost: ${results['metrics']['cost_usd']:.4f}")
            else:
                logger.error(f"❌ REAL API TEST FAILED - Errors: {results['errors']}")
        
        return results


async def main():
    """Main entry point for the test."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test cross-validation with single URS document")
    parser.add_argument("--urs-id", default="URS-001", help="URS document ID to test")
    parser.add_argument("--skip-confirm", action="store_true", help="Skip cost confirmation")
    
    args = parser.parse_args()
    
    # Cost warning
    if not args.skip_confirm:
        print("\n" + "=" * 60)
        print("⚠️  COST WARNING")
        print("=" * 60)
        print("This test will make REAL API calls to DeepSeek V3")
        print("Estimated cost: $0.01 - $0.05")
        print("")
        response = input("Do you want to continue? (yes/no): ")
        if response.lower() != "yes":
            print("Test cancelled.")
            return
    
    # Run the test
    tester = SingleDocumentTester(urs_id=args.urs_id)
    results = await tester.run_test()
    
    # Exit with appropriate code
    sys.exit(0 if results["status"] == "success" else 1)


if __name__ == "__main__":
    asyncio.run(main())