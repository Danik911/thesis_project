---
name: task-analyzer
description: (DEPRECATED - Not used in PRP workflow) Legacy agent for Task-Master AI integration. The project now uses manually created PRP tasks with the /prp workflow instead.
tools: Read, Grep, Glob, Write
color: blue
---

**NOTICE: This agent is deprecated and not used in the current PRP workflow.**

The project now uses manually created PRP tasks executed via the `/prp {task-id}` workflow command, which orchestrates:
- context-collector (research)
- task-executor (implementation)
- tester-agent (validation)
- debugger (conditional issue resolution)

See `CLAUDE.md` for complete PRP workflow documentation.

---

## Legacy Documentation (For Reference Only)

This agent was originally designed for Task-Master AI integration but is no longer actively used.

## Documentation Template (Legacy)
Create: `main/docs/tasks/task_[id]_[description].md`

```markdown
# Task [ID]: [Title]

## Purpose and Objectives
[Clear statement of what needs accomplishing]

## Dependencies Analysis  
[Prerequisites and their current status]

## Implementation Approach
[High-level strategy based on project patterns]

## Success Criteria
[How to measure completion]

## Notes for Next Agents
[Specific guidance for context-collector and task-executor]
```

**Focus**: Solid foundation for execution workflow. Never proceed with blocked dependencies. Flag compliance risks early.