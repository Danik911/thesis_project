#!/usr/bin/env python3
"""
Test OSS model (Qwen 2.5) for OQ generation.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add main to path
sys.path.insert(0, str(Path(__file__).parent))

def test_oss_generation():
    """Test Qwen 2.5 for OQ generation."""
    
    print("="*60)
    print("TESTING OSS (QWEN 2.5) OQ GENERATION")
    print("="*60)
    
    from src.agents.oq_generator.generator import OQTestGenerator
    from src.core.events import GAMPCategory
    
    # Create generator (should use Qwen automatically)
    generator = OQTestGenerator(verbose=True)
    
    # Check LLM type
    print(f"OQ Generator LLM: {generator.llm.model if hasattr(generator.llm, 'model') else 'Unknown'}")
    print(f"Using chunked: {generator._use_chunked}")
    
    # Simple test URS
    test_urs = """
    Pharmaceutical Manufacturing System Requirements:
    - User authentication and access control
    - Batch record management
    - Electronic signatures per 21 CFR Part 11
    - Audit trail for all changes
    - Report generation for compliance
    - Data integrity validation
    - System backup and recovery
    - Role-based permissions
    """
    
    print("\nGenerating OQ tests with Qwen 2.5...")
    
    try:
        result = generator.generate_oq_test_suite(
            gamp_category=GAMPCategory.CATEGORY_5,
            urs_content=test_urs,
            document_name="test_urs.md"
        )
        
        print(f"\nSUCCESS: Generated {result.total_test_count} tests")
        print(f"Target range: 23-33 tests")
        
        if 23 <= result.total_test_count <= 33:
            print("PASSED: Test count within range!")
        else:
            print(f"FAILED: Test count {result.total_test_count} outside range")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_oss_generation()
    print("\n" + "="*60)
    print(f"Result: {'SUCCESS' if success else 'FAILED'}")
    print("="*60)