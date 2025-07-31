# Multi-Agent Pharmaceutical Workflow System - Documentation

**Project**: GAMP-5 Pharmaceutical Test Generation System  
**Version**: 1.1 - MVP Implementation  
**Last Updated**: July 31, 2025  
**Status**: ⚠️ **Under Active Development** - MVP in progress

## 🏥 **CRITICAL** Documentation Overview

⚠️ **Current Status**: MVP implementation focusing on OQ test generation with 9 critical tasks.

This documentation suite provides guidance for the pharmaceutical multi-agent workflow system transitioning from legacy implementation to **MVP architecture** with **Phoenix observability** and **regulatory compliance** (GAMP-5, ALCOA+, 21 CFR Part 11).

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
1. **Read**: [`mvp_implementation_plan.md`](../mvp_implementation_plan.md) (Current priorities)
2. **Execute**: `mcp__task-master-ai__next_task` (Get next MVP task)
3. **Implement**: Focus on Task 1 (categorization agent fixes) first
4. **Test**: Use `main/tests/test_data/gamp5_test_data/testing_data.md`

### **For System Testing** (Current capabilities):
1. **Setup**: `python -m phoenix.server.main serve &`
2. **Execute**: `python main/main.py`
3. **Monitor**: Check Phoenix UI at http://localhost:6006
4. **Validate**: Basic workflow execution and event logging

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

### **Monitor-Agent Features** (NEW):
- **Phoenix UI Analysis**: Puppeteer-based interaction
- **Screenshot Evidence**: Visual validation for regulatory compliance
- **API Cross-Validation**: UI vs API data consistency
- **Performance Monitoring**: Response times & trace collection efficiency
- **Compliance Validation**: GAMP-5, ALCOA+, 21 CFR Part 11 attributes

### **Usage Pattern**:
```bash
# 1. Execute workflow
Task(subagent_type="end-to-end-tester", prompt="...")

# 2. Analyze observability  
Task(subagent_type="monitor-agent", context="[test results]", prompt="...")
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
- **Weekly**: Quick reference commands and troubleshooting patterns
- **Monthly**: Agent descriptions and workflow sequences  
- **Quarterly**: Compliance requirements and regulatory updates

### **Version History**:
- **v1.0** (July 31, 2025): Initial release with 6-agent system and monitor-agent integration
- **Next**: Enhanced Puppeteer capabilities and additional compliance validations

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