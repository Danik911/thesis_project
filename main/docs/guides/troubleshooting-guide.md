# Multi-Agent Workflow Troubleshooting Guide

**🚨 CRITICAL PRINCIPLE**: NO FALLBACKS - All issues must produce explicit diagnostic information

## Common Issues & Solutions

### 1. **Agent Not Found Errors**

#### **Error Message**:
```
Agent type 'monitor-agent' not found. Available agents: general-purpose, tester-agent, task-executor...
```

#### **Root Cause**:
New agents require Claude Code reload to be registered in the system.

#### **Solution**:
```bash
# CRITICAL: Reload Claude Code completely
# New agent definitions in .claude/agents/ are loaded at startup
```

#### **Verification**:
```bash
# After reload, test agent availability
Task(subagent_type="monitor-agent", prompt="Test agent availability")
```

---

### 2. **Context Missing/Incomplete**

#### **Error Symptoms**:
- Agents fail with insufficient information
- Implementation doesn't match requirements
- Compliance attributes missing

#### **Root Cause**:
Subagents operate in isolation - they don't share context automatically.

#### **Solution**:
```bash
# ✅ Always provide complete context
Task(subagent_type="task-executor",
     context="Task Analysis: [COMPLETE RESULTS], Research: [COMPLETE FINDINGS], Dependencies: [VALIDATED], Compliance: GAMP-5 Category 5, ALCOA+ required, 21 CFR Part 11",
     prompt="Implement with provided context")

# ❌ NEVER do this
Task(subagent_type="task-executor", prompt="Implement something")
```

#### **Best Practice**:
```bash
# Context Template
context="
PREVIOUS AGENT RESULTS: [Complete output from previous agent]
COMPLIANCE REQUIREMENTS: GAMP-5, ALCOA+, 21 CFR Part 11
PHARMACEUTICAL FOCUS: Category X system, NO FALLBACKS
DEPENDENCIES: [All validated dependencies]
ERROR CONTEXT: [Any previous failures or issues]
"
```

---

### 3. **Phoenix Observability Failures**

#### **Error Symptoms**:
- monitor-agent fails to access Phoenix
- No traces visible in Phoenix UI
- API endpoints not responding

#### **Diagnostic Commands**:
```bash
# Check Phoenix server status
curl -f http://localhost:6006/health && echo "✅ Phoenix OK" || echo "❌ Phoenix failed"

# Check Phoenix UI accessibility
curl -f http://localhost:6006 && echo "✅ UI accessible" || echo "❌ UI failed"

# Check for traces
curl -s "http://localhost:6006/v1/traces" | head -10
```

#### **Solutions**:

**Phoenix Server Not Running**:
```bash
# Start Phoenix server (adjust command for your setup)
docker run -p 6006:6006 phoenix-server
# OR
phoenix serve --port 6006
```

**Phoenix Running but No Traces**:
```bash
# Check instrumentation in workflow
uv run python main/main.py test_unicode.txt --categorization-only --verbose

# Verify instrumentation logs
grep -i "instrumentation" main/logs/*.log
```

**UI Accessible but Empty**:
```bash
# Generate test traces first
uv run python main/main.py test_unicode.txt --categorization-only

# Then analyze with monitor-agent
Task(subagent_type="monitor-agent",
     context="Phoenix server running, test workflow executed",
     prompt="Analyze Phoenix traces and validate UI accessibility")
```

---

### 4. **Unicode Encoding Crashes**

#### **Error Message**:
```
UnicodeEncodeError: 'charmap' codec can't encode character '\U0001f527' in position X
```

#### **Root Cause**:
Windows console encoding issues with pharmaceutical Unicode characters (🧑‍⚕️✅📋).

#### **Solutions**:

**Environment Variable Fix**:
```bash
# Set UTF-8 environment variable
set PYTHONUTF8=1

# Verify fix
uv run python main/main.py --help
# Should display Unicode characters correctly
```

**System-Level Fix**:
```bash
# Use Windows Terminal instead of Command Prompt
# Or configure system for UTF-8 support
```

#### **Verification**:
```bash
# Test Unicode support
uv run python main/main.py test_unicode.txt --categorization-only
# Should complete without crashes
```

---

### 5. **Fallback Logic Violations**

#### **Error Symptoms**:
- Agents report success with 0% confidence
- Artificial success messages
- Masked error conditions
- "Safe" defaults applied without explicit approval

#### **Detection**:
```bash
# Look for fallback violations in logs
grep -i "fallback\|default\|safe\|masked" main/logs/*.log

# Check for confidence score anomalies
grep -i "confidence.*0\|confidence.*100" main/logs/*.log
```

#### **Solution**:
```bash
# CRITICAL: Agents MUST fail explicitly
# Report actual confidence scores
# Expose real system state
# Require human consultation for low confidence

# Emergency escalation for fallback violations
Task(subagent_type="debugger",
     context="FALLBACK VIOLATION DETECTED: [specific evidence]",
     prompt="Investigate and eliminate fallback logic with complete diagnostic analysis")
```

---

### 6. **Workflow Coordination Failures**

#### **Error Symptoms**:
- Agents execute in wrong sequence
- Missing dependencies not caught
- Context not flowing between agents

#### **Diagnostic**:
```bash
# Check workflow coordinator status
Task(subagent_type="workflow-coordinator",
     prompt="Analyze current coordination status and identify any blocked workflows")
```

