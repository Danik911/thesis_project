# Template: Review/Validation Task

Use this template for tasks that involve reviewing, validating, or assessing code, designs, or implementations.

---

## Template

```markdown
# Review Task: [SUBJECT]

## Objective
[What to review and the purpose of the review]

## Context

### What's Being Reviewed
- Subject: [Code/design/document being reviewed]
- Author: [Who created it]
- Purpose: [What it's supposed to do]
- Phase: [Where this fits in the workflow]

### Review Trigger
[Why this review is happening now]
- [ ] New implementation complete
- [ ] Changes to existing code
- [ ] Pre-deployment validation
- [ ] Periodic audit
- [ ] Issue investigation

### Previous Reviews (if any)
- [Previous review reference and outcome]

## Scope

### Files/Areas to Review
- `[path/to/file1.py]` - [What to look for]
- `[path/to/file2.py]` - [What to look for]
- `[path/to/directory/]` - [Scope of review]

### Out of Scope
- [Files/areas NOT to review]
- [Types of issues NOT to flag]

## Review Criteria

### Critical (Automatic FAIL)
[Issues that must fail the review]
- [ ] Security vulnerabilities
- [ ] Data integrity violations
- [ ] [Domain-specific critical criteria]

### Required (Must Pass for Approval)
[Issues that should fail unless justified]
- [ ] [Required criterion 1]
- [ ] [Required criterion 2]
- [ ] [Required criterion 3]

### Recommended (Should Address)
[Issues to flag but not blocking]
- [ ] Code style improvements
- [ ] Performance optimizations
- [ ] Documentation gaps

## Specific Checks

### [Category 1: e.g., Security]
- [ ] [Specific check]
- [ ] [Specific check]
- [ ] [Specific check]

### [Category 2: e.g., Error Handling]
- [ ] [Specific check]
- [ ] [Specific check]
- [ ] [Specific check]

### [Category 3: e.g., Code Quality]
- [ ] [Specific check]
- [ ] [Specific check]
- [ ] [Specific check]

## Output

### Verdict Format
**VERDICT: PASS / FAIL / CONDITIONAL PASS**
**Confidence: HIGH / MEDIUM / LOW**
**Score: [1-5]/5** (if PASS)

### Report Structure
```markdown
# Review Report: [Subject]

## Verdict: [PASS/FAIL]
**Reason**: [One-line explanation]
**Score**: [1-5]/5
**Confidence**: [HIGH/MEDIUM/LOW]

## Summary
[2-3 sentence overview of findings]

## Critical Issues
[Only if FAIL - must fix]

### Issue 1: [Title]
- **Location**: `file.py:line`
- **Severity**: CRITICAL
- **Description**: [What's wrong]
- **Impact**: [Why it matters]
- **Fix**:
```[language]
[Corrected code]
```

## Required Fixes
[Must address for approval]
[Same structure as critical]

## Recommendations
[Should address but not blocking]

### Recommendation 1: [Title]
- **Location**: `file.py:line`
- **Current**: [What it does]
- **Better**: [What it should do]

## Strengths
- [Positive finding 1]
- [Positive finding 2]

## Checklist Results
| Category | Status | Notes |
|----------|--------|-------|
| Security | PASS/FAIL | [Brief note] |
| Error Handling | PASS/FAIL | [Brief note] |
| Code Quality | PASS/FAIL | [Brief note] |

## Next Steps
- [ ] [Action item if FAIL]
- [ ] [Action item if CONDITIONAL]
```

### Delivery
Save to: `[specified location]`
```

---

## Filled Example

```markdown
# Review Task: S3 Vector Store Implementation

## Objective
Review the S3VectorStore implementation for production readiness,
focusing on error handling, compliance, and code quality.

## Context

### What's Being Reviewed
- Subject: S3VectorStore adapter implementation
- Author: task-executor agent
- Purpose: Vector similarity search using AWS S3 Vectors
- Phase: Task 1.2 - Vector Store Provider

### Review Trigger
- [x] New implementation complete

### Previous Reviews
- None (first implementation)

## Scope

### Files/Areas to Review
- `main/src/adapters/s3_vector_store.py` - Main implementation
- `main/tests/test_s3_vector_store.py` - Test coverage
- `main/src/adapters/base.py` - Interface compliance

### Out of Scope
- Other adapters (storage.py, chromadb_store.py)
- Configuration files
- Documentation (separate review)

## Review Criteria

### Critical (Automatic FAIL)
- [ ] NO FALLBACK LOGIC violations (return defaults on failure)
- [ ] Security vulnerabilities (credential exposure, injection)
- [ ] Missing error handling for AWS operations
- [ ] Interface contract violations

### Required (Must Pass for Approval)
- [ ] All interface methods implemented
- [ ] Type hints on all public methods
- [ ] Exceptions include diagnostic information
- [ ] Unit tests exist for each method

### Recommended (Should Address)
- [ ] Docstrings complete (Google style)
- [ ] Logging for debugging
- [ ] Retry logic for transient failures

## Specific Checks

### NO FALLBACK LOGIC
- [ ] No empty returns in except blocks
- [ ] No default values masking failures
- [ ] No "success" status on failures
- [ ] All exceptions logged and re-raised

### Error Handling
- [ ] Network errors handled with retry
- [ ] Invalid input validated before AWS calls
- [ ] AWS errors wrapped with context
- [ ] Stack traces preserved (`from e`)

### Code Quality
- [ ] Single responsibility per method
- [ ] No magic numbers (constants defined)
- [ ] Consistent naming conventions
- [ ] No dead code or comments

### Compliance
- [ ] Audit logging for data operations
- [ ] User attribution captured
- [ ] Timestamps in ISO 8601 format

## Output

### Verdict Format
**VERDICT: PASS / FAIL / CONDITIONAL PASS**
**Confidence: HIGH / MEDIUM / LOW**
**Score: [1-5]/5**

### Report Structure
[Use standard review report format]

### Delivery
Save to: `.claude/state/results/code-review-{YYYYMMDD-HHMMSS}.md`
```

---

## Specialized Review Templates

### Security Review Focus

```markdown
## Security-Specific Checks

### Authentication
- [ ] All endpoints require authentication
- [ ] Tokens validated on every request
- [ ] Session management secure

### Authorization
- [ ] Role-based access enforced
- [ ] Resource ownership verified
- [ ] Principle of least privilege

### Data Protection
- [ ] Sensitive data encrypted at rest
- [ ] Sensitive data encrypted in transit
- [ ] No credentials in code or logs

### Input Validation
- [ ] All user input sanitized
- [ ] SQL injection prevented
- [ ] XSS attacks prevented
```

### Performance Review Focus

```markdown
## Performance-Specific Checks

### Efficiency
- [ ] No N+1 query patterns
- [ ] Appropriate use of caching
- [ ] Async operations where beneficial

### Resource Usage
- [ ] Memory usage bounded
- [ ] Connection pooling used
- [ ] Resources properly released

### Scalability
- [ ] Stateless design where possible
- [ ] No single points of contention
- [ ] Horizontal scaling supported
```

---

## Checklist Before Sending

- [ ] Review objective is clear
- [ ] Subject and context are specified
- [ ] Scope clearly defines what to review
- [ ] Critical criteria define automatic failures
- [ ] Specific checks are actionable
- [ ] Verdict format includes confidence level
- [ ] Report structure shows how to present findings
- [ ] Delivery location is specified
