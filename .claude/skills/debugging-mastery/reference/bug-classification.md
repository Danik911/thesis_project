# Bug Classification Reference

Categorize bugs to select the most effective debugging approach.

---

## Classification Decision Tree

Use this flowchart to quickly classify a bug and select techniques:

```
START: Bug Detected
       │
       ▼
┌──────────────────────────────┐
│ Can you reproduce it?        │
└──────────────────────────────┘
       │
   ┌───┴───┐
   │       │
  YES     NO
   │       │
   ▼       ▼
Reproducible    Intermittent
Bug             Bug
   │               │
   ▼               ▼
┌────────────┐  ┌────────────────────────┐
│ Did it     │  │ Happens under          │
│ used to    │  │ specific conditions?   │
│ work?      │  └────────────────────────┘
└────────────┘         │
   │              ┌────┴────┐
   ├───YES───┐    │         │
   │         │   YES        NO
   │         ▼    │         │
   │    REGRESSION│         ▼
   │    → Git     │    HEISENBUG
   │      Bisect  │    → Enhanced
   │              │      Logging
   ▼              ▼
  NEW BUG    Timing/State
  → Binary   → Isolation +
    Search     State Capture
```

---

## Bug Types by Category

### 1. Logic Bugs

**Description:** Code does wrong computation or makes wrong decisions.

**Symptoms:**
- Wrong output values
- Incorrect behavior
- Failed assertions
- Edge cases fail

**Common Causes:**
- Off-by-one errors
- Wrong operator (< vs <=)
- Incorrect algorithm
- Missing edge case handling
- Copy-paste errors

**Best Techniques:**
1. Code review / walkthrough
2. Rubber duck debugging
3. Unit tests with edge cases
4. Assertions at key points

**Example:**
```python
# Bug: Off-by-one in range
for i in range(len(items) - 1):  # Misses last item
    process(items[i])

# Fix:
for i in range(len(items)):
    process(items[i])
```

---

### 2. State Bugs

**Description:** Incorrect state management or unexpected state changes.

**Symptoms:**
- Data corruption
- Unexpected None/null values
- Wrong values after certain operations
- State persists unexpectedly

**Common Causes:**
- Uninitialized variables
- Shared mutable state
- Missing state reset
- Incorrect state transitions
- Stale cached data

**Best Techniques:**
1. State logging at transitions
2. Watchpoints on variables
3. State machine validation
4. Immutable data patterns

**Example:**
```python
# Bug: Shared mutable default
def add_item(item, items=[]):  # Shared across calls!
    items.append(item)
    return items

# Fix:
def add_item(item, items=None):
    if items is None:
        items = []
    items.append(item)
    return items
```

---

### 3. Timing Bugs

**Description:** Issues related to timing, concurrency, or ordering.

**Symptoms:**
- Works sometimes, fails sometimes
- Different behavior under load
- Deadlocks or hangs
- Data races

**Types:**
- **Race condition:** Outcome depends on execution order
- **Deadlock:** Two+ threads waiting for each other
- **Livelock:** Threads actively trying but making no progress
- **Starvation:** Thread never gets resources

**Best Techniques:**
1. Sequence diagrams
2. Thread/async tracing
3. Deterministic testing (controlled ordering)
4. Static analysis tools

**Example:**
```python
# Bug: Race condition
class Counter:
    def __init__(self):
        self.value = 0

    def increment(self):
        # Not atomic - race condition!
        self.value = self.value + 1

# Fix:
import threading

class Counter:
    def __init__(self):
        self.value = 0
        self.lock = threading.Lock()

    def increment(self):
        with self.lock:
            self.value += 1
```

---

### 4. Resource Bugs

**Description:** Problems with resource allocation, usage, or cleanup.

**Symptoms:**
- Memory growth over time
- "Too many open files"
- Connection pool exhaustion
- Gradual performance degradation

**Types:**
- **Memory leak:** Objects not garbage collected
- **Handle leak:** File/socket handles not closed
- **Connection leak:** DB/network connections not released
- **Resource exhaustion:** Running out of limited resources

**Best Techniques:**
1. Profiling (memory, connections)
2. Resource monitoring over time
3. Code review for cleanup patterns
4. Context managers / RAII

**Example:**
```python
# Bug: File handle leak
def process_file(path):
    f = open(path)
    data = f.read()
    if not data:
        return None  # Leak! File not closed
    f.close()
    return data

# Fix:
def process_file(path):
    with open(path) as f:
        data = f.read()
        if not data:
            return None
        return data
```

---

### 5. Integration Bugs

**Description:** Problems at boundaries between components or systems.

**Symptoms:**
- Works in isolation, fails together
- API contract violations
- Version mismatches
- Serialization/deserialization errors

