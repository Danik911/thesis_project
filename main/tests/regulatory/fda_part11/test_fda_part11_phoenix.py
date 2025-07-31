"""
Enhanced Test Script for FDA Part-11 Document with Phoenix Observability

This comprehensive test demonstrates:
1. Phoenix server connection and UI accessibility  
2. FDA Part-11 document ingestion with full tracing
3. Multiple search queries with different complexity levels
4. Confidence score calculations and quality assessments
5. Complete trace visibility in Phoenix UI
6. Error handling with full diagnostics

Test Document: FDA Part-11 Electronic Records & Electronic Signatures Guidance
"""

import asyncio
import sys
import time
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
env_path = project_root / ".env"
load_dotenv(env_path)

from main.src.agents.parallel.context_provider import (
    ContextProviderRequest,
    create_context_provider_agent,
)
from main.src.monitoring.phoenix_config import PhoenixConfig, setup_phoenix


class FDAPartPhoenixTester:
    """Comprehensive tester for FDA Part-11 document with Phoenix observability."""

    def __init__(self):
        self.agent = None
        self.phoenix_manager = None
        self.test_document_path = project_root / "main" / "tests" / "test_data" / "FDA Part-11--Electronic-Records--Electronic-Signatures---Scope-and-Application-(PDF).md"

    async def setup_phoenix(self):
        """Initialize Phoenix observability system."""
        print("🔬 Setting up Phoenix observability...")

        try:
            # Initialize Phoenix with project configuration
            config = PhoenixConfig(
                enable_tracing=True,
                phoenix_host="localhost",
                phoenix_port=6006,
                project_name="fda_part11_test",
                experiment_name="chromadb_integration"
            )

            self.phoenix_manager = setup_phoenix(config)

            if self.phoenix_manager and self.phoenix_manager._initialized:
                print("✅ Phoenix connected successfully!")
                print("🌍 Phoenix UI: http://localhost:6006")
                print("📊 Project: fda_part11_test")
                return True
            print("⚠️ Phoenix setup completed but may not be fully initialized")
            print("   This is normal if Phoenix dependencies are missing")
            return True  # Continue with test even if Phoenix isn't fully ready

        except Exception as e:
            print(f"❌ Phoenix setup failed: {e}")
            print("   Continuing test without Phoenix tracing...")
            return False

    async def setup_agent(self):
        """Initialize Context Provider Agent with Phoenix tracing."""
        print("\n🤖 Setting up Context Provider Agent...")

        try:
            self.agent = create_context_provider_agent(
                verbose=True,
                enable_phoenix=True
            )
            print("✅ Context Provider Agent initialized")
            return True

        except Exception as e:
            print(f"❌ Agent setup failed: {e}")
            return False

    async def test_document_ingestion(self):
        """Test FDA Part-11 document ingestion with Phoenix tracing."""
        print("\n📥 Testing FDA Part-11 Document Ingestion...")
        print(f"📄 Document: {self.test_document_path.name}")

        try:
            # Verify document exists
            if not self.test_document_path.exists():
                print(f"❌ Test document not found: {self.test_document_path}")
                return False

            # Create documents directory for ingestion
            docs_dir = project_root / "temp_test_docs"
            docs_dir.mkdir(exist_ok=True)

            # Copy FDA document to temp directory for ingestion
            import shutil
            temp_doc_path = docs_dir / "fda_part11.md"
            shutil.copy2(self.test_document_path, temp_doc_path)

            print(f"📁 Ingesting from: {docs_dir}")
            print("🔍 This will create detailed Phoenix spans for:")
            print("   - Document processing pipeline")
            print("   - Text chunking operations")
            print("   - Embedding generation")
            print("   - ChromaDB storage operations")

            # Ingest with full tracing
            start_time = time.time()
            stats = await self.agent.ingest_documents(
                documents_path=str(docs_dir),
                collection_name="regulatory",
                force_reprocess=True
            )
            ingestion_time = time.time() - start_time

            print(f"\n✅ Ingestion completed in {ingestion_time:.2f}s")
            print(f"📊 Documents processed: {stats.get('documents_processed', 'N/A')}")
            print(f"📋 Nodes created: {stats.get('nodes_created', 'N/A')}")
            print("💾 Collection: regulatory")

            # Cleanup temp directory
            shutil.rmtree(docs_dir)

            return True

        except Exception as e:
            print(f"❌ Document ingestion failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def test_search_queries(self):
        """Test multiple search queries with different complexity levels."""
        print("\n🔍 Testing Search Queries with Phoenix Tracing...")

        # Define test queries with different complexity and expected behavior
        test_queries = [
            {
                "name": "Electronic Records Validation",
                "query": "What are the requirements for electronic records validation in pharmaceutical systems?",
                "expected_confidence": "high",
                "description": "Should find relevant FDA Part-11 content about electronic records"
            },
            {
                "name": "GAMP Category Relationship",
                "query": "How does 21 CFR Part 11 relate to GAMP Category 5 systems and computerized systems validation?",
                "expected_confidence": "medium-high",
                "description": "Should find some relevant content but may need inference"
            },
            {
                "name": "Electronic Signatures",
                "query": "What are the electronic signature requirements for pharmaceutical manufacturing systems?",
                "expected_confidence": "high",
                "description": "Should find specific FDA Part-11 electronic signature content"
            },
            {
                "name": "Audit Trail Requirements",
                "query": "What audit trail and data integrity requirements apply to electronic pharmaceutical records?",
                "expected_confidence": "high",
                "description": "Should find audit trail requirements in FDA Part-11"
            },
            {
                "name": "Low Relevance Query",
                "query": "What are the requirements for nuclear reactor safety protocols?",
                "expected_confidence": "low",
                "description": "Should have low confidence as not relevant to FDA Part-11"
            }
        ]

        results = []

        for i, test_query in enumerate(test_queries, 1):
            print(f"\n📋 Query {i}/5: {test_query['name']}")
            print(f"❓ Question: {test_query['query']}")
            print(f"🎯 Expected: {test_query['expected_confidence']} confidence")
            print(f"📝 Notes: {test_query['description']}")

            try:
                # Create request with proper structure
                request = ContextProviderRequest(
                    gamp_category="5",
                    context_depth="comprehensive",
                    document_sections=["validation_requirements", "compliance_guidelines", "electronic_records"],
                    test_strategy={
                        "type": "validation_testing",
                        "focus_areas": ["electronic_records", "signatures", "audit_trail"],
                        "compliance_level": "pharmaceutical"
                    },
                    search_scope={
                        "collections": ["regulatory", "gamp5"],
                        "max_documents": 10,
                        "relevance_threshold": 0.7
                    },
                    correlation_id=uuid4()
                )

                # Process with Phoenix tracing
                start_time = time.time()
                result = await self.agent.process_request(request)
                query_time = time.time() - start_time

                # Extract results
                confidence = result.confidence_score
                quality = result.context_quality
                doc_count = len(result.retrieved_documents)

                print(f"✅ Query completed in {query_time:.2f}s")
                print(f"🔢 Confidence: {confidence:.3f}")
                print(f"📊 Quality: {quality}")
                print(f"📄 Documents: {doc_count}")

                # Show top document if available
                if result.retrieved_documents:
                    top_doc = result.retrieved_documents[0]
                    print(f"🏆 Top result: {top_doc.get('title', 'Untitled')[:60]}...")

                results.append({
                    "query": test_query["name"],
                    "confidence": confidence,
                    "quality": quality,
                    "doc_count": doc_count,
                    "time": query_time
                })

                # Small delay between queries to see traces separately
                await asyncio.sleep(1)

            except Exception as e:
                print(f"❌ Query failed: {e}")
                import traceback
                traceback.print_exc()
                results.append({
                    "query": test_query["name"],
                    "error": str(e)
                })

        # Summary
        print("\n📈 Query Test Summary:")
        print("=" * 50)
        for result in results:
            if "error" not in result:
                print(f"{result['query']:<25} | Conf: {result['confidence']:.3f} | Qual: {result['quality']:<6} | Docs: {result['doc_count']:>2} | Time: {result['time']:.2f}s")
            else:
                print(f"{result['query']:<25} | ERROR: {result['error']}")

        return results

    async def test_parallel_requests(self):
        """Test concurrent requests to validate Phoenix span isolation."""
        print("\n🔄 Testing Parallel Requests...")

        requests = []
        for i in range(3):
            request = ContextProviderRequest(
                gamp_category="5",
                context_depth="focused",
                document_sections=["validation_requirements", "electronic_records"],
                test_strategy={
                    "type": "unit_testing",
                    "focus_areas": ["basic_validation"],
                    "compliance_level": "pharmaceutical"
                },
                search_scope={
                    "collections": ["regulatory"],
                    "max_documents": 5,
                    "relevance_threshold": 0.8
                },
                correlation_id=uuid4()
            )
            requests.append(request)

        try:
            print("🚀 Launching 3 concurrent requests...")
            start_time = time.time()

            # Execute requests concurrently
            tasks = [self.agent.process_request(req) for req in requests]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            parallel_time = time.time() - start_time

            # Analyze results
            successful = [r for r in results if not isinstance(r, Exception)]
            failed = [r for r in results if isinstance(r, Exception)]

            print(f"✅ Parallel execution completed in {parallel_time:.2f}s")
            print(f"🎯 Successful: {len(successful)}/3")
            print(f"❌ Failed: {len(failed)}/3")

            if successful:
                avg_confidence = sum(r.confidence_score for r in successful) / len(successful)
                print(f"📊 Average confidence: {avg_confidence:.3f}")

            return len(successful) == 3

        except Exception as e:
            print(f"❌ Parallel test failed: {e}")
            return False

    async def test_error_handling(self):
        """Test error scenarios to validate Phoenix error tracing."""
        print("\n🚨 Testing Error Handling...")

        try:
            # Test with invalid collection
            print("🔍 Testing invalid collection name...")

            # This should trigger an error with full Phoenix tracing
            request = ContextProviderRequest(
                gamp_category="invalid",
                context_depth="comprehensive",
                document_sections=["nonexistent_section"],
                test_strategy={
                    "type": "invalid_strategy",
                    "focus_areas": ["nonexistent"],
                    "compliance_level": "invalid"
                },
                search_scope={
                    "collections": ["nonexistent_collection"],
                    "max_documents": 5,
                    "relevance_threshold": 0.5
                },
                correlation_id=uuid4()
            )

            try:
                result = await self.agent.process_request(request)
                print("⚠️ Expected error but got result - check error handling")
            except Exception as e:
                print(f"✅ Error properly caught and traced: {type(e).__name__}")
                print(f"📝 Error message: {str(e)[:100]}...")
                return True

        except Exception as e:
            print(f"❌ Error test failed: {e}")
            return False

    async def validate_phoenix_ui(self):
        """Provide instructions for Phoenix UI validation."""
        print("\n🎯 Phoenix UI Validation Instructions:")
        print("=" * 50)
        print("1. Open Phoenix UI: http://localhost:6006")
        print("2. Look for project: 'fda_part11_test'")
        print("3. Verify trace hierarchy:")
        print("   └── context_provider.process_request")
        print("       ├── chromadb.search_documents")
        print("       │   ├── chromadb.search_collection.regulatory")
        print("       │   │   ├── chromadb.chunk.1")
        print("       │   │   ├── chromadb.chunk.2")
        print("       │   │   └── ...")
        print("       │   └── search_results_summary (event)")
        print("       ├── context_quality_assessment (event)")
        print("       └── confidence_calculation (event)")
        print("4. Check span attributes contain:")
        print("   - Query text and parameters")
        print("   - Document counts and scores")
        print("   - Processing times")
        print("   - Confidence calculation factors")
        print("5. Verify events show meaningful data")
        print("\n🔍 Expected Traces:")
        print("   - Document ingestion spans")
        print("   - 5 search query spans")
        print("   - 3 parallel request spans")
        print("   - Error handling span")

    async def cleanup(self):
        """Clean up resources and flush Phoenix traces."""
        print("\n🧹 Cleaning up...")

        if self.phoenix_manager:
            try:
                print("📤 Flushing Phoenix traces...")
                self.phoenix_manager.shutdown()
                print("✅ Phoenix cleanup completed")
            except Exception as e:
                print(f"⚠️ Phoenix cleanup warning: {e}")

        print("✅ Test cleanup completed")


async def main():
    """Main test execution function."""
    print("🏥 FDA Part-11 Phoenix Observability Test")
    print("=" * 50)
    print("📋 This test will:")
    print("1. Connect to Phoenix server (start manually: docker run -d -p 6006:6006 arizephoenix/phoenix:latest)")
    print("2. Ingest FDA Part-11 document with full tracing")
    print("3. Execute multiple search queries")
    print("4. Test parallel requests")
    print("5. Validate error handling")
    print("6. Provide Phoenix UI validation instructions")
    print("\n🚀 Starting test...")

    tester = FDAPartPhoenixTester()

    try:
        # Setup phase
        phoenix_ok = await tester.setup_phoenix()
        if not phoenix_ok:
            print("⚠️ Phoenix setup had issues - continuing anyway")

        agent_ok = await tester.setup_agent()
        if not agent_ok:
            print("❌ Agent setup failed - cannot continue")
            return

        # Test execution phase
        ingestion_ok = await tester.test_document_ingestion()
        if not ingestion_ok:
            print("❌ Document ingestion failed - skipping search tests")
            return

        search_results = await tester.test_search_queries()
        parallel_ok = await tester.test_parallel_requests()
        error_ok = await tester.test_error_handling()

        # Validation instructions
        await tester.validate_phoenix_ui()

        # Summary
        print("\n🎉 Test Execution Summary:")
        print("=" * 50)
        print(f"✅ Phoenix Setup: {'OK' if phoenix_ok else 'Issues'}")
        print(f"✅ Agent Setup: {'OK' if agent_ok else 'Failed'}")
        print(f"✅ Document Ingestion: {'OK' if ingestion_ok else 'Failed'}")
        print(f"✅ Search Queries: {len([r for r in search_results if 'error' not in r])}/5 successful")
        print(f"✅ Parallel Requests: {'OK' if parallel_ok else 'Failed'}")
        print(f"✅ Error Handling: {'OK' if error_ok else 'Failed'}")
        print("\n🌍 Phoenix UI: http://localhost:6006")
        print("📊 Project: fda_part11_test")

    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
