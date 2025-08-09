#!/usr/bin/env python3
"""
Test chunked OQ generation with OpenAI.
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

def test_chunked_oq_generation():
    """Test chunked generation approach for OpenAI."""
    
    print("="*60)
    print("TESTING CHUNKED OQ GENERATION")
    print("="*60)
    
    from src.agents.oq_generator.chunked_generator import ChunkedOQGenerator
    from src.core.events import GAMPCategory
    
    # Create generator
    generator = ChunkedOQGenerator(verbose=True)
    
    # Check LLM type
    if hasattr(generator.llm, 'model'):
        print(f"Using model: {generator.llm.model}")
    
    # Try generation with minimum valid count
    print("\nGenerating 23 tests in chunks...")
    
    test_urs = """
    Pharmaceutical Manufacturing System Requirements:
    - User authentication and access control
    - Batch record management
    - Electronic signatures per 21 CFR Part 11
    - Audit trail for all changes
    - Report generation for compliance
    """
    
    try:
        result = generator.generate_test_suite(
            gamp_category=GAMPCategory.CATEGORY_5,
            urs_content=test_urs,
            document_name="test_urs.md",
            total_tests=25  # Minimum for Category 5
        )
        
        print(f"\nGenerated {result.total_test_count} tests successfully!")
        
        # Show first test as example
        if result.test_cases:
            first_test = result.test_cases[0]
            print(f"\nExample test:")
            print(f"  ID: {first_test.test_id}")
            print(f"  Name: {first_test.test_name}")
            print(f"  Category: {first_test.test_category}")
            print(f"  Objective: {first_test.objective[:100]}...")
            
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_chunked_oq_generation()
    print("\n" + "="*60)
    print(f"Result: {'SUCCESS' if success else 'FAILED'}")
    print("="*60)