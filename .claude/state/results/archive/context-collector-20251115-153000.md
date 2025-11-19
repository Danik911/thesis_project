# Context Collector Result - Task 3.3

## Agent Configuration
- **Agent:** context-collector
- **Task ID:** 3.3
- **Task Name:** Validate RAG Workflow Locally
- **Phase:** 3 - Containerization & Local Integration
- **Invoked:** 2025-11-15 15:30:00
- **Duration:** 45 minutes
- **Status:** SUCCESS

---

## Task Understanding

Task 3.3 requires implementing a **test harness for the RAG (Retrieval-Augmented Generation) workflow** that exercises:
1. **Document ingestion** from LocalStack S3 (document storage)
2. **Vectorization** using embeddings
3. **Retrieval** from PostgreSQL pgvector (vector storage)

The test harness must:
- Mock Bedrock DeepSeek responses for deterministic tests
- Use pytest fixtures for test isolation (ingestion vs retrieval)
- Capture trace data via Phoenix for developer debugging (local only)
- Follow GAMP-5 compliance for test evidence and audit trails
- Run within Docker Compose container (LocalStack + PostgreSQL accessible)

---

## Architecture Clarification (CRITICAL DISCREPANCY RESOLVED)

### Original Task Description
The task mentions "LocalStack S3-compatible bucket" and code example shows `S3VectorStore`, creating confusion about whether S3 stores vectors.

### Actual Architecture (Based on Task 1.2 Implementation)
The pharmaceutical test generation system uses a **two-tier storage approach**:

```
┌─────────────────────────────────────────────────────────────┐
│ RAG WORKFLOW - Two Tier Storage Architecture                │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. DOCUMENT STORAGE (LocalStack S3 in dev, AWS S3 in prod) │
│     ├─ Purpose: Store raw documents (PDFs, URS files)       │
│     ├─ Access: boto3 with endpoint_url for LocalStack       │
│     └─ Cleanup: Delete bucket contents between test runs    │
│                                                              │
│  2. VECTOR STORAGE (PostgreSQL pgvector)                    │
│     ├─ Purpose: Store embeddings from LLM (1536 dims)       │
│     ├─ Adapter: PostgreSQL pgvector adapter (Task 1.2)      │
│     ├─ Tables: pgvector extension, similarity search        │
│     └─ Cleanup: TRUNCATE vector table between test runs     │
│                                                              │
│  WORKFLOW: PDF → S3 → Extract text → Embed → PostgreSQL     │
└─────────────────────────────────────────────────────────────┘
```

**Clarifications:**
- `S3VectorStore` in task code example is **MISLEADING** - actual implementation is `PostgreSQLPgvectorStore`
- LocalStack S3 is for **document ingestion storage**, NOT vector storage
- PostgreSQL pgvector is the actual **vector similarity search** backend
- This two-tier approach mirrors production (S3 for object storage, Aurora pgvector for vectors)

---

## Research Findings

### LlamaIndex Testing Patterns (0.12.0+)

#### 1. **MockLLM for Deterministic Testing**

LlamaIndex provides a built-in `MockLLM` class for testing without real API calls:

```python
from llama_index.llms.mock import MockLLM

# Create mock LLM with fixed response
mock_llm = MockLLM(max_tokens=200)

# Or with custom response
mock_llm = MockLLM(response="Fixed test response")

# Use in index/query engine
query_engine = index.as_query_engine(llm=mock_llm)
response = query_engine.query("test question")  # Returns fixed response
```

**Key Features:**
- Deterministic responses (no randomness)
- Tracks token usage for cost analysis
- Supports streaming simulation
- No external API calls

**Alternative: Custom Fake LLM Provider**
```python
from llama_index.core.llms import BaseLLM, CompletionResponse
from llama_index.core.base.llm_types import ChatMessage

class FakeBedrockLLM(BaseLLM):
    """Fake Bedrock LLM for testing without API calls."""

    def complete(self, prompt, **kwargs) -> CompletionResponse:
        return CompletionResponse(response="Stubbed test response")

    async def acomplete(self, prompt, **kwargs) -> CompletionResponse:
        return CompletionResponse(response="Stubbed test response")

    def chat(self, messages, **kwargs):
        return ChatMessage(role="assistant", content="Stubbed test response")

    async def achat(self, messages, **kwargs):
        return ChatMessage(role="assistant", content="Stubbed test response")

# Usage
fake_llm = FakeBedrockLLM()
```

#### 2. **Pytest Fixtures for RAG Testing**

Standard fixture pattern for RAG components:

