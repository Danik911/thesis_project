---
name: debugging-mastery
description: Systematic debugging methodologies for finding and resolving complex bugs. Use PROACTIVELY when encountering difficult bugs, mysterious failures, or issues that resist simple fixes. MUST BE USED when debugging spans multiple files, involves race conditions, or has eluded initial investigation attempts.
allowed-tools: ["Read", "Write", "Edit", "Grep", "Glob", "Bash", "Task"]
---

# Debugging Mastery Skill

Master skill for systematic bug resolution using proven methodologies and structured approaches to root cause analysis.

---

## Overview

### Purpose
This skill provides a comprehensive framework for finding and resolving the most difficult bugs in code. It combines industry-standard debugging techniques with structured templates for tracking progress and documenting root causes.

### Key Principle
**Root cause over symptom treatment.** Never be satisfied with making symptoms disappear. Understand WHY the bug occurred and fix the underlying cause.

### When to Use This Skill

**MUST USE when:**
- Bug spans multiple files or components
- Involves race conditions or timing issues
- Has eluded initial investigation attempts (>30 minutes)
- Symptoms are intermittent or hard to reproduce
- Previous fix attempts have failed

**SHOULD USE when:**
- Bug is in unfamiliar code
- Error messages are unclear or misleading
- Multiple hypotheses are possible
- System behavior is unexpected

---

## The DEBUG Framework

A systematic approach to bug resolution. Follow these phases in order:

```
D → E → B → U → G
│   │   │   │   │
│   │   │   │   └─ GUARD: Implement fix and prevent regression
│   │   │   └───── UNCOVER: Identify root cause using RCA techniques
│   │   └───────── BISECT: Narrow down using binary search
│   └───────────── EXPLORE: Gather evidence, reproduce, collect data
└───────────────── DEFINE: State problem clearly (expected vs actual)
```

### D - Define the Problem

Before debugging, clearly articulate what's wrong:

```markdown
## Problem Definition

**Expected Behavior:**
[What SHOULD happen - be specific]

**Actual Behavior:**
[What ACTUALLY happens - be specific]

**Reproduction Steps:**
1. [Step 1]
2. [Step 2]
3. [Observe: Bug occurs]

**Environment:**
- OS: [Windows/Linux/macOS]
- Version: [Software version]
- Config: [Relevant configuration]

**First Occurrence:**
[When was this first observed?]
```

**Quality Check:**
- [ ] Can someone else understand the problem from this description?
- [ ] Are expected and actual behaviors clearly distinguished?
- [ ] Are reproduction steps precise enough to follow?

### E - Explore and Gather Evidence

Collect data before forming hypotheses:

**Evidence to Gather:**
1. **Error Messages**: Full stack traces, not just summaries
2. **Logs**: Surrounding context, not just the error line
3. **State**: Variable values at time of failure
4. **Timeline**: What changed recently?
5. **Scope**: Who else is affected?

**Evidence Collection Commands:**
```bash
# Recent changes that might have introduced the bug
git log --oneline -20

# Search for related error handling
grep -r "except\|catch\|error" --include="*.py" .

# Find where the problematic function is called
grep -r "function_name" --include="*.py" .
```

**Key Questions:**
- When did this last work correctly?
- What changed since then?
- Is the bug reproducible 100% of the time?
- Does it occur in all environments?

### B - Bisect and Narrow Down

Use binary search to isolate the bug:

**Code Bisection:**
```
Working Code ─────────────────────────── Broken Code
     │                                        │
     └──── Test Midpoint ───────────────────┘
                 │
        ┌───────┴───────┐
        │               │
    If broken       If working
    (left half)     (right half)
        │               │
        └───── Repeat ──┘
```

**Git Bisect (for regressions):**
```bash
git bisect start
git bisect bad HEAD                    # Current commit is broken
git bisect good abc123                 # Known good commit
# Git checks out midpoint
# Test and mark:
git bisect good  # or  git bisect bad
# Repeat until culprit found
git bisect reset                       # Return to HEAD
```

**Component Isolation:**
1. Create minimal reproduction case
2. Remove components one by one
3. When removal fixes the bug → that component contains it
4. Drill down within that component

### U - Uncover Root Cause

Apply Root Cause Analysis techniques:

**5 Whys (Primary Technique):**
```
Problem: API returns 500 error
  ↓ Why?
Database query failed
  ↓ Why?
Connection pool exhausted
  ↓ Why?
Connections not being released
  ↓ Why?
Exception handler missing close()
  ↓ Why?
Template code lacked finally block
  ↓
ROOT CAUSE: Missing resource cleanup pattern in error handling template
```

