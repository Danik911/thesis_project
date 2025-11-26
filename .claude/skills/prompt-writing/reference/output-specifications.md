# Output Specifications: Format Templates and Patterns

This document provides ready-to-use output format templates for different types of prompts and tasks.

---

## Table of Contents

1. [Markdown Report Templates](#markdown-report-templates)
2. [JSON/YAML Schemas](#jsonyaml-schemas)
3. [Verdict Patterns](#verdict-patterns)
4. [Checklist Formats](#checklist-formats)
5. [Condensed Response Formats](#condensed-response-formats)

---

## Markdown Report Templates

### Template 1: Task Execution Report

```markdown
## Output Format

# Task Result: [Task Name]

## Meta
| Field | Value |
|-------|-------|
| Task ID | [ID] |
| Timestamp | [ISO 8601] |
| Duration | [time] |
| Status | PASS / FAIL / PARTIAL |

## Summary
[2-3 sentence overview of what was accomplished]

## Changes Made

### Files Created
| File | Purpose |
|------|---------|
| `path/to/file.py` | [Brief description] |

### Files Modified
| File | Changes |
|------|---------|
| `path/to/file.py` | [What was changed] |

## Test Results
```
[Paste test output here]
```
- **Passed**: X
- **Failed**: Y
- **Skipped**: Z

## Issues Encountered
[List any problems and how they were resolved]

## Next Steps
[What should happen next, if anything]
```

### Template 2: Research/Analysis Report

```markdown
## Output Format

# Research Report: [Topic]

## Executive Summary
[3-5 sentences summarizing key findings and recommendation]

## Options Evaluated

### Option 1: [Name]
- **Description**: [What it is]
- **Pros**: [Benefits]
- **Cons**: [Drawbacks]
- **Fit**: HIGH / MEDIUM / LOW

### Option 2: [Name]
[Same structure]

### Option 3: [Name]
[Same structure]

## Comparison Matrix
| Criterion | Option 1 | Option 2 | Option 3 |
|-----------|----------|----------|----------|
| Cost | $ | $$ | $$$ |
| Complexity | Low | Medium | High |
| Fit | HIGH | MEDIUM | LOW |

## Recommendation
**Selected**: [Option Name]

**Rationale**:
1. [Reason 1]
2. [Reason 2]
3. [Reason 3]

## Risks and Mitigations
| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| [Risk 1] | High/Med/Low | High/Med/Low | [How to address] |

## Open Questions
- [Question needing clarification]

## References
- [Source 1]
- [Source 2]
```

### Template 3: Code Review Report

```markdown
## Output Format

# Code Review: [File/Module Name]

## Verdict: PASS / FAIL

**Summary**: [One sentence explanation]

## Quality Score: [1-5]/5

## Critical Issues
[Only if FAIL - must fix before proceeding]

### Issue 1: [Title]
- **Location**: `file.py:45-52`
- **Severity**: CRITICAL / HIGH / MEDIUM / LOW
- **Description**: [What's wrong]
- **Impact**: [Why it matters]
- **Fix**:
```python
# Corrected code
```

## Recommendations
[Should fix but not blocking]

### Recommendation 1: [Title]
- **Location**: `file.py:78`
- **Current**: [What the code does]
- **Better**: [What it should do]
- **Example**:
```python
# Improved code
```

## Strengths
- [What's done well]
- [Another positive]

## Metrics
| Criterion | Assessment |
|-----------|------------|
| Correctness | PASS / FAIL |
| Security | PASS / CONCERNS / FAIL |
| Readability | Excellent / Good / Fair / Poor |
| Test Coverage | X% |
| Type Safety | Complete / Partial / Missing |
```

---

## JSON/YAML Schemas

### Schema 1: Task Result

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["task_id", "status", "timestamp", "summary"],
  "properties": {
    "task_id": {
      "type": "string",
      "description": "Unique task identifier"
    },
    "status": {
      "type": "string",
      "enum": ["PASS", "FAIL", "PARTIAL", "BLOCKED"]
    },
    "timestamp": {
      "type": "string",
      "format": "date-time"
    },
    "duration_seconds": {
      "type": "integer"
    },
    "summary": {
      "type": "string",
      "maxLength": 500
    },
    "files_modified": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "path": {"type": "string"},
          "action": {"enum": ["created", "modified", "deleted"]},
          "description": {"type": "string"}
        }
      }
    },
    "test_results": {
      "type": "object",
      "properties": {
        "passed": {"type": "integer"},
        "failed": {"type": "integer"},
        "skipped": {"type": "integer"}
      }
    },
    "issues": {
      "type": "array",
      "items": {"type": "string"}
    },
    "next_steps": {
      "type": "array",
      "items": {"type": "string"}
    }
  }
}
```

**Example Output:**
```json
{
  "task_id": "1.2",
  "status": "PASS",
  "timestamp": "2025-11-25T14:30:22Z",
  "duration_seconds": 720,
  "summary": "Implemented S3VectorStore class with all interface methods. All tests passing.",
  "files_modified": [
    {
      "path": "main/src/adapters/s3_vector_store.py",
      "action": "created",
      "description": "S3 Vectors adapter implementation"
    }
  ],
  "test_results": {
    "passed": 15,
    "failed": 0,
    "skipped": 2
  },
  "issues": [],
  "next_steps": ["Run integration tests with real S3 bucket"]
}
```

### Schema 2: Validation Result

```yaml
# YAML Schema for validation results
type: object
required:
  - verdict
  - confidence
  - checks
properties:
  verdict:
    type: string
    enum: [PASS, FAIL]
  confidence:
    type: string
    enum: [HIGH, MEDIUM, LOW]
  score:
    type: integer
    minimum: 1
    maximum: 5
  checks:
    type: array
    items:
      type: object
      properties:
        name:
          type: string
        status:
          enum: [PASS, FAIL, SKIP, WARN]
        message:
          type: string
  critical_issues:
    type: array
    items:
      type: string
  recommendations:
    type: array
    items:
      type: string
```

**Example Output:**
```yaml
verdict: PASS
confidence: HIGH
score: 4
checks:
  - name: Type hints
    status: PASS
    message: All public methods have type hints
  - name: Error handling
    status: PASS
    message: Exceptions properly caught and re-raised
  - name: Test coverage
    status: WARN
    message: 87% coverage, target is 90%
critical_issues: []
recommendations:
  - Add tests for edge case in query() method
  - Consider adding retry logic for transient failures
```

---

## Verdict Patterns

### Pattern 1: Binary Verdict First

Always lead with the decision, then explain.

```markdown
## Output Format

**VERDICT: PASS**

**Reason**: All critical requirements met, code is production-ready.

**Score**: 4/5

---

## Detailed Analysis
[Rest of the report]
```

### Pattern 2: Verdict with Confidence

When uncertainty exists.

```markdown
## Output Format

**VERDICT: PASS**
**CONFIDENCE: MEDIUM**

**Reason**: Code meets requirements but edge cases not fully tested.

**Uncertainty Factors**:
- Integration with production S3 not verified
- Performance under load unknown

**Recommendation**: Proceed with caution, add monitoring.
```

### Pattern 3: Conditional Verdict

When pass depends on follow-up actions.

```markdown
## Output Format

**VERDICT: CONDITIONAL PASS**

**Conditions for Full Pass**:
1. [ ] Add error handling for network timeouts
2. [ ] Increase test coverage to 90%
3. [ ] Add logging for debugging

**If conditions met**: Ready for production
**If conditions not met**: Requires another review cycle
```

### Pattern 4: Tiered Verdict

Multiple levels of assessment.

```markdown
## Output Format

## Verdicts

### Security: PASS
No vulnerabilities detected.

### Performance: WARN
Acceptable for MVP, optimize before scale.

### Code Quality: PASS
Follows established patterns.

### Compliance: PASS
GAMP-5 requirements addressed.

---

**Overall: PASS with recommendations**
```

---

## Checklist Formats

### Format 1: Simple Checklist

```markdown
## Output Format

## Completion Status

- [x] Requirement 1: Implemented
- [x] Requirement 2: Implemented
- [ ] Requirement 3: BLOCKED - needs dependency
- [x] Requirement 4: Implemented
- [x] Requirement 5: Implemented

**Completion**: 4/5 (80%)
**Status**: PARTIAL - see blocked items
```

### Format 2: Detailed Checklist

```markdown
## Output Format

## Requirements Checklist

| # | Requirement | Status | Location | Notes |
|---|-------------|--------|----------|-------|
| 1 | Implement query() | DONE | s3_store.py:45 | - |
| 2 | Implement insert() | DONE | s3_store.py:78 | - |
| 3 | Implement delete() | DONE | s3_store.py:102 | - |
| 4 | Add retry logic | PARTIAL | s3_store.py:30 | Only for query |
| 5 | Write unit tests | DONE | test_s3.py | 15 tests |
| 6 | Write integration tests | BLOCKED | - | Needs AWS creds |

**Summary**: 4 DONE, 1 PARTIAL, 1 BLOCKED
```

### Format 3: Hierarchical Checklist

```markdown
## Output Format

## Implementation Checklist

### Core Functionality
- [x] VectorStoreProvider interface implemented
  - [x] query() method
  - [x] insert() method
  - [x] delete() method
  - [x] update() method

### Error Handling
- [x] Network errors caught
- [x] Retry logic implemented
- [ ] Circuit breaker pattern (deferred)

### Testing
- [x] Unit tests
  - [x] Happy path tests
  - [x] Error case tests
  - [ ] Edge case tests (partial)
- [ ] Integration tests (blocked)

### Documentation
- [x] Docstrings complete
- [x] README updated
- [ ] API reference (not required for MVP)
```

---

## Condensed Response Formats

### Format 1: Executive Summary

For quick consumption by humans or other agents.

```markdown
## Output Format

Return ONLY:

## Summary (max 50 words)
[What was done and outcome]

## Key Findings (max 3 bullets)
- [Most important finding]
- [Second most important]
- [Third if critical]

## Recommendation (1 sentence)
[What should happen next]

DO NOT include detailed analysis, full code, or verbose explanations.
```

### Format 2: Structured Brief

```markdown
## Output Format

**Task**: [Name]
**Status**: PASS/FAIL
**Duration**: [time]

**Result**: [1-2 sentences]

**Files**: [List modified files]

**Next**: [One next step]
```

### Format 3: Bullet Summary

```markdown
## Output Format

## [Task Name] - Complete

- **What**: Implemented S3VectorStore adapter
- **Status**: All tests passing
- **Files**: s3_vector_store.py (new), test_s3.py (new)
- **Issues**: None
- **Next**: Integration testing
```

### Format 4: Key-Value Pairs

```markdown
## Output Format

task: 1.2-vector-store
status: PASS
duration: 12m
files_created: 2
files_modified: 1
tests_passed: 15
tests_failed: 0
blocking_issues: 0
next_action: Run integration tests
```

---

## Delivery Location Patterns

### Pattern 1: State Directory

```markdown
## Delivery
Save to: `.claude/state/results/[agent]-[YYYYMMDD-HHMMSS].md`

Example: `.claude/state/results/task-executor-20251125-143022.md`
```

### Pattern 2: Project Output

```markdown
## Delivery
Save to: `output/[task-id]/[artifact-name].md`

Example: `output/1.2/implementation-report.md`
```

### Pattern 3: Inline Return

```markdown
## Delivery
Return the result directly in your response.
DO NOT save to a file.
Keep response under 500 words.
```

### Pattern 4: Multiple Outputs

```markdown
## Delivery

1. **Full Report**: `.claude/state/results/full-report.md`
2. **Summary**: Return inline (max 100 words)
3. **Artifacts**: `output/generated/` directory
```
