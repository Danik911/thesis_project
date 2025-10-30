#!/usr/bin/env python3
"""
Test ChromaDB callback manager fix.
"""

import asyncio

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_chromadb_fix():
    """Test that ChromaDB operations work after callback fix."""

    print("=" * 60)
    print("TESTING CHROMADB CALLBACK FIX")
    print("=" * 60)

    try:
        # Import after env vars are loaded
        from src.agents.parallel.context_provider import create_context_provider_agent
        from src.config.llm_config import LLMConfig

        # Create LLM
        print("\n1. Creating LLM...")
        llm = LLMConfig.get_llm()
        print(f"   LLM created: {llm.model}")

        # Create context provider
        print("\n2. Creating Context Provider Agent...")
        agent = create_context_provider_agent(
            llm=llm,
            verbose=True,
            enable_phoenix=False
        )
        print("   Context Provider created successfully")

        # Test a search operation
        print("\n3. Testing ChromaDB search...")
        import uuid

        from src.agents.parallel.context_provider import ContextProviderRequest
        request = ContextProviderRequest(
            gamp_category="5",
            test_strategy={"approach": "comprehensive"},
            document_sections=["validation_requirements"],
            search_scope={},
            correlation_id=str(uuid.uuid4())
        )

        # Run the agent through internal method
        # The agent expects an AgentRequestEvent, so we'll use the internal method directly
        result = await agent._execute_context_retrieval(request)

        if result:
            # Check what fields the response has
            if hasattr(result, "context") and result.context:
                print(f"   SUCCESS: Context retrieved with {len(result.context)} items")
            elif hasattr(result, "retrieved_documents") and result.retrieved_documents:
                print(f"   SUCCESS: Retrieved {len(result.retrieved_documents)} documents")
            else:
                print(f"   SUCCESS: Response received (type: {type(result).__name__})")
        else:
            print("   No results returned")

        return True

    except AttributeError as e:
        if "event_starts_to_ignore" in str(e):
            print(f"\nCALLBACK ERROR STILL EXISTS: {e}")
            print("\nThe fix needs to be applied in context_provider.py")
            return False
        raise
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_chromadb_fix())
    print(f"\n{'=' * 60}")
    print(f"RESULT: {'SUCCESS - Callback issue fixed!' if success else 'FAILED - Callback issue persists'}")
    print(f"{'=' * 60}")
