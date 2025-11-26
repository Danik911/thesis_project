# Debugging Anti-Patterns Reference

Common debugging mistakes and how to avoid them.

---

## Anti-Pattern 1: Shotgun Debugging

### What It Is
Making random changes hoping something will work, without systematic investigation.

### Why It's Bad
- Wastes time on wrong paths
- May introduce new bugs
- Doesn't build understanding
- "Fixes" may mask the real problem
- Changes can't be explained

### Signs You're Doing It
- "Let me try changing this..."
- Multiple uncommitted changes
- No hypothesis about cause
- Reverting changes frequently
- "I don't know why, but it works now"

### Better Approach
```markdown
INSTEAD OF:
1. Change A → didn't work
2. Change B → didn't work
3. Change A and B → didn't work
4. Change C → worked! (but why?)

DO THIS:
1. Form hypothesis: "The bug is caused by X"
2. Design test: "If X is the cause, then Y should happen"
3. Test hypothesis
4. If refuted → new hypothesis
5. If confirmed → fix with understanding
```

---

## Anti-Pattern 2: Fixing Symptoms

### What It Is
Addressing visible symptoms rather than underlying root cause.

### Why It's Bad
- Bug will return or appear elsewhere
- System becomes fragile with workarounds
- Technical debt accumulates
- Real issue grows worse

### Example

**Symptom fix (bad):**
```python
# Bug: API sometimes returns None
def get_user(id):
    result = api.fetch_user(id)
    if result is None:  # "Fix" the symptom
        return {"id": id, "name": "Unknown"}  # Fake data!
    return result
```

**Root cause fix (good):**
```python
# Investigate WHY api.fetch_user returns None
# Root cause: Connection timeout on slow network

def get_user(id):
    try:
        result = api.fetch_user(id, timeout=30)  # Proper timeout
        if result is None:
            raise UserNotFoundError(id)  # Proper error
        return result
    except TimeoutError:
        raise ServiceUnavailableError("API timeout")  # Clear failure
```

### How to Avoid
- Always ask "Why?" at least 3 times
- Be suspicious of quick fixes
- Ask: "Will this prevent the bug or just hide it?"

---

## Anti-Pattern 3: Skipping Reproduction

### What It Is
Trying to fix a bug without reliably reproducing it first.

### Why It's Bad
- Can't verify fix worked
- May fix wrong thing
- Bug will "come back" (was never fixed)
- Wastes time on guesses

### Better Approach
```markdown
1. ALWAYS reproduce before fixing
   - Write down exact steps
   - Verify you see the same bug
   - Create automated test if possible

2. If can't reproduce:
   - Collect more information
   - Add logging
   - Wait for next occurrence
   - DON'T guess at fix
```

---

## Anti-Pattern 4: Debug in Production

### What It Is
Debugging directly in production without reproducing locally first.

### Why It's Bad
- Limited debugging tools
- Risk to real users
- Pressure leads to mistakes
- Can't experiment safely
- Changes affect everyone

### When It's Necessary
- Bug only occurs in production
- Can't reproduce locally
- Urgent user impact

### Safe Production Debugging
```markdown
1. Add logging (not code changes)
2. Use feature flags to isolate
3. Have rollback ready
4. Limit blast radius
5. Work in low-traffic periods
6. Have another person review
```

---

## Anti-Pattern 5: Ignoring Error Messages

### What It Is
Not reading or dismissing error messages/stack traces.

### Why It's Bad
- Error message often tells you exactly what's wrong
- Stack trace shows where
- Wastes time on speculation

### Common Excuses
- "The error message is always wrong"
- "Stack traces are too long"
- "I know what's wrong"

### Better Approach
```markdown
1. Read the FULL error message
2. Read the FULL stack trace
3. Note:
   - What exception/error type?
   - What file and line?
   - What was the input/state?
4. Search for the exact error message
5. Only then form hypotheses
```

---

## Anti-Pattern 6: Assuming the Obvious

### What It Is
Jumping to conclusions about the cause without verification.

### Why It's Bad
- "Obvious" cause is often wrong
- Wastes time fixing wrong thing
- Confirmation bias blinds you

### Example
```
Developer: "The database must be down"
*Spends 2 hours on database*

Reality: API endpoint URL had typo
*Would have found in 5 minutes if checked*
```

