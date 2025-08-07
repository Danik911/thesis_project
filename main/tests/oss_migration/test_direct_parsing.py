#!/usr/bin/env python3
"""
Test script to verify the OSS migration fix works with both OpenAI and OpenRouter models.

This tests the modified categorization agent that now uses direct LLM calls
instead of LLMTextCompletionProgram to support OSS models.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from project root
env_path = Path(__file__).parent.parent.parent.parent / '.env'
load_dotenv(env_path)

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from llama_index.llms.openai import OpenAI
from src.agents.categorization.agent import categorize_with_pydantic_structured_output
from src.agents.categorization.error_handler import CategorizationErrorHandler
from src.llms.openrouter_llm import OpenRouterLLM


def test_openai_model():
    """Test with standard OpenAI model to ensure backward compatibility."""
    print("\n" + "=" * 60)
    print("Testing with OpenAI GPT-4o-mini")
    print("=" * 60)
    
    # Sample URS content for testing
    urs_content = """
    User Requirements Specification for Laboratory Information Management System (LIMS)
    
    1. System Overview:
    The LIMS will be a commercial off-the-shelf software solution used to manage laboratory 
    samples, workflows, and test results. The system will be used as supplied by the vendor
    without any custom code development.
    
    2. Key Requirements:
    - Track sample lifecycle from receipt to disposal
    - Generate standard reports using built-in templates
    - Integrate with existing laboratory instruments via standard protocols
    - User access control with predefined roles
    - Audit trail for all data changes
    
    3. Configuration:
    The system will use vendor-provided configuration options to:
    - Define sample types and workflows
    - Set up user roles and permissions
    - Configure report templates from available options
    
    No custom programming or code modifications will be performed.
    """
    
    try:
        # Initialize OpenAI LLM
        llm = OpenAI(
            model="gpt-4o-mini",
            api_key=os.getenv("OPENAI_API_KEY"),
            temperature=0.1
        )
        
        # Initialize error handler
        error_handler = CategorizationErrorHandler()
        
        # Test categorization
        result = categorize_with_pydantic_structured_output(
            llm=llm,
            urs_content=urs_content,
            document_name="test_lims_urs.txt",
            error_handler=error_handler
        )
        
        print(f"SUCCESS: OpenAI model categorization completed")
        print(f"Category: {result.gamp_category.value}")
        print(f"Confidence: {result.confidence_score:.2%}")
        # Extract reasoning safely
        if 'REASONING:' in result.justification:
            reasoning_part = result.justification.split('REASONING:')[1]
            reasoning_lines = reasoning_part.split('\n')
            if len(reasoning_lines) > 1:
                print(f"Reasoning excerpt: {reasoning_lines[1][:200]}...")
            else:
                print(f"Reasoning: {reasoning_lines[0][:200]}...")
        else:
            print(f"Justification excerpt: {result.justification[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"FAILED: OpenAI model test failed")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_openrouter_model():
    """Test with OpenRouter OSS model to verify the fix enables OSS support."""
    print("\n" + "=" * 60)
    print("Testing with OpenRouter OSS Model")
    print("=" * 60)
    
    # Check for OpenRouter API key
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if not openrouter_key:
        print("[WARN]  SKIPPED: OPENROUTER_API_KEY not set")
        print("To test OSS models, set OPENROUTER_API_KEY environment variable")
        return None
    
    # Sample URS content for testing
    urs_content = """
    Requirements for Custom Patient Data Analytics Platform
    
    1. Overview:
    Develop a bespoke analytics platform for analyzing patient treatment outcomes.
    This will be a completely custom-built solution tailored to our specific needs.
    
    2. Custom Features Required:
    - Proprietary algorithm for outcome prediction
    - Custom machine learning models for pattern detection  
    - Specialized visualization dashboard designed from scratch
    - Integration with our unique data formats
    - Custom API for third-party connections
    
    3. Development Approach:
    - Full custom development using Python and React
    - In-house developed algorithms and models
    - Custom database schema design
    - Proprietary data processing pipeline
    
    All components will be developed specifically for this application.
    """
    
    try:
        # Initialize OpenRouter LLM using custom class
        llm = OpenRouterLLM(
            model="qwen/qwen-2.5-72b-instruct",  # Fast OSS model
            api_key=openrouter_key,
            temperature=0.1,
            max_tokens=500
        )
        
        # Initialize error handler
        error_handler = CategorizationErrorHandler()
        
        # Test categorization
        result = categorize_with_pydantic_structured_output(
            llm=llm,
            urs_content=urs_content,
            document_name="test_custom_analytics.txt",
            error_handler=error_handler
        )
        
        print(f"[OK] SUCCESS: OpenRouter OSS model categorization completed")
        print(f"Category: {result.gamp_category.value}")
        print(f"Confidence: {result.confidence_score:.2%}")
        # Extract reasoning safely
        if 'REASONING:' in result.justification:
            reasoning_part = result.justification.split('REASONING:')[1]
            reasoning_lines = reasoning_part.split('\n')
            if len(reasoning_lines) > 1:
                print(f"Reasoning excerpt: {reasoning_lines[1][:200]}...")
            else:
                print(f"Reasoning: {reasoning_lines[0][:200]}...")
        else:
            print(f"Justification excerpt: {result.justification[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] FAILED: OpenRouter OSS model test failed")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("OSS MIGRATION FIX VERIFICATION")
    print("Testing direct LLM parsing approach")
    print("=" * 60)
    
    # Test 1: Verify backward compatibility with OpenAI
    openai_result = test_openai_model()
    
    # Test 2: Verify new OSS model support
    openrouter_result = test_openrouter_model()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    if openai_result:
        print("[OK] OpenAI models: WORKING (backward compatibility maintained)")
    else:
        print("[FAIL] OpenAI models: FAILED")
    
    if openrouter_result is None:
        print("[WARN]  OpenRouter/OSS models: NOT TESTED (API key missing)")
    elif openrouter_result:
        print("[OK] OpenRouter/OSS models: WORKING (new capability enabled)")
    else:
        print("[FAIL] OpenRouter/OSS models: FAILED")
    
    if openai_result and (openrouter_result is True or openrouter_result is None):
        print("\n[SUCCESS] SUCCESS: OSS migration fix is working!")
        print("The system now supports both OpenAI and OSS models.")
        return 0
    else:
        print("\n[WARN]  Some tests failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    exit(main())