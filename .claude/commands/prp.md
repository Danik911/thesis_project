---
description: Execute a PRP (Production Readiness Plan) task using orchestrated multi-agent workflow with state management. Use when working on AWS migration tasks from PRPs/tasks/.
argument-hint: <task-id> (e.g., 1.2 for Phase 1 Task 2)
---

# Execute PRP Task Command

Execute PRP task: **$ARGUMENTS**

## Pre-Flight Validation

### Step 1: Validate Task ID Format
Task ID provided: **$ARGUMENTS**

Expected format: `{phase}.{task}` (e.g., `1.2`, `0.3`, `5.1`)

Validation checks:
- Task ID matches pattern: `[0-5]\.[1-4]` (valid range: 0.1-5.3)
- Task file exists: `PRPs/tasks/$ARGUMENTS-*.md`

**Action:** Read task file from `PRPs/tasks/` directory matching pattern `$ARGUMENTS-*.md`

If task file not found, STOP and report error:
```
❌ ERROR: Task $ARGUMENTS not found in PRPs/tasks/
Available tasks: [list all .md files in PRPs/tasks/]
```

### Step 2: Initialize State Management
**Action:** Create initial state files:

1. Copy template to active state file:
   - Source: `.claude/state/prp-workflow-state.template.md`
   - Destination: `.claude/state/prp-workflow-state.md`

2. Create task context file `.claude/state/current-task-context.md`:
   ```markdown
   # Current Task Context: $ARGUMENTS

   ## Task File
   {full path to task file}

   ## Task Content
   {paste complete content of task file}

   ## Task Metadata
   - Task ID: $ARGUMENTS
   - Phase: {extract from task ID}
   - Started: {current timestamp}
   - Workflow Status: INITIALIZED
   ```

3. Update `.claude/state/prp-workflow-state.md` with task details:
   - Set Task ID to $ARGUMENTS
   - Set Status to "in-progress"
   - Set Current Agent to "Main Orchestrator"
   - Set Started timestamp
   - Update Agent Sequence status (all to ⏸️ Pending)

---

## Phase 1: Context & Research Gathering

### Objective
Gather comprehensive context about the task including:
- LlamaIndex patterns and best practices
- Pharmaceutical compliance requirements (GAMP-5, ALCOA+)
- AWS service specifics
- Known implementation gotchas
- Library version compatibility

### Agent Invocation: context-collector

**Update State File First:**
- Mark "context-collector" as 🔄 In Progress
- Update "Current Agent" to "context-collector"
- Update "Last Updated" timestamp

**Invoke Agent:**

```
Use context-collector to research task $ARGUMENTS

## Complete Context (NEVER ASSUME - ALWAYS PROVIDE EXPLICITLY)

### Task Identification
- **Task ID:** $ARGUMENTS
- **Task File:** PRPs/tasks/$ARGUMENTS-{name}.md
- **Phase:** {phase number and name from PRP document}
- **Task Name:** {extract from task file header}

### Task Content
{Paste COMPLETE content from task file including:
- What to Do section
- Dependencies section
- Best Practices section
- Code Examples
- Testing Strategy
- Common Issues to Avoid
}

### Research Focus
You MUST research the following with NO ASSUMPTIONS:

1. **LlamaIndex Patterns** (if applicable to task):
   - Workflow implementation patterns
   - Vector store integration
   - Multi-agent orchestration
   - Latest version compatibility (LlamaIndex 0.12.0+)

2. **Pharmaceutical Compliance**:
   - GAMP-5 categorization requirements
   - ALCOA+ principles relevant to this task
   - 21 CFR Part 11 considerations (if applicable)
   - Audit trail requirements

3. **AWS Service Specifics**:
   - Service configuration best practices
   - Region-specific considerations (eu-west-2)
   - Cost optimization strategies
   - Security and compliance configurations

4. **Implementation Gotchas**:
   - Known issues with libraries/services
   - Version compatibility problems
   - Common pitfalls (from "Common Issues to Avoid" section)
   - Performance considerations

5. **Dependencies & Prerequisites**:
   - Required packages and versions
   - Configuration prerequisites
   - Infrastructure dependencies
   - Previous task completions required

### Research Tools Available
- `mcp__perplexity-mcp__search` - For quick factual queries
- `mcp__perplexity-mcp__reason` - For complex analysis
- `mcp__perplexity-mcp__deep_research` - For comprehensive investigation
- `mcp__context7__resolve-library-id` + `mcp__context7__get-library-docs` - For library documentation
- `mcp__one-search-mcp__one_search` - For web search
- `WebFetch` - For fetching specific documentation pages

### Critical Requirements
- **NO FALLBACK LOGIC:** Research must identify explicit error handling patterns
- **Model Constraints:** task-executor MUST use DeepSeek V3 (NO O3/OpenAI models)
- **Compliance First:** Prioritize GAMP-5 and ALCOA+ requirements
- **Version Specificity:** Provide exact version numbers for all libraries/services

### Output Format Required

Create file: `.claude/state/results/context-collector-{YYYYMMDD-HHMMSS}.md`

Use this structure:
```markdown
# Context Collector Result - {timestamp}

