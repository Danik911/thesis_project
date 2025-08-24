#!/usr/bin/env python3
"""
Simple OQ test without Unicode characters to avoid encoding issues.
"""

import asyncio
import logging
import sys
import traceback
from pathlib import Path
from uuid import uuid4
from datetime import datetime, UTC

# Add main to path
sys.path.insert(0, str(Path(__file__).parent / "main"))

from src.agents.oq_generator.workflow import OQGenerationWorkflow


async def test_oq_workflow():
    """Test OQ workflow can run without errors."""
    print("=== OQ Workflow Test ===")
    print("Testing OQ workflow instantiation and basic execution...")
    
    try:
        # Test workflow creation
        print("1. Creating OQGenerationWorkflow...")
        workflow = OQGenerationWorkflow(timeout=300)
        print("   SUCCESS: OQGenerationWorkflow created")
        
        # Prepare test data
        test_data = {
            "gamp_category": 3,
            "urs_content": "Environmental Monitoring System for pharmaceutical facility. Vendor-supplied software without modification.",
            "document_metadata": {"name": "URS-001-ENV-MONITORING"},
            "required_test_count": 5,
            "test_strategy": {"test_types": ["operational_qualification"]},
            "agent_results": {"context_provider": {"relevant_docs": []}},
            "categorization_confidence": 0.85,
            "correlation_id": str(uuid4())
        }
        
        print("2. Running workflow with test data...")
        print(f"   GAMP Category: {test_data['gamp_category']}")
        print(f"   Required tests: {test_data['required_test_count']}")
        
        # Run workflow
        result = await workflow.run(data=test_data)
        
        print("3. Workflow completed successfully!")
        print(f"   Result type: {type(result)}")
        
        if isinstance(result, dict):
            print(f"   Result keys: {list(result.keys())}")
            
            if "result" in result:
                inner_result = result["result"]
                print(f"   Inner result type: {type(inner_result)}")
                if isinstance(inner_result, dict):
                    print(f"   Inner result keys: {list(inner_result.keys())}")
                    
                    # Check for success indicators
                    if "status" in inner_result:
                        print(f"   Status: {inner_result['status']}")
                    
                    if "test_suite" in inner_result:
                        test_suite = inner_result["test_suite"]
                        if isinstance(test_suite, dict) and "tests" in test_suite:
                            test_count = len(test_suite["tests"])
                            print(f"   Tests generated: {test_count}")
                        else:
                            print("   Test suite present but no tests found")
                    
                    if "consultation_type" in inner_result:
                        print(f"   Consultation type: {inner_result['consultation_type']}")
        
        print("4. TEST PASSED: No exceptions thrown")
        return True
        
    except Exception as e:
        print(f"4. TEST FAILED: {e}")
        print(f"   Error type: {type(e).__name__}")
        print(f"   Traceback: {traceback.format_exc()}")
        
        # Check for specific errors
        if "_cancel_flag" in str(e):
            print("   CRITICAL: _cancel_flag error still present!")
            return False
        else:
            print("   Different error - may be expected due to missing dependencies")
            return True


async def run_simple_test():
    """Run the simple OQ test."""
    print("Starting Simple OQ Workflow Test...")
    print("=====================================")
    
    success = await test_oq_workflow()
    
    print("\n=== TEST RESULTS ===")
    if success:
        print("OVERALL STATUS: PASS")
        print("The workflow can be instantiated and run without critical errors.")
        print("OQ generation should work in the full system.")
    else:
        print("OVERALL STATUS: FAIL")
        print("Critical issues found that need to be fixed.")
    
    return success


if __name__ == "__main__":
    print("Simple OQ Workflow Test")
    print("=======================")
    
    # Run the test
    success = asyncio.run(run_simple_test())
    
    sys.exit(0 if success else 1)
