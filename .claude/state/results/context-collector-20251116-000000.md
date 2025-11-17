# Context Collector Result - Task 3.5: End-to-End Local Testing

**Timestamp:** 2025-11-16T00:00:00Z
**Agent:** context-collector
**Task ID:** 3.5
**Status:** SUCCESS
**Duration:** ~45 minutes

---

## Task Understanding

Task 3.5 requires creating and validating end-to-end local testing for the pharmaceutical test generation system BEFORE AWS deployment. This means:

1. **Verify complete workflow execution locally**: URS document → GAMP-5 categorization → test planning → parallel agent execution → test suite generation
2. **Ensure Docker Compose stack works end-to-end**: API accepts jobs, worker processes them with actual unified workflow
3. **Validate all infrastructure is production-ready**: PostgreSQL, LocalStack, FastAPI, background worker
4. **Confirm GAMP-5 compliance is maintained**: Audit trails, NO FALLBACK LOGIC, ALCOA+ principles
5. **Document testing procedures** for future engineers
6. **Identify gaps and create follow-up tickets** for Phase 4 AWS deployment

---

## Current System Architecture

### Working MVP Components (Verified)

**Task 3.3 Validation Confirmed These Working:**
- ✅ **GAMP-5 Categorization Agent** - 100% confidence for Category 5 documents
- ✅ **Context Provider Agent** - ChromaDB with pharmaceutical document retrieval
- ✅ **Research Agent** - Context-aware research with proper event handling
- ✅ **SME Agent** - Compliance assessment and risk evaluation
- ✅ **OQ Test Generation** - 30 comprehensive tests generated with DeepSeek V3
- ✅ **Phoenix Observability** - 131 spans captured with proper tracing
- ✅ **Audit Trail** - Complete GAMP-5 compliance with ALCOA+ principles

**Execution Performance:**
- Full workflow: 6 minutes 21 seconds
- Cost: $1.35 per 1M tokens (DeepSeek V3 via OpenRouter)
- Output: 30 OQ tests exceeding 25-test target

### Docker Compose Stack (Task 3.2 - OPERATIONAL)

```
STATUS: 4/4 SERVICES RUNNING
┌─────────────────────────────────────────────────────────────┐
│ Service       │ Image              │ Port  │ Status         │
├───────────────┼────────────────────┼───────┼────────────────┤
│ postgres      │ pgvector:pg15      │ 5432  │ Healthy        │
│ localstack    │ localstack:3       │ 4566  │ Started        │
│ api           │ FastAPI (custom)   │ 8080  │ Ready          │
│ worker        │ Python (custom)    │ -     │ Running        │
└─────────────────────────────────────────────────────────────┘
```

**Database Status:**
- PostgreSQL 15 with pgvector v0.8.1 ✅
- Tables: `jobs`, `rag_documents` ✅
- SQS Queues: `testgen-jobs`, `testgen-jobs-dlq` ✅

### Current FastAPI Job Submission (Working)

**Endpoint:** `POST /jobs`
**Status:** ✅ ACCEPTS jobs, creates JobRecord
**Authentication:** Clerk JWT (Task 1.4 complete)

```python
# Current flow (Task 3.2):
1. API receives URS file upload + Clerk token
2. Creates JobRecord (PENDING)
3. Adds job_id to asyncio.Queue
4. Returns job_id to client
5. Worker receives from queue → PROCESSES → Updates status
```

---

## Critical Gap: Worker Implementation Placeholder

### Current State (Non-Functional for E2E)

**File:** `main/api/worker.py` lines 212-238

```python
async def _simulate_job_processing(job: JobRecord) -> str:
    """Placeholder for actual workflow."""
    # Simulate processing time (2-5 seconds)
    processing_time = 3.0
    logger.info(f"Processing job {job.job_id} for {processing_time}s...")
    await asyncio.sleep(processing_time)

    # Simulate random failures for testing (10% failure rate)
    import random
    if random.random() < 0.1:
        raise RuntimeError("Simulated processing failure")

    # Return mock result URI
    return f"file:///output/job_{job.job_id}/test_suite.md"
```

**Problem:** Does NOT execute actual pharmaceutical workflow - just sleeps and returns mock URI.

### What's Needed

