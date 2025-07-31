---
allowed-tools: Task, mcp__task-master-ai__get_task, Read, Grep, Glob
description: EMERGENCY coordination command - escalates blocked workflows to debugger agent with full diagnostic context
argument-hint: [task_id] | last | all
---

# Emergency Workflow Escalation

**CRITICAL**: This command handles workflow failures and escalates complex issues to the debugger agent.

## Current Workflow Diagnostics

- Recent task activity: !`ls -lt main/docs/tasks/ | head -5`
- Error logs: !`ls -lt main/logs/ | head -5`
- Issue tracking: !`ls -la main/docs/tasks_issues/ 2>/dev/null || echo "No tracked issues"`
- Workflow execution logs: !`grep -r "ERROR\|FAIL" main/logs/ | tail -10 || echo "No recent errors in logs"`

## Emergency Escalation Request

Use the workflow-coordinator agent to:
1. **Diagnose** the blocking issue with complete context analysis
2. **Escalate** to debugger agent with full diagnostic information
3. **Coordinate** recovery workflow after issue resolution
4. **Update** Task-Master AI with escalation status

**Arguments**:
- If task ID provided: Escalate specific task $ARGUMENTS
- If "last" provided: Escalate most recent workflow issue
- If "all" provided: Analyze all currently blocked workflows

**IMPORTANT**: Maintain pharmaceutical compliance requirements during emergency escalation and ensure complete audit trail of issue resolution.

**NO FALLBACKS**: If workflows are blocked, FAIL LOUDLY with complete diagnostic information rather than masking issues.
