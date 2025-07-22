# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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
├── screenshots/          # Project screenshots
├── test_generation/      # Test generation utilities
├── CLAUDE.md            # This file
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

### Development Guidelines

- **Always** create a PRP for non-trivial features
- **Include** comprehensive context in every PRP
- **Run** all validation gates before considering work complete
- **Document** important decisions and patterns
- **Test** thoroughly with both unit and integration tests

Remember: This project uses the PRP framework for **one-pass implementation success through comprehensive context and validation**. Every PRP should contain the exact context needed for successful implementation.