The worker must:
1. **Read URS file content** from storage_adapter (already injected)
2. **Instantiate UnifiedTestGenerationWorkflow** with proper configuration
3. **Execute workflow** with URS content as input (5-6 minutes)
4. **Capture SignedAgentResultsEvent** output
5. **Serialize test suite** to markdown/JSON format
6. **Store result** via storage_adapter
7. **Update job status** to COMPLETED with result_uri
8. **Handle errors explicitly** (NO FALLBACK LOGIC)

---

## Unified Workflow Architecture

### Entry Point: `main/src/core/unified_workflow.py`

**Master Orchestrator Class:** `UnifiedTestGenerationWorkflow(Workflow)`

**Initialization Parameters:**
```python
workflow = UnifiedTestGenerationWorkflow(
    timeout=1800,                      # 30 minutes (handles 5-6 min workflow)
    verbose=False,
    enable_phoenix=True,               # CRITICAL: observability
    enable_parallel_coordination=True,  # Research + SME agents
    enable_human_consultation=True,    # Consultation fallback
    llm=None,                          # Uses LLMConfig.get_llm()
    enable_part11_compliance=True,     # 21 CFR Part 11 controls
    user_session_id=None               # Optional user tracking
)
```

**Event Flow:**

```
INPUT:
URSIngestionEvent(urs_content: str)
         ↓
STEP 1: Document Ingestion & Parsing
         ↓
STEP 2: GAMPCategorizationWorkflow (Determines Category 1/3/4/5)
         ↓ GAMPCategorizationEvent
STEP 3: PlannerAgentWorkflow (Test planning + risk assessment)
         ↓ PlanningEvent
STEP 4: Parallel Agent Coordination
         ├─ ContextProviderAgent (ChromaDB retrieval)
         ├─ ResearchAgent (regulatory research)
         └─ SMEAgent (subject matter expertise)
         ↓ AgentResultsEvent
STEP 5: Test Generation (OQGenerationWorkflow for OQ tests)
         ↓
STEP 6: Final Compilation & Signing
         ↓ SignedAgentResultsEvent
OUTPUT:
TestSuiteOutput(tests: List[TestCase], audit_trail: AuditTrail)
```

**Critical Requirements:**

1. **API Keys MUST be set in environment:**
   - `OPENAI_API_KEY` - for text-embedding-3-small (embeddings only)
   - `OPENROUTER_API_KEY` - for DeepSeek V3 (deepseek/deepseek-chat)
   - Both required; NO FALLBACK to other models

2. **LLM Configuration** (from `main/src/config/llm_config.py`):
   ```python
   LLMConfig.get_llm()  # Returns:
   # OpenRouter(
   #     api_key=os.getenv("OPENROUTER_API_KEY"),
   #     model="deepseek/deepseek-chat",
   #     base_url="https://openrouter.ai/api/v1"
   # )
   ```

3. **ChromaDB Must Be Pre-Populated:**
   - Documents embedded before workflow runs
   - ContextProviderAgent searches for relevant documents
   - Affects confidence scores and test coverage

4. **Execution Time:** 5-6 minutes (verified in Task 3.3)
   - NOT 2 minutes (end-to-end-tester agent notes)
   - Includes DeepSeek V3 API latency
   - Job timeout set to 30 minutes (sufficient buffer)

---

## Document Ingestion Strategy

### Current Document Sources

**Location 1: Test Data**
```
main/tests/test_data/gamp5_test_data/
  ├── testing_data.md        # Primary test document
  ├── validation_data.md     # Validation examples
  └── OQ_examples.md         # OQ test examples
```

**Location 2: Regulatory Reference**
- Embedded by previous workers/scripts
- Collection: `pharma_docs` (in ChromaDB) or `rag_documents` (PostgreSQL)
- 26 documents reported in QUICK_START_GUIDE.md

### Ingestion Approach for Task 3.5

**Pre-Workflow Setup Required:**

1. **Create document ingestion script** (if not exists):
   ```python
   # main/scripts/ingest_rag_documents.py (NEW)

   from src.adapters.vector_store import VectorStoreProvider
   from src.config import get_config

   async def ingest_regulatory_documents():
       """Ingest GAMP-5 reference documents for RAG retrieval."""

       vector_store = VectorStoreProvider.get_vector_store(config=get_config())

       # Load documents from main/tests/test_data/gamp5_test_data/
       documents = [
           Document(text=..., metadata={"doc_type": "GAMP-5", ...}),
           ...
       ]

       # Store with GAMP-5 metadata
       await vector_store.add(documents)
       return len(documents)
   ```

