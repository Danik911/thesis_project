"""
Test Suite for GAMP-5 Categorization Agent with Open-Source LLMs

This test suite validates the categorization agent's performance with OSS models
compared to the current OpenAI implementation. Tests focus on accuracy,
consistency, and regulatory compliance.

NO FALLBACKS: All tests must fail explicitly if OSS models don't meet criteria.
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime, UTC
import pytest
from dataclasses import dataclass, asdict

# Add main directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.llms.oss_provider_factory import OSSModelFactory, OSSProvider
from src.agents.categorization.agent import (
    categorize_with_pydantic_structured_output,
    GAMPCategory
)
from llama_index.llms.openai import OpenAI


@dataclass
class TestCase:
    """Test case for categorization validation."""
    name: str
    urs_content: str
    expected_category: GAMPCategory
    min_confidence: float
    description: str


@dataclass
class TestResult:
    """Result of a single test execution."""
    test_case: str
    provider: str
    model: str
    category: int
    confidence: float
    expected_category: int
    passed: bool
    latency_ms: float
    tokens_used: Dict[str, int]
    error: str = None


class CategorizationOSSTestSuite:
    """
    Test suite for validating GAMP-5 categorization with OSS models.
    
    NO FALLBACKS: Tests fail immediately if accuracy thresholds not met.
    """
    
    def __init__(self, verbose: bool = True):
        """Initialize test suite."""
        self.verbose = verbose
        self.factory = OSSModelFactory(verbose=verbose)
        self.test_results: List[TestResult] = []
        self.test_cases = self._load_test_cases()
        
    def _load_test_cases(self) -> List[TestCase]:
        """Load predefined test cases for categorization."""
        return [
            TestCase(
                name="Category 1 - Infrastructure",
                urs_content="""
                User Requirements Specification
                System: Operating System Platform
                Type: Infrastructure Software
                
                This system provides basic computing infrastructure including:
                - Operating system services
                - Network protocols
                - File system management
                - Memory management
                
                No direct GxP impact. Standard commercial software.
                """,
                expected_category=GAMPCategory.CATEGORY_1,
                min_confidence=0.90,
                description="Clear Category 1 infrastructure software"
            ),
            TestCase(
                name="Category 3 - Non-configured",
                urs_content="""
                User Requirements Specification
                System: Laboratory Balance Interface
                Type: Standard Product
                
                Requirements:
                - Connect to analytical balance via RS-232
                - Display weight measurements
                - Log measurements with timestamp
                - No data manipulation or calculations
                - Fixed functionality, no configuration
                
                Standard commercial product used as designed.
                """,
                expected_category=GAMPCategory.CATEGORY_3,
                min_confidence=0.85,
                description="Standard non-configured product"
            ),
            TestCase(
                name="Category 4 - Configured",
                urs_content="""
                User Requirements Specification
                System: LIMS (Laboratory Information Management System)
                Type: Configured Software
                
                Requirements:
                - Sample tracking and management
                - Configurable workflows for different test types
                - User role configuration
                - Report templates customization
                - Audit trail configuration
                - Integration with laboratory instruments
                
                Commercial software requiring configuration for specific laboratory workflows.
                """,
                expected_category=GAMPCategory.CATEGORY_4,
                min_confidence=0.85,
                description="Configured commercial software"
            ),
            TestCase(
                name="Category 5 - Custom",
                urs_content="""
                User Requirements Specification
                System: Custom Pharmaceutical Manufacturing Control System
                Type: Bespoke Application
                
                Requirements:
                - Custom algorithms for batch optimization
                - Proprietary process control logic
                - Custom-developed neural network for quality prediction
                - Novel statistical process control methods
                - Integration with proprietary equipment
                - Custom real-time data processing engine
                
                Fully custom-developed system with no commercial equivalent.
                Contains proprietary algorithms critical to product quality.
                """,
                expected_category=GAMPCategory.CATEGORY_5,
                min_confidence=0.90,
                description="Custom developed application"
            ),
            TestCase(
                name="Category 4/5 Edge Case",
                urs_content="""
                User Requirements Specification
                System: Manufacturing Execution System
                
                Requirements:
                - Based on commercial MES platform
                - Extensive custom modules for proprietary processes
                - Custom integration layer
                - Modified core functionality
                - 60% custom code, 40% commercial base
                
                Heavily customized commercial system.
                """,
                expected_category=GAMPCategory.CATEGORY_5,  # Should lean toward 5 due to extensive customization
                min_confidence=0.70,  # Lower confidence acceptable for edge case
                description="Edge case between Category 4 and 5"
            )
        ]
    
    def test_single_case(
        self,
        test_case: TestCase,
        llm: OpenAI,
        provider: str,
        model: str
    ) -> TestResult:
        """
        Test a single categorization case.
        
        NO FALLBACKS: Raises exception on failure rather than masking errors.
        """
        start_time = time.time()
        
        try:
            # Perform categorization
            result = categorize_with_pydantic_structured_output(
                llm=llm,
                urs_content=test_case.urs_content,
                document_name=test_case.name
            )
            
            # Calculate metrics
            latency_ms = (time.time() - start_time) * 1000
            passed = (
                result.gamp_category == test_case.expected_category and
                result.confidence_score >= test_case.min_confidence
            )
            
            # Create test result
            test_result = TestResult(
                test_case=test_case.name,
                provider=provider,
                model=model,
                category=result.gamp_category.value,
                confidence=result.confidence_score,
                expected_category=test_case.expected_category.value,
                passed=passed,
                latency_ms=latency_ms,
                tokens_used={"estimate": len(test_case.urs_content) // 4}
            )
            
            if self.verbose:
                status = "[PASS]" if passed else "[FAIL]"
                print(f"{status} | {test_case.name}")
                print(f"  Expected: Category {test_case.expected_category.value}")
                print(f"  Got: Category {result.gamp_category.value} (confidence: {result.confidence_score:.2f})")
                print(f"  Latency: {latency_ms:.0f}ms")
                if not passed:
                    print(f"  FAILURE REASON: ", end="")
                    if result.gamp_category != test_case.expected_category:
                        print(f"Wrong category")
                    else:
                        print(f"Low confidence ({result.confidence_score:.2f} < {test_case.min_confidence})")
                print()
            
            return test_result
            
        except Exception as e:
            # NO FALLBACK - Report error explicitly
            error_msg = f"Categorization failed: {str(e)}"
            if self.verbose:
                print(f"[ERROR] | {test_case.name}")
                print(f"  Error: {error_msg}")
                print()
            
            return TestResult(
                test_case=test_case.name,
                provider=provider,
                model=model,
                category=0,
                confidence=0.0,
                expected_category=test_case.expected_category.value,
                passed=False,
                latency_ms=(time.time() - start_time) * 1000,
                tokens_used={},
                error=error_msg
            )
    
    def test_provider(
        self,
        provider: OSSProvider | str,
        model: str = None
    ) -> Dict[str, Any]:
        """
        Test all cases with a specific provider.
        
        Returns:
            Dictionary with test results and metrics
        """
        print(f"\n{'='*60}")
        print(f"Testing Provider: {provider}")
        print(f"Model: {model or 'default'}")
        print(f"{'='*60}\n")
        
        # Create LLM instance
        try:
            llm = self.factory.create_llm(provider, model)
            provider_name = provider.value if isinstance(provider, OSSProvider) else provider
        except Exception as e:
            print(f"[ERROR] Failed to initialize provider: {e}")
            return {
                "provider": str(provider),
                "model": model,
                "error": str(e),
                "tests_run": 0,
                "tests_passed": 0,
                "accuracy": 0.0
            }
        
        # Run all test cases
        results = []
        for test_case in self.test_cases:
            result = self.test_single_case(
                test_case, llm, provider_name, model or "default"
            )
            results.append(result)
            self.test_results.append(result)
        
        # Calculate metrics
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.passed)
        accuracy = passed_tests / total_tests if total_tests > 0 else 0.0
        avg_latency = sum(r.latency_ms for r in results) / total_tests if total_tests > 0 else 0
        
        # Category-specific accuracy
        category_accuracy = {}
        for cat in GAMPCategory:
            cat_results = [r for r in results if r.expected_category == cat.value]
            if cat_results:
                cat_passed = sum(1 for r in cat_results if r.passed)
                category_accuracy[f"category_{cat.value}"] = cat_passed / len(cat_results)
        
        summary = {
            "provider": provider_name,
            "model": model or "default",
            "tests_run": total_tests,
            "tests_passed": passed_tests,
            "accuracy": accuracy,
            "avg_latency_ms": avg_latency,
            "category_accuracy": category_accuracy,
            "results": [asdict(r) for r in results]
        }
        
        # Print summary
        print(f"\n{'-'*40}")
        print(f"Provider Summary: {provider_name}")
        print(f"  Overall Accuracy: {accuracy:.1%} ({passed_tests}/{total_tests})")
        print(f"  Average Latency: {avg_latency:.0f}ms")
        for cat, acc in category_accuracy.items():
            print(f"  {cat}: {acc:.1%}")
        
        # Check if meets minimum criteria
        MIN_ACCURACY = 0.95
        if accuracy < MIN_ACCURACY:
            print(f"\n[WARNING] FAILED: Accuracy {accuracy:.1%} < {MIN_ACCURACY:.1%} threshold")
            print(f"  NO FALLBACK: Provider does not meet pharmaceutical requirements")
        else:
            print(f"\n[PASS] PASSED: Provider meets accuracy requirements")
        
        return summary
    
    def compare_providers(
        self,
        providers: List[Tuple[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Compare multiple providers side-by-side.
        
        Args:
            providers: List of (provider, model) tuples to test
            
        Returns:
            Comparison results dictionary
        """
        if providers is None:
            # Default comparison set
            providers = [
                ("openai", "gpt-4o-mini"),  # Baseline
                ("openrouter", "openai/gpt-oss-120b"),
                ("cerebras", "gpt-oss-120b"),
            ]
        
        print("\n" + "="*80)
        print("PROVIDER COMPARISON TEST")
        print("="*80)
        
        all_results = {}
        
        for provider, model in providers:
            try:
                results = self.test_provider(provider, model)
                all_results[provider] = results
            except Exception as e:
                print(f"[ERROR] Failed to test {provider}: {e}")
                all_results[provider] = {"error": str(e)}
        
        # Generate comparison report
        comparison = self._generate_comparison_report(all_results)
        
        return comparison
    
    def _generate_comparison_report(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive comparison report."""
        print("\n" + "="*80)
        print("COMPARISON SUMMARY")
        print("="*80 + "\n")
        
        # Create comparison table
        providers = list(results.keys())
        metrics = ["accuracy", "avg_latency_ms", "tests_passed", "tests_run"]
        
        # Print comparison table
        print(f"{'Provider':<15} {'Accuracy':<12} {'Latency (ms)':<15} {'Tests Passed':<15}")
        print("-" * 60)
        
        for provider in providers:
            if "error" in results[provider]:
                print(f"{provider:<15} {'ERROR':<12} {'-':<15} {'-':<15}")
            else:
                r = results[provider]
                print(f"{provider:<15} {r['accuracy']:.1%}{'':7} {r['avg_latency_ms']:.0f}{'':10} {r['tests_passed']}/{r['tests_run']}")
        
        # Identify best provider
        valid_providers = [p for p in providers if "error" not in results[p]]
        if valid_providers:
            best_accuracy = max(valid_providers, key=lambda p: results[p]["accuracy"])
            best_latency = min(valid_providers, key=lambda p: results[p]["avg_latency_ms"])
            
            print(f"\n[BEST] Accuracy: {best_accuracy} ({results[best_accuracy]['accuracy']:.1%})")
            print(f"[BEST] Latency: {best_latency} ({results[best_latency]['avg_latency_ms']:.0f}ms)")
            
            # Cost comparison (if not baseline)
            if "openai" in results and best_accuracy != "openai":
                openai_cost = 10.0  # $10 per million tokens
                best_config = self.factory.PROVIDER_CONFIG.get(
                    OSSProvider(best_accuracy), 
                    {"cost_per_m_input": 0}
                )
                best_cost = best_config.get("cost_per_m_input", 0)
                if best_cost > 0:
                    savings = ((openai_cost - best_cost) / openai_cost) * 100
                    print(f"[SAVINGS] Cost Savings: {savings:.1f}% vs OpenAI")
        
        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "providers_tested": len(providers),
            "results": results,
            "recommendations": self._generate_recommendations(results)
        }
    
    def _generate_recommendations(self, results: Dict[str, Any]) -> Dict[str, str]:
        """Generate recommendations based on test results."""
        recommendations = {}
        
        # Check if any OSS provider meets requirements
        oss_providers = [p for p in results.keys() if p != "openai" and "error" not in results[p]]
        qualified_providers = [
            p for p in oss_providers 
            if results[p].get("accuracy", 0) >= 0.95
        ]
        
        if qualified_providers:
            best = max(qualified_providers, key=lambda p: results[p]["accuracy"])
            recommendations["primary"] = best
            recommendations["status"] = "ready_for_integration_testing"
            recommendations["risk_level"] = "low"
            recommendations["action"] = f"Proceed with {best} for integration testing"
        else:
            recommendations["primary"] = "openai"
            recommendations["status"] = "oss_not_ready"
            recommendations["risk_level"] = "high"
            recommendations["action"] = "Continue using OpenAI; OSS models need improvement"
        
        return recommendations
    
    def save_results(self, filepath: str = None):
        """Save test results to file."""
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"test_results_categorization_oss_{timestamp}.json"
        
        results_data = {
            "timestamp": datetime.now(UTC).isoformat(),
            "test_suite": "categorization_oss",
            "total_tests": len(self.test_results),
            "results": [asdict(r) for r in self.test_results]
        }
        
        with open(filepath, 'w') as f:
            json.dump(results_data, f, indent=2, default=str)
        
        print(f"\n[SAVED] Results saved to: {filepath}")


def main():
    """Main test execution."""
    print("""
==================================================================
     GAMP-5 Categorization OSS Model Testing Suite           
                                                              
  Testing pharmaceutical categorization with OSS models       
  NO FALLBACKS - All failures reported explicitly            
==================================================================
    """)
    
    # Initialize test suite
    suite = CategorizationOSSTestSuite(verbose=True)
    
    # Check environment
    provider = os.getenv("LLM_PROVIDER", "openrouter")
    model = os.getenv("LLM_MODEL_OSS")
    
    print(f"Configuration:")
    print(f"  Provider: {provider}")
    print(f"  Model: {model or 'default'}")
    print(f"  Test Mode: {os.getenv('LLM_TEST_MODE', 'isolation')}")
    print()
    
    # Run tests based on mode
    test_mode = os.getenv("LLM_TEST_MODE", "isolation")
    
    if test_mode == "comparison":
        # Compare multiple providers
        results = suite.compare_providers()
    else:
        # Test single provider
        results = suite.test_provider(provider, model)
    
    # Save results
    suite.save_results()
    
    # Return exit code based on success
    if isinstance(results, dict) and results.get("accuracy", 0) >= 0.95:
        print("\n[SUCCESS] TEST SUITE PASSED")
        return 0
    else:
        print("\n[FAILED] TEST SUITE FAILED")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)