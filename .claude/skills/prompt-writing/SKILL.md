---
name: prompt-writing
description: Creates effective prompts for AI coding agents and subagent delegation. Use PROACTIVELY when writing prompts for Task tool delegation, creating agent instructions, or designing multi-step workflows. MUST BE USED when delegating complex tasks to subagents or writing system prompts.
allowed-tools: ["Read", "Write", "Edit", "Grep", "Glob"]
---

# Prompt Writing Skill

## Overview

This skill provides a systematic approach to writing effective prompts for AI coding agents. Whether delegating to subagents, creating system prompts, or designing multi-step workflows, these patterns ensure reliable, consistent results.

**Core Principle:** Context completeness over brevity. Agents cannot infer what you don't provide.

**Target Users:**
- Claude Code delegating to subagents via Task tool
- UI agents that need to generate prompts
- Engineers writing system prompts or agent instructions

---

## The CLEAR Framework

Use this mnemonic for every prompt you write:

### **C** - Context
Complete background information the agent needs.

- **What**: Current state, project details, relevant history
- **Why**: Goals, motivations, constraints that shaped decisions
- **Where**: File paths, repositories, environment details

```markdown
## Context
- Project: Pharmaceutical test generation system (GAMP-5 compliant)
- Current state: Task 1.2 implementation complete, tests passing
- Environment: Python 3.12, FastAPI, ChromaDB
- Previous work: Storage adapter implemented in main/src/adapters/storage.py
```

### **L** - Limitations
Constraints, boundaries, and prohibitions.

- **Technical**: Language versions, frameworks, dependencies
- **Scope**: What NOT to change, files to avoid
- **Rules**: Coding standards, compliance requirements

```markdown
## Limitations
- DO NOT modify main/src/core/unified_workflow.py
- Use DeepSeek V3 model ONLY (no GPT-4, Claude for generation)
- Must maintain backward compatibility with existing API
- Follow GAMP-5 compliance patterns
```

### **E** - Expectations
Exact output format and success criteria.

- **Format**: Markdown structure, JSON schema, code style
- **Quality**: Pass/fail criteria, acceptance tests
- **Delivery**: Where to save results, what to return

```markdown
## Expected Output
Return a markdown report with:
1. Summary (2-3 sentences)
2. Files modified (list with brief descriptions)
3. Test results (PASS/FAIL with details)
4. Next steps (if any)

Save to: .claude/state/results/task-executor-{timestamp}.md
```

### **A** - Actions
Step-by-step instructions to complete the task.

- **Sequence**: Numbered steps in execution order
- **Checkpoints**: Validation points between steps
- **Decisions**: How to handle branches/alternatives

```markdown
## Actions
1. Read the current implementation at main/src/adapters/vector_store.py
2. Identify the interface methods that need implementation
3. Implement the S3 Vectors adapter following the existing pattern
4. Run tests: `pytest main/tests/test_vector_store.py -v`
5. If tests fail, fix issues before proceeding
6. Document changes in the result file
```

### **R** - Resources
Files, tools, references, and materials available.

- **Files**: Paths to read, templates to use
- **Tools**: Available commands, APIs, utilities
- **References**: Documentation, examples, patterns

```markdown
## Resources
### Files to Read
- main/src/adapters/storage.py (reference pattern)
- main/src/adapters/base.py (interface definition)
- PRPs/tasks/1.2-vector-store-provider.md (task specification)

### Available Tools
- pytest for testing
- mypy for type checking
- ruff for linting

### References
- See examples/alex/backend/adapters/ for production patterns
```

---

## Prompt Anatomy

Every effective prompt contains these components in order:

### 1. Role/Identity (Optional but Recommended)
Define who the agent is and their expertise.

```markdown
You are a senior Python developer specializing in pharmaceutical software
with expertise in GAMP-5 compliance and data integrity (ALCOA+).
```

### 2. Task Description
Clear, specific statement of what to accomplish.

