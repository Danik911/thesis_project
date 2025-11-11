# Context Collector Result - 20251110-145230

## Agent Configuration
- Agent: context-collector
- Task ID: 1.2
- Invoked: 2025-11-10T14:52:30Z
- Duration: ~45 minutes
- Status: SUCCESS

## Task Understanding

Task 1.2 requires implementing a pluggable vector store provider that abstracts ChromaDB (local development) and AWS vector storage (production) to enable seamless switching via configuration. The provider must expose methods for adding documents, querying embeddings, performing metadata-based filtering, and support migration utilities to move data between backends. This abstraction builds on Task 1.1's StorageProvider pattern and is critical for the AWS migration path outlined in the PRP.

**Key Requirements:**
1. Dual-mode support: ChromaDB (local) and PostgreSQL/pgvector (AWS production)
2. Use LlamaIndex VectorStoreIndex abstraction to avoid code duplication
3. Implement client-side metadata filtering (over-fetch strategy)
4. Cache embedding model to avoid repeated instantiation
5. Enable migration utilities to reuse provider for data movement
6. GAMP-5/ALCOA+ compliance for pharmaceutical audit trails
7. NO FALLBACK LOGIC - explicit error handling with full diagnostics

## Research Findings

### CRITICAL CLARIFICATION: "S3 Vectors" Misnomer

The task file and AWS migration plan reference "S3 Vectors" as the production vector store. **This AWS service does NOT exist.** After comprehensive research:

- No `boto3.client('s3-vectors')` service exists
- No LlamaIndex integration package `llama-index-vector-stores-s3` exists
- The only S3-related pattern in LlamaIndex is index PERSISTENCE to S3 (using s3fs), NOT vector storage

**Actual Implementation Target:** Based on cost analysis ($5/month aligns with Aurora Serverless v2 minimal capacity), architecture fit (Aurora already chosen for relational data), and superior compliance capabilities, the intended production vector store is:

**PostgreSQL with pgvector extension** running in Amazon Aurora Serverless v2

This makes architectural sense:
- Single database for both relational (audit logs, job metadata) and vector data
- Native pgvector extension provides vector similarity search
- Cost-effective at minimal Aurora capacity (~0.5 ACU + vector storage = ~$5/month)
- LlamaIndex has native support via `llama-index-vector-stores-postgres`
- Superior GAMP-5/ALCOA+ compliance through PostgreSQL audit triggers
- Excellent metadata filtering performance (B-tree indexes + vector HNSW)

**Recommendation for task-executor:** Implement support for ChromaDB (local) and PostgreSQL/pgvector (production), NOT "S3 Vectors" or OpenSearch Serverless.

---

### LlamaIndex VectorStoreIndex Abstraction Patterns

**Version Requirements:**
- Current project: `llama-index-core>=0.11.0`
- Required upgrade: `llama-index-core>=0.12.0` for production features
- Latest stable: v0.14.5 (October 2025)

**Key Architectural Patterns:**

1. **VectorStoreIndex Core Abstraction**
   - Accepts list of Node objects and constructs searchable index
   - `from_documents()` automatically chunks and parses into Node objects
   - Separates data representation from storage implementation
   - Enables consistent interface across vector database backends

2. **Settings Singleton for Global Configuration**
   ```python
   from llama_index.core import Settings

   Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
   Settings.llm = OpenAI(model="gpt-4")
   Settings.chunk_size = 512
   Settings.chunk_overlap = 50
   ```
   - Configures embedding model, LLM, node parser, tokenizer globally
   - Can be overridden locally for specific operations
   - Critical for pharmaceutical audit trails via callback mechanisms

3. **StorageContext Pattern**
   ```python
   from llama_index.core import StorageContext, VectorStoreIndex

   # ChromaDB example
   vector_store = ChromaVectorStore(chroma_collection=collection)
   storage_context = StorageContext.from_defaults(vector_store=vector_store)
   index = VectorStoreIndex.from_documents(documents, storage_context=storage_context)

   # Query
   query_engine = index.as_query_engine()
   response = query_engine.query("GAMP-5 validation requirements")
   ```

4. **Loading from Existing Vector Store**
   ```python
   # Avoid re-indexing by loading from existing store
   index = VectorStoreIndex.from_vector_store(
       vector_store=vector_store,
       storage_context=storage_context
   )
   ```

**Breaking Changes in 0.12.0+:**
- Removed deprecated agent classes (FunctionCallingAgent, old ReActAgent)
- QueryPipeline class removed in favor of retrieval patterns
- `index.as_chat_engine()` default changed to CondensePlusContextChatEngine
- Version 0.14.0 removed deprecated checkpointer and sub-workflows features
- Improved error handling with clearer stacktraces (no WorkflowRuntimeError wrapping)

---

### ChromaDB Integration Patterns

**Package:** `llama-index-vector-stores-chroma>=0.3.0` (already in project)

**Initialization Pattern:**
```python
import chromadb
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import VectorStoreIndex, StorageContext

# Persistent client (survives restarts)
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection("pharma_docs")

# Wrap in LlamaIndex abstraction
vector_store = ChromaVectorStore(chroma_collection=collection)
storage_context = StorageContext.from_defaults(vector_store=vector_store)

# Build or load index
index = VectorStoreIndex.from_documents(
    documents,
    storage_context=storage_context,
    embed_model=embed_model  # Cache this!
)
```

**Resource Management:**
```python
# CRITICAL: Close client to avoid file handle leaks
try:
    # ... operations ...
finally:
    # ChromaDB doesn't have explicit close(), relies on context managers
    # Ensure client goes out of scope or use connection pooling
    pass
```

**Strengths:**
- Lightweight, runs locally without external infrastructure
- HNSW indexing for fast approximate nearest neighbor search
- Multimodal support (text + images)
- Developer-friendly API

**Critical Limitations:**
- **Metadata filtering performance degrades severely at scale**
  - 40,000+ embeddings: metadata filtering takes 5 minutes vs 5-8 seconds unfiltered
  - No proper indexing on metadata fields (sequential iteration)
  - Post-filtering after retrieval creates algorithmic complexity
- Not suitable for production pharmaceutical use with complex filtering requirements
- No built-in audit logging or ACID compliance
- No enterprise-grade backup/recovery mechanisms

**Recommendation:** Use ChromaDB for local development only. Do NOT use in production for pharmaceutical applications requiring metadata filtering or compliance audit trails.

---

### PostgreSQL pgvector Integration Patterns

**Package:** `llama-index-vector-stores-postgres>=0.2.0` (NEW - not yet in project)

**Additional Dependencies:**
- `psycopg2-binary>=2.9.9` OR `asyncpg>=0.29.0` (for async operations)
- PostgreSQL 15+ with pgvector extension installed