```python
import pytest
from typing import AsyncGenerator
from llama_index.core import VectorStoreIndex, Document
from llama_index.vector_stores.postgres import PGVectorStore

@pytest.fixture
async def vector_store():
    """Setup PostgreSQL pgvector for testing."""
    connection_string = "postgresql://postgres:devpassword@postgres:5432/testgen"
    store = PGVectorStore.from_connection_string(connection_string)

    # Initialize if needed
    yield store

    # Cleanup: truncate vector table
    async with store._async_engine.begin() as conn:
        await conn.execute("TRUNCATE {store.table_name}")

@pytest.fixture
async def rag_index(vector_store):
    """Create RAG index for testing."""
    index = VectorStoreIndex.from_vector_store(vector_store)
    yield index

@pytest.fixture
async def sample_documents():
    """Create sample pharmaceutical documents."""
    return [
        Document(
            text="Drug release workflow: 1. QA review, 2. Documentation, 3. Approval",
            id_="doc-1",
            metadata={"source": "protocol.pdf", "gamp_category": "5"}
        ),
        Document(
            text="Test acceptance criteria: Coverage > 80%, Execution time < 5min",
            id_="doc-2",
            metadata={"source": "test_plan.pdf", "gamp_category": "5"}
        ),
    ]

@pytest.fixture
async def rag_client(vector_store, sample_documents):
    """Setup RAG client with mocked LLM."""
    from llama_index.llms.mock import MockLLM

    # Clear vector store
    async with vector_store._async_engine.begin() as conn:
        await conn.execute(f"TRUNCATE {vector_store.table_name}")

    # Add sample documents
    index = VectorStoreIndex.from_documents(
        sample_documents,
        vector_store=vector_store,
        show_progress=True
    )

    # Create query engine with mock LLM
    mock_llm = MockLLM(response="Based on retrieved context...")
    query_engine = index.as_query_engine(llm=mock_llm)

    yield query_engine

    # Cleanup
    async with vector_store._async_engine.begin() as conn:
        await conn.execute(f"TRUNCATE {vector_store.table_name}")
```

#### 3. **Testing Ingestion vs Retrieval Separately**

```python
@pytest.mark.asyncio
async def test_ingestion_stores_documents(vector_store, sample_documents):
    """Test that documents are properly ingested and indexed."""
    # Setup
    index = VectorStoreIndex.from_documents(sample_documents, vector_store=vector_store)

    # Verify documents in vector store
    results = await vector_store.client.query(
        query_embedding=[0.0] * 1536,  # Dummy embedding
        top_k=10
    )

    assert len(results) >= len(sample_documents), "Not all documents stored"
    assert all(doc.metadata["gamp_category"] == "5" for doc in results)

@pytest.mark.asyncio
async def test_retrieval_returns_top_k(rag_client, sample_documents):
    """Test that retrieval returns correct number of results."""
    response = rag_client.query(
        "What is the release workflow?",
        retrieval_options={"top_k": 3}
    )

    # Validate response
    assert response.response is not None
    assert "release" in response.response.lower() or "workflow" in response.response.lower()

    # Validate source nodes
    assert len(response.source_nodes) <= 3, "Should return top_k=3 documents"

@pytest.mark.asyncio
async def test_retrieval_semantic_accuracy(rag_client):
    """Test that retrieval returns semantically relevant documents."""
    query = "What are test acceptance criteria?"
    response = rag_client.query(query)

    # Top result should be about acceptance criteria
    if response.source_nodes:
        top_doc = response.source_nodes[0].node.text
        assert "acceptance" in top_doc.lower() or "criteria" in top_doc.lower()
```

---

### LocalStack S3 Integration

#### 1. **Boto3 Configuration for LocalStack**

```python
import boto3
from botocore.config import Config

# Configure boto3 for LocalStack
s3_client = boto3.client(
    "s3",
    endpoint_url="http://localstack:4566",  # LocalStack endpoint in container
    aws_access_key_id="test",               # LocalStack default credentials
    aws_secret_access_key="test",
    region_name="eu-west-2",                # Match docker-compose.dev.yml
    config=Config(signature_version="s3v4")
)

# Or async version
import aioboto3

session = aioboto3.Session()
async with session.client(
    "s3",
    endpoint_url="http://localstack:4566",
    aws_access_key_id="test",
    aws_secret_access_key="test",
    region_name="eu-west-2"
) as s3_client:
    await s3_client.create_bucket(...)
```

#### 2. **Bucket Lifecycle Management in Tests**

```python
import pytest
import boto3

@pytest.fixture
async def localstack_s3_bucket():
    """Create and cleanup S3 bucket for testing."""
    bucket_name = "test-documents-" + str(uuid.uuid4())[:8]

    # Create bucket
    s3_client = boto3.client(
        "s3",
        endpoint_url="http://localstack:4566",
        aws_access_key_id="test",
        aws_secret_access_key="test",
        region_name="eu-west-2"
    )

    try:
        s3_client.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={"LocationConstraint": "eu-west-2"}
        )

        # Wait for bucket to be ready
        waiter = s3_client.get_waiter("bucket_exists")
        waiter.wait(Bucket=bucket_name)

        yield bucket_name

    finally:
        # Cleanup: Delete all objects first
        try:
            response = s3_client.list_objects_v2(Bucket=bucket_name)
            if "Contents" in response:
                for obj in response["Contents"]:
                    s3_client.delete_object(Bucket=bucket_name, Key=obj["Key"])

            # Delete bucket
            s3_client.delete_bucket(Bucket=bucket_name)
            print(f"Cleaned up bucket: {bucket_name}")
        except Exception as e:
            print(f"Cleanup error for {bucket_name}: {e}")

@pytest.mark.asyncio
async def test_document_upload_and_retrieval(localstack_s3_bucket):
    """Test uploading document to S3 and retrieving it."""
    s3_client = boto3.client(
        "s3",
        endpoint_url="http://localstack:4566",
        aws_access_key_id="test",
        aws_secret_access_key="test",
        region_name="eu-west-2"
    )

    # Upload document
    test_document = b"Protocol: Drug Release Process"
    s3_client.put_object(
        Bucket=localstack_s3_bucket,
        Key="test-protocol.pdf",
        Body=test_document,
        Metadata={
            "gamp_category": "5",
            "created_by": "test_user",
            "document_type": "protocol"
        }
    )

    # Retrieve and verify
    response = s3_client.get_object(
        Bucket=localstack_s3_bucket,
        Key="test-protocol.pdf"
    )

    retrieved = response["Body"].read()
    assert retrieved == test_document
    assert response["Metadata"]["gamp_category"] == "5"
```

