# Tasks 3.5 & 3.6 Analysis: End-to-End Testing and OQ Generation Debugging

**Analysis Date:** 2025-11-17
**Status:** In Plan Mode (Ready for Review)
**Scope:** Comprehensive analysis of test suite generation failure and infinite retry loop

---

## Executive Summary

Task 3.5 (End-to-End Local Validation with Docker) achieved significant milestones but failed at the final test suite generation step. Task 3.6 was created to fix 4 critical issues blocking workflow completion:

1. **Missing `test_suite` key in workflow result** - Workflow completes but doesn't include generated test suite
2. **Missing `consultation_result` state** - Category 3 URS skips human consultation but workflow expects it
3. **Infinite retry loop** - Job retries infinitely instead of stopping after max retries
4. **Read-only filesystem for audit logs** - Cannot persist ALCOA+ compliance records

**Current Status:** Workflow executes successfully through GAMP-5 categorization, parallel agents, and OQ generation, but test suite is not serialized to the result dictionary returned to worker_executor.

---

## Task 3.5: End-to-End Local Validation Status

### What Works (✅ PASS)

| Component | Status | Evidence |
|-----------|--------|----------|
| Docker Stack | ✅ PASS | 4/4 containers healthy (postgres, localstack, api, worker) |
| FastAPI Job Submission | ✅ PASS | Clerk JWT authentication verified, jobs queued successfully |
| GAMP-5 Categorization | ✅ PASS | Category 3, 100% confidence (5.8s execution) |
| ChromaDB RAG Retrieval | ✅ PASS | 182 regulatory chunks retrieved (4.9s) |
| Parallel Agent Execution | ✅ PASS | Context, Research, SME agents all completed (258s total) |
| DeepSeek V3 Integration | ✅ PASS | OpenRouter API integration working (300+ tokens) |
| OpenAI Embeddings | ✅ PASS | Document vectorization successful |
| Volume Mounts & Development Workflow | ✅ PASS | 5-second code restart cycle (60-120x faster than rebuild) |
| Phoenix Observability | ✅ PASS | Traces captured and exportable (131+ spans expected) |

### What Fails (❌ CRITICAL)

| Component | Status | Error | Impact |
|-----------|--------|-------|--------|
| Test Suite Generation | ❌ FAIL | Missing `test_suite` key in result | Workflow completes but no output |
| Workflow Result Structure | ❌ FAIL | Keys: summary, metadata, categorization, planning, agent_coordination, oq_generation, workflow_results - **NO test_suite** | Worker extraction fails, job marked FAILED |
| ALCOA+ Audit Log Persistence | ⚠️ PARTIAL | Read-only filesystem on `main/logs/audit/` | Compliance audit trail not saved |
| Infinite Retry Loop | ⚠️ PARTIAL | Job retries infinitely after max_retries exceeded | Job never reaches FAILED state, queued forever |
| Consultation Result Handling | ⚠️ PARTIAL | Electronic signature fails for Category 3 (no consultation) | Warning logged but doesn't block completion |

---

## Task 3.6: Root Cause Analysis

### Issue 1: Missing Test Suite in Workflow Result

**Symptom:**
```
ERROR: Workflow completed but no test suite generated
Workflow result keys: ['summary', 'workflow_metadata', 'status', 'categorization',
'planning', 'agent_coordination', 'oq_generation', 'workflow_results']
MISSING: test_suite
```

**Root Cause Chain:**

1. **OQ Generation Workflow** (`main/src/agents/oq_generator/workflow.py`)
   - Line 425: Returns `OQTestSuiteEvent` with `test_suite: OQTestSuite` object
   - `OQTestSuite` is a Pydantic model with 194+ fields including test_cases
   - Format is **JSON/dict-serializable**, not YAML

2. **Unified Workflow Complete Step** (`main/src/core/unified_workflow.py:1952-2259`)
   - Line 1955: Receives `OQTestSuiteEvent` from OQ generation
   - Line 1976-1982: Extracts OQ results (suite_id, test_count, coverage, etc.)
   - Line 1998-2016: **Creates test_suite_data dict** with full test case information
   - **Line 2202: Creates `final_results` dict** but **ONLY includes oq_generation key** (line 2197)
   - **MISSING: Code to add test_suite key to final_results**
   - Line 2259: Returns StopEvent with final_results

