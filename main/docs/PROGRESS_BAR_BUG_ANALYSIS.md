# Progress Bar Bug Analysis

## Executive Summary

The progress bar in the pharmaceutical test generation UI shows incorrect progress and jumps unexpectedly (e.g., 35% → 100% or 65% stuck). Multiple fixes were attempted but the root cause is a **fundamental architecture issue** with dual polling systems returning inconsistent data and the backend updating stages out of order. Even after consolidating to a single polling source (Nov 2025 fix), the UX still feels broken because backend stages arrive in large, infrequent jumps.

---

## Problem Statement

**User Expectation:**
Progress bar should smoothly transition through stages:
```
0% (queued) → 10% (ingestion) → 25% (categorization) → 30% (hil_waiting)
→ 45% (planning) → 65% (agent_execution) → 85% (oq_generation) → 100% (completion)
```

**Actual Behavior (as of Nov 30, 2025):**
- Progress can jump straight from 0% to 30% because backend immediately enters the `hil_waiting` stage
- Long-running stages (agent_execution, oq_generation) sit at 65%/85% for minutes, then jump to 100%
- Backend still emits out-of-order stages (85% → 45% → 65%) so percents regress if unguarded
- Stage labels sometimes don't match progress percentage (backend race), though guarded on the client now

---

## Architecture Overview

### Dual Polling System

The frontend uses TWO independent polling mechanisms:

1. **`pollJobStatus`** (generate.tsx)
   - Polls: `GET /jobs/{id}` every 2 seconds
   - Returns: `JobStatusResponse` with progress_percentage, current_stage, etc.

2. **`useJobStatusPolling`** hook (useJobStatusPolling.ts)
   - Polls: `GET /jobs/{id}/approval-status` every 5 seconds
   - Returns: `JobStatusWithApproval` with progress_percentage, current_stage, etc.

**Problem:** Both systems update the same React state (`progressPercentage`, `currentStage`, `currentStageLabel`) independently, causing race conditions.

### Backend Stage Update Flow

```
worker.py
  └── _process_job()
       ├── Sets INGESTION (10%)
       ├── Sets CATEGORIZATION (25%) OR PLANNING (45%)
       ├── Calls _execute_workflow()
       │    └── worker_executor.py
       │         ├── Calls stage_callback("agent_execution") → 65%
       │         ├── Runs workflow.run() (3-6 minutes)
       │         └── Calls stage_callback("oq_generation") → 85%
       └── Sets COMPLETION (100%)
```

---

## Root Cause Analysis

### Issue 1: Race Condition at Job Startup (Resolved)

**Evidence (from logs line 39-53):**
```
Line 39: approvalStatus received: {progress_percentage: 65, current_stage: 'agent_execution'}
Line 41: Progress increased: null → 65
Line 46: pollJobStatus shows: progress: 30%, stage: hil_waiting
Line 53: Ignoring backward progress: 30 (keeping: 65)
```

**What happens:**
1. Job is created, status is PENDING
2. `useJobStatusPolling` starts polling `/approval-status`
3. API returns STALE data from a previous job OR wrong initial state (65% agent_execution)
4. Frontend sets progress to 65%
5. `pollJobStatus` returns correct 30% (hil_waiting)
6. Monotonic update prevents 65 → 30 correction
7. **User is stuck at wrong progress**

### Issue 2: Backend Updates Stages Out of Order (Ongoing)

**Evidence (from logs line 350-366):**
```
Line 350: status: PROCESSING, stage: oq_generation, progress: 85%
Line 361: status: PROCESSING, stage: planning, progress: 45%  ← BACKWARD!
Line 366: status: PROCESSING, stage: agent_execution, progress: 65%  ← STILL BACKWARD!
```

**What happens:**
1. Backend sets `oq_generation` (85%)
2. Some other process or race condition sets `planning` (45%)
3. Then sets `agent_execution` (65%)
4. Stages go BACKWARD in the database
5. Different API calls return different stages based on timing

