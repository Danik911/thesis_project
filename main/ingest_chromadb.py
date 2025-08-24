#!/usr/bin/env python3
"""
Document Ingestion Script for ChromaDB

This script ingests regulatory documents into ChromaDB for RAG functionality.
"""

import os
import sys
from pathlib import Path
from typing import List

import chromadb
from chromadb.config import Settings
from llama_index.core import Document, SimpleDirectoryReader
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.embeddings.openai import OpenAIEmbedding


def ingest_documents(doc_paths: List[str], collection_name: str = "pharmaceutical_regulations"):
    """
    Ingest documents into ChromaDB for RAG.
    
    Args:
        doc_paths: List of document paths to ingest
        collection_name: Name of the ChromaDB collection
    """
    print(f"Starting document ingestion for {len(doc_paths)} documents...")
    
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY not found in environment")
        print("Please set the API key before running ingestion")
        sys.exit(1)
    
    # Initialize ChromaDB client
    print(f"Initializing ChromaDB client...")
    chroma_client = chromadb.PersistentClient(
        path="./chroma_db",
        settings=Settings(anonymized_telemetry=False)
    )
    
    # Create or get collection
    try:
        collection = chroma_client.create_collection(
            name=collection_name,
            metadata={"description": "Pharmaceutical regulatory documents for GAMP-5 compliance"}
        )
        print(f"Created new collection: {collection_name}")
    except Exception:
        # Collection already exists, delete and recreate for fresh ingestion
        chroma_client.delete_collection(collection_name)
        collection = chroma_client.create_collection(
            name=collection_name,
            metadata={"description": "Pharmaceutical regulatory documents for GAMP-5 compliance"}
        )
        print(f"Recreated collection: {collection_name}")
    
    # Initialize embedding model
    print("Initializing OpenAI embedding model...")
    embed_model = OpenAIEmbedding(
        model="text-embedding-3-small",
        embed_batch_size=10
    )
    
    # Process each document
    total_chunks = 0
    for doc_path in doc_paths:
        if not Path(doc_path).exists():
            print(f"Warning: Document not found: {doc_path}")
            continue
        
        print(f"\nProcessing: {Path(doc_path).name}")
        
        # Read document content
        with open(doc_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Create Document object
        doc = Document(
            text=content,
            metadata={
                "filename": Path(doc_path).name,
                "filepath": str(doc_path),
                "document_type": "regulatory_standard"
            }
        )
        
        # Parse into chunks
        parser = SimpleNodeParser.from_defaults(
            chunk_size=1500,
            chunk_overlap=200
        )
        nodes = parser.get_nodes_from_documents([doc])
        print(f"  Created {len(nodes)} chunks")
        
        # Generate embeddings and store
        for i, node in enumerate(nodes):
            # Generate embedding
            embedding = embed_model.get_text_embedding(node.text)
            
            # Store in ChromaDB
            collection.add(
                ids=[f"{Path(doc_path).stem}_chunk_{i}"],
                embeddings=[embedding],
                documents=[node.text],
                metadatas=[{
                    "source": Path(doc_path).name,
                    "chunk_index": i,
                    "total_chunks": len(nodes)
                }]
            )
        
        total_chunks += len(nodes)
        print(f"  Stored {len(nodes)} chunks in ChromaDB")
    
    print(f"\n✅ Ingestion complete!")
    print(f"Total documents: {len(doc_paths)}")
    print(f"Total chunks: {total_chunks}")
    print(f"Collection: {collection_name}")
    
    # Verify collection
    result = collection.peek(1)
    if result['ids']:
        print(f"✅ Verification successful - collection contains data")
    else:
        print(f"⚠️ Warning: Collection appears to be empty")


if __name__ == "__main__":
    # Define documents to ingest
    base_path = Path(__file__).parent / "tests" / "test_data"
    
    documents = [
        str(base_path / "FDA Part-11--Electronic-Records--Electronic-Signatures---Scope-and-Application-(PDF).md"),
        str(base_path / "ISPE - GAMP 5_ A Risk-Based Approach to Compliant GxP Computerized_short.md"),
    ]
    
    # Additional documents if they exist
    optional_docs = [
        str(base_path / "ISPE Baseline® Guide Commissioning and Qualification_short.md"),
        str(base_path / "gamp5_test_data" / "testing_data.md"),
    ]
    
    for doc in optional_docs:
        if Path(doc).exists():
            documents.append(doc)
    
    print("Documents to ingest:")
    for doc in documents:
        print(f"  - {Path(doc).name}")
    
    # Run ingestion
    ingest_documents(documents)