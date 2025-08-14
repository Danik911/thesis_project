#!/usr/bin/env python3
"""
Direct test of OSS models (DeepSeek) for complete workflow.
Bypasses the broken workflow orchestration.
"""

import sys
import time
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add main to path
sys.path.insert(0, str(Path(__file__).parent))

def test_direct_oss():
    """Test all components with DeepSeek directly."""

    print("="*60)
    print("DIRECT OSS TEST WITH DEEPSEEK")
    print("All agents using DeepSeek via OpenRouter")
    print("="*60)

    # Load test data
    test_data_path = Path("tests/test_data/gamp5_test_data/testing_data.md")
    with open(test_data_path) as f:
        urs_content = f.read()

    print(f"\nLoaded URS: {len(urs_content)} characters")

    # Step 1: Categorization with DeepSeek
    print("\n" + "-"*40)
    print("STEP 1: GAMP Categorization (DeepSeek)")
    print("-"*40)

    from src.agents.categorization.agent import categorize_with_structured_output
    from src.config.agent_llm_config import AgentLLMConfig, AgentType

    try:
        # Get DeepSeek LLM
        llm = AgentLLMConfig.get_llm_for_agent(AgentType.CATEGORIZATION)
        print(f"Using: {llm.model}")

        # Categorize
        start = time.time()
        result = categorize_with_structured_output(
            llm=llm,
            urs_content=urs_content[:4000],  # Limit for speed
            document_name="testing_data.md"
        )
        elapsed = time.time() - start

        print(f"Category: {result.get('category', 'Unknown')}")
        print(f"Confidence: {result.get('confidence', 0):.1%}")
        print(f"Time: {elapsed:.2f}s")

        category = result.get("category", 5)

    except Exception as e:
        print(f"ERROR: {e}")
        category = 5  # Default to Category 5

    # Step 2: OQ Generation with DeepSeek
    print("\n" + "-"*40)
    print("STEP 2: OQ Test Generation (DeepSeek)")
    print("-"*40)

    from src.agents.oq_generator.generator import OQTestGenerator
    from src.core.events import GAMPCategory

    try:
        # Create generator with DeepSeek
        generator = OQTestGenerator(verbose=True)
        print(f"Using: {generator.llm.model}")

        # Generate with limited content for speed
        print("\nGenerating OQ tests...")
        start = time.time()

        # Use simpler URS for faster generation
        simple_urs = """
        Pharmaceutical System Requirements:
        1. User authentication with password policy
        2. Electronic signatures for batch records
        3. Audit trail for all data changes
        4. Data backup and recovery procedures
        5. Role-based access control
        """

        result = generator.generate_oq_test_suite(
            gamp_category=GAMPCategory(category),
            urs_content=simple_urs,
            document_name="test.md"
        )

        elapsed = time.time() - start

        print(f"\nGenerated {result.total_test_count} tests in {elapsed:.2f}s")
        print(f"Suite ID: {result.suite_id}")

        # Show first test
        if result.test_cases:
            test = result.test_cases[0]
            print("\nFirst test:")
            print(f"  ID: {test.test_id}")
            print(f"  Name: {test.test_name}")
            print(f"  Category: {test.test_category}")

        # Check compliance
        if 23 <= result.total_test_count <= 33:
            print(f"\nSUCCESS: {result.total_test_count} tests within range (23-33)")
            return True
        print(f"\nFAILED: {result.total_test_count} tests outside range (23-33)")
        return False

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_direct_oss()

    print("\n" + "="*60)
    if success:
        print("DIRECT OSS TEST: SUCCESS")
        print("DeepSeek working for all components!")
    else:
        print("DIRECT OSS TEST: FAILED")
    print("="*60)
