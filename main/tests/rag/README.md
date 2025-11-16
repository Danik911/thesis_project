# RAG Workflow Test Suite

## Overview

Comprehensive test harness for validating the RAG (Retrieval-Augmented Generation) workflow in the pharmaceutical test generation system.

**GAMP-5 Classification:** Category 5 (Custom test scripts, low risk)

**Purpose:** Validate document ingestion, vectorization, and retrieval components using LocalStack S3 and PostgreSQL pgvector.

## Test Architecture

### Two-Tier Storage

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

## Test Modules

### `conftest.py` - Shared Fixtures
- `wait_for_localstack()` - Ensures LocalStack ready before tests
- `localstack_s3_bucket()` - Creates/cleans S3 bucket per test
- `pgvector_store()` - PostgreSQL pgvector adapter setup
- `sample_documents()` - Pharmaceutical sample documents
- `mock_llm()` - MockLLM for deterministic testing
- `audit_context()` - ALCOA+ audit trail context
- `compliance_evidence_dir()` - Evidence folder setup

### `test_ingestion.py` - S3 Document Upload
- `test_upload_single_document_to_s3` - Single document upload
- `test_upload_batch_documents` - Batch upload (10 documents)
- `test_fail_on_missing_bucket` - NO FALLBACK LOGIC validation
- `test_cleanup_verification` - Cleanup reliability test

### `test_vectorization.py` - Embedding Storage
- `test_add_documents_to_pgvector` - Document vectorization
- `test_vector_dimensions_correct` - Embedding dimension validation (1536)
- `test_batch_vectorization` - Batch embedding generation
- `test_metadata_preserved_in_vectors` - GAMP-5 metadata preservation
- `test_fail_on_invalid_documents` - NO FALLBACK LOGIC validation

### `test_retrieval.py` - Vector Similarity Search
- `test_retrieval_returns_top_k` - top_k limit validation
- `test_retrieval_semantic_relevance` - Semantic accuracy
- `test_retrieval_with_metadata_filter` - GAMP-5 filtering
- `test_empty_vector_store_handling` - Empty store behavior
- `test_fail_on_invalid_query` - NO FALLBACK LOGIC validation
- `test_retrieval_score_ordering` - Score sorting verification

### `test_e2e.py` - End-to-End Integration
- `test_full_rag_pipeline` - Complete S3 → vectorize → query workflow
- `test_query_with_mock_llm_deterministic` - Mock LLM consistency
- `test_phoenix_trace_capture` - Observability trace export (local only)
- `test_alcoa_plus_audit_trail` - ALCOA+ compliance verification
- `test_no_real_bedrock_credentials_used` - Security validation

## Running Tests

### Prerequisites
1. Docker Compose stack running (Task 3.2):
   ```bash
   docker-compose -f docker-compose.dev.yml up -d
   ```

2. Services healthy:
   - postgres (pgvector enabled)
   - localstack (S3 available)

### Execute Test Suite

```bash
# All RAG tests
pytest main/tests/rag/ -v

# Specific test module
pytest main/tests/rag/test_ingestion.py -v

# With coverage
pytest main/tests/rag/ --cov=main/src/adapters --cov-report=html

# With Phoenix tracing (local environment)
ENVIRONMENT=local pytest main/tests/rag/ -v -s

# Specific test
pytest main/tests/rag/test_retrieval.py::test_retrieval_returns_top_k -v
```

### Environment Variables

```bash
# LocalStack configuration
LOCALSTACK_ENDPOINT=http://127.0.0.1:4566  # Default (avoids IPv6 issues on Windows)

# PostgreSQL configuration
VECTOR_STORE_CONNECTION_STRING=postgresql://postgres:devpassword@127.0.0.1:5432/testgen

# Environment mode (controls Phoenix tracing)
ENVIRONMENT=local  # Enable observability
```

## Test Fixtures

### Sample Documents (`fixtures/`)
- `sample_protocol.txt` - Drug release workflow protocol (GAMP-5 Category 5)
- `test_urs.txt` - User Requirements Specification
- `test_acceptance_criteria.txt` - Test acceptance criteria document

All fixtures include:
- GAMP-5 metadata
- ALCOA+ compliant structure
- Pharmaceutical domain content

## Compliance Evidence

### Output Structure
```
compliance_evidence/
├── test_logs/
│   ├── test-audit-{uuid}.json       # ALCOA+ audit trail
│   └── pytest-output-{timestamp}.txt # Test execution log
├── traces/
│   └── phoenix-trace-{timestamp}.json  # Observability trace (local only)
└── coverage/
    └── htmlcov/                      # Code coverage HTML report
```

