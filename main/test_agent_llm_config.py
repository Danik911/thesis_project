#!/usr/bin/env python3
"""
Test agent-specific LLM configuration.
Verify OSS for most agents, OpenAI for OQ generation.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add main to path
sys.path.insert(0, str(Path(__file__).parent))

def test_agent_llm_config():
    """Test that each agent gets the correct LLM."""
    
    print("="*60)
    print("AGENT LLM CONFIGURATION TEST")
    print("Expected: OSS (DeepSeek) for all agents except OQ")
    print("Expected: OpenAI for OQ generation only")
    print("="*60)
    
    # Import configuration
    from src.config.agent_llm_config import AgentLLMConfig, AgentType
    
    # Get configuration info
    config_info = AgentLLMConfig.get_agent_config_info()
    print(f"\nConfiguration Strategy: {config_info['strategy']}")
    print(f"OSS Model: {config_info['oss_model']}")
    print(f"OQ Model: {config_info['oq_model']}")
    print(f"OSS API Key Present: {config_info['oss_api_key_present']}")
    print(f"OpenAI API Key Present: {config_info['openai_api_key_present']}")
    
    if not config_info['oss_api_key_present'] or not config_info['openai_api_key_present']:
        print("\nERROR: Missing API keys!")
        return False
    
    print("\nAgent Assignments:")
    for agent, model in config_info['agent_assignments'].items():
        print(f"  {agent}: {model}")
    
    # Test each agent type
    print("\nTesting Agent LLM Instances:")
    
    success = True
    
    # Test categorization (should use OSS)
    try:
        llm = AgentLLMConfig.get_llm_for_agent(AgentType.CATEGORIZATION)
        model_name = getattr(llm, 'model', 'unknown')
        print(f"  Categorization: {model_name}")
        if 'deepseek' not in model_name.lower():
            print("    WARNING: Expected DeepSeek model")
            success = False
    except Exception as e:
        print(f"  Categorization: ERROR - {e}")
        success = False
    
    # Test SME (should use OSS)
    try:
        llm = AgentLLMConfig.get_llm_for_agent(AgentType.SME)
        model_name = getattr(llm, 'model', 'unknown')
        print(f"  SME: {model_name}")
        if 'deepseek' not in model_name.lower():
            print("    WARNING: Expected DeepSeek model")
            success = False
    except Exception as e:
        print(f"  SME: ERROR - {e}")
        success = False
    
    # Test OQ Generator (should use OpenAI)
    try:
        llm = AgentLLMConfig.get_llm_for_agent(AgentType.OQ_GENERATOR)
        model_name = getattr(llm, 'model', 'unknown')
        print(f"  OQ Generator: {model_name}")
        if 'gpt' not in model_name.lower():
            print("    WARNING: Expected GPT model")
            success = False
    except Exception as e:
        print(f"  OQ Generator: ERROR - {e}")
        success = False
    
    return success

def test_oq_generator():
    """Test OQ generator with OpenAI."""
    
    print("\n" + "="*60)
    print("TESTING OQ GENERATOR WITH OPENAI")
    print("="*60)
    
    from src.agents.oq_generator.generator import OQTestGenerator
    from src.core.events import GAMPCategory
    
    # Create generator (should use OpenAI automatically)
    generator = OQTestGenerator(verbose=True)
    
    # Check LLM type
    llm_model = getattr(generator.llm, 'model', 'unknown')
    print(f"\nOQ Generator LLM: {llm_model}")
    
    if 'gpt' not in llm_model.lower():
        print("ERROR: OQ Generator not using OpenAI!")
        return False
    
    # Try simple generation
    print("\nTesting OQ generation with OpenAI...")
    
    try:
        test_urs = """
        Pharmaceutical Manufacturing System Requirements:
        - User authentication and access control
        - Batch record management
        - Electronic signatures per 21 CFR Part 11
        - Audit trail for all changes
        - Report generation for compliance
        """
        
        result = generator.generate_oq_test_suite(
            gamp_category=GAMPCategory.CATEGORY_5,
            urs_content=test_urs,
            document_name="test_urs.md"
        )
        
        if result and hasattr(result, 'test_cases'):
            test_count = len(result.test_cases)
            print(f"Generated {test_count} tests")
            
            if 23 <= test_count <= 33:
                print("SUCCESS: Correct number of tests generated")
                return True
            else:
                print(f"WARNING: Expected 23-33 tests, got {test_count}")
                return False
        else:
            print("ERROR: No test suite generated")
            return False
            
    except Exception as e:
        print(f"ERROR: Generation failed - {e}")
        return False

if __name__ == "__main__":
    # Test configuration
    config_success = test_agent_llm_config()
    
    # Test OQ generation
    oq_success = test_oq_generator()
    
    print("\n" + "="*60)
    print("RESULTS:")
    print(f"  Configuration: {'PASSED' if config_success else 'FAILED'}")
    print(f"  OQ Generation: {'PASSED' if oq_success else 'FAILED'}")
    print("="*60)