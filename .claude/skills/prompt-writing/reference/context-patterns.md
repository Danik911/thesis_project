# Context Patterns: Strategies for Effective Information Transfer

This document covers strategies for providing context to AI agents, with special emphasis on subagent delegation where context isolation is critical.

---

## Table of Contents

1. [Understanding Context Isolation](#understanding-context-isolation)
2. [File-Based State Transfer](#file-based-state-transfer)
3. [Context Embedding Strategies](#context-embedding-strategies)
4. [Multi-Step Workflow Context](#multi-step-workflow-context)
5. [Subagent Orchestration Patterns](#subagent-orchestration-patterns)

---

## Understanding Context Isolation

### The Problem

When delegating to subagents (via Task tool or similar mechanisms):

- **Subagents have NO conversation history** - they don't see prior messages
- **Subagents have NO memory** - each invocation is completely fresh
- **Subagents cannot access other subagent results** - unless explicitly provided
- **Subagents cannot infer context** - they only know what you tell them

### The Impact

```markdown
# WRONG - Assumes subagent knows context
"Now fix the issues you found in the authentication module."

# Result: Subagent has no idea what issues were found or where
```

```markdown
# RIGHT - Provides complete context
"Fix the following issues in main/api/auth.py:
1. Line 45: Missing rate limit check on login endpoint
2. Line 78: JWT expiry not validated
3. Line 112: Session token stored in plain text

See attached review: .claude/state/results/code-review-20251125.md"
```

### The Rule

**Every subagent invocation must be self-contained.** Treat it as if you're explaining the task to a new team member who just joined.

---

## File-Based State Transfer

### Pattern: Save → Reference → Continue

The most reliable way to transfer state between agents.

#### Step 1: First Agent Saves Results

```markdown
# Prompt for Agent 1 (Research)
...
## Output
Save your findings to: `.claude/state/results/research-{YYYYMMDD-HHMMSS}.md`

Include:
- Technology options evaluated
- Recommended approach with rationale
- Key constraints identified
- Open questions
```

#### Step 2: Second Agent References File

```markdown
# Prompt for Agent 2 (Implementation)
## Context
Read the research findings from the previous phase:
- File: `.claude/state/results/research-20251125-143022.md`

This file contains:
- The chosen technology approach
- Constraints to follow
- Design decisions already made

Implement based on the recommended approach in that file.
```

### File Naming Conventions

```markdown
## State Files
.claude/state/
├── prp-workflow-state.md           # Master workflow status
├── current-task-context.md          # Active task details
└── results/
    ├── context-collector-{timestamp}.md    # Research results
    ├── task-executor-{timestamp}.md        # Implementation results
    ├── tester-agent-{timestamp}.md         # Test results
    └── code-review-{timestamp}.md          # Review results
```

### File Content Structure

```markdown
# [Agent Name] Results - [Task ID]

## Meta
- Timestamp: 2025-11-25T14:30:22Z
- Duration: 12 minutes
- Status: COMPLETE | PARTIAL | FAILED

## Summary
[Brief overview of what was accomplished]

## Findings/Results
[Main content - structured for the next consumer]

## Key Decisions
[Important choices made that affect downstream work]

## Open Items
[Questions or issues for the next phase]

## Files Modified
[List of files created or changed]
```

---

## Context Embedding Strategies

### Strategy 1: Full Embedding

Include all necessary context directly in the prompt. Best for small contexts.

```markdown
## Background
The pharmaceutical test generation system needs to migrate from local
ChromaDB to AWS S3 Vectors for production deployment.

Key requirements:
- Must support 1536-dimension embeddings
- Query latency must be <100ms
- Must work with existing VectorStoreProvider interface
- EU data residency (eu-west-2 region)

Previous decisions:
- Pinecone rejected due to data residency
- OpenSearch rejected due to complexity
- S3 Vectors chosen for AWS-native integration
```

### Strategy 2: Summarized Embedding

Condense larger contexts into key points.

```markdown
## Context Summary
From research phase (full details: research-20251125.md):
- **Chosen approach**: S3 Vectors with boto3 client
- **Key constraint**: Must implement async interface
- **Risk identified**: Cold start latency (~500ms first query)
- **Mitigation**: Implement connection pooling
```

### Strategy 3: Layered Context

Provide summary with optional deep-dive references.

```markdown
## Quick Context
Implementing vector store adapter for S3 Vectors, following the pattern
established in storage.py.

## Detailed Context (Read if needed)
- Full requirements: PRPs/tasks/1.2-vector-store-provider.md
- Interface definition: main/src/adapters/base.py
- Reference implementation: main/src/adapters/storage.py
- Research findings: .claude/state/results/research-20251125.md
```

---

## Multi-Step Workflow Context

### Master Status Document

Maintain a single document tracking overall workflow progress.

```markdown
# Workflow Status: Task 1.2 - Vector Store Provider

## Current State
- **Phase**: 3 of 4 (Testing)
- **Started**: 2025-11-25T10:00:00Z
- **Last Updated**: 2025-11-25T14:30:00Z

## Phase History

### Phase 1: Research (COMPLETE)
- Agent: context-collector
- Result: `.claude/state/results/context-collector-20251125-100000.md`
- Outcome: S3 Vectors selected, interface defined

### Phase 2: Implementation (COMPLETE)
- Agent: task-executor
- Result: `.claude/state/results/task-executor-20251125-120000.md`
- Files created:
  - main/src/adapters/s3_vector_store.py
  - main/tests/test_s3_vector_store.py

### Phase 3: Testing (IN PROGRESS)
- Agent: tester-agent
- Status: Running integration tests
- Expected result: `.claude/state/results/tester-agent-20251125-143000.md`

### Phase 4: Review (PENDING)
- Agent: code-reviewer
- Blocked by: Phase 3 completion
```

### Context Chain Pattern

Each agent receives context from all previous phases.

```markdown
## Prompt for Phase 3 (Testing)

## Workflow Context
You are executing Phase 3 of Task 1.2.

### Previous Phase Results (Required Reading)
1. **Research** (Phase 1):
   File: `.claude/state/results/context-collector-20251125-100000.md`
   Key points: S3 Vectors selected, async interface required

2. **Implementation** (Phase 2):
   File: `.claude/state/results/task-executor-20251125-120000.md`
   Key points: S3VectorStore class implemented in s3_vector_store.py

### Your Task
Validate the implementation from Phase 2 by running all tests.

### Expected Output
Save to: `.claude/state/results/tester-agent-20251125-143000.md`
```

---

## Subagent Orchestration Patterns

### Pattern 1: Sequential Chain

Each agent depends on the previous one.

```
Agent 1 (Research) → File A
        ↓
Agent 2 (Design) reads File A → File B
        ↓
Agent 3 (Implement) reads File B → File C
        ↓
Agent 4 (Test) reads File C → File D
```

**Orchestration:**
```markdown
# Step 1
Launch context-collector → Wait for completion → Read result file

# Step 2
Launch task-executor with:
- Reference to context-collector result file
- Wait for completion → Read result file

# Step 3
Launch tester-agent with:
- Reference to task-executor result file
- Wait for completion → Read result file
```

### Pattern 2: Parallel Execution

Independent tasks run simultaneously.

```
        ┌→ Agent A (Security Review) → File A
        │
Main →  ├→ Agent B (Performance Review) → File B
        │
        └→ Agent C (Code Quality Review) → File C
                    ↓
            Aggregate Results
```

**Orchestration:**
```markdown
# Launch in parallel (single message with multiple Task calls)
- Task(security-reviewer, context about code to review)
- Task(performance-reviewer, same context)
- Task(quality-reviewer, same context)

# Wait for all to complete

# Aggregate
Read File A, File B, File C
Synthesize findings into unified report
```

### Pattern 3: Hub and Spoke

One implementation, multiple reviewers.

```
                    ┌→ Reviewer A → Feedback A
                    │
Implementation →    ├→ Reviewer B → Feedback B
                    │
                    └→ Reviewer C → Feedback C
                            ↓
                    Aggregate → Decision
```

### Pattern 4: Iterative Refinement

Multiple rounds of improve-and-review.

```
Round 1: Implement → Review → Feedback
            ↓
Round 2: Implement (with Feedback) → Review → Feedback
            ↓
Round N: Final Implementation
```

**Context Accumulation:**
```markdown
## Round 2 Context

### Original Requirements
[From initial task]

### Round 1 Implementation
File: implementation-v1.md

### Round 1 Feedback
File: review-v1.md
Key issues:
1. Missing error handling on line 45
2. Performance concern with nested loops

### Your Task
Address the Round 1 feedback and produce implementation-v2.
```

---

## Context Size Management

### Problem: Context Overflow

Too much context can overwhelm the agent or exceed limits.

### Solutions

#### 1. Progressive Disclosure
```markdown
## Essential Context (Always include)
[Minimum needed to understand the task]

## Extended Context (Read if needed)
For detailed requirements, see: [file path]
For implementation history, see: [file path]
```

#### 2. Summarization
```markdown
## Research Summary (Full: research.md)
- 5 options evaluated
- S3 Vectors selected due to: cost, latency, compliance
- Key risk: cold starts
- Mitigation: connection pooling
```

#### 3. Relevance Filtering
Only include context relevant to the specific task.

```markdown
## Relevant Context for Vector Store Implementation
[Only vector store related decisions]

## NOT Included (Not relevant)
- Frontend decisions
- Authentication implementation details
- Database schema choices
```

#### 4. Output Constraints for Subagents
Prevent subagents from returning too much context.

```markdown
## Output Format
Return ONLY:
1. Summary (max 100 words)
2. Key findings (max 5 bullets)
3. Recommendation (1 sentence)

DO NOT include:
- Full code listings
- Detailed analysis of rejected options
- Verbose explanations
```

---

## Common Mistakes

### Mistake 1: Implicit References
```markdown
# WRONG
"Continue from where we left off."

# RIGHT
"Continue implementation of S3VectorStore.
Previous work saved to: task-executor-20251125.md
Remaining methods: query(), delete(), update()"
```

### Mistake 2: Assuming Shared Memory
```markdown
# WRONG
"Use the same approach as the storage adapter."

# RIGHT
"Follow the adapter pattern from main/src/adapters/storage.py:
- Inherit from BaseAdapter
- Implement all interface methods
- Use the error handling pattern from lines 45-60"
```

### Mistake 3: Incomplete File References
```markdown
# WRONG
"Check the test file for examples."

# RIGHT
"See test examples in:
- main/tests/test_storage.py (lines 20-45): Unit test pattern
- main/tests/test_storage.py (lines 100-130): Integration test pattern"
```

### Mistake 4: Outdated Context
```markdown
# WRONG
"The interface is defined in base.py" (but it was modified)

# RIGHT
"The interface is defined in base.py (as of commit abc123).
Note: query() method signature updated in latest version."
```
