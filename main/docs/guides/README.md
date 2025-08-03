# Multi-Agent Pharmaceutical Workflow System - Documentation

**Project**: GAMP-5 Pharmaceutical Test Generation System  
**Version**: 1.1 - MVP Implementation  
**Last Updated**: August 3, 2025  
**Status**: ⚠️ **Partially Operational** (~75% functional)

## 🏥 **CRITICAL** Documentation Overview

### 🚨 Current System Status

**✅ Working Components**:
- GAMP-5 Categorization (confidence threshold 0.4)
- OQ Test Generation with o3 model (30 tests for Category 5)
- Basic file-based audit logging
- Test suite JSON file generation

**❌ Non-functional Components**:
- Phoenix observability (missing arize-phoenix packages)
- Research Agent (requires pdfplumber)
- SME Agent (requires pdfplumber)
- Complete workflow tracing
- Audit trail details (shows "unknown")

**🔧 To Restore Full Functionality**:
```bash
pip install pdfplumber
pip install arize-phoenix
pip install openinference-instrumentation-llama-index
pip install openinference-instrumentation-openai
pip install llama-index-callbacks-arize-phoenix
```

This documentation suite reflects the current partially functional state of the pharmaceutical multi-agent workflow system.

## 🚨 **ABSOLUTE RULE: NO FUCKING FALLBACKS** 🚨

All system components follow **ZERO TOLERANCE FOR FALLBACK LOGIC**:
- ❌ NEVER mask errors or hide system failures
- ✅ ALWAYS fail explicitly with complete diagnostic information
- ✅ ALWAYS preserve genuine confidence levels and uncertainties
- ✅ ALWAYS expose real system state for regulatory compliance

---

## 📚 Documentation Suite

### **1. MVP Implementation Plan** ⭐ **ESSENTIAL**
**File**: [`mvp_implementation_plan.md`](../mvp_implementation_plan.md)  
**Purpose**: Complete MVP roadmap with 9 tasks, timeline, and technical details  
**Use When**: Understanding current development status, implementation priorities, daily task planning  

**Key Sections**:
- 9 Task breakdown with dependencies
- Phase-based implementation (5-7 days)
- Technical architecture decisions
- Success metrics and risk mitigation

---

### **2. Multi-Agent Workflow Guide** 📖 **REFERENCE**
**File**: `multi-agent-workflow-guide.md`  
**Purpose**: Legacy system documentation (being transitioned to MVP)  
**Use When**: Understanding completed components, future architecture reference  

**Key Sections**:
- System Architecture & Agent Descriptions
- Phoenix Observability Integration
- Pharmaceutical Compliance Requirements

---

### **3. Quick Start Guide** 🚀 **DAILY USE**
**File**: `QUICK_START_GUIDE.md`  
**Purpose**: Current workflow execution with unified system  
**Use When**: Running current implementation, testing basic functionality  

**Key Features**:
- Basic workflow execution (`python main/main.py`)
- Phoenix monitoring setup
- Current system capabilities

---

### **4. Phoenix Observability Guide** 🔍 **MONITORING**
**File**: `PHOENIX_OBSERVABILITY_GUIDE.md`  
**Purpose**: Monitoring and trace analysis for compliance  
**Use When**: Setting up monitoring, validating system behavior, audit preparation  

**Key Sections**:
- Phoenix setup and configuration
- Trace analysis patterns
- Compliance monitoring requirements

---

## 🎯 **Quick Start Workflow**

### **For MVP Development** (Current):
1. **Read**: Current system status at top of this document
2. **Install**: Missing dependencies listed above
3. **Test**: `uv run python main/main.py test_urs.txt`
4. **Verify**: Check if test file generated with 30 OQ tests

### **For System Testing** (Current Reality):
1. **Phoenix**: ❌ NOT WORKING (GraphQL errors even if running)
2. **Execute**: `uv run python main/main.py test_urs.txt`
3. **Output**: Test JSON file generated successfully
4. **Issues**: No observability, 2 of 3 agents fail

---

## 🤖 **Agent Integration Summary**

### **Complete Workflow Sequence**:
```
task-analyzer → context-collector → task-executor → tester-agent → end-to-end-tester → monitor-agent
```

