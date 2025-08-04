"""
Minimal test for OQ generation to diagnose timeout issues.
"""
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from src.agents.oq_generator.generator import OQTestGenerator
from src.agents.oq_generator.models import OQGenerationConfig
from src.core.events import GAMPCategory
from llama_index.llms.openai import OpenAI

async def test_minimal_oq_generation():
    """Test OQ generation with minimal input."""
    print("Starting minimal OQ generation test...")
    
    # Setup LLM with proper configuration
    llm = OpenAI(
        model=os.getenv("LLM_MODEL", "gpt-4.1-mini-2025-04-14"),
        temperature=0.1,
        timeout=600  # 10 minutes
    )
    
    # Create generator with increased timeout
    generator = OQTestGenerator(
        llm=llm,
        verbose=True,
        generation_timeout=600  # 10 minutes
    )
    
    # Minimal URS content for Category 3
    urs_content = """
    # Simple Test System
    
    ## Purpose
    This is a simple Category 3 system for testing OQ generation.
    
    ## Requirements
    1. The system shall display data
    2. The system shall validate inputs
    3. The system shall generate reports
    """
    
    # Minimal config - Category 3 allows 5-10 tests
    config = OQGenerationConfig(
        gamp_category=GAMPCategory.CATEGORY_3,
        document_name="minimal_test.md",
        target_test_count=5,
        default_test_count=5,
        test_count_overrides={
            GAMPCategory.CATEGORY_3: 5
        }
    )
    
    try:
        print("Generating OQ test suite...")
        test_suite = generator.generate_oq_test_suite(
            gamp_category=GAMPCategory.CATEGORY_3,
            urs_content=urs_content,
            document_name="minimal_test.md",
            config=config
        )
        
        print(f"SUCCESS! Generated {len(test_suite.tests)} tests")
        print(f"Test Suite ID: {test_suite.test_suite_id}")
        
        # Display first test
        if test_suite.tests:
            first_test = test_suite.tests[0]
            print(f"\nFirst test: {first_test.test_id}")
            print(f"Title: {first_test.test_title}")
            print(f"Objective: {first_test.test_objective}")
            
        return test_suite
        
    except Exception as e:
        print(f"FAILED: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = asyncio.run(test_minimal_oq_generation())
    if result:
        print("\nTest completed successfully!")
    else:
        print("\nTest failed!")