## Agent Configuration
- Agent: context-collector
- Task ID: $ARGUMENTS
- Invoked: {timestamp}
- Duration: {minutes}

## Task Understanding
{Summarize what this task is trying to accomplish}

## Research Findings

### LlamaIndex Patterns
{Code examples, patterns, version requirements}

### Pharmaceutical Compliance
- GAMP-5: {specific requirements}
- ALCOA+: {relevant principles}
- Audit Trail: {requirements}

### AWS Services
{Configuration patterns, best practices, gotchas}

### Implementation Gotchas
{Known issues, version conflicts, common pitfalls}

### Recommended Approach
{High-level implementation strategy}

### Required Libraries/Versions
- library1==x.y.z (reason)
- library2>=x.y.z (reason)

## Next Agent Guidance
{Specific instructions for task-executor based on research}

## Files Referenced
{List of documentation sources, URLs, library docs consulted}
```

### State Management
After completing research:
1. Save result to `.claude/state/results/context-collector-{timestamp}.md`
2. DO NOT update state file (main orchestrator will do this)
3. Return summary to main orchestrator
```

**Post-Agent Actions:**
1. Read result file from `.claude/state/results/context-collector-*.md` (latest)
2. Update `.claude/state/prp-workflow-state.md`:
   - Mark context-collector as ✅ Completed
   - Add link to result file in Workflow History
   - Update timestamps
3. Verify research completeness:
   - Check that all required sections are present
   - Confirm actionable guidance provided
   - Validate compliance considerations identified

**Critical Gate:** Do NOT proceed to Phase 2 if research is incomplete or unclear.

---

## Phase 2: Implementation

### Objective
Implement the task requirements following the research findings, maintaining:
- GAMP-5 compliance
- NO FALLBACK LOGIC (explicit error handling)
- DeepSeek V3 model usage (NO O3/OpenAI)
- Comprehensive file modification tracking

### Agent Invocation: task-executor

**Update State File First:**
- Mark "task-executor" as 🔄 In Progress
- Update "Current Agent" to "task-executor"
- Update "Last Updated" timestamp

**Invoke Agent:**

```
Use task-executor to implement task $ARGUMENTS

## Complete Context (DO NOT ASSUME ANYTHING - ALL INFORMATION PROVIDED EXPLICITLY)

### Task Identification
- **Task ID:** $ARGUMENTS
- **Task Name:** {from task file}
- **Phase:** {phase number} - {phase name}
- **Task File:** PRPs/tasks/$ARGUMENTS-{name}.md

### Full Task Description
{Paste complete "What to Do" section from task file}

### Dependencies Validated
{List of dependencies from task file and their status:
- Dependency 1: ✅ Complete
- Dependency 2: ✅ Complete
}

### Research Findings from context-collector
{Paste COMPLETE findings from context-collector result file:

#### LlamaIndex Patterns Found
{paste from context-collector}

#### Pharmaceutical Compliance Requirements
{paste from context-collector}

#### AWS Service Configuration
{paste from context-collector}

#### Implementation Gotchas Identified
{paste from context-collector}

#### Recommended Libraries/Versions
{paste from context-collector}

#### Recommended Implementation Approach
{paste from context-collector}
}

### Project Context & Patterns
- **Project Root:** C:\Users\anteb\Desktop\Courses\Projects\thesis_project
- **Main Application:** main/
- **Working Directory:** {current directory}
- **Git Branch:** backend
- **Python Version:** 3.12
- **Package Manager:** uv (NOT pip - use `uv add` for installations)

### Existing Architecture Patterns
From CLAUDE.md:
- Event-driven multi-agent system via LlamaIndex workflows
- GAMP-5 categorization as mandatory first step
- Compliance validation (ALCOA+, 21 CFR Part 11)
- Phoenix observability integration
- NO FALLBACK LOGIC - fail explicitly with full diagnostics

### Success Criteria
{Specific criteria from task file "Testing Strategy" section and best practices}

---

## CRITICAL REQUIREMENTS (ZERO TOLERANCE)

### 1. NO FALLBACK LOGIC
❌ NEVER implement:
- Default values when actual values missing
- Fallback to alternate models/services
- "Safe" alternatives that mask real errors
- Artificial confidence scores
- Placeholder implementations

✅ ALWAYS implement:
- Explicit error throwing with full stack traces
- Clear error messages with diagnostic information
- Validation that fails fast on invalid input
- Honest reporting of system state
- NO SUCCESS CLAIMS without actual success

Example (FORBIDDEN):
```python
try:
    result = api_call()
