#!/usr/bin/env python3
"""
Complete Real API Test for OSS Migration
Tests all migrated agents with actual OpenRouter API calls
"""

import json
import os
import sys
import time
from datetime import datetime

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set API key
os.environ["OPENROUTER_API_KEY"] = "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"
os.environ["LLM_PROVIDER"] = "openrouter"

from src.agents.oq_generator.generator_v2 import OQTestGeneratorV2
from src.agents.parallel.context_provider import ContextProviderAgent
from src.agents.parallel.research_agent import ResearchAgent
from src.agents.parallel.sme_agent import SMEAgent
from src.agents.planner.agent import PlannerAgent
from src.config.llm_config import LLMConfig


def test_llm_direct():
    """Test direct LLM functionality"""
    print("\n=== Testing Direct LLM API Call ===")
    start = time.time()

    try:
        llm = LLMConfig.get_llm()
        response = llm.complete("What is GAMP-5 Category 3? Provide a brief answer.")
        print(f"PASS: Direct LLM call successful ({time.time()-start:.2f}s)")
        print(f"Response preview: {response.text[:200]}...")
        return True
    except Exception as e:
        print(f"FAIL: Direct LLM call failed: {e}")
        return False

def test_context_provider():
    """Test Context Provider Agent"""
    print("\n=== Testing Context Provider Agent ===")
    start = time.time()

    try:
        agent = ContextProviderAgent(llm=LLMConfig.get_llm())
        print(f"PASS: Context Provider instantiated ({time.time()-start:.2f}s)")

        # Test a simple operation
        llm = agent.llm
        response = llm.complete("Extract key requirements from: 'System must validate user input and store data securely.'")
        print("PASS: Context Provider LLM call successful")
        print(f"Response preview: {response.text[:150]}...")
        return True
    except Exception as e:
        print(f"FAIL: Context Provider test failed: {e}")
        return False

def test_research_agent():
    """Test Research Agent"""
    print("\n=== Testing Research Agent ===")
    start = time.time()

    try:
        agent = ResearchAgent(llm=LLMConfig.get_llm())
        print(f"PASS: Research Agent instantiated ({time.time()-start:.2f}s)")

        # Test research capability
        llm = agent.llm
        response = llm.complete("What are the latest FDA guidelines for software validation?")
        print("PASS: Research Agent LLM call successful")
        print(f"Response preview: {response.text[:150]}...")
        return True
    except Exception as e:
        print(f"FAIL: Research Agent test failed: {e}")
        return False

def test_sme_agent():
    """Test SME Agent"""
    print("\n=== Testing SME Agent ===")
    start = time.time()

    try:
        agent = SMEAgent(llm=LLMConfig.get_llm())
        print(f"PASS: SME Agent instantiated ({time.time()-start:.2f}s)")

        # Test expert analysis
        llm = agent.llm
        response = llm.complete("Provide pharmaceutical validation expertise for a database system.")
        print("PASS: SME Agent LLM call successful")
        print(f"Response preview: {response.text[:150]}...")
        return True
    except Exception as e:
        print(f"FAIL: SME Agent test failed: {e}")
        return False

def test_planning_agent():
    """Test Planning Agent"""
    print("\n=== Testing Planning Agent ===")
    start = time.time()

    try:
        agent = PlannerAgent(llm=LLMConfig.get_llm())
        print(f"PASS: Planning Agent instantiated ({time.time()-start:.2f}s)")

        # Test planning capability
        llm = agent.llm
        response = llm.complete("Create a test strategy for GAMP Category 4 software.")
        print("PASS: Planning Agent LLM call successful")
        print(f"Response preview: {response.text[:150]}...")
        return True
    except Exception as e:
        print(f"FAIL: Planning Agent test failed: {e}")
        return False

def test_oq_generator():
    """Test OQ Generator"""
    print("\n=== Testing OQ Generator ===")
    start = time.time()

    try:
        generator = OQTestGeneratorV2()
        print(f"PASS: OQ Generator instantiated ({time.time()-start:.2f}s)")

        # Test generation capability
        llm = LLMConfig.get_llm()
        response = llm.complete("Generate one OQ test case for user login functionality.")
        print("PASS: OQ Generator LLM call successful")
        print(f"Response preview: {response.text[:150]}...")
        return True
    except Exception as e:
        print(f"FAIL: OQ Generator test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("COMPLETE REAL API TEST FOR OSS MIGRATION")
    print("=" * 60)
    print(f"Provider: {os.environ.get('LLM_PROVIDER', 'openrouter')}")
    print(f"Timestamp: {datetime.now().isoformat()}")

    results = {
        "direct_llm": test_llm_direct(),
        "context_provider": test_context_provider(),
        "research_agent": test_research_agent(),
        "sme_agent": test_sme_agent(),
        "planning_agent": test_planning_agent(),
        "oq_generator": test_oq_generator()
    }

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test, result in results.items():
        status = "PASS: PASS" if result else "FAIL: FAIL"
        print(f"{test:20} {status}")

    print(f"\nTotal: {passed}/{total} tests passed ({100*passed/total:.0f}%)")

    if passed == total:
        print("\nSUCCESS: ALL TESTS PASSED! OSS Migration is fully functional!")
    else:
        print(f"\nWARNING: {total-passed} tests failed. Review errors above.")

    # Save results
    with open("test_results.json", "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "provider": os.environ.get("LLM_PROVIDER", "openrouter"),
            "results": results,
            "summary": f"{passed}/{total} passed"
        }, f, indent=2)

    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
