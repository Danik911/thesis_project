# PRP Methodology Guide

## What is PRP?

**PRP = PRD + curated codebase intelligence + agent/runbook**

A Product Requirement Prompt (PRP) is a structured methodology for enabling AI agents to deliver production-ready code on the first pass through comprehensive context and validation.

## Core Principles

### 1. Context is King
- Include ALL necessary documentation, examples, and caveats
- Reference specific URLs, file paths, and code patterns
- Provide library documentation and gotchas
- Include existing conventions to follow

### 2. Validation Loops
- Provide executable tests/lints the AI can run and fix
- Multiple validation levels (syntax, unit tests, integration)
- Creative validation methods specific to the feature
- Never skip validation steps

### 3. Information Dense
- Use keywords and patterns from the codebase
- Dense, specific language over verbose explanations
- Reference real files and implementations
- Include pseudocode with critical details

### 4. Progressive Success
- Start simple, validate, then enhance
- Build incrementally with validation at each step
- Fix failures immediately before proceeding
- Iterate until all validation gates pass

## PRP Structure Template

```markdown
## Goal
[Specific end state and desired outcomes]

## Why
- Business value and user impact
- Integration with existing features
- Problems this solves and for whom

## What
[User-visible behavior and technical requirements]

### Success Criteria
- [ ] Specific measurable outcomes

## All Needed Context

### Documentation & References
- url: [Official API docs URL]
  why: [Specific sections/methods needed]
- file: [path/to/example.py]
  why: [Pattern to follow, gotchas to avoid]

### Current Codebase Structure
[Run `tree` command output]

### Known Gotchas & Library Quirks
[Critical library requirements and constraints]

## Implementation Blueprint

### Data Models
[Core data structures and validations]

### Task List
[Ordered tasks with specific file modifications]

### Pseudocode
[Critical implementation details]

## Validation Loop

### Level 1: Syntax & Style
```bash
ruff check --fix && mypy .
```

### Level 2: Unit Tests
```bash
uv run pytest tests/ -v
```

### Level 3: Integration
[Manual testing commands]

### Level 4: Creative Validation
[Custom validation methods]
```

## Execution Process

### 1. Load PRP
- Read and understand all context and requirements
- Follow all instructions and extend research if needed
- Ensure comprehensive context for implementation

### 2. ULTRATHINK
- Create comprehensive plan addressing all requirements
- Break down into clear todos using TodoWrite tool
- Use agents/subagents and batch tools
- Never guess - base everything on real context

### 3. Execute the Plan
- Implement step by step following the blueprint
- Follow existing patterns and conventions
- Reference PRP context throughout implementation

### 4. Validate
- Run each validation command in sequence
- Fix any failures immediately
- Re-run until all validation gates pass
- Re-read PRP to ensure requirements are met

### 5. Complete
- Ensure all checklist items are done
- Run final validation suite
- Report completion status

## Anti-Patterns to Avoid

- ❌ Don't create minimal context prompts
- ❌ Don't skip validation steps
- ❌ Don't ignore the structured PRP format
- ❌ Don't create new patterns when existing ones work
- ❌ Don't hardcode values that should be config
- ❌ Don't use broad exception handling

## Quality Scoring

Score PRPs on confidence level (1-10) for one-pass implementation success:

- **8-10**: Comprehensive context, executable validation, clear implementation path
- **5-7**: Good context but missing some validation or implementation details
- **1-4**: Insufficient context or validation for reliable implementation

## Tools and Commands

- `/create-base-prp [feature]` - Generate comprehensive PRP with research
- `/execute-base-prp [prp-file]` - Execute PRP against codebase
- Use TodoWrite tool for task tracking during execution
- Leverage batch tools for parallel research and implementation