#### 3. **Alternative: Moto for Lightweight Unit Tests**

For unit tests that don't need full AWS behavior, use `moto`:

```python
from moto import mock_s3
import boto3

@mock_s3  # Decorator approach (doesn't require running container)
def test_s3_operations():
    s3_client = boto3.client("s3", region_name="eu-west-2")

    # Create bucket (in-memory mock)
    s3_client.create_bucket(
        Bucket="test-bucket",
        CreateBucketConfiguration={"LocationConstraint": "eu-west-2"}
    )

    # Test operations
    s3_client.put_object(Bucket="test-bucket", Key="file.txt", Body=b"content")
    response = s3_client.get_object(Bucket="test-bucket", Key="file.txt")
    assert response["Body"].read() == b"content"
```

**Comparison: LocalStack vs Moto**
- **LocalStack**: Full AWS behavior (S3 versioning, ACLs, lifecycle rules) - Integration tests
- **Moto**: Lightweight, in-memory, fast - Unit tests
- **Recommendation**: Use moto for unit tests, LocalStack for integration tests with Compose stack

---

### Bedrock LLM Mocking

#### 1. **Custom Fake Bedrock Provider**

```python
from llama_index.core.llms import BaseLLM, CompletionResponse, ChatResponse
from llama_index.core.base.llm_types import ChatMessage
from typing import Any, List

class FakeBedrockLLM(BaseLLM):
    """Deterministic Bedrock LLM for testing."""

    def __init__(self, response: str = "This is a test response."):
        super().__init__()
        self.response = response
        self.call_count = 0

    @property
    def metadata(self) -> dict:
        return {"model_name": "bedrock-fake"}

    def complete(self, prompt: str, **kwargs: Any) -> CompletionResponse:
        """Synchronous completion."""
        self.call_count += 1
        return CompletionResponse(response=self.response)

    async def acomplete(self, prompt: str, **kwargs: Any) -> CompletionResponse:
        """Asynchronous completion."""
        self.call_count += 1
        return CompletionResponse(response=self.response)

    def chat(self, messages: List[ChatMessage], **kwargs: Any) -> ChatResponse:
        """Synchronous chat."""
        self.call_count += 1
        return ChatResponse(
            message=ChatMessage(role="assistant", content=self.response)
        )

    async def achat(self, messages: List[ChatMessage], **kwargs: Any) -> ChatResponse:
        """Asynchronous chat."""
        self.call_count += 1
        return ChatResponse(
            message=ChatMessage(role="assistant", content=self.response)
        )

    def stream_complete(self, prompt: str, **kwargs: Any):
        """Stream completion (simplified)."""
        yield self.response

    async def astream_complete(self, prompt: str, **kwargs: Any):
        """Async stream completion."""
        yield self.response

# Usage in tests
@pytest.fixture
def fake_bedrock_llm():
    return FakeBedrockLLM(response="Based on the drug release protocol...")

@pytest.mark.asyncio
async def test_query_with_fake_bedrock(rag_index, fake_bedrock_llm):
    query_engine = rag_index.as_query_engine(llm=fake_bedrock_llm)
    response = query_engine.query("What is the release workflow?")

    assert response.response == "Based on the drug release protocol..."
    assert fake_bedrock_llm.call_count > 0  # Verify LLM was called
```

#### 2. **Using MockLLM (Simpler Alternative)**

```python
from llama_index.llms.mock import MockLLM

# Simpler approach - no custom class needed
mock_llm = MockLLM(response="The drug must complete QA review before release.")

query_engine = rag_index.as_query_engine(llm=mock_llm)
response = query_engine.query("What is required for release?")
# Returns: "The drug must complete QA review before release."
```

#### 3. **Mocking Bedrock API Calls (If Testing API Integration)**

```python
from unittest.mock import patch, MagicMock
import boto3

@patch("boto3.client")
def test_bedrock_api_call_mocked(mock_boto3_client):
    """Test code that calls Bedrock API."""
    # Setup mock
    mock_bedrock = MagicMock()
    mock_boto3_client.return_value = mock_bedrock
    mock_bedrock.invoke_model.return_value = {
        "body": MagicMock(read=lambda: b'{"response":"Test response"}')
    }

    # Your code that calls bedrock
    client = boto3.client("bedrock-runtime", region_name="eu-west-2")
    response = client.invoke_model(
        modelId="amazon.bedrock-models.deepseek-v3.1",
        body=b'{"prompt":"test"}'
    )

    # Verify
    assert response["body"].read() == b'{"response":"Test response"}'
    mock_boto3_client.assert_called_once()
```

---

### Phoenix Observability for Local Testing

#### 1. **Environment Variable Configuration**