### Issue 3: Monotonic Update Fix Backfires (Legacy)

**The fix I implemented:**
```typescript
setProgressPercentage(prev => {
  if (prev === null || prev === undefined || newProgress > prev) {
    return newProgress;
  }
  // Ignore backward movement
  return prev;
});
```

**Why it backfires:**
- When initial data is WRONG (65% instead of 0%), progress is stuck
- When backend sends stages out of order, progress gets stuck at highest (incorrect) value
- The fix prevents BOTH legitimate backward movement AND correction of wrong data

### Issue 4: Stage Label Not Updated With Progress (Legacy)

### Issue 5: Coarse Stage Granularity Causes UX Jumps (New)

Even with race conditions addressed, the backend only ever reports the discrete stage percentages defined in `STAGE_PROGRESS_MAP`. A typical trace now looks like:

1. `hil_waiting` payload arrives first → frontend jumps from placeholder 0% to 30%
2. Job sits in `agent_execution` for 4‑6 minutes → progress locked at 65%
3. Once agents finish, backend immediately emits `oq_generation` (85%) followed by `completion` (100%) → user perceives a sudden leap from 65% to 100%

Because there are no intermediate signals or durations per stage, the bar cannot communicate ongoing work; it appears “frozen” and then “teleports,” which users describe as jarring.

### Issue 6: Backend Emits Older Stage Payloads During Long Runs (New)

The worker periodically sends stale stage snapshots after a token refresh or worker retry (e.g., `oq_generation` → `planning`). The frontend now ignores regressive timestamps, but the noise further underscores that a simple determinate bar is the wrong UI metaphor for this workflow.

**The bug:**
When monotonic update prevents progress from changing, the stage label and stage name are also NOT updated because they're inside the same conditional block.

```typescript
// Current broken logic:
if (newProgress > prev) {
  setCurrentStage(stage);        // Only updates if progress increases
  setCurrentStageLabel(label);   // Only updates if progress increases
  return newProgress;
}
return prev;  // Stage label NOT updated even though it should change
```

**Result:** User sees stale stage label even when backend reports different stage.

---

## Attempted Fixes (All Failed)

### Fix 1: Stale Closure Bug in Status Comparison
**File:** `generate.tsx` line 551-558
**Change:** Used `setStatus(prevStatus => {...})` callback pattern
**Outcome:** Partially working, but didn't address the core issue

### Fix 2: Monotonic Progress Updates
**File:** `generate.tsx` lines 196-256 and 489-507
**Change:** Only allow progress to increase, never decrease
**Outcome:** Made things WORSE - progress gets stuck at wrong high value

### Fix 3: Backend Delay After PLANNING Stage
**File:** `worker.py` lines 342-344 and 560-563
**Change:** Added `await asyncio.sleep(3)` after setting PLANNING
**Outcome:** Didn't help - the stage ordering issue is more fundamental

### Fix 4: Backend Delay After OQ_GENERATION Stage
**File:** `worker_executor.py` lines 249-252
**Change:** Added `await asyncio.sleep(3)` after setting OQ_GENERATION
**Outcome:** Didn't help - backend still updates stages out of order

---

## Files Modified (Need Review/Rollback)

| File | Lines | Change |
|------|-------|--------|
| `main/api/app.py` | 239-246 | Added CORS origins for localhost:3001, 3002 |
| `main/api/worker.py` | 342-344 | Added 3s delay after PLANNING |
| `main/api/worker.py` | 560-563 | Added 3s delay after PLANNING (HIL flow) |
| `main/api/worker_executor.py` | 249-252 | Added 3s delay after OQ_GENERATION |
| `main/frontend/pages/generate.tsx` | 196-256 | Added monotonic progress updates (approvalStatus) |
| `main/frontend/pages/generate.tsx` | 489-507 | Added monotonic progress updates (pollJobStatus) |
| `main/frontend/pages/generate.tsx` | 551-558 | Fixed stale closure bug |

