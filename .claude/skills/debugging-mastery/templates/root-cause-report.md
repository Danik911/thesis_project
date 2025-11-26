# Root Cause Analysis Report Template

Use this template after identifying a bug's root cause for documentation and knowledge sharing.

---

## Template

```markdown
# Root Cause Analysis Report

**Bug ID:** [Ticket/Issue number]
**Title:** [Brief description]
**Date:** [YYYY-MM-DD]
**Author:** [Name]

---

## Executive Summary

| Field | Value |
|-------|-------|
| **Bug** | [One-line description] |
| **Root Cause** | [One sentence] |
| **Fix** | [One sentence] |
| **Impact** | [Users/systems affected] |
| **Severity** | Critical / High / Medium / Low |
| **Time to Resolve** | [X hours/days] |

---

## Timeline

| Time | Event |
|------|-------|
| [Date/Time] | Bug first observed |
| [Date/Time] | Investigation started |
| [Date/Time] | Root cause identified |
| [Date/Time] | Fix implemented |
| [Date/Time] | Fix deployed |
| [Date/Time] | Verified in production |

---

## Problem Description

### Symptoms
[What users/systems experienced]

### Impact
- **Users affected:** [Number or percentage]
- **Duration:** [How long the issue persisted]
- **Business impact:** [Revenue, reputation, etc.]

### Reproduction Steps
1. [Step 1]
2. [Step 2]
3. [Observe: Bug occurs]

---

## Analysis

### 5 Whys

1. **Why** did [symptom] occur?
   → [Answer 1]

2. **Why** did [Answer 1] occur?
   → [Answer 2]

3. **Why** did [Answer 2] occur?
   → [Answer 3]

4. **Why** did [Answer 3] occur?
   → [Answer 4]

5. **Why** did [Answer 4] occur?
   → **ROOT CAUSE: [Final answer]**

### Root Cause Statement
[Detailed explanation of the root cause in 2-3 sentences]

### Contributing Factors
- **Factor 1:** [Description]
- **Factor 2:** [Description]
- **Factor 3:** [Description]

---

## Resolution

### Immediate Fix (Corrective Action)

**Description:** [What was changed]

**Code/Config Change:**
```
[Relevant code snippet or config change]
```

**Files Modified:**
- `[path/to/file.py]` - [What changed]

**Commit:** [Git hash or PR link]

### Verification
- [ ] Bug no longer reproduces
- [ ] Regression test added
- [ ] No new issues introduced
- [ ] Change reviewed and approved

---

## Prevention

### Systemic Improvements

| Action | Owner | Timeline | Status |
|--------|-------|----------|--------|
| [Preventive action 1] | [Name] | [Date] | Pending |
| [Preventive action 2] | [Name] | [Date] | Pending |
| [Preventive action 3] | [Name] | [Date] | Pending |

### Process Changes
- [New rule/process to prevent recurrence]

### Monitoring Added
- [New alert/metric to detect similar issues]

---

## Lessons Learned

### What Went Well
- [Positive aspect of debugging process]

### What Could Improve
- [Area for improvement]

### Key Takeaways
1. [Learning 1]
2. [Learning 2]
3. [Learning 3]

---

## Appendix

### Error Messages
```
[Full error messages and stack traces]
```

### Relevant Logs
```
[Log excerpts]
```

### References
- [Link to ticket]
- [Link to PR]
- [Link to related documentation]
```

---

## Quick RCA (For Smaller Issues)

```markdown
# Quick RCA: [Bug Title]

## Summary
- **Bug:** [What happened]
- **Root Cause:** [Why it happened]
- **Fix:** [What was changed]

## 5 Whys
1. Why? → [A1]
2. Why? → [A2]
3. Why? → [A3]
4. Why? → [A4]
5. Why? → **[ROOT CAUSE]**

## Actions
- [x] Fix implemented
- [x] Test added
- [ ] Prevention: [Action needed]

## Commit
[Git hash]
```

---

## Usage Guidelines

### When to Write Full RCA
- Critical/High severity bugs
- Bugs that affected many users
- Bugs that took >4 hours to resolve
- Recurring issues
- Bugs that indicate systemic problems

### When Quick RCA Suffices
- Low severity bugs
- Isolated issues
- Quick fixes (<1 hour)
- No systemic implications

### Sharing
- Post to team channel
- Add to knowledge base
- Review in retrospective
- Share with stakeholders if significant