```python
import os
from llama_index.core.instrumentation import Instrumentation
from llama_index.core.instrumentation.events import CBEventType

# Configure Phoenix ONLY for local development
if os.getenv("ENVIRONMENT") == "local":
    os.environ["PHOENIX_API_ENDPOINT"] = "http://localhost:6006"
    os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = "http://localhost:4317"

    # Enable detailed tracing
    os.environ["OTEL_SDK_DISABLED"] = "false"
    instrumentation = Instrumentation()
else:
    # Production: disable Phoenix tracing
    os.environ["OTEL_SDK_DISABLED"] = "true"
```

#### 2. **Phoenix Integration in Tests**

```python
import pytest
import os
from llama_index.core.instrumentation import Instrumentation
from llama_index.core.callbacks import CallbackManager

@pytest.fixture
def phoenix_instrumentation():
    """Setup Phoenix tracing for local tests only."""
    if os.getenv("ENVIRONMENT") != "local":
        return None

    try:
        # Import Phoenix only if enabled
        from arize.utils.types import Embedding
        from phoenix.trace.tracer import Tracer

        # Initialize tracer
        tracer = Tracer()

        yield tracer

        # Export traces for compliance evidence
        tracer.close()
    except ImportError:
        pytest.skip("Phoenix not installed")

@pytest.mark.asyncio
async def test_rag_workflow_with_tracing(rag_client, phoenix_instrumentation):
    """Test RAG workflow with Phoenix tracing enabled."""
    query = "What is the drug release workflow?"
    response = rag_client.query(query)

    # Verify response
    assert response.response is not None

    # Traces automatically captured by Phoenix
    # They will be visible at http://localhost:6006 during local development
```

#### 3. **Trace Export for Compliance Evidence**

```python
import json
from datetime import datetime
from pathlib import Path

def export_phoenix_traces(trace_data: dict, output_dir: str = ".claude/state/results"):
    """Export Phoenix traces for GAMP-5 compliance evidence."""
    output_path = Path(output_dir) / f"phoenix-trace-{datetime.now().isoformat()}.json"

    with open(output_path, "w") as f:
        json.dump({
            "trace_timestamp": datetime.now().isoformat(),
            "traces": trace_data,
            "gamp_category": "5",
            "compliance_evidence": True
        }, f, indent=2)

    return output_path

# In test
@pytest.mark.asyncio
async def test_rag_with_trace_export(rag_client):
    query = "What is the acceptance criteria?"
    response = rag_client.query(query)

    trace_data = {
        "query": query,
        "response": response.response,
        "source_nodes": [
            {
                "text": node.node.text[:100],
                "score": node.score
            }
            for node in response.source_nodes
        ],
        "execution_time_ms": 123.45
    }

    # Export for audit trail
    trace_file = export_phoenix_traces(trace_data)
    assert trace_file.exists()
```

#### 4. **LangFuse Alternative (If Phoenix Not Available)**

```python
from langfuse import observe

# Enable tracing ONLY in local environment
ENABLE_LANGFUSE = os.getenv("ENVIRONMENT") == "local"

@observe(disabled=not ENABLE_LANGFUSE)
async def test_query_with_langfuse_tracing(query_engine):
    """RAG query with optional Langfuse tracing."""
    response = query_engine.query("Test question")
    return response
```

---

### Pharmaceutical Compliance (GAMP-5 & ALCOA+)

#### 1. **GAMP-5 Requirements for Test Harnesses**

**Test Harness Classification: Category 5 (Low Risk)**
- Custom written test code/scripts
- No audit trail required (unlike Category 4)
- Documentation must be maintained
- Risk assessment: Minimal (tests are not regulated code, they validate regulated code)

**Required Documentation:**
```
tests/
├── test_rag_workflow.py       # Test code (Category 5 - low risk)
├── README.md                  # Test purpose, scope, environment setup
├── test_data/
│   ├── sample_protocol.pdf    # Test fixture documents
│   └── test_acceptance_criteria.txt
└── evidence/                  # Compliance evidence folder
    ├── test_execution_log.txt  # Test run output
    ├── coverage_report.html    # Code coverage
    └── phoenix_traces.json     # Trace export for observability
```

**GAMP-5 Checklist for Tests:**
- ✅ Test code is version controlled (Git)
- ✅ Test scope clearly defined (RAG ingestion, retrieval, mocking)
- ✅ Test environment documented (Compose stack, LocalStack, PostgreSQL)
- ✅ Test data is fixed/known (sample documents, deterministic LLM)
- ✅ Test pass/fail criteria explicit (assertion statements)
- ✅ Evidence preserved (execution logs, Phoenix traces)

#### 2. **ALCOA+ Principles for Test Data**

