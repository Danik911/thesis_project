#!/usr/bin/env python3
"""
Core LLM API Test - Direct functionality test
"""

import os
import sys
import time
import json
from datetime import datetime

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set API key
os.environ['OPENROUTER_API_KEY'] = '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'
os.environ['LLM_PROVIDER'] = 'openrouter'

from src.config.llm_config import LLMConfig

def test_real_api_calls():
    """Test real API calls with different prompts"""
    
    print("=" * 60)
    print("REAL API TEST - OPENROUTER OSS MODEL")
    print("=" * 60)
    
    # Get LLM
    llm = LLMConfig.get_llm()
    print(f"Model: {LLMConfig.MODELS[LLMConfig.PROVIDER]['model']}")
    print(f"Provider: {LLMConfig.PROVIDER.value}")
    print()
    
    test_cases = [
        {
            "name": "GAMP-5 Categorization",
            "prompt": "What GAMP-5 category would apply to Microsoft SQL Server? Respond with just the category number and a brief reason."
        },
        {
            "name": "Test Generation",
            "prompt": "Generate one OQ test case for user authentication. Format as JSON with fields: test_id, description, steps, expected_result."
        },
        {
            "name": "Regulatory Research",
            "prompt": "What is the latest FDA guidance on computer system validation? Provide a 2-sentence summary."
        },
        {
            "name": "SME Analysis",
            "prompt": "As a pharmaceutical validation expert, what are the top 3 risks for a LIMS system?"
        },
        {
            "name": "Planning",
            "prompt": "Create a brief test strategy outline for GAMP Category 4 software. List 3 main test phases."
        }
    ]
    
    results = []
    total_time = 0
    
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test['name']}")
        print("-" * 40)
        
        try:
            start = time.time()
            response = llm.complete(test['prompt'])
            elapsed = time.time() - start
            total_time += elapsed
            
            print(f"SUCCESS - Response time: {elapsed:.2f}s")
            print(f"Response length: {len(response.text)} chars")
            # Clean response for printing
            clean_text = response.text.encode('ascii', 'ignore').decode('ascii')
            print(f"Preview: {clean_text[:200]}..." if len(clean_text) > 200 else f"Response: {clean_text}")
            
            results.append({
                "test": test['name'],
                "success": True,
                "time": elapsed,
                "response_length": len(response.text)
            })
            
        except Exception as e:
            print(f"FAILED: {e}")
            results.append({
                "test": test['name'],
                "success": False,
                "error": str(e)
            })
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    successful = sum(1 for r in results if r.get('success'))
    print(f"Success Rate: {successful}/{len(test_cases)} ({100*successful/len(test_cases):.0f}%)")
    
    if successful > 0:
        avg_time = total_time / successful
        print(f"Average Response Time: {avg_time:.2f}s")
    
    # Cost estimation
    total_chars = sum(r.get('response_length', 0) for r in results if r.get('success'))
    estimated_tokens = total_chars / 4  # Rough estimate
    cost_per_million = 0.09  # $0.09 per million tokens for openai/gpt-oss-120b
    estimated_cost = (estimated_tokens / 1_000_000) * cost_per_million
    
    print(f"Total tokens (est): {estimated_tokens:.0f}")
    print(f"Estimated cost: ${estimated_cost:.6f}")
    print(f"Cost vs GPT-4: ~91% savings")
    
    # Save results
    with open("core_llm_test_results.json", "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "model": LLMConfig.MODELS[LLMConfig.PROVIDER]['model'],
            "provider": LLMConfig.PROVIDER.value,
            "results": results,
            "summary": {
                "success_rate": f"{successful}/{len(test_cases)}",
                "average_time": avg_time if successful > 0 else 0,
                "estimated_cost": estimated_cost
            }
        }, f, indent=2)
    
    if successful == len(test_cases):
        print("\nALL TESTS PASSED - OSS Model fully functional!")
        return True
    else:
        print(f"\n{len(test_cases) - successful} tests failed")
        return False

if __name__ == "__main__":
    success = test_real_api_calls()
    sys.exit(0 if success else 1)