except Exception:
    result = {"status": "success", "data": []}  # ❌ FALLBACK LOGIC
```

Example (REQUIRED):
```python
try:
    result = api_call()
except Exception as e:
    logger.error(f"API call failed: {e}", exc_info=True)
    raise RuntimeError(f"Failed to retrieve data from API: {e}") from e
```

### 2. Model Enforcement
- **MUST USE:** DeepSeek V3 (deepseek/deepseek-chat) via OpenRouter
- **FORBIDDEN:** GPT-4, GPT-3.5, O3, O1, Claude, or any OpenAI generation models
- **Configuration:** Verify model selection in code/config

### 3. Package Installation
- **NEVER skip** installations due to permissions
- **ALWAYS use** `uv add {package}` (NOT pip install)
- **NEVER assume** packages are optional
- **IF installation fails:** STOP and ask user to resolve

### 4. GAMP-5 Compliance
{Specific GAMP-5 requirements from research findings}

### 5. Error Handling Standards
Every error must include:
- Clear error message describing what failed
- Full context (inputs, state, configuration)
- Stack trace (for exceptions)
- Guidance on resolution (if known)

---

## Implementation Instructions

{Paste specific implementation guidance from context-collector's "Next Agent Guidance" section}

### File Modifications Expected
Based on task requirements, you will likely need to:
{List expected files to create/modify from task description}

### Code Standards
- Follow existing project patterns in main/
- Include comprehensive docstrings
- Add type hints (Python 3.12 syntax)
- Include error handling at every integration point
- Add logging with appropriate levels

---

## Output Requirements

Create file: `.claude/state/results/task-executor-{YYYYMMDD-HHMMSS}.md`

### Required Structure:
```markdown
# Task Executor Result - {timestamp}

## Agent Configuration
- Agent: task-executor
- Task ID: $ARGUMENTS
- Model Used: {confirm DeepSeek V3}
- Invoked: {timestamp}
- Duration: {minutes}
- Status: {SUCCESS | PARTIAL | FAILED}

## Implementation Summary
{High-level description of what was implemented}

## Design Decisions
1. {Decision 1 with rationale}
2. {Decision 2 with rationale}

## Files Modified

### Created
- `path/to/file1.py` - Description
- `path/to/file2.md` - Description

### Modified
- `path/to/existing.py` - What changed and why
- `path/to/config.json` - Configuration updates

### Deleted
- `path/to/old_file.py` - Reason for deletion

## Compliance Checks

### NO FALLBACK LOGIC Verification
✅ All error paths throw explicit exceptions
✅ No default/placeholder values used
✅ All failures report full diagnostic info

### GAMP-5 Compliance
{How requirements were addressed}

### ALCOA+ Principles
{How principles were implemented}

## Package Installations
{List any packages added with `uv add`}

## Known Limitations
{Any intentional limitations or future work needed}

## Next Steps for Validation
{What tester-agent should focus on}
```

### State Management
After implementation:
1. Save result to `.claude/state/results/task-executor-{timestamp}.md`
2. DO NOT update state file (main orchestrator handles this)
3. DO NOT claim success without user verification
4. Return summary to main orchestrator
```

**Post-Agent Actions:**
1. Read result file from `.claude/state/results/task-executor-*.md` (latest)
2. Update `.claude/state/prp-workflow-state.md`:
   - Mark task-executor as ✅ Completed
   - Add link to result file in Workflow History
   - Update "Files Modified" section with created/modified/deleted files
   - Update timestamps
3. Verify implementation completeness:
   - Check that all expected files were modified
   - Confirm NO FALLBACK LOGIC violations reported
   - Validate model compliance (DeepSeek V3 used)

**Critical Gate:** Do NOT proceed to Phase 3 if implementation incomplete or compliance violations found.

---

## Phase 3: Validation & Testing

### Objective
Perform comprehensive validation including:
- Unit and integration tests
- Code quality checks (ruff, mypy)
- Compliance validation
- HONEST assessment of results (failures included)

### Agent Invocation: tester-agent

**Update State File First:**
- Mark "tester-agent" as 🔄 In Progress
- Update "Current Agent" to "tester-agent"
- Update "Last Updated" timestamp

**Invoke Agent:**

