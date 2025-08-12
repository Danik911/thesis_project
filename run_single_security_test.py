#!/usr/bin/env python3
"""
Single Security Test - Proof of Concept

This script executes a SINGLE security test scenario to validate that the system 
can properly detect and mitigate OWASP LLM security vulnerabilities. It serves as 
a proof-of-concept for the complete security assessment framework.

Key Features:
- Tests 1 carefully selected scenario (prompt injection)
- Uses REAL API calls against actual system
- Captures HONEST vulnerability findings
- Reports ACTUAL mitigation effectiveness
- NO FALLBACKS - explicit error reporting only

Expected Results:
- Either successful mitigation detection OR explicit vulnerability report
- Clear evidence of system behavior under attack
- Honest assessment of security posture

This test prioritizes HONESTY and REAL RESULTS over perfect scores.
"""

import asyncio
import json
import logging
import sys
import os
from datetime import datetime, timezone
from pathlib import Path

# Add main to Python path
sys.path.insert(0, str(Path(__file__).parent / "main"))

from src.security.working_test_executor import WorkingSecurityTestExecutor
from src.security.owasp_test_scenarios import OWASPTestScenarios


def setup_environment():
    """Load environment variables from .env file."""
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    # Remove quotes if present
                    value = value.strip('"\'')
                    os.environ[key] = value
    
    # Set provider to OpenRouter for DeepSeek V3
    os.environ['LLM_PROVIDER'] = 'openrouter'


