#!/usr/bin/env python3
"""
Performance Validation Test for ALCOA+ Enhancement (Task 23)
"""

import sys
from pathlib import Path

sys.path.insert(0, "src")
import asyncio
import logging
import time

from compliance_validation.alcoa_scorer import ALCOAScorer
from compliance_validation.evidence_collector import EvidenceCollector
from compliance_validation.metadata_injector import get_metadata_injector

logging.basicConfig(level=logging.WARNING)  # Reduce noise
logger = logging.getLogger(__name__)

async def test_performance_validation():
    """Test performance of ALCOA+ metadata injection under load."""
    try:
        print("ALCOA+ Performance Validation Test")
        print("="*50)

        # Setup
        metadata_injector = get_metadata_injector()
        output_dir = Path("output/perf_test")
        output_dir.mkdir(parents=True, exist_ok=True)
        evidence_collector = EvidenceCollector(output_directory=output_dir)
        alcoa_scorer = ALCOAScorer(evidence_collector)

        # Test data sizes
        test_suites = [
            {"size": "Small", "test_cases": 1, "iterations": 10},
            {"size": "Medium", "test_cases": 5, "iterations": 5},
            {"size": "Large", "test_cases": 20, "iterations": 2}
        ]

        total_processed = 0
        total_time = 0
        all_scores = []

        for test_config in test_suites:
            suite_size = test_config["size"]
            test_case_count = test_config["test_cases"]
            iterations = test_config["iterations"]

            print(f"\nTesting {suite_size} Test Suites ({test_case_count} test cases, {iterations} iterations):")

            suite_times = []
            suite_scores = []

            for i in range(iterations):
                # Create test data
                test_data = {
                    "suite_id": f"PERF-{suite_size}-{i:02d}",
                    "document_name": f"Performance Test Document {suite_size}",
                    "test_cases": [
                        {
                            "test_id": f"PERF-TC-{j:03d}",
                            "test_name": f"Performance Test Case {j}",
                            "objective": f"Performance validation objective {j}"
                        }
                        for j in range(test_case_count)
                    ],
                    "total_test_count": test_case_count
                }

                # Time metadata injection
                start_time = time.time()

                enhanced_dict = metadata_injector.inject_test_suite_metadata(
                    test_suite_dict=test_data,
                    llm_response={"confidence_score": 0.90 + (i * 0.01)},
                    generation_context={
                        "source_document_id": f"PERF_TEST_{suite_size}_{i}",
                        "gamp_category": 4,
                        "pharmaceutical_validation": True,
                        "generation_method": "PerformanceTest"
                    }
                )

                injection_time = time.time() - start_time
                suite_times.append(injection_time)

                # Quick ALCOA+ score validation (sample only)
                if i == 0:  # Only score first iteration to save time
                    assessment = alcoa_scorer.assess_system_data_integrity(
                        system_name=f"perf_test_{suite_size.lower()}",
                        data_samples=[enhanced_dict],
                        target_score=9.0
                    )
                    suite_scores.append(assessment.overall_score)

                total_processed += 1
                total_time += injection_time

            # Report suite performance
            avg_time = sum(suite_times) / len(suite_times)
            max_time = max(suite_times)
            min_time = min(suite_times)

            print(f"  Injection Time - Avg: {avg_time*1000:.1f}ms, Min: {min_time*1000:.1f}ms, Max: {max_time*1000:.1f}ms")

            if suite_scores:
                print(f"  ALCOA+ Score: {suite_scores[0]:.2f}/10")
                all_scores.extend(suite_scores)

        # Overall performance summary
        avg_overall_time = (total_time / total_processed) * 1000  # Convert to ms
        throughput = 60 / (total_time / total_processed) if total_time > 0 else 0  # Suites per minute
        avg_score = sum(all_scores) / len(all_scores) if all_scores else 0

        print()
        print("="*50)
        print("PERFORMANCE SUMMARY")
        print("="*50)
        print(f"Total Test Suites Processed: {total_processed}")
        print(f"Total Processing Time: {total_time:.3f}s")
        print(f"Average Injection Time: {avg_overall_time:.1f}ms per suite")
        print(f"Throughput: {throughput:.1f} suites per minute")
        print(f"Average ALCOA+ Score: {avg_score:.2f}/10")

        # Performance criteria
        performance_targets = {
            "injection_time_ms": 200,  # <200ms per suite
            "throughput_per_min": 100,  # >100 suites per minute
            "alcoa_score": 9.0  # >9.0 ALCOA+ score
        }

        meets_performance = (
            avg_overall_time <= performance_targets["injection_time_ms"] and
            throughput >= performance_targets["throughput_per_min"] and
            avg_score >= performance_targets["alcoa_score"]
        )

        print()
        print("PERFORMANCE CRITERIA:")
        print(f"  Injection Time: {'[PASS]' if avg_overall_time <= performance_targets['injection_time_ms'] else '[FAIL]'} "
              f"({avg_overall_time:.1f}ms <= {performance_targets['injection_time_ms']}ms)")
        print(f"  Throughput: {'[PASS]' if throughput >= performance_targets['throughput_per_min'] else '[FAIL]'} "
              f"({throughput:.1f} >= {performance_targets['throughput_per_min']} suites/min)")
        print(f"  ALCOA+ Score: {'[PASS]' if avg_score >= performance_targets['alcoa_score'] else '[FAIL]'} "
              f"({avg_score:.2f} >= {performance_targets['alcoa_score']})")

        print()
        print("="*50)
        print(f"PERFORMANCE VALIDATION: {'[SUCCESS]' if meets_performance else '[NEEDS OPTIMIZATION]'}")
        print("="*50)

        return meets_performance

    except Exception as e:
        logger.error(f"Performance validation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_performance_validation())
    print(f"\nPerformance Test Result: {'PASSED' if result else 'FAILED'}")
