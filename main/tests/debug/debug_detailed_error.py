#!/usr/bin/env uv run python
"""
Detailed error debugging for Context Provider Agent failures.
"""
import asyncio
import sys
import traceback
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "main"))

from src.agents.parallel.context_provider import (
    ContextProviderAgent,
    ContextProviderRequest,
)
from src.core.events import AgentRequestEvent


async def detailed_error_debug():
    """Debug the Context Provider Agent with detailed error tracking."""
    print("🔍 Detailed Error Debugging for Context Provider Agent")
    print("=" * 60)

    try:
        # Initialize agent
        print("1️⃣ Initializing Context Provider Agent...")
        agent = ContextProviderAgent()
        print("✅ Agent initialized successfully")

        # Create a simple test request with required fields
        correlation_id = uuid4()
        test_request = ContextProviderRequest(
            gamp_category="Category_5",
            test_strategy={
                "approach": "document_retrieval",
                "query": "What is FDA Part 11?",
                "focus_areas": ["scope", "definitions"]
            },
            document_sections=["scope", "definitions", "requirements"],
            search_scope={
                "document_types": ["regulatory"],
                "compliance_level": "high",
                "max_documents": 3
            },
            correlation_id=correlation_id,
            context_depth="standard"
        )
        print(f"2️⃣ Created test request: {test_request.test_strategy['query']}")

        # Create AgentRequestEvent to wrap the request
        request_data = test_request.model_dump()
        # Remove correlation_id from request_data since it will be set by the event
        request_data.pop("correlation_id", None)

        agent_request = AgentRequestEvent(
            agent_type="context_provider",
            request_data=request_data,
            requesting_step="test_debug",
            correlation_id=correlation_id
        )
        print("3️⃣ Created AgentRequestEvent wrapper")

        # Run the workflow with detailed error tracking
        print("4️⃣ Running workflow...")
        try:
            result = await agent.process_request(agent_request)
            print(f"5️⃣ Workflow completed: {type(result)}")
            print(f"📋 Result keys: {result.__dict__.keys() if hasattr(result, '__dict__') else 'No __dict__'}")

            if hasattr(result, "success"):
                print(f"✅ Success: {result.success}")
            if hasattr(result, "error_message"):
                print(f"❌ Error message: {result.error_message}")
            if hasattr(result, "result_data"):
                print(f"📊 Result data type: {type(result.result_data)}")
                if result.result_data:
                    print(f"📊 Result data keys: {result.result_data.keys() if isinstance(result.result_data, dict) else 'Not a dict'}")

        except Exception as workflow_error:
            print(f"❌ Workflow error: {workflow_error}")
            print(f"🔍 Error type: {type(workflow_error)}")
            print("📍 Full traceback:")
            traceback.print_exc()

    except Exception as init_error:
        print(f"❌ Initialization error: {init_error}")
        print(f"🔍 Error type: {type(init_error)}")
        print("📍 Full traceback:")
        traceback.print_exc()

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()

    # Run the debug test
    asyncio.run(detailed_error_debug())