### Better Approach
```markdown
BEFORE assuming:
1. What evidence supports this assumption?
2. What evidence would disprove it?
3. What's the quickest way to verify?

DO verify:
- Check logs
- Test the specific component
- Prove your assumption
```

---

## Anti-Pattern 7: Not Adding Tests

### What It Is
Fixing a bug without adding a regression test.

### Why It's Bad
- Bug can easily return
- No documentation of the bug
- Same mistake will be made again
- Fix may be broken by future changes

### Better Approach
```python
# 1. FIRST write test that fails
def test_bug_123_empty_list_handling():
    """
    Regression test for Bug #123.
    get_average() should raise ValueError on empty list,
    not ZeroDivisionError.
    """
    with pytest.raises(ValueError, match="empty list"):
        get_average([])

# 2. THEN fix the code
def get_average(numbers):
    if not numbers:
        raise ValueError("Cannot compute average of empty list")
    return sum(numbers) / len(numbers)

# 3. Verify test passes
```

---

## Anti-Pattern 8: Solo Debugging Too Long

### What It Is
Struggling alone for hours when help is available.

### Why It's Bad
- Fresh eyes often spot issues quickly
- Rubber duck effect of explaining
- Knowledge sharing opportunity missed
- Time wasted

### Rule of Thumb
```
If stuck for:
- 30 min → Rubber duck (explain to yourself/object)
- 1 hour → Ask a colleague for fresh eyes
- 2 hours → Pair debugging session
- 4 hours → Team discussion / escalate
```

---

## Anti-Pattern 9: Debugging Without Version Control

### What It Is
Making changes without commits, branches, or ability to rollback.

### Why It's Bad
- Can't undo experiments
- Don't know what you changed
- May make things worse
- Lost work when reverting

### Better Approach
```bash
# BEFORE debugging
git stash              # Save current work
git checkout -b debug-bug-123

# DURING debugging
git add -p             # Stage only intentional changes
git commit -m "Debug: testing hypothesis X"

# AFTER debugging
git diff main          # See all changes
git checkout main && git merge debug-bug-123  # Keep fix
# OR
git checkout main && git branch -D debug-bug-123  # Discard
```

---

## Anti-Pattern 10: Premature Optimization Focus

### What It Is
Worrying about performance when there's a correctness bug.

### Why It's Bad
- Correct but slow > Fast but wrong
- Optimization often makes bugs harder to find
- Premature optimization = wasted effort

### Rule
```
First make it work.
Then make it right.
Then make it fast.

Never:
- Optimize code that doesn't work
- Assume performance is the bug (without profiling)
- Combine bug fix with optimization
```

---

## Anti-Pattern 11: Blame-First Debugging

### What It Is
Focusing on who caused the bug rather than fixing it.

### Why It's Bad
- Defensive reactions block information
- Doesn't fix the bug
- Creates hostile environment
- People hide issues

### Better Approach
```markdown
INSTEAD OF: "Who wrote this broken code?"
ASK: "What process allowed this bug to ship?"

INSTEAD OF: "This is John's fault"
ASK: "What can we improve to prevent this?"

Focus on:
- The code (not the person)
- The process (not the blame)
- The future (not the past)
```

---

## Anti-Pattern 12: Abandoning Debugging

### What It Is
Giving up on a bug without resolution.

### Why It's Bad
- Bug will get worse
- User trust erodes
- Technical debt grows
- Problem spreads

### Instead
```markdown
IF can't fix now:
1. Document what you learned
2. Create ticket with all findings
3. Add monitoring/logging
4. Set severity and priority
5. Schedule follow-up

NEVER just ignore a bug.
```

---

## Quick Reference

| Anti-Pattern | One-Line Fix |
|--------------|--------------|
| Shotgun debugging | Form hypothesis before changing |
| Fixing symptoms | Ask "why" 5 times |
| Skipping reproduction | Reproduce before fixing |
| Debug in production | Reproduce locally first |
| Ignoring errors | Read full message and stack |
| Assuming obvious | Verify assumptions |
| Not adding tests | Test first, then fix |
| Solo too long | Ask for help after 1 hour |
| No version control | Branch before debugging |
| Premature optimization | Make it work first |
| Blame-first | Focus on process, not people |
| Abandoning bugs | Document and schedule |
