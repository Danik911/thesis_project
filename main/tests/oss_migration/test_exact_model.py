#!/usr/bin/env python3
"""
TEST WITH EXACT MODEL: openai/gpt-oss-120b
NO FALLBACKS - FAIL IF IT DOESN'T WORK
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent.parent.parent / '.env'
load_dotenv(env_path)

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.llms.openrouter_llm import OpenRouterLLM
from src.agents.categorization.agent import categorize_with_pydantic_structured_output
from src.agents.categorization.error_handler import CategorizationErrorHandler


def test_exact_model():
    """Test with EXACTLY openai/gpt-oss-120b - NO FALLBACKS."""
    
    print("\n" + "="*60)
    print("TESTING EXACT MODEL: openai/gpt-oss-120b")
    print("NO FALLBACKS - THIS MUST WORK OR FAIL")
    print("="*60)
    
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("FATAL ERROR: OPENROUTER_API_KEY not found")
        return False
    
    # Test case from the migration report
    test_content = """
    Software Requirements for Laboratory Information Management System (LIMS)
    
    The system will be a commercial off-the-shelf LIMS solution from LabWare.
    We will use it as supplied by the vendor without any custom code development.
    Configuration will be limited to:
    - Setting up user accounts through the admin interface
    - Defining sample types using built-in configuration screens
    - Creating reports using the standard report templates
    
    No programming or customization will be performed.
    """
    
    try:
        print("\nInitializing model: openai/gpt-oss-120b")
        
        # USE EXACT MODEL - NO FALLBACKS
        llm = OpenRouterLLM(
            model="openai/gpt-oss-120b",  # EXACT MODEL AS REQUESTED
            api_key=api_key,
            temperature=0.1,
            max_tokens=500
        )
        
        print("Model initialized successfully")
        
        error_handler = CategorizationErrorHandler()
        
        print("\nCalling categorization function...")
        
        result = categorize_with_pydantic_structured_output(
            llm=llm,
            urs_content=test_content,
            document_name="test_lims.txt",
            error_handler=error_handler
        )
        
        print("\n" + "="*60)
        print("SUCCESS: openai/gpt-oss-120b WORKS!")
        print("="*60)
        print(f"Category: {result.gamp_category.value}")
        print(f"Confidence: {result.confidence_score:.1%}")
        
        if 'REASONING:' in result.justification:
            reasoning = result.justification.split('REASONING:')[1].split('\n')[1]
            # Encode to ASCII to avoid Unicode issues
            reasoning_ascii = reasoning.encode('ascii', 'replace').decode('ascii')
            print(f"Reasoning: {reasoning_ascii}")
        else:
            print(f"Justification: {result.justification[:200]}")
        
        return True
        
    except Exception as e:
        print("\n" + "="*60)
        print("FAILURE: openai/gpt-oss-120b DOES NOT WORK")
        print("="*60)
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {str(e)}")
        
        # Print full traceback for debugging
        import traceback
        print("\nFull Traceback:")
        traceback.print_exc()
        
        return False


if __name__ == "__main__":
    success = test_exact_model()
    
    print("\n" + "="*60)
    print("FINAL VERDICT")
    print("="*60)
    
    if success:
        print("openai/gpt-oss-120b: WORKING")
        print("The integration supports this specific model.")
    else:
        print("openai/gpt-oss-120b: BROKEN")
        print("The integration DOES NOT work with this model.")
        print("NO FALLBACKS - This is a FAILURE.")
    
    exit(0 if success else 1)