# Phoenix Monitoring with MCP Integration Guide

> **Last Updated**: August 3, 2025  
> **Status**: ❌ Phoenix Monitoring is currently **NON-FUNCTIONAL**

## 🚨 CRITICAL STATUS UPDATE

Phoenix observability is currently broken due to missing dependencies. This guide documents the intended functionality, but **NONE of these features are currently working**.

### Current Issues:
1. **Missing Phoenix Packages**:
   ```
   arize-phoenix
   openinference-instrumentation-llama-index
   openinference-instrumentation-openai
   llama-index-callbacks-arize-phoenix
   ```

2. **GraphQL API Error**: "unexpected error occurred"
3. **No Workflow Traces**: Only 3 OpenAI embedding calls captured
4. **Complete Observability Blackout**: Zero visibility into workflow execution

### To Restore Functionality:
```bash
# Install required packages
pip install arize-phoenix
pip install openinference-instrumentation-llama-index
pip install openinference-instrumentation-openai
pip install llama-index-callbacks-arize-phoenix
```

---

## 🎯 Overview (When Working)

This guide demonstrates how to access and monitor Phoenix traces for the pharmaceutical test generation workflow using programmatic access instead of browser automation MCP tools.

**Key Achievement**: Successfully established Phoenix monitoring without browser dependencies, providing robust trace analysis for GAMP-5 compliance.

## 🚀 Setup Summary

### Expected Configuration (Not Currently Functional)
- **Phoenix Server**: Should run on `localhost:6006` (Docker or Python)
- **Phoenix Client**: Version compatibility required
- **MCP Integration**: Available but not required for monitoring
- **Trace Access**: Programmatic via Phoenix Python client

### Browser MCP Status
- **Playwright MCP**: Available but requires `sudo npx playwright install chrome`
- **Puppeteer MCP**: Available but has dependency issues in WSL environment
- **Alternative**: Direct Phoenix client access (recommended when working)

## 📊 Phoenix Monitoring Script

### Installation Location
```
/home/anteb/thesis_project/main/phoenix_monitoring.py
```

### Core Features (When Functional)
1. **Real-time trace analysis** with comprehensive breakdowns
2. **Workflow execution tracking** for GAMP categorization
3. **Performance metrics** and latency analysis
4. **Export functionality** for compliance reporting
5. **Real-time monitoring** with configurable intervals

### Usage Examples (Currently Non-Functional)

#### 1. Get Trace Summary
```bash
uv run python main/phoenix_monitoring.py --summary --hours 1
```

**Expected Output** (Not Available):
```json
{
  "phoenix_url": "http://localhost:6006",
  "total_spans": 176,
  "recent_spans": 7,
  "workflow_traces": {
    "gamp_workflow_spans": 7,
    "workflow_operations": {
      "GAMPCategorizationWorkflow.start": 1,
      "GAMPCategorizationWorkflow.process_document": 1,
      "GAMPCategorizationWorkflow.categorize_document": 1,
      "GAMPCategorizationWorkflow.handle_error_recovery": 1,
      "GAMPCategorizationWorkflow.check_consultation_required": 1,
      "GAMPCategorizationWorkflow.complete_workflow": 1,
      "GAMPCategorizationWorkflow._done": 1
    }
  }
}
```

## 🔍 What Should Be Captured (Currently Missing)

### Workflow Traces
- `GAMPCategorizationWorkflow.*` operations
- `UnifiedTestGenerationWorkflow.*` operations
- `OQTestGenerationWorkflow.*` operations
- Agent coordination events
- Error handling and recovery

### Current Reality
- **Only 3 traces**: OpenAI embedding calls
- **No workflow visibility**
- **No agent traces**
- **No error tracking**

## 🌐 Phoenix UI Access

### Current Status
```
http://localhost:6006 - Returns GraphQL errors
```

### What's Broken:
- Trace visualization
- Span hierarchy analysis
- Performance metrics
- Token usage tracking
- Export capabilities

## 🔧 Troubleshooting

### Primary Issue: Missing Dependencies
The root cause is missing Python packages. Without these, Phoenix cannot instrument the LlamaIndex workflows.

### Steps to Fix:
1. Install missing packages (see top of document)
2. Restart Phoenix server
3. Re-run workflow with instrumentation enabled
4. Verify traces appear in Phoenix UI

## 📈 Integration with Pharmaceutical Workflow

### Current Impact on Compliance
⚠️ **CRITICAL**: Without Phoenix monitoring, we have:
- **No audit trail** of workflow execution details
- **No performance metrics** for validation
- **No error tracking** for debugging
- **Limited compliance documentation**

### What Should Work (But Doesn't):
```bash
# Before running workflow
uv run python main/phoenix_monitoring.py --export pre_workflow_baseline.json

# Run pharmaceutical workflow
uv run python main/main.py test_document.txt

# Analyze workflow traces
uv run python main/phoenix_monitoring.py --summary --hours 1

# Export final report
uv run python main/phoenix_monitoring.py --export post_workflow_traces.json
```

## 🎯 Key Benefits (Currently Unavailable)

### ❌ No Browser Dependencies
- Would eliminate MCP browser setup complexity
- Would work in WSL, Docker, and restricted environments
- No `sudo` permissions required for monitoring

### ❌ Comprehensive Trace Access
- Should capture hundreds of spans across workflow executions
- Real-time monitoring capabilities missing
- Export functionality non-operational

### ❌ Pharmaceutical Compliance
- Cannot capture GAMP-5 workflow traces
- No error handling documentation
- Missing audit trail for regulatory requirements

### ❌ Performance Insights
- No latency tracking
- No operation breakdown analysis
- No historical trend monitoring

## 📚 Resources for Fixing

### Required Actions:
1. **Install Dependencies**:
   ```bash
   pip install arize-phoenix
   pip install openinference-instrumentation-llama-index
   pip install openinference-instrumentation-openai
   pip install llama-index-callbacks-arize-phoenix
   ```

2. **Verify Phoenix Server**:
   ```bash
   docker ps | grep phoenix
   # or
   ps aux | grep phoenix
   ```

3. **Check Instrumentation**:
   ```python
   # In main.py or workflow files
   from phoenix.otel import register
   tracer_provider = register()
   ```

### Documentation:
- **Phoenix Documentation**: https://arize.com/docs/phoenix
- **OpenInference**: https://github.com/Arize-ai/openinference
- **LlamaIndex Integration**: https://docs.llamaindex.ai/en/stable/module_guides/observability/

---

**Status**: ❌ Phoenix monitoring is **NON-FUNCTIONAL**  
**Root Cause**: Missing Python dependencies  
**Resolution**: Install required packages and restart services  
**Impact**: Complete observability blackout affecting compliance and debugging capabilities