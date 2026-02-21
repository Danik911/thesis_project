# Multi-Agent Pharmaceutical Workflow System - Documentation

**Project**: GAMP-5 Pharmaceutical Test Generation System  
**Version**: 1.2 - MVP Implementation  
**Last Updated**: February 20, 2026  
**Status**: ✅ **Fully Operational** (100% functional with custom span exporter)

## 🏥 **CRITICAL** Documentation Overview

### 🚨 Current System Status

**✅ Working Components** (Verified Aug 5, 2025):
- GAMP-5 Categorization (100% confidence achieved)
- Research Agent with FDA API integration (6 successful calls)
- SME Agent (pharmaceutical expertise)
- OQ Test Generation (30 tests for Category 5)
- Custom span exporter for ChromaDB visibility
- Complete workflow execution (~6 minutes)
- File-based audit logging (412 entries)

**🎯 Key Requirements**:
- **CRITICAL**: API keys MUST be set from .env file
- Use `uv run` to execute (not just `python`)
- Run from `main/` directory
- Expect 5-6 minutes for full workflow

**📝 Important Corrections**:
- `pdfplumber` is already installed (misleading error messages)
- All 3 agents ARE working (100% success rate)
- ChromaDB traces ARE captured via custom span exporter
- Research/SME agents execute but lack OpenTelemetry spans

This documentation suite reflects the current fully functional state of the pharmaceutical multi-agent workflow system.

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

### **5. RAG System Guide** 📊 **RAG & RETRIEVAL**
**File**: [`RAG_SYSTEM_GUIDE.md`](./RAG_SYSTEM_GUIDE.md)
**Purpose**: ChromaDB RAG system documentation for both the thesis pipeline and the AI4LIMS PoC
**Use When**: Troubleshooting RAG retrieval, seeding collections, running evaluations, configuring Langfuse tracing

**Key Sections**:
- Thesis RAG system (regulatory_documents collection, OpenAI embeddings, Docker volume)
- Common issues and solutions (tenant errors, dimension mismatches, empty collections)
- **AI4LIMS RAG System** (new — see below)

#### LIMS RAG Evaluation & Tracing Guide

The AI4LIMS PoC RAG system is documented in `RAG_SYSTEM_GUIDE.md` under the **"AI4LIMS RAG System"** section. Key topics covered:

| Topic | Detail |
|-------|--------|
| Collections | `mda_templates` (325 chunks), `lims_standards` (154 chunks), `calculation_patterns` |
| Chunking | Sheet-level XLSX chunks via `chunking.py` — 13 chunks per XLSX (12 sheets + 1 summary) |
| Langfuse tracing | `@observe` on query functions; `start_span()`/`end()` in pipeline and generator |
| Evaluation metrics | Hit Rate@k, MRR, Precision@k via `rag_evaluator.py` |
| CLI runner | `scripts/evaluate_rag.py` — supports `--sweep`, `--langfuse`, `--collection`, `--top-k` |
| Config | `LIMS_RAG_MDA_TOP_K`, `LIMS_RAG_STANDARDS_TOP_K`, `LIMS_RAG_CHUNK_MAX_SIZE`, `LIMS_RAG_SIMILARITY_THRESHOLD` |

**Key evaluation result** (parameter sweep on `mda_templates`):
`top_k=3` achieves 100% Hit Rate, MRR=0.955 across 11 evaluation queries.

**Quick commands:**
```bash
# Seed mda_templates with sheet-level chunks
uv run python scripts/populate_lims_chroma.py

# Run parameter sweep evaluation
uv run python scripts/evaluate_rag.py --collection mda_templates --sweep --langfuse
```

See `RAG_SYSTEM_GUIDE.md` for the full evaluation results table, all config parameters, and key file inventory.

---

## 🎯 **Quick Start Workflow**

### **For MVP Development** (Current - WORKING):
1. **Set API Key**: Load from .env file (see Quick Start Guide)
2. **Navigate**: `cd main`
3. **Test**: `uv run python main.py tests/test_data/gamp5_test_data/testing_data.md`
4. **Verify**: Full workflow completes in ~6 minutes with all agents

### **For System Testing** (Current Reality - VERIFIED):
1. **Phoenix**: ✅ Custom span exporter captures all traces
2. **Execute**: `uv run python main.py <document>`
3. **Output**: Complete test suite + trace files
4. **Success**: All 3 agents working, ChromaDB traces visible

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
- **Completed**: System verified fully functional with proper setup
- **Next**: Add OpenTelemetry spans for Research/SME agents
- **Future**: Enhance Phoenix integration for better UI visibility

### **Version History**:
- **v1.0** (July 31, 2025): Initial release with 6-agent system
- **v1.1** (August 3, 2025): Incorrectly marked as broken (was actually working)
- **v1.2** (August 5, 2025): Verified fully functional with proper API setup
  - All 3 agents working (100% success rate)
  - Custom span exporter captures ChromaDB traces
  - FDA API integration successful
  - System 100% functional
- **v1.3** (February 20, 2026): Added AI4LIMS RAG documentation
  - New section 5: RAG System Guide covering LIMS RAG evaluation & tracing
  - Sheet-level chunking (325 chunks from 25 XLSX), Langfuse tracing, RAG evaluation framework

### **Recent Fixes** (August 5, 2025):
1. Custom span exporter for ChromaDB visibility
2. Proper API key loading instructions
3. Corrected workflow execution time (5-6 minutes)
4. Updated documentation to reflect actual functionality
5. Fixed monitor-agent to analyze all trace formats

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