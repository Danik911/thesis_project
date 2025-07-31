---
allowed-tools: Task, mcp__task-master-ai__get_tasks, Read, Grep
description: Quick status check for active pharmaceutical development workflows and agent coordination
---

# Pharmaceutical Workflow Status Check

## Current Workflow Status

- Active tasks: !`mcp__task-master-ai__get_tasks --status=in-progress`
- Pending tasks: !`mcp__task-master-ai__get_tasks --status=pending | head -3`
- Recent task documentation: !`ls -la main/docs/tasks/ | head -5`
- Active issues: !`ls -la main/docs/tasks_issues/ 2>/dev/null | head -3 || echo "No active issues"`

## Coordination Analysis

Use the workflow-coordinator agent to:
1. **Analyze** current workflow state and agent coordination status
2. **Identify** any blocked or stalled workflows requiring intervention
3. **Assess** context flow between specialized agents
4. **Recommend** next coordination actions or error escalation

**CRITICAL**: Check for incomplete context handoffs between isolated subagents that may be causing workflow blockages.

**Focus Areas**:
- Context continuity between agents
- Compliance requirement tracking
- Error escalation needs
- Task progression bottlenecks