### ALCOA+ Audit Trail
Each test run generates audit trail with:
- **Attributable:** User ID (`test_harness_automated`)
- **Legible:** Human-readable JSON format
- **Contemporaneous:** Timestamp at execution
- **Original:** Unchanged first-run results
- **Accurate:** Matches actual test outcomes
- **Complete:** All required fields present
- **Consistent:** Standard format across tests
- **Enduring:** Saved to compliance_evidence/
- **Available:** Accessible for audits

## GAMP-5 Compliance

### Test Harness Classification
- **Category:** 5 (Custom test scripts, low risk)
- **Validation:** Test code version controlled (Git)
- **Documentation:** This README + inline docstrings
- **Evidence:** Audit trails + coverage reports

### Required Documentation
- [x] Test purpose and scope defined
- [x] Test environment documented (Docker Compose)
- [x] Test data fixed/known (sample documents)
- [x] Pass/fail criteria explicit (assertions)
- [x] Evidence preserved (compliance_evidence/)
- [x] Version controlled (Git)

## NO FALLBACK LOGIC Enforcement

**CRITICAL:** All tests validate zero-tolerance NO FALLBACK LOGIC policy:

### Validation Tests
- `test_fail_on_missing_bucket` - S3 errors propagate
- `test_fail_on_invalid_documents` - Empty documents rejected
- `test_fail_on_invalid_query` - Invalid queries fail loudly
- `test_no_real_bedrock_credentials_used` - No credential leakage

### Requirements
- ✅ All errors throw explicit exceptions
- ✅ No default values masking missing data
- ✅ Full stack traces on all failures
- ✅ Diagnostic information in all errors
- ❌ No silent failures or swallowed exceptions

## Coverage Targets

### Minimum Requirements
- **Ingestion modules:** ≥80%
- **Vectorization modules:** ≥80%
- **Retrieval modules:** ≥80%

### Measurement
```bash
pytest main/tests/rag/ --cov=main/src/adapters --cov-report=html --cov-report=term
```

Coverage report: `compliance_evidence/coverage/htmlcov/index.html`

## Common Issues

### LocalStack Not Ready
**Error:** `ConnectionError: Could not connect to LocalStack`

**Solution:**
```bash
# Check LocalStack status
docker ps | grep localstack

# Restart if unhealthy
docker-compose -f docker-compose.dev.yml restart localstack

# Wait for readiness
until aws s3 ls --endpoint-url http://localhost:4566; do sleep 1; done
```

### PostgreSQL pgvector Extension Missing
**Error:** `RuntimeError: pgvector extension not found`

**Solution:**
```bash
# Check extension
docker exec pharma-postgres-dev psql -U postgres -d testgen -c "SELECT * FROM pg_extension WHERE extname='vector';"

# Recreate if missing
docker-compose -f docker-compose.dev.yml down -v
docker-compose -f docker-compose.dev.yml up -d
```

### Test Cleanup Failures
**Error:** `RuntimeError: Failed to cleanup S3 bucket`

**Solution:**
- Cleanup errors intentionally fail loudly (NO FALLBACK LOGIC)
- Manual cleanup: `aws s3 rb s3://bucket-name --force --endpoint-url http://localhost:4566`
- Check logs for root cause (permissions, network, etc.)

## Development Notes

### Adding New Tests
1. Follow existing test module patterns
2. Use `audit_context` fixture for ALCOA+ compliance
3. Implement NO FALLBACK LOGIC validation
4. Add docstrings with Args/Verifies sections
5. Update this README with test description

### Fixture Modifications
- All fixtures in `conftest.py`
- Cleanup in `finally` blocks (required)
- Never swallow cleanup errors
- Document all fixture dependencies

### Phoenix Tracing (Optional)
- Only enabled if `ENVIRONMENT=local`
- Trace exports saved to `compliance_evidence/traces/`
- Added to `.gitignore` (no production leakage)
- Manual export for compliance evidence

## Regulatory Alignment

### GAMP-5
- Category 5 test harness (custom scripts)
- Risk assessment: Minimal (tests validate, not execute regulated code)
- Validation package: Documentation + evidence

### ALCOA+ Principles
- All test execution data ALCOA+ compliant
- Audit trails automatically generated
- Evidence preserved for regulatory inspection

### 21 CFR Part 11
- Test harness does NOT require electronic signatures
- Audit trail sufficient for test evidence
- Production system (tested code) requires Part 11 compliance

## Revision History

| Version | Date       | Author       | Changes                        |
|---------|------------|--------------|--------------------------------|
| 1.0     | 2025-11-15 | task-executor | Initial test harness implementation |

## Next Steps

After test execution:
1. Review coverage reports (`compliance_evidence/coverage/htmlcov/`)
2. Analyze audit trails (`compliance_evidence/test_logs/`)
3. Export Phoenix traces if needed (`compliance_evidence/traces/`)
4. Attach evidence to GAMP-5 validation package
5. QA manager review and approval
6. Archive for 7-year retention period
