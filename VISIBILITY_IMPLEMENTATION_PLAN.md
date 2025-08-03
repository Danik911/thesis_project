# Visibility Implementation Plan for Future Agent

**Date**: 2025-08-02  
**Purpose**: Add comprehensive visibility to debug and prove workflow functionality

## 🎯 Current Situation Summary

### What We Know:
- Individual agents work in isolation (proven with direct tests)
- Full workflow times out without completing
- Phoenix observability is broken (can't access traces)
- We have NO VISIBILITY into what's actually happening

### What We Need:
- Real-time visibility of every API call
- Agent execution times and results
- Data flow between components
- Error locations and stack traces

## 📋 Implementation Plan

### Phase 1: Integrate Simple Tracer (1 hour)

1. **Update `unified_workflow.py`**:
   ```python
   from src.monitoring.simple_tracer import get_tracer
   
   # At workflow start
   tracer = get_tracer()
   tracer.start_workflow("unified_test_generation", document_path)
   
   # Before each agent call
   agent_start = time.time()
   tracer.log_step(f"executing_{agent_type}", {"request": ev.request_data})
   
   # After agent response
   tracer.log_agent_execution(agent_type, agent_start, result, error)
   ```

2. **Update each agent's `process_request` method**:
   ```python
   # In context_provider.py, sme_agent.py, research_agent.py
   from src.monitoring.simple_tracer import get_tracer
   
   # Log API calls
   api_start = time.time()
   response = await llm.chat(messages)
   get_tracer().log_api_call("openai", "chat", time.time() - api_start, True)
   ```

3. **Add checkpoints in workflow**:
   ```python
   # Key locations to add logging:
   - After categorization
   - Before/after context storage operations
   - During agent coordination
   - At each workflow step transition
   ```

### Phase 2: Create Debug Runner (30 min)

Create `main/debug_workflow.py`:
```python
"""Debug runner with maximum visibility."""
import sys
from src.monitoring.simple_tracer import get_tracer

# Run with detailed output
tracer = get_tracer()
print(f"🔍 Debug trace will be saved to: {tracer.session_file}")

# Import and run workflow
from main import main
sys.argv = ["main.py", "tests/test_data/gamp5_test_data/testing_data.md", "--verbose"]
main()

# Print summary
summary = tracer.get_summary()
print(f"\n📊 Execution Summary:")
print(f"Total API calls: {summary['api_calls']['count']}")
print(f"Successful: {summary['api_calls']['successful']}")
print(f"Total duration: {summary['api_calls']['total_duration']:.2f}s")
print(f"Errors: {summary['errors']}")
```

### Phase 3: Add Timeout Protection (30 min)

1. **Per-agent timeouts**:
   ```python
   import asyncio
   
   try:
       result = await asyncio.wait_for(
           agent.process_request(ev), 
           timeout=30.0  # 30 second timeout per agent
       )
   except asyncio.TimeoutError:
       tracer.log_error(f"{agent_type}_timeout", "Agent execution timed out after 30s")
       # Continue with partial results
   ```

2. **Workflow-level timeout with graceful degradation**:
   ```python
   # Allow workflow to complete with partial results
   # Log what completed vs what timed out
   ```

## 🔍 Expected Outputs

### 1. Real-time Console Output:
```
🔍 Debug trace will be saved to: logs/traces/trace_20250802_143022.jsonl
🌐 API Call: openai - chat/completions - 2.34s - ✅
🤖 Agent: categorization - 2.45s - ✅
📍 Checkpoint: categorization_complete - Category 5, Confidence 90%
🤖 Agent: context_provider - 5.23s - ✅
🤖 Agent: sme - 30.00s - ❌ (timeout)
```

### 2. Trace File (JSONL):
Each line is a JSON object with full details for analysis

### 3. Summary Report:
- Which agents actually execute
- Real API call times
- Where the workflow fails/times out
- Actual vs expected behavior

## 📝 Key Code Locations to Modify

1. `main/src/core/unified_workflow.py`:
   - Add tracer at class init
   - Log at each workflow step
   - Add timeout protection

2. `main/src/agents/parallel/*.py`:
   - Log API calls in each agent
   - Add execution timing

3. `main/main.py`:
   - Add tracer initialization
   - Ensure proper cleanup on exit

## ⚡ Quick Test Commands

```bash
# Run with visibility
cd main
python debug_workflow.py

# Analyze trace
python -c "
import json
with open('logs/traces/latest.jsonl') as f:
    for line in f:
        event = json.loads(line)
        if event['event_type'] == 'api_call':
            print(f\"{event['data']['service']}: {event['data']['duration']:.2f}s\")
"
```

## 🎯 Success Criteria

After implementation, we should be able to answer:
1. Are real API calls being made? (with proof)
2. Which agents execute successfully?
3. Where exactly does the workflow fail?
4. What are the actual execution times?
5. Is data passed correctly between components?

## 🚨 Important Notes

1. **Simple is better** - Don't over-engineer, we need visibility NOW
2. **File-based is fine** - No complex infrastructure needed
3. **Console output is key** - Immediate feedback during execution
4. **Preserve working code** - Only add logging, don't change logic

---

**For the next agent**: Start with Phase 1. The `simple_tracer.py` is already created at `main/src/monitoring/simple_tracer.py`. Focus on integration and getting that first trace file with real data.