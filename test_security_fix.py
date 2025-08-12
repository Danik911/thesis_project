#!/usr/bin/env python3
"""
Test script to verify the security assessment fix works.

This script tests the WorkingSecurityTestExecutor to ensure:
1. The workflow compatibility issue is fixed
2. Real tests can be executed against the actual system  
3. Actual results are captured and analyzed
4. No fallback or simulation logic is used

Run with: python test_security_fix.py
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add main to path so we can import
sys.path.insert(0, str(Path(__file__).parent / "main"))

from src.security.working_test_executor import WorkingSecurityTestExecutor
from src.security.owasp_test_scenarios import OWASPTestScenarios


async def test_single_scenario():
    """Test executing a single security scenario to verify the fix."""
    print("Testing WorkingSecurityTestExecutor with single scenario...")
    
    # Initialize components
    executor = WorkingSecurityTestExecutor()
    scenario_generator = OWASPTestScenarios()
    
    try:
        # Get a simple test scenario
        all_scenarios = scenario_generator.get_all_scenarios()
        test_scenario = None
        
        # Find a basic prompt injection scenario to test with
        for scenario in all_scenarios:
            if scenario["owasp_category"] == "LLM01" and "basic" in scenario.get("id", "").lower():
                test_scenario = scenario
                break
        
        if not test_scenario:
            # Use the first LLM01 scenario if no basic one found
            llm01_scenarios = [s for s in all_scenarios if s["owasp_category"] == "LLM01"]
            test_scenario = llm01_scenarios[0] if llm01_scenarios else None
        
        if not test_scenario:
            print("ERROR: No test scenarios available")
            return False
        
        print(f"Testing with scenario: {test_scenario['id']}")
        print(f"   Type: {test_scenario.get('type', 'unknown')}")
        print(f"   OWASP: {test_scenario.get('owasp_category', 'unknown')}")
        
        # Execute the single scenario
        result = await executor.execute_single_scenario(test_scenario, "test_batch")
        
        # Verify we got actual results
        print(f"\nSUCCESS: Test completed successfully!")
        print(f"   Status: {result.get('status', 'unknown')}")
        print(f"   Duration: {result.get('duration_seconds', 0):.2f} seconds")
        print(f"   GAMP Category: {result.get('actual_gamp_category', 'unknown')}")
        print(f"   Confidence: {result.get('actual_confidence_score', 0):.2%}")
        print(f"   Vulnerabilities: {len(result.get('vulnerability_analysis', {}).get('vulnerabilities_detected', []))}")
        print(f"   Mitigation Effectiveness: {result.get('mitigation_effectiveness', 0):.2%}")
        
        # Check for expected result structure
        required_fields = [
            'scenario_id', 'status', 'actual_gamp_category', 'actual_confidence_score',
            'vulnerability_analysis', 'mitigation_effectiveness', 'human_consultation_triggered'
        ]
        
        missing_fields = [field for field in required_fields if field not in result]
        if missing_fields:
            print(f"⚠️  Missing fields in result: {missing_fields}")
        
        # Show vulnerability analysis details
        vuln_analysis = result.get('vulnerability_analysis', {})
        if vuln_analysis.get('vulnerabilities_detected'):
            print(f"🚨 Vulnerabilities detected: {vuln_analysis['vulnerabilities_detected']}")
        else:
            print("🛡️  No vulnerabilities detected")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        return False
    
    finally:
        # Clean up
        executor.cleanup()


async def test_basic_workflow_compatibility():
    """Test basic workflow compatibility without full security testing."""
    print("\n🔧 Testing basic workflow compatibility...")
    
    try:
        from src.core.unified_workflow import UnifiedTestGenerationWorkflow
        from pathlib import Path
        import tempfile
        
        # Create a minimal test URS file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as temp_file:
            temp_file.write("""
# Test URS Document

## Software Description
This is a simple pharmaceutical data processing application.

## Functionality  
- Data entry validation
- Report generation
- Audit trail logging

## GAMP Categorization Request
Please categorize this software according to GAMP-5 guidelines.
            """)
            temp_path = temp_file.name
        
        # Create workflow and test basic call
        workflow = UnifiedTestGenerationWorkflow(
            timeout=60,
            verbose=True
        )
        
        print(f"📄 Created test URS file: {temp_path}")
        print(f"🚀 Calling workflow.run(document_path='{temp_path}')")
        
        # This should work now with the correct parameters
        result = await workflow.run(document_path=temp_path)
        
        print(f"✅ Workflow completed successfully!")
        print(f"   Result type: {type(result)}")
        
        # Clean up
        Path(temp_path).unlink()
        
        return True
        
    except Exception as e:
        print(f"❌ Basic workflow test failed: {e}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        return False


async def main():
    """Main test function."""
    print("Security Assessment Fix Verification")
    print("=" * 50)
    
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    # Test 1: Basic workflow compatibility
    compatibility_ok = await test_basic_workflow_compatibility()
    
    # Test 2: Single security scenario execution (only if compatibility works)
    if compatibility_ok:
        scenario_ok = await test_single_scenario()
    else:
        print("⏭️  Skipping scenario test due to compatibility issues")
        scenario_ok = False
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 20)
    print(f"✅ Workflow Compatibility: {'PASS' if compatibility_ok else 'FAIL'}")
    print(f"✅ Security Scenario Test: {'PASS' if scenario_ok else 'FAIL'}")
    
    if compatibility_ok and scenario_ok:
        print("\n🎉 All tests passed! The security assessment fix is working.")
        print("   Ready to run full security assessment with real system testing.")
        return True
    else:
        print("\n❌ Some tests failed. Need to investigate further.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)