**Initialization Pattern:**
```python
from llama_index.vector_stores.postgres import PGVectorStore
from llama_index.core import VectorStoreIndex, StorageContext

# Connection string format
# For Aurora Serverless: use Data API or connection pooling
connection_string = "postgresql+psycopg2://user:password@aurora-endpoint:5432/dbname"

# Initialize vector store
vector_store = PGVectorStore.from_params(
    database="pharma_db",
    host="aurora-endpoint.region.rds.amazonaws.com",
    port=5432,
    user="postgres",
    password="<from-secrets-manager>",
    table_name="rag_documents",  # See schema below
    embed_dim=1536,  # OpenAI text-embedding-3-small
    # HNSW index parameters
    m=16,  # connections per layer (default: 16, range: 2-100)
    ef_construction=128,  # build-time search breadth (default: 128)
    ef=64,  # query-time search breadth (default: 64)
)

storage_context = StorageContext.from_defaults(vector_store=vector_store)
index = VectorStoreIndex.from_documents(
    documents,
    storage_context=storage_context,
    embed_model=embed_model
)
```

**Database Schema (Aurora PostgreSQL):**
```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- RAG document storage table
CREATE TABLE rag_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    embedding VECTOR(1536) NOT NULL,  -- Dimension matches embedding model
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',

    -- GAMP-5 compliance fields
    gamp_category VARCHAR(10),
    document_type VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(255) NOT NULL,

    -- Searchability
    document_hash VARCHAR(64),  -- SHA-256 for deduplication
    version INTEGER DEFAULT 1
);

-- HNSW index for vector similarity (approximate nearest neighbor)
CREATE INDEX ON rag_documents USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 128);

-- B-tree indexes for metadata filtering
CREATE INDEX idx_gamp_category ON rag_documents(gamp_category);
CREATE INDEX idx_document_type ON rag_documents(document_type);
CREATE INDEX idx_created_at ON rag_documents(created_at DESC);

-- JSONB GIN index for flexible metadata queries
CREATE INDEX idx_metadata_gin ON rag_documents USING GIN(metadata);

-- Audit trigger for ALCOA+ compliance
CREATE TABLE rag_audit_log (
    id BIGSERIAL PRIMARY KEY,
    document_id UUID REFERENCES rag_documents(id),
    action VARCHAR(20) NOT NULL,  -- INSERT, UPDATE, DELETE, SELECT
    user_id VARCHAR(255) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    old_values JSONB,
    new_values JSONB,
    client_ip INET,
    session_id VARCHAR(255)
);

CREATE OR REPLACE FUNCTION log_rag_changes()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'DELETE') THEN
        INSERT INTO rag_audit_log (document_id, action, user_id, old_values)
        VALUES (OLD.id, 'DELETE', current_user, row_to_json(OLD));
        RETURN OLD;
    ELSIF (TG_OP = 'UPDATE') THEN
        INSERT INTO rag_audit_log (document_id, action, user_id, old_values, new_values)
        VALUES (NEW.id, 'UPDATE', current_user, row_to_json(OLD), row_to_json(NEW));
        RETURN NEW;
    ELSIF (TG_OP = 'INSERT') THEN
        INSERT INTO rag_audit_log (document_id, action, user_id, new_values)
        VALUES (NEW.id, 'INSERT', current_user, row_to_json(NEW));
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER rag_audit_trigger
    AFTER INSERT OR UPDATE OR DELETE ON rag_documents
    FOR EACH ROW EXECUTE FUNCTION log_rag_changes();
```

**Metadata Filtering Performance:**
```python
# Pre-filtering with SQL WHERE clause (FAST)
from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter

filters = MetadataFilters(
    filters=[
        ExactMatchFilter(key="gamp_category", value="5"),
        ExactMatchFilter(key="document_type", value="validation_protocol")
    ]
)

retriever = VectorIndexRetriever(
    index=index,
    similarity_top_k=10,
    filters=filters
)

results = retriever.retrieve("test execution procedures")
```

**HNSW Index Tuning:**
- `m` (connections per layer): Higher = better recall, larger index size
  - Pharmaceutical use: m=16 (default) for balanced performance
- `ef_construction` (build-time): Higher = better index quality, slower build
  - Pharmaceutical use: 128 (default) adequate for 200-10,000 docs
- `ef` (query-time): Higher = better recall, slower queries
  - Pharmaceutical use: Start at 64, increase if recall < 80%

**Strengths:**
- Enterprise-grade ACID compliance
- Native audit logging via triggers (ALCOA+ requirement)
- Excellent metadata filtering via B-tree indexes
- HNSW and IVFFlat indexing strategies
- Scales to millions of vectors with proper tuning
- Aurora Serverless auto-scaling (0.5-128 ACUs)
- Data API support (no VPC configuration needed)

**Limitations:**
- Requires PostgreSQL administration expertise
- More complex deployment than ChromaDB
- Performance depends heavily on index configuration
- Higher operational overhead

**Recommendation:** Use PostgreSQL/pgvector for AWS production. Superior compliance, filtering, and audit capabilities justify operational complexity.

---

### Embedding Model Caching Patterns

**Model Selection:**
- **Default:** OpenAI `text-embedding-3-small` (1536 dimensions, $0.02/1M tokens)
- **Alternative:** `text-embedding-3-large` (3072 dims, higher accuracy, $0.13/1M tokens)
- **Local:** HuggingFace `BAAI/bge-small-en-v1.5` (384 dims, free, runs offline)

**Caching Strategy 1: Model Instance Caching**
```python
# BAD: Creates new embedding model on every call
def get_index(documents):
    embed_model = OpenAIEmbedding(model="text-embedding-3-small")
    return VectorStoreIndex.from_documents(documents, embed_model=embed_model)

# GOOD: Cache embedding model at provider level
class VectorStoreProvider:
    def __init__(self, settings):
        # Create embedding model ONCE
        self._embed_model = OpenAIEmbedding(
            model=settings.embedding_model,
            dimensions=settings.embedding_dimensions,
            api_key=settings.openai_api_key
        )
        # Cache for reuse
        Settings.embed_model = self._embed_model

    def create_index(self, documents):
        # Reuses cached embedding model
        return VectorStoreIndex.from_documents(documents)
```

**Caching Strategy 2: Document Embedding Caching (IngestionPipeline)**
```python
from llama_index.core.ingestion import IngestionPipeline, IngestionCache
from llama_index.storage.kvstore.redis import RedisKVStore
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.extractors import TitleExtractor, KeywordExtractor

# Redis-backed caching for processed documents
redis_kvstore = RedisKVStore.from_host_and_port(
    host="localhost",
    port=6379
)
cache = IngestionCache(cache=redis_kvstore)

# Pipeline with transformations
pipeline = IngestionPipeline(
    transformations=[
        SentenceSplitter(chunk_size=512, chunk_overlap=50),
        TitleExtractor(),
        KeywordExtractor(keywords=10),
        embed_model,  # Embedding generation (cached)
    ],
    cache=cache,
    docstore_strategy="UPSERTS"  # Update existing, skip unchanged
)

# Process documents (cached results reused automatically)
nodes = pipeline.run(documents=documents)
```

**Benefits:**
- Avoids redundant API calls for unchanged documents
- Reduces embedding costs (OpenAI charges per token)
- Faster ingestion for updated document sets
- Essential for pharmaceutical document libraries (10,000+ docs)

