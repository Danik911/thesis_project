# Workflow Coordination System Documentation

## Overview

The **CRITICAL** main agent (Claude Code) directly orchestrates pharmaceutical multi-agent systems, coordinating specialized agents while maintaining GAMP-5 compliance and pharmaceutical regulatory requirements. **IMPORTANT**: The main agent serves as the central coordinator, managing context flow between isolated subagents.

## **IMPORTANT** Design Principles

### 1. Context Management Authority
- **CRITICAL RESPONSIBILITY**: The main agent (Claude Code) is the ONLY agent responsible for context flow between isolated subagents
- Each subagent operates in its own context window to prevent contamination
- Context sharing happens through structured documentation files and main agent mediation
- **NO** direct communication between subagents - ALL coordination flows through the main agent

### 2. Agent Specialization
Each specialized subagent has a specific expertise area:
- `task-analyzer`: Task analysis, dependency validation, initial documentation
- `context-collector`: Research, context gathering, multi-source investigation
- `task-executor`: Implementation with compliance requirements
- `tester-agent`: Validation, testing, quality assurance
- `end-to-end-tester`: Complete workflow validation with Phoenix observability
- `monitor-agent`: Phoenix observability analysis and monitoring assessment (CRITICAL for major features)
- `debugger`: Complex issue resolution using systematic analysis

### 3. Pharmaceutical Compliance
- **GAMP-5** categorization and validation throughout workflows
- **ALCOA+** data integrity principles maintained
- **21 CFR Part 11** audit trail requirements
- **Complete traceability** from task initiation to completion

## Coordination Workflow Patterns

### Standard Development Workflow
```
Task-Master AI → Main Agent → task-analyzer → context-collector → task-executor → tester-agent → Task-Master AI
```

### Research-Heavy Workflow
```
Task-Master AI → Main Agent → task-analyzer → context-collector (extended research) → task-executor → tester-agent → end-to-end-tester → Task-Master AI
```

### Major Feature Workflow
```
Task-Master AI → Main Agent → task-analyzer → context-collector → task-executor → tester-agent → end-to-end-tester → monitor-agent → Task-Master AI
```

### Issue Resolution Workflow
```
Any Agent → Main Agent → debugger → (resolution) → tester-agent → Task-Master AI
```

### Emergency Escalation Workflow
```
Blocked Agent → Main Agent → debugger → human consultation → recovery workflow
```

## **CRITICAL** Context Sharing Mechanism

### Documentation File Structure
All context sharing happens through structured files in `main/docs/tasks/`:
```
main/docs/tasks/task_[id]_[description].md
├── ## Purpose and Objectives (by task-analyzer)
├── ## Dependencies Analysis (by task-analyzer)  
├── ## Research and Context (by context-collector)
├── ## Implementation (by task-executor)
├── ## Testing and Validation (by tester-agent)
├── ## End-to-End Testing (by end-to-end-tester, if applicable)
├── ## Monitoring Analysis (by monitor-agent, if applicable)
└── ## Coordination Summary (by main agent)
```

### Context Handoff Protocol
**CRITICAL**: The main agent MUST perform these steps between each subagent invocation:
1. **Read** complete context from previous agent sections in task documentation
2. **Synthesize** information for next agent with comprehensive briefing
3. **Prepare** specific guidance based on previous agent outputs
4. **Include** compliance requirements and success criteria
5. **Update** task documentation with coordination decisions
6. **Provide** complete context to next subagent via Task tool

## Usage Instructions

### Using Slash Commands (Recommended)

#### Start Coordinated Workflow
```bash
# Coordinate specific task
/coordinate 3.2

# Coordinate next available task
/coordinate next

# Check coordination status
/coordinate status
```

#### Check Workflow Status
```bash
# Get comprehensive status
/workflow-status
```

#### Emergency Escalation
```bash
# Escalate specific task
/escalate 3.2

# Escalate most recent issue
/escalate last

# Analyze all blocked workflows
/escalate all
```

### Direct Main Agent Orchestration
The main agent (Claude Code) directly coordinates all subagents:
```bash
# Main agent uses Task tool with subagent_type parameter
Use the task-analyzer agent to analyze task 3.2 and validate dependencies.
Use the context-collector agent to gather research for task 3.2.
Use the task-executor agent to implement task 3.2.
# ... continuing with other agents as needed
```

