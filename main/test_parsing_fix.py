#!/usr/bin/env python3
"""
Quick test to validate YAML parsing fixes for OSS model responses.
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_parsing():
    """Test YAML parsing with simulated OSS response."""
    
    # Simulated truncated OSS response (what we typically get)
    oss_response = """
    {
      "suite_id": "OQ-SUITE-0001",
      "test_cases": [
        {"test_id": "OQ-001", "test_description": "Verify user authentication"},
        {"test_id": "OQ-002", "test_description": "Test data encryption"},
        {"test_id": "OQ-003", "test_description": "Validate audit trail"},
        {"test_id": "OQ-004", "test_description": "Check access control"},
        {"test_id": "OQ-005", "test_description": "Test data integrity"}
    """  # Truncated JSON
    
    from src.agents.oq_generator.yaml_parser import extract_structured_text_format
    
    print("Testing structured text extraction on truncated response...")
    result = extract_structured_text_format(oss_response)
    
    if result:
        print(f"SUCCESS: Extracted {len(result.get('test_cases', []))} test cases")
        print(f"Fields extracted: {list(result.keys())}")
        if 'test_cases' in result and result['test_cases']:
            print(f"First test: {result['test_cases'][0]}")
        return True
    else:
        print("FAILED: Could not extract structured data")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_parsing())
    print(f"\nParsing test {'PASSED' if success else 'FAILED'}")