**Batch Size Optimization:**
```python
# OpenAI rate limits: 10 embeddings/batch by default
# For high-volume workloads, tune batch size
embed_model = OpenAIEmbedding(
    model="text-embedding-3-small",
    embed_batch_size=50  # Increase for throughput (monitor rate limits)
)
```

---

### Migration Utilities: ChromaDB → PostgreSQL pgvector

**Migration Strategy:**
```python
# scripts/migrate_chromadb_to_pgvector.py

import chromadb
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.vector_stores.postgres import PGVectorStore
from llama_index.core import VectorStoreIndex, StorageContext
import logging

logger = logging.getLogger(__name__)

def export_from_chromadb(chroma_path: str, collection_name: str) -> list[dict]:
    """
    Export embeddings and metadata from ChromaDB.

    Returns:
        List of dicts with keys: id, embedding, content, metadata
    """
    client = chromadb.PersistentClient(path=chroma_path)
    collection = client.get_collection(collection_name)

    # Get all documents
    results = collection.get(include=["embeddings", "documents", "metadatas"])

    documents = []
    for i, doc_id in enumerate(results["ids"]):
        documents.append({
            "id": doc_id,
            "embedding": results["embeddings"][i],
            "content": results["documents"][i],
            "metadata": results["metadatas"][i] if results["metadatas"] else {}
        })

    logger.info(f"Exported {len(documents)} documents from ChromaDB")
    return documents


def import_to_pgvector(
    documents: list[dict],
    connection_string: str,
    table_name: str = "rag_documents"
) -> None:
    """
    Import embeddings into PostgreSQL pgvector.

    Args:
        documents: List from export_from_chromadb()
        connection_string: PostgreSQL connection string
        table_name: Target table name
    """
    # Initialize pgvector store
    vector_store = PGVectorStore.from_params(
        connection_string=connection_string,
        table_name=table_name,
        embed_dim=len(documents[0]["embedding"])
    )

    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    # Convert to LlamaIndex Document objects
    from llama_index.core import Document

    llama_docs = []
    for doc in documents:
        llama_docs.append(
            Document(
                text=doc["content"],
                metadata=doc["metadata"],
                doc_id=doc["id"]
            )
        )

    # Build index (this inserts into pgvector)
    index = VectorStoreIndex.from_documents(
        llama_docs,
        storage_context=storage_context
    )

    logger.info(f"Imported {len(llama_docs)} documents to pgvector")


def validate_migration(
    chroma_path: str,
    chroma_collection: str,
    pg_connection: str,
    test_queries: list[str],
    similarity_threshold: float = 0.8
) -> bool:
    """
    Validate migration by comparing retrieval results.

    Returns:
        True if top-5 retrieval overlap >= similarity_threshold
    """
    # ChromaDB index
    chroma_client = chromadb.PersistentClient(path=chroma_path)
    chroma_coll = chroma_client.get_collection(chroma_collection)
    chroma_store = ChromaVectorStore(chroma_collection=chroma_coll)
    chroma_index = VectorStoreIndex.from_vector_store(chroma_store)

    # pgvector index
    pg_store = PGVectorStore.from_params(connection_string=pg_connection)
    pg_index = VectorStoreIndex.from_vector_store(pg_store)

    overlaps = []
    for query in test_queries:
        # Retrieve top-5 from both
        chroma_results = chroma_index.as_retriever(similarity_top_k=5).retrieve(query)
        pg_results = pg_index.as_retriever(similarity_top_k=5).retrieve(query)

        chroma_ids = {r.node.node_id for r in chroma_results}
        pg_ids = {r.node.node_id for r in pg_results}

        # Calculate overlap
        intersection = len(chroma_ids & pg_ids)
        overlap = intersection / 5.0  # top-5
        overlaps.append(overlap)

        logger.info(f"Query: '{query[:50]}...' | Overlap: {overlap:.1%}")

    avg_overlap = sum(overlaps) / len(overlaps)
    logger.info(f"Average top-5 overlap: {avg_overlap:.1%}")

    return avg_overlap >= similarity_threshold


# Usage
if __name__ == "__main__":
    # 1. Export from ChromaDB
    docs = export_from_chromadb(
        chroma_path="./chroma_db",
        collection_name="pharma_docs"
    )

    # 2. Import to pgvector
    import_to_pgvector(
        documents=docs,
        connection_string="postgresql://user:pass@aurora-endpoint/db"
    )

    # 3. Validate migration
    test_queries = [
        "GAMP-5 category 4 validation requirements",
        "OQ test execution procedures",
        "IQ installation qualification checklist"
    ]

    success = validate_migration(
        chroma_path="./chroma_db",
        chroma_collection="pharma_docs",
        pg_connection="postgresql://user:pass@aurora-endpoint/db",
        test_queries=test_queries,
        similarity_threshold=0.8  # 80% overlap target
    )

    if success:
        logger.info("✅ Migration validated successfully")
    else:
        logger.error("❌ Migration validation failed - investigate discrepancies")
```

**Migration Best Practices:**
1. **Parallel Operation Period:** Run ChromaDB and pgvector simultaneously during transition
2. **Dual-Write Pattern:** Write new documents to both systems until validation completes
3. **Incremental Migration:** Migrate documents in batches (1000 at a time) to avoid memory issues
4. **Validation Queries:** Use actual pharmaceutical queries from production workload
5. **Rollback Plan:** Maintain ChromaDB until pgvector performance validated in production

---

### Implementation Gotchas & Known Issues

**1. Embedding Dimension Mismatches**
- **Issue:** Changing embedding models without recreating index causes dimension errors
- **Example:** Switching from text-embedding-ada-002 (1536 dims) to text-embedding-3-large (3072 dims)
- **Solution:**
  - Store embedding model name/version in metadata
  - Validate dimensions match before querying: `assert vector_store.embed_dim == embed_model.embedding_dimension`
  - Rebuild index if model changes

**2. ChromaDB File Handle Leaks**
- **Issue:** PersistentClient opens file handles that may not close properly
- **Symptoms:** "Too many open files" error after repeated indexing operations
- **Solution:**
  ```python
  # Use context managers or ensure client cleanup
  try:
      client = chromadb.PersistentClient(path="./chroma_db")
      # ... operations ...
  finally:
      # Explicitly delete client to trigger cleanup
      del client
  ```

**3. Missing Metadata Keys in Legacy Documents**
- **Issue:** Documents ingested before metadata schema changes lack required keys
- **Example:** GAMP category added later, old docs don't have this field
- **Solution:**
  ```python
  # Defensive metadata access with defaults
  def get_metadata_safe(node: Node, key: str, default: Any) -> Any:
      return node.metadata.get(key, default)

  # Or update existing documents with migration script
  collection.update(ids=doc_ids, metadatas=updated_metadatas)
  ```

