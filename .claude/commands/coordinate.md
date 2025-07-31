---
allowed-tools: Task, mcp__task-master-ai__get_task, mcp__task-master-ai__set_task_status, mcp__task-master-ai__next_task, mcp__task-master-ai__update_task, mcp__task-master-ai__update_subtask, mcp__task-master-ai__get_tasks, Read, Write, Edit, Grep, Glob
description: CRITICAL coordination command - main agent directly orchestrates complete pharmaceutical development workflow using specialized agents
argument-hint: [task_id] | next | status
---

# Coordinate Pharmaceutical Development Workflow

**CRITICAL**: This command enables the main agent (Claude Code) to directly orchestrate specialized agents for pharmaceutical GAMP-5 compliant development.

## Task Context Discovery

- Current Task-Master AI status: !`mcp__task-master-ai__get_tasks --status=pending | head -5`
- Recent workflow activity: !`ls -la main/docs/tasks/ | head -10`
- Active issues: !`ls -la main/docs/tasks_issues/ 2>/dev/null | head -5 || echo "No active issues"`

## Direct Orchestration Protocol

**IMPORTANT**: The main agent (you) will directly coordinate all subagents, managing context flow between them.

### Step 1: Task Retrieval
Based on $ARGUMENTS:
- If task ID provided: `mcp__task-master-ai__get_task --id=$ARGUMENTS`
- If "next": `mcp__task-master-ai__next_task`
- If "status": Show coordination status using `mcp__task-master-ai__get_tasks --status=in-progress`

### Step 2: Initialize Task Documentation
Create/update task documentation file: `main/docs/tasks/task_[id]_[description].md`

### Step 3: Execute Agent Workflow Sequence

**CRITICAL**: You MUST manage context between each agent call. Read previous outputs and synthesize comprehensive briefings.

#### Phase 1: Task Analysis
```
Use the task-analyzer agent to analyze task $TASK_ID and validate dependencies.
Provide complete task details and compliance requirements.
```

#### Phase 2: Context Collection (if needed)
```
Read task-analyzer output from main/docs/tasks/task_[id]_[description].md.
If research is needed:
Use the context-collector agent to gather research and context for task $TASK_ID.
Include: [previous analysis results, specific research areas, compliance focus]
```

#### Phase 3: Task Execution
```
Read all previous agent outputs from documentation file.
Use the task-executor agent to implement task $TASK_ID.
Provide: [complete context from analysis and research, implementation requirements, success criteria]
```

#### Phase 4: Testing & Validation
```
Read implementation details from documentation file.
Use the tester-agent to validate implementation for task $TASK_ID.
Include: [implementation specifics, test requirements, compliance criteria]
```

#### Phase 5: End-to-End Testing (for major features)
```
If major feature:
Use the end-to-end-tester agent to perform comprehensive workflow testing.
Provide: [complete workflow context, integration points, expected behavior]
```

#### Phase 6: Monitoring Analysis (for major features)
```
If Phoenix monitoring is relevant:
Use the monitor-agent to analyze observability and traces.
Include: [workflow execution results, performance requirements, monitoring criteria]
```

### Step 4: Error Handling & Escalation
If any agent reports failures or issues:
```
Use the debugger agent to analyze and resolve [specific issue].
Provide: [complete error context, diagnostic information, previous attempts]
```

### Step 5: Update Task Status
- Update Task-Master AI: `mcp__task-master-ai__set_task_status --id=$TASK_ID --status=[appropriate status]`
- Update subtasks if applicable: `mcp__task-master-ai__update_subtask`

## **CRITICAL** Context Management Protocol

Between EACH agent invocation, you MUST:
1. **Read** the complete task documentation file
2. **Synthesize** all previous agent outputs
3. **Prepare** comprehensive context for the next agent
4. **Include** specific guidance based on previous results
5. **Update** the documentation file with new outputs

## Compliance Requirements
- **GAMP-5**: Maintain categorization and validation throughout
- **ALCOA+**: Ensure data integrity principles
- **21 CFR Part 11**: Complete audit trail
- **NO FALLBACKS**: Fail explicitly with diagnostics if issues occur

**REMEMBER**: You are the central orchestrator. Each subagent depends on you for context and guidance.