**The Gap:**
```python
# What gets included in final_results:
"oq_generation": oq_results  # Contains metadata but NOT the actual test suite

# What is MISSING:
"test_suite": ?  # Should contain serialized test suite YAML or dict

# What exists but unused:
test_suite_data = {...}  # Lines 1998-2016, created but never added to final_results
```

**Worker Extraction Expectation** (`main/api/worker_executor.py:160`):
```python
test_suite_content = workflow_result.get("test_suite")  # Returns None
if not test_suite_content:
    raise RuntimeError("CRITICAL: Workflow completed but no test suite generated")
```

**Fix Required:**
In `complete_workflow` method (line 2140-2200), after creating test_suite_data, must convert to YAML and add to final_results:

```python
# After line 2016 (after test_suite_data is created)
import yaml

# Convert Pydantic model to dict for YAML serialization
test_suite_dict = ev.test_suite.model_dump(mode='json', exclude_none=True)

# Serialize to YAML format
test_suite_yaml = yaml.dump(
    test_suite_dict,
    default_flow_style=False,
    sort_keys=False,
    allow_unicode=True
)

# Add to final_results
final_results["test_suite"] = test_suite_yaml
```

---

### Issue 2: Missing `consultation_result` State

**Symptom:**
```
ERROR: Context retrieval failed for key consultation_result:
Path 'consultation_result' not found in state

WARNING: Electronic signature failed for categorization:
Context storage system failure for key 'consultation_result'
```

**Root Cause:**
- Line 159-209: `safe_context_get()` function uses `ctx.store.get(key)`
- Raises RuntimeError if key not found and no default provided
- GAMP-5 categorization workflow (line 1406+) creates `consultation_result` only for Category 4/5
- Category 3 URS skips human-in-the-loop, so `consultation_result` is never stored
- Electronic signature step (line 2030+) tries to access `consultation_result` unconditionally

**Current Behavior:**
- Line 1798-1801: `generate_oq_tests()` validates planning_event and categorization_result
- Does NOT validate consultation_result (correctly optional)
- Line 2030-2065: Electronic signature tries to access consultation_result via safe_context_get
- With no fallback, this triggers the RuntimeError

**Fix Required:**
Make consultation_result optional with explicit handling:

```python
# In complete_workflow, before electronic signature:
consultation_result = await safe_context_get(ctx, "consultation_result", None)

if consultation_result is None:
    logger.info("No human consultation required for Category 3 (configured product)")
    # Continue without consultation context
else:
    # Use consultation_result for signature binding
    additional_context["consultation_approved"] = True
```

---

### Issue 3: Infinite Retry Loop

**Symptom:**
```
WARNING: Job 67077789... retry 1/3 after 1s: ...
WARNING: Job 67077789... retry 2/3 after 2s: ...
WARNING: Job 67077789... retry 3/3 after 4s: ...
ERROR: Job 67077789... failed after 3 retries
[Then retries start again infinitely - never reaches FAILED status]
```

**Root Cause Analysis:**
Looking at `main/api/worker.py` lines 175-224:

```python
while retry_count <= max_retries:  # Line 175: Critical bug!
    try:
        result = await _execute_workflow(job, executor)
        return True  # Success - exits loop

    except Exception as e:
        retry_count += 1

        if retry_count > max_retries:  # Line 210: Check happens AFTER increment
            return False  # Failure - should exit

        # Exponential backoff and retry
        await asyncio.sleep(backoff_delay)
        # IMPLICIT: Loop continues, but only if retry_count <= max_retries

return False  # Line 224: Should not reach, but does in some edge cases
```

**The Bug:**
- `while retry_count <= max_retries` with `max_retries = 3`
- Iteration 1: retry_count=0, increment to 1, check `1 > 3` (false), sleep, continue
- Iteration 2: retry_count=1, increment to 2, check `2 > 3` (false), sleep, continue
- Iteration 3: retry_count=2, increment to 3, check `3 > 3` (false), sleep, continue
- Iteration 4: retry_count=3, increment to 4, check `4 > 3` (true), return False

**This logic is correct!** But the infinite retry happens AFTER the function returns.

**Root Cause - In process_job_worker()** (lines 22-145):
Looking at the workflow:
1. Line 91-96: `_process_job_with_retries()` returns False after max retries
2. Line 100-132: Updates job status to FAILED
3. Line 135: `job_queue.task_done()` marks the queue task done
4. **Line 59: `while True` - loops forever**
5. **Line 62: `await job_queue.get()` - blocks waiting for next job**