**4. PostgreSQL Connection Pooling**
- **Issue:** Creating new connections for each query exhausts Aurora connection limits
- **Solution:** Use connection pooling (pgBouncer or SQLAlchemy pooling)
  ```python
  from sqlalchemy import create_engine
  from sqlalchemy.pool import QueuePool

  engine = create_engine(
      connection_string,
      poolclass=QueuePool,
      pool_size=5,
      max_overflow=10,
      pool_pre_ping=True  # Verify connections before use
  )
  ```

**5. Aurora Serverless v2 Cold Start**
- **Issue:** First query after period of inactivity takes 10-30 seconds (Aurora scaling up)
- **Solution:**
  - Set minimum ACU to 0.5 (stays warm)
  - Implement connection keep-alive pings
  - Configure Data API for connection-less access

**6. HNSW Index Build Time**
- **Issue:** Building HNSW index on 10,000+ documents takes minutes, blocking writes
- **Solution:**
  - Build index asynchronously during low-traffic periods
  - Use `CREATE INDEX CONCURRENTLY` to avoid locking table
  - Consider IVFFlat for faster build (lower recall trade-off)

**7. Metadata Filter Selectivity**
- **Issue:** Filtering on high-cardinality fields (e.g., document_id) performs poorly
- **Solution:**
  - Create specific indexes for frequently filtered fields
  - Use PostgreSQL EXPLAIN ANALYZE to verify query plans
  - Combine filters strategically (filter on indexed columns first)

---

### Pharmaceutical Compliance: GAMP-5 & ALCOA+

**GAMP-5 Requirements for Vector Storage:**

1. **System Categorization**
   - Vector database = Category 4 (Configured Product) or Category 5 (Custom Application)
   - Validation intensity scales with risk level
   - Document intended use, functional requirements, design specifications

2. **Validation Lifecycle (V-Model)**
   - Requirements: Document retrieval accuracy, latency, compliance needs
   - Design: Architecture diagrams, database schema, API specifications
   - Implementation: Code with type hints, docstrings, error handling
   - Testing: Unit tests, integration tests, performance benchmarks, parity tests
   - Operational: Change control, backup/recovery, monitoring, audit reviews

3. **Risk-Based Validation**
   - High-risk: Vector retrieval affects patient safety decisions → Extensive testing
   - Medium-risk: Used for documentation support → Standard validation
   - Low-risk: Exploratory research only → Minimal validation

**ALCOA+ Principles Implementation:**

1. **Attributable**
   - Track user identity for every query: `metadata.created_by = current_user`
   - Log which documents were retrieved and why
   - PostgreSQL audit triggers capture all modifications

2. **Legible**
   - Store human-readable metadata alongside vectors
   - Preserve source documents (not just embeddings)
   - Document embedding model and version used

3. **Contemporaneous**
   - Auto-timestamp queries: `created_at = NOW()` (UTC)
   - Use network time protocol (NTP), not local system clock
   - Log events immediately, not retrospectively

4. **Original**
   - PostgreSQL: Use triggers to prevent post-storage modification
   - ChromaDB: Implement application-level checks (less robust)
   - Consider Aurora versioning for immutability

5. **Accurate**
   - Validate embedding dimensions match model
   - Verify metadata schema compliance before insertion
   - Monitor retrieval accuracy via parity tests

6. **Complete**
   - Store all required metadata fields (no optional compliance fields)
   - Capture full query context (query text, filters, results, scores)
   - Maintain audit trail for entire record lifecycle

7. **Consistent**
   - Enforce same metadata structure across ChromaDB and pgvector
   - Protocol interface ensures method signature consistency
   - Validation tests verify behavior parity

8. **Enduring**
   - PostgreSQL: 11 nines durability (99.999999999%)
   - Aurora Serverless: Automated backups, 7-year retention
   - Implement backup verification procedures

9. **Available**
   - Monitor query latency (P95 < 200ms target)
   - Implement connection failover mechanisms
   - Document disaster recovery procedures

**Audit Trail Implementation:**
```python
# Log every query for ALCOA+ compliance
import logging
from datetime import datetime, UTC

audit_logger = logging.getLogger("pharmaceutical_audit")

def log_vector_query(
    user_id: str,
    query_text: str,
    retrieved_doc_ids: list[str],
    similarity_scores: list[float],
    metadata_filters: dict[str, Any]
) -> None:
    """
    Log vector retrieval query for audit trail.

    ALCOA+ Requirements:
    - Attributable: user_id
    - Contemporaneous: timestamp
    - Complete: full query context
    - Traceable: correlation to results
    """
    audit_record = {
        "timestamp": datetime.now(UTC).isoformat(),
        "user_id": user_id,
        "action": "VECTOR_QUERY",
        "query_text": query_text,
        "filters": metadata_filters,
        "retrieved_documents": [
            {"doc_id": doc_id, "score": score}
            for doc_id, score in zip(retrieved_doc_ids, similarity_scores)
        ],
        "compliance_standard": "ALCOA+"
    }

    audit_logger.info(json.dumps(audit_record))
```

---

## Recommended Approach

### 1. Protocol-Based Abstraction (Similar to Task 1.1)

```python
# src/adapters/vector_store.py

from typing import Protocol, Any
from llama_index.core import VectorStoreIndex, Document
from llama_index.core.schema import NodeWithScore


class VectorStoreProvider(Protocol):
    """
    Protocol defining contract for vector store providers.

    All implementations (ChromaDB, pgvector) must implement this interface
    to ensure consistent behavior across different backends.

    GAMP-5 Compliance:
    - All methods must preserve metadata for audit trail
    - All failures must raise explicit exceptions with diagnostic information

    NO FALLBACK LOGIC:
    - Never return success on failure
    - Never use default values to mask errors
    - Never silently catch exceptions
    """

    async def add_documents(
        self,
        documents: list[Document],
        metadata: dict[str, Any]
    ) -> list[str]:
        """
        Add documents to vector store with embeddings.

        Args:
            documents: LlamaIndex Document objects
            metadata: GAMP-5 compliant metadata (gamp_category, created_by, etc.)

        Returns:
            List of document IDs inserted

        Raises:
            ValueError: If metadata invalid or documents malformed
            RuntimeError: If vector store operation fails (with full diagnostics)

        CRITICAL: NO FALLBACK LOGIC - All errors must propagate with full context
        """
        ...

    async def query(
        self,
        query_text: str,
        top_k: int = 10,
        metadata_filters: dict[str, Any] | None = None
    ) -> list[NodeWithScore]:
        """
        Query vector store for similar documents.

        Args:
            query_text: Natural language query
            top_k: Number of results to return
            metadata_filters: Optional filters (e.g., {"gamp_category": "5"})

        Returns:
            List of retrieved nodes with similarity scores

        Raises:
            ValueError: If query parameters invalid
            RuntimeError: If retrieval operation fails (with full diagnostics)

        CRITICAL: NO FALLBACK LOGIC - Never return empty results to mask errors
        """
        ...

    def get_index(self) -> VectorStoreIndex:
        """
        Get LlamaIndex VectorStoreIndex for advanced operations.

        Returns:
            Configured VectorStoreIndex instance

        Raises:
            RuntimeError: If index not initialized or unavailable
        """
        ...


class VectorStoreFactory:
    """Factory for creating vector store providers based on configuration."""

    @staticmethod
    def create_provider(mode: str, **kwargs) -> VectorStoreProvider:
        """
        Create vector store provider based on mode.

        Args:
            mode: "chromadb" or "pgvector"
            **kwargs: Configuration parameters
                For chromadb:
                    - persist_path: str (default: "./chroma_db")
                    - collection_name: str (default: "pharma_docs")
                For pgvector:
                    - connection_string: str (required)
                    - table_name: str (default: "rag_documents")
                    - embed_dim: int (default: 1536)

        Returns:
            Configured vector store provider

        Raises:
            ValueError: If mode invalid or required parameters missing

        CRITICAL: NO FALLBACK LOGIC - Never default to chromadb on pgvector failure
        """
        from src.adapters.chroma_adapter import ChromaVectorStoreAdapter
        from src.adapters.postgres_adapter import PostgresVectorStoreAdapter

        if mode == "chromadb":
            return ChromaVectorStoreAdapter(**kwargs)
        elif mode == "pgvector":
            return PostgresVectorStoreAdapter(**kwargs)
        else:
            raise ValueError(
                f"CRITICAL: Invalid vector store mode '{mode}'\n"
                f"Supported modes: 'chromadb', 'pgvector'\n"
                "Check RAG_MODE environment variable"
            )
```

