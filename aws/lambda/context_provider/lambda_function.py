"""
Context Provider Lambda Function
Retrieves regulatory context from ChromaDB for OQ test generation
"""
import json
import os
import tarfile
import boto3
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any

# Configuration
S3_BUCKET = os.environ.get('S3_BUCKET', 'pharma-vectors-eu')
S3_KEY = os.environ.get('S3_KEY', 'chroma_db.tar.gz')
CHROMA_PATH = '/tmp/chroma_db'
COLLECTION_NAME = 'regulatory_docs'

# AWS clients
s3 = boto3.client('s3')

# Global cache
_chroma_client = None
_collection = None


def download_and_extract_chroma():
    """Download ChromaDB from S3 and extract to /tmp/"""
    if os.path.exists(CHROMA_PATH):
        print("✅ ChromaDB already exists in /tmp/")
        return
    
    print(f"📥 Downloading ChromaDB from s3://{S3_BUCKET}/{S3_KEY}...")
    tarball_path = '/tmp/chroma_db.tar.gz'
    
    s3.download_file(S3_BUCKET, S3_KEY, tarball_path)
    print(f"✅ Downloaded {os.path.getsize(tarball_path) / (1024*1024):.2f} MB")
    
    print("📦 Extracting...")
    with tarfile.open(tarball_path, 'r:gz') as tar:
        tar.extractall('/tmp/')
    
    os.remove(tarball_path)
    print("✅ ChromaDB ready")


def get_chroma_collection():
    """Initialize ChromaDB client and collection (cached)"""
    global _chroma_client, _collection
    
    if _chroma_client is None:
        download_and_extract_chroma()
        
        print("🔧 Initializing ChromaDB client...")
        _chroma_client = chromadb.PersistentClient(
            path=CHROMA_PATH,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=False,
                is_persistent=True
            )
        )
        
        _collection = _chroma_client.get_collection(COLLECTION_NAME)
        print(f"✅ Collection '{COLLECTION_NAME}' loaded ({_collection.count()} documents)")
    
    return _collection


def query_context(
    query_embedding: List[float],
    n_results: int = 5,
    where: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Query ChromaDB for relevant regulatory context"""
    collection = get_chroma_collection()
    
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where=where,
        include=['documents', 'metadatas', 'distances']
    )
    
    return {
        'documents': results['documents'][0],
        'metadatas': results['metadatas'][0],
        'distances': results['distances'][0]
    }


def lambda_handler(event, context):
    """
    Lambda handler for context retrieval
    
    Event format:
    {
        "embedding": [0.1, 0.2, ...],  # 1536 dimensions
        "n_results": 5,                 # Optional
        "filter": {"category": "GAMP-5"}  # Optional metadata filter
    }
    """
    try:
        # Handle EventBridge warm-up
        if event.get('source') == 'aws.events':
            print("🔥 Warm-up invocation")
            get_chroma_collection()  # Pre-load ChromaDB
            return {
                'statusCode': 200,
                'body': json.dumps({'status': 'warmed'})
            }
        
        # Validate input
        if 'embedding' not in event:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing embedding field'})
            }
        
        embedding = event['embedding']
        n_results = event.get('n_results', 5)
        where_filter = event.get('filter')
        
        # Query ChromaDB
        print(f"🔍 Querying for {n_results} results...")
        results = query_context(embedding, n_results, where_filter)
        
        print(f"✅ Found {len(results['documents'])} documents")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'results': results,
                'count': len(results['documents'])
            })
        }
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'type': type(e).__name__
            })
        }
