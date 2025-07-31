#!/usr/bin/env python3
"""
Basic Phoenix Trace Test for ChromaDB Integration
Tests the core tracing functionality with minimal dependencies
"""

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

def test_basic_phoenix_connection():
    """Test basic Phoenix connection and tracing"""
    print("🏥 Basic Phoenix Trace Test")
    print("=" * 50)
    
    try:
        # Import Phoenix after setting environment
        import phoenix as px
        from phoenix.trace import using_project
        
        print("✅ Phoenix imported successfully")
        
        # Test creating traces with project context
        with using_project("basic_phoenix_test"):
            print("📊 Creating test traces in project: basic_phoenix_test")
            
            # Create a simple trace span
            tracer = px.Client().tracer
            
            with tracer.start_as_current_span("test_document_ingestion") as span:
                span.set_attribute("document.name", "FDA_Part_11_test.md")
                span.set_attribute("document.size", "12345")
                span.set_attribute("collection.name", "regulatory")
                
                print("🔍 Created document ingestion span")
                
                # Child span for processing
                with tracer.start_as_current_span("process_document") as child_span:
                    child_span.set_attribute("chunks.count", 5)
                    child_span.set_attribute("embeddings.model", "text-embedding-ada-002")
                    child_span.set_attribute("processing.time_ms", 1500)
                    
                    print("📄 Created document processing child span")
                    
                    # Another child span for ChromaDB operations
                    with tracer.start_as_current_span("chromadb_store") as db_span:
                        db_span.set_attribute("chromadb.collection", "regulatory")
                        db_span.set_attribute("chromadb.operation", "add")
                        db_span.set_attribute("chromadb.documents_added", 5)
                        
                        print("💾 Created ChromaDB storage span")
            
            # Create a search trace
            with tracer.start_as_current_span("test_document_search") as search_span:
                search_span.set_attribute("query.text", "What are electronic records in FDA Part 11?")
                search_span.set_attribute("search.collection", "regulatory")
                search_span.set_attribute("search.max_results", 10)
                
                print("🔍 Created document search span")
                
                # Child span for retrieval
                with tracer.start_as_current_span("chromadb_search") as retrieval_span:
                    retrieval_span.set_attribute("chromadb.query_type", "similarity")
                    retrieval_span.set_attribute("chromadb.results_found", 3)
                    retrieval_span.set_attribute("confidence.avg_score", 0.85)
                    
                    print("📊 Created search retrieval child span")
        
        print("\n✅ All traces created successfully!")
        print("🌍 Check Phoenix UI at: http://localhost:6006")
        print("📊 Project name: basic_phoenix_test")
        print("🔍 You should see:")
        print("   - test_document_ingestion span with child spans")
        print("   - test_document_search span with child spans")
        print("   - Attributes showing document metadata")
        print("   - ChromaDB operation details")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_simple_chromadb_operation():
    """Test a simple ChromaDB operation with Phoenix tracing"""
    print("\n🗄️ Testing Simple ChromaDB Operation...")
    
    try:
        import chromadb
        import phoenix as px
        from phoenix.trace import using_project
        
        # Create in-memory ChromaDB client
        client = chromadb.Client()
        
        with using_project("chromadb_basic_test"):
            tracer = px.Client().tracer
            
            with tracer.start_as_current_span("chromadb_collection_create") as span:
                span.set_attribute("operation", "create_collection")
                span.set_attribute("collection.name", "test_regulatory")
                
                # Create collection
                collection = client.create_collection(name="test_regulatory")
                
                print("📁 Created ChromaDB collection")
                
                with tracer.start_as_current_span("chromadb_add_documents") as add_span:
                    add_span.set_attribute("documents.count", 2)
                    add_span.set_attribute("operation", "add")
                    
                    # Add some test documents
                    collection.add(
                        documents=[
                            "FDA Part 11 establishes requirements for electronic records and signatures.",
                            "Electronic records must be validated according to GAMP-5 Category 5 systems."
                        ],
                        metadatas=[
                            {"source": "fda_part11", "section": "overview"},
                            {"source": "fda_part11", "section": "validation"}
                        ],
                        ids=["doc1", "doc2"]
                    )
                    
                    print("📄 Added documents to collection")
                
                with tracer.start_as_current_span("chromadb_query") as query_span:
                    query_span.set_attribute("query.text", "electronic records validation")
                    query_span.set_attribute("n_results", 2)
                    
                    # Query the collection
                    results = collection.query(
                        query_texts=["electronic records validation"],
                        n_results=2
                    )
                    
                    query_span.set_attribute("results.found", len(results['documents'][0]))
                    
                    print(f"🔍 Query returned {len(results['documents'][0])} results")
                    for i, doc in enumerate(results['documents'][0]):
                        print(f"   Result {i+1}: {doc[:50]}...")
        
        print("✅ ChromaDB operation completed with Phoenix tracing")
        return True
        
    except Exception as e:
        print(f"❌ ChromaDB test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Phoenix ChromaDB integration tests...")
    
    # Test 1: Basic Phoenix connection and tracing
    test1_ok = test_basic_phoenix_connection()
    
    # Test 2: Simple ChromaDB with tracing
    test2_ok = test_simple_chromadb_operation()
    
    if test1_ok and test2_ok:
        print("\n🎉 All tests passed!")
        print("\n📋 Next steps:")
        print("1. Open Phoenix UI: http://localhost:6006")
        print("2. Look for projects: 'basic_phoenix_test' and 'chromadb_basic_test'")
        print("3. Verify span hierarchy and attributes are visible")
        print("4. Check that document ingestion, search, and ChromaDB operations are traced")
        return True
    else:
        print("\n❌ Some tests failed")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Phoenix observability integration verified!")
    else:
        print("\n❌ Integration test failed")
        sys.exit(1)