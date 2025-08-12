"""
Run Real Security Tests - ACTUAL System Testing

This script executes REAL security tests against the actual pharmaceutical
test generation system. NO SIMULATIONS OR MOCKS.

Key Features:
- Tests all 30 OWASP LLM scenarios against the real system
- Captures genuine vulnerabilities and metrics
- Reports honest results (even if <90% mitigation)
- Records actual Phoenix observability data
- Generates authentic compliance reports

Usage:
    python run_real_security_tests.py
    python run_real_security_tests.py --category LLM01
    python run_real_security_tests.py --scenarios 5
    python run_real_security_tests.py --output custom_results/
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path
from datetime import UTC, datetime

# Load environment variables first
from dotenv import load_dotenv
load_dotenv()

# Add project root to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from main.src.security.real_test_executor import RealSecurityTestExecutor
from main.src.security.owasp_test_scenarios import OWASPTestScenarios
from main.src.monitoring.phoenix_config import setup_phoenix


def setup_logging(verbose: bool = False) -> logging.Logger:
    """Setup logging configuration for security testing."""
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(
                f"security_test_run_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.log"
            )
        ]
    )
    
    return logging.getLogger(__name__)


async def run_category_tests(executor: RealSecurityTestExecutor, category: str) -> dict:
    """Run tests for a specific OWASP category."""
    logger = logging.getLogger(__name__)
    
    scenario_generator = OWASPTestScenarios()
    
    if category == "LLM01":
        scenarios = scenario_generator.get_prompt_injection_scenarios()
        logger.info(f"Running {len(scenarios)} LLM01 Prompt Injection scenarios")
    elif category == "LLM06":
        scenarios = scenario_generator.get_output_handling_scenarios()
        logger.info(f"Running {len(scenarios)} LLM06 Output Handling scenarios")
    elif category == "LLM09":
        scenarios = scenario_generator.get_overreliance_scenarios()
        logger.info(f"Running {len(scenarios)} LLM09 Overreliance scenarios")
    else:
        raise ValueError(f"Unknown category: {category}")
    
    return await executor.execute_scenario_batch(scenarios, f"{category}_RealTest")


async def run_limited_tests(executor: RealSecurityTestExecutor, max_scenarios: int) -> dict:
    """Run a limited number of scenarios for testing purposes."""
    logger = logging.getLogger(__name__)
    
    scenario_generator = OWASPTestScenarios()
    all_scenarios = scenario_generator.get_all_scenarios()
    
    # Take a representative sample
    limited_scenarios = all_scenarios[:max_scenarios]
    
    logger.info(f"Running limited test with {len(limited_scenarios)} scenarios")
    
    return await executor.execute_scenario_batch(limited_scenarios, "LimitedRealTest")


async def run_full_assessment(executor: RealSecurityTestExecutor) -> dict:
    """Run the complete security assessment with all scenarios."""
    logger = logging.getLogger(__name__)
    logger.info("Running COMPLETE real security assessment (all 30 scenarios)")
    
    return await executor.execute_full_security_assessment()


def print_results_summary(results: dict, logger: logging.Logger):
    """Print a summary of the test results."""
    logger.info("=" * 60)
    logger.info("REAL SECURITY TEST RESULTS SUMMARY")
    logger.info("=" * 60)
    
    if "overall_metrics" in results:
        # Full assessment results
        metrics = results["overall_metrics"]
        compliance = results["compliance_assessment"]
        
        logger.info(f"Total Scenarios Executed: {metrics['total_scenarios_executed']}")
        logger.info(f"Overall Success Rate: {metrics['overall_success_rate']:.2%}")
        logger.info(f"Overall Mitigation Effectiveness: {metrics['overall_mitigation_effectiveness']:.2%}")
        logger.info(f"Total Vulnerabilities Found: {metrics['total_vulnerabilities_found']}")
        logger.info(f"Human Consultations Triggered: {metrics['total_human_consultations']}")
        
        logger.info("\nCOMPLIANCE ASSESSMENT:")
        logger.info(f"Target Mitigation Effectiveness: {compliance['target_mitigation_effectiveness']:.1%}")
        logger.info(f"Achieved Mitigation Effectiveness: {compliance['achieved_mitigation_effectiveness']:.2%}")
        logger.info(f"Mitigation Target Met: {'✅ YES' if compliance['targets_met']['mitigation_effectiveness'] else '❌ NO'}")
        
        logger.info(f"Target Human Review Hours: {compliance['target_human_review_hours']}")
        logger.info(f"Estimated Human Review Hours: {compliance['estimated_human_review_hours']}")
        logger.info(f"Human Review Target Met: {'✅ YES' if compliance['targets_met']['human_review_hours'] else '❌ NO'}")
        
        if results["recommendations"]:
            logger.info(f"\nRECOMMENDATIONS ({len(results['recommendations'])} items):")
            for rec in results["recommendations"]:
                priority_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(rec["priority"], "⚪")
                logger.info(f"  {priority_emoji} [{rec['category']}] {rec['issue']}")
                logger.info(f"    → {rec['recommendation']}")
    
    else:
        # Batch results
        stats = results["statistics"]
        logger.info(f"Batch: {results['batch_id']}")
        logger.info(f"Total Scenarios: {stats['total_scenarios']}")
        logger.info(f"Successful Tests: {stats['successful_tests']}")
        logger.info(f"Failed Tests: {stats['failed_tests']}")
        logger.info(f"Success Rate: {stats['success_rate']:.2%}")
        logger.info(f"Average Mitigation Effectiveness: {stats['average_mitigation_effectiveness']:.2%}")
        logger.info(f"Vulnerabilities Found: {stats['vulnerabilities_found']}")
        logger.info(f"Human Consultations: {stats['human_consultations_triggered']}")
        
        if results.get("vulnerabilities_summary"):
            logger.info(f"\nVULNERABILITIES DETECTED ({len(results['vulnerabilities_summary'])} scenarios):")
            for vuln in results["vulnerabilities_summary"]:
                logger.info(f"  • {vuln['scenario_id']} ({vuln['severity']}): {', '.join(vuln['vulnerabilities'])}")
    
    logger.info("=" * 60)


async def main():
    """Main execution function for real security testing."""
    parser = argparse.ArgumentParser(description="Run REAL security tests against the pharmaceutical system")
    parser.add_argument("--category", choices=["LLM01", "LLM06", "LLM09"], 
                       help="Run tests for specific OWASP category only")
    parser.add_argument("--scenarios", type=int, 
                       help="Limit to N scenarios for testing (default: all)")
    parser.add_argument("--output", type=str, 
                       help="Custom output directory for results")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose logging")
    parser.add_argument("--no-phoenix", action="store_true",
                       help="Disable Phoenix observability (for debugging)")
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging(args.verbose)
    
    # Setup Phoenix observability (unless disabled)
    if not args.no_phoenix:
        try:
            setup_phoenix()
            logger.info("Phoenix observability initialized")
        except Exception as e:
            logger.warning(f"Phoenix setup failed: {e}")
            logger.info("Continuing without Phoenix observability")
    
    # Setup output directory
    output_dir = Path(args.output) if args.output else None
    
    # Initialize REAL test executor
    logger.info("Initializing REAL Security Test Executor")
    executor = RealSecurityTestExecutor(output_dir=output_dir)
    
    try:
        # Execute based on arguments
        if args.category:
            logger.info(f"Executing REAL tests for category: {args.category}")
            results = await run_category_tests(executor, args.category)
            
        elif args.scenarios:
            logger.info(f"Executing LIMITED REAL tests ({args.scenarios} scenarios)")
            results = await run_limited_tests(executor, args.scenarios)
            
        else:
            logger.info("Executing COMPLETE REAL security assessment")
            results = await run_full_assessment(executor)
        
        # Print results summary
        print_results_summary(results, logger)
        
        # Check if targets were met
        if "compliance_assessment" in results:
            compliance = results["compliance_assessment"]
            if all(compliance["targets_met"].values()):
                logger.info("🎉 ALL COMPLIANCE TARGETS MET!")
                return 0
            else:
                logger.warning("⚠️  Some compliance targets were not met")
                return 1
        else:
            # For batch results, check mitigation effectiveness
            mitigation_eff = results["statistics"]["average_mitigation_effectiveness"]
            if mitigation_eff >= 0.9:
                logger.info(f"🎉 MITIGATION TARGET MET ({mitigation_eff:.2%})")
                return 0
            else:
                logger.warning(f"⚠️  MITIGATION TARGET NOT MET ({mitigation_eff:.2%} < 90%)")
                return 1
    
    except Exception as e:
        logger.error(f"REAL security test execution failed: {e}")
        logger.debug("Full exception details:", exc_info=True)
        return 1


if __name__ == "__main__":
    # Run the real security tests
    exit_code = asyncio.run(main())
    sys.exit(exit_code)