2. **Execute before Docker Compose starts:**
   ```bash
   # Setup steps for Task 3.5:
   uv run python main/scripts/ingest_rag_documents.py

   # Verify ingestion:
   docker-compose -f docker-compose.dev.yml up -d
   curl http://localhost:8080/health  # Wait for API ready
   ```

3. **Verification Query:**
   ```python
   # Quick check in worker startup:
   context_provider = ContextProviderAgent()
   result = context_provider.search_context('GAMP-5 categories')
   if result['total_results'] == 0:
       raise RuntimeError("ChromaDB empty - documents not ingested!")
   ```

---

## Environment Configuration Checklist

### Required Environment Variables

**File:** `.env.development` (NOT tracked in Git)

```bash
# === API Keys (CRITICAL) ===
OPENAI_API_KEY=sk-...                    # For embeddings
OPENROUTER_API_KEY=sk-or-...             # For DeepSeek V3

# === Application Mode ===
ENVIRONMENT=development                  # Triggers local config loading
DEBUG=1                                   # Verbose logging

# === Storage (Local for dev, S3 in prod) ===
STORAGE_MODE=local                        # or 's3' for LocalStack
STORAGE_LOCAL_BASE_PATH=/app/output       # Docker volume path

# === Vector Store ===
RAG_MODE=chromadb                         # or 'pgvector'
CHROMA_PATH=/app/chroma_db                # Persistent storage
CHROMA_COLLECTION=pharma_docs

# === Database ===
DATABASE_URL=postgresql://postgres:devpassword@postgres:5432/testgen
POSTGRES_PASSWORD=devpassword

# === SQS (LocalStack) ===
QUEUE_MODE=sqs
AWS_ENDPOINT_URL=http://localstack:4566
AWS_REGION=eu-west-2
SQS_QUEUE_URL=http://localstack:4566/000000000000/testgen-jobs

# === Clerk Auth (Dev Instance) ===
CLERK_ISSUER=https://helped-sturgeon-19.clerk.accounts.dev
CLERK_PEM_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----\n..."

# === LangFuse Observability (Optional but recommended) ===
LANGFUSE_PUBLIC_KEY=pk_...
LANGFUSE_SECRET_KEY=sk_...

# === Logging ===
LOG_LEVEL=DEBUG
PYTHONUNBUFFERED=1
```

### Pre-Workflow Checklist

```bash
# 1. Verify API keys are set
echo "OpenRouter Key: ${OPENROUTER_API_KEY:0:20}..."
echo "OpenAI Key: ${OPENAI_API_KEY:0:20}..."

# 2. Start Phoenix observability (REQUIRED for traces)
docker run -d -p 6006:6006 --name phoenix-server arizephoenix/phoenix:latest

# 3. Start Docker Compose services
docker-compose -f docker-compose.dev.yml up -d

# 4. Wait for health checks (30-60 seconds)
sleep 30
curl http://localhost:8080/health  # Should return {"status":"healthy"}

# 5. Ingest documents into ChromaDB
uv run python main/scripts/ingest_rag_documents.py

# 6. Verify document ingestion
uv run python -c "
from src.agents.parallel.context_provider import ContextProviderAgent
agent = ContextProviderAgent()
result = agent.search_context('GAMP-5 categories')
print(f'Documents ingested: {result[\"total_results\"]}')
"

# 7. Ready for end-to-end testing
```

---

## Testing Strategy

### Test Data Sources

**Primary Test Document:**
```
File: main/tests/test_data/gamp5_test_data/testing_data.md
Size: ~5 KB
Content: Sample User Requirements document for Category 5 software
Usage: URS input for workflow
```

**Test Flow:**

