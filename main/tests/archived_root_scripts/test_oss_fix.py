#!/usr/bin/env python
"""
Test script for OSS model compatibility fixes.

This script tests the OpenRouter compatibility wrapper and validates
that it can create FunctionAgent instances without Pydantic validation errors.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_openrouter_compat():
    """Test OpenRouter compatibility wrapper."""
    print("=== Testing OpenRouter Compatibility Wrapper ===")

    # Check API key
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("[ERROR] OPENROUTER_API_KEY not found in environment")
        return False

    print(f"[OK] OPENROUTER_API_KEY found: {api_key[:10]}...")

    try:
        # Import and test LLM config
        from src.config.llm_config import LLMConfig, ModelProvider

        # Set provider to OpenRouter
        LLMConfig.PROVIDER = ModelProvider.OPENROUTER

        print("[OK] LLM config imported successfully")
        print(f"   Provider: {LLMConfig.PROVIDER.value}")
        print(f"   Model: {LLMConfig.MODELS[LLMConfig.PROVIDER]['model']}")

        # Test LLM creation
        llm = LLMConfig.get_llm()
        print(f"[OK] LLM instance created: {type(llm).__name__}")
        print(f"   Model: {llm.model}")
        print(f"   Type: {llm}")

        return True

    except Exception as e:
        print(f"[ERROR] LLM creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_function_agent_compatibility():
    """Test that OpenRouter LLM works with FunctionAgent."""
    print("\n=== Testing FunctionAgent Compatibility ===")

    try:
        from llama_index.core.agent.workflow import FunctionAgent
        from llama_index.core.tools import FunctionTool
        from src.config.llm_config import LLMConfig, ModelProvider

        # Set provider to OpenRouter
        LLMConfig.PROVIDER = ModelProvider.OPENROUTER

        # Create LLM instance
        llm = LLMConfig.get_llm()
        print(f"[OK] LLM created: {type(llm).__name__}")

        # Create a simple tool for testing
        def test_tool(query: str) -> str:
            """A simple test tool."""
            return f"Test response for: {query}"

        tool = FunctionTool.from_defaults(test_tool)
        print("[OK] Test tool created")

        # Try to create FunctionAgent - this is where the validation error occurred
        try:
            agent = FunctionAgent(
                llm=llm,
                tools=[tool],
                max_iterations=5,
                verbose=True
            )
            print("[OK] FunctionAgent created successfully!")
            print(f"   Agent type: {type(agent).__name__}")
            print(f"   LLM type: {type(agent.llm).__name__}")
            print(f"   Tools count: {len(agent.tools)}")

            return True

        except Exception as e:
            print(f"[ERROR] FunctionAgent creation failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    except Exception as e:
        print(f"[ERROR] Setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_simple_llm_call():
    """Test a simple LLM API call."""
    print("\n=== Testing Simple LLM Call ===")

    try:
        from src.config.llm_config import LLMConfig, ModelProvider

        # Set provider to OpenRouter
        LLMConfig.PROVIDER = ModelProvider.OPENROUTER

        # Create LLM
        llm = LLMConfig.get_llm()

        # Test simple completion
        response = llm.complete("Say 'Hello from OpenRouter OSS model!'")
        print("[OK] LLM call successful!")
        print(f"   Response: {response.text[:100]}...")

        return True

    except Exception as e:
        print(f"[ERROR] LLM call failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_categorization_agent():
    """Test categorization agent with OSS model."""
    print("\n=== Testing Categorization Agent ===")

    try:
        from src.agents.categorization.agent import create_gamp_categorization_agent
        from src.config.llm_config import LLMConfig, ModelProvider

        # Set provider to OpenRouter
        LLMConfig.PROVIDER = ModelProvider.OPENROUTER

        # Create categorization agent
        agent = create_gamp_categorization_agent(verbose=True)
        print("[OK] Categorization agent created successfully!")
        print(f"   Agent type: {type(agent).__name__}")

        return True

    except Exception as e:
        print(f"[ERROR] Categorization agent creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("OSS Model Compatibility Testing")
    print("=" * 50)

    tests = [
        ("OpenRouter Compatibility", test_openrouter_compat),
        ("FunctionAgent Compatibility", test_function_agent_compatibility),
        ("Simple LLM Call", test_simple_llm_call),
        ("Categorization Agent", test_categorization_agent),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                passed += 1
                print(f"[PASS] {test_name}: PASSED")
            else:
                print(f"[FAIL] {test_name}: FAILED")
        except Exception as e:
            print(f"[FAIL] {test_name}: FAILED with exception: {e}")

    print("\n" + "="*60)
    print(f"Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! OSS model compatibility is working.")
        print("\nNext steps:")
        print("1. Run setup_phoenix.py to install Phoenix dependencies")
        print("2. Test full workflow with: LLM_PROVIDER=openrouter uv run python main.py <document>")
    else:
        print("⚠️  Some tests failed. Check the errors above.")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
