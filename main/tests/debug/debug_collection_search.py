#!/usr/bin/env python3
"""
Debug script to test collection search process in Context Provider Agent.
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

from src.agents.parallel.context_provider import ContextProviderAgent, ContextProviderRequest
from src.core.events import AgentRequestEvent

async def debug_collection_search():
    """Debug collection search process step by step."""
    print("🔍 Context Provider Agent - Collection Search Debug")
    print("=" * 60)
    
    try:
        # Initialize agent
        print("1️⃣ Initializing Context Provider Agent...")
        agent = ContextProviderAgent(enable_phoenix=True, verbose=True)
        print("✅ Agent initialized successfully")
        print(f"📚 Available collections: {list(agent.collections.keys())}")
        
        # Show actual collection names in ChromaDB
        print("\n📁 ChromaDB Collection Details:")
        for key, collection in agent.collections.items():
            count = collection.count()
            print(f"   🔑 Key: '{key}' → Name: '{collection.name}' → Count: {count}")
        
        # Create test request
        correlation_id = uuid4()
        test_request = ContextProviderRequest(
            gamp_category="5",
            test_strategy={
                "approach": "document_retrieval",
                "query": "FDA Part 11 scope and application",
                "focus_areas": ["scope", "definitions", "enforcement"]
            },
            document_sections=["scope", "definitions", "requirements"],
            search_scope={
                "document_types": ["regulatory"],
                "compliance_level": "high",
                "max_documents": 5
            },
            correlation_id=correlation_id,
            context_depth="standard"
        )
        
        # Test collection selection logic
        print(f"\n2️⃣ Testing Collection Selection Logic:")
        selected_collections = agent._select_collections(test_request.gamp_category, test_request.search_scope)
        print(f"   🎯 Selected collection keys: {selected_collections}")
        
        # Verify collections exist and have data
        print(f"\n3️⃣ Verifying Selected Collections:")
        for collection_key in selected_collections:
            if collection_key in agent.collections:
                collection = agent.collections[collection_key]
                count = collection.count()
                print(f"   ✅ '{collection_key}' → '{collection.name}' → {count} documents")
                
                # Test direct search on each collection
                if count > 0:
                    print(f"      🔍 Testing direct search on '{collection_key}'...")
                    try:
                        test_results = collection.query(
                            query_texts=["FDA Part 11"],
                            n_results=2
                        )
                        if test_results and 'ids' in test_results:
                            print(f"      ✅ Found {len(test_results['ids'][0])} documents")
                            for doc_id in test_results['ids'][0]:
                                print(f"         📄 {doc_id}")
                        else:
                            print(f"      ❌ No results for 'FDA Part 11'")
                    except Exception as search_error:
                        print(f"      ❌ Search error: {search_error}")
            else:
                print(f"   ❌ Collection key '{collection_key}' not found in agent.collections")
        
        # Test the search query building
        print(f"\n4️⃣ Testing Search Query Building:")
        search_query = agent._build_search_query(test_request)
        print(f"   📝 Generated query: '{search_query}'")
        
        # Test full agent processing
        print(f"\n5️⃣ Testing Full Agent Processing:")
        request_data = test_request.model_dump()
        request_data.pop('correlation_id', None)
        
        agent_request = AgentRequestEvent(
            agent_type="context_provider",
            request_data=request_data,
            requesting_step="debug_collection_search",
            correlation_id=correlation_id
        )
        
        result = await agent.process_request(agent_request)
        print(f"   ✅ Success: {result.success}")
        
        if result.success:
            results = result.result_data
            print(f"   📊 Retrieved: {len(results.get('retrieved_documents', []))} documents")
            print(f"   🎯 Quality: {results.get('context_quality', 'unknown')}")
            print(f"   📈 Coverage: {results.get('search_coverage', 0.0):.1%}")
            print(f"   🏆 Confidence: {results.get('confidence_score', 0.0):.3f}")
        else:
            print(f"   ❌ Error: {result.error_message}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Run debug
    asyncio.run(debug_collection_search())