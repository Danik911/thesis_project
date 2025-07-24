# CLAUDE.md

This file provides guidance to Claude Code when working with this thesis project.

## 🚨 CRITICAL OPERATING PRINCIPLE 🚨

**NEVER CLAIM SUCCESS WITHOUT USER CONFIRMATION**

- ❌ NEVER say "working", "successful", "complete", "fixed", "resolved" without explicit user verification
- ✅ ALWAYS ask "Did you hear/see/experience the expected result?" before claiming success
- ✅ ALWAYS wait for user confirmation before updating status to "complete"

## Project Overview

**Thesis Project**: Multi-agent LLM system for pharmaceutical test generation (GAMP-5 compliant)
**Dual Framework**: Task-Master AI (project management) + PRP Framework (technical specs)

## 🎯 Task-Master AI Integration

### Essential Commands
```bash
# Daily workflow
mcp__task-master-ai__next_task                    # Get next task
mcp__task-master-ai__get_task --id=X              # View task details
mcp__task-master-ai__set_task_status --id=X --status=in-progress
mcp__task-master-ai__update_subtask --id=X.Y --prompt="Progress notes"
mcp__task-master-ai__set_task_status --id=X.Y --status=done

# Task management
mcp__task-master-ai__expand_task --id=X --research
mcp__task-master-ai__research --query="..." --taskIds="X,Y"
mcp__task-master-ai__get_tasks --status=pending
```

### Pre-configured Tasks
- **14 main tasks** following GAMP-5 implementation order
- **19+ subtasks** for detailed tracking
- **Dependencies** enforced for proper workflow
- **Compliance focus** (ALCOA+, 21 CFR Part 11)

**📖 Full Documentation**: [Task-Master AI Guide](https://github.com/eyaltoledano/claude-task-master/blob/main/docs/tutorial.md)

## 🔧 PRP Framework Integration

### Core Commands
```bash
/create-base-prp "feature description"     # Generate comprehensive PRPs
/execute-base-prp PRPs/feature.md         # Execute PRP implementation
/review-staged-unstaged                    # Review changes
```

### Usage Pattern
- **Task-Master**: Daily progress tracking, dependencies, research
- **PRP**: Detailed technical specifications and implementation guidance
- **Integration**: Reference PRP details within task-master tasks

## 🏗️ Development Workflow

### 1. Start Development Session
```bash
mcp__task-master-ai__next_task              # Get next available task
mcp__task-master-ai__set_task_status --id=X --status=in-progress
```

### 2. During Implementation
```bash
# Log progress frequently
mcp__task-master-ai__update_subtask --id=X.Y --prompt="Implementation notes"

# Research when stuck
mcp__task-master-ai__research --query="specific question" --taskIds="X"

# Use PRP for complex features
/execute-base-prp PRPs/detailed-feature.md
```

### 3. Complete Tasks
```bash
# Mark subtasks complete
mcp__task-master-ai__set_task_status --id=X.Y --status=done

# Validate with tests
uv run ruff check --fix && uv run mypy .
uv run pytest tests/ -v

# Mark main task complete
mcp__task-master-ai__set_task_status --id=X --status=done
```

## 🧪 Critical Project Requirements

### Architecture
- **LlamaIndex 0.12.0+** workflows with event-driven multi-agent system
- **GAMP-5 categorization** as critical first step
- **Compliance validation** (ALCOA+, 21 CFR Part 11)
- **Error handling** with comprehensive recovery

### Technology Stack
- **Python 3.12+** with UV package manager
- **Claude Sonnet 4.0** (configured in task-master)
- **Phoenix AI** monitoring integration
- **ChromaDB** with transactional support

### Development Principles
- **Research first**: Always check context7 and official docs
- **Incremental validation**: Test after each change
- **Compliance focus**: All implementations must be GAMP-5 compliant
- **Error prevention**: Address known gotchas proactively

## 📂 Project Structure
```
thesis_project/
├── .taskmaster/           # Task-Master AI (project management)
├── PRPs/                  # PRP Framework (technical specs)
├── src/agents/            # Multi-agent implementation
├── src/core/              # Workflow orchestration
├── tests/                 # Comprehensive test suites
└── .claude/commands/      # Custom Claude commands
```

## 🔗 External Resources

- **Task-Master Documentation**: [GitHub Repository](https://github.com/eyaltoledano/claude-task-master)
- **Task-Master Tutorial**: [Getting Started Guide](https://github.com/eyaltoledano/claude-task-master/blob/main/docs/tutorial.md)
- **GAMP-5 Guidelines**: [ISPE GAMP-5](https://ispe.org/publications/guidance-documents/gamp-5)
- **LlamaIndex Workflows**: [Official Documentation](https://docs.llamaindex.ai/en/stable/module_guides/workflow/)
- **21 CFR Part 11**: [FDA Guidance](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/part-11-electronic-records-electronic-signatures-scope-and-application)

## ⚡ Quick References

**Status Values**: `pending`, `in-progress`, `done`, `blocked`, `deferred`, `cancelled`
**Priority Levels**: `high`, `medium`, `low`
**Task ID Format**: Main tasks (1, 2, 3), Subtasks (1.1, 1.2, 2.1)

Remember: This project requires **regulatory compliance** and **pharmaceutical validation standards**. Always prioritize compliance over speed.