```python
import logging
from datetime import UTC, datetime
import uuid

# Setup GAMP-5 audit logger for test execution
audit_logger = logging.getLogger("test_audit")

class TestAuditContext:
    """ALCOA+ compliant test execution context."""

    def __init__(self):
        self.test_id = str(uuid.uuid4())
        self.test_user = "test_harness_automated"
        self.test_timestamp = datetime.now(UTC).isoformat()
        self.test_results = []

    def record_test(self, test_name: str, passed: bool, details: str):
        """Record test result with ALCOA+ metadata."""
        self.test_results.append({
            # Attributable: who executed?
            "user": self.test_user,
            # Legible: human readable format
            "timestamp": self.test_timestamp,
            "test_name": test_name,
            # Contemporaneous: recorded at time of execution
            "result": "PASS" if passed else "FAIL",
            # Original: unchanged after recording
            "details": details,
            # Accurate: matches actual outcome
            "test_id": self.test_id,
            # Complete: all required fields present
            "execution_environment": "local_development",
            # Consistent: always same format
            "gamp_category": "5"
            # Enduring: persisted to file
            # Available: retrievable when needed
        })

        audit_logger.info(f"Test {test_name}: {details}")

@pytest.fixture
def audit_context():
    ctx = TestAuditContext()
    yield ctx

    # Export audit trail to file for compliance
    with open(f".claude/state/results/test-audit-{ctx.test_id}.json", "w") as f:
        import json
        json.dump(ctx.test_results, f, indent=2)

@pytest.mark.asyncio
async def test_ingestion_with_audit(rag_client, sample_documents, audit_context):
    """Test ingestion with ALCOA+ audit trail."""
    try:
        # Execute test
        results = await rag_client.ingest(sample_documents)

        # Record result
        audit_context.record_test(
            test_name="test_ingestion_with_audit",
            passed=True,
            details=f"Ingested {len(results)} documents successfully"
        )

        assert len(results) == len(sample_documents)
    except Exception as e:
        audit_context.record_test(
            test_name="test_ingestion_with_audit",
            passed=False,
            details=f"Failed: {str(e)}"
        )
        raise
```

#### 3. **Test Evidence Folder Structure**

```
.claude/state/results/
├── test-execution-20251115-153000.txt    # Pytest output
├── test-audit-{uuid}.json                # ALCOA+ audit trail
├── phoenix-trace-{timestamp}.json        # Observability traces
├── coverage-report.html                  # Code coverage
└── GAMP5_TEST_VALIDATION.md              # Summary document
```

**GAMP-5 Test Validation Document:**
```markdown
# GAMP-5 Test Validation Report

## Test Harness Classification
- **Category:** 5 (Custom test scripts, low risk)
- **Test Scope:** RAG workflow (ingestion, vectorization, retrieval)

## Test Environment
- **Stack:** Docker Compose (LocalStack S3, PostgreSQL pgvector)
- **Region:** eu-west-2 (London) - production parity
- **Date Executed:** 2025-11-15

## Test Coverage
- Ingestion: 100% (sample documents)
- Vectorization: 100% (mock embeddings)
- Retrieval: 100% (top_k tests)

## Compliance Evidence
- Audit trails: test-audit-*.json
- Traces: phoenix-trace-*.json
- Coverage: coverage-report.html

## Regulatory Alignment
- ✅ GAMP-5 Category 5 (low risk)
- ✅ ALCOA+ principles (audit trail captured)
- ✅ 21 CFR Part 11 ready (no electronic signatures needed for test harness)
```

---

### Implementation Gotchas & Prevention

#### 1. **LocalStack Bucket Cleanup (Prevent Duplication)**

**Problem:** If cleanup fails, old buckets accumulate, causing duplicate data in tests

**Solution:**
```python
@pytest.fixture
async def localstack_s3_bucket():
    bucket_name = "test-bucket-" + str(uuid.uuid4())[:8]
    s3_client = boto3.client(
        "s3",
        endpoint_url="http://localstack:4566",
        aws_access_key_id="test",
        aws_secret_access_key="test",
        region_name="eu-west-2"
    )

    try:
        s3_client.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={"LocationConstraint": "eu-west-2"}
        )
        yield bucket_name
    finally:
        # CRITICAL: Delete all objects before bucket
        try:
            paginator = s3_client.get_paginator("list_objects_v2")
            pages = paginator.paginate(Bucket=bucket_name)

            for page in pages:
                if "Contents" in page:
                    for obj in page["Contents"]:
                        s3_client.delete_object(Bucket=bucket_name, Key=obj["Key"])

            s3_client.delete_bucket(Bucket=bucket_name)
        except Exception as e:
            print(f"ERROR: Failed to cleanup {bucket_name}: {e}")
            # Don't swallow error - let test fail loudly
            raise

# Test with cleanup verification
@pytest.mark.asyncio
async def test_cleanup_verification(localstack_s3_bucket):
    """Verify bucket cleanup works."""
    # Upload multiple objects
    s3_client = boto3.client("s3", endpoint_url="http://localstack:4566", ...)
    for i in range(10):
        s3_client.put_object(
            Bucket=localstack_s3_bucket,
            Key=f"test-file-{i}.txt",
            Body=b"test content"
        )

    # Fixture cleanup should handle all 10 objects
```

**Prevention:** Always test cleanup separately; use pagination for large buckets

#### 2. **Credential Isolation (NO Real Bedrock Keys)**

**Problem:** Real credentials in test code → security breach

**Solution:**
```python
# NEVER do this:
# bedrock_client = boto3.client("bedrock-runtime",
#     aws_access_key_id="AKIAIOSFODNN7EXAMPLE",
#     aws_secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
# )

# ALWAYS use environment variables or mocks:
import os

# For unit tests: Use mocks
from llama_index.llms.mock import MockLLM
mock_llm = MockLLM()

# For integration tests: Use environment variables
bedrock_key = os.getenv("BEDROCK_API_KEY")
if not bedrock_key:
    pytest.skip("Bedrock API key not configured (expected for unit tests)")

# For LocalStack: Use default test credentials
s3_client = boto3.client(
    "s3",
    endpoint_url="http://localstack:4566",
    aws_access_key_id="test",      # LocalStack default (safe)
    aws_secret_access_key="test"
)
```