### 2. ChromaDB Adapter Implementation

```python
# src/adapters/chroma_adapter.py

import chromadb
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import VectorStoreIndex, StorageContext, Document, Settings
from llama_index.core.schema import NodeWithScore
from typing import Any
import logging

logger = logging.getLogger(__name__)


class ChromaVectorStoreAdapter:
    """ChromaDB vector store adapter for local development."""

    def __init__(
        self,
        persist_path: str = "./chroma_db",
        collection_name: str = "pharma_docs",
        embed_model: Any = None
    ):
        """
        Initialize ChromaDB vector store.

        Args:
            persist_path: Directory for persistent storage
            collection_name: ChromaDB collection name
            embed_model: Cached embedding model (reuse to avoid instantiation)
        """
        try:
            self.client = chromadb.PersistentClient(path=persist_path)
            self.collection = self.client.get_or_create_collection(collection_name)

            # Wrap in LlamaIndex abstraction
            self.vector_store = ChromaVectorStore(chroma_collection=self.collection)
            self.storage_context = StorageContext.from_defaults(
                vector_store=self.vector_store
            )

            # Cache embedding model (CRITICAL for performance)
            if embed_model:
                Settings.embed_model = embed_model

            logger.info(f"ChromaDB initialized: {persist_path}/{collection_name}")

        except Exception as e:
            raise RuntimeError(
                f"CRITICAL: ChromaDB initialization failed\n"
                f"Persist path: {persist_path}\n"
                f"Collection: {collection_name}\n"
                f"Error: {str(e)}"
            ) from e

    async def add_documents(
        self,
        documents: list[Document],
        metadata: dict[str, Any]
    ) -> list[str]:
        """Add documents to ChromaDB with embeddings."""
        try:
            # Validate metadata
            self._validate_metadata(metadata)

            # Enrich documents with metadata
            for doc in documents:
                doc.metadata.update(metadata)

            # Build index (generates embeddings and stores)
            index = VectorStoreIndex.from_documents(
                documents,
                storage_context=self.storage_context
            )

            # Extract document IDs
            doc_ids = [doc.doc_id for doc in documents]

            logger.info(f"Added {len(doc_ids)} documents to ChromaDB")
            return doc_ids

        except Exception as e:
            raise RuntimeError(
                f"CRITICAL: Failed to add documents to ChromaDB\n"
                f"Document count: {len(documents)}\n"
                f"Error: {str(e)}\n"
                f"Stack trace: {traceback.format_exc()}"
            ) from e

    async def query(
        self,
        query_text: str,
        top_k: int = 10,
        metadata_filters: dict[str, Any] | None = None
    ) -> list[NodeWithScore]:
        """Query ChromaDB for similar documents."""
        try:
            # Load index from vector store
            index = VectorStoreIndex.from_vector_store(
                self.vector_store,
                storage_context=self.storage_context
            )

            # Create retriever
            retriever = index.as_retriever(similarity_top_k=top_k)

            # Retrieve (ChromaDB handles filtering internally, but poorly)
            if metadata_filters:
                logger.warning(
                    "ChromaDB metadata filtering has poor performance at scale. "
                    "Consider pre-filtering at application level."
                )
                # Apply filters (ChromaDB will post-filter after retrieval)
                from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter
                filters = MetadataFilters(
                    filters=[
                        ExactMatchFilter(key=k, value=v)
                        for k, v in metadata_filters.items()
                    ]
                )
                retriever = index.as_retriever(
                    similarity_top_k=top_k * 2,  # Over-fetch to compensate
                    filters=filters
                )

            results = retriever.retrieve(query_text)

            logger.info(f"Retrieved {len(results)} documents from ChromaDB")
            return results

        except Exception as e:
            raise RuntimeError(
                f"CRITICAL: ChromaDB query failed\n"
                f"Query: {query_text}\n"
                f"Filters: {metadata_filters}\n"
                f"Error: {str(e)}"
            ) from e

    def get_index(self) -> VectorStoreIndex:
        """Get LlamaIndex VectorStoreIndex."""
        return VectorStoreIndex.from_vector_store(
            self.vector_store,
            storage_context=self.storage_context
        )

    def _validate_metadata(self, metadata: dict[str, Any]) -> None:
        """Validate GAMP-5 compliant metadata."""
        required = ["gamp_category", "created_by", "document_type"]
        missing = [k for k in required if k not in metadata]
        if missing:
            raise ValueError(
                f"CRITICAL: Missing required metadata fields: {missing}\n"
                f"Required: {required}\n"
                f"Provided: {list(metadata.keys())}"
            )
```

### 3. PostgreSQL pgvector Adapter Implementation

