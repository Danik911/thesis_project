#!/usr/bin/env python3
"""
Run the complete real security assessment using the working test executor.

This executes actual security tests against the live pharmaceutical system
and provides honest metrics on vulnerabilities and mitigation effectiveness.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("Loaded environment variables from .env file")
except ImportError:
    print("python-dotenv not available, using system environment")

# Add main to path so we can import
sys.path.insert(0, str(Path(__file__).parent / "main"))

from src.security.working_test_executor import WorkingSecurityTestExecutor


async def main():
    """Run the complete real security assessment."""
    print("Real Security Assessment for Pharmaceutical Test Generation System")
    print("=" * 70)
    print("This will execute REAL security tests against the actual system")
    print("NO SIMULATIONS - capturing genuine vulnerabilities and mitigation rates")
    print()

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Initialize the working security test executor
    executor = WorkingSecurityTestExecutor()

    try:
        print("Starting complete security assessment...")

        # Execute the full security assessment
        # This will test LLM01 (prompt injection), LLM06 (output handling), and LLM09 (overreliance)
        assessment_results = await executor.execute_full_security_assessment()

        print("\nSECURITY ASSESSMENT COMPLETED!")
        print("=" * 35)

        # Display key metrics
        metrics = assessment_results["overall_metrics"]
        print(f"Total Scenarios Executed: {metrics['total_scenarios_executed']}")
        print(f"Overall Success Rate: {metrics['overall_success_rate']:.1%}")
        print(f"Overall Mitigation Effectiveness: {metrics['overall_mitigation_effectiveness']:.1%}")
        print(f"Total Vulnerabilities Found: {metrics['total_vulnerabilities_found']}")
        print(f"Total Human Consultations: {metrics['total_human_consultations']}")

        # Show category breakdown
        print("\nCategory Breakdown:")
        for category, results in assessment_results["category_results"].items():
            stats = results["statistics"]
            print(f"  {category}: {stats['successful_tests']}/{stats['total_scenarios']} tests "
                  f"({stats['success_rate']:.1%} success, "
                  f"{stats['average_mitigation_effectiveness']:.1%} mitigation)")

        # Compliance assessment
        print("\nCompliance Assessment:")
        compliance = assessment_results.get("compliance_assessment", {})
        target_mitigation = compliance.get("target_mitigation_effectiveness", 0.9)
        achieved_mitigation = compliance.get("achieved_mitigation_effectiveness", 0.0)

        print(f"Target Mitigation Effectiveness: {target_mitigation:.1%}")
        print(f"Achieved Mitigation Effectiveness: {achieved_mitigation:.1%}")

        if achieved_mitigation >= target_mitigation:
            print("STATUS: COMPLIANT - Mitigation targets met")
        else:
            print("STATUS: NON-COMPLIANT - Mitigation targets not met")

        print("\nDetailed results saved to:")
        print(f"  {executor.output_dir}")

        return True

    except Exception as e:
        print(f"ERROR: Security assessment failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

    finally:
        # Clean up temporary files
        executor.cleanup()


if __name__ == "__main__":
    success = asyncio.run(main())
    if success:
        print("\nSecurity assessment completed successfully!")
        sys.exit(0)
    else:
        print("\nSecurity assessment failed!")
        sys.exit(1)
