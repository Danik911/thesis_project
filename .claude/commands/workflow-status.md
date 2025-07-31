---
allowed-tools: mcp__task-master-ai__get_tasks, Read, Grep, Glob
description: Quick status check for active pharmaceutical development workflows and agent coordination - directly analyzed by main agent
---

# Pharmaceutical Workflow Status Check

## Current Workflow Status

- Active tasks: !`mcp__task-master-ai__get_tasks --status=in-progress`
- Pending tasks: !`mcp__task-master-ai__get_tasks --status=pending | head -3`
- Recent task documentation: !`ls -la main/docs/tasks/ | head -5`
- Active issues: !`ls -la main/docs/tasks_issues/ 2>/dev/null | head -3 || echo "No active issues"`

## Direct Status Analysis Protocol

**IMPORTANT**: The main agent (you) will directly analyze workflow status and coordination health.

### Step 1: Workflow State Assessment
1. **Review** active tasks from Task-Master AI output above
2. **Check** task documentation files for each active task
3. **Identify** last agent execution for each workflow
4. **Determine** time since last progress update

### Step 2: Coordination Health Check
For each active workflow, verify:
- **Context Flow**: Read task documentation to ensure agents received proper context
- **Progress Status**: Check if workflow is progressing or stalled
- **Agent Handoffs**: Verify successful transitions between agents
- **Error States**: Look for failed agent executions or unresolved issues

### Step 3: Bottleneck Identification
**MUST** check for:
1. **Stalled Workflows**: Tasks in-progress > 24 hours without updates
2. **Failed Handoffs**: Incomplete context between agent transitions
3. **Dependency Blocks**: Tasks waiting on unresolved dependencies
4. **Error Accumulation**: Multiple failed attempts without escalation

### Step 4: Status Summary
Provide comprehensive status including:
- **Active Workflows**: Current state and last progress
- **Blocked Items**: Workflows requiring intervention
- **Success Rate**: Completed vs failed agent executions
- **Recommendations**: Next actions for each workflow

### Step 5: Compliance Verification
Ensure all active workflows maintain:
- **GAMP-5** categorization and validation
- **ALCOA+** data integrity principles
- **21 CFR Part 11** audit trail completeness
- **Complete traceability** in documentation

## **CRITICAL** Status Indicators

**Healthy Workflow**:
- Regular progress updates in task documentation
- Clear agent handoffs with context
- No error accumulation
- Compliance requirements tracked

**Workflow Requiring Attention**:
- No updates > 12 hours
- Failed agent executions
- Missing context documentation
- Compliance gaps identified

**REMEMBER**: Proactive status monitoring prevents workflow blockages and ensures pharmaceutical compliance.