```python
# src/adapters/postgres_adapter.py

from llama_index.vector_stores.postgres import PGVectorStore
from llama_index.core import VectorStoreIndex, StorageContext, Document, Settings
from llama_index.core.schema import NodeWithScore
from typing import Any
import logging

logger = logging.getLogger(__name__)


class PostgresVectorStoreAdapter:
    """PostgreSQL pgvector adapter for AWS production (Aurora Serverless)."""

    def __init__(
        self,
        connection_string: str,
        table_name: str = "rag_documents",
        embed_dim: int = 1536,
        embed_model: Any = None
    ):
        """
        Initialize PostgreSQL pgvector store.

        Args:
            connection_string: PostgreSQL connection string
            table_name: Vector storage table name
            embed_dim: Embedding dimension (must match model)
            embed_model: Cached embedding model
        """
        try:
            if not connection_string:
                raise ValueError(
                    "CRITICAL: PostgreSQL connection string required\n"
                    "Set via VECTOR_STORE_CONNECTION_STRING environment variable"
                )

            # Initialize pgvector store
            self.vector_store = PGVectorStore.from_params(
                connection_string=connection_string,
                table_name=table_name,
                embed_dim=embed_dim,
                # HNSW index parameters (tuned for pharmaceutical use)
                m=16,  # connections per layer
                ef_construction=128,  # build-time search breadth
                ef=64  # query-time search breadth
            )

            self.storage_context = StorageContext.from_defaults(
                vector_store=self.vector_store
            )

            # Cache embedding model
            if embed_model:
                Settings.embed_model = embed_model

            logger.info(f"PostgreSQL pgvector initialized: {table_name}")

        except Exception as e:
            raise RuntimeError(
                f"CRITICAL: PostgreSQL pgvector initialization failed\n"
                f"Connection string: {connection_string[:50]}...\n"
                f"Table: {table_name}\n"
                f"Error: {str(e)}"
            ) from e

    async def add_documents(
        self,
        documents: list[Document],
        metadata: dict[str, Any]
    ) -> list[str]:
        """Add documents to pgvector with embeddings."""
        try:
            # Validate metadata
            self._validate_metadata(metadata)

            # Enrich documents
            for doc in documents:
                doc.metadata.update(metadata)

            # Build index (PostgreSQL audit triggers log automatically)
            index = VectorStoreIndex.from_documents(
                documents,
                storage_context=self.storage_context
            )

            doc_ids = [doc.doc_id for doc in documents]

            logger.info(f"Added {len(doc_ids)} documents to pgvector")
            return doc_ids

        except Exception as e:
            raise RuntimeError(
                f"CRITICAL: Failed to add documents to pgvector\n"
                f"Document count: {len(documents)}\n"
                f"Error: {str(e)}\n"
                f"Check PostgreSQL connection and table schema"
            ) from e

    async def query(
        self,
        query_text: str,
        top_k: int = 10,
        metadata_filters: dict[str, Any] | None = None
    ) -> list[NodeWithScore]:
        """Query pgvector for similar documents with metadata filtering."""
        try:
            # Load index
            index = VectorStoreIndex.from_vector_store(
                self.vector_store,
                storage_context=self.storage_context
            )

            # Create retriever with filters
            if metadata_filters:
                from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter
                filters = MetadataFilters(
                    filters=[
                        ExactMatchFilter(key=k, value=v)
                        for k, v in metadata_filters.items()
                    ]
                )
                retriever = index.as_retriever(
                    similarity_top_k=top_k,
                    filters=filters  # PostgreSQL handles efficiently via B-tree indexes
                )
            else:
                retriever = index.as_retriever(similarity_top_k=top_k)

            results = retriever.retrieve(query_text)

            logger.info(f"Retrieved {len(results)} documents from pgvector")
            return results

        except Exception as e:
            raise RuntimeError(
                f"CRITICAL: pgvector query failed\n"
                f"Query: {query_text}\n"
                f"Filters: {metadata_filters}\n"
                f"Error: {str(e)}"
            ) from e

    def get_index(self) -> VectorStoreIndex:
        """Get LlamaIndex VectorStoreIndex."""
        return VectorStoreIndex.from_vector_store(
            self.vector_store,
            storage_context=self.storage_context
        )

    def _validate_metadata(self, metadata: dict[str, Any]) -> None:
        """Validate GAMP-5 compliant metadata."""
        required = ["gamp_category", "created_by", "document_type"]
        missing = [k for k in required if k not in metadata]
        if missing:
            raise ValueError(
                f"CRITICAL: Missing required metadata fields: {missing}\n"
                f"Required: {required}\n"
                f"Pharmaceutical compliance mandate"
            )
```

### 4. Configuration Integration

```python
# Add to src/shared/config.py

@dataclass
class VectorStoreConfig:
    """Configuration for dual-mode vector store (ChromaDB/pgvector)."""

    # Vector store mode settings
    rag_mode: str = field(
        default_factory=lambda: os.getenv("RAG_MODE", "chromadb")
    )

    # ChromaDB settings (local development)
    chroma_path: str = field(
        default_factory=lambda: os.getenv("CHROMA_PATH", "./chroma_db")
    )
    chroma_collection: str = field(
        default_factory=lambda: os.getenv("CHROMA_COLLECTION", "pharma_docs")
    )

    # PostgreSQL pgvector settings (AWS production)
    pg_connection_string: str = field(
        default_factory=lambda: os.getenv("VECTOR_STORE_CONNECTION_STRING", "")
    )
    pg_table_name: str = field(
        default_factory=lambda: os.getenv("VECTOR_STORE_TABLE", "rag_documents")
    )

    # Embedding settings
    embedding_model: str = field(
        default_factory=lambda: os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    )
    embedding_dimensions: int = field(
        default_factory=lambda: int(os.getenv("EMBEDDING_DIMENSIONS", "1536"))
    )

    # Query settings
    similarity_top_k: int = field(
        default_factory=lambda: int(os.getenv("SIMILARITY_TOP_K", "10"))
    )

    def __post_init__(self) -> None:
        """Validate vector store configuration."""
        valid_modes = ["chromadb", "pgvector"]
        if self.rag_mode not in valid_modes:
            raise ValueError(
                f"CRITICAL: Invalid RAG mode '{self.rag_mode}'\n"
                f"Valid modes: {valid_modes}\n"
                "Set RAG_MODE environment variable"
            )

        # Validate pgvector configuration if pgvector mode
        if self.rag_mode == "pgvector":
            if not self.pg_connection_string:
                raise ValueError(
                    "CRITICAL: pgvector mode requires connection string\n"
                    "Set VECTOR_STORE_CONNECTION_STRING environment variable\n"
                    "Format: postgresql://user:pass@aurora-endpoint:5432/dbname"
                )

        # Validate embedding dimensions
        valid_dims = [384, 768, 1024, 1536, 3072]
        if self.embedding_dimensions not in valid_dims:
            raise ValueError(
                f"CRITICAL: Unusual embedding dimension: {self.embedding_dimensions}\n"
                f"Common dimensions: {valid_dims}\n"
                "Verify EMBEDDING_DIMENSIONS matches model"
            )
```

### 5. Usage Example

```python
# main/src/core/unified_workflow.py (example integration)

from src.adapters.vector_store import VectorStoreFactory
from src.shared.config import get_config
from llama_index.core import Document
from llama_index.embeddings.openai import OpenAIEmbedding

# Get configuration
config = get_config()
vector_config = config.vector_store

# Cache embedding model (CRITICAL: reuse across operations)
cached_embed_model = OpenAIEmbedding(
    model=vector_config.embedding_model,
    dimensions=vector_config.embedding_dimensions
)

# Create vector store provider
vector_provider = VectorStoreFactory.create_provider(
    mode=vector_config.rag_mode,
    # ChromaDB params (used if rag_mode="chromadb")
    persist_path=vector_config.chroma_path,
    collection_name=vector_config.chroma_collection,
    # pgvector params (used if rag_mode="pgvector")
    connection_string=vector_config.pg_connection_string,
    table_name=vector_config.pg_table_name,
    embed_dim=vector_config.embedding_dimensions,
    # Shared
    embed_model=cached_embed_model
)

# Add documents
documents = [
    Document(
        text="GAMP-5 category 5 requires extensive validation testing...",
        metadata={"document_type": "guideline", "source": "ISPE GAMP-5"}
    )
]

metadata = {
    "gamp_category": "5",
    "created_by": "ingestion_service",
    "document_type": "validation_protocol"
}

doc_ids = await vector_provider.add_documents(documents, metadata)

# Query with metadata filtering
results = await vector_provider.query(
    query_text="What are OQ test execution procedures?",
    top_k=5,
    metadata_filters={"gamp_category": "5"}
)

for result in results:
    print(f"Score: {result.score:.3f} | {result.node.text[:100]}...")
```

