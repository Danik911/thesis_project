#!/usr/bin/env uv run python
"""
Debug script to test Context Provider Agent and examine detailed results.
"""
import asyncio
import sys
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


async def debug_with_results():
    """Debug the Context Provider Agent and examine detailed results."""
    print("🔍 Context Provider Agent - Detailed Results Debug")
    print("=" * 60)

    try:
        # Initialize agent
        print("1️⃣ Initializing Context Provider Agent...")
        agent = ContextProviderAgent(enable_phoenix=True, verbose=True)
        print("✅ Agent initialized successfully")

        # Create test request with required fields
        correlation_id = uuid4()
        test_request = ContextProviderRequest(
            gamp_category="Category_5",
            test_strategy={
                "approach": "document_retrieval",
                "query": "What is FDA Part 11 scope and when does it apply to electronic records?",
                "focus_areas": ["scope", "definitions", "enforcement"]
            },
            document_sections=["scope", "definitions", "requirements", "enforcement"],
            search_scope={
                "document_types": ["regulatory"],
                "compliance_level": "high",
                "max_documents": 5
            },
            correlation_id=correlation_id,
            context_depth="standard"
        )
        print(f"2️⃣ Created test request: {test_request.test_strategy['query']}")

        # Create AgentRequestEvent
        request_data = test_request.model_dump()
        request_data.pop("correlation_id", None)  # Remove to avoid conflict

        agent_request = AgentRequestEvent(
            agent_type="context_provider",
            request_data=request_data,
            requesting_step="debug_test",
            correlation_id=correlation_id
        )
        print("3️⃣ Created AgentRequestEvent wrapper")

        # Execute request
        print("4️⃣ Running Context Provider Agent...")
        result = await agent.process_request(agent_request)

        print(f"5️⃣ Processing completed in {result.processing_time:.2f} seconds")
        print(f"✅ Success: {result.success}")

        if result.success and result.result_data:
            print("\n📊 DETAILED RESULTS ANALYSIS")
            print("-" * 40)

            # Extract results
            results = result.result_data

            print(f"🔍 Retrieved Documents: {len(results.get('retrieved_documents', []))}")
            print(f"🎯 Context Quality: {results.get('context_quality', 'unknown')}")
            print(f"📈 Search Coverage: {results.get('search_coverage', 0.0):.1%}")
            print(f"🏆 Confidence Score: {results.get('confidence_score', 0.0):.3f}")

            # Show retrieved documents
            documents = results.get("retrieved_documents", [])
            if documents:
                print(f"\n📄 RETRIEVED DOCUMENTS ({len(documents)} found)")
                print("-" * 40)
                for i, doc in enumerate(documents[:3], 1):  # Show first 3
                    print(f"\n📑 Document {i}:")
                    print(f"   📝 Source: {doc.get('source', 'Unknown')}")
                    print(f"   ⭐ Relevance: {doc.get('relevance_score', 0.0):.3f}")
                    print(f"   📏 Content Length: {len(doc.get('content', ''))} chars")
                    print(f"   🏷️ Metadata: {doc.get('metadata', {}).get('section', 'Unknown section')}")

                    # Show snippet of content
                    content = doc.get("content", "")
                    if content:
                        snippet = content[:200] + "..." if len(content) > 200 else content
                        print(f"   📖 Content Preview: {snippet}")

            # Show document summaries
            summaries = results.get("document_summaries", [])
            if summaries:
                print(f"\n📋 DOCUMENT SUMMARIES ({len(summaries)} generated)")
                print("-" * 40)
                for i, summary in enumerate(summaries[:2], 1):
                    print(f"\n📊 Summary {i}:")
                    print(f"   📄 Title: {summary.get('title', 'Untitled')}")
                    print(f"   📝 Summary: {summary.get('summary', 'No summary')[:150]}...")
                    print(f"   🔑 Key Points: {len(summary.get('key_points', []))} points")

            # Show requirements
            requirements = results.get("requirements_extracted", [])
            if requirements:
                print(f"\n⚖️ EXTRACTED REQUIREMENTS ({len(requirements)} found)")
                print("-" * 40)
                for i, req in enumerate(requirements[:3], 1):
                    print(f"\n📋 Requirement {i}:")
                    print(f"   📝 Text: {req.get('requirement_text', 'N/A')[:100]}...")
                    print(f"   🏷️ Type: {req.get('requirement_type', 'Unknown')}")
                    print(f"   🎯 Priority: {req.get('priority', 'Unknown')}")

            # Show processing metadata
            metadata = results.get("processing_metadata", {})
            if metadata:
                print("\n🔧 PROCESSING METADATA")
                print("-" * 40)
                for key, value in metadata.items():
                    if isinstance(value, (str, int, float)):
                        print(f"   {key}: {value}")
                    elif isinstance(value, list):
                        print(f"   {key}: {len(value)} items")
                    elif isinstance(value, dict):
                        print(f"   {key}: {len(value)} keys")

        else:
            print(f"❌ Error: {result.error_message}")

        print("\n🔗 Phoenix UI: http://localhost:6006")
        print(f"📊 Correlation ID: {correlation_id}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()

    # Run the debug test
    asyncio.run(debug_with_results())
