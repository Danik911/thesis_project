"""
Test script for Context Provider Agent with Phoenix observability.

This script demonstrates:
1. Phoenix tracing integration with ChromaDB operations
2. Comprehensive logging of document retrieval
3. Confidence score calculation visibility
4. Error handling with full diagnostics
"""

import asyncio
import os
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
    ContextProviderAgent,
    ContextProviderRequest,
    create_context_provider_agent
)
from main.src.core.events import AgentRequestEvent
from main.src.monitoring.phoenix_config import setup_phoenix, shutdown_phoenix


async def test_context_provider_with_phoenix():
    """Test the Context Provider Agent with Phoenix observability enabled."""
    print("🔬 Testing Context Provider Agent with Phoenix Observability\n")
    
    # 1. Setup Phoenix
    print("1️⃣ Setting up Phoenix observability...")
    phoenix_manager = setup_phoenix()
    print("✅ Phoenix observability initialized\n")
    
    # 2. Initialize agent with Phoenix enabled
    print("2️⃣ Initializing Context Provider Agent with Phoenix tracing...")
    agent = create_context_provider_agent(
        verbose=True,
        enable_phoenix=True
    )
    print("✅ Agent initialized with Phoenix tracing enabled\n")
    
    # 3. Create and ingest test documents
    print("3️⃣ Creating test pharmaceutical documents...")
    test_docs_dir = Path("./test_docs")
    test_docs_dir.mkdir(exist_ok=True)
    
    # Create GAMP-5 test document with high relevance content
    gamp5_content = """
    # GAMP-5 Testing Guidelines for Category 4 Systems
    
    ## Overview
    This document provides comprehensive testing guidelines for GAMP Category 4 
    (Configured Software) systems in pharmaceutical environments.
    
    ## Validation Requirements
    1. Risk Assessment: Perform FMEA analysis for all critical functions
    2. Installation Qualification (IQ): Verify proper installation
    3. Operational Qualification (OQ): Confirm operational parameters
    4. Performance Qualification (PQ): Validate performance metrics
    
    ## Testing Strategy
    - Unit Testing: Required for custom configurations
    - Integration Testing: Mandatory for system interfaces
    - System Testing: Full validation protocol required
    - User Acceptance Testing: With qualified personnel
    
    ## Risk Assessment
    All Category 4 systems require comprehensive risk assessment including:
    - Patient impact analysis
    - Data integrity risk evaluation
    - System criticality assessment
    
    ## Compliance Requirements
    - 21 CFR Part 11 electronic records and signatures
    - ALCOA+ data integrity principles
    - Audit trail implementation and validation
    - Change control procedures
    """
    
    gamp5_path = test_docs_dir / "gamp5_category_4_guidelines.md"
    gamp5_path.write_text(gamp5_content)
    
    # Create regulatory document
    regulatory_content = """
    # 21 CFR Part 11 Compliance Framework for Category 4 Systems
    
    ## Electronic Records Requirements
    1. Secure, computer-generated timestamps for all records
    2. Use of secure electronic signatures with authentication
    3. Ability to generate accurate and complete copies
    4. Protection of records throughout retention period
    
    ## Audit Trail Requirements for Category 4
    - Record creation, modification, and deletion events
    - User identification for all actions with role-based access
    - Time and date stamps with timezone information
    - Reason for change documentation with approval workflow
    
    ## Validation Requirements
    - System validation documentation per GAMP-5 guidelines
    - Change control procedures with impact assessment
    - Backup and recovery procedures with RPO/RTO defined
    - Security controls validation including penetration testing
    
    ## Testing Requirements
    Integration testing must cover all electronic record operations
    Performance testing for audit trail under load conditions
    Security testing for access controls and data encryption
    """
    
    regulatory_path = test_docs_dir / "21cfr_part11_category4.md"
    regulatory_path.write_text(regulatory_content)
    
    print(f"✅ Created test documents in {test_docs_dir}\n")
    
    # 4. Ingest documents with Phoenix tracing
    print("4️⃣ Ingesting documents into ChromaDB (observe Phoenix traces)...")
    
    # Ingest GAMP-5 document
    gamp5_stats = await agent.ingest_documents(
        documents_path=str(gamp5_path),
        collection_name="gamp5",
        force_reprocess=True
    )
    print(f"   GAMP-5 ingestion stats: {gamp5_stats}\n")
    
    # Ingest regulatory document
    regulatory_stats = await agent.ingest_documents(
        documents_path=str(regulatory_path),
        collection_name="regulatory",
        force_reprocess=True
    )
    print(f"   Regulatory ingestion stats: {regulatory_stats}\n")
    
    # 5. Test search with comprehensive Phoenix tracing
    print("5️⃣ Testing document search with Phoenix observability...")
    
    # Create test request with specific requirements
    request_event = AgentRequestEvent(
        agent_type="context_provider",
        request_data={
            "gamp_category": "4",
            "test_strategy": {
                "test_types": ["unit_testing", "integration_testing", "validation", "security_testing"]
            },
            "document_sections": [
                "validation_requirements", 
                "testing_strategy", 
                "risk_assessment",
                "audit_trail_requirements"
            ],
            "search_scope": {
                "collections": ["gamp5", "regulatory"],
                "include_best_practices": True,
                "focus_areas": ["Category 4", "audit trail", "electronic records"]
            },
            "context_depth": "comprehensive"
        },
        correlation_id=uuid4(),
        requesting_step="phoenix_test_search"
    )
    
    # Process request with full Phoenix tracing
    print("\n   🔍 Executing search (check Phoenix UI for detailed traces)...")
    result = await agent.process_request(request_event)
    
    print(f"\n   📊 Search Results:")
    print(f"      - Success: {result.success}")
    print(f"      - Processing time: {result.processing_time:.2f}s")
    print(f"      - Documents retrieved: {len(result.result_data.get('retrieved_documents', []))}")
    print(f"      - Context quality: {result.result_data.get('context_quality', 'unknown')}")
    print(f"      - Search coverage: {result.result_data.get('search_coverage', 0.0):.2%}")
    print(f"      - Confidence score: {result.result_data.get('confidence_score', 0.0):.2%}")
    
    if result.success and result.result_data.get('retrieved_documents'):
        print(f"\n   📄 Top Retrieved Documents:")
        for i, doc in enumerate(result.result_data['retrieved_documents'][:5], 1):
            print(f"      {i}. {doc.get('title', 'Unknown')}")
            print(f"         - Relevance: {doc.get('relevance_score', 0.0):.3f}")
            print(f"         - Type: {doc.get('type', 'unknown')}")
            print(f"         - Collection: {doc.get('collection', 'unknown')}")
            print(f"         - GAMP Categories: {doc.get('gamp_categories', [])}")
    
    print("\n✅ Search completed - check Phoenix UI for detailed traces\n")
    
    # 6. Test error handling with Phoenix tracing
    print("6️⃣ Testing error handling with full diagnostics...")
    
    # Test with invalid search that should fail
    error_request = AgentRequestEvent(
        agent_type="context_provider",
        request_data={
            "gamp_category": "invalid",  # Invalid GAMP category
            "test_strategy": {},
            "document_sections": ["nonexistent_section"],
            "search_scope": {"collections": ["nonexistent_collection"]},
            "context_depth": "standard"
        },
        correlation_id=uuid4(),
        requesting_step="phoenix_error_test"
    )
    
    error_result = await agent.process_request(error_request)
    if not error_result.success:
        print(f"   ✅ Error properly traced: {error_result.error_message}")
        print(f"   📊 Check Phoenix UI for error details and stack trace\n")
    
    # 7. Performance statistics
    print("7️⃣ Agent Performance Statistics:")
    stats = agent.get_performance_stats()
    print(f"   - Total requests: {stats['total_requests']}")
    print(f"   - Successful requests: {stats['successful_requests']}")
    print(f"   - Average processing time: {stats['avg_processing_time']:.2f}s")
    print(f"   - Documents in collections:")
    for key, value in stats.items():
        if key.endswith('_documents'):
            print(f"     - {key}: {value}")
    
    # Cleanup
    print("\n8️⃣ Cleaning up test data...")
    for file in test_docs_dir.glob("*.md"):
        file.unlink()
    test_docs_dir.rmdir()
    print("✅ Test cleanup complete\n")
    
    # Shutdown Phoenix with trace flush
    print("9️⃣ Shutting down Phoenix (flushing traces)...")
    shutdown_phoenix(timeout_seconds=5)
    print("✅ Phoenix shutdown complete\n")
    
    print("🎉 All tests completed! Check Phoenix UI at http://localhost:6006 for:")
    print("   - Detailed span hierarchy")
    print("   - ChromaDB operation traces")
    print("   - Document retrieval metrics")
    print("   - Confidence score calculations")
    print("   - Error diagnostics with stack traces")
    
    return True


