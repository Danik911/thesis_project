# Monitor Agent Updates
**Date**: 2025-08-28
**Updated by**: Previous orchestration session

## Trace Locations - CONFIRMED

### Primary Trace Storage
**Path**: `C:\Users\anteb\Desktop\Courses\Projects\thesis_project\main\logs\traces\`

### File Types Generated
1. **all_spans_*.jsonl**
   - Contains: Complete span data from workflow execution
   - Format: JSONL (one JSON object per line)
   - Typical Size: 47-200 spans depending on completion
   - Key Fields: span_id, name, duration_ns, attributes, status

2. **chromadb_spans_*.jsonl**
   - Contains: ChromaDB-specific operations
   - Format: JSONL
   - Typical Size: 25-50 operations
   - Key Operations: query, add, get

3. **trace_*.jsonl**
   - Contains: High-level API call events
   - Format: JSONL
   - Typical Size: 1-5 events
   - Tracks: OpenAI embeddings, OpenRouter LLM calls

### Phoenix UI Data
- **URL**: http://localhost:6006
- **Export Location**: Can export to `demonstration.csv` via UI
- **Container**: phoenix-server (Docker)
- **Real-time Monitoring**: Traces appear during execution

## Common Trace Analysis Issues

### Issue 1: Missing LLM Traces
- **Symptom**: No llm.completion spans in Phoenix
- **Cause**: OpenRouter authentication failures prevent LLM calls
- **Verification**: Check for 401 errors in all_spans file

### Issue 2: Incomplete Trace Export
- **Symptom**: Phoenix UI shows traces but export fails
- **Cause**: GraphQL errors or missing instrumentation packages
- **Workaround**: Use file-based traces in logs/traces/

### Issue 3: ChromaDB Span Separation
- **Finding**: ChromaDB spans are duplicated in both all_spans and chromadb_spans files
- **Analysis Tip**: Use chromadb_spans file for focused vector DB analysis

## Analysis Commands

### Quick Trace Inspection
```bash
# Count total spans
wc -l logs/traces/all_spans_*.jsonl

# Extract span names
jq -r '.name' logs/traces/all_spans_*.jsonl | sort | uniq -c

# Find errors
grep -i error logs/traces/all_spans_*.jsonl

# Get execution timeline
jq -r '[.timestamp, .name] | @csv' logs/traces/all_spans_*.jsonl | sort
```

### Performance Analysis
```bash
# Calculate total duration
jq '.duration_ns' logs/traces/all_spans_*.jsonl | awk '{sum+=$1} END {print sum/1000000000 " seconds"}'

# Find slowest operations
jq -r '[.duration_ns, .name] | @csv' logs/traces/all_spans_*.jsonl | sort -rn | head -10
```

## Critical Monitoring Points

### Success Indicators
1. **Categorization**: Look for "GAMPCategorizationEvent" with confidence > 0.6
2. **Agent Coordination**: Verify "AgentResultEvent" for each agent
3. **Test Generation**: Check for "OQTestSuiteEvent" with test_count > 20
4. **Completion**: "WorkflowCompletionEvent" with status="success"

### Failure Indicators
1. **Authentication**: "401 Client Error" in error messages
2. **Timeout**: Spans with duration_ns > 60000000000 (60 seconds)
3. **Consultation Required**: "ConsultationRequiredEvent" indicates workflow halt
4. **No Fallback**: "NO FALLBACK ALLOWED" confirms compliance behavior

## Backup Trace Locations

### Historical Traces
Path: `logs/traces/backup_YYYYMMDD/`
- Contains previous execution traces
- Useful for comparison analysis

### Comprehensive Audit
Path: `logs/comprehensive_audit/`
- More detailed regulatory compliance traces
- Includes ALCOA+ validation events

## Notes for Accurate Reporting
1. **Always verify file existence** before claiming traces captured
2. **Count actual spans** using `wc -l`, not estimated
3. **Check timestamps** to ensure analyzing correct execution
4. **Validate Phoenix accessibility** at http://localhost:6006
5. **Document authentication failures** as compliance features, not bugs