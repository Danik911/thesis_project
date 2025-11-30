# Agent Prompt: Fix Progress Bar Race Condition Bug

## Role
You are a senior React/TypeScript developer specializing in real-time UI synchronization and state management. You have deep expertise in fixing race conditions in polling-based systems.

## Task Description
Design and implement a new **stage timeline + hybrid progress indicator** for the pharmaceutical test generation UI. The old determinate bar still feels broken even after the race-condition fix: it leaps from 0 → 30% (HIL) and then sits at 65% for minutes before jumping straight to 100%. Users need a visualization that communicates discrete workflow stages and long-running work without implying smooth percentages.

---

## Context (C)

### Project Background
- **Project:** Pharmaceutical test generation system (GAMP-5 compliant)
- **Stack:** Next.js frontend, FastAPI backend, PostgreSQL database
- **Issue:** Progress bar shows wrong values (jumps from ~35% to 100%, or gets stuck at 65%)

### Current Architecture Problem
- Race-condition portion is fixed: `/jobs/{id}` is now the single source for stage/progress, and stale payloads are ignored.
- However, backend still emits only coarse stage milestones (0, 30, 45, 65, 85, 100). There is no telemetry for the minutes-long work inside each stage, so the determinate bar appears frozen and then “teleports.”
- Users report the experience as misleading, even though the data is technically correct.

### Previous Fixes
1. Consolidated to single polling loop
2. Added stage-order/time guards so regressions are ignored
3. Retained approval polling solely for HIL modal

**Result:** Data is now correct but UX remains poor due to coarse milestones.

### Evidence from Logs
```
2025-11-30 12:02: Job status: AWAITING_APPROVAL, stage hil_waiting, progress 30%
... (minutes later) status: PROCESSING, stage agent_execution, progress 65%
... (minutes later) status: PROCESSING, stage agent_execution, progress 65%  ← stuck
... sudden jump: stage oq_generation 85%, then completion 100%
```

No intermediate updates arrive, so the determinate bar cannot move smoothly.

---

## Limitations (L)

### DO NOT
- Modify backend APIs or database schema (treat `JobStatusResponse` contract as immutable)
- Remove approval polling or modal logic
- Introduce WebSocket/SSE (future consideration, not now)
- Fake per-second percentages that could mislead GMP/ALCOA auditors

### MUST
- Maintain backward compatibility with existing API contracts
- Keep the approval modal functionality working
- Ensure stage labels still mirror backend stages
- Provide a UX that explains long-running stages without lying about progress
- Test with actual workflow execution (not just UI inspection)

### Files You May Modify
- `main/frontend/pages/generate.tsx` (wire new component, state wiring)
- `main/frontend/components/JobProgress.tsx` (likely replace or heavily refactor)
- New UI components under `main/frontend/components/` (timeline, stage chips, etc.)
- Supporting style/util files as needed

### Files You Must NOT Modify
- `main/api/*.py` - Backend is off-limits
- `main/src/**/*.py` - Core workflow is off-limits

---

### Success Criteria
- Stage timeline clearly shows which milestone the job is on, which ones are completed, and which are pending
- Long-running stages display indeterminate motion or contextual text (“Executing AI Agents · usually 4–6 min”)
- A secondary progress indicator (percentage or mini bar) still reaches the same values as backend milestones without appearing frozen
- Approval modal triggers exactly as before
- No console errors or lint issues
- New UX passes manual test: job goes 0 → HIL → agent execution → completion with understandable visuals

### Output Expectations
1. Exact code paths and explanation of major changes
2. Rationale for UX decisions (timeline vs bar, animations, copy)
3. Test steps (include what to look for at 30%, 65%, 100%)

---

## Actions (A)

### Step 1: Understand Current State
Read these files completely before making changes:
- `main/frontend/pages/generate.tsx` - Focus on lines 196-256, 489-507, 551-558
- `main/frontend/hooks/useJobStatusPolling.ts` - Understand what it returns
- `main/docs/PROGRESS_BAR_BUG_ANALYSIS.md` - Full problem analysis