```
Use tester-agent to validate task $ARGUMENTS implementation

## Complete Context

### Task Identification
- **Task ID:** $ARGUMENTS
- **Task Name:** {from task file}
- **Phase:** {phase number} - {phase name}

### Implementation Summary
{Paste complete summary from task-executor result file:

#### What Was Implemented
{from task-executor}

#### Files Modified
{complete list from task-executor}

#### Design Decisions
{from task-executor}

#### Compliance Claims
{from task-executor}
}

### Success Criteria from Task Definition
{Paste "Testing Strategy" section from original task file}

### Additional Validation Requirements
{From task file "Best Practices" and "Common Issues to Avoid"}

---

## CRITICAL TESTING REQUIREMENTS

### 1. HONEST Assessment
❌ NEVER claim PASS if:
- Tests are failing
- Implementation is incomplete
- Errors are being masked
- Confidence is artificially inflated
- You didn't actually run the tests

✅ ALWAYS provide:
- Actual test results (not assumed)
- Complete failure details
- Specific error messages and stack traces
- Evidence-based assessment

### 2. NO FALLBACK LOGIC Validation
**CRITICAL CHECK:** Scan all modified code for forbidden patterns:
- Default values masking missing data
- Try-except blocks returning success on failure
- Placeholder/dummy implementations
- Artificial confidence scores
- Silent error swallowing

**How to Check:**
1. Read all modified Python files
2. Search for try-except blocks
3. Verify exceptions are re-raised or logged with full context
4. Check return values don't indicate success on failure
5. Validate all errors include diagnostic information

**Report Format:**
```
NO FALLBACK LOGIC SCAN:
✅ storage.py:45-52 - Exception properly re-raised with context
✅ workflow.py:120-125 - Validation fails fast on invalid input
❌ adapter.py:89 - Returns empty dict on failure (VIOLATION!)
```

### 3. Code Quality Checks
Run these commands and report ACTUAL results:

```bash
# Style and lint
ruff check --fix main/

# Type checking
mypy main/

# Security scan (if applicable)
bandit -r main/src/
```

Include COMPLETE output (not summary). If checks fail, report every error.

### 4. Compliance Validation

#### GAMP-5 Checks
{Specific checks based on task requirements}

#### ALCOA+ Validation
Verify each principle:
- [ ] Attributable: Changes tracked with author info
- [ ] Legible: Code is readable and documented
- [ ] Contemporaneous: Logs/audit trail in real-time
- [ ] Original: Primary source preserved
- [ ] Accurate: Data validation implemented
- [ ] Complete: All required fields present
- [ ] Consistent: Data format standardized
- [ ] Enduring: Persistence mechanisms implemented
- [ ] Available: Access controls defined

### 5. Functional Testing
Based on task's "Testing Strategy" section:
{Paste testing strategy from task file}

Run ACTUAL tests. If no tests exist yet, CREATE them, then run them.

---

## Testing Protocol

### Step 1: Code Quality
```bash
cd main
ruff check --fix .
mypy .
```
**Capture COMPLETE output** - all errors, warnings, info messages

### Step 2: NO FALLBACK LOGIC Scan
- Read all files from task-executor's "Files Modified" list
- Scan for forbidden patterns
- Document every try-except, error handling block
- Verify compliance with explicit error handling

### Step 3: Unit Tests
```bash
cd main
pytest tests/ -v --tb=short
```
**Capture COMPLETE output** - pass/fail counts, error messages, stack traces

### Step 4: Integration Tests
{Task-specific integration test commands}
**Capture COMPLETE output**

### Step 5: Compliance Checks
{Task-specific compliance validation commands}
**Capture COMPLETE output**

---

## Output Requirements

Create file: `.claude/state/results/tester-agent-{YYYYMMDD-HHMMSS}.md`

### Required Structure:
```markdown
# Tester Agent Result - {timestamp}

## Agent Configuration
- Agent: tester-agent
- Task ID: $ARGUMENTS
- Invoked: {timestamp}
- Duration: {minutes}
- Status: PASS | FAIL

## Test Results Summary
- **Overall Status:** PASS | FAIL
- **Critical Issues:** {count}
- **Warnings:** {count}
- **Tests Run:** {count}
- **Tests Passed:** {count}
- **Tests Failed:** {count}

## Code Quality Results

### Ruff (Style/Lint)
```
{COMPLETE ruff output - paste everything}
```
**Status:** ✅ PASS | ❌ FAIL
**Issues Found:** {count}

### Mypy (Type Checking)
```
{COMPLETE mypy output - paste everything}
```
**Status:** ✅ PASS | ❌ FAIL
**Type Errors:** {count}

## NO FALLBACK LOGIC Validation

### Scan Results
{For each modified file, list all error handling:
- File: path/to/file.py
  - Line X: ✅ Exception re-raised with context
  - Line Y: ❌ Returns default value on error (VIOLATION!)
}

**Violations Found:** {count}
**Status:** ✅ PASS | ❌ FAIL

### Violation Details
{For each violation, provide:
- File and line number
- Code snippet showing violation
- Explanation of why it violates NO FALLBACK LOGIC
- Recommended fix
}

