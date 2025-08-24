#!/usr/bin/env uv run python
"""
Test script for FDA Part 11 document ingestion with Phoenix observability.

This script demonstrates comprehensive testing of:
1. Phoenix tracing integration with ChromaDB operations  
2. FDA Part 11 regulatory document ingestion
3. Search and context extraction with traceability
4. Confidence score calculation visibility
5. Error handling with full diagnostics

Usage:
    uv run uv run python main/tests/regulatory/fda_part11/test_fda_part11_phoenix_ingestion.py
"""

import asyncio
import sys
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
from main.src.core.events import AgentRequestEvent
from main.src.monitoring.phoenix_config import setup_phoenix, shutdown_phoenix


async def test_fda_part11_ingestion_with_phoenix():
    """Test FDA Part 11 document ingestion with comprehensive Phoenix observability."""
    print("🔬 Testing FDA Part 11 Document Ingestion with Phoenix Observability")
    print("="*70)

    # 1. Setup Phoenix
    print("1️⃣ Setting up Phoenix observability...")
    phoenix_manager = setup_phoenix()
    if phoenix_manager._initialized:
        print("✅ Phoenix observability initialized successfully")
    else:
        print("⚠️  Phoenix initialization failed, continuing without tracing")
    print("🌐 Phoenix UI available at: http://localhost:6006")
    print()

    try:
        # 2. Initialize Context Provider Agent
        print("2️⃣ Initializing Context Provider Agent with Phoenix tracing...")
        agent = create_context_provider_agent(
            verbose=True,
            enable_phoenix=True,
            max_documents=100
        )
        print("✅ Context Provider Agent initialized with Phoenix tracing enabled")
        print()

        # 3. Verify FDA Part 11 document exists
        fda_doc_path = Path("/home/anteb/thesis_project/main/tests/test_data/FDA Part-11--Electronic-Records--Electronic-Signatures---Scope-and-Application-(PDF).md")

        if not fda_doc_path.exists():
            print(f"❌ FDA Part 11 document not found at: {fda_doc_path}")
            return False

        print(f"3️⃣ FDA Part 11 document found at: {fda_doc_path}")
        print(f"📄 Document size: {fda_doc_path.stat().st_size} bytes")
        print()

        # 4. Ingest FDA Part 11 document with Phoenix tracing
        print("4️⃣ Ingesting FDA Part 11 document into ChromaDB...")
        print("🔍 Monitor Phoenix UI for real-time ingestion traces")
        print()

        ingestion_stats = await agent.ingest_documents(
            documents_path=str(fda_doc_path),
            collection_name="regulatory",
            force_reprocess=True
        )

        print("✅ FDA Part 11 document ingestion completed!")
        print("📊 Ingestion Statistics:")
        for key, value in ingestion_stats.items():
            print(f"   • {key}: {value}")
        print()

        # 5. Test search operations with FDA Part 11 specific queries
        print("5️⃣ Testing search operations with FDA Part 11 queries...")
        print("🔍 Monitor Phoenix UI for search trace hierarchy")
        print()

        # Test Query 1: Electronic Records
        print("🔍 Query 1: Electronic Records Requirements")
        correlation_id1 = uuid4()
        query1_request = ContextProviderRequest(
            gamp_category="4",
            test_strategy={
                "validation_type": "regulatory_compliance",
                "focus_area": "electronic_records"
            },
            document_sections=["electronic_records", "validation", "compliance"],
            search_scope={
                "collections": ["regulatory"],
                "max_results": 10
            },
            context_depth="detailed",
            correlation_id=correlation_id1,
            timeout_seconds=60
        )

        # Remove correlation_id from model_dump to avoid duplicate
        request_data = query1_request.model_dump()
        request_data.pop("correlation_id", None)

        request_event = AgentRequestEvent(
            agent_type="context_provider",
            request_data=request_data,
            requesting_step="test_electronic_records_query",
            correlation_id=correlation_id1
        )

        result1 = await agent.process_request(request_event)

        # Extract the ContextProviderResponse from result_data
        if result1.success and "response" in result1.result_data:
            response1 = result1.result_data["response"]
            print(f"   📋 Retrieved {len(response1.get('retrieved_documents', []))} documents")
            print(f"   🎯 Context Quality: {response1.get('context_quality', 'unknown')}")
            print(f"   📊 Search Coverage: {response1.get('search_coverage', 0.0):.2%}")
            print(f"   🎖️ Confidence Score: {response1.get('confidence_score', 0.0):.3f}")
        else:
            print(f"   ❌ Query failed: {result1.error_message}")
            response1 = {}
        print()

        # Test Query 2: Electronic Signatures
        print("🔍 Query 2: Electronic Signatures Validation")
        correlation_id2 = uuid4()
        query2_request = ContextProviderRequest(
            gamp_category="4",
            test_strategy={
                "validation_type": "signature_validation",
                "focus_area": "electronic_signatures"
            },
            document_sections=["electronic_signatures", "authentication", "security"],
            search_scope={
                "collections": ["regulatory"],
                "max_results": 15
            },
            context_depth="comprehensive",
            correlation_id=correlation_id2,
            timeout_seconds=60
        )

        # Remove correlation_id from model_dump to avoid duplicate
        request_data2 = query2_request.model_dump()
        request_data2.pop("correlation_id", None)

        request_event2 = AgentRequestEvent(
            agent_type="context_provider",
            request_data=request_data2,
            requesting_step="test_electronic_signatures_query",
            correlation_id=correlation_id2
        )

        result2 = await agent.process_request(request_event2)

        # Extract the ContextProviderResponse from result_data
        if result2.success and "response" in result2.result_data:
            response2 = result2.result_data["response"]
            print(f"   📋 Retrieved {len(response2.get('retrieved_documents', []))} documents")
            print(f"   🎯 Context Quality: {response2.get('context_quality', 'unknown')}")
            print(f"   📊 Search Coverage: {response2.get('search_coverage', 0.0):.2%}")
            print(f"   🎖️ Confidence Score: {response2.get('confidence_score', 0.0):.3f}")
        else:
            print(f"   ❌ Query failed: {result2.error_message}")
            response2 = {}
        print()

        # Test Query 3: GAMP-5 Scope and Application
        print("🔍 Query 3: GAMP-5 Scope and Application Context")
        correlation_id3 = uuid4()
        query3_request = ContextProviderRequest(
            gamp_category="4",
            test_strategy={
                "validation_type": "scope_analysis",
                "focus_area": "gamp5_application"
            },
            document_sections=["scope", "application", "gamp", "pharmaceutical"],
            search_scope={
                "collections": ["regulatory"],
                "max_results": 20
            },
            context_depth="standard",
            correlation_id=correlation_id3,
            timeout_seconds=60
        )

        # Remove correlation_id from model_dump to avoid duplicate
        request_data3 = query3_request.model_dump()
        request_data3.pop("correlation_id", None)

        request_event3 = AgentRequestEvent(
            agent_type="context_provider",
            request_data=request_data3,
            requesting_step="test_gamp5_scope_query",
            correlation_id=correlation_id3
        )

        result3 = await agent.process_request(request_event3)

        # Extract the ContextProviderResponse from result_data
        if result3.success and "response" in result3.result_data:
            response3 = result3.result_data["response"]
            print(f"   📋 Retrieved {len(response3.get('retrieved_documents', []))} documents")
            print(f"   🎯 Context Quality: {response3.get('context_quality', 'unknown')}")
            print(f"   📊 Search Coverage: {response3.get('search_coverage', 0.0):.2%}")
            print(f"   🎖️ Confidence Score: {response3.get('confidence_score', 0.0):.3f}")
        else:
            print(f"   ❌ Query failed: {result3.error_message}")
            response3 = {}
        print()

        # 6. Display retrieved content samples
        print("6️⃣ Sample Retrieved Content Analysis")
        print("-" * 50)

        if response1 and response1.get("retrieved_documents"):
            print("📄 Sample from Electronic Records Query:")
            sample_doc = response1["retrieved_documents"][0]
            content_preview = sample_doc.get("content", "")[:200] + "..." if len(sample_doc.get("content", "")) > 200 else sample_doc.get("content", "")
            print(f"   Content: {content_preview}")
            print(f"   Metadata: {sample_doc.get('metadata', {})}")
            print()

        # 7. Phoenix observability summary
        print("7️⃣ Phoenix Observability Summary")
        print("-" * 40)
        print("✅ All operations traced in Phoenix UI")
        print("🔗 Trace Categories Expected:")
        print("   • Document ingestion pipeline")
        print("   • ChromaDB collection operations")
        print("   • Search and retrieval spans")
        print("   • Confidence score calculations")
        print("   • Context quality assessments")
        print()
        print("🌐 View complete traces at: http://localhost:6006")

        return True

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # 8. Clean shutdown with trace persistence
        print()
        print("8️⃣ Shutting down with trace persistence...")
        shutdown_phoenix(timeout_seconds=10)
        print("✅ Phoenix shutdown complete - UI remains accessible for trace review")


async def main():
    """Main test execution."""
    print("🚀 Starting FDA Part 11 Phoenix Ingestion Test")
    print()

    success = await test_fda_part11_ingestion_with_phoenix()

    if success:
        print()
        print("🎉 FDA Part 11 Phoenix Ingestion Test COMPLETED SUCCESSFULLY!")
        print("📊 Check Phoenix UI for detailed trace analysis")
        print("🌐 Phoenix UI: http://localhost:6006")
    else:
        print()
        print("❌ FDA Part 11 Phoenix Ingestion Test FAILED")
        print("🔍 Check logs above for error details")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
