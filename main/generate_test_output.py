#!/usr/bin/env python3
"""
Generate and save the actual OQ test cases using DeepSeek V3.
This script will generate the tests and save them regardless of validation.
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the main directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), "."))

from src.agents.oq_generator.generator import OQTestGenerator
from src.agents.oq_generator.models import OQGenerationConfig
from src.core.events import GAMPCategory
from src.config.llm_config import LLMConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def generate_test_suite():
    """Generate OQ test suite with DeepSeek V3 and save output."""
    
    print("\n" + "="*80)
    print("GENERATING OQ TEST SUITE WITH DEEPSEEK V3")
    print("="*80)
    
    try:
        # Initialize DeepSeek V3 via OpenRouter
        print("\n1. Initializing DeepSeek V3 LLM...")
        llm = LLMConfig.get_llm()
        
        # Verify model configuration
        provider_info = LLMConfig.get_provider_info()
        print(f"   Provider: {provider_info['provider']}")
        print(f"   Model: {provider_info['configuration']['model']}")
        print(f"   API Key Present: {provider_info['api_key_present']}")
        
        if not provider_info['api_key_present']:
            print("FAILED: OPENROUTER_API_KEY not found")
            return None
        
        # Initialize OQ Generator
        print("\n2. Initializing OQ Test Generator...")
        generator = OQTestGenerator(
            llm=llm,
            verbose=True,
            generation_timeout=300  # 5 minutes
        )
        
        # Test URS content
        urs_content = """
        User Requirements Specification (URS)
        
        System: Pharmaceutical Manufacturing Execution System (MES)
        GAMP Category: 5 (Custom Application)
        
        REQ-001: User Authentication and Access Control
        The system shall provide secure multi-factor authentication mechanisms to ensure only authorized personnel can access the system. Authentication must comply with 21 CFR Part 11 requirements for electronic signatures and access controls.
        
        REQ-002: Data Integrity and Audit Trail
        The system shall maintain complete data integrity per 21 CFR Part 11 and ALCOA+ principles. All data changes must be tracked in an immutable audit trail with timestamp, user identification, and reason for change.
        
        REQ-003: Electronic Signatures
        The system shall support legally binding electronic signatures that meet 21 CFR Part 11 requirements. Each signature must include user authentication, timestamp, and meaning of signature.
        
        REQ-004: Batch Record Management
        The system shall manage and track pharmaceutical batch records throughout the manufacturing process. This includes material tracking, equipment usage, environmental conditions, and quality control results.
        
        REQ-005: Reporting and Analytics
        The system shall generate GMP-compliant reports and analytics for batch release, deviations, investigations, and trending. Reports must be available in PDF format with electronic signatures.
        
        REQ-006: Equipment Integration
        The system shall integrate with manufacturing equipment to collect process parameters automatically. Data collection must be validated and include error checking mechanisms.
        
        REQ-007: Material Management
        The system shall track all materials including raw materials, intermediates, and finished products. Material genealogy and chain of custody must be maintained.
        
        REQ-008: Quality Control Integration
        The system shall integrate with laboratory systems to receive test results and manage specifications. Out-of-specification results must trigger automatic notifications.
        
        REQ-009: Deviation Management
        The system shall provide workflow for managing deviations, investigations, and CAPA. All deviations must be tracked to closure with full documentation.
        
        REQ-010: Training Records
        The system shall maintain training records for all users and verify training status before allowing access to specific functions.
        """
        
        # Configuration for exactly 25 tests
        config = OQGenerationConfig(
            gamp_category=5,
            document_name="Pharmaceutical MES OQ Test Suite",
            target_test_count=25,  # Request exactly 25 tests
            complexity_level="comprehensive",
            regulatory_requirements=["21 CFR Part 11", "EU Annex 11", "GAMP-5"],
            require_traceability=True,
            include_negative_testing=True,
            validate_data_integrity=True
        )
        
        print("\n3. Generating OQ Test Suite...")
        print(f"   GAMP Category: {GAMPCategory.CATEGORY_5.value}")
        print(f"   Target test count: {config.target_test_count}")
        print(f"   Model: DeepSeek V3 (deepseek/deepseek-chat)")
        
        # Generate test suite
        start_time = datetime.now()
        
        try:
            # Try to generate with validation
            test_suite = generator.generate_oq_test_suite(
                gamp_category=GAMPCategory.CATEGORY_5,
                urs_content=urs_content,
                document_name="Pharmaceutical MES OQ Validation",
                context_data={
                    "validation_context": {
                        "test_strategy_alignment": {
                            "risk_based": True,
                            "gmp_compliant": True
                        }
                    }
                },
                config=config
            )
            
            generation_time = (datetime.now() - start_time).total_seconds()
            print(f"\nSUCCESS: Generated test suite in {generation_time:.2f}s")
            
            # Convert to dict for saving
            test_suite_dict = test_suite.model_dump()
            
        except Exception as e:
            generation_time = (datetime.now() - start_time).total_seconds()
            print(f"\nValidation failed after {generation_time:.2f}s: {e}")
            print("\nAttempting to save raw output...")
            
            # Try to get raw output from generator's last response
            # This is a workaround to save the tests even if validation fails
            test_suite_dict = {
                "suite_id": f"OQ-SUITE-DEEPSEEK-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                "model": "deepseek/deepseek-chat",
                "generation_status": "VALIDATION_FAILED",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "note": "Tests were generated but validation failed. Manual review required."
            }
            
            # Check if generator has any partial data we can save
            if hasattr(generator, '_last_raw_response'):
                test_suite_dict["raw_response"] = generator._last_raw_response
        
        # Save output
        os.makedirs('outputs', exist_ok=True)
        output_file = f'outputs/oq_test_suite_deepseek_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        with open(output_file, 'w') as f:
            json.dump(test_suite_dict, f, indent=2, default=str)
        
        print(f"\n4. Output saved to: {output_file}")
        
        # Print summary
        if 'test_cases' in test_suite_dict:
            print(f"\n5. Test Suite Summary:")
            print(f"   Total tests: {len(test_suite_dict['test_cases'])}")
            print(f"   Test IDs: {[t['test_id'] for t in test_suite_dict['test_cases'][:5]]}...")
            
            # Show sample test
            if test_suite_dict['test_cases']:
                sample = test_suite_dict['test_cases'][0]
                print(f"\n6. Sample Test Case:")
                print(f"   ID: {sample.get('test_id', 'N/A')}")
                print(f"   Name: {sample.get('test_name', 'N/A')}")
                print(f"   Category: {sample.get('test_category', 'N/A')}")
                print(f"   Objective: {sample.get('objective', 'N/A')[:100]}...")
        
        print("\n" + "="*80)
        print("GENERATION COMPLETE - Check output file for full test suite")
        print("="*80)
        
        return test_suite_dict
        
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Run the test generation."""
    test_suite = generate_test_suite()
    
    if test_suite and 'test_cases' in test_suite:
        print(f"\nSUCCESS: Generated {len(test_suite['test_cases'])} test cases")
    else:
        print("\nWARNING: Test generation completed with issues - check output file")

if __name__ == "__main__":
    main()