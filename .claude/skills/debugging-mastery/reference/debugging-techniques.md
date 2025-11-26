# Debugging Techniques Reference

Practical techniques for isolating and identifying bugs in code.

---

## Binary Search / Code Bisection

### What It Is
Systematically halving the search space until the bug location is found.

### When to Use
- Bug is somewhere in a large codebase
- Clear "working" and "broken" states exist
- Bug is deterministic (reproducible)

### How to Apply

**General Process:**
```
1. Identify boundaries
   - Working state (code, commit, config)
   - Broken state

2. Test midpoint
   - Add checkpoint or test at halfway point
   - Verify: working or broken?

3. Narrow scope
   - If broken → bug is in first half
   - If working → bug is in second half

4. Repeat
   - Halve the remaining scope
   - Continue until single change/location found
```

**Code Bisection Example:**

```python
def complex_function():
    step1()  # ← Add print("checkpoint 1 OK")
    step2()
    step3()
    step4()  # ← Add print("checkpoint 4 OK")
    step5()
    step6()
    step7()
    step8()

# If checkpoint 4 prints → bug is in steps 5-8
# If checkpoint 4 doesn't print → bug is in steps 1-4
# Add checkpoint at step 2 (or 6), repeat
```

**Function Bisection:**

```python
# Suspect one of these functions causes the bug
result = (
    func_a(data)      # Comment out half
    .pipe(func_b)
    .pipe(func_c)     # ← Start here: test with just a,b,c
    .pipe(func_d)
    .pipe(func_e)
    .pipe(func_f)
)

# If bug persists with a,b,c → problem is in first half
# If bug disappears → problem is in d,e,f
```

---

## Git Bisect

### What It Is
Automated binary search through commit history to find the commit that introduced a bug.

### When to Use
- Bug is a regression (used to work)
- Can identify a known-good commit
- Bug is reliably reproducible
- Commit history is meaningful (small commits)

### Basic Workflow

```bash
# Start bisect
git bisect start

# Mark current (broken) commit as bad
git bisect bad HEAD

# Mark known-good commit as good
git bisect good abc123

# Git checks out middle commit
# Test if bug exists...

# If bug exists in this commit:
git bisect bad

# If bug doesn't exist:
git bisect good

# Repeat until Git identifies the first bad commit
# Output: "abc123 is the first bad commit"

# Reset to original HEAD when done
git bisect reset
```

### Automated Bisect

Use a test script to automate:

```bash
# Create test script
cat > test_bug.sh << 'EOF'
#!/bin/bash
# Exit 0 = good (no bug), Exit 1 = bad (bug exists)
python -c "
from mymodule import function_under_test
result = function_under_test()
assert result == expected_value
" && exit 0 || exit 1
EOF

chmod +x test_bug.sh

# Run automated bisect
git bisect start
git bisect bad HEAD
git bisect good v1.0.0
git bisect run ./test_bug.sh

# Git automatically finds the offending commit
```

### Tips for Git Bisect

1. **Use meaningful "good" commit** - Pick a version you're confident worked
2. **Simple test** - Make the test quick and reliable
3. **Handle build failures** - Use `git bisect skip` for broken commits
4. **Verify result** - Check the identified commit actually makes sense
5. **Document findings** - Note the commit hash in your bug report

### Handling Broken Intermediate Commits

```bash
# If a commit doesn't compile or can't be tested:
git bisect skip

# Or skip a range of commits:
git bisect skip v1.0..v1.5
```

---

## Isolation / Minimal Reproduction

### What It Is
Creating the smallest possible code that still exhibits the bug.

### When to Use
- Bug is entangled in complex system
- Need to share bug report with others
- Bug is hard to understand in context
- Want to test fixes safely

### Process

```
1. Start with failing case
   └─ Full system exhibiting the bug

2. Remove components one by one
   ├─ Remove unused imports
   ├─ Remove unrelated functions
   ├─ Simplify data structures
   └─ After each removal: does bug still occur?

3. Identify the core
   └─ Minimal code that still shows bug

4. Verify isolation
   └─ Bug is in isolated code, not removed parts
```

