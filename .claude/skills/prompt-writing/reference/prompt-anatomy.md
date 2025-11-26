# Prompt Anatomy: Complete Component Reference

This document provides detailed guidance on each component of an effective prompt, with real-world examples and language-specific patterns.

---

## Table of Contents

1. [Role/Identity Declaration](#roleidentity-declaration)
2. [Task Description](#task-description)
3. [Context Provision](#context-provision)
4. [Constraints and Limitations](#constraints-and-limitations)
5. [Output Format Specification](#output-format-specification)
6. [Success Criteria](#success-criteria)
7. [Examples and Demonstrations](#examples-and-demonstrations)
8. [Language-Specific Patterns](#language-specific-patterns)

---

## Role/Identity Declaration

### Purpose
Establishes the agent's expertise, perspective, and behavioral constraints.

### When to Use
- Complex domain-specific tasks
- Tasks requiring specific expertise
- When quality standards matter
- For review/evaluation tasks

### Structure
```markdown
You are a [role] with expertise in [domains].
Your focus is [primary responsibility].
You prioritize [key values/standards].
```

### Examples

**Software Engineering:**
```markdown
You are a senior software engineer specializing in distributed systems
and API design. You prioritize code clarity, maintainability, and
comprehensive error handling over premature optimization.
```

**Code Review:**
```markdown
You are an expert code reviewer focused on security and best practices.
You evaluate code objectively, providing constructive feedback with
specific examples and actionable improvements.
```

**Pharmaceutical Compliance:**
```markdown
You are a pharmaceutical software validation specialist with expertise
in GAMP-5 categorization, ALCOA+ data integrity, and 21 CFR Part 11
compliance. Patient safety and data integrity are your highest priorities.
```

### Anti-Pattern
```markdown
# Too vague - doesn't establish useful context
You are a helpful assistant.
```

---

## Task Description

### Purpose
Clear, specific statement of what the agent must accomplish.

### Structure
```markdown
[Action verb] [specific object] [purpose/goal]
```

### Effective Patterns

**Specific and Bounded:**
```markdown
Implement the `S3VectorStore` class that implements the `VectorStoreProvider`
interface, enabling vector similarity search using AWS S3 Vectors service.
```

**With Scope:**
```markdown
Review the authentication module (main/api/auth.py) for security vulnerabilities,
focusing on JWT validation, session management, and rate limiting.
```

**With Context:**
```markdown
Refactor the `process_document` function to use async/await patterns,
maintaining backward compatibility with existing callers while improving
throughput for batch operations.
```

### Anti-Patterns

**Too Vague:**
```markdown
# Bad - What specifically? What constitutes "better"?
Make the code better.
```

**Too Broad:**
```markdown
# Bad - Unbounded scope leads to inconsistent results
Improve the entire application.
```

**Ambiguous:**
```markdown
# Bad - "Handle" could mean many things
Handle the errors in the system.
```

---

## Context Provision

### Purpose
Provides all background information the agent needs to complete the task successfully.

### Categories of Context

#### 1. Project Context
```markdown
## Project Context
- **Project**: Pharmaceutical test generation system
- **Phase**: AWS Migration (Phase 2 of 5)
- **Tech Stack**: Python 3.12, FastAPI, LlamaIndex, ChromaDB
- **Compliance**: GAMP-5 Category 5, ALCOA+ required
```

#### 2. Current State
```markdown
## Current State
- Storage adapter implemented (Task 1.1 - COMPLETE)
- Vector store interface defined but not implemented
- Local ChromaDB working, need S3 Vectors for production
- Tests exist for interface, implementation tests needed
```

#### 3. Historical Context
```markdown
## Background
The team previously attempted using Pinecone but found:
- EU data residency requirements not met
- Cost prohibitive at scale
- Decided on S3 Vectors for AWS-native integration
```

#### 4. Environmental Context
```markdown
## Environment
- OS: Windows 11 with WSL2
- Python: 3.12.0
- Docker: Desktop 4.25 (ARM64 native)
- AWS Region: eu-west-2 (London)
```

### File Reference Patterns

**Explicit Reading List:**
```markdown
## Required Reading
Before starting, read these files in order:
1. `main/src/adapters/base.py` - Interface definitions
2. `main/src/adapters/storage.py` - Reference implementation pattern
3. `PRPs/tasks/1.2-vector-store-provider.md` - Full requirements

DO NOT proceed until you understand the interface contract.
```

**With Purpose:**
```markdown
## Files to Reference
| File | Purpose |
|------|---------|
| `base.py` | Understand the interface to implement |
| `storage.py` | Copy the adapter pattern |
| `test_storage.py` | See expected test structure |
```

---

## Constraints and Limitations

### Purpose
Defines boundaries, prohibitions, and rules the agent must follow.

### Types of Constraints

#### 1. Technical Constraints
```markdown
## Technical Constraints
- Python 3.12+ syntax required
- Use only standard library + approved packages (see requirements.txt)
- Must be compatible with AWS Lambda environment
- Maximum memory: 512MB
```

#### 2. Scope Constraints
```markdown
## Scope Boundaries
- ONLY modify files in `main/src/adapters/`
- DO NOT change the interface definitions in `base.py`
- DO NOT modify existing tests
- DO NOT add new dependencies without approval
```

#### 3. Compliance Constraints
```markdown
## Compliance Requirements
- All functions must have type hints
- All public methods require docstrings (Google style)
- Error handling must preserve stack traces
- Audit logging required for data operations
- NO FALLBACK LOGIC - fail explicitly with diagnostics
```

#### 4. Model/Tool Constraints
```markdown
## Model Requirements
- Use DeepSeek V3 (deepseek/deepseek-chat) for any LLM calls
- FORBIDDEN: GPT-4, O3, O1, Claude for generation tasks
- Embedding model: text-embedding-3-small only
```

### Explicit Prohibitions Pattern
```markdown
## DO NOT
- Implement fallback values that mask failures
- Return success status when operations fail
- Swallow exceptions without logging
- Use placeholder implementations
- Assume data availability without checking
```

---

## Output Format Specification

### Purpose
Defines exactly what the agent should return and in what structure.

### Components

#### 1. Format Type
```markdown
## Output Format
Return a **Markdown report** with the following structure:
```

#### 2. Structure Template
```markdown
## Output Structure

# [Task Name] - Result

## Summary
[2-3 sentence overview of what was done]

## Changes Made
| File | Change Type | Description |
|------|-------------|-------------|
| ... | ... | ... |

## Test Results
```
[paste test output]
```

## Issues
[Any problems encountered and how resolved]

## Status
**VERDICT**: PASS | FAIL
**Confidence**: HIGH | MEDIUM | LOW
```

#### 3. Length Constraints
```markdown
## Output Constraints
- Summary: Maximum 100 words
- Changes table: One row per file modified
- Total response: Under 500 words
- DO NOT include full file contents
```

#### 4. Delivery Location
```markdown
## Delivery
Save the result to: `.claude/state/results/task-executor-{YYYYMMDD-HHMMSS}.md`
Return a brief confirmation message to the user.
```

---

## Success Criteria

### Purpose
Defines measurable conditions for task completion.

### Patterns

#### Checklist Pattern
```markdown
## Success Criteria
The task is complete when ALL of the following are true:
- [ ] `S3VectorStore` class implements all `VectorStoreProvider` methods
- [ ] Unit tests pass: `pytest main/tests/test_vector_store.py -v`
- [ ] Type checking passes: `mypy main/src/adapters/`
- [ ] Linting passes: `ruff check main/src/adapters/`
- [ ] Documentation complete for all public methods
```

#### Measurable Criteria
```markdown
## Success Metrics
- Test coverage: ≥90% on new code
- Performance: Query latency <100ms for 1000 vectors
- Compatibility: All existing integration tests still pass
```

#### Quality Gates
```markdown
## Quality Gates
1. **Gate 1 - Implementation**: Code compiles without errors
2. **Gate 2 - Testing**: All unit tests pass
3. **Gate 3 - Integration**: System tests with mock S3 pass
4. **Gate 4 - Review**: Code follows project patterns
```

---

## Examples and Demonstrations

### Purpose
Shows expected behavior through concrete input/output pairs.

### When to Use Examples
- Complex transformations
- Specific formatting requirements
- Edge cases that need handling
- Quality standards demonstration

### Example Structure

#### Simple Example
```markdown
## Example

**Input:**
```python
def process(data):
    return data.upper()
```

**Expected Analysis:**
- Missing type hints
- No error handling
- No docstring

**Expected Output:**
```python
def process(data: str) -> str:
    """Convert input string to uppercase.

    Args:
        data: Input string to process

    Returns:
        Uppercase version of input

    Raises:
        TypeError: If data is not a string
    """
    if not isinstance(data, str):
        raise TypeError(f"Expected str, got {type(data).__name__}")
    return data.upper()
```
```

#### Multiple Examples
```markdown
## Examples

### Example 1: Simple Query
**Input**: "Find authentication code"
**Expected**: Returns files containing auth logic with relevance scores

### Example 2: Specific Function
**Input**: "Find the calculate_discount function"
**Expected**: Returns exact file:line location

### Example 3: Pattern Search
**Input**: "Find all API endpoints"
**Expected**: Returns list of route definitions with HTTP methods
```

---

## Language-Specific Patterns

### Python Prompts

```markdown
## Python-Specific Requirements
- Use Python 3.12+ features (match/case, union types with |)
- Type hints required on all function signatures
- Use `pathlib.Path` instead of `os.path`
- Prefer `dataclasses` or `pydantic` for data structures
- Use f-strings for formatting (never % or .format())
- Context managers for resource management
- Async/await for I/O operations
```

### JavaScript/TypeScript Prompts

```markdown
## TypeScript-Specific Requirements
- Strict TypeScript (no `any` types without justification)
- Use ES2025 features (optional chaining, nullish coalescing)
- Zod schemas for runtime validation
- Async/await over Promise chains
- Destructuring for object/array access
- Template literals over concatenation
```

### Infrastructure/DevOps Prompts

```markdown
## Infrastructure Requirements
- Terraform 1.6+ syntax
- AWS provider version constraints specified
- Resources tagged with: Environment, Project, Owner
- Sensitive values via AWS Secrets Manager
- State stored in S3 with DynamoDB locking
```

---

## Complete Prompt Example

```markdown
# Task: Implement S3 Vector Store Adapter

## Role
You are a senior Python developer specializing in AWS services and
vector databases. You prioritize clean interfaces, comprehensive
error handling, and production-ready code.

## Task
Implement the `S3VectorStore` class that implements the `VectorStoreProvider`
interface, enabling the pharmaceutical test generation system to use
AWS S3 Vectors for production deployments.

## Context
- Project: Pharmaceutical test generation (GAMP-5 Category 5)
- Current state: ChromaDB working locally, need S3 for production
- Previous task: Storage adapter pattern established in Task 1.1
- Environment: Python 3.12, AWS SDK (boto3), eu-west-2 region

## Required Reading
1. `main/src/adapters/base.py` - VectorStoreProvider interface
2. `main/src/adapters/storage.py` - Reference adapter pattern
3. `main/src/adapters/chromadb_store.py` - Existing implementation

## Constraints
- Implement ALL VectorStoreProvider interface methods
- Use boto3 for AWS operations
- NO FALLBACK LOGIC - fail explicitly on errors
- Preserve error context with `from e` pattern
- DO NOT modify interface definitions

## Expected Output
Save to: `.claude/state/results/task-executor-{timestamp}.md`

Structure:
1. Summary (what was implemented)
2. Files created/modified
3. Test results
4. Integration notes

## Success Criteria
- [ ] All interface methods implemented
- [ ] Unit tests passing
- [ ] Type hints on all methods
- [ ] Docstrings complete
- [ ] Error handling preserves stack traces

## Example
**Interface Method:**
```python
async def query(self, embedding: List[float], top_k: int) -> List[Document]:
```

**Expected Implementation Pattern:**
```python
async def query(self, embedding: List[float], top_k: int) -> List[Document]:
    """Query S3 Vectors for similar documents.

    Args:
        embedding: Query vector (1536 dimensions)
        top_k: Number of results to return

    Returns:
        List of Document objects with similarity scores

    Raises:
        VectorStoreError: If S3 Vectors query fails
    """
    try:
        response = await self._client.query(
            vector=embedding,
            top_k=top_k
        )
        return [self._to_document(r) for r in response.results]
    except ClientError as e:
        raise VectorStoreError(f"S3 Vectors query failed: {e}") from e
```
```