#### **Solution**:
```bash
# Use coordinated approach instead of manual
# ❌ Manual (error-prone)
Task(subagent_type="task-executor", ...)

# ✅ Coordinated (recommended)
Task(subagent_type="workflow-coordinator",
     prompt="Execute complete workflow for [specific task]")
```

---

### 7. **Task-Master AI Integration Issues**

#### **Error Symptoms**:
- Cannot retrieve tasks
- Task status updates fail
- Research integration broken

#### **Diagnostic Commands**:
```bash
# Test Task-Master AI connectivity
mcp__task-master-ai__get_tasks --status=pending | head -3

# Check project configuration
mcp__task-master-ai__models --projectRoot="C:\Users\anteb\Desktop\Courses\Projects\thesis_project"
```

#### **Solutions**:

**Connection Issues**:
```bash
# Verify project root is correct
mcp__task-master-ai__get_tasks --projectRoot="[ABSOLUTE_PATH_TO_PROJECT]"

# Check Task-Master AI configuration
ls -la .taskmaster/
```

**Model Configuration**:
```bash
# Verify model configuration
mcp__task-master-ai__models --projectRoot="C:\Users\anteb\Desktop\Courses\Projects\thesis_project"
```

---

### 8. **Compliance Violations**

#### **Error Symptoms**:
- Missing GAMP-5 attributes
- ALCOA+ principles not implemented
- 21 CFR Part 11 audit trail incomplete

#### **Detection**:
```bash
# Check for compliance attributes in traces
curl -s "http://localhost:6006/v1/traces" | grep -i "gamp\|alcoa\|cfr\|compliance"

# Verify audit trail completeness
ls -la main/logs/audit/
```

#### **Solution**:
```bash
# Re-run workflow with explicit compliance requirements
Task(subagent_type="workflow-coordinator",
     context="COMPLIANCE CRITICAL: GAMP-5 Category 5, ALCOA+ all principles, 21 CFR Part 11 full implementation",
     prompt="Re-execute workflow with enhanced compliance validation")

# Follow up with compliance validation
Task(subagent_type="monitor-agent",
     context="Compliance-focused workflow execution completed",
     prompt="Generate comprehensive compliance monitoring report with regulatory evidence")
```

---

## Emergency Escalation Patterns

### **Complex System Issues**
```bash
Task(subagent_type="debugger",
     context="SYSTEM FAILURE: [complete diagnostic context including all agent execution logs, error messages, and system state]",
     prompt="Systematically debug critical system failure with up to 5 iteration attempts and provide architectural recommendations if unresolvable")
```

### **Pharmaceutical Compliance Failures**
```bash
Task(subagent_type="workflow-coordinator",
     context="COMPLIANCE VIOLATION: [specific violation details with evidence]",
     prompt="Escalate compliance issue through proper pharmaceutical quality assurance channels")
```

### **Phoenix Observability Complete Failure**
```bash
# Emergency Phoenix recovery
docker restart phoenix-container  # Adjust for your setup

# Re-run monitoring analysis
Task(subagent_type="monitor-agent",
     context="Phoenix restarted, system recovered",
     prompt="Generate emergency Phoenix recovery report with full diagnostic analysis")
```

---

## Diagnostic Information Collection

### **For All Issues**
```bash
# System state
curl -f http://localhost:6006/health
echo "Python Path: $PYTHONPATH"
echo "Working Directory: $(pwd)"
echo "Environment: $PYTHONUTF8"

# Recent logs
ls -la main/logs/ | tail -10
tail -20 main/logs/*.log

# Agent status
Task(subagent_type="workflow-coordinator",
     prompt="Generate complete system diagnostic report")
```

### **For Phoenix Issues**
```bash
# Phoenix diagnostics
curl -s http://localhost:6006/health
curl -s "http://localhost:6006/v1/traces" | wc -l
docker ps | grep phoenix
netstat -an | grep 6006
```

### **For Compliance Issues**
```bash
# Compliance audit
ls -la main/logs/audit/
grep -r "GAMP\|ALCOA\|CFR" main/logs/
mcp__task-master-ai__complexity_report --projectRoot="C:\Users\anteb\Desktop\Courses\Projects\thesis_project"
```

---

## Prevention Strategies

### **1. Always Use Complete Context**
```bash
# Template for every agent call
Task(subagent_type="[AGENT_NAME]",
     context="
TASK: [Specific task description]
PREVIOUS_RESULTS: [Complete output from previous agents]  
COMPLIANCE: GAMP-5 Category X, ALCOA+ required, 21 CFR Part 11
DEPENDENCIES: [All validated dependencies]
CONSTRAINTS: NO FALLBACKS, explicit error handling only
ERROR_HISTORY: [Any previous failures in this workflow]
     ",
     prompt="[Specific instructions with success criteria]")
```

### **2. Verify Prerequisites**
```bash
# Before any workflow
curl -f http://localhost:6006/health && echo "✅ Phoenix ready"
set PYTHONUTF8=1
uv run python -c "import openai, chromadb; print('✅ Dependencies ready')"
```

### **3. Use Coordinated Workflows**
```bash
# Preferred approach
Task(subagent_type="workflow-coordinator",
     prompt="[Complete task description]")

# Instead of manual coordination
```

### **4. Monitor and Validate**
```bash
# After major workflows
Task(subagent_type="monitor-agent",
     context="[Complete workflow execution context]",
     prompt="Generate comprehensive monitoring validation report")
```

---

**Last Updated**: July 31, 2025  
**Critical Reminder**: NO FALLBACKS - system must fail explicitly with complete diagnostic information for pharmaceutical compliance.