# HIL Research - Document Index & Quick Reference

**Research Date:** 2025-11-26
**Total Documents:** 4
**Status:** COMPLETE AND READY FOR IMPLEMENTATION

---

## Document Overview

### 1. **hil-research-20251126-174500.md** (Main Research)
**Size:** ~6,500 lines | **Read Time:** 45 minutes

**Contents:**
- LlamaIndex workflow patterns for HIL (Events, serialization, checkpointing)
- Known LlamaIndex issues (cross-session resumption, serialization failures)
- FastAPI + PostgreSQL job state management patterns
- Async connection pooling with asyncpg
- Database polling for approval workflows
- Langfuse tracing best practices (manual spans, nesting, distributed tracing)
- Implementation gotchas (404 errors, multiple traces, state loss)
- GAMP-5 and ALCOA+ compliance requirements
- Recommended implementation approach
- Complete code example: HIL implementation

**When to Read:** First-time understanding of HIL patterns, architecture review

---

### 2. **hil-research-executive-summary.md** (Quick Reference)
**Size:** ~2,000 lines | **Read Time:** 15 minutes

**Contents:**
- Key findings at a glance (3 critical problems + solutions)
- LlamaIndex workflow issues summary
- GAMP-5 compliance checklist
- Current implementation assessment (what's good, what needs attention)
- Next steps (prioritized 1-5)
- Implementation code snippets
- Key resources and references

**When to Read:** Quick understanding before diving into full research, status updates, implementation planning

---

### 3. **hil-debugging-guide.md** (Troubleshooting)
**Size:** ~3,000 lines | **Read Time:** 30 minutes

**Contents:**
- Issue #1: 404 "Job Not Found" (step-by-step diagnosis)
- Issue #2: Multiple Langfuse Traces (causes and solutions)
- Issue #3: Worker Doesn't Resume After Approval (end-to-end test)
- Issue #4: Async Event Loop Blocking (detection and fixes)
- Issue #5: Langfuse Never Receives Traces (validation steps)
- Quick reference table
- Emergency debugging with full trace
- Database SQL queries for validation
- Bash commands for testing

**When to Read:** Actively debugging issues, running tests, verifying fixes

---

### 4. **hil-research-index.md** (This Document)
**Size:** ~800 lines | **Read Time:** 5 minutes

**Contents:**
- Document index and overview
- Quick reference by topic
- URL references to external documentation
- Implementation checklist
- Next steps

**When to Read:** Orientation, finding the right document for your task

---

## Quick Reference by Topic

### Issue: 404 "Job Not Found"
**File:** `hil-debugging-guide.md` → "Issue #1: 404 Job Not Found"
**Steps:** 5-step root cause analysis with code examples
**Time to Fix:** 30 minutes

### Issue: Multiple Langfuse Traces
**File:** `hil-research-executive-summary.md` → "Problem #2"
**File:** `hil-debugging-guide.md` → "Issue #2: Multiple Traces"
**Fix:** Nest spans with `parent.start_child_span()`
**Time to Fix:** 15 minutes

### Issue: Worker Won't Resume After Approval
**File:** `hil-debugging-guide.md` → "Issue #3: Worker Doesn't Resume"
**File:** `hil-research-20251126-174500.md` → "Section 7.2: Next Steps"
**Check:** Worker receiving db_job_repo, polling mode set correctly
**Time to Fix:** 30 minutes

### LlamaIndex Patterns
**File:** `hil-research-20251126-174500.md` → "Section 1: LlamaIndex Workflow Patterns"
**Topics:** Events, serialization, checkpointing
**Code Examples:** Yes (4 patterns)

### FastAPI + PostgreSQL
**File:** `hil-research-20251126-174500.md` → "Section 3: FastAPI + PostgreSQL"
**Topics:** Connection pooling, polling pattern, atomic updates
**Code Examples:** Yes (3 patterns)

### Langfuse Tracing
**File:** `hil-research-20251126-174500.md` → "Section 4: Langfuse Tracing"
**File:** `hil-research-executive-summary.md` → "Problem #3"
**Topics:** Manual spans, nesting, distributed tracing
**Code Examples:** Yes (4 patterns)

### GAMP-5 Compliance
**File:** `hil-research-20251126-174500.md` → "Section 6: Pharmaceutical Compliance"
**File:** `hil-research-executive-summary.md` → "GAMP-5 Compliance Requirements"
**Requirements:** Audit trail, validation, change control, data integrity
**Audit Fields:** 10 required fields listed

### Debugging Procedures
**File:** `hil-debugging-guide.md` → All sections
**Type:** Step-by-step procedures with SQL queries and bash commands
**Total Procedures:** 5 major issues

---

## Implementation Sequence

### Phase 1: Diagnosis (30 minutes)
1. Read `hil-research-executive-summary.md` (15 min)
2. Run diagnostics from `hil-debugging-guide.md` (15 min)

### Phase 2: Understanding (1 hour)
1. Read relevant sections from `hil-research-20251126-174500.md`
2. Review code examples matching your issue

### Phase 3: Implementation (2-4 hours)
1. Follow step-by-step debugging guides
2. Apply code examples
3. Test with end-to-end scenario

### Phase 4: Verification (30 minutes)
1. Run full end-to-end test (Terminal 3-4 scenario in debugging guide)
2. Verify Langfuse traces
3. Check audit trail logging

---

## Critical Implementation Checklist

### Architecture
- [ ] PostgreSQL backend initialized with connection pooling
- [ ] asyncpg pool max_size sufficient for concurrent requests
- [ ] db_job_repo passed to worker in FastAPI lifespan
- [ ] Database polling configured (2-second interval)

### LlamaIndex Workflow
- [ ] InputRequiredEvent and HumanResponseEvent handlers implemented
- [ ] Context serialization working (JsonSerializer)
- [ ] Workflow checkpoint recovery tested
- [ ] No non-serializable objects in context

### Langfuse Tracing
- [ ] Manual spans used (not @observe decorator)
- [ ] All spans nest under parent with consistent trace_id
- [ ] Single langfuse.flush() at end of workflow
- [ ] Span output contains only JSON-serializable data

### Async Safety
- [ ] No time.sleep() calls (use await asyncio.sleep())
- [ ] Database queries all async
- [ ] No blocking I/O on event loop
- [ ] Connection pool not exhausted (check logs)

### GAMP-5 Compliance
- [ ] Audit trail logs all state transitions
- [ ] User attribution on every decision (Clerk user_id + email)
- [ ] Timestamps with UTC timezone
- [ ] Digital signatures on approval records
- [ ] Immutability constraints on job data after approval

### Testing
- [ ] 404 error resolved (job found after submission)
- [ ] Langfuse shows single trace with nested spans
- [ ] Worker resumes after approval without 404
- [ ] Container restart doesn't lose approved jobs
- [ ] Timeout logic auto-rejects expired approvals

---

## External Resources

### Official Documentation

**LlamaIndex:**
- [Workflows Guide](https://developers.llamaindex.ai/python/framework/module_guides/workflow/)
- [State Persistence](https://developers.llamaindex.ai/python/framework/understanding/agent/state/)
- [API Reference](https://docs.llamaindex.ai/en/stable/api_reference/workflow/workflow/)

**asyncpg:**
- [Documentation](https://magicstack.github.io/asyncpg/current/usage.html)
- [GitHub Issues](https://github.com/MagicStack/asyncpg/issues)

**Langfuse:**
- [Python SDK](https://langfuse.com/docs/sdk/python/decorators)
- [Distributed Tracing](https://langfuse.com/docs/observability/features/trace-ids-and-distributed-tracing)
- [Tracing Best Practices](https://langfuse.com/docs/tracing)

**Pharmaceutical Compliance:**
- [GAMP-5 Guidelines](https://intuitionlabs.ai/articles/gamp-5-guidelines-system-validation)
- [21 CFR Part 11](https://www.tsaprocessequipments.com/fda-21-cfr-part-11-gamp-5-compliance-in-pharma/)
- [ISPE GAMP Publications](https://ispe.org/publications/guidance-documents)

### Technical Articles

**Async Patterns:**
- [Python Async/Await Behind the Scenes](https://tenthousandmeters.com/blog/python-behind-the-scenes-12-how-async-await-works-in-python/)
- [Async Worker Pool Pattern](https://shav.dev/blog/pool-of-workers)

**Job Queues:**
- [TaskIQ - Distributed Task Queue](https://github.com/taskiq-python/taskiq)
- [Celery with FastAPI](https://testdriven.io/blog/fastapi-and-celery/)

**FastAPI:**
- [Background Tasks](https://unfoldai.com/fastapi-background-tasks/)
- [Async Database Patterns](https://neon.com/guides/fastapi-async)

---

## File Structure on Disk

```
.claude/state/results/
├── hil-research-20251126-174500.md          # Main research (6,500 lines)
├── hil-research-executive-summary.md        # Quick reference (2,000 lines)
├── hil-debugging-guide.md                   # Troubleshooting (3,000 lines)
└── hil-research-index.md                    # This file (800 lines)
```

**Total Size:** ~12,300 lines of comprehensive HIL research
**Read Time:** 60-90 minutes (all documents)

---

## Key Findings Summary

### Problem #1: 404 Job Not Found
- **Root Cause:** Database connection pool exhausted OR job not persisting
- **Fix Time:** 30 minutes
- **Solution:** Increase pool max_size, verify database persistence

### Problem #2: Multiple Langfuse Traces
- **Root Cause:** Spans not nesting under parent
- **Fix Time:** 15 minutes
- **Solution:** Use `parent.start_child_span()` instead of `langfuse.start_span()`

### Problem #3: @observe Decorator Hangs
- **Root Cause:** Serializes non-serializable objects (files, connections)
- **Fix Time:** 30 minutes
- **Solution:** Use manual spans with `langfuse.start_span()` + `span.end()`

### Problem #4: Worker Won't Resume
- **Root Cause:** db_job_repo not passed to worker
- **Fix Time:** 15 minutes
- **Solution:** Pass `db_job_repo=db_job_repo` in lifespan

### Problem #5: State Lost on Restart
- **Root Cause:** In-memory queue/dict
- **Fix Time:** Already fixed
- **Solution:** PostgreSQL polling (already implemented)

---

## Next Steps Prioritized

1. **Read Executive Summary** (15 min)
   → Understand problems and solutions

2. **Run Diagnostics** (30 min)
   → Use debugging guide to identify which issues affect your system

3. **Fix 404 Error** (30 min)
   → Most impactful issue, prevents approvals from working

4. **Reduce Traces** (15 min)
   → Improve observability

5. **Test End-to-End** (30 min)
   → Verify workflow from submission through approval to completion

6. **Verify Compliance** (1 hour)
   → Ensure audit trail meets GAMP-5 requirements

---

## Quick Command Reference

### Test Database Connectivity
```bash
psql postgresql://user:pass@localhost/testdb -c "SELECT COUNT(*) FROM jobs;"
```

### Check Job Status
```bash
SELECT job_id, status, human_category, updated_at FROM jobs WHERE job_id = 'abc123';
```

### Submit Test Job (requires token)
```bash
curl -X POST http://localhost:8000/jobs \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test.urs"
```

### Approve Job (requires token and job_id)
```bash
curl -X POST http://localhost:8000/jobs/$JOB_ID/approval \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "approval_decision": "approve",
    "human_category": 4,
    "justification": "Test approval"
  }'
```

### Monitor Worker Logs
```bash
tail -f logs/worker.log | grep -E "\[HIL\]|\[DB\]"
```

### Check Langfuse Traces
```bash
# Open in browser:
https://cloud.langfuse.com/dashboard
# Filter by trace_id: job_abc123
```

---

## Document Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-11-26 | Initial research complete |

---

## Contact & Support

For questions about research findings:
- Review the specific document section first
- Check debugging guide for step-by-step procedures
- Verify against external documentation links provided

---

**Research Status:** COMPLETE ✅
**Ready for Implementation:** YES
**Last Updated:** 2025-11-26 17:45 UTC