**Prevention:**
- ✅ Use `pytest.skip()` if real credentials needed
- ✅ Use environment variables for sensitive data
- ✅ Add `.env.development` to `.gitignore`
- ✅ Use deterministic mocks instead of real APIs

#### 3. **Phoenix Config Isolation (Local Only)**

**Problem:** Phoenix tracing leaks to production; config committed to Git

**Solution:**
```python
import os

# Environment-based Phoenix config
if os.getenv("ENVIRONMENT") == "local":
    os.environ["PHOENIX_API_ENDPOINT"] = "http://localhost:6006"
    PHOENIX_ENABLED = True
else:
    PHOENIX_ENABLED = False

# NEVER commit this to Git:
# Remove from .gitignore if present:
# ❌ .env.development  (contains Phoenix keys)
# ❌ phoenix-traces.json (contains trace data)

# DO add to .gitignore:
# ✅ .env.development
# ✅ phoenix-traces-*.json
# ✅ .claude/state/results/phoenix-*.json

@pytest.fixture
def phoenix_cleanup():
    """Ensure Phoenix traces are cleaned up after tests."""
    yield

    # Clean up trace files
    from pathlib import Path
    for trace_file in Path(".claude/state/results").glob("phoenix-trace-*.json"):
        trace_file.unlink(missing_ok=True)
```

**Prevention:**
- ✅ Check `ENVIRONMENT` variable before enabling Phoenix
- ✅ Add trace files to `.gitignore`
- ✅ Use `pytest --capture=no` to see logs without trace file
- ✅ Export traces ONLY when explicitly requested

#### 4. **PostgreSQL pgvector Table Initialization**

**Problem:** Tests fail if pgvector extension not loaded or table doesn't exist

**Solution:**
```python
import asyncpg

async def ensure_pgvector_ready(connection_string: str):
    """Initialize pgvector extension and tables before tests."""
    conn = await asyncpg.connect(connection_string)

    try:
        # Enable pgvector extension
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")

        # Create embeddings table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS embeddings (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                content TEXT NOT NULL,
                embedding vector(1536) NOT NULL,
                metadata JSONB,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)

        # Create index for similarity search
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS embeddings_vector_idx
            ON embeddings USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100);
        """)

        print("pgvector ready for tests")
    finally:
        await conn.close()

@pytest.fixture
async def pgvector_ready():
    """Setup pgvector before tests."""
    await ensure_pgvector_ready("postgresql://postgres:devpassword@postgres:5432/testgen")
    yield
    # Note: Don't drop tables - reuse for multiple tests
```

**Prevention:**
- ✅ Check extension with `SELECT * FROM pg_extension WHERE extname='vector'`
- ✅ Create table with `IF NOT EXISTS` (idempotent)
- ✅ Create index after table exists
- ✅ Use connection pooling for efficiency

#### 5. **LocalStack Service Readiness**

**Problem:** Tests run before LocalStack is fully initialized

**Solution:**
```python
import asyncio
import boto3
from botocore.exceptions import ConnectionError

async def wait_for_localstack(endpoint_url: str, max_retries: int = 30):
    """Wait for LocalStack to be ready before running tests."""
    s3_client = boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id="test",
        aws_secret_access_key="test",
        region_name="eu-west-2"
    )

    for attempt in range(max_retries):
        try:
            # Try a simple operation
            s3_client.list_buckets()
            print(f"LocalStack ready after {attempt + 1} attempts")
            return True
        except ConnectionError:
            if attempt < max_retries - 1:
                await asyncio.sleep(1)
            else:
                raise RuntimeError(f"LocalStack not ready after {max_retries} attempts")

@pytest.fixture(scope="session")
async def localstack_ready():
    """Setup: Wait for LocalStack before any tests run."""
    await wait_for_localstack("http://localstack:4566")
    yield

@pytest.mark.usefixtures("localstack_ready")
@pytest.mark.asyncio
async def test_s3_operations():
    """Test S3 operations (LocalStack guaranteed ready)."""
    # Your test code
```

**Prevention:**
- ✅ Use `scope="session"` fixture to run once before all tests
- ✅ Add exponential backoff between retries
- ✅ Fail loudly with error message if LocalStack not ready
- ✅ Check `docker-compose logs localstack` if still failing

---

## Recommended Approach

### Test Harness Architecture

```
main/tests/rag/
├── __init__.py
├── conftest.py                    # Pytest fixtures (shared across tests)
│   ├── s3_bucket fixture
│   ├── vector_store fixture
│   ├── sample_documents fixture
│   └── rag_client fixture
├── test_ingestion.py              # Test document ingestion
│   ├── test_ingest_single_document
│   ├── test_ingest_batch_documents
│   └── test_invalid_document_handling
├── test_vectorization.py          # Test embedding generation
│   ├── test_embedding_dimensions
│   ├── test_embedding_consistency
│   └── test_missing_embedding_error
├── test_retrieval.py              # Test vector similarity search
│   ├── test_retrieval_top_k
│   ├── test_semantic_relevance
│   └── test_empty_query_handling
├── test_e2e.py                    # End-to-end integration tests
│   ├── test_full_rag_workflow
│   ├── test_query_with_mock_bedrock
│   └── test_phoenix_tracing_enabled
└── fixtures/
    ├── sample_protocol.pdf
    ├── test_urs.txt
    └── test_acceptance_criteria.txt
```

