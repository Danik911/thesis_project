# LIMS-003: Chat Agent + Mandatory HITL + Router Endpoints

**Date:** 2026-02-17
**Status:** Complete
**Branch:** `prjoject_p_protatype`
**Task:** L4b (PRP Tasks Merged: L4.3, L4.4, L4.6)

---

## Summary

Implemented the conversational MDA refinement chat agent with structured edit actions (OpenAI function calling), the mandatory HITL state machine (no auto-approval, no confidence thresholds, no timeout bypass), and all LIMS API endpoints. The export endpoint returns HTTP 403 unless a human has explicitly called POST /approve -- there is no bypass path.

## Files Created

| File | Purpose |
|------|---------|
| `main/src/lims/chat_agent.py` | ChatSession with MDAEditAction, OpenAI function calling, TTL (2h) + turn limits (50), rollback on failure (471 lines) |
| `main/src/lims/job_store.py` | In-memory job store + state machine: EXTRACTING->GENERATING->PENDING_REVIEW->APPROVED->EXPORTED (238 lines) |
| `main/src/lims/prompts/chat_system_prompt.py` | Chat prompt template with {mda_state} and {pdf_context} placeholders |
| `main/src/lims/prompts/edit_contract_prompt.py` | MDAEditAction JSON schema docs for LLM tool description |
| `main/tests/lims/test_job_store.py` | 32 state machine tests (valid/invalid transitions, HITL enforcement) |
| `main/tests/lims/test_chat_agent.py` | 37 chat agent unit tests (mock LLM, structured edit validation, rollback) |

## Files Modified

| File | Change |
|------|--------|
| `main/api/lims_router.py` | Added ChatRequest model, 4 new endpoints (GET /status, POST /chat, POST /approve, GET /export). Updated POST /extract to create jobs + trigger MDA generation. 460 lines total. |
| `main/tests/lims/test_lims_router.py` | Fixed mock config for L4a fields, added autouse fixture to clear _jobs |

## API Endpoints (Complete)

| Method | Path | Status Gate | Purpose |
|--------|------|-------------|---------|
| POST | `/lims/extract` | None -> EXTRACTING -> GENERATING -> PENDING_REVIEW | Upload PDF, extract, generate MDA |
| GET | `/lims/status/{job_id}` | Any | Get job status + current MDA template |
| POST | `/lims/chat` | PENDING_REVIEW only (409 otherwise) | Chat-based MDA refinement |
| POST | `/lims/approve/{job_id}` | PENDING_REVIEW -> APPROVED | Mandatory HITL gate |
| GET | `/lims/export/{job_id}` | APPROVED only (403 otherwise) | Download 4-sheet XLSX |

## HITL State Machine

```
EXTRACTING -> GENERATING -> PENDING_REVIEW -> APPROVED -> EXPORTED
                                    |
                                  FAILED (from EXTRACTING or GENERATING)
```

Key enforcement:
- `update_status()` raises ValueError if called with APPROVED -- directs to `approve_job()`
- `approve_job()` is the ONLY path to APPROVED -- requires PENDING_REVIEW state
- Export returns 403 for any status other than APPROVED
- No auto-approval, no confidence thresholds, no timeout bypass

## Test Results

- tester-agent: **84 passed, 2 skipped** (integration markers)
- All gate criteria met
- No no-fallback violations

## Manual E2E Test

```bash
# Full pipeline tested via curl:
# 1. POST /extract -> job_id, status: PENDING_REVIEW
# 2. GET /status/{job_id} -> mda_template populated
# 3. GET /export/{job_id} -> HTTP 403 (not approved)
# 4. POST /approve/{job_id} -> status: APPROVED
# 5. GET /export/{job_id} -> XLSX download (4 sheets)
```

---

## Issues Encountered

### 1. Router Test Mock Config Missing L4a Fields (FIXED)

**Symptom:** Router tests failed because mock LIMSConfig lacked new fields (openrouter_api_key, openrouter_model, chromadb_path).
**Fix:** Updated test mock config to include all LIMSConfig fields.

### 2. Job Store Pollution Between Tests (FIXED)

**Symptom:** Non-deterministic tests because in-memory `_jobs` dict persisted between test functions.
**Fix:** Added `@pytest.fixture(autouse=True)` clearing `_jobs` before/after each test.

### 3. chat() Signature Deviation from Spec

**Symptom:** Spec showed `chat(user_message)` but implementation uses `chat(user_message, config)`.
**Reason:** Intentional -- config passed per call so ChatSession doesn't store API keys as instance state. Router handles config loading and passes through. Matches mda_generator.py pattern.

---

## Architecture Notes

### Chat Agent Design

- Uses OpenAI function calling (`tools` parameter) with a single `modify_mda` tool
- LLM decides when to call the tool based on user intent
- Each edit is validated by `MDAEditAction` Pydantic model (sheet, action, target, changes, reason)
- After applying edit, entire MDA is re-validated via `MDATemplate.model_validate()`
- If validation fails, snapshot is restored (rollback)
- Edit reasons are logged for ALCOA+ audit trail compliance

### Session Management

- In-memory per-job sessions (`_sessions` dict)
- `get_or_create_session()` is the public API
- TTL: 2 hours (TimeoutError raised)
- Turn limit: 50 (ValueError raised)
- Sessions lost on restart (acceptable for PoC)

---

## Useful Commands

```bash
# Start API
uv run uvicorn main.api.app:app --port 8080

# Test chat
curl -X POST http://localhost:8080/lims/chat \
  -H "Content-Type: application/json" \
  -d '{"job_id": "...", "message": "Why is DYE_VOLUME result_type K?"}'

# Test approval
curl -X POST http://localhost:8080/lims/approve/{job_id}

# Test export
curl -O http://localhost:8080/lims/export/{job_id}

# Run tests
uv run pytest main/tests/lims/ -v
```

---

## Next Steps

- L5: Backend E2E testing (test_e2e_pipeline.py, test_thesis_preservation.py, test_lims_e2e.sh)
- L6: Full HITL UI (ChatInterface.tsx, LIMSStepIndicator.tsx, lims.tsx multi-step flow)
