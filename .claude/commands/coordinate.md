---
allowed-tools: Task, mcp__task-master-ai__get_task, mcp__task-master-ai__set_task_status, mcp__task-master-ai__next_task
description: CRITICAL coordination command - orchestrates complete pharmaceutical development workflow using specialized agents
argument-hint: [task_id] | next | status
---

# Coordinate Pharmaceutical Development Workflow

**IMPORTANT**: This command triggers the master workflow coordinator to orchestrate specialized agents for pharmaceutical GAMP-5 compliant development.

## Task Context Discovery

- Current Task-Master AI status: !`mcp__task-master-ai__get_tasks --status=pending | head -5`
- Recent workflow activity: !`ls -la main/docs/tasks/ | head -10`
- Active issues: !`ls -la main/docs/tasks_issues/ 2>/dev/null | head -5 || echo "No active issues"`

## Coordination Request

Use the workflow-coordinator agent to orchestrate a complete pharmaceutical development workflow.

**CRITICAL INSTRUCTIONS**:
1. **Context Management**: Ensure each specialized agent receives complete context from previous agents
2. **Compliance Focus**: Maintain GAMP-5, ALCOA+, and 21 CFR Part 11 requirements throughout
3. **Error Escalation**: Route complex issues to debugger agent with full diagnostic context
4. **Audit Trail**: Maintain complete traceability in task documentation files

**Arguments**:
- If task ID provided: Coordinate workflow for specific task $ARGUMENTS
- If "next" provided: Get next available task and coordinate workflow
- If "status" provided: Show current coordination status and active workflows

**Workflow Sequence**:
1. task-analyzer → dependency validation and initial documentation
2. context-collector → research and context gathering (if needed)
3. task-executor → implementation with compliance requirements  
4. tester-agent → validation and quality assurance
5. end-to-end-tester → comprehensive testing (for major features)
6. monitor-agent → Phoenix observability analysis and monitoring assessment (CRITICAL for major features)

**MUST** use workflow-coordinator agent to ensure proper context flow between isolated subagents.