```markdown
Implement the S3 Vectors adapter for the vector store provider abstraction,
enabling the system to use AWS S3 Vectors instead of ChromaDB.
```

### 3. Context Provision (CLEAR: C)
Background information needed to understand the task.

### 4. Constraints/Limitations (CLEAR: L)
Boundaries and rules to follow.

### 5. Output Format (CLEAR: E)
Exact specification of expected deliverables.

### 6. Success Criteria
How to know when the task is complete.

```markdown
## Success Criteria
- [ ] All vector store interface methods implemented
- [ ] Unit tests passing (100% coverage on new code)
- [ ] Integration test with mock S3 successful
- [ ] Type hints on all public methods
- [ ] Docstrings following Google style
```

### 7. Examples (Optional but Powerful)
Input/output pairs demonstrating expected behavior.

```markdown
## Example
**Input**: Query "authentication failure handling"
**Expected Output**:
- 3-5 relevant code chunks from the codebase
- Similarity scores > 0.7
- Source file paths included
```

---

## Context Provision Strategies

### For Subagent Delegation (Critical)

**Key Insight:** Subagents have NO access to conversation history. Each invocation starts fresh.

#### Strategy 1: File-Based State Transfer
Save intermediate results to files, pass file paths to next agent.

```markdown
## Context
Read the research findings from the previous phase:
- File: .claude/state/results/context-collector-20251125-120000.md

This contains:
- Technology options evaluated
- Recommended approach
- Key constraints identified
```

#### Strategy 2: Embedded Context
Include all necessary information directly in the prompt.

```markdown
## Background
The user requested implementing a vector store abstraction. Previous research found:
- ChromaDB works locally but doesn't scale
- S3 Vectors is the AWS production solution
- Interface should support both seamlessly

The storage adapter pattern from Task 1.1 should be followed.
```

#### Strategy 3: Explicit File References
List exactly which files to read and why.

```markdown
## Required Reading (Before Starting)
1. main/src/adapters/base.py - Interface definition (understand contract)
2. main/src/adapters/storage.py - Reference implementation (copy pattern)
3. PRPs/tasks/1.2-vector-store-provider.md - Full requirements

DO NOT proceed until you have read all three files.
```

### For Multi-Step Workflows

Use a master status document that accumulates across steps:

```markdown
## Workflow Status
Current Phase: 3 of 5 (Implementation)
Previous Phases:
- Phase 1 (Research): Complete - see research-notes.md
- Phase 2 (Design): Complete - see design-spec.md

Your task: Execute Phase 3 based on the approved design.
```

---

## Output Format Patterns

### Pattern 1: Structured Markdown Report
For comprehensive task results.

```markdown
## Output Format

# Task Result: [Task Name]

## Meta
- Task ID: [ID]
- Timestamp: [ISO 8601]
- Duration: [time]
- Status: PASS | FAIL

## Summary
[2-3 sentence overview]

## Changes Made
| File | Action | Description |
|------|--------|-------------|
| path/file.py | Modified | Added X method |

## Test Results
- Unit tests: X/Y passing
- Integration: PASS/FAIL

## Issues Encountered
[If any, with resolutions]

## Next Steps
[If applicable]
```

### Pattern 2: Binary Verdict First
For review/validation tasks.

```markdown
## Output Format

**VERDICT: PASS | FAIL**

**Reason**: [One-line explanation]

**Score**: [1-5]/5 (if PASS)

**Details**:
[Structured analysis]
```

### Pattern 3: Checklist Completion
For multi-requirement tasks.

```markdown
## Output Format

## Requirements Checklist
- [x] Requirement 1 - Implemented in file.py:45
- [x] Requirement 2 - Verified with test_x.py
- [ ] Requirement 3 - BLOCKED: Needs dependency X
- [x] Requirement 4 - Complete

## Completion: 3/4 (75%)
## Status: PARTIAL - See blocked items
```

### Pattern 4: Condensed Summary
For subagent responses (prevent context overload).

