# Current Task Context: 1.2

## Task File
PRPs/tasks/1.2-vector-store-provider.md

## Task Content

### What to Do
- Implement a provider that supports both local ChromaDB and AWS S3 Vector Store selection via configuration.
- Expose methods for adding documents, querying embeddings, and performing metadata-based filtering.
- Ensure migration utilities can reuse this provider to move data between backends.

### Dependencies
- Depends on Task P1.1 (storage adapter) for consistent metadata handling.
- Requires S3 Vector Store provisioning (Task 4) for full parity tests.

### Best Practices
- Use the LlamaIndex `VectorStoreIndex` abstraction to avoid code duplication.
- Over-fetch results from S3 Vector Store (no server-side filters) and filter client-side.
- Cache embedding model selection to avoid repeated instantiation.

### Code Example
```python
class VectorStoreProvider:
    def __init__(self, settings: Settings):
        self.mode = settings.rag_mode
        if self.mode == "chromadb":
            import chromadb
            self.client = chromadb.PersistentClient(path=settings.chroma_path)
            self.collection = self.client.get_or_create_collection("pharma_docs")
        elif self.mode == "s3_vectors":
            from llama_index.vector_stores.s3 import S3VectorStore
            self.vector_store = S3VectorStore(
                index_name_or_arn=settings.s3_vector_index,
                bucket_name_or_arn=settings.s3_vector_bucket,
                data_type="float32",
                distance_metric="cosine"
            )
```

### Links
- [LlamaIndex S3 Vector Store guide](https://github.com/run-llama/llama_index/tree/main/llama-index-integrations/vector_stores/llama-index-vector-stores-s3)

### Testing Strategy
- Write parity tests comparing top-k overlap between ChromaDB and S3 Vector Store using a fixture dataset (target ≥80%).
- Validate latency metrics using pytest benchmarks to ensure S3 queries remain under 200 ms P95.
- Confirm metadata filters behave identically across modes.

### Common Issues to Avoid
- Mismatched embedding dimensions causing ingestion failures.
- Forgetting to close Chroma clients, leaving file handles open.
- Not handling missing metadata keys returned from legacy Chroma entries.

## Task Metadata
- Task ID: 1.2
- Phase: 1 - Backend Abstraction
- Started: 2025-11-10
- Workflow Status: INITIALIZED
