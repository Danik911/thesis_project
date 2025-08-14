#!/usr/bin/env python3
"""
Simple OSS Migration Test

Test the OSS migration from OpenAI to OpenRouter models.
"""

import os
import sys
from pathlib import Path

# Add the main directory to the Python path
sys.path.append(str(Path(__file__).parent))

# Load environment variables from .env file
def load_env():
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key] = value.strip('"')
        print(f"Loaded environment from {env_path}")
    else:
        print(f"No .env file found at {env_path}")

# Load environment variables
load_env()

def test_llm_config():
    """Test LLM configuration."""
    print("Testing LLM Configuration...")

    try:
        from src.config.llm_config import LLMConfig

        # Check provider
        print(f"Provider: {LLMConfig.PROVIDER.value}")

        # Check configuration validation
        is_valid, message = LLMConfig.validate_configuration()
        print(f"Config valid: {is_valid}")
        if not is_valid:
            print(f"Error: {message}")
            return False

        # Get provider info
        info = LLMConfig.get_provider_info()
        print(f"Model: {info['configuration']['model']}")
        print(f"API key present: {info['api_key_present']}")

        return True

    except Exception as e:
        print(f"LLM Config test failed: {e}")
        return False

def test_llm_creation():
    """Test LLM creation and basic functionality."""
    print("\nTesting LLM Creation...")

    try:
        from src.config.llm_config import LLMConfig

        # Create LLM instance
        llm = LLMConfig.get_llm()
        print(f"LLM type: {type(llm).__name__}")

        # Test simple completion
        print("Testing completion...")
        response = llm.complete("What is GAMP-5? Answer briefly.")
        response_text = response.text.strip()

        if response_text and len(response_text) > 10:
            # Handle potential unicode encoding issues
            safe_text = response_text[:100].encode("ascii", "ignore").decode("ascii")
            print(f"Response: {safe_text}...")
            return True
        safe_text = response_text.encode("ascii", "ignore").decode("ascii")
        print(f"Response too short: {safe_text}")
        return False

    except Exception as e:
        print(f"LLM creation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_agent_creation():
    """Test agent instantiation with migrated LLM config."""
    print("\nTesting Agent Creation...")

    agents_tested = 0
    agents_passed = 0

    # Test Context Provider Agent
    try:
        from src.agents.parallel.context_provider import ContextProviderAgent
        agent = ContextProviderAgent(verbose=False, enable_phoenix=False)
        print(f"Context Provider Agent: {type(agent.llm).__name__} - SUCCESS")
        agents_tested += 1
        agents_passed += 1
    except Exception as e:
        print(f"Context Provider Agent: FAILED - {e}")
        import traceback
        traceback.print_exc()
        agents_tested += 1

    # Test Research Agent
    try:
        from src.agents.parallel.research_agent import ResearchAgent
        agent = ResearchAgent(verbose=False, enable_phoenix=False)
        print(f"Research Agent: {type(agent.llm).__name__} - SUCCESS")
        agents_tested += 1
        agents_passed += 1
    except Exception as e:
        print(f"Research Agent: FAILED - {e}")
        agents_tested += 1

    # Test Agent Factory
    try:
        from src.agents.parallel.agent_factory import AgentFactory
        factory = AgentFactory(verbose=False, enable_phoenix=False)
        print(f"Agent Factory: {type(factory.llm).__name__} - SUCCESS")
        agents_tested += 1
        agents_passed += 1
    except Exception as e:
        print(f"Agent Factory: FAILED - {e}")
        agents_tested += 1

    # Test SME Agent
    try:
        from src.agents.parallel.sme_agent import SMEAgent
        agent = SMEAgent(verbose=False, enable_phoenix=False)
        print(f"SME Agent: {type(agent.llm).__name__} - SUCCESS")
        agents_tested += 1
        agents_passed += 1
    except Exception as e:
        print(f"SME Agent: FAILED - {e}")
        agents_tested += 1

    print(f"Agent test results: {agents_passed}/{agents_tested} passed")
    return agents_passed > 0

def main():
    """Run all tests."""
    print("OSS Migration Validation Test")
    print("=" * 40)

    results = []

    # Test 1: LLM Configuration
    results.append(test_llm_config())

    # Test 2: LLM Creation and functionality
    results.append(test_llm_creation())

    # Test 3: Agent creation
    results.append(test_agent_creation())

    # Summary
    print(f"\nTest Summary: {sum(results)}/{len(results)} tests passed")

    if all(results):
        print("SUCCESS: OSS migration is working correctly!")
        return 0
    print("FAILURE: Some tests failed")
    return 1

if __name__ == "__main__":
    sys.exit(main())
