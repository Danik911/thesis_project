# Template: Code Implementation Task

Use this template for tasks that involve writing or modifying code.

---

## Template

```markdown
# Task: [TASK_NAME]

## Role
You are a [ROLE] with expertise in [DOMAINS].
You prioritize [KEY_VALUES].

## Objective
[Clear statement of what code to write/modify]

## Context

### Project Background
- Project: [Name and purpose]
- Tech stack: [Languages, frameworks, key libraries]
- Current state: [Relevant context about existing code]

### Files to Read (Before Starting)
1. `[path/to/file1]` - [Purpose: what to learn from it]
2. `[path/to/file2]` - [Purpose: what to learn from it]
3. `[path/to/file3]` - [Purpose: what to learn from it]

## Requirements

### Functional Requirements
1. [What the code must DO - specific behavior]
2. [What the code must DO - specific behavior]
3. [What the code must DO - specific behavior]

### Technical Requirements
- [Language version/features to use]
- [Patterns to follow]
- [Dependencies allowed]

### Quality Requirements
- [ ] Type hints on all public functions
- [ ] Docstrings (Google/NumPy/Sphinx style)
- [ ] Error handling with context preservation
- [ ] Unit tests for new code

## Constraints

### DO NOT
- [Specific prohibition]
- [Specific prohibition]
- [Specific prohibition]

### Boundaries
- Only modify files in: `[path/to/directory/]`
- Do not change: `[protected files]`

## Implementation Guide

### Suggested Approach
1. [Step 1: What to do first]
2. [Step 2: What to do next]
3. [Step 3: Continue building]
4. [Step 4: Finalize]

### Pattern to Follow
Reference: `[path/to/example/file.py]`

```[language]
# Example pattern to replicate
[code snippet showing the pattern]
```

## Validation

### Commands to Run
```bash
# After implementation
pytest [test_path] -v
mypy [source_path]
ruff check [source_path]
```

### Expected Results
- Tests: All passing
- Type check: No errors
- Linting: No warnings

## Success Criteria
- [ ] [Specific, measurable criterion]
- [ ] [Specific, measurable criterion]
- [ ] [Specific, measurable criterion]
- [ ] All validation commands pass

## Output

### Deliverables
1. Implementation in `[path/to/new/file.py]`
2. Tests in `[path/to/test/file.py]`
3. Report (see format below)

### Report Format
```markdown
# Implementation Report: [Task Name]

## Summary
[What was implemented in 2-3 sentences]

## Files
| File | Action | Lines | Description |
|------|--------|-------|-------------|
| ... | created/modified | X | ... |

## Key Decisions
- [Decision 1 and why]
- [Decision 2 and why]

## Test Results
[Paste test output]

## Status: PASS / FAIL
```
```

---

## Filled Example

```markdown
# Task: Implement Rate Limiter Middleware

## Role
You are a senior Python backend developer with expertise in FastAPI
and API security. You prioritize clean code, comprehensive error handling,
and performance.

## Objective
Implement a rate limiting middleware for the FastAPI application that
limits API requests per user based on their authentication tier.

## Context

### Project Background
- Project: Pharmaceutical test generation API
- Tech stack: Python 3.12, FastAPI, Redis, Clerk authentication
- Current state: Authentication working, no rate limiting exists

### Files to Read (Before Starting)
1. `main/api/middleware/auth.py` - Understand auth middleware pattern
2. `main/api/deps.py` - See how dependencies are injected
3. `main/config/settings.py` - Find rate limit configuration

## Requirements

### Functional Requirements
1. Limit requests based on user tier (free: 10/min, pro: 100/min, enterprise: unlimited)
2. Return 429 Too Many Requests when limit exceeded
3. Include rate limit headers in all responses (X-RateLimit-*)
4. Use Redis for distributed rate limiting

### Technical Requirements
- Use sliding window algorithm
- Async Redis client (aioredis or redis-py async)
- Follow existing middleware pattern from auth.py

### Quality Requirements
- [ ] Type hints on all public functions
- [ ] Docstrings (Google style)
- [ ] Error handling with diagnostic info
- [ ] Unit tests with mocked Redis

## Constraints

### DO NOT
- Block requests without proper error response
- Store rate limit data in memory (must use Redis)
- Modify the authentication middleware

### Boundaries
- Only modify files in: `main/api/middleware/`
- Do not change: `main/api/middleware/auth.py`

## Implementation Guide

### Suggested Approach
1. Create `main/api/middleware/rate_limit.py`
2. Implement `RateLimitMiddleware` class
3. Add configuration to `settings.py`
4. Register middleware in `main/api/app.py`
5. Write tests

### Pattern to Follow
Reference: `main/api/middleware/auth.py`

```python
class AuthMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        # Middleware logic here
        await self.app(scope, receive, send)
```

## Validation

### Commands to Run
```bash
pytest main/tests/test_rate_limit.py -v
mypy main/api/middleware/rate_limit.py
ruff check main/api/middleware/
```

### Expected Results
- Tests: All passing
- Type check: No errors
- Linting: No warnings

## Success Criteria
- [ ] Rate limiting works per user tier
- [ ] 429 response includes retry-after header
- [ ] Redis connection errors don't crash the app (log and allow request)
- [ ] All tests pass
- [ ] No type errors

## Output

### Deliverables
1. Implementation in `main/api/middleware/rate_limit.py`
2. Tests in `main/tests/test_rate_limit.py`
3. Configuration in `main/config/settings.py` (if needed)

### Report Format
# Implementation Report: Rate Limiter Middleware

## Summary
Implemented sliding window rate limiter using Redis...

## Files
| File | Action | Lines | Description |
|------|--------|-------|-------------|
| rate_limit.py | created | 120 | Main middleware |
| test_rate_limit.py | created | 85 | Unit tests |

## Key Decisions
- Used sliding window for smoother limiting
- Added graceful degradation on Redis failure

## Test Results
[output]

## Status: PASS
```

---

## Checklist Before Sending

- [ ] Role establishes relevant expertise
- [ ] Objective is clear and specific
- [ ] Required reading files are listed with purposes
- [ ] Functional requirements describe WHAT, not HOW
- [ ] Technical requirements specify versions and patterns
- [ ] DO NOT list is explicit
- [ ] Implementation guide provides structure without dictating
- [ ] Validation commands are runnable
- [ ] Success criteria are all measurable
- [ ] Output format is fully specified