## **IMPORTANT** Error Handling

### Error Escalation Matrix
| Error Type | Escalation Path | Required Action |
|------------|-----------------|-----------------|
| Dependency blocked | task-analyzer → main agent → human consultation | Dependency resolution |
| Research insufficient | context-collector → main agent → debugger → additional research | Context enhancement |
| Implementation failure | task-executor → main agent → debugger → root cause analysis | Technical resolution |
| Test failures | tester-agent → main agent → debugger → fix validation | Quality assurance |
| Compliance violations | Any agent → main agent → human consultation | Regulatory review |

### **NO FALLBACKS** Policy
- **NEVER** mask errors with artificial success reporting
- **ALWAYS** expose real system state to users
- **FAIL LOUDLY** with complete diagnostic information
- **PRESERVE** genuine confidence levels and uncertainties

## Agent Communication Protocols

### Context Preparation Before Handoff
The main agent **MUST** provide each subagent with:
1. **Complete context** from all previous agents
2. **Specific task requirements** clearly defined
3. **Compliance implications** identified and communicated
4. **Error handling guidance** for edge cases
5. **Success criteria** and next steps outlined

### Monitoring and Status Updates
- Main agent monitors each subagent's execution for failures or blocking issues
- Main agent updates Task-Master AI with progress throughout workflow
- Main agent maintains audit trail in task documentation files
- Main agent routes to human consultation when compliance issues arise

## Best Practices

### For Users
1. **Use slash commands** for standard workflows (`/coordinate`, `/workflow-status`, `/escalate`)
2. **Provide specific task IDs** when possible for targeted coordination
3. **Monitor workflow progress** through Task-Master AI integration
4. **Escalate early** when issues are detected rather than waiting

### For Agent Development
1. **Follow documentation templates** exactly for consistency
2. **Include main agent handoff sections** in all subagent outputs
3. **Maintain compliance focus** throughout implementation
4. **Test context flow** through main agent coordination during development

### For Pharmaceutical Compliance
1. **Validate GAMP-5 requirements** at each workflow stage
2. **Maintain complete audit trails** in documentation files
3. **Escalate compliance concerns** immediately to human review
4. **Document all coordination decisions** for regulatory inspection

## Integration with Existing Systems

### Task-Master AI Integration
- Automatic task retrieval and status updates
- Progress tracking throughout coordinated workflows
- Dependency validation and management
- Research integration when needed

### Phoenix Observability Integration
- Complete workflow tracing through end-to-end-tester
- Performance monitoring and bottleneck identification
- Error tracking and resolution documentation

### Development Environment Integration
- Code quality validation through tester-agent
- Real workflow execution with actual API calls
- Compliance requirement verification

## Troubleshooting

### Common Issues

#### Context Not Flowing Between Agents
**Problem**: Subagents lack necessary context from previous work
**Solution**: Main agent must read and synthesize complete context before each handoff

#### Workflow Stalls or Blocks
**Problem**: Tasks get stuck in one agent without progression
**Solution**: Use `/escalate` command to route to debugger with full diagnostic context

#### Compliance Violations
**Problem**: Regulatory requirements not properly tracked
**Solution**: Main agent escalates to human consultation immediately

#### Test Failures or Quality Issues
**Problem**: Implementation doesn't meet validation criteria
**Solution**: Main agent routes back through debugger → task-executor → tester-agent cycle

### Diagnostic Commands
```bash
# Check current workflow state
/workflow-status

# Review recent task documentation
ls -la main/docs/tasks/

# Check for error logs
grep -r "ERROR\|FAIL" main/logs/

# Review Task-Master AI status
mcp__task-master-ai__get_tasks --status=in-progress
```

## **CRITICAL** Success Metrics

The coordination system is successful when:
- **Context Continuity**: Each subagent receives complete necessary context from main agent
- **Workflow Efficiency**: Minimal back-and-forth between agents through proper coordination
- **Compliance Maintenance**: All regulatory requirements tracked and validated by main agent
- **Error Resolution**: Issues escalated and resolved systematically through main agent
- **Audit Trail Completeness**: Full traceability from start to finish maintained by main agent

**Remember**: The main agent (Claude Code) is the central intelligence that connects specialized subagents into a cohesive, compliant, and effective development workflow. Every coordination decision impacts patient safety and regulatory compliance.