**Stop When:**
- You've identified a actionable fix point
- Further "why" questions leave your control (e.g., "why did the user do that?")
- You reach 5-7 levels (usually sufficient)

**Verification:**
Ask: "If we fix this root cause, would the bug have been prevented?"

### G - Guard Against Recurrence

A bug fix is incomplete without prevention:

**Fix Implementation:**
1. Fix the root cause (not just the symptom)
2. Add regression test that would have caught this
3. Update documentation if process gap found
4. Consider: Are there similar bugs elsewhere?

**Regression Test Template:**
```python
def test_bug_123_resource_cleanup_on_error():
    """
    Regression test for Bug #123.

    Root Cause: Exception handler didn't close database connection.
    Fix: Added finally block to ensure cleanup.

    This test verifies connections are released even when exceptions occur.
    """
    # Arrange
    initial_connections = get_active_connection_count()

    # Act - trigger the error condition
    with pytest.raises(ExpectedException):
        function_that_was_buggy()

    # Assert - connections are properly released
    assert get_active_connection_count() == initial_connections
```

**Prevention Checklist:**
- [ ] Root cause fix implemented (not just workaround)
- [ ] Regression test added
- [ ] Similar patterns searched and fixed
- [ ] Code review updated if applicable
- [ ] Documentation updated

---

## Bug Classification

Different bugs require different approaches. Use this decision tree:

### By Reproducibility

```
Is the bug reproducible?
├── YES (100% of the time)
│   └── Use: Standard debugging, breakpoints, logging
│
├── SOMETIMES (intermittent)
│   └── Use: Logging, state capture, timing analysis
│   └── Suspect: Race conditions, resource exhaustion, external dependencies
│
└── RARELY (hard to reproduce)
    └── Use: Defensive logging, assertions, monitoring
    └── Suspect: Memory corruption, cosmic rays (really: edge cases)
```

### By Bug Type

| Type | Symptoms | Primary Technique |
|------|----------|-------------------|
| **Logic** | Wrong output, incorrect calculations | Code review, test cases |
| **State** | Corruption, unexpected values | State logging, watchpoints |
| **Timing** | Race conditions, deadlocks | Thread analysis, timing logs |
| **Resource** | Leaks, exhaustion | Profiling, resource monitoring |
| **Integration** | API mismatches, version conflicts | Interface comparison, version audit |
| **Environment** | Works locally, fails elsewhere | Config comparison, dependency audit |

### Technique Selection Guide

```
┌─────────────────────────────────────────────────────────────┐
│                    BUG CLASSIFICATION                        │
├───────────────────┬─────────────────────────────────────────┤
│ If bug is...      │ Start with...                           │
├───────────────────┼─────────────────────────────────────────┤
│ Regression        │ Git Bisect → find introducing commit    │
│ Reproducible      │ Binary Search → isolate component       │
│ Intermittent      │ Enhanced Logging → capture state        │
│ Performance       │ Profiling → identify bottleneck         │
│ In unfamiliar code│ Rubber Duck → explain the flow          │
│ Timing-related    │ Sequence Diagram → visualize order      │
│ Multi-component   │ Isolation → test each component alone   │
└───────────────────┴─────────────────────────────────────────┘
```

---

## Core Techniques Quick Reference

### 5 Whys
Ask "why" repeatedly until root cause emerges. See: `reference/root-cause-analysis.md`

### Binary Search / Bisection
Divide search space in half repeatedly. See: `reference/debugging-techniques.md`

### Git Bisect
Automated binary search through commit history. See: `reference/debugging-techniques.md`

### Isolation / Minimal Reproduction
Create smallest possible case that exhibits bug. See: `reference/debugging-techniques.md`

### Rubber Duck Debugging
Explain code line-by-line to expose hidden assumptions:
1. State the problem clearly
2. Explain what the code SHOULD do
3. Walk through line by line, explaining each
4. Note any "wait, that's not right" moments
5. Investigate those moments

### Scientific Method
```
OBSERVE → HYPOTHESIZE → PREDICT → EXPERIMENT → ANALYZE → ITERATE
```
See: `templates/hypothesis-log.md`

---

## Integration with Debugger Subagent

This skill provides methodology. The `debugger` subagent provides execution with advanced tools.

### When to Escalate to Debugger Subagent

Escalate when:
- Standard techniques haven't worked after 3 attempts
- Bug requires multi-codebase analysis
- Need for advanced reasoning (Ultrathink methodology)
- Complex distributed system issues

