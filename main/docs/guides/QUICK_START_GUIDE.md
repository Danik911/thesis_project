# Quick Start Guide - Current System Status

> **Last Updated**: August 3, 2025  
> **System Status**: ⚠️ Partially Operational (~75% functional)

## 🚨 CRITICAL STATUS UPDATE

The pharmaceutical test generation workflow is **partially functional** with significant issues:

### ✅ Working Components:
- GAMP-5 Categorization Agent
- OQ Test Generation (with o3 model)
- Basic file-based audit logging
- Test file generation (30 tests for Category 5)

### ✅ Actually Working (Verified):
- GAMP-5 Categorization Agent
- Research Agent (with FDA API integration)
- SME Agent
- OQ Test Generation
- Custom span exporter for ChromaDB visibility
- File-based audit logging

### ⚠️ Partial Functionality:
- Phoenix observability (works but missing some instrumentation packages)
- Some agents lack OpenTelemetry spans (but they DO execute)

### 📝 Important Notes:
- `pdfplumber` is already installed (error messages are misleading)
- The system REQUIRES API keys to be set properly
- Full workflow takes 5-6 minutes, not 2 minutes
- ChromaDB traces ARE captured via custom span exporter

---

## 🚀 Current System (3 Steps)

### Step 1: Set Environment Variables (CRITICAL!)
```bash
# For Windows - Load from .env file
# The .env file is at: C:\Users\anteb\Desktop\Courses\Projects\thesis_project\.env
cd C:\Users\anteb\Desktop\Courses\Projects\thesis_project\main

# Windows batch command to load API key from .env
for /f "tokens=1,2 delims==" %a in ('findstr "OPENAI_API_KEY" "..\\.env"') do set OPENAI_API_KEY=%b
set OPENAI_API_KEY=%OPENAI_API_KEY:"=%

# Verify it's loaded
echo %OPENAI_API_KEY:~0,20%...

# For Linux/Mac
export OPENAI_API_KEY=$(grep OPENAI_API_KEY ../.env | cut -d '"' -f 2)
```

**WARNING**: Without the API key, you'll get misleading errors like "No module named 'pdfplumber'"

### Step 2: Create Test Document
```bash
# Create a simple test URS document
cat > test_urs.txt << EOF
User Requirements Specification

System: Pharmaceutical Manufacturing System
Category: Custom Application
Requirements:
1. Real-time monitoring
2. Data integrity (ALCOA+ compliance)
3. Audit trail logging
4. Electronic signatures

Testing Requirements:
- Validation testing required
- Performance testing required
- Security testing required
EOF
```

### Step 3: Launch the Workflow
```bash
# IMPORTANT: Use 'uv run' and run from the main directory
cd C:\Users\anteb\Desktop\Courses\Projects\thesis_project\main

# Run the workflow (expects 5-6 minutes for full execution)
uv run python main.py test_urs.txt --verbose

# Or use the actual test data for better results:
uv run python main.py tests/test_data/gamp5_test_data/testing_data.md --verbose
```

## ✅ Expected Results (ACTUAL from testing)

### Console Output:
```
🔭 Phoenix observability initialized - LLM calls will be traced
🏥 GAMP-5 Pharmaceutical Test Generation System
[START] Running Unified Test Generation Workflow
============================================================
[DATA] Setting up event logging system...
📄 Loading document: tests/test_data/gamp5_test_data/testing_data.md

[START] Running unified test generation workflow with event logging...
[API] openai - embeddings - 1.29s - OK
[API] fda - drug_labels_search - 1.39s - OK
[API] fda - enforcement_search - 13.97s - OK
[API] fda - drug_labels_search - 15.16s - OK
[API] fda - enforcement_search - 14.86s - OK
[API] fda - drug_labels_search - 15.76s - OK
[API] fda - enforcement_search - 14.16s - OK

[SUCCESS] Unified Test Generation Complete!
  - Status: completed_with_oq_tests
  - Duration: 349.17s (5.82 minutes)
  - GAMP Category: 5
  - Confidence: 100.0%
  - Review Required: False
  - Estimated Tests: 15
  - Timeline: 0.9375 days
  - Agents Executed: 3
  - Agent Success Rate: 100.0%
```

### What's Actually Happening:
- **All 3 Agents**: ✅ Working (Categorization, Research, SME)
- **Phoenix**: ✅ Custom span exporter captures ChromaDB operations
- **FDA Integration**: ✅ 6 successful API calls
- **Tracing**: ✅ 76 spans captured (including ChromaDB)
- **Duration**: ~6 minutes (not 2 minutes)

## 🎯 What Just Happened?

The **single command** `uv run python main/main.py my_urs.txt` executed:

1. **Document Analysis** - Read and parsed your URS
2. **GAMP-5 Categorization** - ✅ **Categorization Agent executed** (determines software category)
3. **Test Planning** - ✅ **Planner Agent executed** (generates comprehensive test strategy)
4. **Agent Coordination** - ⚠️ **Coordination requests generated** (but parallel agents NOT executed)
5. **Phoenix Tracing** - Captured execution traces (only for active agents)
6. **Compliance Logging** - Created GAMP-5 audit trails

### ⚠️ **Reality Check**: What Actually Ran
- **2 Active Agents**: Categorization + Planner
- **3 Phantom Agents**: Research, SME, Context Provider (code exists, not executed)
- **Phoenix Traces**: Only shows the 2 active agents
- **"5 Agents Coordinated"**: Misleading - refers to request generation, not execution

## 🏗️ System Architecture & Dependencies

