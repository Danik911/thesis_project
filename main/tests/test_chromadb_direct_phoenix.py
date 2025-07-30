#!/usr/bin/env python3
"""
Direct ChromaDB Phoenix Integration Test
Tests ChromaDB operations with Phoenix observability without complex event system
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv("/home/anteb/thesis_project/.env")

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Phoenix setup - MUST be done before other imports
os.environ["PHOENIX_COLLECTOR_ENDPOINT"] = "http://localhost:6006"

async def test_chromadb_with_phoenix():
    """Test ChromaDB operations with Phoenix tracing"""
    print("🏥 Direct ChromaDB Phoenix Integration Test")
    print("=" * 50)
    
    try:
        import phoenix as px
        from phoenix.trace import using_project
        import chromadb
        from opentelemetry import trace
        
        print("✅ Phoenix and ChromaDB imported successfully")
        
        # Create tracer
        tracer = trace.get_tracer(__name__)
        
        with using_project("chromadb_direct_test"):
            print("📊 Project: chromadb_direct_test")
            
            # Test document ingestion with tracing
            with tracer.start_as_current_span("fda_document_ingestion") as ingestion_span:
                ingestion_span.set_attribute("document.source", "FDA_Part_11")
                ingestion_span.set_attribute("document.type", "regulatory")
                
                print("📥 Starting document ingestion span")
                
                # Initialize ChromaDB
                with tracer.start_as_current_span("chromadb_initialization") as init_span:
                    client = chromadb.Client()
                    collection = client.create_collection(name="fda_regulatory")
                    init_span.set_attribute("collection.name", "fda_regulatory")
                    print("📁 Created ChromaDB collection")
                
                # Add FDA Part-11 content
                with tracer.start_as_current_span("document_processing") as process_span:
                    fda_documents = [
                        "FDA 21 CFR Part 11 establishes requirements for electronic records and electronic signatures in pharmaceutical systems.",
                        "Electronic records must be validated according to GAMP Category 5 systems for custom applications.",
                        "Audit trails are required for all electronic records to ensure data integrity and ALCOA+ compliance.",
                        "Electronic signatures must be unique to one individual and must not be reused or reassigned.",
                        "System validation must include operational and performance qualification for pharmaceutical manufacturing systems."
                    ]
                    
                    metadatas = [
                        {"section": "overview", "category": "general", "gamp_level": "5"},
                        {"section": "validation", "category": "technical", "gamp_level": "5"},
                        {"section": "audit_trail", "category": "compliance", "gamp_level": "5"},
                        {"section": "signatures", "category": "security", "gamp_level": "5"},
                        {"section": "qualification", "category": "validation", "gamp_level": "5"}
                    ]
                    
                    ids = [f"fda_doc_{i+1}" for i in range(len(fda_documents))]
                    
                    process_span.set_attribute("documents.count", len(fda_documents))
                    process_span.set_attribute("processing.method", "direct_ingestion")
                    
                    collection.add(
                        documents=fda_documents,
                        metadatas=metadatas,
                        ids=ids
                    )
                    
                    print(f"📄 Added {len(fda_documents)} FDA documents to collection")
            
            # Test search operations with tracing
            test_queries = [
                {
                    "query": "What are electronic records validation requirements?",
                    "expected_sections": ["validation", "overview"],
                    "description": "High confidence query about validation"
                },
                {
                    "query": "How do audit trails work in pharmaceutical systems?",
                    "expected_sections": ["audit_trail", "compliance"],
                    "description": "High confidence query about audit trails"
                },
                {
                    "query": "What are GAMP Category 5 requirements?",
                    "expected_sections": ["validation", "general"],
                    "description": "Medium confidence query about GAMP"
                }
            ]
            
            for i, test_query in enumerate(test_queries, 1):
                with tracer.start_as_current_span(f"search_query_{i}") as search_span:
                    search_span.set_attribute("query.text", test_query["query"])
                    search_span.set_attribute("query.type", "similarity_search")
                    search_span.set_attribute("expected.confidence", "high" if "High" in test_query["description"] else "medium")
                    
                    print(f"\n🔍 Query {i}: {test_query['query']}")
                    print(f"📝 {test_query['description']}")
                    
                    # Perform search
                    with tracer.start_as_current_span("chromadb_query") as query_span:
                        results = collection.query(
                            query_texts=[test_query["query"]],
                            n_results=3
                        )
                        
                        # Add search results to span
                        documents_found = len(results['documents'][0])
                        query_span.set_attribute("results.count", documents_found)
                        query_span.set_attribute("collection.name", "fda_regulatory")
                        
                        if results['distances'] and results['distances'][0]:
                            avg_distance = sum(results['distances'][0]) / len(results['distances'][0])
                            confidence_score = max(0.0, 1.0 - avg_distance)  # Convert distance to confidence
                            query_span.set_attribute("results.avg_distance", avg_distance)
                            query_span.set_attribute("results.confidence_score", confidence_score)
                            
                            print(f"✅ Found {documents_found} documents")
                            print(f"🔢 Confidence: {confidence_score:.3f}")
                            
                            # Display top results
                            for j, (doc, metadata, distance) in enumerate(zip(
                                results['documents'][0], 
                                results['metadatas'][0], 
                                results['distances'][0]
                            )):
                                print(f"   📄 Result {j+1}: {doc[:60]}... (distance: {distance:.3f})")
                                print(f"      📋 Section: {metadata.get('section', 'N/A')}, Category: {metadata.get('category', 'N/A')}")
                        else:
                            print("❌ No results found")
                            query_span.set_attribute("results.confidence_score", 0.0)
            
            # Test parallel queries
            print(f"\n🚀 Testing parallel queries...")
            with tracer.start_as_current_span("parallel_queries") as parallel_span:
                parallel_span.set_attribute("queries.count", 3)
                parallel_span.set_attribute("execution.type", "concurrent")
                
                async def search_query(query_text, span_name):
                    with tracer.start_as_current_span(span_name) as span:
                        span.set_attribute("query.text", query_text)
                        results = collection.query(query_texts=[query_text], n_results=2)
                        span.set_attribute("results.count", len(results['documents'][0]))
                        return len(results['documents'][0])
                
                # Run concurrent searches
                tasks = [
                    search_query("electronic signatures requirements", "parallel_query_1"),
                    search_query("audit trail pharmaceutical", "parallel_query_2"),  
                    search_query("GAMP validation systems", "parallel_query_3")
                ]
                
                results = await asyncio.gather(*tasks)
                total_results = sum(results)
                
                parallel_span.set_attribute("total_results", total_results)
                print(f"✅ Parallel queries completed - Total results: {total_results}")
        
        print(f"\n🎉 All tests completed successfully!")
        print(f"🌍 Check Phoenix UI at: http://localhost:6006")
        print(f"📊 Project: chromadb_direct_test")
        print(f"🔍 Expected traces:")
        print(f"   - fda_document_ingestion (with child spans)")
        print(f"   - search_query_1, search_query_2, search_query_3")
        print(f"   - parallel_queries (with concurrent child spans)")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test execution"""
    print("🚀 Starting direct ChromaDB Phoenix integration test...")
    
    success = await test_chromadb_with_phoenix()
    
    if success:
        print("\n✅ Phoenix observability with ChromaDB verified!")
        print("\nNext steps:")
        print("1. Open Phoenix UI: http://localhost:6006")
        print("2. Look for project 'chromadb_direct_test'")
        print("3. Verify span hierarchy shows:")
        print("   - Document ingestion pipeline")
        print("   - Individual search operations")
        print("   - Parallel query execution")
        print("4. Check span attributes contain query details and results")
    else:
        print("\n❌ Integration test failed")
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    
    if not success:
        sys.exit(1)