---

## Required Libraries/Versions

### Current Project (pyproject.toml)
```toml
llama-index-core = ">=0.11.0"
llama-index = ">=0.11.0"
llama-index-vector-stores-chroma = ">=0.3.0"
chromadb = ">=0.4.22"
```

### Required Additions for Task 1.2
```bash
# Add via `uv add`:

# PostgreSQL pgvector support (REQUIRED for AWS production)
uv add "llama-index-vector-stores-postgres>=0.2.0"
uv add "psycopg2-binary>=2.9.9"  # Or asyncpg>=0.29.0 for async

# Upgrade LlamaIndex core for 0.12.0+ features
uv add "llama-index-core>=0.12.0"

# Redis for embedding caching (optional but recommended)
uv add "redis>=5.0.0"
uv add "llama-index-storage-kvstore-redis>=0.1.0"
```

### Complete Dependency Specifications

**Core LlamaIndex:**
- `llama-index-core>=0.12.0` - Core framework (upgrade from 0.11.0)
- `llama-index>=0.12.0` - Meta-package

**Vector Store Integrations:**
- `llama-index-vector-stores-chroma>=0.3.0` - ChromaDB support (already present)
- `llama-index-vector-stores-postgres>=0.2.0` - PostgreSQL pgvector support (NEW)

**Database Drivers:**
- `chromadb>=0.4.22` - ChromaDB client (already present)
- `psycopg2-binary>=2.9.9` - PostgreSQL driver (synchronous) (NEW)
- OR `asyncpg>=0.29.0` - PostgreSQL driver (asynchronous, better for production) (NEW)

**Embedding Models:**
- `llama-index-embeddings-openai>=0.2.0` - OpenAI embeddings (already present)
- `openai>=1.12.0` - OpenAI API client (already present)

**Caching (Optional but Recommended):**
- `redis>=5.0.0` - Redis client for caching
- `llama-index-storage-kvstore-redis>=0.1.0` - Redis KV store integration

**Already Present (No Action Needed):**
- `aiofiles>=23.2.1` - Async file operations
- `python-dotenv>=1.0.0` - Environment variable management
- `numpy<2.0` - Numerical operations
- `tiktoken>=0.5.0` - Token counting

### Version Rationale

**llama-index-core>=0.12.0:**
- Breaking changes removed deprecated patterns
- Improved error handling (clearer stacktraces)
- Enhanced workflow capabilities
- Better Settings singleton management

**llama-index-vector-stores-postgres>=0.2.0:**
- Latest stable release (October 2025)
- Full pgvector extension support
- HNSW and IVFFlat indexing
- Metadata filtering via SQL WHERE clauses

**psycopg2-binary vs asyncpg:**
- `psycopg2-binary`: Easier setup, synchronous operations
- `asyncpg`: Better performance, native async, production-grade
- **Recommendation:** Use `asyncpg>=0.29.0` for production (aligns with LlamaIndex async patterns)

---

## Next Agent Guidance (task-executor)

### Implementation Priority

1. **CRITICAL CLARIFICATION: Reject "S3 Vectors" terminology**
   - The task file references "S3 Vectors" which is NOT a real AWS service
   - Implement support for **PostgreSQL with pgvector** (Aurora Serverless v2)
   - Update task documentation to reflect correct terminology

2. **Protocol-Based Abstraction (High Priority)**
   - Create `src/adapters/vector_store.py` with `VectorStoreProvider` Protocol
   - Follow Task 1.1's `StorageProvider` pattern for consistency
   - Implement `VectorStoreFactory` for dependency injection

3. **ChromaDB Adapter (Medium Priority)**
   - Create `src/adapters/chroma_adapter.py`
   - Wrap ChromaDB in LlamaIndex abstractions
   - Handle resource cleanup (file handles)
   - Warn about metadata filtering performance limitations

4. **PostgreSQL pgvector Adapter (High Priority)**
   - Create `src/adapters/postgres_adapter.py`
   - Implement connection pooling for Aurora
   - Configure HNSW indexes with pharmaceutical-optimized parameters
   - Leverage B-tree indexes for metadata filtering

5. **Configuration Integration (High Priority)**
   - Add `VectorStoreConfig` to `src/shared/config.py`
   - Support environment variables: `RAG_MODE`, `CHROMA_PATH`, `VECTOR_STORE_CONNECTION_STRING`
   - Validate configuration at startup (NO FALLBACK to defaults)

6. **Embedding Model Caching (Critical)**
   - Cache embedding model instance at provider initialization
   - Use `Settings.embed_model` for global configuration
   - Implement IngestionPipeline with Redis for document-level caching

7. **Migration Utilities (Medium Priority)**
   - Create `scripts/migrate_chromadb_to_pgvector.py`
   - Implement export/import functions
   - Add validation tests (80% top-5 overlap target)

### Critical Implementation Requirements

**NO FALLBACK LOGIC:**
- All errors must raise explicit exceptions with full diagnostic context
- Never return empty results to mask failures
- Never default to ChromaDB if pgvector fails
- Never use placeholder values for missing metadata

**Error Handling Pattern:**
```python
try:
    # Vector operation
except Exception as e:
    raise RuntimeError(
        f"CRITICAL: Vector store operation failed\n"
        f"Operation: {operation_name}\n"
        f"Mode: {self.mode}\n"
        f"Error: {str(e)}\n"
        f"Stack trace: {traceback.format_exc()}"
    ) from e
```

**GAMP-5/ALCOA+ Compliance:**
- Validate metadata on every document insertion
- Required fields: `gamp_category`, `created_by`, `document_type`
- Log all queries with timestamps, user IDs, results for audit trail
- Implement PostgreSQL audit triggers (see database schema in research findings)

**Metadata Filtering Strategy:**
- ChromaDB: Over-fetch (2x top_k) to compensate for post-filtering
- pgvector: Use SQL WHERE clauses with B-tree indexes (efficient)
- Warn users about ChromaDB limitations at scale

### Testing Strategy

**Unit Tests (Priority 1):**
- Test `VectorStoreFactory` with valid/invalid modes
- Test metadata validation (missing fields, invalid GAMP categories)
- Test embedding model caching (verify single instantiation)
- Test error handling (no fallback logic violations)

