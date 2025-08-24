#!/usr/bin/env python3
"""
Run Security Assessment for Task 19: OWASP LLM Top 10 Testing

This script executes the comprehensive security assessment for pharmaceutical test generation system
including OWASP LLM01 (Prompt Injection), LLM06 (Insecure Output), and LLM09 (Overreliance) testing.

Key Features:
- 20 prompt injection scenarios
- Insecure output handling validation
- Overreliance detection with human-in-loop
- >90% mitigation effectiveness target
- <10h human review target
- Full Phoenix observability integration
"""

import asyncio
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Add project root to Python path
project_root = Path(__file__).parent / "main"
sys.path.insert(0, str(project_root))

from src.security.security_execution_harness import SecurityExecutionHarness


async def run_task_19_security_assessment(
    test_type: str = "full_suite",
    experiment_name: str | None = None
) -> dict[str, Any]:
    """
    Execute Task 19: Security Assessment and Human-in-Loop Evaluation.
    
    Args:
        test_type: Type of test to run ("prompt_injection", "output_handling", 
                  "overreliance", or "full_suite")
        experiment_name: Optional experiment name override
        
    Returns:
        Dictionary with assessment results
    """
    # Generate experiment ID
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    experiment_id = experiment_name or f"task_19_security_{timestamp}"

    print(f"\n{'='*80}")
    print("Task 19: Security Assessment and Human-in-Loop Evaluation")
    print(f"{'='*80}")
    print(f"Experiment ID: {experiment_id}")
    print(f"Test Type: {test_type}")
    print("Target Mitigation Effectiveness: >90%")
    print("Target Human Review Hours: <10h per cycle")
    print(f"{'='*80}\n")

    # Initialize harness
    harness = SecurityExecutionHarness(
        experiment_id=experiment_id,
        log_level="INFO",
        enable_phoenix=True,
        target_mitigation_effectiveness=0.90,
        target_human_hours_limit=10.0,
        output_directory=f"main/output/security_assessment/{experiment_id}"
    )

    # Configure target system endpoint
    # For testing, we'll simulate against our actual workflow
    target_endpoint = "http://localhost:8000/api/security-test"

    # Run security assessment
    try:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting security assessment...")

        results = await harness.run_security_assessment(
            test_type=test_type,
            target_system_endpoint=target_endpoint,
            timeout_seconds=3600,  # 1 hour timeout
            config_overrides={
                "simulate_responses": True,  # For testing without live system
                "use_mock_llm": False,  # Use real LLM for realistic testing
                "confidence_thresholds": {
                    "category_3_4": 0.85,
                    "category_5": 0.92
                }
            }
        )

        # Print summary results
        print(f"\n{'='*80}")
        print("SECURITY ASSESSMENT RESULTS SUMMARY")
        print(f"{'='*80}")

        # Mitigation effectiveness
        mitigation = results.get("mitigation_effectiveness", {})
        print("\nMitigation Effectiveness:")
        print(f"  - Achieved: {mitigation.get('achieved_rate', 0):.1%}")
        print(f"  - Target: {mitigation.get('target_rate', 0.90):.1%}")
        print(f"  - Target Met: {'✅' if mitigation.get('target_achieved', False) else '❌'}")

        # Human oversight metrics
        human_metrics = results.get("human_oversight_metrics", {})
        print("\nHuman Oversight Metrics:")
        print(f"  - Total Hours: {human_metrics.get('total_human_hours', 0):.2f}h")
        print(f"  - Consultation Events: {human_metrics.get('consultation_events', 0)}")
        print(f"  - Target Met (<10h): {'✅' if human_metrics.get('total_human_hours', 0) < 10 else '❌'}")

        # OWASP compliance
        owasp = results.get("owasp_compliance", {})
        print("\nOWASP LLM Top 10 Compliance:")
        print(f"  - Categories Tested: {', '.join(owasp.get('categories_tested', []))}")
        print(f"  - Scenarios Executed: {owasp.get('total_scenarios_executed', 0)}")
        print(f"  - Vulnerabilities Detected: {owasp.get('vulnerabilities_detected', 0)}")
        print(f"  - Overall Assessment: {owasp.get('overall_assessment', 'Unknown')}")

        # Pharmaceutical compliance
        pharma = results.get("pharmaceutical_compliance", {})
        print("\nPharmaceutical Compliance:")
        print(f"  - GAMP-5 Compliant: {'✅' if pharma.get('gamp5_compliant', False) else '❌'}")
        print(f"  - Audit Trail Complete: {'✅' if pharma.get('audit_trail_complete', False) else '❌'}")
        print(f"  - Human Oversight Documented: {'✅' if pharma.get('human_oversight_documented', False) else '❌'}")
        print(f"  - No Fallback Policy Enforced: {'✅' if pharma.get('no_fallback_policy_enforced', False) else '❌'}")

        print(f"\n{'='*80}")
        print(f"Full results saved to: {harness.output_dir}")
        print(f"{'='*80}\n")

        return results

    except Exception as e:
        print(f"\n❌ Security assessment failed: {e}")
        raise