```markdown
## Output Format
Return ONLY:
1. Top 3 findings (2-3 sentences each)
2. One code example (if applicable)
3. Recommended next step (1 sentence)

DO NOT include:
- Full file contents
- Verbose explanations
- Alternative approaches not chosen
```

---

## Quality Checklist

**Before using any prompt, verify:**

### Context (C)
- [ ] All background information included?
- [ ] No assumptions about prior knowledge?
- [ ] File paths are absolute or clearly relative?
- [ ] Environment/dependencies specified?

### Limitations (L)
- [ ] Constraints clearly stated?
- [ ] Prohibited actions explicit?
- [ ] Scope boundaries defined?
- [ ] Compliance requirements noted?

### Expectations (E)
- [ ] Output format specified exactly?
- [ ] Success criteria measurable?
- [ ] Delivery location defined?
- [ ] Quality standards clear?

### Actions (A)
- [ ] Steps numbered and sequential?
- [ ] Decision points addressed?
- [ ] Validation checkpoints included?
- [ ] Error handling guidance provided?

### Resources (R)
- [ ] Required files listed?
- [ ] Available tools mentioned?
- [ ] Reference materials linked?
- [ ] Examples provided where helpful?

### Subagent-Specific
- [ ] No implicit context assumptions?
- [ ] State transfer mechanism defined?
- [ ] Output format prevents overload?
- [ ] Complete in single invocation?

---

## Anti-Patterns (Quick Reference)

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| **Context Amnesia** | Assuming subagent remembers | Embed all context explicitly |
| **Vague Expectations** | "Give me a good result" | Specify exact format |
| **Implicit Constraints** | "Follow best practices" | List specific requirements |
| **Unbounded Scope** | "Improve the code" | Define precise boundaries |
| **Missing Resources** | "Check the docs" | Provide file paths |
| **Output Overload** | No format limits | Request condensed response |

For detailed anti-patterns with examples, see `reference/anti-patterns.md`

---

## Troubleshooting

### Problem: Subagent returns irrelevant results
**Cause**: Insufficient context or vague task description
**Solution**:
1. Review the Context (C) section - is it complete?
2. Add explicit file references
3. Include an example of expected output

### Problem: Output format doesn't match expectations
**Cause**: Format specification too vague
**Solution**:
1. Provide a template with placeholders
2. Show a complete example output
3. Specify what NOT to include

### Problem: Agent makes unwanted changes
**Cause**: Missing limitations/constraints
**Solution**:
1. Add explicit "DO NOT" statements
2. List files that should not be modified
3. Define scope boundaries clearly

### Problem: Task incomplete or partial
**Cause**: Success criteria unclear or too broad
**Solution**:
1. Break into smaller, atomic tasks
2. Add specific acceptance criteria
3. Include verification steps

### Problem: Agent asks clarifying questions instead of executing
**Cause**: Ambiguous requirements or missing decisions
**Solution**:
1. Make all decisions upfront
2. Provide defaults for optional choices
3. Remove ambiguous language

---

## Templates

Ready-to-use templates for common scenarios:

- **Subagent Delegation**: `templates/subagent-delegation.md`
- **Coding Tasks**: `templates/code-task.md`
- **Research Tasks**: `templates/research-task.md`
- **Review/Validation**: `templates/review-task.md`

---

## Advanced Topics

For deeper coverage, see reference files:

- **Prompt Anatomy**: `reference/prompt-anatomy.md` - Detailed component breakdown
- **Context Patterns**: `reference/context-patterns.md` - State transfer strategies
- **Output Specs**: `reference/output-specifications.md` - Format templates
- **Anti-Patterns**: `reference/anti-patterns.md` - Detailed examples with solutions

---

## Quick Start

1. **Choose a template** from `templates/` matching your task type
2. **Fill in CLEAR** sections systematically
3. **Run the checklist** to verify completeness
4. **Execute** the prompt
5. **Iterate** if results don't match expectations

**Remember**: More context is almost always better. When in doubt, include it.