**Common Causes:**
- API changes without updating clients
- Incorrect assumptions about external services
- Protocol/format mismatches
- Timezone/encoding issues

**Best Techniques:**
1. Contract testing
2. Interface comparison (expected vs actual)
3. Request/response logging
4. Version audit

**Example:**
```python
# Bug: API changed from snake_case to camelCase
# Old API returned: {"user_name": "john"}
# New API returns: {"userName": "john"}

def get_username(response):
    return response["user_name"]  # KeyError now!

# Fix:
def get_username(response):
    return response.get("userName") or response.get("user_name")
```

---

### 6. Environment Bugs

**Description:** Bug exists in one environment but not another.

**Symptoms:**
- "Works on my machine"
- CI fails, local passes
- Production differs from staging
- Platform-specific failures

**Common Causes:**
- Different dependency versions
- Environment variable differences
- File path differences (OS)
- Timezone differences
- Permission differences

**Best Techniques:**
1. Environment comparison
2. Containerization (Docker)
3. Dependency pinning
4. Environment variable audit

**Example:**
```python
# Bug: Path separator differences
log_path = "logs\\app.log"  # Works Windows, fails Linux

# Fix:
from pathlib import Path
log_path = Path("logs") / "app.log"
```

---

### 7. Configuration Bugs

**Description:** Incorrect or missing configuration.

**Symptoms:**
- Default values being used unexpectedly
- Features disabled/enabled wrongly
- Connection to wrong services
- Security misconfigurations

**Common Causes:**
- Typos in config keys
- Missing required config
- Incorrect value types
- Config not loaded from expected source

**Best Techniques:**
1. Configuration validation at startup
2. Log effective configuration
3. Schema validation
4. Config diff between environments

**Example:**
```python
# Bug: Typo in config key
db_host = config.get("databse_host", "localhost")  # Typo!
# Always connects to localhost, never reads config

# Fix:
db_host = config["database_host"]  # Fail fast if missing
# Or with validation:
assert "database_host" in config, "Missing database_host config"
```

---

### 8. Data Bugs

**Description:** Issues caused by unexpected data.

**Symptoms:**
- Works for some inputs, fails for others
- Edge cases fail
- Production data causes failures
- Special characters cause issues

**Common Causes:**
- Unexpected null/empty values
- Special characters (unicode, escape sequences)
- Boundary values (max int, empty list)
- Format assumptions violated

**Best Techniques:**
1. Data validation
2. Property-based testing
3. Fuzz testing
4. Boundary value analysis

**Example:**
```python
# Bug: Assumes non-empty list
def get_average(numbers):
    return sum(numbers) / len(numbers)  # ZeroDivisionError if empty

# Fix:
def get_average(numbers):
    if not numbers:
        raise ValueError("Cannot compute average of empty list")
    return sum(numbers) / len(numbers)
```

---

## Reproducibility Classification

| Level | Description | Approach |
|-------|-------------|----------|
| **Always** (100%) | Bug occurs every time | Standard debugging |
| **Usually** (>50%) | Bug occurs most times | Add logging, multiple runs |
| **Sometimes** (<50%) | Bug is intermittent | State capture, timing analysis |
| **Rarely** (<5%) | Bug is elusive | Defensive logging, monitoring |
| **Once** | Happened once | Forensic analysis, logs |

### Handling Intermittent Bugs

```
1. Capture everything
   - Add comprehensive logging
   - Record all state before/after
   - Include timestamps

2. Identify patterns
   - When does it happen? (Time, load)
   - What data was involved?
   - What else was running?

3. Increase frequency
   - Run tests in loop
   - Add artificial stress/load
   - Manipulate timing

4. Use deterministic tools
   - Record/replay debugging
   - Controlled thread scheduling
   - Chaos testing
```

---

## Quick Reference Table

| Bug Type | Key Symptom | First Technique |
|----------|-------------|-----------------|
| Logic | Wrong output | Code review |
| State | Corruption | State logging |
| Timing | Intermittent | Sequence diagram |
| Resource | Gradual degradation | Profiling |
| Integration | Works alone, fails together | Interface comparison |
| Environment | "Works on my machine" | Env comparison |
| Configuration | Wrong behavior at startup | Config logging |
| Data | Some inputs fail | Data validation |

---

## Bug Severity Classification

For prioritization:

| Severity | Impact | Response |
|----------|--------|----------|
| **Critical** | System down, data loss | Immediate fix |
| **High** | Major feature broken | Fix in hours |
| **Medium** | Feature impaired | Fix in days |
| **Low** | Minor inconvenience | Fix in sprint |
| **Trivial** | Cosmetic | Backlog |

Use severity + bug type to prioritize debugging efforts.