## Functional Test Results

### Unit Tests
```
{COMPLETE pytest output}
```
**Tests Passed:** {count}/{total}
**Status:** ✅ PASS | ❌ FAIL

### Integration Tests
```
{COMPLETE output from integration tests}
```
**Status:** ✅ PASS | ❌ FAIL

## Compliance Validation

### GAMP-5 Compliance
{Specific checks and results}
**Status:** ✅ PASS | ⏸️ PENDING | ❌ FAIL

### ALCOA+ Principles
- Attributable: ✅ | ⏸️ | ❌
- Legible: ✅ | ⏸️ | ❌
- Contemporaneous: ✅ | ⏸️ | ❌
- Original: ✅ | ⏸️ | ❌
- Accurate: ✅ | ⏸️ | ❌
- Complete: ✅ | ⏸️ | ❌
- Consistent: ✅ | ⏸️ | ❌
- Enduring: ✅ | ⏸️ | ❌
- Available: ✅ | ⏸️ | ❌

**Status:** ✅ PASS | ⏸️ PARTIAL | ❌ FAIL

## Critical Issues Found

{List ALL critical issues - don't hide or minimize problems:
1. Issue description with evidence (error messages, line numbers)
2. Impact assessment
3. Recommended resolution
}

## Overall Assessment

**Status:** ✅ PASS | ⏸️ PARTIAL | ❌ FAIL

**Justification:**
{Honest, evidence-based assessment of whether implementation meets requirements}

**Recommendation:**
- [✅ PASS] Proceed to user confirmation
- [⏸️ PARTIAL] Minor fixes needed, then retest
- [❌ FAIL] Invoke debugger for critical issue resolution

## Next Steps
{If FAIL, what debugger should focus on}
{If PASS, what user should verify}
```

### State Management
After testing:
1. Save result to `.claude/state/results/tester-agent-{timestamp}.md`
2. DO NOT update state file (main orchestrator handles this)
3. Return HONEST assessment to main orchestrator
```

**Post-Agent Actions:**
1. Read result file from `.claude/state/results/tester-agent-*.md` (latest)
2. Update `.claude/state/prp-workflow-state.md`:
   - Mark tester-agent as ✅ Completed
   - Add link to result file in Workflow History
   - Update Critical Flags based on test results
   - Update timestamps
3. Analyze test results:
   - Extract overall status (PASS/FAIL)
   - Count critical issues
   - Determine if debugger invocation needed

**Critical Decision Point:**
- If status = PASS → Proceed to Phase 5 (User Confirmation)
- If status = FAIL and critical issues > 0 → Proceed to Phase 4 (Debugging)
- If status = PARTIAL → Ask user whether to proceed or debug

---

## Phase 4: Debugging (CONDITIONAL - Only if Critical Failures)

**Conditional Execution:** This phase ONLY runs if tester-agent reports FAIL status with critical issues.

If tester-agent status = PASS, skip to Phase 5.

### Objective
Systematically resolve critical issues found during testing using:
- Root cause analysis
- Targeted fixes
- Incremental validation
- Maximum 5 iteration attempts

### Agent Invocation: debugger

**Update State File First:**
- Mark "debugger" as 🔄 In Progress
- Update "Current Agent" to "debugger"
- Update "Last Updated" timestamp

**Invoke Agent:**

```
Use debugger to fix critical issues in task $ARGUMENTS

## Complete Context

### Task Identification
- **Task ID:** $ARGUMENTS
- **Task Name:** {from task file}
- **Phase:** {phase number} - {phase name}

### Implementation Context
{Paste summary from task-executor result file}

### Test Failure Report
{Paste COMPLETE "Critical Issues Found" section from tester-agent result file:

#### Critical Issues
{all critical issues with evidence}

#### Error Messages
{complete error messages and stack traces}

#### NO FALLBACK LOGIC Violations (if any)
{violations found by tester-agent}

#### Failed Tests
{which tests failed and why}
}

### Files Modified
{List from task-executor}

---

## DEBUGGING PROTOCOL

### Maximum Iterations
You have **MAXIMUM 5 ATTEMPTS** to resolve issues.
- Iteration 1-3: Targeted fixes
- Iteration 4-5: Broader investigation
- If 5 iterations fail: Recommend architectural changes to user

### Debugging Tools Available
- `mcp__sequential-thinking__sequentialthinking` - For systematic analysis
- `mcp__perplexity-mcp__reason` - For complex problem-solving
- `mcp__one-search-mcp__one_search` - For searching similar problems
- File reading/editing tools - For code modifications
- `Bash` - For running tests

### Required Approach
1. **Root Cause Analysis:**
   - Use sequential thinking to analyze each critical issue
   - Identify underlying causes (not just symptoms)
   - Research similar problems if needed

2. **Create Debug Plan:**
   - Document planned fixes in `.claude/state/debug-plan-{timestamp}.md`
   - Prioritize critical issues
   - Identify dependencies between issues

3. **Implement Fixes Incrementally:**
   - Fix one issue at a time
   - Validate each fix before proceeding
   - DO NOT introduce new fallback logic

4. **Validate After Each Fix:**
   - Run relevant tests
   - Check for regressions
   - Verify NO FALLBACK LOGIC still maintained

### Critical Requirements
- **NO NEW FALLBACK LOGIC:** Fixes must maintain explicit error handling
- **Evidence-Based:** Every fix must be validated with actual test runs
- **Iteration Tracking:** Track which iteration you're on
- **Honest Assessment:** If unfixable, say so (don't hide problems)

---

## Output Requirements

Create file: `.claude/state/results/debugger-{YYYYMMDD-HHMMSS}.md`

### Required Structure:
```markdown
# Debugger Result - {timestamp}

