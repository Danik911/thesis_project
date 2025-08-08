#!/usr/bin/env python3
"""Quick baseline test with OpenAI before OpenRouter migration test."""

import os
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Set OpenAI provider
os.environ["LLM_PROVIDER"] = "openai"
os.environ["OPENAI_API_KEY"] = "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"

from src.config.llm_config import LLMConfig
from src.agents.categorization.agent import categorize_with_pydantic_structured_output

def test_openai_baseline():
    """Test categorization with OpenAI as baseline."""
    
    print("\n" + "="*60)
    print("BASELINE TEST WITH OPENAI")
    print("="*60)
    
    # Simple test case
    test_urs = """
    User Requirements Specification
    
    System: Custom pharmaceutical manufacturing execution system
    
    Requirements:
    1. Custom business logic for batch processing
    2. Integration with proprietary equipment
    3. Custom reporting and analytics
    4. GMP compliance tracking
    5. Electronic batch records
    
    This is a fully custom application built specifically for our manufacturing process.
    """
    
    print(f"\nProvider: {LLMConfig.get_provider_info()['provider']}")
    print(f"Model: {LLMConfig.get_provider_info()['configuration']['model']}")
    
    print("\nRunning categorization...")
    start_time = time.time()
    
    try:
        # Get LLM from centralized config
        llm = LLMConfig.get_llm()
        
        # Run categorization
        result = categorize_with_pydantic_structured_output(
            llm=llm,
            urs_content=test_urs,
            document_name="test_baseline.txt"
        )
        
        elapsed = time.time() - start_time
        
        print(f"\n✅ SUCCESS")
        print(f"Category: {result.category}")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"Time: {elapsed:.2f}s")
        print(f"Rationale: {result.rationale[:200]}...")
        
        return True
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"\n❌ FAILED after {elapsed:.2f}s")
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    success = test_openai_baseline()
    sys.exit(0 if success else 1)