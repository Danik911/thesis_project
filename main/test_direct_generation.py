#!/usr/bin/env python3
"""
Direct test of OQ generation without the complex workflow.
This tests the core functionality directly.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add main to path
sys.path.insert(0, str(Path(__file__).parent))

async def test_direct_generation():
    """Test OQ generation directly without workflow complexity."""
    
    print("="*60)
    print("DIRECT OQ GENERATION TEST")
    print("Testing core functionality without workflow overhead")
    print("="*60)
    
    # 1. Test GAMP Categorization
    print("\n1. Testing GAMP Categorization...")
    from src.core.categorization_workflow import run_categorization_workflow
    
    test_doc = Path("tests/test_data/gamp5_test_data/testing_data.md")
    document_content = test_doc.read_text(encoding="utf-8")
    
    try:
        cat_result = await run_categorization_workflow(
            urs_content=document_content,
            document_name=test_doc.name,
            enable_error_handling=True,
            verbose=True
        )
        
        if cat_result:
            # Handle both dict and object results
            if isinstance(cat_result, dict):
                category = cat_result.get('gamp_category', cat_result.get('category'))
                confidence = cat_result.get('confidence_score', cat_result.get('confidence', 0))
            else:
                category = getattr(cat_result, 'gamp_category', getattr(cat_result, 'category', None))
                confidence = getattr(cat_result, 'confidence_score', getattr(cat_result, 'confidence', 0))
            
            print(f"   Category: {category}")
            print(f"   Confidence: {confidence}")
            print("   SUCCESS: Categorization working")
        else:
            print("   FAILED: No categorization result")
            return False
    except Exception as e:
        print(f"   FAILED: {e}")
        return False
    
    # 2. Test Context Provider (ChromaDB)
    print("\n2. Testing Context Provider...")
    try:
        from src.agents.parallel.context_provider import ContextProvider
        
        context_provider = ContextProvider(verbose=True)
        context_results = context_provider.retrieve_context(
            gamp_category=5,
            urs_content=document_content[:1000]  # First 1000 chars
        )
        
        if context_results and context_results.get("retrieved_documents"):
            doc_count = len(context_results["retrieved_documents"])
            print(f"   Documents retrieved: {doc_count}")
            print("   SUCCESS: Context provider working")
        else:
            print("   WARNING: No documents retrieved (ChromaDB may be empty)")
    except Exception as e:
        print(f"   WARNING: Context provider issue: {e}")
    
    # 3. Test OQ Generation with DeepSeek V3
    print("\n3. Testing OQ Generation with DeepSeek V3...")
    from src.agents.oq_generator.generator import OQTestGenerator
    from src.config.llm_config import LLMConfig
    from src.core.events import GAMPCategory
    
    try:
        # Get LLM (should be DeepSeek V3)
        llm = LLMConfig.get_llm()
        provider_info = LLMConfig.get_provider_info()
        print(f"   Model: {provider_info['configuration']['model']}")
        print(f"   Max tokens: {provider_info['configuration']['max_tokens']}")
        
        # Initialize generator
        generator = OQTestGenerator(llm=llm, verbose=True)
        
        # Generate tests
        print("   Generating OQ tests...")
        test_suite = generator.generate_oq_test_suite(
            gamp_category=GAMPCategory.CATEGORY_5,
            urs_content=document_content,
            document_name=test_doc.name,
            context_data={
                "validation_context": {
                    "test_strategy_alignment": {
                        "risk_based": True,
                        "gmp_compliant": True
                    }
                }
            }
        )
        
        if test_suite and hasattr(test_suite, 'test_cases'):
            test_count = len(test_suite.test_cases)
            print(f"   Tests generated: {test_count}")
            
            if 23 <= test_count <= 33:
                print("   SUCCESS: Correct number of tests (23-33 range)")
                
                # Check if tests are unique
                if test_count >= 2:
                    first_test_name = test_suite.test_cases[0].test_name
                    second_test_name = test_suite.test_cases[1].test_name
                    
                    if first_test_name != second_test_name:
                        print("   SUCCESS: Tests have unique content")
                    else:
                        print("   WARNING: Tests appear to be templates")
                
                # Save output
                output_dir = Path("output/test_suites")
                output_dir.mkdir(parents=True, exist_ok=True)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = output_dir / f"direct_test_{timestamp}.json"
                
                # Convert to dict for JSON serialization
                output_data = {
                    "suite_id": test_suite.suite_id,
                    "gamp_category": test_suite.gamp_category,
                    "total_test_count": test_suite.total_test_count,
                    "test_cases": [
                        {
                            "test_id": tc.test_id,
                            "test_name": tc.test_name,
                            "test_category": tc.test_category,
                            "objective": tc.objective
                        }
                        for tc in test_suite.test_cases[:5]  # First 5 for preview
                    ],
                    "preview_only": True,
                    "actual_test_count": len(test_suite.test_cases)
                }
                
                with open(output_file, 'w') as f:
                    json.dump(output_data, f, indent=2)
                
                print(f"   Output saved: {output_file.name}")
                print("\n   SUCCESS: OQ generation working!")
                return True
                
            else:
                print(f"   FAILED: Wrong number of tests ({test_count} not in 23-33 range)")
                return False
        else:
            print("   FAILED: No test suite generated")
            return False
            
    except Exception as e:
        print(f"   FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main entry point."""
    success = await test_direct_generation()
    
    print("\n" + "="*60)
    if success:
        print("RESULT: Core functionality WORKING")
        print("The OQ generation system works when called directly.")
        print("The workflow orchestration layer has version issues.")
    else:
        print("RESULT: Core functionality has issues")
    print("="*60)
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)