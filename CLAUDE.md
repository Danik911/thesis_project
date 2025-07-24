# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🚨 CRITICAL OPERATING PRINCIPLE 🚨

**NEVER CLAIM SUCCESS WITHOUT USER CONFIRMATION**

- ❌ NEVER say "working", "successful", "complete", "fixed", "resolved" without explicit user verification
- ❌ NEVER assume logs showing "success" mean actual success from user perspective  
- ❌ NEVER claim "mission accomplished" or similar without user confirming the result
- ✅ ALWAYS ask "Did you hear/see/experience the expected result?" before claiming success
- ✅ ALWAYS wait for user confirmation before updating status to "complete"
- ✅ ALWAYS acknowledge when user reports "no" or "didn't work" immediately

**USER FEEDBACK IS THE ONLY SOURCE OF TRUTH FOR SUCCESS**

## Project Nature

This is a **thesis project** with integrated **PRP (Product Requirement Prompt) Framework**. The project follows the PRP methodology: **"PRP = PRD + curated codebase intelligence + agent/runbook"** - designed to enable AI agents to ship production-ready code on the first pass.

## Core Architecture

### PRP Framework Integration

- **Pre-configured Claude Code commands** in `.claude/commands/`
- Core commands available:
  - `/create-base-prp` - Generate comprehensive PRPs with research
  - `/execute-base-prp` - Execute PRPs against codebase
  - `/review-general` - Code review workflows
  - `/review-staged-unstaged` - Review git changes
  - `/prime-core` - Prime Claude with project context
  - `/onboarding` - Onboarding process for new team members

### Template-Based Methodology

- **PRP Templates** in `PRPs/templates/` follow structured format with validation loops
- **Context-Rich Approach**: Every PRP must include comprehensive documentation, examples, and gotchas
- **Validation-First Design**: Each PRP contains executable validation gates (syntax, tests, integration)

### AI Documentation Curation

- `PRPs/ai_docs/` contains curated documentation for AI context injection
- Framework supports multiple programming languages and tech stacks

### Model Configuration

- **Testing Model**: `gpt-4.1-mini-2025-04-14` (fast development, higher rate limits)
- **Production Model**: `o3-2025-04-16` (highest quality reasoning)
- **Embedding Model**: `text-embedding-3-small` (for all agents)
  - Designed for compatibility with open-source models
  - Can be swapped with open-source embeddings after workflow validation

## Development Workflow

### Creating Features with PRPs

1. **Use PRP Creation**: `/create-base-prp [feature description]`
2. **Research Phase**: Deep codebase analysis and external research
3. **Context Gathering**: Include all necessary documentation and examples
4. **Implementation**: `/execute-base-prp PRPs/[feature-name].md`
5. **Validation**: Run all validation gates until passing

### Validation Requirements

Every implementation must pass these validation gates:

```bash
# Level 1: Syntax & Style (adjust based on your tech stack)
# For Python projects:
ruff check --fix && mypy .

# For JavaScript/TypeScript:
npm run lint && npm run typecheck

# Level 2: Unit Tests
# For Python:
uv run pytest tests/ -v
# For Node.js:
npm run test

# Level 3: Integration Tests
# Start your application and test endpoints/functionality

# Level 4: Creative Validation
# Custom validation methods specific to your project
```

## Critical Success Patterns

### The PRP Methodology

1. **Context is King**: Include ALL necessary documentation, examples, and caveats
2. **Validation Loops**: Provide executable tests/lints the AI can run and fix
3. **Information Dense**: Use keywords and patterns from the codebase
4. **Progressive Success**: Start simple, validate, then enhance

### Code Quality Standards

- **Type Safety**: Use proper type hints/annotations
- **Error Handling**: Specific exception handling, no broad catches
- **Testing**: Unit tests co-located with features
- **Documentation**: Clear README and inline documentation
- **Security**: Input validation, no hardcoded secrets
- **Performance**: Efficient algorithms, proper async usage where applicable

