#!/usr/bin/env uv run python
"""
Context Provider Agent Q&A Testing with Phoenix Observability

This script executes comprehensive testing of the Context Provider Agent using
targeted FDA Part 11 questions and provides detailed Phoenix trace analysis
of the complete retrieval process.
"""

import asyncio
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
env_path = project_root / ".env"
load_dotenv(env_path)

from main.src.agents.parallel.context_provider import (
    ContextProviderRequest,
    create_context_provider_agent,
)
from main.src.core.events import AgentRequestEvent
from main.src.monitoring.phoenix_config import setup_phoenix, shutdown_phoenix
from main.tests.regulatory.fda_part11.fda_part11_qa_questions import FDApart11Questions


class ContextProviderQATest:
    """Comprehensive Q&A testing framework with Phoenix observability."""

    def __init__(self, verbose: bool = True):
        """Initialize the testing framework."""
        self.verbose = verbose
        self.agent = None
        self.phoenix_manager = None
        self.test_results = []
        self.start_time = None
        self.end_time = None

    async def setup(self) -> bool:
        """Setup Phoenix observability and Context Provider Agent."""
        try:
            print("🔬 Context Provider Agent Q&A Testing with Phoenix Observability")
            print("=" * 70)
            print()

            # Setup Phoenix observability
            print("1️⃣ Initializing Phoenix Observability...")
            self.phoenix_manager = setup_phoenix()

            if self.phoenix_manager._initialized:
                print("✅ Phoenix observability initialized successfully")
                print("   🌐 Phoenix UI: http://localhost:6006")
            else:
                print("⚠️  Phoenix initialization failed, continuing without tracing")
            print()

            # Initialize Context Provider Agent
            print("2️⃣ Initializing Context Provider Agent...")
            self.agent = create_context_provider_agent(
                verbose=self.verbose,
                enable_phoenix=True,
                max_documents=50
            )
            print("✅ Context Provider Agent initialized with Phoenix tracing")
            print()

            return True

        except Exception as e:
            print(f"❌ Setup failed: {e}")
            return False

    async def execute_question_test(self, question: dict[str, Any]) -> dict[str, Any]:
        """
        Execute a single question test with detailed Phoenix tracing.
        
        Args:
            question: Question dictionary from FDApart11Questions
            
        Returns:
            Comprehensive test result with Phoenix trace analysis
        """
        test_start = datetime.now(UTC)
        correlation_id = uuid4()

        print(f"🔍 Testing Question: {question['id']}")
        print(f"   Category: {question['category']}")
        print(f"   Question: {question['question']}")
        print(f"   Expected min confidence: {question['expected_confidence_min']}")
        print()

        try:
            # Create Context Provider Request
            request = ContextProviderRequest(
                gamp_category=question["gamp_category"],
                test_strategy=question["test_strategy"],
                document_sections=question["search_sections"],
                search_scope={
                    "collections": ["regulatory"],
                    "max_results": 20
                },
                context_depth=question["context_depth"],
                correlation_id=correlation_id,
                timeout_seconds=120
            )

            # Remove correlation_id from model_dump to avoid duplicate
            request_data = request.model_dump()
            request_data.pop("correlation_id", None)

            # Create Agent Request Event
            agent_request = AgentRequestEvent(
                agent_type="context_provider",
                request_data=request_data,
                requesting_step=f"qa_test_{question['id']}",
                correlation_id=correlation_id
            )

            # Execute the request with Phoenix tracing
            print("   🔄 Executing context retrieval with Phoenix tracing...")
            response = await self.agent.process_request(agent_request)

            test_end = datetime.now(UTC)
            processing_time = (test_end - test_start).total_seconds()

            # Analyze response
            if response.success:
                # The result_data directly contains the response fields
                agent_response = response.result_data

                # Extract retrieved content for validation
                retrieved_documents = agent_response.get("retrieved_documents", [])
                retrieved_content = ""

                if retrieved_documents:
                    # Combine content from all retrieved documents
                    retrieved_content = " ".join([
                        doc.get("content_summary", "") for doc in retrieved_documents
                    ])

                # Validate answer quality
                validation_result = FDApart11Questions.validate_answer_quality(
                    question, retrieved_content
                )

                # Create comprehensive test result
                test_result = {
                    "question_id": question["id"],
                    "question_category": question["category"],
                    "question_text": question["question"],
                    "test_timestamp": test_start.isoformat(),
                    "processing_time_seconds": processing_time,
                    "correlation_id": str(correlation_id),

                    # Agent Response Metrics
                    "success": True,
                    "documents_retrieved": len(retrieved_documents),
                    "context_quality": agent_response.get("context_quality", "unknown"),
                    "search_coverage": agent_response.get("search_coverage", 0.0),
                    "confidence_score": agent_response.get("confidence_score", 0.0),

                    # Answer Quality Validation
                    "answer_validation": validation_result,
                    "meets_confidence_threshold": (
                        agent_response.get("confidence_score", 0.0) >= question["expected_confidence_min"]
                    ),

                    # Document Details
                    "retrieved_documents_details": [
                        {
                            "title": doc.get("title", "Unknown"),
                            "relevance_score": doc.get("relevance_score", 0.0),
                            "content_preview": doc.get("content_summary", "")[:200] + "...",
                            "sections": doc.get("sections", []),
                            "metadata": doc.get("metadata", {})
                        }
                        for doc in retrieved_documents[:3]  # Top 3 documents
                    ],

                    # Phoenix Observability
                    "phoenix_trace_available": self.phoenix_manager._initialized if self.phoenix_manager else False,
                    "expected_phoenix_spans": [
                        f"context_provider.process_request.{question['id']}",
                        "chromadb.search_documents",
                        "chromadb.search_collection.regulatory",
                        "confidence_score_calculation",
                        "context_quality_assessment"
                    ]
                }

                # Display results
                print("   ✅ Test completed successfully!")
                print("   📊 Results:")
                print(f"      • Documents retrieved: {test_result['documents_retrieved']}")
                print(f"      • Context quality: {test_result['context_quality']}")
                print(f"      • Search coverage: {test_result['search_coverage']:.1%}")
                print(f"      • Confidence score: {test_result['confidence_score']:.3f}")
                print(f"      • Meets threshold: {'✅' if test_result['meets_confidence_threshold'] else '❌'}")
                print(f"      • Answer quality: {validation_result['quality_assessment']}")
                print(f"      • Concept coverage: {validation_result['coverage_percentage']:.1f}%")
                print(f"      • Processing time: {processing_time:.2f}s")

            else:
                # Handle failure case
                test_result = {
                    "question_id": question["id"],
                    "question_category": question["category"],
                    "question_text": question["question"],
                    "test_timestamp": test_start.isoformat(),
                    "processing_time_seconds": processing_time,
                    "correlation_id": str(correlation_id),
                    "success": False,
                    "error_message": response.error_message or "Unknown error",
                    "phoenix_trace_available": self.phoenix_manager._initialized if self.phoenix_manager else False
                }

                print(f"   ❌ Test failed: {test_result['error_message']}")

            print()
            return test_result

        except Exception as e:
            test_end = datetime.now(UTC)
            processing_time = (test_end - test_start).total_seconds()

            error_result = {
                "question_id": question["id"],
                "question_category": question["category"],
                "question_text": question["question"],
                "test_timestamp": test_start.isoformat(),
                "processing_time_seconds": processing_time,
                "correlation_id": str(correlation_id),
                "success": False,
                "error_message": str(e),
                "exception_type": type(e).__name__
            }

            print(f"   ❌ Test exception: {e}")
            print()
            return error_result

    async def run_comprehensive_test_suite(self) -> dict[str, Any]:
        """Run complete test suite with all FDA Part 11 questions."""
        self.start_time = datetime.now(UTC)

        print("3️⃣ Executing Comprehensive Q&A Test Suite")
        print("-" * 45)
        print()

        # Get all test questions
        questions = FDApart11Questions.get_test_questions()
        print(f"📋 Total questions to test: {len(questions)}")
        print()

        # Execute each question test
        for i, question in enumerate(questions, 1):
            print(f"Test {i}/{len(questions)}: {question['id']}")
            result = await self.execute_question_test(question)
            self.test_results.append(result)

            # Small delay between tests
            await asyncio.sleep(1)

        self.end_time = datetime.now(UTC)

        # Generate summary
        return self._generate_test_summary()

    def _generate_test_summary(self) -> dict[str, Any]:
        """Generate comprehensive test summary with analytics."""
        total_tests = len(self.test_results)
        successful_tests = sum(1 for r in self.test_results if r.get("success", False))
        failed_tests = total_tests - successful_tests

        # Calculate metrics for successful tests only
        successful_results = [r for r in self.test_results if r.get("success", False)]

        if successful_results:
            avg_confidence = sum(r.get("confidence_score", 0.0) for r in successful_results) / len(successful_results)
            avg_processing_time = sum(r.get("processing_time_seconds", 0.0) for r in successful_results) / len(successful_results)
            avg_documents_retrieved = sum(r.get("documents_retrieved", 0) for r in successful_results) / len(successful_results)

            # Context quality distribution
            quality_dist = {}
            for result in successful_results:
                quality = result.get("context_quality", "unknown")
                quality_dist[quality] = quality_dist.get(quality, 0) + 1

            # Answer validation metrics
            excellent_answers = sum(1 for r in successful_results
                                  if r.get("answer_validation", {}).get("quality_assessment") == "excellent")
            good_answers = sum(1 for r in successful_results
                             if r.get("answer_validation", {}).get("quality_assessment") == "good")
            acceptable_answers = sum(1 for r in successful_results
                                   if r.get("answer_validation", {}).get("quality_assessment") == "acceptable")
        else:
            avg_confidence = 0.0
            avg_processing_time = 0.0
            avg_documents_retrieved = 0.0
            quality_dist = {}
            excellent_answers = good_answers = acceptable_answers = 0

        return {
            "test_execution_summary": {
                "total_questions_tested": total_tests,
                "successful_tests": successful_tests,
                "failed_tests": failed_tests,
                "success_rate_percentage": (successful_tests / total_tests * 100) if total_tests > 0 else 0,
                "test_start_time": self.start_time.isoformat() if self.start_time else None,
                "test_end_time": self.end_time.isoformat() if self.end_time else None,
                "total_execution_time_seconds": (
                    (self.end_time - self.start_time).total_seconds()
                    if self.start_time and self.end_time else 0
                )
            },

            "performance_metrics": {
                "average_confidence_score": avg_confidence,
                "average_processing_time_seconds": avg_processing_time,
                "average_documents_retrieved": avg_documents_retrieved,
                "context_quality_distribution": quality_dist
            },

            "answer_quality_metrics": {
                "excellent_answers": excellent_answers,
                "good_answers": good_answers,
                "acceptable_answers": acceptable_answers,
                "poor_answers": successful_tests - (excellent_answers + good_answers + acceptable_answers)
            },

            "phoenix_observability": {
                "phoenix_initialized": self.phoenix_manager._initialized if self.phoenix_manager else False,
                "traces_generated": successful_tests,
                "phoenix_ui_url": "http://localhost:6006"
            },

            "detailed_results": self.test_results
        }

    async def cleanup(self):
        """Cleanup resources and shutdown Phoenix with trace persistence."""
        print("4️⃣ Cleaning up and preserving Phoenix traces...")

        if self.phoenix_manager:
            shutdown_phoenix(timeout_seconds=10)
            print("✅ Phoenix shutdown complete - traces preserved")
            print("🌐 Phoenix UI remains accessible for trace review")

        print("✅ Cleanup complete")


