"""
Integration test for error handling with real agent execution.

This script tests the error handling system with actual LLM calls and real scenarios.
Run this to validate the implementation works end-to-end.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from main.src.agents.categorization.agent import (
    create_gamp_categorization_agent,
    categorize_with_error_handling,
    categorize_with_structured_output
)
from main.src.agents.categorization.error_handler import CategorizationErrorHandler
from main.src.core.events import GAMPCategory


def test_real_error_scenarios():
    """Test error handling with real agent and various error scenarios."""
    
    print("🧪 Error Handling Integration Test")
    print("=" * 60)
    
    # Create agent with error handling
    agent = create_gamp_categorization_agent(
        enable_error_handling=True,
        confidence_threshold=0.60,
        verbose=True
    )
    
    # Test scenarios
    test_cases = [
        {
            "name": "Empty Document",
            "content": "",
            "expected": "empty or invalid"
        },
        {
            "name": "Too Short Document",
            "content": "ABC",
            "expected": "too short"
        },
        {
            "name": "Unicode/Special Characters",
            "content": "System Requirements: Unicode test 你好世界 🌍 Special chars: @#$%^&*()",
            "expected": "should process or fallback"
        },
        {
            "name": "Ambiguous Content",
            "content": """
            This system might be infrastructure software like Windows Server,
            but also has custom development requirements for proprietary algorithms.
            It could be Category 1 or Category 5, hard to determine.
            """,
            "expected": "low confidence or ambiguity"
        },
        {
            "name": "Clear Category 4",
            "content": """
            LIMS Configuration Requirements:
            - Configure sample management workflows
            - Set up user-defined parameters for testing protocols
            - Configure approval workflows for batch release
            - No custom code development required
            """,
            "expected": "Category 4 with good confidence"
        },
        {
            "name": "Binary/Nonsense Content",
            "content": "\x00\x01\x02\x03\x04 Binary data mixed with text",
            "expected": "parsing error or fallback"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test {i}: {test_case['name']}")
        print(f"Expected: {test_case['expected']}")
        
        try:
            result = categorize_with_structured_output(
                agent,
                test_case["content"],
                f"test_{i}_{test_case['name'].lower().replace(' ', '_')}.urs"
            )
            
            print(f"✅ Result:")
            print(f"   Category: {result.gamp_category.name} ({result.gamp_category.value})")
            print(f"   Confidence: {result.confidence_score:.2%}")
            print(f"   Review Required: {result.review_required}")
            print(f"   Error Type: {result.risk_assessment.get('error_details', {}).get('error_type', 'None')}")
            
            # Extract key info from justification
            if "FALLBACK" in result.justification:
                print(f"   ⚠️  Fallback triggered")
            
            results.append({
                "test": test_case["name"],
                "category": result.gamp_category.value,
                "confidence": result.confidence_score,
                "is_fallback": result.gamp_category == GAMPCategory.CATEGORY_5 and result.confidence_score == 0.0
            })
            
        except Exception as e:
            print(f"❌ Unexpected error: {str(e)}")
            results.append({
                "test": test_case["name"],
                "category": "ERROR",
                "confidence": 0.0,
                "is_fallback": False
            })
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary:")
    print(f"Total tests: {len(test_cases)}")
    
    fallback_count = sum(1 for r in results if r["is_fallback"])
    error_count = sum(1 for r in results if r["category"] == "ERROR")
    success_count = len(test_cases) - error_count
    
    print(f"✅ Successful executions: {success_count}")
    print(f"⚠️  Fallbacks triggered: {fallback_count}")
    print(f"❌ Unexpected errors: {error_count}")
    
    # Check error handler statistics
    if hasattr(agent, 'error_handler'):
        stats = agent.error_handler.get_error_statistics()
        print(f"\n📈 Error Handler Statistics:")
        print(f"   Total errors handled: {stats['total_errors']}")
        print(f"   Fallback count: {stats['fallback_count']}")
        print(f"   Error types: {stats['error_type_distribution']}")
        print(f"   Audit log entries: {stats['audit_log_entries']}")
    
    return results


def test_audit_trail_generation():
    """Test that audit trails are properly generated."""
    
    print("\n\n🔍 Audit Trail Test")
    print("=" * 60)
    
    # Create agent with error handling
    agent = create_gamp_categorization_agent(
        enable_error_handling=True,
        confidence_threshold=0.70,  # Higher threshold to trigger more fallbacks
        verbose=False
    )
    
    # Trigger various errors
    test_errors = [
        ("", "empty_doc.urs"),
        ("XX", "short_doc.urs"),
        ("Low confidence content without clear indicators", "ambiguous.urs")
    ]
    
    for content, doc_name in test_errors:
        categorize_with_structured_output(agent, content, doc_name)
    
    # Get audit log
    if hasattr(agent, 'error_handler'):
        audit_log = agent.error_handler.get_audit_log()
        
        print(f"Generated {len(audit_log)} audit log entries:")
        for entry in audit_log:
            print(f"\n📝 Entry ID: {entry['entry_id']}")
            print(f"   Timestamp: {entry['timestamp']}")
            print(f"   Document: {entry['document_name']}")
            print(f"   Action: {entry['action']}")
            print(f"   Error Type: {entry['error_type']}")
            print(f"   Decision: {entry['decision_rationale'][:100]}...")
    
    return audit_log


def test_confidence_thresholds():
    """Test different confidence thresholds and their effects."""
    
    print("\n\n📊 Confidence Threshold Test")
    print("=" * 60)
    
    test_content = """
    Software system with some configuration options.
    May require user setup and parameters.
    """
    
    thresholds = [0.50, 0.60, 0.70, 0.80, 0.90]
    
    for threshold in thresholds:
        agent = create_gamp_categorization_agent(
            enable_error_handling=True,
            confidence_threshold=threshold,
            verbose=False
        )
        
        result = categorize_with_structured_output(
            agent,
            test_content,
            f"threshold_test_{threshold}.urs"
        )
        
        print(f"\nThreshold: {threshold:.0%}")
        print(f"  Category: {result.gamp_category.value}")
        print(f"  Confidence: {result.confidence_score:.2%}")
        print(f"  Fallback: {result.gamp_category == GAMPCategory.CATEGORY_5 and result.confidence_score == 0.0}")


if __name__ == "__main__":
    # Check if API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        print("Please set your OpenAI API key to run integration tests")
        sys.exit(1)
    
    print("🚀 Starting Error Handling Integration Tests")
    print("Note: This will make real API calls to OpenAI\n")
    
    # Run tests
    try:
        # Test 1: Real error scenarios
        error_results = test_real_error_scenarios()
        
        # Test 2: Audit trail generation
        audit_log = test_audit_trail_generation()
        
        # Test 3: Confidence thresholds
        test_confidence_thresholds()
        
        print("\n\n✅ All integration tests completed!")
        
    except Exception as e:
        print(f"\n\n❌ Integration test failed: {str(e)}")
        import traceback
        traceback.print_exc()