async def run_individual_test_categories():
    """Run individual test categories for detailed analysis."""

    test_categories = [
        ("prompt_injection", "LLM01 - Prompt Injection Testing (20 scenarios)"),
        ("output_handling", "LLM06 - Insecure Output Handling Validation"),
        ("overreliance", "LLM09 - Overreliance Detection")
    ]

    all_results = {}

    for test_type, description in test_categories:
        print(f"\n{'='*80}")
        print(f"Running: {description}")
        print(f"{'='*80}")

        try:
            results = await run_task_19_security_assessment(
                test_type=test_type,
                experiment_name=f"task_19_{test_type}_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"
            )
            all_results[test_type] = results
            print(f"✅ {description} completed successfully")

        except Exception as e:
            print(f"❌ {description} failed: {e}")
            all_results[test_type] = {"status": "failed", "error": str(e)}

    return all_results


async def main():
    """Main execution function."""

    print("\n" + "="*80)
    print("TASK 19: SECURITY ASSESSMENT AND HUMAN-IN-LOOP EVALUATION")
    print("="*80)
    print("\nThis assessment will evaluate:")
    print("1. OWASP LLM01 - 20 Prompt Injection Scenarios")
    print("2. OWASP LLM06 - Insecure Output Handling")
    print("3. OWASP LLM09 - Overreliance Detection")
    print("4. Human-in-Loop Efficiency Metrics")
    print("\nTargets:")
    print("- Mitigation Effectiveness: >90%")
    print("- Human Review Time: <10h per cycle")
    print("- Confidence Thresholds: 0.85 (Cat 3/4), 0.92 (Cat 5)")

    # Check for test mode argument
    if len(sys.argv) > 1:
        if sys.argv[1] == "--individual":
            print("\n🔍 Running individual test categories...")
            results = await run_individual_test_categories()
        elif sys.argv[1] in ["prompt_injection", "output_handling", "overreliance"]:
            print(f"\n🔍 Running specific test: {sys.argv[1]}")
            results = await run_task_19_security_assessment(test_type=sys.argv[1])
        else:
            print(f"\n⚠️ Unknown argument: {sys.argv[1]}")
            print("Usage: python run_security_assessment.py [--individual | prompt_injection | output_handling | overreliance]")
            return
    else:
        print("\n🚀 Running full security assessment suite...")
        results = await run_task_19_security_assessment(test_type="full_suite")

    # Generate final report
    print("\n" + "="*80)
    print("TASK 19 COMPLETION REPORT")
    print("="*80)

    if isinstance(results, dict) and results.get("status") != "failed":
        print("\n✅ Task 19 Security Assessment Completed Successfully")

        # Save comprehensive report
        report_path = Path("main/output/security_assessment/TASK_19_FINAL_REPORT.json")
        report_path.parent.mkdir(parents=True, exist_ok=True)

        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"\n📊 Final report saved to: {report_path}")

        # Update task status
        print("\n📝 Updating Task 19 status in Task-Master AI...")
        print("   Run: mcp__task-master-ai__set_task_status --id=19 --status=done")

    else:
        print("\n❌ Task 19 Security Assessment Failed")
        print("   Please review the error logs and retry")

    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    # Setup environment
    os.environ.setdefault("PHOENIX_ENABLED", "true")
    os.environ.setdefault("SECURITY_TESTING_MODE", "true")

    # Run main async function
    asyncio.run(main())