**The actual infinite retry likely comes from:**
- Worker process exits after max retries
- Docker container restart policy: `restart: unless-stopped`
- Container restarts, picks up same job from queue again
- Or: Job is re-added to queue by a retry mechanism elsewhere

**Investigation Steps Needed:**
1. Check if failed jobs are being re-queued automatically
2. Check if there's an external retry mechanism in `main/api/app.py` lifespan
3. Check SQS queue processing - does task_done() properly remove message?

**Likely Fix:**
```python
# In main/api/worker.py after job marked as FAILED (line 117-132):
# Ensure job is NOT re-queued
logger.info(f"Job {job_id} marked as FAILED - marking queue task done")
job_queue.task_done()  # Already at line 135

# If using SQS (not in-memory queue), must delete message from queue:
if hasattr(job, 'sqs_receipt_handle'):
    await sqs_client.delete_message(
        QueueUrl=queue_url,
        ReceiptHandle=job.sqs_receipt_handle
    )
```

---

### Issue 4: ALCOA+ Audit Log Read-Only Filesystem

**Symptom:**
```
Warning: Failed to persist ALCOA+ record:
[Errno 30] Read-only file system: 'main/logs/audit/alcoa_records_20251117.json'
```

**Root Cause:**
In `docker-compose.dev.yml` line 220 and 269:
```yaml
volumes:
  - ./main:/app/main:ro  # Read-only flag `:ro`
```

The entire `main` directory is mounted as read-only, including `main/logs/audit/`.

When workflow tries to write audit logs (line 2068-2119 in unified_workflow.py):
```python
alcoa_validator.create_data_record(...)  # Attempts to write to main/logs/audit/
```

The file system rejects the write with "Read-only file system" error.

**Current Status:**
- Line 2129: Error caught as warning, execution continues
- BUT: Compliance audit trail is not persisted (GAMP-5 violation)

**Fix Required:**
In `docker-compose.dev.yml`, add separate writable mount for logs:

```yaml
volumes:
  # Read-only code mount (prevents accidental modification)
  - ./main:/app/main:ro

  # Writable logs mount (ALCOA+ compliance requires audit trail persistence)
  - ./main/logs:/app/main/logs:rw

  # Other mounts remain unchanged
  - output-data:/app/output
  - chroma-data:/app/chroma_db
```

Note: This must be applied to BOTH `api` and `worker` services (lines 220 and 269).

---

## Current Workflow Architecture - Execution Flow

### Step-by-Step Flow (Task 3.5 Successful Execution)

```
1. API receives URS file upload
   └─> FastAPI POST /jobs endpoint
   └─> Validates Clerk JWT token
   └─> Stores URS to local filesystem
   └─> Creates JobRecord in repository
   └─> Returns job_id to client

2. Background worker picks up job
   └─> Polling loop in main/api/app.py (lifespan event)
   └─> Calls process_job_worker() in main/api/worker.py
   └─> Gets job from queue, updates status to PROCESSING

3. Worker executes workflow
   └─> _execute_workflow() in main/api/worker.py:227-289
   └─> Creates WorkflowExecutor() instance
   └─> Calls execute_workflow() in main/api/worker_executor.py:69-214

4. Workflow Executor (main/api/worker_executor.py)
   └─> Loads URS content from storage
   └─> Creates UnifiedTestGenerationWorkflow instance
   └─> Calls await workflow.run(document_path=...) [5-6 minutes]
   └─> Gets workflow_result dict
   └─> Extracts test_suite_content from result["test_suite"]  ❌ FAILS HERE

5. Unified Workflow (main/src/core/unified_workflow.py)
   └─> Step 1: start_unified_workflow() - Ingests URS document
   └─> Step 2: run_categorization_workflow() - GAMP-5 categorization ✅
   └─> Step 3: run_planning_workflow() - Creates test plan ✅
   └─> Step 4: execute_context_agent() - RAG retrieval ✅
   └─> Step 5: execute_research_agent() - Pattern analysis ✅
   └─> Step 6: execute_sme_agent() - SME consultation ✅
   └─> Step 7: sign_agent_results() - Electronic signature ✅
   └─> Step 8: generate_oq_tests() - OQ test generation ✅
       └─> Calls OQGenerationWorkflow.run()
       └─> Returns OQTestSuiteEvent with OQTestSuite model
   └─> Step 9: complete_workflow() - Compiles final results ⚠️ INCOMPLETE
       └─> Receives OQTestSuiteEvent
       └─> Extracts oq_results (metadata)
       └─> Creates test_suite_data dict (full test cases)
       └─> Creates final_results dict
       └─> ADDS: summary, metadata, categorization, planning, agent_coordination, oq_generation
       └─> MISSING: test_suite (the actual generated tests as YAML string)
       └─> Returns StopEvent(result=final_results)

6. Worker Executor expects (main/api/worker_executor.py:160-170)
   └─> test_suite_content = workflow_result.get("test_suite")
   └─> ❌ Returns None
   └─> Raises RuntimeError("CRITICAL: Workflow completed but no test suite generated")

7. Worker catches exception
   └─> Updates job.error_message
   └─> Increments job.retry_count
   └─> Checks: retry_count > max_retries (4 > 3) ✅ True
   └─> Returns False from _process_job_with_retries()
   └─> Job marked as FAILED
   └─> job_queue.task_done()
   └─> Loop continues (while True)
   └─> Waits for next job from queue

8. Infinite Retry Loop (Likely Cause)
   └─> If same job_id is re-queued by external mechanism
   └─> Or if worker container restarts automatically
   └─> Then steps 2-7 repeat infinitely
```

