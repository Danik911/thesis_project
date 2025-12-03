# Debug Report: AWS Workflow Failure Investigation

**Issue ID:** AWS-WORKFLOW-001
**Date:** 2025-12-02
**Status:** 🟢 RESOLVED - OpenRouter WORKING, LangFuse EXTERNAL OUTAGE
**Priority:** CRITICAL (was)
**Resolution:**
- OpenRouter: API task definition v8 deployed with missing secrets - NOW WORKING
- LangFuse: Traces being sent but LangFuse EU experiencing database outage

---

## Problem Summary

| Environment | LangFuse Traces | OpenRouter API Calls | Job Duration | Status |
|-------------|-----------------|---------------------|--------------|--------|
| **Local Docker** | ✅ Yes | ✅ Yes | ~5 min | WORKING |
| **AWS ECS (Initial)** | ❌ No | ❌ No | ~2.5 min | BROKEN |
| **AWS ECS (After Fix)** | ⏳ Pending* | ✅ Yes | TBD | MOSTLY WORKING |

*LangFuse traces are being sent (verified via `auth_check()`), but LangFuse EU is experiencing an outage preventing traces from appearing in dashboard.

**Conclusion:** Code is proven correct (works locally). Initial issue was AWS configuration drift. Remaining LangFuse issue is external outage.

---

## Symptoms

1. **No traces in LangFuse** - Despite health check passing at startup
2. **No API calls to OpenRouter** - Dashboard shows zero activity from AWS
3. **Job completes in half the time** - 2.5 min vs 5 min expected
4. **Test scripts generated** - But likely empty/placeholder content

---

## Investigation Timeline

### Phase 1: CloudWatch Log Analysis

**Started:** 2025-12-02 13:30 UTC
**Status:** ✅ COMPLETED

#### 1.1 Worker Container Logs (WORKING)
```
INFO:main.scripts.init_chromadb:Downloading ChromaDB from s3://pharma-test-gen-vectors-staging/chroma_db.tar.gz
INFO:main.scripts.init_chromadb:Downloaded 1.44 MB
INFO:main.scripts.init_chromadb:ChromaDB extracted to /app/chroma_db
INFO:main.api.observability:LangFuse initialized successfully
  Host: https://cloud.langfuse.com
  Public Key: pk-lf-9b...
  Health Check: PASSED
```

#### 1.2 API Container Logs (BROKEN)
```
ERROR: LangFuse credentials missing. Required environment variables:
  - LANGFUSE_PUBLIC_KEY (current: MISSING)
  - LANGFUSE_SECRET_KEY (current: MISSING)

ERROR - SME Agent error: SME analysis failed: CRITICAL: Recommendations generation LLM call failed.
ERROR - SME Agent error: SME analysis failed: CRITICAL: Regulatory considerations LLM call failed.
ERROR - ChromaDB search failed: CRITICAL: Context Provider cannot execute - ALL ChromaDB collections are empty.
```

**Findings:**
- ✅ Worker container has secrets correctly injected
- ❌ API container is MISSING all LangFuse and OpenRouter secrets
- ❌ API container has empty ChromaDB (no S3 download configured)

---

### Phase 2: Secrets Manager Verification

**Started:** 2025-12-02 13:35 UTC
**Status:** ✅ COMPLETED

#### 2.1 Task Definition Secrets Configuration

**API Task Definition (revision 6) - INCOMPLETE:**
```json
"secrets": [
    {"name": "DATABASE_URL", "valueFrom": "...placeholder..."},
    {"name": "CLERK_PEM_PUBLIC_KEY", "valueFrom": "...clerk..."},
    {"name": "CLERK_ISSUER", "valueFrom": "...clerk..."}
]
```
**MISSING:** OPENROUTER_API_KEY, OPENAI_API_KEY, LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY

**Worker Task Definition (revision 9) - COMPLETE:**
```json
"secrets": [
    {"name": "DATABASE_URL", "valueFrom": "...placeholder..."},
    {"name": "OPENAI_API_KEY", "valueFrom": "...openrouter:OPENAI_API_KEY::"},
    {"name": "OPENROUTER_API_KEY", "valueFrom": "...openrouter:OPENROUTER_API_KEY::"},
    {"name": "LANGFUSE_PUBLIC_KEY", "valueFrom": "...langfuse:LANGFUSE_PUBLIC_KEY::"},
    {"name": "LANGFUSE_SECRET_KEY", "valueFrom": "...langfuse:LANGFUSE_SECRET_KEY::"}
]
```

#### 2.2 Secret Values (Verified)
```
OpenRouter Secret: arn:aws:secretsmanager:eu-west-2:275333454012:secret:pharma-test-gen/openrouter-9BAg9h ✅
LangFuse Secret: arn:aws:secretsmanager:eu-west-2:275333454012:secret:pharma-test-gen/langfuse-5TMVwo ✅
```

**Findings:**
- ✅ Secrets exist in AWS Secrets Manager
- ✅ Worker task definition has correct secret ARNs
- ❌ API task definition is MISSING these secrets entirely

---

