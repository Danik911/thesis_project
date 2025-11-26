# Debugging Session Template

Copy this template to track your debugging session.

---

## Template

```markdown
# Debugging Session: [Bug ID/Description]

**Started:** [YYYY-MM-DD HH:MM]
**Status:** In Progress / Resolved / Blocked / Escalated

---

## D - Define the Problem

### Problem Statement
**Expected Behavior:**
[What SHOULD happen - be specific]

**Actual Behavior:**
[What ACTUALLY happens - be specific]

**Reproducible:** Yes / No / Intermittent (X out of Y attempts)

**First Observed:**
- When: [Date/Time]
- Where: [Environment - local/staging/production]
- Who: [Reporter]

### Reproduction Steps
1. [Step 1]
2. [Step 2]
3. [Step 3]
4. [Observe: Bug occurs]

### Environment
- OS: [Windows/Linux/macOS + version]
- Language/Runtime: [Python 3.12, Node 20, etc.]
- Framework: [FastAPI, React, etc.]
- Dependencies: [Key versions]
- Config: [Relevant settings]

---

## E - Explore Evidence

### Error Messages
```
[Full error message and stack trace]
```

### Relevant Logs
```
[Log excerpts with context]
```

### Recent Changes
- [ ] Code changes in last [X] days
- [ ] Config changes
- [ ] Dependency updates
- [ ] Infrastructure changes

**Git commits since last known good:**
```
[git log output]
```

### Scope Assessment
- Affected users: [All / Some / Single]
- Affected features: [List]
- Related bugs: [Links]

---

## B - Bisect and Narrow

### Last Known Good State
- Commit: [hash]
- Date: [when it worked]
- Version: [release]

### First Known Bad State
- Commit: [hash]
- Date: [when bug appeared]
- Version: [release]

### Bisection Progress
| Step | Range | Test Point | Result | New Range |
|------|-------|------------|--------|-----------|
| 1 | [a..z] | [m] | Bad | [a..m] |
| 2 | [a..m] | [g] | Good | [g..m] |
| ... | ... | ... | ... | ... |

### Narrowed Location
**Component:** [Which module/file]
**Function:** [Which function]
**Line range:** [Approximate lines]

---

## U - Uncover Root Cause

### Hypotheses

#### Hypothesis 1
**Statement:** [What I think is wrong]
**Confidence:** High / Medium / Low
**Test:** [How to verify]
**Result:** [What happened]
**Verdict:** Confirmed / Refuted / Inconclusive

#### Hypothesis 2
**Statement:** [What I think is wrong]
**Confidence:** High / Medium / Low
**Test:** [How to verify]
**Result:** [What happened]
**Verdict:** Confirmed / Refuted / Inconclusive

### 5 Whys Analysis
1. Why [symptom]?
   → [Answer 1]
2. Why [Answer 1]?
   → [Answer 2]
3. Why [Answer 2]?
   → [Answer 3]
4. Why [Answer 3]?
   → [Answer 4]
5. Why [Answer 4]?
   → **[ROOT CAUSE]**

### Root Cause Statement
[Clear explanation of what caused the bug]

---

## G - Guard with Fix

### Fix Implementation
**File(s) modified:**
- `[path/to/file.py]` - [What changed]

**Code change:**
```python
# Before
[old code]

# After
[new code]
```

### Verification
- [ ] Bug no longer reproduces with original steps
- [ ] Regression test added
- [ ] Related code reviewed for same issue
- [ ] No new test failures

### Regression Test
```python
def test_bug_[ID]_[description]():
    """
    Regression test for [Bug ID].
    Root cause: [Brief explanation]
    """
    # Test that the bug is fixed
    ...
```

---

## Investigation Log

### Attempt 1
**Time:** [HH:MM]
**Action:** [What I tried]
**Result:** [What happened]
**Learning:** [What this tells us]

### Attempt 2
**Time:** [HH:MM]
**Action:** [What I tried]
**Result:** [What happened]
**Learning:** [What this tells us]

[Continue as needed...]

---

## Summary

### Resolution
**Root Cause:** [One sentence]
**Fix:** [One sentence]
**Time Spent:** [X hours]

### Prevention
- [ ] Similar patterns checked elsewhere
- [ ] Process improvement identified
- [ ] Documentation updated

### Follow-up Actions
- [ ] [Action 1]
- [ ] [Action 2]

---

## Notes
[Any additional observations or learnings]
```

---

## Quick Session (For Simpler Bugs)

```markdown
# Quick Debug: [Description]

## Problem
Expected: [X]
Actual: [Y]
Steps: [1, 2, 3]

## Evidence
Error: [message]
Stack: [key frames]

## Hypotheses
1. [Guess] → [Test] → [Result]
2. [Guess] → [Test] → [Result]

## Root Cause
[Why it happened]

## Fix
[What I changed]

## Test
[How I verified]
```

---

## Usage Guidelines

1. **Start immediately** - Create the doc before diving in
2. **Update as you go** - Don't try to remember later
3. **Be specific** - Details matter for debugging
4. **Save even if unresolved** - Future you will thank you
5. **Link to commits** - Reference git hashes