---

## Langfuse Integration Analysis

**Current Status:** Phoenix observability is working, Langfuse not yet integrated

### What's Instrumented (✅ WORKING)

| Component | Status | Evidence |
|-----------|--------|----------|
| Phoenix Setup | ✅ WORKING | `setup_phoenix()` called in workflow init (line 498) |
| @observe Decorators | ✅ WORKING | `WorkflowExecutor.execute_workflow()` has `@observe` (line 68) |
| Span Capture | ✅ WORKING | 131+ spans expected, trace export working |
| Phoenix Tracing | ✅ WORKING | Traces captured to Phoenix server (port 6006) |

### Langfuse Integration Gaps (⚠️ NOT DONE)

**Status:** Langfuse implementation was deferred to Task 2.3 (which completed), but may not be fully integrated with this workflow.

**Current Implementation** (from Task 2.3):
- Backend LangFuse instrumentation in `main/api/observability.py` ✅
- Frontend LangFuse dashboard in `main/frontend/pages/observability.tsx` ✅
- API route `/api/langfuse/summary` with HTTP Basic Auth ✅

**Missing for Unified Workflow:**
- Callback handler integration with UnifiedWorkflow (would need LlamaIndex LangfuseCallbackHandler)
- Trace metadata injection (GAMP-5 required fields in each span)
- ALCOA+ attribute mapping to Langfuse trace context

**Audit Trail Traceability:** Currently handled by ALCOA+ validator in unified_workflow.py, which persists to local JSON files. This is sufficient for Task 3.5/3.6 but would need Langfuse for production deployment.

---

## Implementation Priorities - Task 3.6

### Phase 1: CRITICAL (Fix workflow result) - 15 minutes

**File:** `main/src/core/unified_workflow.py`, method `complete_workflow()` (lines 1951-2259)

**Action:** Add test_suite YAML serialization to final_results

**Code Location:** After line 2016 (after test_suite_data creation), before line 2140

```python
# CRITICAL FIX: Serialize test suite to YAML for worker extraction
import yaml

# Convert OQTestSuite Pydantic model to dict
test_suite_dict = ev.test_suite.model_dump(mode='json', exclude_none=True)

# Serialize to YAML format (what worker_executor expects)
try:
    test_suite_yaml = yaml.dump(
        test_suite_dict,
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True
    )
except Exception as yaml_error:
    self.logger.error(f"Test suite YAML serialization failed: {yaml_error}")
    raise RuntimeError(f"Cannot serialize test suite to YAML: {yaml_error}") from yaml_error

# Add to final_results dict (worker_executor expects this key)
final_results["test_suite"] = test_suite_yaml
self.logger.info(f"✅ Test suite YAML generated: {len(test_suite_yaml)} characters")
```

**Why:** Worker extraction (worker_executor.py:160) explicitly expects `workflow_result.get("test_suite")`. Without this key, the workflow appears to complete successfully but worker fails with "CRITICAL: Workflow completed but no test suite generated".

---

### Phase 2: IMPORTANT (Fix consultation_result optional) - 10 minutes

**File:** Same as above, method `complete_workflow()`

**Action:** Make consultation_result optional before electronic signature