### Example: API Bug

**Original (complex):**
```python
class ComplexService:
    def __init__(self, db, cache, logger, metrics):
        self.db = db
        self.cache = cache
        self.logger = logger
        self.metrics = metrics

    async def process_request(self, user_id, payload):
        self.logger.info(f"Processing {user_id}")
        cached = await self.cache.get(user_id)
        if cached:
            self.metrics.cache_hit()
            return cached
        self.metrics.cache_miss()
        result = await self.db.query(payload)
        await self.cache.set(user_id, result)
        return result  # BUG: Sometimes returns None
```

**Minimal reproduction:**
```python
async def minimal_repro():
    # Bug: empty payload causes None return
    result = await db.query({})  # Empty dict
    return result  # Returns None instead of raising

# Root cause: query() returns None for empty input
# instead of raising ValueError
```

### Isolation Checklist

- [ ] Removed all unused imports
- [ ] Removed all unrelated classes/functions
- [ ] Simplified data to minimum that triggers bug
- [ ] Removed logging, metrics, caching (unless they're the bug)
- [ ] Verified bug still reproduces
- [ ] Code can run independently

---

## Differential Debugging

### What It Is
Comparing working and broken states side by side to spot differences.

### When to Use
- "It works on my machine" scenarios
- Bug in one environment but not another
- Intermittent bugs
- Recent code changes broke something

### Comparison Areas

| Area | How to Compare |
|------|----------------|
| **Code** | `git diff good_commit bad_commit` |
| **Config** | `diff config_good.yaml config_bad.yaml` |
| **Environment** | Compare env vars, versions |
| **Data** | Compare input data sets |
| **State** | Log and compare runtime state |

### Side-by-Side State Logging

```python
import json

def log_state(label, state):
    """Log state for differential debugging."""
    print(f"=== {label} ===")
    print(json.dumps(state, indent=2, default=str))

# In working environment
log_state("WORKING", {
    "config": config.__dict__,
    "input": input_data,
    "env": dict(os.environ),
})

# In broken environment
log_state("BROKEN", {
    "config": config.__dict__,
    "input": input_data,
    "env": dict(os.environ),
})

# Compare outputs to find differences
```

---

## Strategic Logging

### What It Is
Adding temporary logging to understand code flow and state.

### When to Use
- Need to understand execution path
- Tracking down where values change
- Debugging without debugger (production)
- Async/concurrent code

### Logging Patterns

**Execution Flow:**
```python
def complex_function(data):
    print(f">>> complex_function ENTER: data={data}")

    if condition:
        print(">>> Branch: condition=True")
        result = path_a(data)
    else:
        print(">>> Branch: condition=False")
        result = path_b(data)

    print(f">>> complex_function EXIT: result={result}")
    return result
```

**State Tracking:**
```python
def process_items(items):
    for i, item in enumerate(items):
        print(f"[{i}] Processing: {item}")
        result = transform(item)
        print(f"[{i}] Result: {result}")
        # If bug: which iteration? What was the state?
```

**Async Flow:**
```python
import asyncio

async def async_operation(id):
    print(f"[{id}] START at {asyncio.get_event_loop().time()}")
    result = await do_work()
    print(f"[{id}] END at {asyncio.get_event_loop().time()}")
    return result

# Helps identify timing issues, race conditions
```

### Log Levels for Debugging

```python
import logging

# Temporarily increase verbosity
logging.getLogger("mymodule").setLevel(logging.DEBUG)

# Strategic debug logs
logger.debug(f"Input validation: {input_data}")
logger.debug(f"Cache lookup: key={key}, hit={hit}")
logger.debug(f"Query result: {len(results)} rows")
```

---

## Breakpoint Strategy

### What It Is
Strategically placing breakpoints to pause execution and inspect state.

### When to Use
- Interactive debugging available
- Need to inspect complex state
- Step through logic flow
- Modify state during execution

### Breakpoint Types

| Type | Use Case |
|------|----------|
| **Line breakpoint** | Stop at specific line |
| **Conditional** | Stop only when condition true |
| **Logpoint** | Log without stopping |
| **Exception** | Stop when exception raised |
| **Data** | Stop when variable changes |

### Python Breakpoint Patterns

```python
# Built-in breakpoint (Python 3.7+)
def function_to_debug():
    x = compute_something()
    breakpoint()  # Execution pauses here
    return process(x)

# Conditional breakpoint
def loop_debug():
    for i in range(1000):
        if i == 500:  # Only break on specific iteration
            breakpoint()
        process(i)

# Post-mortem debugging (after exception)
import pdb
try:
    buggy_code()
except Exception:
    pdb.post_mortem()  # Debug at point of failure
```

### IDE Breakpoint Strategy

```
1. Set breakpoint at entry point
2. Step over (F10) to find failing line
3. Step into (F11) to examine function
4. Inspect variables in watch/locals panel
5. Set conditional breakpoint if in loop
6. Continue (F5) to next breakpoint
```

---

## Rubber Duck Debugging

### What It Is
Explaining code line by line to expose hidden assumptions.

### When to Use
- Stuck and out of ideas
- Code "should work" but doesn't
- Need fresh perspective
- Reviewing unfamiliar code

### Protocol

```markdown
1. STATE THE PROBLEM
   "I'm trying to [goal], but [what happens instead]"

2. EXPLAIN THE CODE'S PURPOSE
   "This function is supposed to [high-level purpose]"

3. WALK THROUGH LINE BY LINE
   For each line:
   - What does this line do?
   - What values does it use?
   - What result does it produce?
   - Does this match expectations?

4. NOTE SURPRISES
   Any "wait, that's not right" → investigate

5. INVESTIGATE SURPRISES
   Each surprise is a potential bug location
```

### Example Session

```python
# Code to debug
def calculate_average(numbers):
    total = 0
    for num in numbers:
        total += num
    return total / len(numbers)

# Rubber duck session:
# "This calculates the average of a list..."
# "Line 2: total starts at 0, correct"
# "Line 3-4: adds each number to total, correct"
# "Line 5: divides total by... wait"
# "What if numbers is empty? Division by zero!"

# BUG FOUND: Missing empty list check
```

---

## Printf Debugging

### What It Is
Strategic print statements to trace execution (when debuggers aren't available).

### When to Use
- No debugger available (production, embedded)
- Debugger changes behavior (timing bugs)
- Quick investigation
- Remote debugging

### Patterns

**Entry/Exit Pattern:**
```python
def function(arg):
    print(f"ENTER function({arg})")
    # ... code ...
    print(f"EXIT function -> {result}")
    return result
```

**Checkpoint Pattern:**
```python
def complex():
    print("CHECKPOINT 1: starting")
    do_a()
    print("CHECKPOINT 2: after A")
    do_b()
    print("CHECKPOINT 3: after B")
    # If only checkpoints 1,2 print → bug in do_b()
```

**Value Tracking Pattern:**
```python
def process(data):
    print(f"data type: {type(data)}, len: {len(data)}")
    print(f"data sample: {data[:3]}...")
    result = transform(data)
    print(f"result type: {type(result)}, value: {result}")
```

### Cleanup

After debugging, remove or convert to proper logging:

```python
# Debug (remove)
print(f"DEBUG: x={x}")

# Keep as proper logging
import logging
logger.debug(f"x={x}")
```

---

## Technique Selection Quick Reference

| Scenario | Best Technique |
|----------|---------------|
| Regression (used to work) | Git Bisect |
| Large codebase, unknown location | Binary Search |
| Complex bug, need to share | Isolation / Minimal Repro |
| "Works on my machine" | Differential Debugging |
| Production debugging | Strategic Logging |
| Interactive debugging | Breakpoints |
| Stuck, out of ideas | Rubber Duck |
| No debugger available | Printf Debugging |
