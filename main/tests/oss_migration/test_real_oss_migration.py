"""
REAL OSS Migration Testing with Actual API Calls
CRITICAL: This test uses REAL API calls, not mocks
HONEST REPORTING: All failures reported without masking
"""

import json
import os
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import required modules
from llama_index.core import Document
from src.agents.categorization.agent import categorize_urs_document
from src.config.llm_config import LLMConfig
from src.core.events import DocumentEvent
from src.core.unified_workflow import UnifiedOQTestingWorkflow

# Phoenix tracing setup (if available)
try:
    from opentelemetry import trace
    from src.monitoring.phoenix_config import setup_phoenix
    phoenix_available = True
    phoenix_manager = setup_phoenix()
    tracer = trace.get_tracer("oss_migration_testing")
except ImportError:
    phoenix_available = False
    print("⚠️ Phoenix tracing not available - continuing without traces")


class OSSMigrationTester:
    """Real OSS migration testing with actual API calls"""

    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "provider": None,
            "api_key_present": False,
            "tests": [],
            "summary": {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "errors": 0,
                "total_cost": 0.0,
                "avg_latency": 0.0
            }
        }

    def check_environment(self) -> dict[str, Any]:
        """Check environment configuration"""
        env_check = {
            "llm_provider": os.getenv("LLM_PROVIDER", "not_set"),
            "openrouter_key_present": bool(os.getenv("OPENROUTER_API_KEY")),
            "openai_key_present": bool(os.getenv("OPENAI_API_KEY")),
            "phoenix_tracing": phoenix_available
        }

        print("\n" + "="*80)
        print("ENVIRONMENT CHECK")
        print("="*80)
        print(f"LLM Provider: {env_check['llm_provider']}")
        print(f"OpenRouter API Key: {'✅ Present' if env_check['openrouter_key_present'] else '❌ MISSING'}")
        print(f"OpenAI API Key: {'✅ Present' if env_check['openai_key_present'] else '❌ MISSING'}")
        print(f"Phoenix Tracing: {'✅ Available' if phoenix_available else '⚠️ Not Available'}")

        self.results["provider"] = env_check["llm_provider"]
        self.results["api_key_present"] = env_check["openrouter_key_present"]

        return env_check

    def test_llm_initialization(self) -> dict[str, Any]:
        """Test LLM initialization with real API"""
        test_result = {
            "test_name": "LLM Initialization",
            "status": "pending",
            "error": None,
            "details": {}
        }

        print("\n" + "="*80)
        print("TEST: LLM INITIALIZATION")
        print("="*80)

        try:
            # Get provider info
            provider_info = LLMConfig.get_provider_info()
            print(f"Provider: {provider_info['provider']}")
            print(f"Model: {provider_info['configuration']['model']}")
            print(f"API Key Present: {provider_info['api_key_present']}")

            test_result["details"]["provider_info"] = provider_info

            # Validate configuration
            is_valid, message = LLMConfig.validate_configuration()
            print(f"Configuration Valid: {is_valid}")
            if not is_valid:
                print(f"Error: {message}")
                test_result["error"] = message
                test_result["status"] = "failed"
                return test_result

            # Try to initialize LLM
            print("\nInitializing LLM...")
            start_time = time.time()
            llm = LLMConfig.get_llm()
            init_time = time.time() - start_time

            print(f"✅ LLM initialized in {init_time:.2f}s")
            print(f"LLM Type: {type(llm).__name__}")

            # Test with a simple completion
            print("\nTesting simple completion...")
            start_time = time.time()
            response = llm.complete("Say 'OSS migration test successful' and nothing else.")
            completion_time = time.time() - start_time

            print(f"Response: {response.text[:100]}")
            print(f"Completion time: {completion_time:.2f}s")

            test_result["status"] = "passed"
            test_result["details"]["init_time"] = init_time
            test_result["details"]["completion_time"] = completion_time
            test_result["details"]["response_preview"] = str(response.text[:100])

        except Exception as e:
            print(f"❌ FAILED: {e!s}")
            print(f"Full traceback:\n{traceback.format_exc()}")
            test_result["status"] = "error"
            test_result["error"] = str(e)
            test_result["details"]["traceback"] = traceback.format_exc()

        self.results["tests"].append(test_result)
        return test_result

    def test_categorization_agent(self, test_documents: list) -> dict[str, Any]:
        """Test categorization agent with real pharmaceutical documents"""
        test_result = {
            "test_name": "Categorization Agent",
            "status": "pending",
            "error": None,
            "details": {
                "test_cases": []
            }
        }

        print("\n" + "="*80)
        print("TEST: CATEGORIZATION AGENT")
        print("="*80)

        try:
            # No need to initialize agent - using function directly
            print("Testing Categorization with Real API Calls...")

            total_tests = len(test_documents)
            passed = 0
            failed = 0

            for i, doc_info in enumerate(test_documents, 1):
                print(f"\n--- Test Case {i}/{total_tests}: {doc_info['name']} ---")
                print(f"Expected Category: {doc_info['expected_category']}")

                case_result = {
                    "name": doc_info["name"],
                    "expected": doc_info["expected_category"],
                    "actual": None,
                    "confidence": None,
                    "status": "pending",
                    "error": None,
                    "latency": None
                }

                try:
                    # Run categorization with REAL API call
                    start_time = time.time()
                    result = categorize_urs_document(
                        urs_content=doc_info["content"],
                        document_name=doc_info["name"],
                        use_structured_output=True,
                        verbose=True
                    )
                    latency = time.time() - start_time

                    case_result["latency"] = latency
                    case_result["actual"] = result.category
                    case_result["confidence"] = result.confidence

                    print(f"Actual Category: {result.category}")
                    print(f"Confidence: {result.confidence:.2%}")
                    print(f"Latency: {latency:.2f}s")

                    # Validate result
                    if result.category == doc_info["expected_category"]:
                        if result.confidence >= 0.7:
                            print("✅ PASSED - Correct category with good confidence")
                            case_result["status"] = "passed"
                            passed += 1
                        else:
                            print(f"⚠️ WARNING - Correct category but low confidence ({result.confidence:.2%})")
                            case_result["status"] = "warning"
                            passed += 1
                    else:
                        print(f"❌ FAILED - Wrong category (expected {doc_info['expected_category']}, got {result.category})")
                        case_result["status"] = "failed"
                        failed += 1

                    # Show reasoning
                    print(f"Reasoning: {result.reasoning[:200]}...")

                except Exception as e:
                    print(f"❌ ERROR: {e!s}")
                    case_result["status"] = "error"
                    case_result["error"] = str(e)
                    failed += 1

                test_result["details"]["test_cases"].append(case_result)

            # Summary
            print("\n--- Categorization Summary ---")
            print(f"Total: {total_tests}")
            print(f"Passed: {passed} ({passed/total_tests*100:.1f}%)")
            print(f"Failed: {failed} ({failed/total_tests*100:.1f}%)")

            test_result["status"] = "passed" if failed == 0 else "failed"
            test_result["details"]["summary"] = {
                "total": total_tests,
                "passed": passed,
                "failed": failed,
                "success_rate": passed / total_tests
            }

        except Exception as e:
            print(f"❌ CRITICAL ERROR: {e!s}")
            print(f"Full traceback:\n{traceback.format_exc()}")
            test_result["status"] = "error"
            test_result["error"] = str(e)
            test_result["details"]["traceback"] = traceback.format_exc()

        self.results["tests"].append(test_result)
        return test_result

    def test_unified_workflow(self, test_urs: str) -> dict[str, Any]:
        """Test unified workflow with real API calls"""
        test_result = {
            "test_name": "Unified Workflow",
            "status": "pending",
            "error": None,
            "details": {}
        }

        print("\n" + "="*80)
        print("TEST: UNIFIED WORKFLOW")
        print("="*80)

        try:
            # Initialize workflow
            print("Initializing Unified Workflow...")
            workflow = UnifiedOQTestingWorkflow()

            # Create document event
            doc = Document(text=test_urs, metadata={"source": "test"})
            event = DocumentEvent(document=doc)

            print("Running workflow with real API calls...")
            start_time = time.time()

            # Run workflow
            result = workflow.run(initial_event=event)

            total_time = time.time() - start_time

            print(f"\n✅ Workflow completed in {total_time:.2f}s")

            # Extract results
            if hasattr(result, "__iter__"):
                for event in result:
                    if hasattr(event, "tests") and event.tests:
                        print(f"Generated {len(event.tests)} OQ tests")
                        test_result["details"]["num_tests"] = len(event.tests)
                        test_result["details"]["test_preview"] = [
                            test.test_id for test in event.tests[:3]
                        ]
                        break

            test_result["status"] = "passed"
            test_result["details"]["execution_time"] = total_time

        except Exception as e:
            print(f"❌ WORKFLOW ERROR: {e!s}")
            print(f"Full traceback:\n{traceback.format_exc()}")
            test_result["status"] = "error"
            test_result["error"] = str(e)
            test_result["details"]["traceback"] = traceback.format_exc()

        self.results["tests"].append(test_result)
        return test_result

    def generate_report(self):
        """Generate honest test report"""
        print("\n" + "="*80)
        print("OSS MIGRATION TEST REPORT")
        print("="*80)

        # Calculate summary
        total = len(self.results["tests"])
        passed = sum(1 for t in self.results["tests"] if t["status"] == "passed")
        failed = sum(1 for t in self.results["tests"] if t["status"] == "failed")
        errors = sum(1 for t in self.results["tests"] if t["status"] == "error")

        self.results["summary"]["total"] = total
        self.results["summary"]["passed"] = passed
        self.results["summary"]["failed"] = failed
        self.results["summary"]["errors"] = errors

        print(f"\nTimestamp: {self.results['timestamp']}")
        print(f"Provider: {self.results['provider']}")
        print(f"API Key Present: {self.results['api_key_present']}")

        print("\n--- Test Summary ---")
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"💥 Errors: {errors}")

        if total > 0:
            success_rate = (passed / total) * 100
            print(f"Success Rate: {success_rate:.1f}%")

            if success_rate >= 80:
                print("\n✅ OSS Migration: VIABLE (>80% success)")
            elif success_rate >= 60:
                print("\n⚠️ OSS Migration: PARTIALLY SUCCESSFUL (60-80% success)")
            else:
                print("\n❌ OSS Migration: NOT READY (<60% success)")

        # Detailed results
        print("\n--- Detailed Results ---")
        for test in self.results["tests"]:
            status_icon = "✅" if test["status"] == "passed" else "❌" if test["status"] == "failed" else "💥"
            print(f"{status_icon} {test['test_name']}: {test['status'].upper()}")
            if test["error"]:
                print(f"   Error: {test['error']}")

        # Save report
        report_path = Path(__file__).parent / f"oss_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, "w") as f:
            json.dump(self.results, f, indent=2, default=str)
        print(f"\nReport saved to: {report_path}")

        return self.results