async def main():
    """Main test execution function."""
    print("🚀 Starting Context Provider Agent Q&A Testing")
    print()

    # Initialize test framework
    qa_test = ContextProviderQATest(verbose=True)

    try:
        # Setup
        setup_success = await qa_test.setup()
        if not setup_success:
            print("❌ Setup failed, aborting test")
            return

        # Run comprehensive test suite
        summary = await qa_test.run_comprehensive_test_suite()

        # Display summary
        print("🎉 Q&A Test Suite Completed!")
        print("=" * 50)
        print()
        print("📊 Test Execution Summary:")
        exec_summary = summary["test_execution_summary"]
        print(f"   • Total questions: {exec_summary['total_questions_tested']}")
        print(f"   • Successful tests: {exec_summary['successful_tests']}")
        print(f"   • Failed tests: {exec_summary['failed_tests']}")
        print(f"   • Success rate: {exec_summary['success_rate_percentage']:.1f}%")
        print(f"   • Total execution time: {exec_summary['total_execution_time_seconds']:.1f}s")
        print()

        perf_metrics = summary["performance_metrics"]
        print("⚡ Performance Metrics:")
        print(f"   • Average confidence score: {perf_metrics['average_confidence_score']:.3f}")
        print(f"   • Average processing time: {perf_metrics['average_processing_time_seconds']:.2f}s")
        print(f"   • Average documents retrieved: {perf_metrics['average_documents_retrieved']:.1f}")
        print(f"   • Context quality distribution: {perf_metrics['context_quality_distribution']}")
        print()

        quality_metrics = summary["answer_quality_metrics"]
        print("🎯 Answer Quality Metrics:")
        print(f"   • Excellent answers: {quality_metrics['excellent_answers']}")
        print(f"   • Good answers: {quality_metrics['good_answers']}")
        print(f"   • Acceptable answers: {quality_metrics['acceptable_answers']}")
        print(f"   • Poor answers: {quality_metrics['poor_answers']}")
        print()

        phoenix_info = summary["phoenix_observability"]
        print("🔍 Phoenix Observability:")
        print(f"   • Phoenix initialized: {'✅' if phoenix_info['phoenix_initialized'] else '❌'}")
        print(f"   • Traces generated: {phoenix_info['traces_generated']}")
        print(f"   • Phoenix UI: {phoenix_info['phoenix_ui_url']}")
        print()

        # Save results to file
        results_file = Path("/home/anteb/thesis_project/main/tests/test_data/qa_test_results.json")
        with open(results_file, "w") as f:
            json.dump(summary, f, indent=2, default=str)
        print(f"💾 Detailed results saved to: {results_file}")

    finally:
        # Cleanup
        await qa_test.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
