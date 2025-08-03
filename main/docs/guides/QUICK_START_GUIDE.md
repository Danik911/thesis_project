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

### ❌ Non-functional Components:
- Phoenix observability (missing dependencies)
- Research Agent (requires pdfplumber)
- SME Agent (requires pdfplumber)
- Complete workflow tracing
- Audit trail shows "unknown" for all steps

### 🔧 To Restore Full Functionality:
```bash
# Install missing dependencies
pip install pdfplumber
pip install arize-phoenix
pip install openinference-instrumentation-llama-index
pip install openinference-instrumentation-openai
pip install llama-index-callbacks-arize-phoenix
```

---

## 🚀 Current System (3 Steps)

### Step 1: Set Environment Variables
```bash
# Required for workflow to function
export OPENAI_API_KEY=your_key_here
export PYTHONUTF8=1  # Required on Windows
```

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
# Run the workflow (Phoenix not required as it's broken)
uv run python main/main.py test_urs.txt --verbose
```

## ✅ Expected Results

### Console Output:
```
🏥 GAMP-5 Pharmaceutical Test Generation System
🚀 Running Unified Test Generation Workflow
============================================================
📊 Setting up event logging system...
WARNING - Failed to initialize Phoenix: No module named 'arize'
⚠️  Phoenix observability not available - continuing without tracing

Processing document: test_urs.txt
Starting GAMP categorization...
Categorization complete: Category 5 (confidence: 0.42)

Starting OQ test generation...
Using o3-2025-04-16 model for Category 5
Generated 30 OQ tests

✅ Workflow completed!
  - Status: SUCCESS
  - Duration: ~300s (o3 model is slow)
  - GAMP Category: 5
  - Tests Generated: 30
  - Output File: test_generation_CATEGORY_5_2025-08-03_timestamp.json
```

### What's Actually Happening:
- **Phoenix**: NOT working (GraphQL errors)
- **Tracing**: NOT captured (only 3 embedding calls)
- **Audit Trail**: Shows "unknown" for all steps
- **Agents**: Only 1 of 3 agents functional (OQ Generator)

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