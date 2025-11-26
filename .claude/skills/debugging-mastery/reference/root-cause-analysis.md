# Root Cause Analysis (RCA) Reference

Comprehensive guide to root cause analysis techniques for debugging.

---

## Overview

Root Cause Analysis is a systematic approach to identifying the underlying cause of a problem, rather than just addressing symptoms. In debugging, RCA helps ensure bugs don't recur.

**Key Principle:** Ask "why" until you reach something actionable.

---

## The 5 Whys Technique

### What It Is
A simple iterative technique where you ask "why" repeatedly (typically 5 times) to drill down from symptoms to root cause.

### When to Use
- Bug cause isn't immediately obvious
- Surface-level fix keeps breaking
- Need to understand systemic issues
- Want to prevent recurrence

### How to Apply

**Step 1:** State the problem clearly
**Step 2:** Ask "Why did this happen?"
**Step 3:** For each answer, ask "Why?" again
**Step 4:** Continue until you reach a root cause (actionable fix point)
**Step 5:** Verify by asking "If we fix this, would the problem have been prevented?"

### Example 1: API Error

```
PROBLEM: API returns 500 error on user login

Why 1: Why does the API return 500?
→ Database query throws exception

Why 2: Why does the database query throw exception?
→ Connection pool is exhausted

Why 3: Why is the connection pool exhausted?
→ Connections are not being released after use

Why 4: Why are connections not being released?
→ Exception handler doesn't close the connection

Why 5: Why doesn't exception handler close the connection?
→ Developer copied template code that lacked finally block

ROOT CAUSE: Code template missing proper resource cleanup pattern
FIX: Update template + fix all instances + add linting rule
```

### Example 2: Test Flakiness

```
PROBLEM: Test suite randomly fails in CI

Why 1: Why does the test fail?
→ Assertion on timestamp comparison fails

Why 2: Why does timestamp comparison fail?
→ Expected and actual times differ by milliseconds

Why 3: Why do times differ by milliseconds?
→ Test creates timestamp before slow operation completes

Why 4: Why is there a slow operation during test?
→ Test hits real database instead of mock

Why 5: Why does test hit real database?
→ Mock wasn't properly injected due to import order

ROOT CAUSE: Test dependency injection happens after import-time DB init
FIX: Lazy initialization of DB connection + fix import order
```

### Example 3: Memory Leak

```
PROBLEM: Application memory grows continuously

Why 1: Why does memory grow?
→ Objects are being created but not garbage collected

Why 2: Why aren't objects garbage collected?
→ References are held in a global cache

Why 3: Why does cache hold references indefinitely?
→ Cache has no eviction policy

Why 4: Why is there no eviction policy?
→ Cache was added as quick fix without proper design

Why 5: Why was it a quick fix?
→ Original bug required immediate hotfix, cache "temporarily" added

ROOT CAUSE: Technical debt from quick fix not followed up
FIX: Implement proper cache with TTL + size limits + add to tech debt process
```

### Tips for Effective 5 Whys

1. **Be specific** - Vague answers lead to vague root causes
2. **Focus on process** - "Why did the process allow this?" not "Who made the mistake?"
3. **Don't stop too early** - Surface causes feel like answers but often aren't
4. **Don't go too far** - Stop at actionable items within your control
5. **Branch when needed** - Sometimes one "why" has multiple answers
6. **Verify at end** - Confirm root cause would have prevented issue

### Common Mistakes

| Mistake | Problem | Better |
|---------|---------|--------|
| Stopping at first answer | Fixes symptom, not cause | Keep asking why |
| Blaming people | Doesn't improve system | Ask about process |
| Being too vague | Can't create specific fix | Be precise |
| Going too deep | Reaches unactionable causes | Stop at your control boundary |
| Single-threading | Misses contributing factors | Branch when multiple causes exist |

---

## Fishbone Diagram (Ishikawa)

### What It Is
A visual tool that categorizes potential causes into major categories, creating a "fishbone" structure.

### When to Use
- Multiple potential cause categories
- Team brainstorming session
- Complex systems with many components
- Need to visualize cause relationships

### Standard Categories (6 M's)

```
                    ┌─── Methods
                    │
        ┌─── Materials       ┌─── Machines
        │                    │
        │                    │
────────┴────────────────────┴──────────→ PROBLEM
        │                    │
        │                    │
        └─── Measurements    └─── Manpower
                    │
                    └─── Mother Nature
                         (Environment)
```

### Software-Adapted Categories

```
            ┌─── Code               ┌─── Infrastructure
            │                       │
   ┌─── Configuration      ┌─── Dependencies
   │                       │
   │                       │
───┴───────────────────────┴───────────────→ BUG
   │                       │
   │                       │
   └─── Data              └─── Environment
            │                       │
            └─── Process           └─── External Services
```

### Example: API Performance Bug

```
        ┌─── Code                       ┌─── Infrastructure
        │   ├─ N+1 queries              │   ├─ Undersized instances
        │   ├─ Missing indexes          │   └─ Network latency
        │   └─ Synchronous calls        │
        │                               │
────────┴───────────────────────────────┴──────→ SLOW API
        │                               │
        │                               │
        └─── Database                   └─── External APIs
            ├─ Connection pool small        ├─ Rate limiting
            ├─ Query plan changed           └─ Increased latency
            └─ Data volume growth
```

### How to Create

1. Draw the "spine" → problem at the head
2. Add major category "bones"
3. Brainstorm causes for each category
4. Add sub-causes branching from main causes
5. Identify most likely causes to investigate first

