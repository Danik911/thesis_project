# Template: Subagent Delegation

Use this template when delegating tasks to subagents via the Task tool.

---

## Template

```markdown
Use the [AGENT_NAME] agent to [BRIEF_TASK_DESCRIPTION].

## Context

### Background
[What the agent needs to know about the project/situation]
- Project: [Project name and type]
- Current phase: [Where we are in the workflow]
- Previous work: [What has been done before this]

### State Files (Required Reading)
[List files the agent MUST read before starting]
- `.claude/state/results/[previous-agent]-[timestamp].md` - [What it contains]
- `[other/relevant/file.md]` - [What it contains]

### Environment
- Language/Framework: [Tech stack]
- Key constraints: [Technical limitations]

## Task

### Primary Objective
[Clear, specific statement of what to accomplish]

### Specific Requirements
1. [Requirement 1 - be specific]
2. [Requirement 2 - be specific]
3. [Requirement 3 - be specific]

### Constraints
- DO NOT [specific prohibition]
- DO NOT [specific prohibition]
- ONLY [specific boundary]

## Success Criteria
[Measurable conditions for completion]
- [ ] [Criterion 1]
- [ ] [Criterion 2]
- [ ] [Criterion 3]

## Output

### Format
[Exact structure of expected output]

### Delivery
Save to: `.claude/state/results/[agent-name]-{YYYYMMDD-HHMMSS}.md`

### Size Constraints
- Summary: [max words]
- Total response: [max words or sections]
```

---

## Filled Example

```markdown
Use the task-executor agent to implement the S3 Vector Store adapter.

## Context

### Background
- Project: Pharmaceutical test generation system (GAMP-5 Category 5)
- Current phase: Phase 2 - Backend Abstraction (Task 1.2)
- Previous work: Storage adapter completed (Task 1.1), interface defined

### State Files (Required Reading)
- `.claude/state/results/context-collector-20251125-100000.md` - Research findings recommending S3 Vectors
- `PRPs/tasks/1.2-vector-store-provider.md` - Full task requirements

### Environment
- Language: Python 3.12
- Framework: FastAPI, LlamaIndex
- Key constraints: AWS eu-west-2 region, async interface required

## Task

### Primary Objective
Implement the `S3VectorStore` class that implements the `VectorStoreProvider` interface, enabling vector similarity search using AWS S3 Vectors.

### Specific Requirements
1. Implement all four interface methods: query(), insert(), delete(), update()
2. Use boto3 for AWS SDK operations
3. Follow the adapter pattern from `main/src/adapters/storage.py`
4. Include comprehensive error handling with diagnostic information

### Constraints
- DO NOT modify the interface definition in `base.py`
- DO NOT add new dependencies without documenting them
- ONLY modify files in `main/src/adapters/`
- NO FALLBACK LOGIC - fail explicitly on errors

## Success Criteria
- [ ] All `VectorStoreProvider` interface methods implemented
- [ ] Unit tests pass: `pytest main/tests/test_s3_vector_store.py -v`
- [ ] Type checking passes: `mypy main/src/adapters/s3_vector_store.py`
- [ ] All public methods have docstrings

## Output

### Format
# Task Executor Result: Task 1.2

## Summary
[2-3 sentences on what was implemented]

## Files Created/Modified
| File | Action | Description |
|------|--------|-------------|
| ... | ... | ... |

## Test Results
[Test output]

## Issues Encountered
[Any problems and resolutions]

## Status
PASS / FAIL with reason

### Delivery
Save to: `.claude/state/results/task-executor-{YYYYMMDD-HHMMSS}.md`

### Size Constraints
- Summary: max 100 words
- Total report: max 500 words (exclude code blocks)
```

---

## Checklist Before Sending

- [ ] Agent name is correct for the task type
- [ ] All required state files are listed
- [ ] Context is complete (no implicit assumptions)
- [ ] Requirements are numbered and specific
- [ ] Constraints list what NOT to do
- [ ] Success criteria are measurable
- [ ] Output format is explicitly defined
- [ ] Delivery location uses timestamp pattern
- [ ] Size constraints prevent context overflow