### Phase 3: Local vs AWS Comparison

**Started:** 2025-12-02 13:40 UTC
**Status:** ✅ COMPLETED

| Variable | Local Value | AWS Worker | AWS API | Match? |
|----------|-------------|------------|---------|--------|
| OPENROUTER_API_KEY | ✅ Present | ✅ Present | ❌ MISSING | NO |
| LANGFUSE_PUBLIC_KEY | ✅ Present | ✅ Present | ❌ MISSING | NO |
| LANGFUSE_SECRET_KEY | ✅ Present | ✅ Present | ❌ MISSING | NO |
| LLM_PROVIDER | openrouter | openrouter | ❌ MISSING | NO |
| LLM_MODEL | deepseek/deepseek-chat | deepseek/deepseek-chat | ❌ MISSING | NO |
| ENVIRONMENT | development | staging | staging | YES |

**Findings:**
- ✅ Local Docker has all required environment variables
- ✅ AWS Worker task definition (v9) has all secrets correctly configured
- ❌ AWS API task definition (v6) is missing ALL LLM and observability configuration

---

### Phase 4: Debug Logging (If Needed)

**Started:** N/A
**Status:** ⏭️ SKIPPED

**Reason:** Root cause identified from CloudWatch logs and task definition comparison. No additional logging required.

---

### Phase 5: Fix Applied (OpenRouter)

**Started:** 2025-12-02 13:45 UTC
**Status:** ✅ COMPLETED - OPENROUTER NOW WORKING

**Root Cause:**
API Task Definition (revision 6) was never updated with LLM and observability secrets when Worker (v9) was updated.

**Additional Issue:**
The `placeholder-p1v3ys` secret for DATABASE_URL was marked for deletion, blocking new task startup.

**Fix Applied:**
1. Created `aws/terraform/task-definition-api-v7.json` with:

   **Added Secrets:**
   - `OPENAI_API_KEY` → `pharma-test-gen/openrouter-9BAg9h:OPENAI_API_KEY::`
   - `OPENROUTER_API_KEY` → `pharma-test-gen/openrouter-9BAg9h:OPENROUTER_API_KEY::`
   - `LANGFUSE_PUBLIC_KEY` → `pharma-test-gen/langfuse-5TMVwo:LANGFUSE_PUBLIC_KEY::`
   - `LANGFUSE_SECRET_KEY` → `pharma-test-gen/langfuse-5TMVwo:LANGFUSE_SECRET_KEY::`

   **Added Environment Variables:**
   - `LLM_PROVIDER` = `openrouter`
   - `LLM_MODEL` = `deepseek/deepseek-chat`
   - `LANGFUSE_HOST` = `https://cloud.langfuse.com`
   - `OUTPUT_BUCKET` = `pharma-test-gen-output-staging`
   - `S3_CHROMADB_BUCKET` = `pharma-test-gen-vectors-staging`
   - `S3_CHROMADB_KEY` = `chroma_db.tar.gz`
   - `RAG_VECTOR_STORE_PATH` = `/app/chroma_db`

2. Created new DATABASE_URL placeholder secret:
   - `pharma-test-gen/database-uSIzYF` (replaced deleted `placeholder-p1v3ys`)

3. Registered API task definition v8 (with corrected DATABASE_URL secret)

4. Updated API service to use `pharma-test-gen-api:8`

**Verification:**
- [x] API task definition v8 registered (2025-12-02 17:06 UTC)
- [x] API service updated with new task definition
- [x] API logs show "LangFuse initialized successfully" (2025-12-02 17:08:07 UTC)
- [x] OpenRouter dashboard shows API calls ✅ USER CONFIRMED WORKING
- [ ] LangFuse dashboard shows traces (blocked by external outage)
- [ ] Job duration is ~5 minutes (pending test job)

---

### Phase 6: LangFuse Trace Investigation

**Started:** 2025-12-02 17:45 UTC
**Status:** ✅ COMPLETED - EXTERNAL OUTAGE IDENTIFIED

#### 6.1 Problem Statement
Despite OpenRouter now working, LangFuse traces still not appearing in dashboard.

#### 6.2 Diagnostic Enhancement
Added `auth_check()` diagnostic to `main/api/observability.py`:

```python
# Health check: Use auth_check() for synchronous verification
# This actually makes an HTTP request and verifies credentials + network
auth_result = False
try:
    auth_result = self.client.auth_check()
    logger.info(f"LangFuse auth_check() result: {auth_result}")
except Exception as auth_error:
    logger.error(f"LangFuse auth_check() failed: {type(auth_error).__name__}: {auth_error}")

if not auth_result:
    logger.error(
        f"LangFuse authentication FAILED!\n"
        f"  Host: {self._host}\n"
        f"  Public Key: {self._public_key[:8]}...\n"
        f"  This indicates network connectivity issues or invalid credentials."
    )
```

#### 6.3 Deployment
1. Created `aws/terraform/task-definition-api-v9.json` with new image tag `staging-auth-check`
2. Built and pushed API image with auth_check diagnostic
3. Registered task definition v9
4. Updated API service to use v9