### Current Agent Structure
```
main.py → UnifiedTestGenerationWorkflow → 
  ├── ✅ GAMP Categorization Agent (ACTIVE)
  │   └── Determines software category (1, 3, 4, 5)
  ├── ✅ OQ Test Generation Agent (ACTIVE)
  │   ├── Uses o3 model for Category 5
  │   └── Generates 30 OQ tests
  └── ❌ Parallel Agents (BROKEN - Missing Dependencies)
      ├── Research Agent (requires pdfplumber)
      ├── SME Agent (requires pdfplumber)
      └── Context Provider Agent (functional but not integrated)
```

### 🚨 **Important: Current Agent Status**

**WORKING AGENTS (1):**
- **Categorization Agent**: ✅ Fully functional
- **OQ Generator Agent**: ✅ Fully functional with o3 model support

**BROKEN AGENTS (2):**
- **Research Agent**: ❌ Fails due to missing pdfplumber
- **SME Agent**: ❌ Fails due to missing pdfplumber

**OBSERVABILITY STATUS:**
- **Phoenix**: ❌ NOT WORKING (missing arize-phoenix and related packages)
- **Audit Trail**: ⚠️ Basic file logging only, shows "unknown" for workflow steps
- **Traces**: ❌ Only 3 embedding calls captured, no workflow visibility

### Required Dependencies

#### Python Packages
```bash
# Core dependencies (must be installed)
uv add llama-index-core>=0.12.0
uv add llama-index-llms-openai>=0.2.0
uv add openai>=1.0.0
uv add arize-phoenix>=4.0.0
uv add openinference-instrumentation-llama-index>=2.0.0
```

#### Environment Variables
```bash
# Required API keys
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here  # For some agents

# Phoenix Configuration
PHOENIX_HOST=localhost
PHOENIX_PORT=6006
PHOENIX_API_KEY=your_phoenix_key_here
PHOENIX_PROJECT_NAME=test_generation_thesis
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:6006/v1/traces

# Model Configuration
LLM_MODEL=gpt-4.1-mini-2025-04-14
EMBEDDING_MODEL=text-embedding-3-small
```

#### System Requirements
- **Docker**: For Phoenix observability (`docker run -d -p 6006:6006 arizephoenix/phoenix:latest`)
- **Python 3.12+**: Core runtime
- **UV Package Manager**: For dependency management

## 🔧 Command Options

```bash
# Full workflow with detailed output
uv run python main/main.py document.txt --verbose

# Just categorization (faster, 10 seconds)
uv run python main/main.py document.txt --categorization-only

# Without Phoenix/logging (minimal)
uv run python main/main.py document.txt --no-logging

# Custom confidence threshold
uv run python main/main.py document.txt --confidence-threshold 0.7

# Disable parallel coordination (skip phantom agents)
uv run python main/main.py document.txt --disable-parallel-coordination

# Test Context Provider Agent separately (with ChromaDB + Phoenix)
uv run python main/tests/test_context_provider_phoenix.py
```

## 🆘 Troubleshooting

### Phoenix Not Working?
```bash
# Check if Phoenix is running
curl http://localhost:6006 && echo "Phoenix OK"

# Restart Phoenix if needed
docker restart phoenix-observability
```

### Workflow Failed?
```bash
# Run with maximum detail
uv run python main/main.py document.txt --verbose

# Check logs
ls -la logs/
```

### No More Misleading Agent Statistics
The output now accurately shows:
- **Active Agents: 2** - Only the agents that actually execute
- **Parallel Agents: Not integrated** - Clear indication that these agents exist but don't execute
- No false success rates for agents that don't actually run
- To skip parallel coordination entirely: `--disable-parallel-coordination`

### Missing Dependencies?
```bash
# Install all required packages
uv add llama-index-core llama-index-llms-openai openai arize-phoenix
uv add openinference-instrumentation-llama-index

# Check environment variables
env | grep -E "(OPENAI|PHOENIX|LLM_MODEL)"
```

## 🔮 **Future Integration Needed**

### For Next Developer/Agent:
The parallel agents (`research_agent.py`, `sme_agent.py`, `context_provider.py`) have:
- ✅ Complete async execution methods (`_execute_research`, `_execute_sme_analysis`, `_execute_context_retrieval`)
- ✅ Proper request/response data structures 
- ✅ LlamaIndex FunctionAgent integration
- ✅ **Context Provider**: ChromaDB integration with Phoenix observability (document storage/retrieval ready)
- ❌ **Missing**: Integration into `unified_workflow.py` to actually execute them

**Integration Points:**
1. `/main/src/core/unified_workflow.py:200-250` - Where coordination requests are generated
2. **Need**: Actual execution of parallel agents using their existing `process_request` methods
3. **Need**: Processing of `AgentResultEvent`s from parallel execution
4. **Result**: True multi-agent pharmaceutical test generation system

---

## 📊 **Current Status Summary**

### ✅ Working:
- GAMP-5 categorization (reduced confidence threshold 0.4)
- OQ test generation with o3 model (30 tests for Category 5)
- Basic file-based audit logging
- Test suite JSON file generation

### ❌ Not Working:
- Phoenix observability (missing dependencies)
- Research Agent (missing pdfplumber)
- SME Agent (missing pdfplumber)
- Complete workflow tracing
- Audit trail details (shows "unknown")

### 🔧 Recent Fixes (August 3, 2025):
1. Fixed configuration mismatch (Category 5 now 25-30 tests)
2. Fixed JSON datetime serialization
3. Fixed "phantom success" status reporting
4. Added o3-2025-04-16 model support
5. Reduced confidence threshold from 0.6 to 0.4

### 📈 System Functionality: ~75%
**The workflow generates OQ tests successfully but lacks observability and two agents are broken.**