**Integration Tests (Priority 2):**
- Test ChromaDB adapter: add documents, query, metadata filtering
- Test pgvector adapter: same operations as ChromaDB
- Test parity: compare retrieval results between modes

**Performance Tests (Priority 3):**
- Benchmark query latency (target: P95 < 200ms)
- Test metadata filtering at scale (1000, 10,000, 100,000 docs)
- Validate pgvector outperforms ChromaDB on filtered queries

**Migration Tests (Priority 3):**
- Export 1000 docs from ChromaDB
- Import to pgvector
- Validate 80%+ top-5 overlap on test queries

### Package Installation Sequence

```bash
# Run in project root
cd /path/to/thesis_project

# 1. Upgrade LlamaIndex core
uv add "llama-index-core>=0.12.0"

# 2. Add PostgreSQL pgvector support
uv add "llama-index-vector-stores-postgres>=0.2.0"

# 3. Add PostgreSQL driver (choose one)
uv add "asyncpg>=0.29.0"  # RECOMMENDED for production
# OR
uv add "psycopg2-binary>=2.9.9"  # Easier setup, synchronous

# 4. Optional: Redis caching
uv add "redis>=5.0.0"
uv add "llama-index-storage-kvstore-redis>=0.1.0"

# 5. Verify installations
uv pip list | grep llama-index
uv pip list | grep postgres
uv pip list | grep asyncpg
```

### Files to Create

1. `main/src/adapters/vector_store.py` - Protocol and Factory (~150 lines)
2. `main/src/adapters/chroma_adapter.py` - ChromaDB implementation (~200 lines)
3. `main/src/adapters/postgres_adapter.py` - pgvector implementation (~250 lines)
4. `main/tests/test_vector_store_adapter.py` - Comprehensive tests (~500 lines)
5. `main/scripts/migrate_chromadb_to_pgvector.py` - Migration utility (~200 lines)

### Files to Modify

1. `main/src/shared/config.py` - Add `VectorStoreConfig` dataclass (+60 lines)
2. `pyproject.toml` - Add new dependencies (+5 lines)

### Environment Variables to Document

```bash
# Vector Store Configuration
RAG_MODE=chromadb  # or "pgvector" for production
CHROMA_PATH=./chroma_db
CHROMA_COLLECTION=pharma_docs

# PostgreSQL pgvector (Aurora production)
VECTOR_STORE_CONNECTION_STRING=postgresql://user:pass@aurora-endpoint:5432/pharma_db
VECTOR_STORE_TABLE=rag_documents

# Embedding Model
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=1536

# Query Settings
SIMILARITY_TOP_K=10
```

### Success Criteria

- [ ] Protocol-based abstraction implemented (VectorStoreProvider)
- [ ] ChromaDB adapter functional (add, query, metadata filtering)
- [ ] PostgreSQL pgvector adapter functional (same operations)
- [ ] Factory pattern enables mode switching via configuration
- [ ] Embedding model cached (single instantiation verified)
- [ ] NO FALLBACK LOGIC violations (all errors explicit)
- [ ] GAMP-5 metadata validation enforced
- [ ] Tests passing: unit (20+), integration (10+), parity (5+)
- [ ] Migration utility implemented and validated (80%+ overlap)
- [ ] Documentation updated (README, architecture diagrams)

---

## Files Referenced

### LlamaIndex Documentation
- https://developers.llamaindex.ai/python/framework/module_guides/indexing/vector_store_index/
- https://developers.llamaindex.ai/python/framework/module_guides/models/embeddings/
- https://developers.llamaindex.ai/python/framework/changelog/
- https://github.com/run-llama/llama_index/releases

### Vector Database Documentation
- https://docs.trychroma.com/ (ChromaDB)
- https://github.com/pgvector/pgvector (pgvector)
- https://www.postgresql.org/docs/15/index.html (PostgreSQL 15)

### AWS Documentation
- https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/aurora-serverless-v2.html (Aurora Serverless v2)
- https://aws.amazon.com/blogs/database/accelerate-hnsw-indexing-and-searching-with-pgvector-on-amazon-aurora/

### Research Reports
- Perplexity Deep Research: "LlamaIndex 0.12.0+ VectorStoreIndex abstraction best practices" (2025-11-10)
- Perplexity Search: "LlamaIndex AWS OpenSearch Serverless integration" (2025-11-10)
- Perplexity Search: "LlamaIndex PostgreSQL pgvector integration Aurora Serverless" (2025-11-10)

### Regulatory Standards
- ISPE GAMP-5: A Risk-Based Approach to Compliant GxP Computerized Systems
- FDA 21 CFR Part 11: Electronic Records and Electronic Signatures
- ALCOA+ Principles: Attributable, Legible, Contemporaneous, Original, Accurate, Complete, Consistent, Enduring, Available

### Project Files
- `C:\Users\anteb\Desktop\Courses\Projects\thesis_project\PRPs\aws-migration-updated.md`
- `C:\Users\anteb\Desktop\Courses\Projects\thesis_project\PRPs\tasks\1.2-vector-store-provider.md`
- `C:\Users\anteb\Desktop\Courses\Projects\thesis_project\.claude\state\results\task-executor-20251110-202405.md` (Task 1.1 reference)
- `C:\Users\anteb\Desktop\Courses\Projects\thesis_project\main\src\adapters\storage.py` (Task 1.1 Protocol pattern)
- `C:\Users\anteb\Desktop\Courses\Projects\thesis_project\main\src\shared\config.py` (Configuration integration)
- `C:\Users\anteb\Desktop\Courses\Projects\thesis_project\main\src\agents\parallel\context_provider.py` (Current ChromaDB usage)
- `C:\Users\anteb\Desktop\Courses\Projects\thesis_project\pyproject.toml` (Dependency management)

---

## Summary

Task 1.2 requires implementing a pluggable vector store provider abstracting ChromaDB (local development) and PostgreSQL with pgvector extension (AWS production via Aurora Serverless v2). The key finding is that "S3 Vectors" referenced in the migration plan is NOT a real AWS service - the intended implementation is PostgreSQL/pgvector based on cost, architecture, and compliance requirements.

The implementation follows the Protocol-based abstraction pattern from Task 1.1, using `VectorStoreProvider` Protocol and `VectorStoreFactory` for dependency injection. Both adapters leverage LlamaIndex's `VectorStoreIndex` abstraction to avoid code duplication. Embedding model caching at provider initialization is critical for performance, and metadata filtering performance differs dramatically between backends (pgvector superior).

GAMP-5/ALCOA+ compliance requires metadata validation, audit trail logging, and explicit error handling without fallback logic. PostgreSQL audit triggers provide the necessary audit trail infrastructure for pharmaceutical applications.

The task-executor should prioritize Protocol abstraction, pgvector adapter, and embedding caching. ChromaDB remains for local development but should NOT be used in production for pharmaceutical applications requiring complex metadata filtering or compliance audit trails.

**Estimated Implementation Time:** 6-8 hours (Protocol + 2 adapters + configuration + basic tests)
**Critical Path:** Protocol → pgvector adapter → embedding caching → migration utility