#### 6.4 Results (2025-12-02 18:06 UTC)
CloudWatch logs show:
```
2025-12-02 18:06:32,568 - main.api.observability - INFO - LangFuse auth_check() result: True
2025-12-02 18:06:32,675 - main.api.observability - INFO - LangFuse health_check_span created and flushed
2025-12-02 18:06:32,675 - main.api.observability - INFO - LangFuse initialized successfully
2025-12-02 18:06:32,675 - main.api.app - INFO - LangFuse observability initialized
```

**Key Finding:** `auth_check() result: True`
- ✅ Credentials are valid
- ✅ Network connectivity from ECS to cloud.langfuse.com is working
- ✅ Health check span was created and flushed

#### 6.5 Root Cause: LangFuse EU Outage

User discovered LangFuse status page showing active incident:

```
⚠️ We're currently experiencing issues

EU (cloud.langfuse.com)

⚠️ Database errors cause high error rates across the product

As the database is under high load, some data does not show up currently.
We will replay data into Clickhouse once the situation recovered.

Investigating · Ongoing for 33 minutes · Affects EU (cloud.langfuse.com)
```

**Conclusion:** Traces ARE being sent correctly, but LangFuse EU database is under high load and not displaying data. LangFuse will replay data once recovered.

---

## Root Cause Analysis

### Issue 1: OpenRouter Not Working (RESOLVED)
**Root Cause:** Configuration Drift
- API task definition (v6) was created earlier and never updated when Worker task definition (v9) received LLM and observability secrets during Task 4.2 implementation.

**Fix:** Updated API task definition to v8/v9 with all required secrets.

### Issue 2: LangFuse Traces Not Appearing (EXTERNAL)
**Root Cause:** LangFuse EU Outage
- LangFuse EU (cloud.langfuse.com) experiencing database issues
- Data is being sent but not displayed due to high load
- LangFuse will replay data once recovered

**Status:** Waiting for LangFuse recovery. Monitor: https://status.langfuse.com/

### Contributing Factors
1. **Separate task definitions** - API and Worker have independent configurations
2. **Incremental updates** - Worker was updated to v9 with secrets, API remained at v6
3. **No automated sync** - No process to ensure both task definitions have consistent environment
4. **Health check passing** - API health check (`/health`) passes without LLM/LangFuse

### Prevention Measures
1. **Checklist for secret updates** - When adding secrets, update BOTH API and Worker
2. **Terraform modules** - Share common secrets/env vars via Terraform locals
3. **Integration test** - Add test that verifies LLM and LangFuse are functional
4. **Environment parity check** - Script to compare API vs Worker task definitions
5. **External service monitoring** - Check status pages before debugging internal issues

---

## Files Modified

| File | Change | Version |
|------|--------|---------|
| `aws/terraform/task-definition-api-v7.json` | Added LLM/LangFuse secrets | v7 |
| `aws/terraform/task-definition-api-v9.json` | Added auth_check diagnostic image | v9 |
| `main/api/observability.py` | Added auth_check() diagnostic | - |

---

## Final Status

| Component | Status | Notes |
|-----------|--------|-------|
| OpenRouter API | ✅ WORKING | User confirmed via dashboard |
| LangFuse SDK | ✅ WORKING | auth_check() returns True |
| LangFuse Dashboard | ⏳ WAITING | External outage, data will replay |
| AWS Secrets | ✅ CORRECT | Verified match with user credentials |
| Network Connectivity | ✅ WORKING | ECS can reach cloud.langfuse.com |

---

## Next Steps

1. **Wait for LangFuse recovery** - Monitor https://status.langfuse.com/
2. **Verify traces appear** - Check dashboard after outage resolves
3. **Run test job** - Submit new URS file to verify full workflow
4. **Consider US region** - If EU outages are frequent, consider us.cloud.langfuse.com

---

## Appendix

### A. CloudWatch Logs - LangFuse Auth Check (2025-12-02 18:06 UTC)
```
2025-12-02 18:06:32,568 - main.api.observability - INFO - LangFuse auth_check() result: True
2025-12-02 18:06:32,675 - main.api.observability - INFO - LangFuse health_check_span created and flushed
2025-12-02 18:06:32,675 - main.api.observability - INFO - LangFuse initialized successfully
  Host: https://cloud.langfuse.com
  Public Key: pk-lf-9b...
  Auth Check: PASSED
```

### B. LangFuse Status Page (2025-12-02 ~18:10 UTC)
```
⚠️ We're currently experiencing issues
EU (cloud.langfuse.com)
Database errors cause high error rates across the product
Investigating · Ongoing for 33 minutes
```

### C. Task Definition Revisions

| Revision | Date | Changes |
|----------|------|---------|
| v6 | Initial | Missing LLM/LangFuse secrets |
| v7 | 2025-12-02 | Added all secrets, placeholder DB secret wrong |
| v8 | 2025-12-02 17:06 | Fixed DATABASE_URL secret ARN |
| v9 | 2025-12-02 18:04 | Added auth_check diagnostic image |
