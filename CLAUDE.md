# CLAUDE.md

This file provides guidance to Claude Code when working with this thesis project.

## 🚨 CRITICAL OPERATING PRINCIPLE 🚨

**NEVER CLAIM SUCCESS WITHOUT USER CONFIRMATION**

- ❌ NEVER say "working", "successful", "complete", "fixed", "resolved" without explicit user verification
- ✅ ALWAYS ask "Did you hear/see/experience the expected result?" before claiming success
- ✅ ALWAYS wait for user confirmation before updating status to "complete"

## 🚨 ABSOLUTE RULE: NO FUCKING FALLBACKS 🚨

**ZERO TOLERANCE FOR FALLBACK LOGIC**

- ❌ NEVER implement fallback values, default behaviors, or "safe" alternatives
- ❌ NEVER mask errors with artificial confidence scores
- ❌ NEVER create deceptive logic that hides real system behavior
- ✅ ALWAYS throw errors with full stack traces when something fails
- ✅ ALWAYS preserve genuine confidence levels and uncertainties
- ✅ ALWAYS expose real system state to users for regulatory compliance

**If something doesn't work - FAIL LOUDLY with complete diagnostic information**

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
**Current Status**: MVP implementation (Tasks 1-9) - ~1 week timeline
**Focus**: OQ test generation only, fix categorization agent issues

## 🤖 LLM Configuration

- **Production Model**: `deepseek/deepseek-chat` (DeepSeek V3 - 671B MoE) via OpenRouter
- **Development Model**: `gpt-4.1-mini-2025-04-14` (for rapid prototyping)
- **Task-Master AI**: Claude Sonnet 4.0 (via MCP)
- **Cost Achievement**: 91% reduction ($15 → $1.35 per 1M tokens)


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

### MVP Status: ✅ COMPLETE
- **All 9 Tasks**: Successfully completed
- **OSS Migration**: DeepSeek V3 deployed
- **Test Generation**: 30 OQ tests (120% of target)
- **Phoenix Monitoring**: 131 spans captured
- **ChromaDB**: 26 documents indexed
- **Cost Reduction**: 91% achieved

**Implementation Plan**: [`main/docs/mvp_implementation_plan.md`](main/docs/mvp_implementation_plan.md)

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
- **NO FALLBACKS**: Fail explicitly with full diagnostic information

## 🤖 Subagent Workflow System

You have 6 specialized subagents at `/home/anteb/thesis_project/.claude/agents/`:

### Core Subagents
- **context-collector**: Research specialist for GAMP-5 compliance, LlamaIndex patterns, pharmaceutical standards
- **debugger**: Advanced debugging with systematic root cause analysis using Ultrathink methodology - **NO FALLBACKS ALLOWED**
- **task-analyzer**: Analyzes Task-Master AI tasks, checks dependencies, creates execution documentation
- **task-executor**: Executes specific Task-Master AI tasks following GAMP-5 compliance patterns - **NO FALLBACKS ALLOWED** 
- **tester-agent**: Validates implementations, runs tests, ensures regulatory compliance - **NO FALLBACKS ALLOWED**
- **monitor-agent**: Phoenix observability analysis and monitoring assessment specialist - **NO FALLBACKS ALLOWED**

### 🚨 Critical Orchestration Rules
- **Subagents lack context**: Always provide comprehensive context when delegating tasks
- **Verify results**: Must check and validate all subagent work before accepting
- **Orchestration responsibility**: You manage workflow coordination and final decisions
- **NO FALLBACKS**: All subagents must fail explicitly rather than mask problems

## 📚 Key Documentation & Reports

### Essential References
- **OSS Migration Report**: [`main/docs/tasks_issues/oss_migration_comprehensive_report.md`](main/docs/tasks_issues/oss_migration_comprehensive_report.md)
- **Honest Assessment**: [`main/docs/HONEST_ASSESSMENT_REPORT.md`](main/docs/HONEST_ASSESSMENT_REPORT.md)
- **Phoenix Guide**: [`main/docs/guides/PHOENIX_OBSERVABILITY_GUIDE.md`](main/docs/guides/PHOENIX_OBSERVABILITY_GUIDE.md)
- **Quick Start**: [`main/docs/guides/QUICK_START_GUIDE.md`](main/docs/guides/QUICK_START_GUIDE.md)
- **Test Output**: `main/output/test_suites/test_suite_OQ-SUITE-*.json`

## 📂 Project Structure
```
thesis_project/
├── .taskmaster/                              # Task-Master AI (9 MVP tasks)
├── main/                                     # Main application
│   ├── main.py                              # Current entry point
│   ├── src/core/unified_workflow.py         # Master workflow orchestrator
│   ├── src/agents/categorization/           # NEEDS FIXES (Task 1)
│   ├── src/agents/parallel/                 # Context, SME, Research agents
│   ├── docs/mvp_implementation_plan.md      # MVP roadmap
│   └── tests/                               # Test suites
├── .claude/agents/                          # Subagent specifications
└── PRPs/                                    # Technical specs (reference)
```

## 🚨 Critical Files for MVP
- `main/src/agents/categorization/agent.py` - Remove fallback logic (Task 1)
- `main/src/agents/parallel/context_provider.py` - Integration tool (Task 3)
- `main/tests/test_data/gamp5_test_data/testing_data.md` - Test cases

## 🔗 Key References

- **Task-Master AI**: [Tutorial Guide](https://github.com/eyaltoledano/claude-task-master/blob/main/docs/tutorial.md)
- **LlamaIndex Workflows**: [Official Docs](https://docs.llamaindex.ai/en/stable/module_guides/workflow/)

## ⚡ Quick References

**Status Values**: `pending`, `in-progress`, `done`, `blocked`, `deferred`, `cancelled`
**Priority Levels**: `high`, `medium`, `low`
**Task ID Format**: Main tasks (1, 2, 3), Subtasks (1.1, 1.2, 2.1)

Remember: This project requires **regulatory compliance** and **pharmaceutical validation standards**. Always prioritize compliance over speed. **NEVER IMPLEMENT FALLBACKS - FAIL EXPLICITLY WITH FULL DIAGNOSTIC INFORMATION.**