**Code Location:** Before line 2030 (before electronic signature), around line 2140

```python
# Make consultation_result optional for Category 3
consultation_result = await safe_context_get(ctx, "consultation_result", None)

if consultation_result is None:
    # Category 3 (configured product) skips human consultation - this is expected
    if categorization_result and categorization_result.gamp_category.value == 3:
        self.logger.info(
            "No human consultation required for Category 3 (configured product) - "
            "electronic signature will proceed without consultation context"
        )
    else:
        self.logger.warning(
            "consultation_result not found - workflow may have skipped consultation step"
        )
```

**Why:** Currently, safe_context_get raises RuntimeError if key not found and no default provided. Category 3 URS doesn't have consultation_result (it's not required), so this triggers a warning that blocks completion.

---

### Phase 3: ESSENTIAL (Fix audit log persistence) - 5 minutes

**File:** `docker-compose.dev.yml`

**Action:** Add writable volume mount for logs directory to both API and worker services

**Changes Needed:**

**API service (around line 217-224):**
```yaml
volumes:
  # Read-only code mount (prevents accidental modification)
  - ./main:/app/main:ro

  # Writable logs mount (ALCOA+ compliance requires audit trail persistence)
  - ./main/logs:/app/main/logs:rw

  # Shared volumes for storage adapter and vector store
  - output-data:/app/output          # LocalStorageAdapter base path
  - chroma-data:/app/chroma_db       # ChromaDB persistence
```

**Worker service (around line 266-273):**
```yaml
volumes:
  # Read-only code mount (prevents accidental modification)
  - ./main:/app/main:ro

  # Writable logs mount (ALCOA+ compliance requires audit trail persistence)
  - ./main/logs:/app/main/logs:rw

  # Shared volumes (same as API for storage adapter consistency)
  - output-data:/app/output
  - chroma-data:/app/chroma_db
```

**After modification, restart containers:**
```bash
docker-compose -f docker-compose.dev.yml down
docker-compose -f docker-compose.dev.yml up -d
```

**Why:** Audit logs are written to `main/logs/audit/alcoa_records_YYYYMMDD.json` for GAMP-5 compliance. The read-only mount prevents persistence, violating ALCOA+ requirements (Enduring, Available principles).

---

### Phase 4: RESEARCH (Investigate infinite retry) - 20 minutes

**Files to Investigate:**
1. `main/api/worker.py` - Retry logic and queue management
2. `main/api/app.py` - Lifespan event and background worker startup
3. SQS polling mechanism - If using LocalStack SQS, check message handling

**Questions to Answer:**
1. Is `job_queue.task_done()` properly removing messages from queue?
2. Is there an external retry mechanism re-queueing failed jobs?
3. Does the worker container restart on crash? (`restart: unless-stopped`)
4. If using SQS (not in-memory queue), is `delete_message()` being called?

**Likely Fix:**
Ensure failed jobs are marked as FAILED and not re-processed:
```python
# In process_job_worker() after job marked FAILED (line 117-132):
# Explicitly mark job as done and prevent re-queueing
job_queue.task_done()  # Already at line 135

# If using SQS, delete message from queue to prevent redelivery
if hasattr(job, 'sqs_receipt_handle'):
    try:
        await sqs_client.delete_message(
            QueueUrl=queue_url,
            ReceiptHandle=job.sqs_receipt_handle
        )
        logger.info(f"Deleted failed job {job_id} from SQS queue")
    except Exception as e:
        logger.error(f"Failed to delete job from SQS: {e}")
```

---

## Key Files & Code Sections

### Core Workflow Files

| File | Purpose | Critical Sections |
|------|---------|-------------------|
| `main/src/core/unified_workflow.py` | Master workflow orchestration | Lines 1951-2259: complete_workflow() method |
| `main/api/worker_executor.py` | Workflow execution wrapper | Lines 150-170: Test suite extraction |
| `main/api/worker.py` | Background job processor | Lines 175-224: Retry logic |
| `main/src/agents/oq_generator/workflow.py` | OQ test generation | Lines 87-430: Test suite generation |
| `main/src/agents/oq_generator/models.py` | OQTestSuite Pydantic model | Lines 103-200: Test suite structure |
| `docker-compose.dev.yml` | Container orchestration | Lines 217-224, 266-273: Volume mounts |

### Critical Code Sections to Fix

