#!/usr/bin/env python3
"""
Quick validation test for the workflow validation fix.

This script tests that the UnifiedTestGenerationWorkflow can be instantiated
without LlamaIndex workflow validation errors.
"""
import os
import sys

# Add the main directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

def test_workflow_validation():
    """Test that the workflow can be instantiated without validation errors."""
    print("🧪 Testing workflow validation fix...")

    try:
        # Import the workflow
        print("📦 Importing UnifiedTestGenerationWorkflow...")
        from src.core.unified_workflow import UnifiedTestGenerationWorkflow

        # Import the new event
        print("📦 Importing AgentResultsEvent...")
        from src.core.events import AgentResultEvent, AgentResultsEvent

        # Create a workflow instance (this should trigger validation)
        print("🏗️ Creating workflow instance...")
        workflow = UnifiedTestGenerationWorkflow(verbose=True)

        # Test creating the new event
        print("🔄 Testing AgentResultsEvent creation...")
        test_agent_results = [
            AgentResultEvent(
                agent_type="test_agent",
                result_data={"test": "data"},
                success=True,
                processing_time=1.0,
                correlation_id="test-correlation-id"
            )
        ]

        agent_results_event = AgentResultsEvent(
            agent_results=test_agent_results,
            session_id="test-session"
        )

        # Verify the event properties
        assert agent_results_event.total_count == 1
        assert agent_results_event.success_count == 1
        assert len(agent_results_event.agent_results) == 1

        print("✅ Workflow validation fix successful!")
        print("   - Workflow created without validation errors")
        print("   - AgentResultsEvent working correctly")
        print(f"   - Event contains {agent_results_event.total_count} results with {agent_results_event.success_count} successful")

        return True

    except Exception as e:
        print(f"❌ Workflow validation fix failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_workflow_validation()
    sys.exit(0 if success else 1)