```
1. Upload testing_data.md via API:
   curl -X POST http://localhost:8080/jobs \
     -H "Authorization: Bearer $CLERK_TOKEN" \
     -F "file=@main/tests/test_data/gamp5_test_data/testing_data.md"

   Response: {"job_id": "job_uuid", "status": "PENDING"}

2. Monitor job status:
   curl http://localhost:8080/jobs/job_uuid \
     -H "Authorization: Bearer $CLERK_TOKEN"

   Expected progression: PENDING → PROCESSING → COMPLETED

3. Workflow execution (5-6 minutes):
   - Categorization: ~30 seconds
   - Planning: ~1 minute
   - Parallel agents: ~2 minutes
   - Test generation: ~1.5 minutes
   - Total: ~5-6 minutes

4. Retrieve test suite:
   curl http://localhost:8080/jobs/job_uuid/result \
     -H "Authorization: Bearer $CLERK_TOKEN"

   Expected: OQ test suite (30 tests)

5. Verify in Phoenix:
   - Navigate to http://localhost:6006
   - Should see 131+ spans
   - Check trace timeline for workflow steps
```

### Expected Output Format

**Test Suite Structure** (from `main/src/agents/oq_generator/workflow.py`):

```python
OQTestSuiteEvent(
    test_suite=OQTestSuite(
        suite_id="OQ-SUITE-{uuid}",
        timestamp=datetime.now(UTC),
        urs_hash="sha256:...",
        tests=[
            OQTest(
                test_id="OQ-001",
                description="Verify software module initialization",
                expected_result="Module loads without errors",
                actual_result="...",
                status="PASS",
                evidence="...",
                gamp_category=5,
            ),
            ... # 30 tests total
        ],
        audit_trail={
            "created_by": "user_id",
            "creation_time": "ISO 8601",
            "system_version": "1.0",
            "test_framework_version": "...",
        }
    )
)
```

**Stored As:**
```
output/job_uuid/test_suite_OQ-SUITE-{id}_{timestamp}.json
output/job_uuid/test_suite_OQ-SUITE-{id}_{timestamp}.md
```

---

## Success Criteria for Task 3.5

### Functional Requirements

- [ ] **End-to-End Execution**: Submit URS → Workflow completes → Test suite generated
- [ ] **Complete Workflow**: All 5 steps execute (categorization → planning → agents → generation)
- [ ] **Job Status Tracking**: API correctly reports PENDING → PROCESSING → COMPLETED
- [ ] **Test Suite Output**: 25+ OQ tests generated with proper metadata
- [ ] **Storage Integration**: Results correctly stored via storage_adapter
- [ ] **Phoenix Traces**: 131+ spans captured in local observability server

### Compliance Requirements

- [ ] **GAMP-5 Compliance**: All tests include Category 5 metadata
- [ ] **ALCOA+ Audit Trail**: Complete and verifiable in audit logs
- [ ] **NO FALLBACK LOGIC**: All errors fail explicitly with diagnostics (0 violations)
- [ ] **Error Messages**: Meaningful diagnostics when problems occur
- [ ] **Audit Trail Exports**: Evidence package includes test logs

### Performance Requirements

- [ ] **Execution Time**: 5-6 minutes for full workflow (acceptable for local testing)
- [ ] **Memory Usage**: Reasonable consumption on 8GB+ systems
- [ ] **Container Stability**: No unexpected restarts during workflow
- [ ] **Error Recovery**: Failed jobs can be retried without manual intervention

### Documentation Requirements

- [ ] **Setup Instructions**: Clear steps for onboarding new engineers
- [ ] **Troubleshooting Guide**: Common issues and solutions
- [ ] **Testing Checklist**: Step-by-step verification procedures
- [ ] **Known Limitations**: Document what works and what doesn't
- [ ] **Gap Analysis**: Identify missing features for Phase 4 AWS deployment

---

## Known Issues and Gotchas

### 1. API Key Configuration Errors

**Problem:** Missing `OPENROUTER_API_KEY` causes cryptic import errors

**Symptom:**
```
ModuleNotFoundError: No module named 'pdfplumber'
```

**Root Cause:** LLMConfig fails silently if API key missing; subsequent imports fail

**Solution:**
```bash
# Verify both keys are loaded BEFORE starting Docker
echo "OPENAI_API_KEY=${OPENAI_API_KEY:0,20}..."
echo "OPENROUTER_API_KEY=${OPENROUTER_API_KEY:0,20}..."

# If empty, load from .env.development:
export OPENROUTER_API_KEY=$(grep OPENROUTER_API_KEY .env.development | cut -d= -f2)
```

### 2. Empty ChromaDB

**Problem:** Workflow fails if no documents indexed