### Handoff Protocol

Before escalating, prepare:

```markdown
## Debugger Escalation Context

### Bug Summary
[One paragraph describing the issue]

### DEBUG Progress
- [D] Define: [Problem statement]
- [E] Explore: [Evidence collected]
- [B] Bisect: [Narrowing done so far]
- [U] Uncover: [Hypotheses tested and results]
- [G] Guard: [Not yet - need fix first]

### Files Involved
- `path/to/file1.py:line` - [relevance]
- `path/to/file2.py:line` - [relevance]

### Hypotheses Tested
| Hypothesis | Test | Result |
|------------|------|--------|
| [H1] | [How tested] | Refuted |
| [H2] | [How tested] | Inconclusive |

### What's Needed
[Specific request for debugger subagent]
```

### Iteration Tracking

The debugger subagent has a **5-iteration limit**. Track attempts:

```markdown
## Debugging Iterations

### Iteration 1 (skill)
- Action: [What was tried]
- Result: [What happened]
- Next: [What to try next]

### Iteration 2 (skill)
...

### Iteration 3 → Escalate to debugger subagent
[Handoff context above]
```

---

## Quality Checklist

Before declaring a bug fixed:

### Must Pass
- [ ] **Root cause identified** - Not just symptom addressed
- [ ] **Fix tested** - Reproduction steps no longer reproduce bug
- [ ] **Regression test added** - Automated test that would catch recurrence
- [ ] **No new bugs** - Fix doesn't break other functionality

### Should Pass
- [ ] **Similar patterns checked** - Other code reviewed for same issue
- [ ] **Documentation updated** - If process/knowledge gap found
- [ ] **Code review complete** - Fix reviewed by another person
- [ ] **Monitoring added** - If applicable, alerts for similar issues

### Nice to Have
- [ ] **RCA report written** - For significant bugs
- [ ] **Team notified** - If learning opportunity for others
- [ ] **Process improved** - If systemic issue found

---

## Anti-Patterns to Avoid

These debugging mistakes waste time and often make things worse:

| Anti-Pattern | Why It's Bad | Better Approach |
|--------------|--------------|-----------------|
| **Shotgun debugging** | Random changes, no systematic approach | Use DEBUG framework |
| **Fixing symptoms** | Bug will return or manifest elsewhere | Find root cause with 5 Whys |
| **Skipping reproduction** | Can't verify fix | Always reproduce before fixing |
| **Ignoring intermittent bugs** | They get worse over time | Add logging, capture state |
| **Debug in production** | High risk, limited tools | Reproduce locally first |
| **Assuming the obvious** | Wastes time on wrong paths | Verify assumptions with tests |
| **Not adding tests** | Bug will recur | Always add regression test |

See: `reference/anti-patterns.md` for detailed examples.

---

## Templates

Use these templates to track debugging sessions:

| Template | Purpose | When to Use |
|----------|---------|-------------|
| `templates/debugging-session.md` | Track entire session | Every significant bug |
| `templates/root-cause-report.md` | Document RCA | After root cause found |
| `templates/hypothesis-log.md` | Track hypotheses | Multiple possible causes |

---

## Quick Start

For immediate bug investigation:

```markdown
## Quick DEBUG

**D - Define:**
Expected: [what should happen]
Actual: [what happens]
Steps: [to reproduce]

**E - Explore:**
Error: [full message]
Changed: [recent changes]
Scope: [who's affected]

**B - Bisect:**
Last working: [commit/date]
First broken: [commit/date]
Narrowed to: [component/file]

**U - Uncover:**
Why 1: [symptom reason]
Why 2: [deeper reason]
Why 3: [root cause]

**G - Guard:**
Fix: [what to change]
Test: [regression test]
```

---

## Reference Documentation

For detailed techniques and examples:

- `reference/root-cause-analysis.md` - 5 Whys, Fishbone, Fault Trees
- `reference/debugging-techniques.md` - Binary search, git bisect, isolation
- `reference/bug-classification.md` - Bug types and recommended approaches
- `reference/anti-patterns.md` - Common mistakes and consequences

---

## Summary

The DEBUG framework provides a systematic approach:

1. **D**efine clearly before investigating
2. **E**xplore thoroughly before hypothesizing
3. **B**isect methodically to narrow scope
4. **U**ncover root cause, not just symptoms
5. **G**uard against recurrence with tests

**Remember:** A bug isn't fixed until you understand WHY it occurred and have prevented it from recurring.