def setup_logging():
    """Configure logging for the security test."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(
                f"single_security_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            )
        ]
    )
    return logging.getLogger(__name__)


async def run_single_security_test():
    """
    Execute a SINGLE security test scenario to validate the system.
    
    Returns:
        Dict containing test results and security findings
    """
    logger = setup_logging()
    logger.info("=" * 60)
    logger.info("STARTING SINGLE SECURITY TEST - PROOF OF CONCEPT")
    logger.info("=" * 60)
    
    test_start = datetime.now(timezone.utc)
    
    # Initialize test components
    logger.info("Loading environment and initializing components...")
    setup_environment()
    
    scenario_generator = OWASPTestScenarios()
    executor = WorkingSecurityTestExecutor(
        output_dir=Path("main/output/security_assessment/single_test")
    )
    
    # Get a single, representative test scenario
    all_scenarios = scenario_generator.get_all_scenarios()
    
    # Select one LLM01 prompt injection scenario for testing
    llm01_scenarios = [s for s in all_scenarios if s["owasp_category"] == "LLM01"]
    if not llm01_scenarios:
        raise Exception("No LLM01 scenarios available for testing")
    
    test_scenario = llm01_scenarios[0]  # Get first prompt injection scenario
    logger.info(f"Selected test scenario: {test_scenario['id']} - {test_scenario.get('attack_type', 'prompt_injection')}")
    logger.info(f"Scenario description: {test_scenario.get('description', 'No description available')}")
    
    try:
        # Execute the SINGLE security test
        logger.info("EXECUTING SINGLE SECURITY TEST...")
        logger.info(f"Testing scenario: {test_scenario['id']}")
        logger.info(f"Attack type: {test_scenario.get('attack_type', 'unknown')}")
        logger.info(f"Expected behavior: {test_scenario.get('expected_behavior', 'unknown')}")
        
        result = await executor.execute_single_scenario(
            test_scenario, 
            "SingleSecurityTest"
        )
        
        test_end = datetime.now(timezone.utc)
        
        # Analyze results
        logger.info("ANALYZING TEST RESULTS...")
        vulnerabilities_found = result.get("vulnerability_analysis", {}).get("vulnerabilities_detected", [])
        mitigation_effectiveness = result.get("mitigation_effectiveness", 0.0)
        human_consultation = result.get("human_consultation_triggered", False)
        
        # Log findings
        if vulnerabilities_found and "ANALYSIS_FAILED" not in vulnerabilities_found:
            logger.warning(f"VULNERABILITIES DETECTED: {vulnerabilities_found}")
        else:
            logger.info("No vulnerabilities detected in this test")
        
        logger.info(f"Mitigation Effectiveness: {mitigation_effectiveness:.2%}")
        logger.info(f"Human Consultation Triggered: {human_consultation}")
        
        # Compile final report
        test_report = {
            "test_metadata": {
                "test_id": f"single_security_test_{test_start.strftime('%Y%m%d_%H%M%S')}",
                "test_type": "single_scenario_validation",
                "scenario_tested": test_scenario['id'],
                "execution_timestamp": test_start.isoformat(),
                "completion_timestamp": test_end.isoformat(),
                "duration_seconds": (test_end - test_start).total_seconds()
            },
            "scenario_details": {
                "owasp_category": test_scenario.get("owasp_category", ""),
                "attack_type": test_scenario.get("attack_type", ""),
                "severity": test_scenario.get("severity", ""),
                "description": test_scenario.get("description", ""),
                "expected_behavior": test_scenario.get("expected_behavior", "")
            },
            "security_findings": {
                "vulnerabilities_detected": vulnerabilities_found,
                "vulnerability_count": len([v for v in vulnerabilities_found if v != "ANALYSIS_FAILED"]),
                "mitigation_effectiveness": mitigation_effectiveness,
                "human_consultation_triggered": human_consultation,
                "test_successful": result.get("status") == "completed"
            },
            "detailed_results": result
        }
        
        # Save report
        output_dir = Path("main/output/security_assessment/single_test")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        report_file = output_dir / f"single_test_report_{test_start.strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(test_report, f, indent=2, ensure_ascii=False)
        
        # Generate summary
        logger.info("=" * 60)
        logger.info("SINGLE SECURITY TEST COMPLETED")
        logger.info("=" * 60)
        logger.info(f"Scenario: {test_scenario['id']} ({test_scenario.get('attack_type', 'prompt_injection')})")
        logger.info(f"Test Status: {'SUCCESS' if result.get('status') == 'completed' else 'FAILED'}")
        logger.info(f"Vulnerabilities Found: {len([v for v in vulnerabilities_found if v != 'ANALYSIS_FAILED'])}")
        logger.info(f"Mitigation Effectiveness: {mitigation_effectiveness:.1%}")
        logger.info(f"Human Consultation: {'YES' if human_consultation else 'NO'}")
        logger.info(f"Duration: {(test_end - test_start).total_seconds():.1f} seconds")
        logger.info(f"Report saved to: {report_file}")
        
        return test_report
        
    except Exception as e:
        logger.error(f"SINGLE SECURITY TEST FAILED: {e}")
        logger.error("Full traceback:", exc_info=True)
        raise
    
    finally:
        # Cleanup temporary resources
        executor.cleanup()


async def main():
    """Main execution function."""
    try:
        print("[SECURITY] Starting Single Security Test...")
        print("[TARGET] Testing one OWASP LLM scenario against real system")
        print("[NOTICE] This is a proof-of-concept for the complete assessment")
        print()
        
        test_report = await run_single_security_test()
        
        print("\n" + "="*60)
        print("[SUCCESS] SINGLE SECURITY TEST COMPLETED")
        print("="*60)
        print(f"[SCENARIO] {test_report['scenario_details']['owasp_category']} - {test_report['test_metadata']['scenario_tested']}")
        print(f"[VULNERABILITIES] {test_report['security_findings']['vulnerability_count']} detected")
        print(f"[MITIGATION] {test_report['security_findings']['mitigation_effectiveness']:.1%} effective")
        print(f"[CONSULTATION] {'Required' if test_report['security_findings']['human_consultation_triggered'] else 'Not required'}")
        print(f"[STATUS] {'PASSED' if test_report['security_findings']['test_successful'] else 'FAILED'}")
        
        return test_report
        
    except KeyboardInterrupt:
        print("\n[INTERRUPT] Test interrupted by user")
        return None
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        return None


if __name__ == "__main__":
    # Run the single security test
    result = asyncio.run(main())
    
    if result and result['security_findings']['test_successful']:
        print("\n[SUCCESS] Single security test completed successfully!")
        sys.exit(0)
    else:
        print("\n[FAILED] Single security test failed!")
        sys.exit(1)