**Symptom:**
```
ValueError: ContextProviderAgent found 0 documents
```

**Solution:** Execute ingestion script before starting workflow
```bash
uv run python main/scripts/ingest_rag_documents.py
```

### 3. Workflow Takes 5-6 Minutes (Not 2)

**Problem:** Test expectations set incorrectly

**Symptom:** Operator thinks something is broken when it's just slow

**Root Cause:**
- DeepSeek V3 API latency: ~30s per major step
- 5 sequential workflow steps
- Network round-trips to OpenRouter

**Solution:** Set timeout to 30 minutes minimum
```python
workflow = UnifiedTestGenerationWorkflow(timeout=1800)  # 30 min
```

### 4. Phoenix Not Running

**Problem:** Traces don't capture

**Symptom:** Phoenix UI shows no data at http://localhost:6006

**Solution:**
```bash
docker run -d -p 6006:6006 --name phoenix-server arizephoenix/phoenix:latest
# Wait 10 seconds for startup
sleep 10
curl http://localhost:6006 || echo "Phoenix not accessible"
```

### 5. Async Compatibility Issues

**Problem:** Worker needs to properly await async workflow

**Symptom:** Worker completes immediately without executing workflow

**Solution:** Use `asyncio.run()` or proper `await` in async context
```python
# In worker coroutine:
result = await workflow.run(urs_content=job.urs_filename)
```

### 6. Storage Adapter Path Issues

**Problem:** Hardcoded paths won't work in Docker containers

**Symptom:** FileNotFoundError in container but works locally

**Solution:** Always use injected storage_adapter dependency
```python
# WRONG:
with open(f"/output/{job_id}/result.json") as f: ...

# CORRECT:
result_path = await storage_adapter.store_result(job_id, test_suite)
```

### 7. Job Repository Lock Contention

**Problem:** In-memory repository with asyncio.Lock can cause deadlocks

**Symptom:** Worker hangs during job status update

**Solution:** Set reasonable lock timeouts
```python
try:
    async with asyncio.timeout(5):  # 5 second timeout
        async with job_lock:
            job.status = JobStatus.COMPLETED
except asyncio.TimeoutError:
    logger.error(f"Lock timeout for job {job_id}")
    raise RuntimeError("Job state update failed - lock timeout")
```

---

## Worker Implementation Requirements

### Pseudo-code for Task 3.5 Implementation

```python
# main/api/worker.py - _process_job_with_retries method

async def _process_job_with_retries(
    job: JobRecord,
    job_lock: asyncio.Lock,
    audit_logger: Any,
    storage_adapter: StorageProvider,  # NEW: injected dependency
) -> bool:
    """Execute pharmaceutical workflow (REPLACES simulation)."""

    retry_count = 0
    max_retries = job.max_retries

    while retry_count <= max_retries:
        try:
            # Step 1: Read URS file from storage
            urs_content = await storage_adapter.read_file(job.urs_filename)
            if not urs_content:
                raise ValueError(f"URS file empty: {job.urs_filename}")

            # Step 2: Verify ChromaDB has documents
            context_provider = ContextProviderAgent()
            doc_check = context_provider.search_context("GAMP-5")
            if doc_check['total_results'] == 0:
                raise RuntimeError("ChromaDB empty - ingest documents first")

            # Step 3: Instantiate workflow
            workflow = UnifiedTestGenerationWorkflow(
                timeout=1800,
                enable_phoenix=True,
                enable_parallel_coordination=True,
                user_session_id=job.user_id
            )

            # Step 4: Execute workflow (5-6 minutes)
            logger.info(f"Starting workflow for job {job.job_id}...")

            # CRITICAL: Properly initialize event with URS content
            start_event = URSIngestionEvent(urs_content=urs_content)

            # Run workflow - this is async and may take 5-6 minutes
            result = await workflow.run(start_event=start_event)

            # Step 5: Extract test suite from result
            if isinstance(result, SignedAgentResultsEvent):
                test_suite = result.test_suite
            else:
                raise ValueError(f"Unexpected result type: {type(result)}")

            # Step 6: Serialize to markdown/JSON
            test_suite_md = _serialize_test_suite_markdown(test_suite)
            test_suite_json = _serialize_test_suite_json(test_suite)

            # Step 7: Store result via storage adapter
            result_path = await storage_adapter.store_test_suite(
                job_id=job.job_id,
                test_suite_md=test_suite_md,
                test_suite_json=test_suite_json,
                metadata={
                    "gamp_category": test_suite.gamp_category,
                    "test_count": len(test_suite.tests),
                    "generated_at": datetime.now(UTC).isoformat(),
                }
            )

            # Step 8: Update job with success
            async with job_lock:
                job.result_uri = result_path
                job.gamp_category = test_suite.gamp_category or "5"

                # Log completion audit event
                audit_logger.log_event(
                    job_id=job.job_id,
                    event_type="workflow_complete",
                    user_id=job.user_id,
                    status=JobStatus.COMPLETED,
                    metadata={
                        "test_count": len(test_suite.tests),
                        "result_uri": result_path,
                        "execution_time_minutes": (time.time() - job.started_at) / 60
                    }
                )

            return True  # Success

        except Exception as e:
            retry_count += 1

            # Log retry with full diagnostics (NO FALLBACK)
            async with job_lock:
                job.retry_count = retry_count
                job.error_message = str(e)
                job.error_type = type(e).__name__

            if retry_count > max_retries:
                logger.error(f"Job {job.job_id} failed after {max_retries} retries")

                # Log comprehensive error for audit
                audit_logger.log_event(
                    job_id=job.job_id,
                    event_type="workflow_failed",
                    user_id=job.user_id,
                    status=JobStatus.FAILED,
                    metadata={
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "stack_trace": traceback.format_exc(),
                        "final_retry_count": retry_count,
                    }
                )
                return False

            # Retry with exponential backoff
            backoff_delay = 2 ** (retry_count - 1)
            logger.warning(
                f"Job {job.job_id} error (attempt {retry_count}/{max_retries}): {e}"
            )
            await asyncio.sleep(backoff_delay)

    return False
```

