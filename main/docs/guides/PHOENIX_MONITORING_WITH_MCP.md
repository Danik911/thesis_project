# Phoenix Monitoring with MCP Integration Guide

## 🎯 Overview

This guide demonstrates how to access and monitor Phoenix traces for the pharmaceutical test generation workflow using programmatic access instead of browser automation MCP tools.

**Key Achievement**: Successfully established Phoenix monitoring without browser dependencies, providing robust trace analysis for GAMP-5 compliance.

## 🚀 Setup Summary

### Current Configuration
- **Phoenix Server**: Running on `localhost:6006` (Docker or Python)
- **Phoenix Client**: Version 11.10.1 (compatible with server 11.13.2)
- **MCP Integration**: Available but not required for monitoring
- **Trace Access**: Programmatic via Phoenix Python client

### Browser MCP Status
- **Playwright MCP**: Available but requires `sudo npx playwright install chrome`
- **Puppeteer MCP**: Available but has dependency issues in WSL environment
- **Alternative**: Direct Phoenix client access (recommended)

## 📊 Phoenix Monitoring Script

### Installation Location
```
/home/anteb/thesis_project/main/phoenix_monitoring.py
```

### Core Features
1. **Real-time trace analysis** with comprehensive breakdowns
2. **Workflow execution tracking** for GAMP categorization
3. **Performance metrics** and latency analysis
4. **Export functionality** for compliance reporting
5. **Real-time monitoring** with configurable intervals

### Usage Examples

#### 1. Get Trace Summary
```bash
uv run python main/phoenix_monitoring.py --summary --hours 1
```

**Sample Output**:
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

#### 2. Export Comprehensive Report
```bash
uv run python main/phoenix_monitoring.py --export phoenix_traces_report.json
```

**Generated Report Includes**:
- 24-hour trace summary
- 1-hour recent activity
- GAMP workflow execution details
- Context provider operation traces
- ChromaDB search operations

#### 3. Real-time Monitoring
```bash
uv run python main/phoenix_monitoring.py --monitor
```

**Features**:
- Live span count updates
- New operation detection
- Configurable monitoring intervals
- Keyboard interrupt support

## 🔍 Captured Trace Types

### Workflow Traces (Recent Execution)
- `GAMPCategorizationWorkflow.start`
- `GAMPCategorizationWorkflow.process_document`
- `GAMPCategorizationWorkflow.categorize_document`
- `GAMPCategorizationWorkflow.handle_error_recovery`
- `GAMPCategorizationWorkflow.check_consultation_required`
- `GAMPCategorizationWorkflow.complete_workflow`

### RAG System Traces (Historical)
- `OpenAIEmbedding._get_query_embedding` (23 spans)
- `VectorIndexRetriever._retrieve` (23 spans)
- `context_provider.process_request` (6 spans)
- `chromadb.search_documents` (6 spans)
- `chromadb.chunk.*` operations (per document chunk)

### ChromaDB Operations
- `chromadb.search_collection.regulatory`
- `chromadb.search_collection.gamp5`
- `chromadb.search_collection.best_practices`
- `chromadb.search_collection.sops`

## 🌐 Phoenix UI Access

### Direct Browser Access
```
http://localhost:6006
```

**Available without MCP browser tools**:
- Trace visualization
- Span hierarchy analysis
- Performance metrics
- Token usage tracking
- Export capabilities

### Manual Browser Navigation
Since MCP browser tools require additional setup, you can:
1. Open browser manually to `http://localhost:6006`
2. Use Phoenix UI for visual trace analysis
3. Export data programmatically via monitoring script

## 🔧 Troubleshooting

### MCP Browser Tools (Optional)
If you want to set up browser automation:

#### Playwright MCP Setup
```bash
# Install browser (requires sudo)
sudo npx playwright install chrome

# Test connection
uv run python -c "
from mcp__playwright__browser_navigate import browser_navigate
browser_navigate('http://localhost:6006')
"
```

#### Puppeteer MCP Issues
- **Error**: `qemu-x86_64: Could not open '/lib64/ld-linux-x86-64.so.2'`
- **Cause**: WSL/Docker environment compatibility
- **Solution**: Use Playwright or direct Phoenix client access

### Phoenix Client Issues
- **Version Warning**: Phoenix server (11.13.2) vs client (11.10.1)
- **Impact**: Minor compatibility warnings, functionality works
- **Solution**: Warnings are safe to ignore

## 📈 Integration with Pharmaceutical Workflow

### GAMP-5 Compliance Monitoring
The monitoring script captures:
- **Complete workflow execution** traces
- **Error handling** and recovery operations  
- **Decision audit trails** for regulatory compliance
- **Performance metrics** for validation

### Real-world Usage
```bash
# Before running workflow
uv run python main/phoenix_monitoring.py --export pre_workflow_baseline.json

# Run pharmaceutical workflow
uv run python main/main.py test_document.txt --categorization-only

# Analyze workflow traces
uv run python main/phoenix_monitoring.py --summary --hours 1

# Export final report
uv run python main/phoenix_monitoring.py --export post_workflow_traces.json
```

## 🎯 Key Benefits Achieved

### ✅ No Browser Dependencies
- Direct Phoenix client access eliminates MCP browser setup complexity
- Works in WSL, Docker, and restricted environments
- No `sudo` permissions required for monitoring

### ✅ Comprehensive Trace Access
- **176 total spans** captured across workflow executions
- **Real-time monitoring** capabilities
- **Export functionality** for compliance documentation

### ✅ Pharmaceutical Compliance
- Complete GAMP-5 workflow trace capture
- Error handling and recovery documentation
- Audit trail generation for regulatory requirements

### ✅ Performance Insights
- Latency tracking for optimization
- Operation breakdown analysis
- Historical trend monitoring

## 🔄 Workflow Integration

### 1. Pre-execution Setup
```bash
# Ensure Phoenix is running
curl -f http://localhost:6006 && echo "Phoenix ready"

# Clear previous monitoring data if needed
uv run python main/phoenix_monitoring.py --export baseline.json
```

### 2. Workflow Execution with Monitoring
```bash
# Start real-time monitoring in background
uv run python main/phoenix_monitoring.py --monitor &

# Run pharmaceutical workflow
uv run python main/main.py your_document.txt

# Stop monitoring (Ctrl+C)
```

### 3. Post-execution Analysis
```bash
# Generate comprehensive report
uv run python main/phoenix_monitoring.py --export final_report.json

# Review workflow-specific traces
uv run python main/phoenix_monitoring.py --workflow GAMP
```

## 📚 Additional Resources

- **Phoenix UI**: http://localhost:6006 (manual browser access)
- **Monitoring Script**: `/home/anteb/thesis_project/main/phoenix_monitoring.py`
- **Export Reports**: Generated in project root directory
- **Phoenix Documentation**: https://arize.com/docs/phoenix

---

**Status**: ✅ Phoenix monitoring fully operational without MCP browser dependencies  
**Alternative**: Browser automation available with additional setup  
**Recommendation**: Use programmatic access for reliable, permission-free monitoring