### Step 2: Implement the New UX

**Required approach (Stage Timeline + Hybrid Indicator):**
1. Build a component that renders the ordered stages (`STAGE_PROGRESS_MAP`). For each stage show: label, optional subtitle, status icon (complete/current/pending).
2. Highlight the active stage based on `currentStage`. When status is `AWAITING_APPROVAL`, visually emphasize that stage and keep modal controls unaffected.
3. Within the active stage, show an indeterminate animation or sub-progress to signal work.
4. Keep a small determinate bar or numeric percent, but clearly communicate that percentages update only when milestones arrive (e.g., “Progress: 65% (Executing AI Agents…)”).
5. Handle stage regression payloads gracefully (already filtered) and ensure the UI never jumps backwards visually.
6. Make the component responsive and accessible (ARIA labels for timeline steps).

### Step 3: Cleanup
- Remove leftover console noise or comments referencing monotonic fixes.
- Ensure `JobProgress` (or replacement) is self-contained and documented.

### Step 4: Test the Fix
1. Start a job → confirm timeline shows “Queued” then “Awaiting Human Approval” once 30% arrives (jump acceptable but explained by UI).
2. Remain on agent execution for several minutes → ensure indeterminate animation continues and contextual text reassures user.
3. After completion, confirm all stages marked done and secondary percent reads 100%.
4. Verify approval modal flow unchanged.
5. Confirm no console warnings and lint/tests pass if applicable.

### Step 5: Document Changes
Add comments explaining:
- Which polling system is authoritative for progress
- How approval detection still works
- Why monotonic logic was removed

---

## Resources (R)

### Files to Read
```
main/frontend/pages/generate.tsx           # Primary file to fix
main/frontend/hooks/useJobStatusPolling.ts # Understand hook behavior
main/docs/PROGRESS_BAR_BUG_ANALYSIS.md     # Full problem analysis
main/logs/logs_webconsole_api_docker.md    # Latest debug logs
```

### Stage Mapping Reference
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
```

### Key State Variables in generate.tsx
```typescript
const [progressPercentage, setProgressPercentage] = useState<number | null>(null);
const [currentStage, setCurrentStage] = useState<string | null>(null);
const [currentStageLabel, setCurrentStageLabel] = useState<string | null>(null);
const [status, setStatus] = useState<JobStatus>('IDLE');
```

### Debug Log Format
Current logs use this format (keep it for debugging):
```typescript
console.log('[PROGRESS-DEBUG] approvalStatus received:', data);
console.log('[PROGRESS-DEBUG] Progress increased:', prev, '→', newProgress);
console.log('[PROGRESS-DEBUG] Ignoring backward progress:', newProgress, '(keeping:', prev, ')');
```

---

## Example Expected Behavior

### Before Fix (Current Bug)
```
Job Created → Progress: 65% (WRONG)
HIL Waiting → Progress: 65% (stuck, should be 30%)
After Approval → Progress: 65% → 85% → 100% (skipped 45%)
```

### After Fix (Expected)
```
Job Created → Progress: 0% or 10%
Categorization → Progress: 25%
HIL Waiting → Progress: 30%, Label: "Awaiting Human Approval"
After Approval → Progress: 45% → 65% → 85% → 100%
Completed → Progress: 100%, Label: "Finalizing Results"
```

---

## Verification Checklist

After implementing, verify:
- [ ] `npm run dev` starts without errors
- [ ] Submit a new job - progress starts low (0-10%)
- [ ] Progress reaches 30% and shows "Awaiting Human Approval"
- [ ] Approval modal appears correctly
- [ ] After approval, progress smoothly increases
- [ ] No console errors about state updates
- [ ] No "Ignoring backward progress" debug messages
- [ ] Job completes at 100% with correct label