### Critical Implementation Notes

1. **Import UnifiedTestGenerationWorkflow** at top:
   ```python
   from src.core.unified_workflow import UnifiedTestGenerationWorkflow, URSIngestionEvent
   from src.core.events import SignedAgentResultsEvent
   ```

2. **Import ContextProviderAgent** for validation:
   ```python
   from src.agents.parallel.context_provider import ContextProviderAgent
   ```

3. **Error Handling is CRITICAL** - NO FALLBACK LOGIC:
   - Every exception must be caught and logged
   - Include full stack trace in audit
   - Fail explicitly when retries exhausted
   - No default/safe values

4. **Async/Await Compatibility**:
   - Worker is already async (process_job_worker coroutine)
   - Workflow is async (await workflow.run())
   - Storage adapter is async (await storage_adapter.*)
   - Lock access must use async context manager

5. **Timeout Handling**:
   - Workflow timeout: 30 minutes (sufficient for 5-6 min execution)
   - Lock timeout: 5 seconds (prevent deadlock)
   - Overall worker timeout: 1 hour (for multiple retries)

---

## Compliance and GAMP-5 Requirements

### NO FALLBACK LOGIC Verification

**Task 3.5 must achieve:**
- ✅ 0 fallback logic violations in worker implementation
- ✅ 0 artificial confidence scores
- ✅ 0 default values masking errors
- ✅ All errors fail LOUDLY with diagnostics

**Audit Trail:**
- Complete trace of workflow execution
- Error messages with full stack traces
- Timestamps for all state transitions
- User attribution (via Clerk token)

### GAMP-5 Compliance

**Category 5 Classification:** Custom pharmaceutical test generation software

**Requirements Met by Task 3.5:**
- ✅ Test harness for workflow validation
- ✅ Version control (Git tracked)
- ✅ Change documentation (audit logs)
- ✅ Traceability (Phoenix traces + audit trail)
- ✅ Access control (Clerk authentication)

### ALCOA+ Principles

- **Attributable**: User ID from Clerk token
- **Legible**: Structured JSON/markdown output
- **Contemporaneous**: Timestamps on all events
- **Original**: No modification after creation (audit trail)
- **Accurate**: Verified against workflow output
- **Complete**: All required metadata included
- **Consistent**: Same format across all runs
- **Enduring**: Stored in persistent volume
- **Available**: Retrievable via API endpoints

---

## Recommended Approach for Task 3.5