## CRITICAL DEVELOPMENT PRINCIPLES

**DO NOT WRITE EXCESSIVE CODE. THE BEST CODE IS THE CODE THAT IS NOT WRITTEN.**

- **Always check official documentation before implementation**
- **Always check context7 before implementation**
- **This project contains new libraries you don't know - research first**
- **Minimize code complexity - prioritize simplicity over features**
- **Verify minimal viable solutions before adding complexity**

## Project Structure

```
thesis_project/
├── .claude/
│   ├── commands/          # Claude Code commands for PRP workflow
│   └── settings.local.json
├── .git/
├── .gitignore
├── .mcp.json
├── PRPs/
│   ├── templates/         # PRP templates (prp_base.md, prp_spec.md, prp_planning.md)
│   ├── scripts/          # PRP execution scripts
│   ├── ai_docs/          # AI documentation for context
│   └── completed/        # Archive of finished PRPs
├── src/                  # Source code
│   ├── agents/           # Multi-agent components
│   ├── core/             # Workflow orchestration
│   ├── rag/              # RAG/CAG implementation
│   ├── security/         # Security validators
│   ├── validation/       # Compliance checks
│   └── shared/           # Shared utilities
├── tests/                # Test suites
│   ├── unit/             # Unit tests
│   └── integration/      # Integration tests
├── docs/                 # Documentation
├── screenshots/          # Project screenshots
├── test_generation/      # Test generation utilities
├── CLAUDE.md            # This file
├── README.md            # Project overview
└── LICENSE
```

## Anti-Patterns to Avoid

- ❌ Don't create minimal context prompts - context is everything
- ❌ Don't skip validation steps - they're critical for success
- ❌ Don't ignore the structured PRP format
- ❌ Don't create new patterns when existing templates work
- ❌ Don't hardcode values that should be configurable
- ❌ Don't use broad exception handling

## Working with This Project

### Getting Started

1. **Prime Context**: Use `/prime-core` to understand the project
2. **Onboarding**: Use `/onboarding` for comprehensive project overview
3. **Create Features**: Use `/create-base-prp [description]` for new functionality
4. **Execute Work**: Use `/execute-base-prp PRPs/[feature].md` to implement

### Command Usage

- Access commands via `/` prefix in Claude Code
- Commands are self-documenting with argument placeholders
- Use the PRP methodology for all significant changes
- Leverage review commands before committing changes

## Development Guidelines

### Core Development Principles

#### 1. Planning & Problem Solving
- **ALWAYS use "Ultrathink"** when planning complex tasks or solving difficult issues
- Use sequential-thinking tool (`mcp__sequential-thinking__sequentialthinking`) for complex problem analysis
- Create detailed task execution plans before implementation
- Document architectural decisions and reasoning

#### 2. Technology Standards
- **Use latest versions** of all libraries and dependencies (as of July 2025)
- Always check for the most recent library versions and updates
- Stick strictly to documentation from context7 tool or from provided web links
- Stick strictly to the examples provided by a user

#### 3. Code Quality Standards
- **Keep files under 500 lines** to preserve readability
- Write concise, focused code with clear separation of concerns
- Follow Python PEP 8 style guidelines
- Use descriptive variable and function names
- Add docstrings for all public functions and classes

#### 4. Implementation Approach
- **Implement iterative approach**: Verify functionality with real app after ANY changes
- Only add complexity after verifying core features work with real app
- Always create REAL implementation - no fake data or mock implementations
- Choose the most straightforward approach always
- Launch the app after changes to verify functionality

### PRP-Specific Guidelines

- **Always** create a PRP for non-trivial features
- **Include** comprehensive context in every PRP
- **Run** all validation gates before considering work complete
- **Document** important decisions and patterns
- **Test** thoroughly with both unit and integration tests

Remember: This project uses the PRP framework for **one-pass implementation success through comprehensive context and validation**. Every PRP should contain the exact context needed for successful implementation.