def main():
    """Run comprehensive OSS migration tests with REAL API calls"""

    print("\n" + "="*80)
    print("OSS MIGRATION TESTING - REAL API CALLS")
    print("HONEST REPORTING - NO FAKE RESULTS")
    print("="*80)

    tester = OSSMigrationTester()

    # 1. Check environment
    env_check = tester.check_environment()

    if not env_check["openrouter_key_present"] and env_check["llm_provider"] == "openrouter":
        print("\n❌ CRITICAL: OPENROUTER_API_KEY not set!")
        print("Please set the API key to run real tests:")
        print("  export OPENROUTER_API_KEY='your-key-here'")
        print("  export LLM_PROVIDER=openrouter")
        return None

    # 2. Test LLM initialization
    llm_test = tester.test_llm_initialization()

    if llm_test["status"] == "error":
        print("\n❌ LLM initialization failed - cannot continue tests")
        tester.generate_report()
        return None

    # 3. Prepare test documents
    test_documents = [
        {
            "name": "Environmental Monitoring System",
            "expected_category": 3,
            "content": """
            This system uses vendor-supplied software without modification.
            The system shall use vendor's standard database format.
            Standard reports provided by vendor shall be used for batch release.
            Temperature monitoring with vendor's built-in functionality.
            """
        },
        {
            "name": "LIMS Configuration",
            "expected_category": 4,
            "content": """
            System shall be based on commercial LIMS package (LabWare).
            Configure workflows for testing using vendor's configuration tools.
            Configure sample login screens to capture site-specific attributes.
            Implement custom business rules using vendor's scripting language.
            """
        },
        {
            "name": "Custom MES",
            "expected_category": 5,
            "content": """
            System shall be custom-developed to integrate with proprietary equipment.
            Custom algorithms required for dynamic in-process control limits.
            Develop custom interfaces for proprietary protocols.
            Custom workflow engine with site-specific business rules.
            Bespoke analytics module for real-time process monitoring.
            """
        }
    ]

    # 4. Test categorization agent
    cat_test = tester.test_categorization_agent(test_documents)

    # 5. Test unified workflow (if categorization worked)
    if cat_test["status"] != "error":
        workflow_urs = """
        Environmental Monitoring System for GMP storage areas.
        The system shall use vendor-supplied software without modification.
        Temperature readings shall be recorded at 5-minute intervals.
        Standard vendor reports shall be used for batch release.
        """
        workflow_test = tester.test_unified_workflow(workflow_urs)

    # 6. Generate final report
    report = tester.generate_report()

    # 7. Cost estimation
    print("\n--- Cost Analysis ---")
    print("OpenRouter (OSS): ~$0.09 per 1M tokens")
    print("OpenAI GPT-4: ~$10-30 per 1M tokens")
    print("Potential savings: >90% reduction in API costs")

    return report


if __name__ == "__main__":
    # Set environment for OSS testing
    os.environ["LLM_PROVIDER"] = "openrouter"

    # Run tests
    results = main()

    # Exit with appropriate code
    if results and results["summary"]["errors"] == 0 and results["summary"]["failed"] == 0:
        sys.exit(0)
    else:
        sys.exit(1)