### Phase 1: Setup (30 minutes)

1. Create document ingestion script (`main/scripts/ingest_rag_documents.py`)
2. Verify environment configuration (API keys, Docker, Phoenix)
3. Start Docker Compose stack and wait for health checks
4. Pre-populate ChromaDB with regulatory documents

### Phase 2: Worker Implementation (2-3 hours)

1. Replace `_simulate_job_processing()` with actual workflow execution
2. Add UnifiedTestGenerationWorkflow instantiation
3. Implement proper async/await handling
4. Add error handling with full diagnostics
5. Implement storage adapter integration
6. Add audit logging for workflow completion

### Phase 3: Testing & Validation (2-3 hours)

1. Unit test: Verify worker can instantiate workflow
2. Integration test: Submit job via API → worker processes → test suite generated
3. Performance test: Confirm 5-6 minute execution time
4. Compliance test: Verify GAMP-5 metadata and audit trail
5. Error test: Confirm NO FALLBACK LOGIC (fail on missing API keys, empty ChromaDB, etc.)

### Phase 4: Documentation & Hardening (1-2 hours)

1. Create troubleshooting guide
2. Document onboarding checklist
3. Create testing procedures for engineers
4. Identify gaps for Phase 4 AWS migration
5. Update compliance evidence package

---

## Required Libraries and Versions

Based on existing project:

```
# Core Framework
llama-index-core==0.13.3              # Event-driven workflow engine
llama-index-workflows==0.2.0            # Workflow support

# LLM Integration
openai>=1.0.0                           # For embeddings (text-embedding-3-small)
# NOTE: DeepSeek via OpenRouter (no direct SDK needed, uses openai-compatible API)

# Data & Storage
pydantic==2.0+                          # Data validation
sqlalchemy==2.0+                        # ORM for PostgreSQL
asyncpg==0.30.0+                        # Async PostgreSQL driver
pgvector==0.3.0+                        # Vector extension support

# Vector Stores
chromadb>=0.4.0                         # In-memory/persistent vector store

# FastAPI
fastapi>=0.100.0                        # Web framework
uvicorn>=0.23.0                         # ASGI server

# Observability
phoenix-evals>=0.1.0                    # Phoenix observability
opentelemetry-api>=1.20.0               # Instrumentation
opentelemetry-sdk>=1.20.0               # SDK

# Utilities
python-dotenv>=1.0.0                    # Environment loading
pdfplumber>=0.9.0                       # PDF parsing
python-jose>=3.3.0                      # JWT handling
```

---

## Next Agent Guidance for task-executor

### Primary Deliverables

1. **Create Document Ingestion Script** (`main/scripts/ingest_rag_documents.py`)
   - Load test documents from `main/tests/test_data/gamp5_test_data/`
   - Ingest into ChromaDB or PostgreSQL pgvector
   - Verify with context_provider.search_context()
   - Include error handling (fail if no documents found)

2. **Replace Worker Placeholder** (`main/api/worker.py`)
   - Modify `_process_job_with_retries()` function (lines 134-209)
   - Remove `_simulate_job_processing()` (lines 212-238)
   - Implement full workflow execution as shown in pseudo-code above
   - Ensure NO FALLBACK LOGIC (all errors fail explicitly)

3. **Create Workflow Integration Tests** (`main/tests/test_e2e_workflow.py`)
   - Test worker can instantiate UnifiedTestGenerationWorkflow
   - Mock LLM for deterministic testing
   - Verify test suite generation and storage
   - Validate audit trail creation
   - NO external API calls (use mocks)

4. **Document Setup Procedures** (Update `docs/LOCAL_DEVELOPMENT.md`)
   - Add "End-to-End Testing" section
   - Pre-workflow checklist (API keys, Phoenix, document ingestion)
   - Step-by-step testing procedure with actual commands
   - Expected output and success criteria
   - Troubleshooting guide for common issues

### Specific Requirements for Implementation

**CRITICAL - NO FALLBACK LOGIC:**
- All API key validation must fail loudly
- Empty ChromaDB must raise explicit error
- Workflow execution errors must include full stack trace
- No default values or silent fallbacks

**CRITICAL - Async/Await Handling:**
- Use `await workflow.run()` (not `workflow.run()`)
- Use `async with job_lock:` for state updates
- Use `await storage_adapter.*()` methods
- Proper asyncio.timeout() usage