---

## Fault Tree Analysis (FTA)

### What It Is
A top-down, deductive approach that starts with the failure and works backward through possible causes using logic gates.

### When to Use
- Safety-critical systems
- Complex failure modes
- Need to understand failure probability
- Multiple conditions must combine for failure

### Logic Gates

```
AND Gate (all inputs required):
    A ─┬─┐
       │  ├─→ Output occurs only if A AND B
    B ─┴─┘

OR Gate (any input sufficient):
    A ─┬─┐
       │  ├─→ Output occurs if A OR B
    B ─┴─┘
```

### Example: Authentication Failure

```
                    ┌──────────────────────┐
                    │  USER CAN'T LOGIN    │
                    └──────────┬───────────┘
                               │
                            (OR)
              ┌────────────────┼────────────────┐
              │                │                │
    ┌─────────┴──────┐ ┌──────┴───────┐ ┌──────┴───────┐
    │ Invalid        │ │ Auth Service │ │ Session      │
    │ Credentials    │ │ Down         │ │ Error        │
    └────────┬───────┘ └──────┬───────┘ └──────┬───────┘
             │                │                │
          (OR)             (OR)             (AND)
      ┌────┴────┐      ┌────┴────┐      ┌────┴────┐
      │         │      │         │      │         │
   Wrong    Account  Server   Network  Cookie   Cache
   Password Locked   Crash    Issue   Invalid  Stale
```

### How to Create

1. Define top event (the failure)
2. Identify immediate causes (first level)
3. For each cause, determine if it's AND or OR
4. Continue decomposing until reaching basic events
5. Evaluate which paths are most likely

---

## Pareto Analysis (80/20 Rule)

### What It Is
Focuses debugging effort on the 20% of causes that produce 80% of bugs.

### When to Use
- Prioritizing multiple bugs
- Limited debugging time
- Pattern recognition across bugs
- Resource allocation decisions

### How to Apply

1. **Collect data** on bug occurrences by category
2. **Count frequency** for each category
3. **Calculate percentages** and cumulative percentage
4. **Create Pareto chart** (bar + line graph)
5. **Focus on top categories** (usually 2-3)

### Example: Bug Categories

| Category | Count | % | Cumulative % |
|----------|-------|---|--------------|
| Null pointer | 45 | 35% | 35% |
| Off-by-one | 30 | 23% | 58% |
| Race condition | 22 | 17% | 75% |
| Type mismatch | 15 | 12% | 87% |
| Encoding | 10 | 8% | 95% |
| Other | 6 | 5% | 100% |

**Insight:** Focus on null pointer and off-by-one → addresses 58% of bugs

---

## Change Analysis

### What It Is
Compares working state to broken state to identify what changed.

### When to Use
- Bug appeared suddenly
- Known last-working state exists
- System was stable before
- Deployment-related issues

### Comparison Areas

| Area | Questions |
|------|-----------|
| **Code** | What commits since last working? |
| **Config** | Any config file changes? |
| **Dependencies** | Package versions changed? |
| **Data** | Data patterns changed? |
| **Infrastructure** | Server/network changes? |
| **External** | Third-party API changes? |

### Change Timeline Template

```markdown
## Change Timeline

### Last Known Good
- Date: YYYY-MM-DD HH:MM
- Commit: abc123
- Config: [snapshot]
- Deps: [versions]

### First Known Bad
- Date: YYYY-MM-DD HH:MM
- Commit: def456
- Config: [snapshot]
- Deps: [versions]

### Changes Between
1. [Change 1] - [Who] - [When]
2. [Change 2] - [Who] - [When]
3. [Change 3] - [Who] - [When]

### Most Likely Cause
[Change X] because [reasoning]
```

---

## Choosing the Right Technique

| Situation | Best Technique |
|-----------|---------------|
| Single bug, unclear cause | 5 Whys |
| Team debugging session | Fishbone Diagram |
| Safety-critical system | Fault Tree Analysis |
| Many bugs, limited time | Pareto Analysis |
| Sudden regression | Change Analysis |
| Complex multi-factor issue | Combined approach |

---

## RCA Report Template

After completing root cause analysis:

```markdown
# Root Cause Analysis: [Bug ID/Title]

## Summary
- **Issue:** [One-line description]
- **Root Cause:** [One sentence]
- **Fix:** [One sentence]
- **Prevention:** [One sentence]

## Timeline
- **First Observed:** [Date/Time]
- **Reproduced:** [Date/Time]
- **Root Cause Found:** [Date/Time]
- **Fix Deployed:** [Date/Time]

## Analysis Method
[5 Whys / Fishbone / FTA / etc.]

## Analysis

### 5 Whys
1. Why [symptom]? → [Answer 1]
2. Why [Answer 1]? → [Answer 2]
3. Why [Answer 2]? → [Answer 3]
4. Why [Answer 3]? → [Answer 4]
5. Why [Answer 4]? → **[ROOT CAUSE]**

## Contributing Factors
- [Factor 1]
- [Factor 2]

## Actions Taken

### Immediate (Corrective)
| Action | Owner | Status |
|--------|-------|--------|
| [Fix root cause] | [Name] | Done |
| [Regression test] | [Name] | Done |

### Long-term (Preventive)
| Action | Timeline |
|--------|----------|
| [Systemic improvement] | [When] |
| [Process change] | [When] |

## Lessons Learned
[What the team should remember]
```
