---
allowed-tools: Task, mcp__task-master-ai__get_task, mcp__task-master-ai__get_tasks, mcp__task-master-ai__update_task, Read, Write, Grep, Glob
description: EMERGENCY coordination command - main agent directly escalates blocked workflows to debugger agent with full diagnostic context
argument-hint: [task_id] | last | all
---

# Emergency Workflow Escalation

**CRITICAL**: This command enables the main agent to handle workflow failures and escalate complex issues directly to the debugger agent.

## Current Workflow Diagnostics

- Recent task activity: !`ls -lt main/docs/tasks/ | head -5`
- Error logs: !`ls -lt main/logs/ | head -5`
- Issue tracking: !`ls -la main/docs/tasks_issues/ 2>/dev/null || echo "No tracked issues"`
- Workflow execution logs: !`grep -r "ERROR\|FAIL" main/logs/ | tail -10 || echo "No recent errors in logs"`

## Direct Emergency Escalation Protocol

**IMPORTANT**: The main agent (you) will directly handle the escalation process.

### Step 1: Identify Blocked Workflows
Based on $ARGUMENTS:
- If task ID provided: `mcp__task-master-ai__get_task --id=$ARGUMENTS`
- If "last": Examine most recent task documentation in `main/docs/tasks/`
- If "all": `mcp__task-master-ai__get_tasks --status=in-progress` and check for stalled items

### Step 2: Gather Diagnostic Context
**MUST** collect comprehensive diagnostic information:
1. Read task documentation file: `main/docs/tasks/task_[id]_[description].md`
2. Check error logs: Search for task-related errors in `main/logs/`
3. Review agent outputs: Identify where workflow failed
4. Compile diagnostic summary with:
   - Last successful agent execution
   - Point of failure
   - Error messages and stack traces
   - Previous resolution attempts

### Step 3: Escalate to Debugger
```
Use the debugger agent to analyze and resolve the blocked workflow for task $TASK_ID.
Provide COMPLETE diagnostic context including:
- Full task context and requirements
- All previous agent outputs
- Specific failure point and error details
- Stack traces and diagnostic logs
- Previous resolution attempts
- Compliance implications
```

### Step 4: Coordinate Recovery
After debugger analysis:
1. **Implement** recommended fixes
2. **Resume** workflow from appropriate point
3. **Re-engage** necessary agents with updated context
4. **Validate** resolution meets compliance requirements

### Step 5: Update Documentation
- Create/update issue tracking: `main/docs/tasks_issues/issue_[task_id]_[timestamp].md`
- Update task documentation with resolution
- Update Task-Master AI: `mcp__task-master-ai__update_task --id=$TASK_ID --prompt="Issue resolved: [summary]"`

## **CRITICAL** Escalation Requirements

- **Complete Context**: Provide debugger with ALL relevant information
- **Audit Trail**: Document entire escalation and resolution process
- **Compliance**: Maintain GAMP-5, ALCOA+, and 21 CFR Part 11 requirements
- **NO FALLBACKS**: Expose real failure state with full diagnostics

**REMEMBER**: Quick escalation with complete context leads to faster resolution.
