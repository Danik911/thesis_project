# Task-Master-AI Workflow Execution

Execute a comprehensive task using task-master-ai integration with full context research and documentation.

## Command: /tm-execute

**Arguments**: `$ARGUMENTS` - Task description or task ID to execute

Execute a complete task workflow following the 6-step task-master-ai methodology:

## Workflow Overview

1. **Task Understanding** - Analyze the task using task-master-ai tools
2. **Status Assessment** - Check existing work and known issues  
3. **Context Collection** - Research libraries, examples, and best practices
4. **Planning & Documentation** - Create execution plan and task documentation
5. **Issue Management** - Handle problems with structured research and recovery
6. **Quality Assurance** - Test implementation and ensure compliance

## Step 1: Task Understanding

First, analyze the provided task using task-master-ai integration:

```bash
# Get task details if ID provided
mcp__task-master-ai__get_task --id=$ARGUMENTS --projectRoot=/home/anteb/thesis_project

# Or get next available task if no ID
mcp__task-master-ai__next_task --projectRoot=/home/anteb/thesis_project

# Set task to in-progress
mcp__task-master-ai__set_task_status --id=[TASK_ID] --status=in-progress --projectRoot=/home/anteb/thesis_project
```

## Step 2: Status Assessment

Check the current state of work and any existing issues:

### Check Existing Task Documentation
1. **Read task folder**: Look in `/home/anteb/thesis_project/main/docs/tasks/` for:
   - `task_[ID]_*_report.md` files for completed or partial work
   - Progress reports and implementation details
   
2. **Check issues folder**: Look in `/home/anteb/thesis_project/main/docs/tasks_issues/` for:
   - `task_[ID]_issues.md` files for known problems
   - Previous troubleshooting attempts and solutions

### Assessment Actions
- If task is **new**: Proceed to full context collection
- If task is **partially done**: Read existing documentation and continue from checkpoint
- If task has **known issues**: Review issue documentation and plan resolution strategy

## Step 3: Context Collection

**CRITICAL**: Collect comprehensive context using all available MCP tools:

### 3.1 Library Research (ALWAYS USE)
```bash
# Research required libraries using context7
mcp__context7__resolve-library-id --libraryName="[LIBRARY_NAME]"
mcp__context7__get-library-docs --context7CompatibleLibraryID="[RESOLVED_ID]" --topic="[SPECIFIC_TOPIC]"
```

### 3.2 Examples and Best Practices (ALWAYS USE)  
```bash
# Search for implementation examples
mcp__one-search-mcp__one_search --query="[TECHNOLOGY] [FEATURE] example implementation"
mcp__one-search-mcp__one_search --query="[TECHNOLOGY] best practices [YEAR]"
mcp__one-search-mcp__one_search --query="[TECHNOLOGY] common issues troubleshooting"
```

### 3.3 Complex Research (USE FOR ARCHITECTURAL QUESTIONS)
```bash
# Use perplexity for complex questions
mcp__perplexity-mcp__reason --query="How to implement [COMPLEX_FEATURE] with [TECHNOLOGY]?"
mcp__perplexity-mcp__deep_research --query="[DOMAIN] implementation patterns and gotchas" --focus_areas=["architecture", "best_practices", "common_issues"]
```

### 3.4 Codebase Analysis
- Review `/home/anteb/thesis_project/test_generation/examples/` for workflow patterns
- Study existing implementations in `/home/anteb/thesis_project/main/src/`
- Check project dependencies in `pyproject.toml`

## Step 4: Planning & Documentation

### 4.1 Create Execution Plan
Use TodoWrite tool to create a detailed task breakdown:

```bash
# Create comprehensive todo list for the task
TodoWrite --todos=[
  {"id": "1", "content": "Research phase completion", "status": "completed", "priority": "high"},
  {"id": "2", "content": "Design implementation approach", "status": "pending", "priority": "high"},
  {"id": "3", "content": "Implement core functionality", "status": "pending", "priority": "high"},
  {"id": "4", "content": "Add error handling and validation", "status": "pending", "priority": "medium"},
  {"id": "5", "content": "Write comprehensive tests", "status": "pending", "priority": "high"},
  {"id": "6", "content": "Update documentation", "status": "pending", "priority": "low"}
]
```

### 4.2 Create Task Documentation
Create or update task documentation file:

**File**: `/home/anteb/thesis_project/main/docs/tasks/task_[ID]_[FEATURE_NAME]_report.md`

**Structure**:
```markdown
# Task [ID]: [TITLE] - [STATUS] Report

**Date Started**: [DATE]
**Status**: 🔄 IN PROGRESS  
**Complexity Score**: [SCORE]/10

## 📋 Task Overview
**Objective**: [CLEAR_DESCRIPTION]
**Requirements**: [DETAILED_REQUIREMENTS]

## 🔬 Research Summary
### Libraries and Technologies
- [LIBRARY_NAME]: [VERSION] - [PURPOSE]
- [DOCUMENTATION_LINKS]

### Best Practices Found
- [PRACTICE_1]: [DESCRIPTION]
- [PRACTICE_2]: [DESCRIPTION]

### Common Issues Identified
- [ISSUE_1]: [SOLUTION_APPROACH]
- [ISSUE_2]: [SOLUTION_APPROACH]

## 🎯 Implementation Plan
[DETAILED_STEP_BY_STEP_PLAN]

## 📊 Progress Updates
[TIMESTAMPED_PROGRESS_ENTRIES]
```

