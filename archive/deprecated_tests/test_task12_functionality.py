"""
Test script to validate Task 12 categorization accuracy fix.
Tests URS-003 and other cases for proper categorization without false ambiguity.
"""

import os
import sys
from pathlib import Path
import asyncio
from dotenv import load_dotenv

# Add main directory to path
sys.path.insert(0, str(Path(__file__).parent / "main"))

# Load environment variables
load_dotenv()

# Set required environment variables
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
os.environ["PHOENIX_HOST"] = "localhost"
os.environ["PHOENIX_PORT"] = "6006"
os.environ["PHOENIX_ENABLE_TRACING"] = "false"

from src.agents.categorization.agent import create_gamp_categorization_agent
from src.core.models.events import WorkflowStartEvent, CategorizationEvent, CategorizationResultEvent, CategorizationErrorEvent
from src.core.models.requirement import UserRequirement
from src.core.models.context import WorkflowContext
from llama_index.core.workflow import Workflow, Context, StartEvent, StopEvent
import asyncio

# Test cases
TEST_CASES = [
    {
        "id": "URS-003",
        "title": "Automated Test Report Generation with Custom Templates",
        "description": "The system shall provide automated generation of test execution reports using customizable templates that comply with regulatory requirements for pharmaceutical validation documentation.",
        "rationale": "Standardized reporting ensures consistent documentation across all test executions while allowing flexibility for project-specific requirements.",
        "acceptance_criteria": [
            "System generates reports in multiple formats (PDF, Word, HTML)",
            "Templates support dynamic data insertion from test results", 
            "Reports include all required regulatory compliance fields",
            "Custom templates can be created and saved for reuse",
            "Report generation completes within 60 seconds for standard test suites"
        ],
        "expected_category": 5,
        "expected_rationale": "custom development"
    },
    {
        "id": "URS-001", 
        "title": "User Authentication and Authorization",
        "description": "The system shall provide secure user authentication and role-based authorization to ensure only authorized personnel can access and perform specific functions within the system.",
        "rationale": "Regulatory compliance requires strict access control and audit trails for all system activities in pharmaceutical environments.",
        "acceptance_criteria": [
            "Users must authenticate with username and strong password",
            "System supports role-based access control (RBAC)",
            "All authentication attempts are logged",
            "Session timeout after 30 minutes of inactivity",
            "Password complexity requirements enforced"
        ],
        "expected_category": 3,
        "expected_rationale": "standard security"
    }
]

async def test_categorization():
    """Test categorization for URS cases."""
    print("\n" + "="*80)
    print("TASK 12 CATEGORIZATION VALIDATION TEST")
    print("="*80 + "\n")
    
    # Create the categorization agent
    print("Creating categorization agent...")
    try:
        categorization_agent = create_gamp_categorization_agent()
        print("✓ Agent created successfully\n")
    except Exception as e:
        print(f"❌ Failed to create agent: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Track results
    results = {
        "passed": 0,
        "failed": 0,
        "errors": []
    }
    
    for test_case in TEST_CASES:
        print(f"\nTesting {test_case['id']}: {test_case['title']}")
        print("-" * 60)
        
        try:
            # Create requirement
            requirement = UserRequirement(
                id=test_case["id"],
                title=test_case["title"],
                description=test_case["description"],
                rationale=test_case["rationale"],
                acceptance_criteria=test_case["acceptance_criteria"]
            )
            
            # Create workflow context
            workflow_context = WorkflowContext(
                requirements=[requirement],
                workflow_id=f"test_{test_case['id']}",
                config={}
            )
            
            # Create categorization event
            event = CategorizationEvent(
                requirement=requirement,
                workflow_context=workflow_context
            )
            
            # Run categorization using the workflow
            print(f"Running categorization agent...")
            
            # Create a simple workflow to run the agent
            class TestWorkflow(Workflow):
                @StartEvent()
                async def start(self, ctx: Context, event: StartEvent) -> StopEvent:
                    # Call the categorization agent directly
                    result = await categorization_agent.run(ctx, event.data)
                    return StopEvent(result=result)
            
            # Run the workflow
            workflow = TestWorkflow()
            result = await workflow.run(event)
            
            # Extract the actual result
            if hasattr(result, 'result'):
                result = result.result
            
            # Check result type
            if isinstance(result, CategorizationErrorEvent):
                print(f"❌ ERROR: {result.error}")
                print(f"   Error Type: {result.error_type}")
                print(f"   Severity: {result.severity}")
                if hasattr(result, 'categorization_result') and result.categorization_result:
                    print(f"   Attempted Category: {result.categorization_result.category}")
                    print(f"   Confidence: {result.categorization_result.confidence}")
                results["failed"] += 1
                results["errors"].append({
                    "id": test_case["id"],
                    "error": str(result.error),
                    "type": "error_event"
                })
                continue
                
            elif isinstance(result, CategorizationResultEvent):
                cat_result = result.categorization_result
                print(f"✓ Categorization completed successfully")
                print(f"  Category: {cat_result.category}")
                print(f"  Confidence: {cat_result.confidence:.2f}")
                print(f"  Rationale: {cat_result.rationale}")
                
                # Validate results
                if cat_result.category == test_case["expected_category"]:
                    print(f"✅ PASS: Correct category")
                    
                    # Additional validation for URS-003
                    if test_case["id"] == "URS-003":
                        if cat_result.confidence >= 0.7:
                            print(f"✅ PASS: High confidence for clear Category 5 case")
                            print(f"✅ PASS: No false ambiguity detected")
                            results["passed"] += 1
                        else:
                            print(f"❌ FAIL: Low confidence {cat_result.confidence} for clear case")
                            results["failed"] += 1
                            results["errors"].append({
                                "id": test_case["id"],
                                "error": f"Low confidence: {cat_result.confidence}",
                                "type": "confidence"
                            })
                    else:
                        results["passed"] += 1
                else:
                    print(f"❌ FAIL: Wrong category (expected {test_case['expected_category']})")
                    results["failed"] += 1
                    results["errors"].append({
                        "id": test_case["id"],
                        "error": f"Wrong category: {cat_result.category} (expected {test_case['expected_category']})",
                        "type": "category"
                    })
            else:
                print(f"❌ ERROR: Unexpected result type: {type(result)}")
                results["failed"] += 1
                results["errors"].append({
                    "id": test_case["id"],
                    "error": f"Unexpected result type: {type(result)}",
                    "type": "unexpected"
                })
                
        except Exception as e:
            print(f"❌ EXCEPTION: {str(e)}")
            import traceback
            traceback.print_exc()
            results["failed"] += 1
            results["errors"].append({
                "id": test_case["id"],
                "error": str(e),
                "type": "exception"
            })
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Total Tests: {len(TEST_CASES)}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    print(f"Success Rate: {(results['passed'] / len(TEST_CASES)) * 100:.1f}%")
    
    if results["errors"]:
        print("\n❌ ERRORS:")
        for error in results["errors"]:
            print(f"  - {error['id']}: {error['error']} (Type: {error['type']})")
    
    # Overall result
    if results["failed"] == 0:
        print("\n✅ ALL TESTS PASSED - Task 12 implementation is working correctly!")
        return True
    else:
        print(f"\n❌ TESTS FAILED - {results['failed']} failures detected")
        print("\n💡 Task 12 needs debugging - Using debugger agent...")
        return False

if __name__ == "__main__":
    # Run the test
    success = asyncio.run(test_categorization())
    sys.exit(0 if success else 1)