## Agent Configuration
- Agent: debugger
- Task ID: $ARGUMENTS
- Invoked: {timestamp}
- Duration: {minutes}
- Status: RESOLVED | PARTIAL | FAILED
- Iterations Used: {count}/5

## Issues Addressed
{List all critical issues from tester-agent}

## Root Cause Analysis
{For each issue:
- Issue description
- Root cause identified
- Why it occurred
- Fix approach
}

## Fixes Implemented

### Iteration 1
**Issue:** {description}
**Fix:** {what was changed}
**Files Modified:** {list}
**Validation:** {test results}
**Status:** ✅ RESOLVED | ⏸️ PARTIAL | ❌ FAILED

### Iteration 2
{same structure}

{... up to Iteration 5 if needed}

## Files Modified (All Iterations)

### Modified
- `path/to/file.py` - {changes made}

### Created
- `path/to/new_file.py` - {reason}

## Validation Results

### Tests After Fixes
```
{COMPLETE test output after all fixes}
```

### NO FALLBACK LOGIC Re-Check
{Verify no new violations introduced}

## Overall Assessment

**Issues Resolved:** {count}/{total}
**Issues Remaining:** {count}
**Status:** RESOLVED | PARTIAL | FAILED

### If RESOLVED:
All critical issues fixed. Ready for user confirmation.