async def test_parallel_requests_with_phoenix():
    """Test parallel request handling with Phoenix tracing."""
    print("\n🔄 Testing parallel requests with Phoenix tracing...")
    
    # Setup Phoenix if not already setup
    phoenix_manager = setup_phoenix()
    
    agent = create_context_provider_agent(verbose=False, enable_phoenix=True)
    
    # Create multiple requests with different GAMP categories
    requests = []
    for i in range(3):
        request = AgentRequestEvent(
            agent_type="context_provider",
            request_data={
                "gamp_category": str(3 + i),  # Categories 3, 4, 5
                "test_strategy": {"test_types": ["validation", "integration_testing"]},
                "document_sections": ["requirements", "testing_strategy"],
                "search_scope": {"collections": ["gamp5", "regulatory"]}
            },
            correlation_id=uuid4(),
            requesting_step=f"parallel_phoenix_test_{i}"
        )
        requests.append(agent.process_request(request))
    
    # Process in parallel
    results = await asyncio.gather(*requests)
    
    success_count = sum(1 for r in results if r.success)
    print(f"✅ Processed {success_count}/{len(results)} requests in parallel")
    print(f"   Check Phoenix UI for parallel execution traces\n")


if __name__ == "__main__":
    # Run tests
    asyncio.run(test_context_provider_with_phoenix())
    asyncio.run(test_parallel_requests_with_phoenix())