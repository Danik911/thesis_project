#!/usr/bin/env python3
"""
Debug script to investigate Q&A test failures.
"""

import asyncio
import sys
from pathlib import Path
from uuid import uuid4
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
env_path = project_root / ".env"
load_dotenv(env_path)

from main.src.agents.parallel.context_provider import (
    ContextProviderAgent,
    ContextProviderRequest,
    create_context_provider_agent
)
from main.src.core.events import AgentRequestEvent
from main.tests.regulatory.fda_part11.fda_part11_qa_questions import FDApart11Questions


async def debug_single_question():
    """Debug a single question to identify the issue."""
    print("🔍 Debugging Context Provider Agent Q&A Issue")
    print("=" * 50)
    
    try:
        # Initialize agent without Phoenix to isolate issues
        print("1️⃣ Initializing Context Provider Agent (without Phoenix)...")
        agent = create_context_provider_agent(
            verbose=True,
            enable_phoenix=False,
            max_documents=20
        )
        print("✅ Agent initialized successfully")
        print()
        
        # Get a simple test question
        questions = FDApart11Questions.get_test_questions()
        test_question = questions[0]  # First question
        
        print(f"2️⃣ Testing question: {test_question['id']}")
        print(f"   Question: {test_question['question']}")
        print()
        
        # Create request
        correlation_id = uuid4()
        request = ContextProviderRequest(
            gamp_category=test_question['gamp_category'],
            test_strategy=test_question['test_strategy'],
            document_sections=test_question['search_sections'],
            search_scope={
                "collections": ["regulatory"],
                "max_results": 10
            },
            context_depth=test_question['context_depth'],
            correlation_id=correlation_id,
            timeout_seconds=60
        )
        
        print("3️⃣ Created ContextProviderRequest successfully")
        print(f"   GAMP Category: {request.gamp_category}")
        print(f"   Search sections: {request.document_sections}")
        print(f"   Collections: {request.search_scope['collections']}")
        print()
        
        # Remove correlation_id from model_dump
        request_data = request.model_dump()
        request_data.pop('correlation_id', None)
        
        # Create Agent Request Event
        agent_request = AgentRequestEvent(
            agent_type="context_provider",
            request_data=request_data,
            requesting_step="debug_test",
            correlation_id=correlation_id
        )
        
        print("4️⃣ Created AgentRequestEvent successfully")
        print(f"   Agent type: {agent_request.agent_type}")
        print(f"   Requesting step: {agent_request.requesting_step}")
        print()
        
        # Execute request
        print("5️⃣ Executing request...")
        response = await agent.process_request(agent_request)
        
        print("6️⃣ Response received!")
        print(f"   Success: {response.success}")
        
        if response.success:
            print(f"   Result data keys: {list(response.result_data.keys())}")
            if 'response' in response.result_data:
                agent_response = response.result_data['response']
                print(f"   Documents retrieved: {len(agent_response.get('retrieved_documents', []))}")
                print(f"   Context quality: {agent_response.get('context_quality', 'unknown')}")
                print(f"   Confidence score: {agent_response.get('confidence_score', 0.0)}")
        else:
            print(f"   Error message: {response.error_message}")
        
        return True
        
    except Exception as e:
        print(f"❌ Debug failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    asyncio.run(debug_single_question())