### 4.3 Confirmation Check
**ALWAYS ASK**: "Do you need more information, examples, or context before I proceed with implementation?"

## Step 5: Issue Management

When encountering problems during implementation:

### 5.1 Create Issue Documentation
**File**: `/home/anteb/thesis_project/main/docs/tasks_issues/task_[ID]_issues.md`

**Structure**:
```markdown
# Task [ID] Issues and Resolutions

**Date Created**: [DATE]
**Task**: [TASK_TITLE]

## 🚨 Issues Encountered

### Issue 1: [ISSUE_TITLE]
**Description**: [DETAILED_DESCRIPTION]
**Error Messages**: [ACTUAL_ERRORS]
**Attempted Solutions**: [WHAT_WAS_TRIED]
**Root Cause**: [ANALYSIS]

## 🔍 Research Findings
[PERPLEXITY_RESEARCH_RESULTS]

## 🛠️ Resolution Plan
[STEP_BY_STEP_SOLUTION]

## ✅ Final Resolution
[WHAT_ACTUALLY_WORKED]
```

### 5.2 Issue Research Process
```bash
# Research the specific issue
mcp__perplexity-mcp__reason --query="[SPECIFIC_ERROR] troubleshooting [TECHNOLOGY]"
mcp__one-search-mcp__one_search --query="[ERROR_MESSAGE] solution [YEAR]"

# For complex issues, use sequential thinking
mcp__sequential-thinking__sequentialthinking --thought="Analyzing the root cause of [ISSUE]..."
```

### 5.3 Recovery Strategy
- Document all attempts and findings in the issue file
- Try alternative approaches based on research
- If issue persists after multiple attempts, ask for user guidance
- Consider alternative implementations if original approach has known limitations

## Step 6: Quality Assurance

### 6.1 Implementation Standards
- **Use latest libraries**: Ensure July 2025 compatible versions
- **Follow project patterns**: Match existing code style and architecture
S

### 6.2 Testing Requirements
```bash
# Lint and format code
uv run ruff check --fix src/
uv run mypy src/

# Run comprehensive tests
uv run pytest tests/ -v
uv run pytest tests/unit/[FEATURE]/ -v
uv run pytest tests/integration/[FEATURE]/ -v
```

### 6.3 Completion Workflow
```bash
# Update task status
mcp__task-master-ai__update_task --id=[TASK_ID] --prompt="Implementation completed with [SUMMARY]" --projectRoot=/home/anteb/thesis_project

# Mark subtasks as complete
mcp__task-master-ai__set_task_status --id=[TASK_ID].[SUBTASK_ID] --status=done --projectRoot=/home/anteb/thesis_project

# Final task completion (ONLY after user confirmation)
mcp__task-master-ai__set_task_status --id=[TASK_ID] --status=done --projectRoot=/home/anteb/thesis_project
```

## 🚨 CRITICAL OPERATING PRINCIPLES

### Never Claim Success Without User Confirmation
- ❌ NEVER say "working", "successful", "complete" without user verification
- ✅ ALWAYS ask "Did you experience the expected result?" before claiming success
- ✅ ALWAYS wait for user confirmation before marking tasks complete

### Package Installation Policy
- **NEVER skip** package installation due to permission issues
- **ALWAYS ask user** to install missing packages instead of proceeding
- **NEVER assume** packages are optional if required for functionality

### System Dependencies
- When encountering "Permission denied": Ask user to run with appropriate permissions
- When encountering missing packages: Stop and request user installation
- Never skip system-level operations - always request user assistance

## Usage Examples

```bash
# Execute specific task by ID
/tm-execute 2

# Execute task by description
/tm-execute "implement GAMP-5 categorization agent"

# Continue work on partially completed task
/tm-execute 4.2
```

## Integration with Project Structure

This command integrates seamlessly with:
- **Task-Master AI**: Project management and task tracking
- **PRP Framework**: Technical specifications in `/PRPs/` directory
- **GAMP-5 Requirements**: Pharmaceutical compliance standards
- **LlamaIndex Workflows**: Event-driven multi-agent architecture

## Success Criteria

A task is considered successfully executed when:
1. ✅ All research context has been collected and documented
2. ✅ Implementation follows project standards and best practices
3. ✅ Comprehensive tests pass (lint, type check, unit, integration)
4. ✅ Documentation is updated in both task files and issue files (if applicable)
5. ✅ User confirms the implementation meets requirements
6. ✅ Task status is properly updated in task-master-ai system

**Remember**: This is a pharmaceutical validation system requiring regulatory compliance. Always prioritize compliance and thorough documentation over speed.