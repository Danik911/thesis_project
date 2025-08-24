#!/usr/bin/env python3
"""
Debug test for OQ generation failure.

This script will test the workflow with minimal setup to identify
where exactly the OQ generation is failing.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add the main package to path
sys.path.insert(0, str(Path(__file__).parent / "main"))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Set validation mode to bypass consultation
os.environ["VALIDATION_MODE"] = "true"

async def test_oq_generation():
    """Test OQ generation with minimal workflow."""
    try:
        from main.src.core.unified_workflow import run_unified_test_generation_workflow
        
        # Use a simple test document
        test_doc_path = "main/tests/test_data/gamp5_test_data/category3_test.md"
        
        if not Path(test_doc_path).exists():
            # Create a minimal test document
            test_content = """
# Environmental Monitoring System - URS

## 1. System Overview
This document defines requirements for an Environmental Monitoring System 
used in pharmaceutical manufacturing facilities.

## 2. Functional Requirements
- Temperature monitoring (15-25°C)
- Humidity monitoring (30-50% RH)
- Data logging every 15 minutes
- Alert system for out-of-range conditions
- 21 CFR Part 11 compliant data storage

## 3. Software Classification
This is a vendor-supplied software package without modification.
Standard configuration interfaces will be used for setup.
No custom programming or source code modification required.

## 4. Compliance Requirements
- GAMP Category 3 (Standard Software)
- 21 CFR Part 11 electronic records
- ALCOA+ data integrity principles
- FDA validation requirements
"""
            Path(test_doc_path).parent.mkdir(parents=True, exist_ok=True)
            Path(test_doc_path).write_text(test_content)
            print(f"Created test document: {test_doc_path}")
        
        print("Starting OQ generation debug test...")
        print(f"Document path: {test_doc_path}")
        print(f"Validation mode: {os.environ.get('VALIDATION_MODE')}")
        
        # Run the workflow with debug enabled
        result = await run_unified_test_generation_workflow(
            document_path=test_doc_path,
            verbose=True,
            timeout=600,  # 10 minutes
            validation_mode=True,
            enable_parallel_coordination=True
        )
        
        print(f"Workflow completed with status: {result.get('status', 'UNKNOWN')}")
        
        # Check for OQ generation results
        if 'oq_generation' in result:
            oq_results = result['oq_generation']
            print(f"OQ generation results: {oq_results}")
            
            if 'total_tests' in oq_results:
                test_count = oq_results['total_tests']
                print(f"TOTAL TESTS GENERATED: {test_count}")
                
                if test_count == 0:
                    print("ERROR: Workflow completed but generated 0 tests!")
                    return False
                else:
                    print(f"SUCCESS: Generated {test_count} OQ tests")
                    return True
            else:
                print("ERROR: No 'total_tests' field in OQ results")
                return False
        else:
            print("ERROR: No 'oq_generation' section in results")
            print(f"Available result keys: {list(result.keys())}")
            return False
            
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_oq_generation())
    if success:
        print("\n✅ OQ generation debug test PASSED")
        sys.exit(0)
    else:
        print("\n❌ OQ generation debug test FAILED")
        sys.exit(1)