### If PARTIAL:
- Issues resolved: {list}
- Issues remaining: {list with reasons why couldn't fix}

### If FAILED (5 iterations exhausted):
**Recommended Architectural Changes:**
{Specific recommendations for user to consider}

## Next Steps
{What should happen next based on status}
```

### State Management
After debugging:
1. Save result to `.claude/state/results/debugger-{timestamp}.md`
2. DO NOT update state file (main orchestrator handles this)
3. Return assessment to main orchestrator
```

**Post-Agent Actions:**
1. Read result file from `.claude/state/results/debugger-*.md` (latest)
2. Update `.claude/state/prp-workflow-state.md`:
   - Mark debugger as ✅ Completed
   - Add link to result file in Workflow History
   - Update Files Modified with additional changes
   - Update timestamps
3. Analyze debugging results:
   - Extract status (RESOLVED/PARTIAL/FAILED)
   - Count remaining issues
   - Determine if ready for user confirmation

**Critical Decision Point:**
- If status = RESOLVED → Proceed to Phase 5 (User Confirmation)
- If status = PARTIAL → Ask user whether to proceed or continue debugging
- If status = FAILED → Present architectural recommendations to user, await decision

---

## Phase 5: Completion & User Confirmation

### Objective
Aggregate all workflow results and obtain explicit user confirmation before marking task complete.

### Step 1: Aggregate Results

Read all result files:
1. `.claude/state/results/context-collector-*.md` (latest)
2. `.claude/state/results/task-executor-*.md` (latest)
3. `.claude/state/results/tester-agent-*.md` (latest)
4. `.claude/state/results/debugger-*.md` (latest, if exists)

Extract key information:
- Files created/modified/deleted (combine from all agents)
- Compliance validation status
- Test results
- Critical issues (resolved and remaining)
- NO FALLBACK LOGIC verification status

### Step 2: Update Final State

Update `.claude/state/prp-workflow-state.md`:
- Set "Status" to "completed" (workflow complete, awaiting user confirmation)
- Set "Current Agent" to "none"
- Update all agent statuses to ✅ Completed
- Populate complete "Files Modified" section
- Populate complete "Workflow History" section
- Update all timestamps

### Step 3: Present Comprehensive Summary to User

```markdown
## 🎯 Task $ARGUMENTS Execution Summary

### ✅ Workflow Completed

**Agents Executed:**
1. ✅ **context-collector** (Duration: {X} min)
   - Result: [.claude/state/results/context-collector-{timestamp}.md]
   - Key Findings: {1-2 sentence summary}

2. ✅ **task-executor** (Duration: {X} min)
   - Result: [.claude/state/results/task-executor-{timestamp}.md]
   - Implementation: {1-2 sentence summary}
   - Model Used: {confirm DeepSeek V3}

3. ✅ **tester-agent** (Duration: {X} min)
   - Result: [.claude/state/results/tester-agent-{timestamp}.md]
   - Test Status: {PASS/FAIL}
   - Tests: {passed}/{total}

{IF debugger was invoked:}
4. ✅ **debugger** (Duration: {X} min, Iterations: {count}/5)
   - Result: [.claude/state/results/debugger-{timestamp}.md]
   - Issues Resolved: {count}/{total}

---

### 📁 Files Modified

#### Created ({count} files)
{List each file with:
- Full path relative to project root
- Brief description of purpose
- Which agent created it
}

#### Modified ({count} files)
{List each file with:
- Full path relative to project root
- Summary of changes made
- Which agent modified it
}

#### Deleted ({count} files)
{List each file with:
- Full path relative to project root
- Reason for deletion
- Which agent deleted it
}

---

### ✅ Compliance Validation

#### GAMP-5 Compliance
- **Status:** ✅ PASS | ⏸️ PENDING | ❌ FAIL
- **Category:** {if applicable}
- **Details:** {summary of how requirements were met}

#### ALCOA+ Principles
- Attributable: ✅ | ⏸️ | ❌
- Legible: ✅ | ⏸️ | ❌
- Contemporaneous: ✅ | ⏸️ | ❌
- Original: ✅ | ⏸️ | ❌
- Accurate: ✅ | ⏸️ | ❌
- Complete: ✅ | ⏸️ | ❌
- Consistent: ✅ | ⏸️ | ❌
- Enduring: ✅ | ⏸️ | ❌
- Available: ✅ | ⏸️ | ❌

**Overall:** ✅ COMPLIANT | ⏸️ PARTIAL | ❌ NON-COMPLIANT

#### NO FALLBACK LOGIC Verification
- **Status:** ✅ VERIFIED | ❌ VIOLATIONS FOUND
- **Violations:** {count if any}
- **Details:** {summary of verification}

---

### 🧪 Test Results

#### Code Quality
- **Ruff (Lint):** ✅ PASS | ❌ FAIL ({issues count})
- **Mypy (Types):** ✅ PASS | ❌ FAIL ({errors count})

#### Functional Tests
- **Unit Tests:** {passed}/{total} ✅ | ❌
- **Integration Tests:** ✅ PASS | ❌ FAIL
- **Coverage:** {percentage}%

#### Overall Test Status
✅ ALL TESTS PASSING | ⏸️ SOME FAILURES | ❌ CRITICAL FAILURES

---

### ⚠️ Critical Issues

{IF no critical issues:}
✅ **No critical issues found**

{IF critical issues exist but resolved:}
**Resolved Issues ({count}):**
1. {Issue description} - ✅ RESOLVED in debugger iteration {X}
2. {Issue description} - ✅ RESOLVED in debugger iteration {Y}

{IF critical issues remain:}
**Remaining Issues ({count}):**
1. {Issue description with impact assessment}
2. {Issue description with impact assessment}

---

### 📊 Package Changes

{IF packages were installed:}
**Packages Added:**
- `package1==x.y.z` - {reason}
- `package2>=x.y.z` - {reason}

{IF no packages installed:}
✅ No new packages required

---

### 🔍 Next Steps for User

1. **Review Implementation:**
   - Check modified files in your code editor
   - Verify changes align with task requirements
   - Review compliance implementation

2. **Manual Validation:**
   - Run the application locally (if applicable)
   - Test the new functionality
   - Verify expected behavior

3. **Review Test Results:**
   - Check test output in tester-agent result file
   - Verify tests are comprehensive
   - Confirm no failures are acceptable

---

## ⚡ USER CONFIRMATION REQUIRED

**Did you see the expected result? Did the implementation work as intended?**

Please respond with ONE of the following:

### Option 1: ✅ Success - Mark Complete
"Yes, the implementation works as expected."

**What happens next:**
- State files will remain in `.claude/state/` for audit trail
- Workflow considered complete
- Task can be tracked as complete in your project management system

### Option 2: ⏸️ Partial Success - Needs Adjustment
"Partial success, but needs additional work on: {specific issues}"

**What happens next:**
- I will address the specific issues you mention
- State files updated with additional iterations
- New testing cycle initiated

### Option 3: ❌ Failed - Investigation Needed
"No, it didn't work. Here's what I observed: {details}"

**What happens next:**
- Debugger agent re-invoked with your feedback
- Comprehensive investigation of reported issues
- Architectural recommendations if problem persists

---

**⚠️ IMPORTANT:** I will NOT mark this task as 'done' until you explicitly confirm success.

Please take your time to review the changes and test the implementation before confirming.
```

### Step 4: Wait for User Response

DO NOT proceed without explicit user confirmation.

**User Response Handling:**

**If user confirms success ("Yes"):**
1. Update `.claude/state/prp-workflow-state.md`:
   - Set "Status" to "completed-confirmed"
   - Add "User Confirmation" timestamp
   - Set "USER_CONFIRMATION_REQUIRED" to false

2. Final message to user:
   ```markdown
   ✅ **Task $ARGUMENTS marked as COMPLETE**

   Workflow results archived in:
   - State file: `.claude/state/prp-workflow-state.md`
   - Results: `.claude/state/results/`

   Ready for next task!
   ```

**If user reports partial success:**
1. Capture user's specific feedback
2. Update state file with user notes
3. Re-invoke appropriate agent (likely task-executor or debugger)
4. Re-run testing
5. Return to user confirmation step

**If user reports failure:**
1. Capture detailed user feedback
2. Update state file with failure details
3. Invoke debugger with user's observations as additional context
4. Allow up to remaining debug iterations (of original 5)
5. Return to user confirmation step

---

## Error Handling Throughout Workflow

### Known Failure Modes & Responses

#### 1. Task File Not Found
**Error:** Task ID $ARGUMENTS does not match any file in PRPs/tasks/
**Response:**
- List all available task IDs
- Ask user to verify task ID format
- STOP workflow

#### 2. Agent Invocation Failure
**Error:** Agent {name} failed to complete or returned error
**Response:**
- Capture full error message
- Update state file with failure
- Report to user with full diagnostic info
- Ask user how to proceed (retry, skip, abort)
- DO NOT attempt automatic recovery

#### 3. Dependency Blocked
**Error:** Task dependencies not satisfied
**Response:**
- List blocked dependencies from task file
- Report which tasks must complete first
- STOP workflow
- DO NOT attempt workarounds

#### 4. Package Installation Failure
**Error:** `uv add {package}` failed
**Response:**
- Capture full error output
- Report to user
- Ask user to resolve installation issue
- STOP workflow
- NEVER skip package installation

#### 5. Test Failures Beyond Debug Capacity
**Error:** Debugger exhausted 5 iterations, critical issues remain
**Response:**
- Present architectural recommendations
- Show what was attempted
- Ask user for guidance (architectural change, different approach, etc.)
- DO NOT claim success
- DO NOT hide remaining issues

#### 6. Compliance Violations Found
**Error:** GAMP-5, ALCOA+, or NO FALLBACK LOGIC violations detected
**Response:**
- Immediately halt and report violations
- Provide specific code locations and violations
- Invoke debugger to fix
- DO NOT proceed with violations

---

## State File Management

### State File Locations
- **Main State:** `.claude/state/prp-workflow-state.md` (tracked in Git)
- **Task Context:** `.claude/state/current-task-context.md` (tracked in Git)
- **Results:** `.claude/state/results/*.md` (tracked in Git)

### Git Tracking
All state files ARE tracked in Git for GAMP-5 audit trail compliance.

### State File Lifecycle
1. **Initialization:** Copy template, populate with task details
2. **During Workflow:** Updated after each agent completion
3. **After Completion:** Final state with user confirmation
4. **Post-Task:** Remains for audit trail (never deleted)

### State File Updates
Main orchestrator (you) updates state file after each agent:
- Agent status (⏸️ → 🔄 → ✅)
- Timestamps
- Result file links
- Files modified aggregation
- Critical flags

Agents NEVER directly update state file - only write their result files.

---

## Success Criteria for This Workflow

The workflow is considered successful when ALL of the following are true:

✅ Task file found and read successfully
✅ All 3-4 agents completed (context-collector, task-executor, tester-agent, optionally debugger)
✅ Result files created by all agents
✅ NO FALLBACK LOGIC violations = 0
✅ GAMP-5 compliance requirements met
✅ Tests passing (or failures acceptable per user)
✅ User explicitly confirmed success
✅ State files updated and tracked in Git

---

## Notes

- **Estimated Total Time:** 20-60 minutes depending on task complexity
- **Agent Concurrency:** Agents run sequentially (never in parallel)
- **Model Usage:** Main orchestrator uses Sonnet 4.5, agents may use different models per their config
- **Error Philosophy:** Fail fast, fail explicitly, never mask problems
- **Audit Trail:** Complete workflow history preserved in state files

---

**Workflow Version:** 1.0
**Last Updated:** 2025-11-04
