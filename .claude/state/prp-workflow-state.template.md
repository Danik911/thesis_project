# PRP Workflow State

## Current Task
- **Task ID:** {task-id} (e.g., 1.2)
- **Task Name:** {task-name}
- **Phase:** {phase-number} - {phase-name}
- **Status:** {status} (pending, in-progress, completed, failed)
- **Current Agent:** {agent-name} (none, context-collector, task-executor, tester-agent, debugger)
- **Started:** {timestamp}
- **Last Updated:** {timestamp}

---

## Workflow Progress

### Agent Sequence
1. ⏸️ **Main Orchestrator** → Task initialization
2. ⏸️ **context-collector** → Research & context gathering
   - Result: `.claude/state/results/context-collector-{timestamp}.md`
3. ⏸️ **task-executor** → Implementation
   - Result: `.claude/state/results/task-executor-{timestamp}.md`
4. ⏸️ **tester-agent** → Validation & testing
   - Result: `.claude/state/results/tester-agent-{timestamp}.md`
5. ⏸️ **debugger** (conditional) → Issue resolution
   - Result: `.claude/state/results/debugger-{timestamp}.md`

**Status Legend:**
- ⏸️ Pending
- 🔄 In Progress
- ✅ Completed
- ❌ Failed

---

## Workflow History

*No previous executions yet*

Example format:
```
1. ✅ context-collector (2025-11-04 14:20:00 - 14:28:00)
   → results/context-collector-20251104-142000.md

2. ✅ task-executor (2025-11-04 14:30:00 - 14:45:00)
   → results/task-executor-20251104-143000.md

3. ✅ tester-agent (2025-11-04 14:50:00 - 15:00:00)
   → results/tester-agent-20251104-145000.md
```

---

## Critical Flags & Checks

### Compliance & Error Handling
- **NO_FALLBACK_VIOLATIONS:** 0
- **GAMP5_COMPLIANCE_CHECK:** PENDING
- **ALCOA_PLUS_VALIDATION:** PENDING
- **EXPLICIT_ERROR_HANDLING:** YES/NO

### User Confirmation
- **USER_CONFIRMATION_REQUIRED:** false
- **SUCCESS_CLAIMED_WITHOUT_VERIFICATION:** false

### Dependencies
- **PACKAGE_INSTALLATIONS_NEEDED:** []
- **MISSING_DEPENDENCIES:** []
- **BLOCKED_DEPENDENCIES:** []

---

## Files Modified

### Created
*No files created yet*

Example:
- `main/src/adapters/storage.py`
- `main/api/app.py`

### Modified
*No files modified yet*

Example:
- `main/src/core/unified_workflow.py`
- `main/docs/plans/mvp_implementation_plan.md`

### Deleted
*No files deleted yet*

---

## Task-Master AI Integration

- **Task-Master Task ID:** {tm-task-id} (if mapped)
- **Task-Master Status:** {tm-status}
- **Last Synced:** {timestamp}

---

## Notes

*Add any important notes, blockers, or context here*

---

**Last Modified:** {timestamp}
**Workflow Version:** 1.0
