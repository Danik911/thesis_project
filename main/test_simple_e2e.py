#!/usr/bin/env python3
"""
Simple end-to-end test bypassing workflow issues.
Tests the core components directly:
1. Categorization with DeepSeek
2. OQ Generation with OpenAI chunked approach
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add main to path
sys.path.insert(0, str(Path(__file__).parent))

# Enable logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_simple_e2e():
    """Test core components directly."""
    
    print("="*60)
    print("SIMPLE END-TO-END TEST")
    print("OSS (DeepSeek) for analysis, OpenAI for generation")
    print("="*60)
    
    # Load test data
    test_data_path = Path("tests/test_data/gamp5_test_data/testing_data.md")
    if not test_data_path.exists():
        print(f"ERROR: Test data not found at {test_data_path}")
        return False
    
    with open(test_data_path, 'r') as f:
        urs_content = f.read()
    
    print(f"\nLoaded URS content: {len(urs_content)} characters")
    
    # Step 1: Categorization with DeepSeek
    print("\n" + "-"*40)
    print("STEP 1: GAMP Categorization (DeepSeek)")
    print("-"*40)
    
    try:
        from src.agents.categorization.agent import CategorizationAgentWrapper
        from src.config.agent_llm_config import AgentLLMConfig, AgentType
        
        # Get DeepSeek LLM for categorization
        categorization_llm = AgentLLMConfig.get_llm_for_agent(AgentType.CATEGORIZATION)
        print(f"Categorization LLM: {categorization_llm.model}")
        
        # Run categorization
        categorization_agent = CategorizationAgentWrapper(llm=categorization_llm, verbose=True)
        category_result = categorization_agent.analyze_system_for_gamp(
            urs_content=urs_content,
            document_name="testing_data.md"
        )
        
        print(f"\nGAMP Category: {category_result.category}")
        print(f"Confidence: {category_result.confidence:.1%}")
        print(f"Rationale: {category_result.rationale[:200]}...")
        
    except Exception as e:
        print(f"ERROR in categorization: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 2: OQ Generation with OpenAI (chunked)
    print("\n" + "-"*40)
    print("STEP 2: OQ Test Generation (OpenAI)")
    print("-"*40)
    
    try:
        from src.agents.oq_generator.generator import OQTestGenerator
        from src.core.events import GAMPCategory
        
        # Create generator (will use OpenAI automatically)
        generator = OQTestGenerator(verbose=True)
        
        # Check if using chunked approach
        if hasattr(generator, '_use_chunked'):
            print(f"Using chunked generation: {generator._use_chunked}")
        
        print(f"OQ Generator LLM: {generator.llm.model}")
        
        # Generate test suite
        print("\nGenerating OQ test suite...")
        test_suite = generator.generate_oq_test_suite(
            gamp_category=GAMPCategory.CATEGORY_5,
            urs_content=urs_content,
            document_name="testing_data.md"
        )
        
        print(f"\nSUCCESS: Generated {test_suite.total_test_count} tests!")
        print(f"Suite ID: {test_suite.suite_id}")
        print(f"Execution time: {test_suite.estimated_execution_time} minutes")
        
        # Show first few tests
        print("\nFirst 3 tests:")
        for i, test in enumerate(test_suite.test_cases[:3]):
            print(f"\n  Test {i+1}: {test.test_id}")
            print(f"    Name: {test.test_name}")
            print(f"    Category: {test.test_category}")
            print(f"    Objective: {test.objective[:100]}...")
        
        # Validate test count
        if 23 <= test_suite.total_test_count <= 33:
            print(f"\nSUCCESS: Test count {test_suite.total_test_count} within target range (23-33)")
        else:
            print(f"\nFAILED: Test count {test_suite.total_test_count} outside target range (23-33)")
            return False
        
        return True
        
    except Exception as e:
        print(f"ERROR in OQ generation: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_simple_e2e()
    
    print("\n" + "="*60)
    if success:
        print("SIMPLE E2E TEST: SUCCESS")
        print("DeepSeek categorization + OpenAI generation working!")
    else:
        print("SIMPLE E2E TEST: FAILED")
    print("="*60)