### Test Execution Flow

```python
# conftest.py - Shared fixtures

@pytest.fixture(scope="session")
async def docker_compose_ready():
    """Wait for all services before tests."""
    await wait_for_localstack()
    await ensure_pgvector_ready()
    yield

@pytest.fixture
async def s3_bucket():
    """Create/cleanup S3 bucket for each test."""
    # ... (see earlier code)

@pytest.fixture
async def vector_store():
    """Create/cleanup PostgreSQL pgvector store for each test."""
    # ... (see earlier code)

@pytest.fixture
async def sample_documents():
    """Load sample pharmaceutical documents."""
    # ... (see earlier code)

@pytest.fixture
async def rag_client(vector_store, s3_bucket):
    """Initialize RAG client with mock LLM."""
    mock_llm = MockLLM(response="Test response based on context...")
    return RagClient(
        vector_store=vector_store,
        s3_bucket=s3_bucket,
        llm=mock_llm
    )

# test_ingestion.py

@pytest.mark.asyncio
async def test_ingest_single_document(rag_client, sample_documents):
    """Verify single document ingestion."""
    doc = sample_documents[0]
    result = await rag_client.ingest(doc)

    assert result.success
    assert result.document_id is not None

@pytest.mark.asyncio
async def test_ingest_batch_documents(rag_client, sample_documents):
    """Verify batch ingestion."""
    results = await rag_client.ingest_batch(sample_documents)

    assert len(results) == len(sample_documents)
    assert all(r.success for r in results)

# test_retrieval.py

@pytest.mark.asyncio
async def test_retrieval_top_k(rag_client, sample_documents):
    """Verify top_k retrieval."""
    await rag_client.ingest_batch(sample_documents)

    response = rag_client.query(
        "What is the release workflow?",
        top_k=3
    )

    assert len(response.source_nodes) <= 3
    assert all(node.score > 0 for node in response.source_nodes)

# test_e2e.py

@pytest.mark.asyncio
async def test_full_rag_workflow(rag_client, sample_documents):
    """Test complete RAG workflow: ingest → embed → retrieve."""
    # Ingest
    await rag_client.ingest_batch(sample_documents)

    # Query
    response = rag_client.query("What are acceptance criteria?")

    # Verify
    assert response.response is not None
    assert response.source_nodes is not None
    assert "acceptance" in response.response.lower() or "criteria" in response.response.lower()
```

### Running Tests

```bash
# Run all RAG tests
pytest main/tests/rag/ -v

# Run with coverage
pytest main/tests/rag/ --cov=main/src --cov-report=html

# Run with Phoenix tracing (local only)
ENVIRONMENT=local pytest main/tests/rag/ -v -s

# Run specific test
pytest main/tests/rag/test_retrieval.py::test_retrieval_top_k -v
```

---

## Required Libraries/Versions

Based on existing project setup (Task 3.2, 1.2):

| Library | Version | Purpose | Installation |
|---------|---------|---------|--------------|
| **pytest** | >=7.4.0 | Test framework | `uv add pytest` |
| **pytest-asyncio** | >=0.21.0 | Async test support | `uv add pytest-asyncio` |
| **boto3** | >=1.28.0 | AWS SDK (S3 mocking) | `uv add boto3` |
| **aioboto3** | >=12.0.0 | Async AWS SDK | `uv add aioboto3` |
| **llama-index-core** | >=0.13.0 | LlamaIndex (compatible with 0.12.0+) | Already installed |
| **llama-index-vector-stores-postgres** | >=0.7.1 | PostgreSQL pgvector adapter | Already installed |
| **asyncpg** | >=0.30.0 | PostgreSQL async driver | Already installed |
| **moto** | >=5.0.0 | S3 mocking (lightweight unit tests) | `uv add moto[s3]` |
| **arize-phoenix** | >=2.0.0 | Phoenix observability (optional local) | `uv add arize-phoenix` |
| **python-dotenv** | >=1.0.0 | .env configuration | `uv add python-dotenv` |

**Why These Versions:**
- `pytest-asyncio>=0.21.0`: Required for async/await test support (Task 1.3 uses async)
- `boto3>=1.28.0`: LocalStack S3 compatibility (path-style endpoint)
- `llama-index-core>=0.13.0`: Stable workflows API, MockLLM class
- `llama-index-vector-stores-postgres>=0.7.1`: Matches Task 1.2 implementation
- `moto>=5.0.0`: Latest S3 mocking, better LocalStack compatibility

---

## Next Agent Guidance

### For task-executor (Implementation)

1. **Create test structure:**
   - Create `main/tests/rag/` directory
   - Create `conftest.py` with shared pytest fixtures
   - Create test files: `test_ingestion.py`, `test_vectorization.py`, `test_retrieval.py`, `test_e2e.py`

2. **Implement fixtures (HIGH PRIORITY):**
   - `localstack_s3_bucket`: Create/cleanup S3 bucket with explicit object deletion
   - `vector_store`: Initialize PostgreSQL pgvector with table/index creation
   - `sample_documents`: Load pharmaceutical sample documents
   - `rag_client`: Combine above with MockLLM (CRITICAL: mock, not real Bedrock)

