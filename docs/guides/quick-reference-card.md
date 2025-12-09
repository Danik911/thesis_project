# Multi-Agent Workflow Quick Reference Card

**🚨 CRITICAL**: NO FALLBACKS ALLOWED - System must fail explicitly with diagnostic information

## Agent Sequence & Usage

### **Standard Workflow** (Copy & Paste Ready)
```bash
# Complete Coordination (Recommended)
Task(subagent_type="workflow-coordinator", 
     prompt="Execute complete pharmaceutical development workflow for [YOUR TASK HERE]")
```

### **Manual Step-by-Step** (Detailed Control)
```bash
# 1. Analysis
Task(subagent_type="task-analyzer", 
     prompt="Analyze requirements for [YOUR TASK]")

# 2. Research (if needed)
Task(subagent_type="context-collector",
     context="[RESULTS FROM STEP 1]",
     prompt="Research GAMP-5 requirements for [YOUR TASK]")

# 3. Implementation
Task(subagent_type="task-executor",
     context="[COMPLETE CONTEXT FROM PREVIOUS STEPS]",
     prompt="Implement [YOUR TASK] with pharmaceutical compliance")

# 4. Testing
Task(subagent_type="tester-agent",
     context="[IMPLEMENTATION DETAILS]",
     prompt="Validate implementation with comprehensive testing")

# 5. End-to-End Testing (Major Features)
Task(subagent_type="end-to-end-tester",
     context="[TESTING RESULTS]",
     prompt="Execute complete pharmaceutical workflow validation")

# 6. Monitoring Analysis (After Testing)
Task(subagent_type="monitor-agent",
     context="[END-TO-END TEST RESULTS]",
     prompt="Analyze Phoenix observability with UI validation and generate monitoring report")
```

## Built-in Commands
```bash
/coordinate next          # Complete workflow for next task
/coordinate [task_id]     # Workflow for specific task
/workflow-status          # Check current status
/escalate [task_id]       # Emergency debugging
```

## Agent Quick Reference

| Agent | Purpose | When to Use | NO FALLBACKS |
|-------|---------|-------------|--------------|
| **task-analyzer** | Initial analysis | ALWAYS start here | ✅ |
| **context-collector** | Research & context | When research needed | ✅ |
| **task-executor** | Implementation | Code/feature work | ✅ |
| **tester-agent** | Quality assurance | Testing & validation | ✅ |
| **end-to-end-tester** | Complete workflow | Major features | ✅ |
| **monitor-agent** | Phoenix analysis | AFTER end-to-end-tester | ✅ |
| **debugger** | Issue resolution | Complex problems | ✅ |

## Pre-Flight Checklist
```bash
# ✅ Phoenix Running
curl -f http://localhost:6006 && echo "✅ Phoenix ready"

# ✅ UTF-8 Support (Windows)
set PYTHONUTF8=1

# ✅ Dependencies
uv run python -c "import openai; print('✅ OpenAI ready')"
```

## **CRITICAL** Context Rules

### ✅ **DO**
- Always provide complete context from previous agents
- Include pharmaceutical compliance requirements
- Specify GAMP-5, ALCOA+, 21 CFR Part 11 requirements
- Let agents fail explicitly with full diagnostic information

### ❌ **DON'T**  
- Skip context between agents
- Allow fallback behaviors or artificial success
- Mask errors or hide system failures
- Use agents without understanding their outputs

## Emergency Patterns

### **Issue Resolution**
```bash
Task(subagent_type="debugger",
     context="[COMPLETE FAILURE CONTEXT]",
     prompt="Systematically debug [SPECIFIC ISSUE] with full root cause analysis")
```

### **Phoenix Not Working**
```bash
# Check Phoenix
curl -f http://localhost:6006/health

# Restart if needed
docker restart phoenix  # or your Phoenix startup command
```

### **Agent Not Found**
```bash
# Solution: Reload Claude Code
# New agents require system restart to be recognized
```

## Monitoring & Reports

### **Phoenix Analysis**
```bash
# After any major workflow
Task(subagent_type="monitor-agent",
     context="[WORKFLOW RESULTS WITH TIMESTAMPS]",
     prompt="Analyze Phoenix traces and generate compliance monitoring report")
```

### **Report Locations**
```
main/docs/reports/monitoring/    # Phoenix analysis reports
main/docs/reports/               # All workflow reports  
main/logs/                       # System execution logs
```

## **PHARMACEUTICAL COMPLIANCE**

### **Required Every Time**
- **GAMP-5**: Category determination with confidence scoring
- **ALCOA+**: All 9 data integrity principles
- **21 CFR Part 11**: Electronic records and audit trails
- **NO FALLBACKS**: Explicit error handling only

### **Success Criteria**
- ✅ Complete context flow between agents
- ✅ Pharmaceutical compliance maintained
- ✅ Audit trail completeness  
- ✅ Phoenix observability functional
- ✅ NO artificial success reporting

---

**🎯 Remember**: Each agent operates in isolation. YOU are responsible for context flow and coordination success.

**📞 Help**: See `multi-agent-workflow-guide.md` for complete documentation.