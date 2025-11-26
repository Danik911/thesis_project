# Hypothesis Log Template

Track hypotheses systematically using the scientific method for debugging.

---

## Template

```markdown
# Hypothesis Log: [Bug Description]

**Bug ID:** [Ticket number]
**Started:** [YYYY-MM-DD HH:MM]
**Status:** Investigating / Root Cause Found / Blocked

---

## Problem Statement

**Expected:** [What should happen]
**Actual:** [What happens instead]
**Reproducible:** Yes / No / Intermittent

---

## Hypothesis 1

### Statement
[Clear, testable statement about what might be wrong]

**Example:** "The API returns 500 because the database connection pool is exhausted"

### Confidence Level
- [ ] High (>70%) - Strong evidence points to this
- [ ] Medium (30-70%) - Some evidence, worth testing
- [ ] Low (<30%) - Speculation, test if others fail

### Evidence

**For (supports hypothesis):**
- [Evidence 1]
- [Evidence 2]

**Against (contradicts hypothesis):**
- [Counter-evidence 1]
- [Counter-evidence 2]

### Test Plan
**Method:** [How to test this hypothesis]
**Prediction:** If hypothesis is true, then [X] should happen
**Effort:** Low / Medium / High

### Experiment
**Steps taken:**
1. [What I did]
2. [What I did]

**Observations:**
[What I observed]

### Result
**Outcome:** [What actually happened]
**Matches prediction:** Yes / No / Partially

### Verdict
- [ ] **CONFIRMED** - Evidence supports hypothesis
- [ ] **REFUTED** - Evidence contradicts hypothesis
- [ ] **INCONCLUSIVE** - Need more data

### Next Action
[What to do based on this result]

---

## Hypothesis 2

### Statement
[Another potential cause]

### Confidence Level
- [ ] High
- [ ] Medium
- [ ] Low

### Evidence
**For:** [Evidence]
**Against:** [Counter-evidence]

### Test Plan
**Method:** [How to test]
**Prediction:** [Expected outcome if true]

### Experiment
[What was done and observed]

### Verdict
- [ ] CONFIRMED
- [ ] REFUTED
- [ ] INCONCLUSIVE

---

## Hypothesis 3

[Continue pattern as needed...]

---

## Summary Table

| # | Hypothesis | Confidence | Verdict | Notes |
|---|------------|------------|---------|-------|
| 1 | [Brief statement] | High/Med/Low | Confirmed/Refuted/? | [Key finding] |
| 2 | [Brief statement] | High/Med/Low | Confirmed/Refuted/? | [Key finding] |
| 3 | [Brief statement] | High/Med/Low | Confirmed/Refuted/? | [Key finding] |

---

## Root Cause Determination

**Confirmed hypothesis:** #[Number]
**Root cause:** [Clear statement]
**Confidence:** High / Medium

**Supporting evidence:**
1. [Evidence 1]
2. [Evidence 2]
3. [Evidence 3]

---

## Lessons for Future

**What worked:**
- [Effective technique]

**What didn't work:**
- [Ineffective approach]

**Time breakdown:**
- Hypothesis generation: [X min]
- Testing hypotheses: [X min]
- Total investigation: [X hours]
```

---

## Quick Hypothesis Log

For simpler bugs or time-constrained debugging:

```markdown
# Hypotheses: [Bug]

| # | Guess | Test | Result |
|---|-------|------|--------|
| 1 | [Cause] | [How tested] | Refuted |
| 2 | [Cause] | [How tested] | **CONFIRMED** |
| 3 | [Cause] | [Skipped] | - |

**Root Cause:** [Hypothesis 2 - explanation]
```

---

## Hypothesis Generation Tips

### Good Hypothesis Characteristics
- **Specific:** "Connection pool is exhausted" not "Something's wrong with the database"
- **Testable:** Can be verified or refuted
- **Falsifiable:** Possible to prove wrong
- **Relevant:** Related to observed symptoms

### Generating Hypotheses

**From symptoms:**
- What could cause this error message?
- What changed recently?
- What's different from working cases?

**From knowledge:**
- Common causes of this type of bug
- Known issues in this area
- Similar past bugs

**From exploration:**
- What the code actually does
- What state exists at failure point
- What the logs show

### Prioritizing Hypotheses

Test in this order:
1. **High confidence + Low effort** - Quick wins
2. **High confidence + High effort** - Likely root cause
3. **Low confidence + Low effort** - Easy to rule out
4. **Low confidence + High effort** - Last resort

---

## Common Hypothesis Categories

| Category | Example Hypotheses |
|----------|-------------------|
| **Data** | Invalid input, null value, encoding issue |
| **State** | Uninitialized, stale cache, race condition |
| **Config** | Wrong setting, missing env var, wrong file |
| **Dependency** | Version mismatch, service down, API changed |
| **Resource** | Memory exhausted, connection pool full, timeout |
| **Logic** | Wrong condition, off-by-one, missing case |
| **Environment** | Works locally fails in CI, OS difference |

---

## When to Stop

Stop generating hypotheses when:
- You've found and confirmed the root cause
- You've exhausted reasonable possibilities
- You need more data (add logging and wait)
- You should escalate (bring in more expertise)

**Red flags to escalate:**
- >5 hypotheses tested, none confirmed
- >2 hours without progress
- Hypothesis requires expertise you lack
- Intermittent bug that won't reproduce