3. **Implement ingestion tests:**
   - Single document ingestion
   - Batch ingestion (10+ documents)
   - Error handling (invalid format, missing metadata)
   - Verify documents stored in vector store

4. **Implement retrieval tests:**
   - top_k=3 returns ≤3 results
   - Semantic relevance verification
   - Empty vector store handling
   - Query with no matching documents

5. **Implement E2E tests:**
   - Full workflow: ingest → embed → query
   - Mock Bedrock response verification
   - Phoenix tracing capture (if ENVIRONMENT=local)
   - Audit trail generation

6. **Test configuration:**
   - Ensure LocalStack S3 endpoint: `http://localstack:4566`
   - Ensure PostgreSQL endpoint: `postgresql://postgres:devpassword@postgres:5432/testgen`
   - Ensure Mock LLM used (NO real Bedrock credentials)
   - Ensure cleanup fixtures run after each test

7. **Coverage & Evidence:**
   - Aim for ≥80% coverage (ingestion, vectorization, retrieval)
   - Export Phoenix traces (if local)
   - Generate audit trail (ALCOA+ compliance)
   - Document test environment in README

### Critical Constraints (NO FALLBACK LOGIC)
- ❌ DO NOT swallow cleanup exceptions (raise them loudly)
- ❌ DO NOT use real Bedrock/AWS credentials
- ❌ DO NOT skip cleanup if bucket has objects
- ❌ DO NOT return success on retrieval with 0 results
- ✅ DO fail fast on any error with full diagnostics
- ✅ DO verify LocalStack ready before tests start
- ✅ DO cleanup after EVERY test (isolation)

### Known Issues to Avoid
1. LocalStack bucket accumulation → Use unique names + explicit cleanup
2. PostgreSQL table conflicts → Use TRUNCATE not DROP (faster, preserves schema)
3. Mock LLM not called → Verify LLM passed to query_engine
4. Phoenix traces not exported → Check ENVIRONMENT=local before export
5. pgvector extension missing → Create in fixture setup, not test

---

## Files Referenced

### LlamaIndex Documentation
- [LlamaIndex Testing Guide](https://docs.llamaindex.ai/en/stable/how_to/testing/)
- [LlamaIndex Observability (Phoenix)](https://docs.llamaindex.ai/en/v0.12.15/module_guides/observability/observability.html)
- [LlamaIndex Workflows (0.12.0+)](https://developers.llamaindex.ai/python/framework/understanding/workflows/)
- [LlamaIndex DeepEval Integration](https://developers.llamaindex.ai/python/framework/community/integrations/deepeval/)

### LocalStack & AWS Mocking
- [LocalStack S3 Documentation](https://docs.localstack.cloud/user-guide/aws-services/s3/)
- [Moto Library Documentation](https://docs.getmoto.org/)
- [boto3 S3 Client Reference](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html)

### PostgreSQL pgvector
- [pgvector Extension](https://github.com/pgvector/pgvector)
- [LlamaIndex PostgreSQL Vector Store](https://github.com/run-llama/llama_index/tree/main/llama-index-integrations/vector_stores/llama-index-vector-stores-postgres)

### Pharmaceutical Compliance
- [GAMP-5 Guidelines (ISPE)](https://www.ispe.org/publications/guidance-documents/gamp-5-guidance)
- [ALCOA+ Data Integrity Principles](https://www.fda.gov/media/119267/download)
- [21 CFR Part 11 - Electronic Records & Signatures](https://www.ecfr.gov/current/title-21/part-11)

### Project-Specific References
- [docker-compose.dev.yml](C:\Users\anteb\Desktop\Courses\Projects\thesis_project\docker-compose.dev.yml) - Service configuration
- [scripts/postgres-init.sql](C:\Users\anteb\Desktop\Courses\Projects\thesis_project\scripts\postgres-init.sql) - Database schema
- [Task 1.2 Results](C:\Users\anteb\Desktop\Courses\Projects\thesis_project\.claude\state\results\task-executor-20251110-202405.md) - Vector store adapter implementation
- [CLAUDE.md](C:\Users\anteb\Desktop\Courses\Projects\thesis_project\CLAUDE.md) - Project compliance requirements

---

## Summary

**Task 3.3 Test Harness Implementation** requires:

1. **Two-tier storage testing**: S3 (documents) + PostgreSQL pgvector (vectors)
2. **Pytest fixtures**: Isolated setup/cleanup for each test component
3. **MockLLM usage**: Deterministic Bedrock responses (NO real API calls)
4. **LocalStack S3 integration**: With explicit bucket cleanup
5. **Phoenix tracing**: Local-only via environment variables
6. **GAMP-5 compliance**: Category 5 test harness with audit trail
7. **ALCOA+ principles**: All test data and results documented

**Critical Success Factors:**
- MockLLM for deterministic testing (not real Bedrock)
- Explicit cleanup in fixtures (no resource leaks)
- Environment-based Phoenix configuration (local only)
- pgvector table initialization (extension + table + index)
- LocalStack readiness check before tests start
- Audit trail generation (compliance evidence)

This research provides implementation patterns, code examples, and best practices. The task-executor should use these as templates while adapting to the actual project structure.
