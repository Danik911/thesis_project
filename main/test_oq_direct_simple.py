#!/usr/bin/env python3
"""Direct test of OQ generator bypassing workflow"""
import asyncio
import os
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv('../.env')

# Import OQ components
from src.agents.oq_generator.generator import OQTestGenerator
from src.agents.oq_generator.models import OQTestSuite, OQTestCase
from llama_index.llms.openai import OpenAI

async def generate_oq_directly():
    """Generate OQ tests directly without workflow"""
    
    print("Direct OQ Generation Test")
    print("="*60)
    
    # Create output directory
    output_dir = Path("output/test_suites")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize generator
    llm = OpenAI(
        model="gpt-4o-mini",
        api_key=os.getenv("OPENAI_API_KEY"),
        timeout=120.0
    )
    
    generator = OQTestGenerator(
        llm=llm,
        verbose=True,
        generation_timeout=120  # 2 minutes
    )
    
    # Create minimal context
    context = {
        "document_name": "test_document.md",
        "gamp_category": 5,
        "compliance_level": "GAMP-5",
        "regulatory_requirements": ["21 CFR Part 11", "EU Annex 11"],
        "test_focus": "functional",
        "test_count": 3  # Only 3 tests
    }
    
    try:
        print("Generating OQ tests...")
        
        # Generate tests
        tests = await generator.generate_tests(
            gamp_category=5,
            document_content="Sample pharmaceutical system requiring GAMP-5 validation",
            test_count=3,
            context=context
        )
        
        print(f"Generated {len(tests)} tests")
        
        # Create test suite
        test_suite = OQTestSuite(
            suite_id=f"OQ_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            suite_name="Direct OQ Test Suite",
            gamp_category=5,
            tests=tests,
            total_test_count=len(tests),
            created_at=datetime.now(),
            pharmaceutical_compliance={
                "gamp5_compliant": True,
                "regulatory_standards": ["21 CFR Part 11", "EU Annex 11"],
                "validation_level": "full"
            }
        )
        
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_suite_DIRECT_{timestamp}.json"
        output_file = output_dir / filename
        
        output_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "generator": "Direct OQ Test",
                "test_count": len(tests)
            },
            "test_suite": test_suite.model_dump()
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\nSUCCESS! Test suite saved to: {output_file}")
        print(f"File size: {output_file.stat().st_size} bytes")
        
        # Show first test
        if tests:
            print(f"\nExample test generated:")
            print(f"  ID: {tests[0].test_id}")
            print(f"  Name: {tests[0].test_name}")
            print(f"  Category: {tests[0].test_category}")
            
        return output_file
        
    except Exception as e:
        print(f"\nERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = asyncio.run(generate_oq_directly())
    
    if result:
        print(f"\nTest generation complete. Output: {result}")
    else:
        print("\nTest generation failed.")