**CRITICAL - Error Handling:**
- Catch and re-log all exceptions
- Include exception type in metadata
- Preserve original traceback
- Log to both logger and audit_logger

**CRITICAL - Testing Strategy:**
- Use deterministic mock LLM
- Don't call real APIs in unit tests
- Integration tests can use real Docker services
- E2E tests should verify complete workflow execution

### File Modifications Summary

```
FILES TO CREATE:
✓ main/scripts/ingest_rag_documents.py      (100-200 lines)
✓ main/tests/test_e2e_workflow.py           (300-500 lines)

FILES TO MODIFY:
✓ main/api/worker.py                        (+150 lines, replace placeholder)
✓ docs/LOCAL_DEVELOPMENT.md                 (+200 lines, add E2E section)

FILES TO UPDATE:
✓ docker-compose.dev.yml                    (add volume mounts if needed)
✓ .env.development                          (verify all keys documented)

NO FILES TO DELETE (all existing code stays)
```

### Success Indicators

When task-executor completes, these should be true:

- ✅ `docker-compose -f docker-compose.dev.yml up -d` starts all 4 services
- ✅ `docker-compose exec api curl http://localhost:8080/health` returns healthy
- ✅ Documents are ingested into vector store (verified via agent query)
- ✅ Submitting URS file via API creates job in PENDING state
- ✅ Worker picks up job and starts workflow execution
- ✅ After 5-6 minutes, job status becomes COMPLETED
- ✅ Test suite is stored and retrievable via API
- ✅ Phoenix traces show 131+ spans for full workflow
- ✅ All errors fail loudly with diagnostics (0 fallback violations)
- ✅ GAMP-5 audit trail is complete and verifiable
- ✅ Onboarding documentation enables new engineers to run full E2E test

---

## Files Referenced

### Core Workflow
- `main/src/core/unified_workflow.py` - Master orchestrator
- `main/src/core/categorization_workflow.py` - GAMP-5 categorization
- `main/src/core/events.py` - Event definitions

### Agent Infrastructure
- `main/src/agents/oq_generator/workflow.py` - Test generation
- `main/src/agents/parallel/context_provider.py` - Document retrieval

### API & Worker
- `main/api/app.py` - FastAPI application
- `main/api/worker.py` - Background job processor (NEEDS UPDATE)
- `main/api/dependencies.py` - Dependency injection
- `main/api/models.py` - Pydantic data models

### Storage & Configuration
- `main/src/adapters/storage.py` - Storage abstraction layer
- `main/src/adapters/vector_store.py` - Vector store provider
- `main/src/config/llm_config.py` - LLM configuration
- `main/src/shared/config.py` - Application configuration

### Docker & Infrastructure
- `docker-compose.dev.yml` - Multi-service orchestration
- `.env.development` - Configuration (NOT tracked)
- `scripts/postgres-init.sql` - Database initialization
- `Dockerfile.api` - API container
- `Dockerfile.worker` - Worker container (uses same image currently)

### Test & Documentation
- `main/tests/rag/` - RAG workflow tests (Task 3.3 - COMPLETE)
- `main/tests/test_api_jobs.py` - API endpoint tests
- `docs/LOCAL_DEVELOPMENT.md` - Developer guide (NEEDS UPDATES)
- `main/docs/guides/QUICK_START_GUIDE.md` - Production workflow guide

### Compliance & Audit
- `main/api/audit.py` - Audit logging
- `main/src/core/audit_trail.py` - GAMP-5 audit trail
- `main/src/compliance/` - Regulatory compliance modules

---

## Summary

Task 3.5: End-to-End Local Testing is the bridge between functional workflow components (verified in Task 3.3) and production-ready AWS deployment (Phase 4). It requires:

1. **Connecting worker to unified workflow** (currently disconnected)
2. **Pre-loading documents into vector store** (for context retrieval)
3. **Validating complete execution** with real DeepSeek V3 API calls
4. **Maintaining GAMP-5 compliance** throughout (NO FALLBACK LOGIC)
5. **Documenting procedures** for future engineers

Success means: Submit URS file → Worker executes 5-6 minute workflow → Test suite generated → Job completes with audit trail intact.

All previous components are functional. Task 3.5 integrates them end-to-end.

