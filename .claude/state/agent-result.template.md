# {Agent-Name} Result - {Date/Time}

## Agent Configuration
- **Agent:** {agent-name}
- **Task ID:** {task-id}
- **Task Name:** {task-name}
- **Invoked:** {timestamp}
- **Completed:** {timestamp}
- **Duration:** {duration}
- **Status:** {SUCCESS | PARTIAL | FAILED}

---

## Context Provided to Agent

### Task Details
{What the main orchestrator told this agent about the task}

### Previous Agent Results
{Summary of what previous agents in the chain produced}

### Success Criteria
{How to know when this agent's work is complete}

---

## Work Performed

### Actions Taken
1. {Action 1}
2. {Action 2}
3. {Action 3}

### Tools Used
- {Tool 1 with description}
- {Tool 2 with description}

### Research Conducted (if applicable)
- {Research source 1}
- {Research source 2}

---

## Key Findings

### {Agent-Specific Section}

**For context-collector:**
- Code Examples Found
- Implementation Gotchas
- Regulatory Considerations (GAMP-5, ALCOA+)
- Recommended Libraries/Versions

**For task-executor:**
- Implementation Summary
- Design Decisions Made
- Compliance Considerations Addressed
- Error Handling Approach

**For tester-agent:**
- Test Results Summary
- Code Quality Metrics
- Compliance Validation Results
- Critical Issues Found

**For debugger:**
- Root Cause Analysis
- Fixes Implemented
- Verification Results
- Remaining Issues (if any)

---

## Files Modified

### Created
*No files created*

Example:
- `path/to/file1.py` - Description of file
- `path/to/file2.md` - Description of file

### Modified
*No files modified*

Example:
- `path/to/existing_file.py` - What was changed and why
- `path/to/config.json` - Configuration updates

### Deleted
*No files deleted*

Example:
- `path/to/old_file.py` - Reason for deletion

---

## Issues Encountered

### Blockers
*No blockers encountered*

Example:
- Missing dependency: `package-name` (version X.Y.Z required)
- Permission issue: Cannot write to `path/to/file`

### Warnings
*No warnings*

Example:
- Potential performance concern in `function_name()`
- Deprecated API usage in `module_name`

### Errors
*No errors encountered*

Example:
- `ErrorType`: Description of error
  - Stack trace (if applicable)
  - Attempted resolution
  - Current status

---

## Compliance & Quality Checks

### NO FALLBACK LOGIC Verification
- **Status:** ✅ PASS / ❌ FAIL
- **Details:** {Explanation of how explicit error handling was implemented}

### GAMP-5 Compliance
- **Status:** ✅ PASS / ⏸️ PENDING / ❌ FAIL
- **Category:** {Software category if applicable}
- **Details:** {Specific compliance considerations addressed}

### ALCOA+ Validation
- **Attributable:** ✅ / ⏸️ / ❌
- **Legible:** ✅ / ⏸️ / ❌
- **Contemporaneous:** ✅ / ⏸️ / ❌
- **Original:** ✅ / ⏸️ / ❌
- **Accurate:** ✅ / ⏸️ / ❌
- **Complete:** ✅ / ⏸️ / ❌
- **Consistent:** ✅ / ⏸️ / ❌
- **Enduring:** ✅ / ⏸️ / ❌
- **Available:** ✅ / ⏸️ / ❌

---

## Next Agent Instructions

### Context to Pass Forward
{What the next agent in the chain needs to know from this agent's work}

### Specific Guidance
1. {Instruction 1}
2. {Instruction 2}
3. {Instruction 3}

### Files to Review
- `path/to/file1` - Why the next agent should review this
- `path/to/file2` - What to look for

---

## Success Criteria Met?

- [ ] {Criterion 1 from task requirements}
- [ ] {Criterion 2 from task requirements}
- [ ] {Criterion 3 from task requirements}

**Overall Assessment:** {COMPLETE | PARTIAL | FAILED}

**User Confirmation Required:** {YES | NO}

---

## Agent-Specific Metadata

### context-collector
- Sources Consulted: {number}
- Research Depth: {quick | medium | thorough}
- Confidence Level: {high | medium | low}

### task-executor
- Model Used: {model-name}
- Lines of Code Written: {number}
- Compliance Checks Passed: {number}/{total}

### tester-agent
- Tests Run: {number}
- Tests Passed: {number}
- Tests Failed: {number}
- Code Coverage: {percentage}

### debugger
- Iteration Count: {number}/5
- Issues Resolved: {number}
- Issues Remaining: {number}
- Architectural Changes Recommended: {YES | NO}

---

**Generated:** {timestamp}
**Workflow Version:** 1.0