1. **Test Suite Serialization**
   - **File:** `unified_workflow.py:1951-2259`
   - **Method:** `complete_workflow()`
   - **Issue:** Missing `test_suite` key in final_results
   - **Action:** Serialize OQTestSuite to YAML after line 2016

2. **Consultation Result Handling**
   - **File:** `unified_workflow.py:1951-2259`
   - **Method:** `complete_workflow()`
   - **Issue:** Electronic signature fails when consultation_result is None
   - **Action:** Add optional handling before line 2030

3. **Audit Log Persistence**
   - **File:** `docker-compose.dev.yml`
   - **Services:** `api` (line 220), `worker` (line 269)
   - **Issue:** Read-only mount prevents ALCOA+ log writing
   - **Action:** Add separate writable volume mount for `./main/logs`

4. **Infinite Retry Loop**
   - **File:** `main/api/worker.py:22-145`
   - **Function:** `process_job_worker()`
   - **Issue:** Unclear if failed jobs are re-queued
   - **Action:** Investigate SQS message handling and container restart policy

---

## Expected Behavior After Fixes

### Success Criteria

When Task 3.6 is complete, the workflow should:

1. ✅ Execute end-to-end: URS → GAMP-5 → Agents → OQ Generation → Result
2. ✅ Return workflow_result with `test_suite` key containing YAML
3. ✅ Test suite is saved to `/app/output/{job_id}/test_suite.yaml`
4. ✅ Job status transitions: `pending` → `processing` → `completed`
5. ✅ No errors for Category 3 (consultation_result optional)
6. ✅ ALCOA+ audit logs persisted to `main/logs/audit/`
7. ✅ No infinite retries (max 3 retries, then FAILED status)
8. ✅ Execution time: 5-6 minutes for Category 3 URS

### Test Case: Category 3 URS

```bash
# Submit Category 3 URS
curl -X POST http://localhost:8080/jobs \
  -H "Authorization: Bearer $CLERK_TOKEN" \
  -F "file=@datasets/urs_corpus_v2/category_3/URS-020.md"

# Expected workflow:
# 0:00 - Job submitted (pending)
# 0:30 - GAMP-5 categorization complete (Category 3, 100% confidence)
# 1:30 - RAG retrieval complete (182 chunks)
# 3:00 - Parallel agents complete (context, research, SME)
# 5:00 - OQ test generation complete (50-100 tests)
# 5:30 - Job completed (status: completed, test_suite saved)

# Verify results
curl http://localhost:8080/jobs/$JOB_ID | jq .status
# Expected: "completed"

docker exec pharma-api-dev cat /app/output/$JOB_ID/test_suite.yaml | head -30
# Expected: YAML with test_cases array

ls -lah /app/output/$JOB_ID/
# Expected: test_suite.yaml file with size > 1KB
```

---

## Next Steps for Task Executor

When implementing Task 3.6, follow this sequence:

1. **Read this analysis** to understand all 4 issues
2. **Phase 1 - Critical:** Fix test_suite serialization in unified_workflow.py
3. **Phase 2 - Important:** Fix consultation_result optional handling
4. **Phase 3 - Essential:** Fix audit log volume mount in docker-compose.dev.yml
5. **Phase 4 - Research:** Investigate infinite retry mechanism
6. **Restart services:** `docker-compose down && docker-compose up -d`
7. **Test with Category 3 URS:** Verify 5-6 minute execution and no test_suite errors
8. **Verify audit logs:** Check `main/logs/audit/alcoa_records_*.json` exists
9. **Verify no infinite retries:** Monitor logs for "Job X completed successfully"
10. **Collect evidence:** Screenshots, logs, test suite YAML sample

---

## References

**Task Definitions:**
- Task 3.5: `PRPs/tasks/3.5-end-to-end-local-validation.md`
- Task 3.6: `PRPs/tasks/3.6-fix-test-generation.md`

**Workflow Architecture:**
- `main/src/core/unified_workflow.py` (2,300+ lines)
- `main/src/agents/oq_generator/workflow.py` (450+ lines)

**Previous Task Results:**
- `.claude/state/prp-workflow-state.md` (lines 18-132: Task 3.5 status)

**Compliance Standards:**
- GAMP-5 categorization (lines 61, 365-370)
- ALCOA+ audit trail (lines 2067-2119)
- 21 CFR Part 11 (lines 472-487)

---

**Analysis Completed:** 2025-11-17
**Status:** Ready for task-executor review and implementation
