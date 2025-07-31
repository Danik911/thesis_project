# Quick Start Guide - Current System Status

⚠️ **MVP Status**: Basic workflow available, full features under development

## 🚀 Current System (3 Steps)

### Step 1: Start Phoenix (Docker)
```bash
docker run -d -p 6006:6006 --name phoenix-observability arizephoenix/phoenix:latest
```

### Step 2: Run Current Workflow
```bash
# Execute basic workflow
cd main
python main.py
2. Data integrity (ALCOA+ compliance)
3. Audit trail logging
4. Electronic signatures

Testing Requirements:
- Validation testing required
- Performance testing required
- Security testing required
EOF
```

### Step 3: Launch the End-to-End Workflow
```bash
uv run python main/main.py my_urs.txt --verbose
```

## ✅ Expected Results

### Console Output:
```
🏥 GAMP-5 Pharmaceutical Test Generation System
🚀 Running Unified Test Generation Workflow
============================================================
📊 Setting up event logging system...
✅ Connected to existing Phoenix instance at: http://localhost:6006
🔭 OpenTelemetry Tracing Details 🔭
|  Phoenix Project: test_generation_thesis
|  Collector Endpoint: http://localhost:6006/v1/traces

✅ Unified Test Generation Complete!
  - Status: Completed Successfully
  - Duration: ~20s
  - GAMP Category: 5
  - Estimated Tests: 65
  - Timeline: 195 days
  - Active Agents: 2 (Categorization + Planner)
  - Parallel Agents: Not integrated (coordination requests generated only)
```

### Phoenix UI:
- **URL**: http://localhost:6006
- **Project**: test_generation_thesis
- **Traces**: Full workflow execution visible

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
  ├── ✅ Planner Agent (ACTIVE) 
  │   ├── Generates test strategies
  │   └── Creates coordination requests for parallel agents
  └── ❌ Parallel Agents (CODE EXISTS BUT NOT INTEGRATED)
      ├── Research Agent (regulatory updates, not executed)
      ├── SME Agent (domain expertise, not executed)
      └── Context Provider Agent (RAG/CAG with ChromaDB + Phoenix, not executed)
```

### 🚨 **Important: Current Agent Status**

**ACTIVE AGENTS (2):**
- **Categorization Agent**: ✅ Fully integrated and executed
- **Planner Agent**: ✅ Fully integrated and executed

**PHANTOM AGENTS (3):**
- **Research Agent**: ❌ Code exists in `/agents/parallel/research_agent.py` but NOT executed
- **SME Agent**: ❌ Code exists in `/agents/parallel/sme_agent.py` but NOT executed  
- **Context Provider**: ✅ Code exists in `/agents/parallel/context_provider.py` with **ChromaDB integration and Phoenix observability** but NOT executed in main workflow

**Agent Status Now Shows Reality:**
- **Active Agents: 2** - Only these agents actually execute (Categorization + Planner)
- **Parallel Agents: Not integrated** - Code exists but agents are not executed
- No more misleading "Agent Success Rate: 100.0%" 
- Coordination requests are generated but no longer falsely reported as successful execution

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

- **✅ Working**: GAMP-5 categorization and test planning
- **✅ Working**: Phoenix observability for active agents
- **⚠️ Misleading**: Agent coordination statistics  
- **❌ Missing**: Actual parallel agent execution
- **📈 Potential**: 3 additional agents ready for integration

**Current system provides solid foundation with 2 active agents and framework for 3 more.**