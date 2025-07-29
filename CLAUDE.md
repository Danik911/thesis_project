# CLAUDE.md

This file provides guidance to Claude Code when working with this thesis project.

## 🚨 CRITICAL OPERATING PRINCIPLE 🚨

**NEVER CLAIM SUCCESS WITHOUT USER CONFIRMATION**

- ❌ NEVER say "working", "successful", "complete", "fixed", "resolved" without explicit user verification
- ✅ ALWAYS ask "Did you hear/see/experience the expected result?" before claiming success
- ✅ ALWAYS wait for user confirmation before updating status to "complete"

## 🔧 System Dependencies & Permissions

### Package Installation Policy
- **NEVER skip** package installation due to permission issues
- **ALWAYS ask user** to install missing packages instead of proceeding without them
- **NEVER assume** packages are optional if they're required for functionality

### Required Actions:
- **Missing packages**: Stop and ask user to install rather than skipping
- **Permission denied**: Request user run with appropriate permissions
- **System operations**: Always ask for user assistance

## Project Overview

**Thesis Project**: Multi-agent LLM system for pharmaceutical test generation (GAMP-5 compliant)
**Management Framework**: Task-Master AI for project management and workflow tracking

## 🤖 LLM Configuration

- **Development Model**: `gpt-4.1-mini-2025-04-14` (cost-efficient)
- **Task-Master AI**: Claude Sonnet 4.0 (via MCP)
- **🚨 Critical Issue**: NEVER use `response_format={"type": "json_object"}` with LlamaIndex `FunctionAgent` - causes infinite loops

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
- **GAMP-5 implementation workflow** with enforced dependencies
- **Detailed subtask tracking** for granular progress
- **Compliance focus** (ALCOA+, 21 CFR Part 11)

**📖 Full Documentation**: [Task-Master AI Guide](https://github.com/eyaltoledano/claude-task-master/blob/main/docs/tutorial.md)

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

## 🤖 Subagent Workflow System

You have 5 specialized subagents at `/home/anteb/thesis_project/.claude/agents/`:

### Core Subagents
- **context-collector**: Research specialist for GAMP-5 compliance, LlamaIndex patterns, pharmaceutical standards
- **debugger**: Advanced debugging with systematic root cause analysis using Ultrathink methodology
- **task-analyzer**: Analyzes Task-Master AI tasks, checks dependencies, creates execution documentation
- **task-executor**: Executes specific Task-Master AI tasks following GAMP-5 compliance patterns
- **tester-agent**: Validates implementations, runs tests, ensures regulatory compliance

### 🚨 Critical Orchestration Rules
- **Subagents lack context**: Always provide comprehensive context when delegating tasks
- **Verify results**: Must check and validate all subagent work before accepting
- **Orchestration responsibility**: You manage workflow coordination and final decisions

## 📂 Project Structure
```
thesis_project/
├── .taskmaster/                              # Task-Master AI (project management)
├── PRPs/                                     # PRP Framework (technical specs)
├── main/                                     # Main application
│   ├── main.py                              # Main entry point
│   ├── src/core/unified_workflow.py         # Master workflow orchestrator
│   ├── docs/                                # All project documentation
│   └── tests/                               # Comprehensive test suites
├── test_generation/examples/scientific_writer/thesis/  # Legacy examples for reference
└── .claude/agents/                          # Subagent specifications
```

## 🔗 Key References

- **Task-Master AI**: [Tutorial Guide](https://github.com/eyaltoledano/claude-task-master/blob/main/docs/tutorial.md)
- **LlamaIndex Workflows**: [Official Docs](https://docs.llamaindex.ai/en/stable/module_guides/workflow/)

## ⚡ Quick References

**Status Values**: `pending`, `in-progress`, `done`, `blocked`, `deferred`, `cancelled`
**Priority Levels**: `high`, `medium`, `low`
**Task ID Format**: Main tasks (1, 2, 3), Subtasks (1.1, 1.2, 2.1)

Remember: This project requires **regulatory compliance** and **pharmaceutical validation standards**. Always prioritize compliance over speed.