---

## Proposed Solution Architecture

### Option A: Single Source of Truth (Recommended)

1. **Eliminate dual polling** - Use ONLY `pollJobStatus` for progress
2. **Disable `useJobStatusPolling`** for progress updates (keep for approval modal only)
3. **Always trust `/jobs/{id}` endpoint** as the authoritative source
4. **Remove monotonic update logic** - Trust the backend

### Option B: Backend-Driven Progress with Versioning

1. **Add `stage_sequence_number`** to JobRecord (increments with each stage change)
2. **Frontend tracks highest sequence seen**
3. **Only accept updates with higher sequence number**
4. **Guarantees ordering regardless of poll timing**

### Option C: Server-Sent Events / WebSocket
### Option D: Stage Timeline UI (New Recommendation)

Instead of forcing a determinate bar to interpolate sparse data, pivot to a stage-driven UX:

1. Replace the percent bar with a vertical (or horizontal) timeline of discrete stages (Queued → Ingestion → … → Completion)
2. Highlight the active stage, show completed ones with checkmarks, and future ones as pending
3. For long-running stages, show indeterminate motion (pulse/loop) and optionally display historical average duration (“Typically 4‑6 min”)
4. Keep the numeric percentage as secondary text for parity with existing data contracts

This approach matches what users actually receive from the backend—ordered milestones rather than continuous progress—and prevents jarring jumps.

### Option E: Hybrid Determinate + Indeterminate Bar

If leadership insists on a bar, combine the stage timeline with a “smooth” client-side animation that slowly increments between milestones while still snapping to the real percentage when a new stage arrives. This requires clear copy to avoid implying false precision.


1. **Replace polling with push notifications**
2. **Backend emits stage change events**
3. **Frontend receives ordered stream**
4. **No race conditions possible**

---

## Recommended Immediate Fix

Phase 1 (DONE Nov 30, 2025): **Option A** - consolidate to single polling system:

1. Disabled progress updates from `useJobStatusPolling`
2. Kept the hook only for detecting `AWAITING_APPROVAL`
3. Made `/jobs/{id}` the sole authority and removed monotonic logic
4. Added stage-order guards so stale payloads are ignored

Phase 2 (NEXT): Ship **Option D** (Stage Timeline UI) to address UX complaints without waiting for backend refactors. Optionally layer Option B/E later for richer telemetry.

---

## Test Scenarios

After fixing, verify these scenarios:

1. **New job submission:** Progress should start at 0%, not jump to random value
2. **HIL waiting:** Progress should show 30%, label "Awaiting Human Approval"
3. **After approval:** Progress should smoothly transition 45% → 65% → 85% → 100%
4. **Stage labels:** Should always match the progress percentage
5. **No backward jumps:** Progress should never decrease during normal flow

---

## Log Analysis Reference

**Full log file:** `main/logs/logs_webconsole_api_docker.md`

**Key problematic lines:**
- Lines 39-43: Wrong initial progress (65% instead of 0%)
- Lines 51-53: Monotonic update prevents correction
- Lines 350-366: Backend stages go backward
- Lines 353, 365, 373, etc.: "Ignoring backward progress" messages

---

## Appendix: Stage Mapping

```typescript
const STAGE_PROGRESS_MAP = {
  "queued": 0,
  "ingestion": 10,
  "categorization": 25,
  "hil_waiting": 30,
  "planning": 45,
  "agent_execution": 65,
  "oq_generation": 85,
  "completion": 100
};

const STAGE_LABELS = {
  "queued": "Queued",
  "ingestion": "Loading Document",
  "categorization": "GAMP-5 Classification",
  "hil_waiting": "Awaiting Human Approval",
  "planning": "Planning Test Strategy",
  "agent_execution": "Executing AI Agents",
  "oq_generation": "Generating Test Cases",
  "completion": "Finalizing Results"
};
```
