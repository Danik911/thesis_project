#!/usr/bin/env python3
"""
HONEST REAL-WORLD TEST of OSS model integration.
This test will reveal if the categorization agent REALLY works with OSS models.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import json

# Load environment variables
env_path = Path(__file__).parent.parent.parent.parent / '.env'
load_dotenv(env_path)

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.llms.openrouter_llm import OpenRouterLLM
from src.agents.categorization.agent import categorize_with_pydantic_structured_output
from src.agents.categorization.error_handler import CategorizationErrorHandler


def test_real_oss_categorization():
    """Test with actual OSS models to see if they REALLY work."""
    
    print("\n" + "="*60)
    print("HONEST REAL-WORLD TEST OF OSS INTEGRATION")
    print("="*60)
    
    # Real test cases from actual pharmaceutical systems
    test_cases = [
        {
            "name": "Oracle Database Infrastructure",
            "content": """
            Requirements for Oracle Database 19c Implementation
            
            We need to deploy Oracle Database 19c Enterprise Edition as the backend 
            database infrastructure for our clinical trials management system.
            This is a standard Oracle installation with no custom code.
            
            Requirements:
            - Install Oracle 19c on Linux servers
            - Configure standard backup procedures
            - Set up user authentication
            - Enable audit logging
            - Use Oracle's built-in features only
            """,
            "expected_category": 1  # Infrastructure
        },
        {
            "name": "LabWare LIMS Configuration",
            "content": """
            Laboratory Information Management System Configuration Requirements
            
            We will implement LabWare LIMS version 7 for our QC laboratory.
            The system requires configuration of:
            - Sample workflows using LabWare's configuration tools
            - User roles and permissions through the admin interface
            - Report templates using the built-in report designer
            - Integration with instruments using LabWare's standard connectors
            
            All configuration will be done through LabWare's standard interfaces.
            No custom programming or code modifications will be performed.
            """,
            "expected_category": 4  # Configured product
        },
        {
            "name": "Custom Clinical Analytics Platform",
            "content": """
            Bespoke Clinical Trial Analytics System Development
            
            Develop a completely custom analytics platform for our unique clinical 
            trial protocols. This system must:
            
            - Implement proprietary statistical algorithms we've developed
            - Create custom visualizations for our specific data formats
            - Build a custom API for integration with our in-house systems
            - Develop machine learning models specific to our trial designs
            - Create a custom database schema for our unique data structures
            
            All components will be developed from scratch using Python and React.
            """,
            "expected_category": 5  # Custom application
        }
    ]
    
    # Test with multiple OSS models
    models_to_test = [
        "qwen/qwen-2.5-72b-instruct",
        "meta-llama/llama-3.1-70b-instruct",
        "mistralai/mistral-large"
    ]
    
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("ERROR: OPENROUTER_API_KEY not found")
        return False
    
    results = []
    
    for model in models_to_test:
        print(f"\n\nTesting Model: {model}")
        print("-" * 40)
        
        try:
            llm = OpenRouterLLM(
                model=model,
                api_key=api_key,
                temperature=0.1,
                max_tokens=500
            )
            
            error_handler = CategorizationErrorHandler()
            
            for test_case in test_cases:
                print(f"\nTest Case: {test_case['name']}")
                print(f"Expected Category: {test_case['expected_category']}")
                
                try:
                    result = categorize_with_pydantic_structured_output(
                        llm=llm,
                        urs_content=test_case['content'],
                        document_name=test_case['name'],
                        error_handler=error_handler
                    )
                    
                    actual_category = result.gamp_category.value
                    confidence = result.confidence_score
                    
                    status = "PASS" if actual_category == test_case['expected_category'] else "FAIL"
                    
                    print(f"Result: Category {actual_category} (Confidence: {confidence:.1%}) - {status}")
                    
                    results.append({
                        "model": model,
                        "test_case": test_case['name'],
                        "expected": test_case['expected_category'],
                        "actual": actual_category,
                        "confidence": confidence,
                        "status": status,
                        "reasoning": result.justification.split('REASONING:')[1].split('\n')[1] if 'REASONING:' in result.justification else "N/A"
                    })
                    
                except Exception as e:
                    print(f"ERROR: {str(e)[:200]}")
                    results.append({
                        "model": model,
                        "test_case": test_case['name'],
                        "expected": test_case['expected_category'],
                        "actual": "ERROR",
                        "confidence": 0,
                        "status": "ERROR",
                        "reasoning": str(e)[:200]
                    })
                    
        except Exception as e:
            print(f"Failed to initialize model {model}: {e}")
            continue
    
    # Generate honest report
    print("\n\n" + "="*60)
    print("HONEST ASSESSMENT REPORT")
    print("="*60)
    
    # Calculate success rate
    successful = sum(1 for r in results if r["status"] == "PASS")
    total = len(results)
    success_rate = (successful / total * 100) if total > 0 else 0
    
    print(f"\nOverall Success Rate: {successful}/{total} ({success_rate:.1f}%)")
    
    # Analyze by model
    print("\nBy Model Performance:")
    for model in models_to_test:
        model_results = [r for r in results if r["model"] == model]
        model_success = sum(1 for r in model_results if r["status"] == "PASS")
        model_total = len(model_results)
        if model_total > 0:
            print(f"  {model}: {model_success}/{model_total} ({model_success/model_total*100:.1f}%)")
    
    # Identify issues
    print("\nIssues Found:")
    issues = [r for r in results if r["status"] != "PASS"]
    if issues:
        for issue in issues:
            print(f"  - {issue['model']} on {issue['test_case']}: {issue['reasoning'][:100]}")
    else:
        print("  None - All tests passed!")
    
    # Save detailed results
    with open("oss_test_results_detailed.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nDetailed results saved to oss_test_results_detailed.json")
    
    # HONEST VERDICT
    print("\n" + "="*60)
    print("HONEST VERDICT")
    print("="*60)
    
    if success_rate >= 80:
        print("SUCCESS: The OSS integration REALLY WORKS!")
        print(f"With {success_rate:.1f}% accuracy, the system is production-ready.")
        return True
    elif success_rate >= 60:
        print("PARTIAL SUCCESS: The OSS integration works but needs tuning.")
        print(f"At {success_rate:.1f}% accuracy, some prompt engineering may be needed.")
        return True
    else:
        print("FAILURE: The OSS integration has serious issues.")
        print(f"Only {success_rate:.1f}% accuracy - not ready for production.")
        return False


if __name__ == "__main__":
    success = test_real_oss_categorization()
    exit(0 if success else 1)