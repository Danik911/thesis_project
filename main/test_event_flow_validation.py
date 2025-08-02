#!/usr/bin/env python3
"""
Test Event Flow Architecture Validation
Task 10 - Testing and Validation

This script tests the event flow fixes implemented in the unified workflow
to ensure no infinite loops or orphaned events occur.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the main directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.unified_workflow import UnifiedTestGenerationWorkflow

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def analyze_workflow_structure():
    """Analyze the workflow structure for event flow issues."""
    print("ANALYZING Workflow Event Flow Structure")
    print("=" * 60)
    
    workflow = UnifiedTestGenerationWorkflow(verbose=False)
    
    try:
        # This will trigger validation and show us the exact error
        workflow._validate()
        print("PASS Workflow validation passed - no orphaned events detected")
        return True
    except Exception as e:
        print(f"FAIL Workflow validation failed: {e}")
        if "produced but never consumed" in str(e):
            print("CRITICAL: Event flow architecture has orphaned events")
            return False
        return False


async def test_minimal_workflow():
    """Test minimal workflow execution to identify specific flow issues."""
    print("\nTESTING Minimal Workflow Execution")
    print("=" * 60)
    
    # Create a minimal test URS document
    test_content = """
# Test URS - Category 3 System
## Functional Requirements
- System shall use standard vendor software
- No custom development required
- Standard reporting only
"""
    
    temp_file = Path("temp_minimal_test.md")
    temp_file.write_text(test_content)
    
    try:
        workflow = UnifiedTestGenerationWorkflow(
            enable_phoenix=False,
            enable_parallel_coordination=False,
            enable_human_consultation=False,
            verbose=False,
            timeout=60
        )
        
        # Try to validate the workflow first
        print("Validating workflow structure...")
        workflow._validate()
        print("PASS Workflow structure validation passed")
        
        # Now try a minimal run
        print("Starting minimal workflow execution...")
        result = await workflow.run(document_path=str(temp_file))
        
        print("PASS Minimal workflow completed successfully")
        return True
        
    except Exception as e:
        print(f"FAIL Minimal workflow failed: {e}")
        if "produced but never consumed" in str(e):
            print("CRITICAL Event flow issue: Orphaned events detected")
        return False
    finally:
        if temp_file.exists():
            temp_file.unlink()


def identify_orphaned_events():
    """Identify which specific events are orphaned."""
    print("\nIDENTIFYING Orphaned Events")
    print("=" * 60)
    
    workflow = UnifiedTestGenerationWorkflow(verbose=False)
    
    try:
        workflow._validate()
    except Exception as e:
        error_msg = str(e)
        if "produced but never consumed" in error_msg:
            # Extract event names from error message
            start = error_msg.find("produced but never consumed: ") + len("produced but never consumed: ")
            orphaned_events = error_msg[start:].strip()
            
            print(f"CRITICAL Orphaned Events Found: {orphaned_events}")
            
            # Check each step to see where these events are produced
            print("\nEVENT PRODUCTION ANALYSIS:")
            
            # Get all steps that might produce OQTestGenerationEvent
            if "OQTestGenerationEvent" in orphaned_events:
                print("- OQTestGenerationEvent is produced but not consumed")
                print("- This suggests the OQ generation flow is broken")
                print("- Need to ensure proper event consumption chain")
            
            return orphaned_events
        else:
            print("No orphaned events detected in error message")
            return None
    
    # No exception means validation passed
    print("No orphaned events detected - workflow validation passed")
    return None


async def test_urs003_categorization_only():
    """Test just the categorization step to isolate event flow issues."""
    print("\nTESTING URS-003 Categorization Only")
    print("=" * 60)
    
    from src.core.categorization_workflow import GAMPCategorizationWorkflow
    
    # Extract URS-003 content
    test_file = Path("tests/test_data/gamp5_test_data/testing_data.md")
    if not test_file.exists():
        print("FAIL Test data file not found")
        return False
        
    content = test_file.read_text()
    start_marker = "## URS-003: Manufacturing Execution System (MES)"
    end_marker = "## URS-004:"
    
    start_idx = content.find(start_marker)
    end_idx = content.find(end_marker)
    
    if start_idx == -1:
        print("FAIL Could not find URS-003 in test file")
        return False
        
    urs003_content = content[start_idx:end_idx].strip()
    
    try:
        # Test just categorization
        categorization_workflow = GAMPCategorizationWorkflow(verbose=True)
        
        result = await categorization_workflow.run(
            urs_content=urs003_content,
            document_name="URS-003",
            document_version="1.0",
            author="test"
        )
        
        print("PASS Categorization completed successfully")
        
        # Check result
        if hasattr(result, "result"):
            cat_result = result.result
        else:
            cat_result = result
            
        if isinstance(cat_result, dict) and "categorization_event" in cat_result:
            cat_event = cat_result["categorization_event"]
            print(f"RESULT GAMP Category: {cat_event.gamp_category.value}")
            print(f"RESULT Confidence: {cat_event.confidence_score:.2%}")
            
            # Verify it's Category 5 as expected
            if cat_event.gamp_category.value == 5:
                print("PASS Correct categorization - Category 5 detected")
                return True
            else:
                print(f"FAIL Incorrect categorization - Expected 5, got {cat_event.gamp_category.value}")
                return False
        else:
            print("FAIL Unexpected result format")
            return False
            
    except Exception as e:
        print(f"FAIL Categorization failed: {e}")
        return False


def main():
    """Run comprehensive event flow validation."""
    print("TEST Task 10 Event Flow Architecture Testing")
    print("=" * 80)
    print("Testing the event flow fixes for infinite loops and orphaned events")
    print("=" * 80)
    
    results = []
    
    # Test 1: Workflow structure analysis
    results.append(("Workflow Structure Analysis", analyze_workflow_structure()))
    
    # Test 2: Identify specific orphaned events
    orphaned = identify_orphaned_events()
    results.append(("Orphaned Event Detection", orphaned is None))  # Success = no orphaned events
    
    # Test 3: Minimal workflow execution
    results.append(("Minimal Workflow Execution", asyncio.run(test_minimal_workflow())))
    
    # Test 4: URS-003 categorization only
    results.append(("URS-003 Categorization Test", asyncio.run(test_urs003_categorization_only())))
    
    # Summary
    print("\n" + "=" * 80)
    print("FINAL EVENT FLOW VALIDATION SUMMARY")
    print("=" * 80)
    
    passed = 0
    for test_name, success in results:
        status = "PASS" if success else "FAIL"
        print(f"{status} {test_name}")
        if success:
            passed += 1
    
    print(f"\nResults: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("SUCCESS All event flow tests passed!")
        return 0
    else:
        print("CRITICAL Event flow issues detected - fixes needed")
        return 1


if __name__ == "__main__":
    sys.exit(main())