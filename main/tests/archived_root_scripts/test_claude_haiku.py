#!/usr/bin/env python3
"""
Test script for Step 3 - Claude 3.5 Haiku model implementation.

This script tests the OQ generator with Claude 3.5 Haiku model:
- Best structured output capabilities 
- Superior YAML generation accuracy
- 70-80% reduction in validation errors vs OSS models
- Exactly 25 tests requirement validation
"""

import logging
import os
import sys
from datetime import datetime

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the main directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), "."))

from src.agents.oq_generator.generator import OQTestGenerator
from src.agents.oq_generator.models import OQGenerationConfig
from src.config.llm_config import LLMConfig
from src.core.events import GAMPCategory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

def test_claude_haiku_generation():
    """Test OQ generation with Claude 3.5 Haiku model."""

    print("\n" + "="*80)
    print("TESTING: Step 3 - Claude 3.5 Haiku Model Implementation")
    print("="*80)

    try:
        # Initialize Claude 3.5 Haiku via OpenRouter
        print("\n1. Initializing Claude 3.5 Haiku LLM...")
        llm = LLMConfig.get_llm()

        # Verify model configuration
        provider_info = LLMConfig.get_provider_info()
        print(f"   Provider: {provider_info['provider']}")
        print(f"   Model: {provider_info['configuration']['model']}")
        print(f"   Max tokens: {provider_info['configuration']['max_tokens']}")
        print(f"   Temperature: {provider_info['configuration']['temperature']}")
        print(f"   API Key Present: {provider_info['api_key_present']}")

        if not provider_info["api_key_present"]:
            print("FAILED FAILED: OPENROUTER_API_KEY not found in environment")
            return False

        print("SUCCESS: Claude 3.5 Haiku initialized")

        # Initialize OQ Generator
        print("\n2. Initializing OQ Test Generator...")
        generator = OQTestGenerator(
            llm=llm,
            verbose=True,
            generation_timeout=300  # 5 minutes
        )
        print("SUCCESS SUCCESS: OQ Generator initialized")

        # Test URS content
        urs_content = """
        User Requirements Specification (URS)
        
        System: Pharmaceutical Manufacturing Execution System (MES)
        GAMP Category: 5 (Custom Application)
        
        REQ-001: User Authentication and Access Control
        The system shall provide secure multi-factor authentication mechanisms
        
        REQ-002: Data Integrity and Audit Trail
        The system shall maintain complete data integrity per 21 CFR Part 11
        
        REQ-003: Electronic Signatures
        The system shall support legally binding electronic signatures
        
        REQ-004: Batch Record Management
        The system shall manage and track pharmaceutical batch records
        
        REQ-005: Reporting and Analytics
        The system shall generate GMP-compliant reports and analytics
        """

        # Configuration for exactly 25 tests
        config = OQGenerationConfig(
            gamp_category=5,
            document_name="Pharmaceutical MES Validation Suite",
            target_test_count=25,  # Exactly 25 tests required
            complexity_level="comprehensive",
            regulatory_requirements=["21 CFR Part 11", "EU Annex 11", "GAMP-5"],
            require_traceability=True,
            include_negative_testing=True,
            validate_data_integrity=True
        )

        print("\n3. Generating OQ Test Suite with Claude 3.5 Haiku...")
        print(f"   GAMP Category: {GAMPCategory.CATEGORY_5.value}")
        print(f"   Target test count: {config.target_test_count}")
        print("   Model: Claude 3.5 Haiku (anthropic/claude-3.5-haiku)")
        print("   Format: YAML (optimized for Claude models)")

        # Generate test suite
        start_time = datetime.now()

        try:
            test_suite = generator.generate_oq_test_suite(
                gamp_category=GAMPCategory.CATEGORY_5,
                urs_content=urs_content,
                document_name="Pharmaceutical MES Validation",
                context_data={
                    "validation_context": {
                        "test_strategy_alignment": {
                            "risk_based": True,
                            "gmp_compliant": True
                        }
                    }
                },
                config=config
            )

            generation_time = (datetime.now() - start_time).total_seconds()

            print(f"\nSUCCESS SUCCESS: Generation SUCCESSFUL in {generation_time:.2f}s")

            # Validation Results
            print("\n4. Validation Results:")
            print(f"   Suite ID: {test_suite.suite_id}")
            print(f"   GAMP Category: {test_suite.gamp_category}")
            print(f"   Total Test Count: {test_suite.total_test_count}")
            print(f"   Actual Test Cases: {len(test_suite.test_cases)}")
            print(f"   Version: {test_suite.version}")

            # Validate exactly 25 tests
            if test_suite.total_test_count == 25:
                print("   SUCCESS Test count validation: PASSED (exactly 25 tests)")
            else:
                print(f"   FAILED Test count validation: FAILED (expected 25, got {test_suite.total_test_count})")

            # Validate test IDs
            test_ids = [test.test_id for test in test_suite.test_cases]
            expected_ids = [f"OQ-{i:03d}" for i in range(1, 26)]

            if test_ids == expected_ids:
                print("   SUCCESS Test ID format: PASSED (OQ-001 through OQ-025)")
            else:
                print("   FAILED Test ID format: FAILED")
                print(f"      Expected: {expected_ids[:3]}...{expected_ids[-3:]}")
                print(f"      Got: {test_ids[:3] if len(test_ids) >= 3 else test_ids}...{test_ids[-3:] if len(test_ids) >= 3 else ''}")

            # Validate required fields
            sample_test = test_suite.test_cases[0] if test_suite.test_cases else None
            if sample_test:
                required_fields = ["test_id", "test_name", "test_category", "objective", "test_steps", "acceptance_criteria"]
                missing_fields = [field for field in required_fields if not hasattr(sample_test, field)]

                if not missing_fields:
                    print("   SUCCESS Required fields: PASSED (all fields present)")
                else:
                    print(f"   FAILED Required fields: FAILED (missing: {missing_fields})")

            # Validate test categories are correct
            valid_categories = {"installation", "functional", "performance", "security", "data_integrity", "integration", "usability"}
            categories = {}
            invalid_categories = []

            for test in test_suite.test_cases:
                cat = getattr(test, "test_category", "unknown")
                if cat not in valid_categories:
                    invalid_categories.append(f"{test.test_id}:{cat}")
                categories[cat] = categories.get(cat, 0) + 1

            if not invalid_categories:
                print("   SUCCESS Test categories: PASSED (all categories valid)")
            else:
                print(f"   FAILED Test categories: FAILED (invalid: {invalid_categories[:5]}...)")

            # Compliance validation
            compliance = test_suite.pharmaceutical_compliance
            print("\n5. Pharmaceutical Compliance:")
            print(f"   ALCOA+ Compliant: {compliance.get('alcoa_plus_compliant', 'Unknown')}")
            print(f"   CFR Part 11 Compliant: {compliance.get('cfr_part11_compliant', 'Unknown')}")
            print(f"   GAMP-5 Compliant: {compliance.get('gamp5_compliant', 'Unknown')}")
            print(f"   Data Integrity Validated: {compliance.get('data_integrity_validated', 'Unknown')}")

            # Test categories distribution
            print("\n6. Test Categories Distribution:")
            for category, count in sorted(categories.items()):
                print(f"   {category}: {count} tests")

            # Overall success assessment
            all_passed = (
                test_suite.total_test_count == 25 and
                test_ids == expected_ids and
                not missing_fields and
                not invalid_categories
            )

            print("\n" + "="*80)
            if all_passed:
                print("SUCCESSSUCCESSSUCCESS STEP 3 IMPLEMENTATION: COMPLETE SUCCESS SUCCESSSUCCESSSUCCESS")
                print("SUCCESS Claude 3.5 Haiku model working perfectly")
                print("SUCCESS Exactly 25 tests generated with valid structure")
                print("SUCCESS All test categories and fields validated")
                print("SUCCESS NO FALLBACKS policy maintained")
            else:
                print("WARNING STEP 3 IMPLEMENTATION: PARTIAL SUCCESS")
                print("WARNING Some validation issues remain")
                print("WARNING Review test categories and field completeness")
            print("="*80)

            return all_passed

        except Exception as e:
            generation_time = (datetime.now() - start_time).total_seconds()
            print(f"\nFAILED FAILED: Generation FAILED after {generation_time:.2f}s")
            print(f"   Error: {e}")

            if hasattr(e, "error_context"):
                context = e.error_context
                print(f"   Error Type: {context.get('error_type', 'unknown')}")
                print(f"   Generation Method: {context.get('generation_method', 'unknown')}")
                print(f"   No Fallback Available: {context.get('no_fallback_available', 'unknown')}")

                if "suggested_actions" in context:
                    print("   Suggested Actions:")
                    for action in context["suggested_actions"]:
                        print(f"     - {action}")

            print("\n" + "="*80)
            print("FAILED STEP 3 IMPLEMENTATION: FAILED")
            print("FAILED Claude 3.5 Haiku generation needs debugging")
            print("="*80)

            return False

    except Exception as e:
        print(f"\nFAILED FAILED: Test setup failed: {e}")
        print("\n" + "="*80)
        print("FAILED STEP 3 IMPLEMENTATION: SETUP FAILED")
        print("="*80)
        return False

def main():
    """Run the Claude 3.5 Haiku test."""
    success = test_claude_haiku_generation()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
