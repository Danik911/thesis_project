#!/usr/bin/env python3
"""
Simplified Phoenix ChromaDB Integration Test
Focus on core observability functionality with FDA Part-11 document
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from uuid import uuid4

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Phoenix setup - MUST be done before other imports
os.environ["PHOENIX_COLLECTOR_ENDPOINT"] = "http://localhost:6006"
import phoenix as px

from main.src.agents.parallel.context_provider import (
    ContextProviderAgent,
    ContextProviderRequest,
)


class SimplePhoenixTest:
    def __init__(self):
        self.agent = None

    async def setup_phoenix(self):
        """Initialize Phoenix observability"""
        print("🔬 Setting up Phoenix observability...")

        # Start Phoenix tracing session
        px.launch_app(host="localhost", port=6006)

        print("✅ Phoenix connected successfully!")
        print("🌍 Phoenix UI: http://localhost:6006")
        print("📊 Project: simple_chromadb_test")
        return True

    async def setup_agent(self):
        """Initialize Context Provider Agent"""
        print("\n🤖 Setting up Context Provider Agent...")

        try:
            self.agent = ContextProviderAgent()
            print("✅ Context Provider Agent initialized")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize agent: {e}")
            return False

    async def test_document_ingestion(self):
        """Test FDA Part-11 document ingestion"""
        print("\n📥 Testing FDA Part-11 Document Ingestion...")

        # Test document path
        test_doc = "/home/anteb/thesis_project/main/tests/test_data/FDA Part-11--Electronic-Records--Electronic-Signatures---Scope-and-Application-(PDF).md"

        if not os.path.exists(test_doc):
            print(f"❌ Test document not found: {test_doc}")
            return False

        print(f"📄 Document: {os.path.basename(test_doc)}")

        try:
            # Copy to temp directory for ingestion
            temp_dir = "/home/anteb/thesis_project/temp_test_docs"
            os.makedirs(temp_dir, exist_ok=True)

            import shutil
            temp_doc = os.path.join(temp_dir, "fda_part11.md")
            shutil.copy2(test_doc, temp_doc)

            print(f"📁 Ingesting from: {temp_dir}")

            # Ingest with Phoenix tracing
            result = await self.agent.ingest_documents(temp_dir)

            print("✅ Ingestion completed")
            print(f"📋 Result: {result}")
            return True

        except Exception as e:
            print(f"❌ Ingestion failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def test_simple_search(self):
        """Test a simple search query"""
        print("\n🔍 Testing Simple Search Query...")

        try:
            # Create a simple request
            request = ContextProviderRequest(
                gamp_category="5",
                context_depth="basic",
                document_sections=["electronic_records", "validation"],
                test_strategy={
                    "type": "basic_search",
                    "focus_areas": ["electronic_records"],
                    "compliance_level": "pharmaceutical"
                },
                search_scope={
                    "collections": ["regulatory"],
                    "max_documents": 3,
                    "relevance_threshold": 0.6
                },
                correlation_id=uuid4()
            )

            # Simple query
            query = "What are electronic records in FDA Part 11?"
            print(f"❓ Question: {query}")

            # Process with Phoenix tracing
            response = await self.agent.process_request(request, query)

            print("✅ Search completed")
            print(f"📋 Response type: {type(response)}")

            if hasattr(response, "content"):
                content = response.content[:200] + "..." if len(response.content) > 200 else response.content
                print(f"📝 Content preview: {content}")

            return True

        except Exception as e:
            print(f"❌ Search failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def cleanup(self):
        """Cleanup Phoenix session"""
        print("\n🧹 Cleaning up...")
        try:
            # Force flush any remaining traces
            px.Client().flush()
            print("✅ Phoenix cleanup completed")
        except Exception as e:
            print(f"⚠️ Cleanup warning: {e}")

async def main():
    """Main test execution"""
    print("🏥 Simple Phoenix ChromaDB Test")
    print("=" * 50)
    print("📋 This test will:")
    print("1. Connect to Phoenix server (should be running at localhost:6006)")
    print("2. Initialize Context Provider Agent")
    print("3. Ingest FDA Part-11 document")
    print("4. Execute one simple search query")
    print("5. Show results and Phoenix traces")
    print()

    tester = SimplePhoenixTest()

    try:
        # Setup phase
        phoenix_ok = await tester.setup_phoenix()
        if not phoenix_ok:
            print("❌ Phoenix setup failed")
            return False

        agent_ok = await tester.setup_agent()
        if not agent_ok:
            print("❌ Agent setup failed")
            return False

        # Test document ingestion
        ingest_ok = await tester.test_document_ingestion()
        if not ingest_ok:
            print("❌ Document ingestion failed")
            return False

        # Test simple search
        search_ok = await tester.test_simple_search()
        if not search_ok:
            print("❌ Search test failed")
            return False

        print("\n🎉 All tests completed successfully!")
        print("🌍 Check Phoenix UI at http://localhost:6006 for traces")
        print("📊 Look for project: simple_chromadb_test")

        return True

    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        await tester.cleanup()

if __name__ == "__main__":
    # Set logging level to reduce noise
    logging.getLogger().setLevel(logging.WARNING)

    # Run the test
    success = asyncio.run(main())

    if success:
        print("\n✅ Test completed successfully!")
        print("Next steps:")
        print("1. Check Phoenix UI at http://localhost:6006")
        print("2. Look for traces under 'simple_chromadb_test' project")
        print("3. Verify document ingestion and search spans are visible")
    else:
        print("\n❌ Test failed - check logs above")
        sys.exit(1)
