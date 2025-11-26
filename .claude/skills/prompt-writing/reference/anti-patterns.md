# Anti-Patterns: Common Mistakes and How to Avoid Them

This document catalogs common prompt writing mistakes with clear examples and solutions.

---

## Table of Contents

1. [Context Anti-Patterns](#context-anti-patterns)
2. [Scope Anti-Patterns](#scope-anti-patterns)
3. [Output Anti-Patterns](#output-anti-patterns)
4. [Subagent Anti-Patterns](#subagent-anti-patterns)
5. [Quality Anti-Patterns](#quality-anti-patterns)

---

## Context Anti-Patterns

### Anti-Pattern 1: Context Amnesia

**Problem**: Assuming the agent remembers previous interactions.

```markdown
# WRONG
"Continue from where we left off with the authentication module."

# Impact
- Agent has no memory of previous work
- Results will be inconsistent or wrong
- Time wasted on clarification
```

```markdown
# RIGHT
"Continue implementing the authentication module.

Previous work:
- JWT validation implemented in auth.py:45-78
- Session management pending
- Rate limiting pending

Next step: Implement session management in auth.py.
Reference the JWT pattern for consistency."
```

---

### Anti-Pattern 2: Implicit File References

**Problem**: Referring to files without explicit paths.

```markdown
# WRONG
"Check the config file for the API keys."
"Look at the test file for examples."
"The interface is in the base module."
```

```markdown
# RIGHT
"Check `main/config/settings.py` for API key configuration."
"See test examples in `main/tests/test_auth.py:20-45`."
"The interface is defined in `main/src/adapters/base.py:VectorStoreProvider`."
```

---

### Anti-Pattern 3: Assumed Knowledge

**Problem**: Assuming the agent knows project-specific details.

```markdown
# WRONG
"Follow our standard error handling pattern."
"Use the usual logging setup."
"Apply the team's code style."
```

```markdown
# RIGHT
"Follow the error handling pattern from `main/src/adapters/storage.py:45-60`:
- Catch specific exceptions
- Log with context
- Re-raise with `from e`
- Include diagnostic information"

"Use logging setup:
```python
import logging
logger = logging.getLogger(__name__)
logger.info('Operation', extra={'context': data})
```"
```

---

### Anti-Pattern 4: Stale Context

**Problem**: Providing outdated information.

```markdown
# WRONG
"The interface has three methods: query, insert, delete."
# (But update() was added last week)
```

```markdown
# RIGHT
"The interface (as of commit abc123) has four methods:
- query() - Search for similar vectors
- insert() - Add new vectors
- delete() - Remove vectors
- update() - Modify existing vectors (added in PR #45)

Read `main/src/adapters/base.py` for current interface definition."
```

---

## Scope Anti-Patterns

### Anti-Pattern 5: Unbounded Scope

**Problem**: Vague or unlimited task boundaries.

```markdown
# WRONG
"Improve the codebase."
"Fix all the issues."
"Make the code better."
"Refactor as needed."
```

```markdown
# RIGHT
"Improve error handling in `main/api/auth.py`:
1. Add specific exception types for auth failures
2. Include user ID in error logs
3. Add rate limit exceeded handling

DO NOT modify:
- Other files
- Existing test assertions
- Public API signatures"
```

---

### Anti-Pattern 6: Missing Constraints

**Problem**: Not specifying what the agent should NOT do.

```markdown
# WRONG
"Implement the vector store adapter."
# Agent might: change interfaces, add dependencies, modify unrelated files
```

```markdown
# RIGHT
"Implement the vector store adapter.

Constraints:
- DO NOT modify `base.py` interface definitions
- DO NOT add new dependencies without approval
- DO NOT change existing method signatures
- ONLY modify files in `main/src/adapters/`
- Use existing error types from `exceptions.py`"
```

---

### Anti-Pattern 7: Scope Creep Permission

**Problem**: Allowing or encouraging unlimited expansion.

```markdown
# WRONG
"While you're there, feel free to fix anything else you notice."
"Improve whatever seems relevant."
"Add any enhancements you think would help."
```

```markdown
# RIGHT
"Implement the query() method ONLY.

If you notice other issues:
1. Document them in the 'Issues Found' section of your report
2. DO NOT fix them in this task
3. They will be addressed in separate tasks"
```

---

## Output Anti-Patterns

### Anti-Pattern 8: Vague Output Expectations

**Problem**: Not specifying what the output should look like.

```markdown
# WRONG
"Give me a report on what you did."
"Summarize the changes."
"Let me know when done."
```

```markdown
# RIGHT
"Provide a report with this exact structure:

## Summary
[2-3 sentences]

## Files Modified
| File | Change |
|------|--------|
| ... | ... |

## Test Results
- Passed: X
- Failed: Y

## Status
PASS / FAIL with reason"
```

---

### Anti-Pattern 9: Output Overload

**Problem**: Not limiting response size, causing context overflow.

```markdown
# WRONG
"Research best practices for error handling and tell me everything."
# Agent returns 15 pages of content
```

```markdown
# RIGHT
"Research error handling best practices.

Return ONLY:
1. Top 3 patterns (2-3 sentences each)
2. One code example for Python
3. Key anti-patterns (bullet list, max 5)

Maximum response: 300 words.
DO NOT include full documentation or multiple examples."
```

---

### Anti-Pattern 10: Missing Delivery Location

**Problem**: Not specifying where to save results.

```markdown
# WRONG
"Generate the implementation report."
# Where does it go? Inline? File? Which file?
```

```markdown
# RIGHT
"Generate the implementation report.

Delivery:
1. Save full report to: `.claude/state/results/impl-report-{timestamp}.md`
2. Return brief summary (max 50 words) inline
3. List created files in your response"
```

---

## Subagent Anti-Patterns

### Anti-Pattern 11: Nested Delegation

**Problem**: Expecting subagents to invoke other subagents.

```markdown
# WRONG (in subagent prompt)
"If you need more research, delegate to the context-collector agent."
# Subagents CANNOT invoke other subagents
```

```markdown
# RIGHT (in main orchestrator)
"Main agent handles all delegation:

Step 1: Launch context-collector → Get results
Step 2: Launch task-executor with context-collector results
Step 3: Launch tester with task-executor results

Each subagent returns to main agent, which coordinates next step."
```

---

### Anti-Pattern 12: Implicit State Sharing

**Problem**: Assuming subagents can access shared state.

```markdown
# WRONG
"Agent A will prepare the data."
"Agent B, use the data that Agent A prepared."
# Agent B has no access to Agent A's work
```

```markdown
# RIGHT
"Agent A: Save prepared data to `temp/prepared-data.json`

Agent B: Read prepared data from `temp/prepared-data.json`
This file contains:
- Cleaned records (array)
- Metadata (object)
- Processing timestamp"
```

---

### Anti-Pattern 13: Cross-Invocation Memory

**Problem**: Expecting subagent to remember previous invocations.

```markdown
# WRONG
First call: "Analyze the authentication module."
Second call: "Now fix the issues you found."
# Second call has NO memory of first call
```

```markdown
# RIGHT
First call: "Analyze auth module. Save findings to `analysis.md`"

Second call: "Fix issues listed in `analysis.md`:
1. Missing rate limiting (line 45)
2. JWT not validated (line 78)
3. Session timeout too long (line 92)

Read `analysis.md` for full context."
```

---

## Quality Anti-Patterns

### Anti-Pattern 14: Ambiguous Success Criteria

**Problem**: Unclear definition of "done."

```markdown
# WRONG
"Make it work."
"Ensure quality."
"Test thoroughly."
```

```markdown
# RIGHT
"Success criteria:
- [ ] All interface methods implemented
- [ ] Unit tests: 100% pass rate
- [ ] Coverage: ≥90% on new code
- [ ] Type checking: `mypy` passes with no errors
- [ ] Linting: `ruff` passes with no warnings
- [ ] Documentation: Docstrings on all public methods"
```

---

### Anti-Pattern 15: Missing Validation Steps

**Problem**: No checkpoints to verify progress.

```markdown
# WRONG
"Implement the feature and let me know when done."
```

```markdown
# RIGHT
"Implement the feature with these checkpoints:

1. After interface design:
   - Run: `mypy main/src/adapters/`
   - Verify: No type errors

2. After implementation:
   - Run: `pytest main/tests/ -v`
   - Verify: All tests pass

3. After documentation:
   - Run: `pydoc main.src.adapters.s3_store`
   - Verify: Documentation renders correctly

Report status at each checkpoint."
```

---

### Anti-Pattern 16: No Examples

**Problem**: Not showing expected behavior.

```markdown
# WRONG
"Parse the log file and extract errors."
# What format? What counts as an error? What output structure?
```

```markdown
# RIGHT
"Parse the log file and extract errors.

Input example:
```
2025-11-25 14:30:22 INFO Starting process
2025-11-25 14:30:23 ERROR Database connection failed: timeout
2025-11-25 14:30:24 WARN Retrying connection
2025-11-25 14:30:25 ERROR Retry failed: max attempts exceeded
```

Expected output:
```json
{
  "errors": [
    {
      "timestamp": "2025-11-25T14:30:23",
      "message": "Database connection failed: timeout",
      "line": 2
    },
    {
      "timestamp": "2025-11-25T14:30:25",
      "message": "Retry failed: max attempts exceeded",
      "line": 4
    }
  ],
  "total": 2
}
```"
```

---

### Anti-Pattern 17: Conflicting Instructions

**Problem**: Contradictory requirements in the same prompt.

```markdown
# WRONG
"Keep the code simple."
"Handle all edge cases comprehensively."
"Don't add too much error handling."
"Ensure robust error recovery."
```

```markdown
# RIGHT
"Error handling priorities (in order):
1. CRITICAL: Network failures - must handle with retry
2. CRITICAL: Invalid input - must validate and reject
3. OPTIONAL: Edge cases like empty arrays - log and continue
4. SKIP: Theoretical cases that can't happen in practice

Focus on #1 and #2. Document #3 for future. Ignore #4."
```

---

## Quick Reference: Anti-Pattern Checklist

Before sending a prompt, verify you haven't made these mistakes:

### Context
- [ ] No implicit references to previous conversations
- [ ] All file paths are explicit and complete
- [ ] No assumed project knowledge
- [ ] Context is current, not stale

### Scope
- [ ] Task has clear boundaries
- [ ] Constraints are explicit (what NOT to do)
- [ ] No open-ended "improve anything" permission

### Output
- [ ] Format is explicitly specified
- [ ] Response size is bounded
- [ ] Delivery location is defined

### Subagents
- [ ] No nested delegation expected
- [ ] State transfer is explicit via files
- [ ] No cross-invocation memory assumed

### Quality
- [ ] Success criteria are measurable
- [ ] Validation steps are included
- [ ] Examples provided for complex tasks
- [ ] No conflicting instructions