### **6 Specialized Agents**:
1. **task-analyzer**: Initial analysis & dependency validation
2. **context-collector**: Research & pharmaceutical context gathering
3. **task-executor**: Implementation with compliance (NO FALLBACKS)
4. **tester-agent**: Quality assurance & validation (NO FALLBACKS)
5. **end-to-end-tester**: Complete workflow validation
6. **monitor-agent**: Phoenix observability & UI analysis (NEW with Puppeteer)

### **Coordination Options**:
```bash
# Recommended: Complete coordination
Task(subagent_type="workflow-coordinator", prompt="...")

# Manual: Step-by-step control
Task(subagent_type="task-analyzer", prompt="...")
```

---

## 📊 **Phoenix Observability Integration**

### ❌ **CURRENTLY NON-FUNCTIONAL**

Phoenix monitoring is broken due to missing dependencies. When working, it would provide:

- **Phoenix UI Analysis**: Currently returns GraphQL errors
- **Screenshot Evidence**: Not available
- **API Cross-Validation**: No traces to validate
- **Performance Monitoring**: Only 3 embedding calls captured
- **Compliance Validation**: Audit trail shows "unknown"

### **To Fix Phoenix**:
```bash
# Install all missing packages first
pip install arize-phoenix openinference-instrumentation-llama-index openinference-instrumentation-openai llama-index-callbacks-arize-phoenix
```

---

## 🏥 **Pharmaceutical Compliance**

### **Always Required**:
- **GAMP-5**: Category determination with explicit confidence
- **ALCOA+**: All 9 data integrity principles 
- **21 CFR Part 11**: Electronic records & audit trails
- **NO FALLBACKS**: Explicit error handling only

### **Success Criteria**:
- ✅ Complete context flow between agents
- ✅ Pharmaceutical compliance maintained throughout
- ✅ Phoenix observability functional with UI validation
- ✅ Audit trail completeness for regulatory inspection
- ✅ NO artificial success reporting or masked failures

---

## 🔗 **Related Resources**

### **Project Files**:
```
.claude/agents/                    # Agent definitions
main/docs/reports/                 # Generated workflow reports
main/docs/reports/monitoring/      # Phoenix analysis reports
main/logs/                        # System execution logs
CLAUDE.md                         # Core system instructions
```

### **Commands**:
```bash
/coordinate next                  # Complete workflow coordination
/workflow-status                  # Quick status check
/escalate [issue]                # Emergency debugging
```

### **External Documentation**:
- [Claude Code Subagents](https://docs.anthropic.com/en/docs/claude-code/sub-agents)
- [Task-Master AI](https://github.com/eyaltoledano/claude-task-master)
- [Phoenix Observability](https://arize.com/docs/phoenix)

---

## 📋 **Document Maintenance**

### **Update Schedule**:
- **Immediate**: Install missing dependencies to restore functionality
- **Critical**: Fix audit trail to show actual workflow steps
- **Next**: Restore Phoenix observability for compliance

### **Version History**:
- **v1.0** (July 31, 2025): Initial release with 6-agent system
- **v1.1** (August 3, 2025): Updated to reflect current broken state
  - Phoenix non-functional
  - 2 of 3 agents fail
  - Audit trail incomplete
  - System ~75% functional

### **Recent Fixes** (August 3, 2025):
1. Configuration alignment (Category 5: 25-30 tests)
2. JSON datetime serialization
3. Phantom success status reporting
4. o3-2025-04-16 model integration
5. Confidence threshold reduced to 0.4

---

## 🆘 **Emergency Contacts**

### **System Issues**:
```bash
# Complex debugging
Task(subagent_type="debugger", context="[COMPLETE DIAGNOSTIC]", prompt="...")

# Workflow coordination failures
Task(subagent_type="workflow-coordinator", prompt="Analyze coordination status")
```

### **Compliance Issues**:
```bash
# Compliance violations
Task(subagent_type="monitor-agent", prompt="Generate compliance violation report")

# Regulatory audit preparation
Task(subagent_type="end-to-end-tester", prompt="Execute compliance validation workflow")
```

---

**🎯 Remember**: This multi-agent system prioritizes **pharmaceutical compliance over speed**, **complete context sharing over efficiency**, and **systematic coordination over ad-hoc delegation**. Every decision impacts patient safety and regulatory compliance.

**📞 Support**: For issues not covered in troubleshooting guide, use the debugger agent with complete diagnostic context.