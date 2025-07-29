# GAMP-5 Categorization Agent Iteration Loop Debug Plan

## Issue Summary
The UnifiedTestGenerationWorkflow's GAMP-5 categorization agent is getting stuck in an iteration loop, hitting the max_iterations limit (10, previously 20) and falling back to Category 5 with 0% confidence.

## Root Cause Analysis

### Symptoms
1. Agent makes 40+ API calls in 55+ seconds
2. Gets stuck in a loop: `call_tool` → `aggregate_tool_results` → `setup_agent`
3. Hits max_iterations and falls back to Category 5 with 0% confidence
4. Error message: "'FunctionAgent' object has no attribute 'chat'"

### Investigation Findings

1. **Correct FunctionAgent Usage**: The code correctly uses `await agent.run(user_msg=...)` (line 706 in agent.py)
2. **No JSON Mode**: Code explicitly avoids JSON mode with comment "JSON mode NOT used - FunctionAgent requires natural language responses"
3. **Tool Configuration**: Two tools are provided: `gamp_analysis_tool` and `confidence_tool`
4. **Max Iterations**: Set to 10 (reduced from 20)

### Hypothesis

The FunctionAgent is likely getting stuck because:

1. **Tool Response Format**: The tools might be returning data in a format that the LLM can't properly interpret, causing it to repeatedly call tools
2. **Missing Stop Signal**: The agent might not be getting a clear signal that it has completed its task
3. **System Prompt Issue**: The system prompt might not be clear enough about when to stop tool calling

## Solution Plan

### 1. Analyze Tool Response Format

The `gamp_analysis_tool` returns a complex dictionary:
```python
{
    "predicted_category": predicted_category.value,
    "evidence": evidence,
    "all_categories_analysis": categories_analysis,
    "decision_rationale": f"Category {predicted_category.value} selected based on {evidence['strong_count']} strong indicators"
}
```

The `confidence_tool` returns a simple float value.

**Issue**: The complex nested dictionary from `gamp_analysis_tool` might be confusing the LLM.

### 2. Improve System Prompt

Current system prompt (lines 438-456) needs to be more explicit about:
- When to stop calling tools
- How to interpret tool results
- Expected output format

### 3. Add Explicit Stop Condition

The agent needs a clearer indication that it has completed its task after calling both tools.

## Proposed Fixes

### Fix 1: Simplify Tool Output Format

Modify `gamp_analysis_tool` to return a simpler, more LLM-friendly format:

```python
def gamp_analysis_tool(urs_content: str) -> dict[str, Any]:
    # ... existing analysis logic ...
    
    # Simplify the return format
    return {
        "category": predicted_category.value,
        "confidence_indicators": evidence['strong_count'],
        "rationale": f"Category {predicted_category.value} selected based on {evidence['strong_count']} strong indicators and {evidence['weak_count']} weak indicators"
    }
```

### Fix 2: Enhanced System Prompt

Update the system prompt to be more explicit:

```python
system_prompt = """You are a GAMP-5 categorization expert. Your task is to analyze URS documents and determine the GAMP category.

Categories:
- Category 1: Infrastructure (OS, databases, middleware)
- Category 3: Non-configured COTS (used as supplied)
- Category 4: Configured products (user parameters)
- Category 5: Custom applications (bespoke code)

IMPORTANT INSTRUCTIONS:
1. First, call the gamp_analysis_tool with the URS content
2. Then, call the confidence_tool with the analysis results
3. After calling both tools, provide your final answer with:
   - The determined category (1, 3, 4, or 5)
   - The confidence score (0.0 to 1.0)
   - A brief justification

DO NOT call the tools more than once each. Once you have both results, provide your final answer immediately.

Error Handling:
- If analysis fails or confidence is below 60%, Category 5 will be assigned
- All errors are logged for regulatory compliance
- Low confidence results require human review"""
```

### Fix 3: Add Tool Call Tracking

Implement a mechanism to track which tools have been called and prevent repeated calls:

```python
class ToolCallTracker:
    def __init__(self):
        self.called_tools = set()
    
    def mark_called(self, tool_name: str):
        self.called_tools.add(tool_name)
    
    def has_called(self, tool_name: str) -> bool:
        return tool_name in self.called_tools
    
    def all_tools_called(self, required_tools: list[str]) -> bool:
        return all(tool in self.called_tools for tool in required_tools)
```

### Fix 4: Implement Return Direct Pattern

Consider using the `return_direct` pattern from LlamaIndex where certain tool outputs can directly end the agent loop.

### Fix 5: Add Debugging and Monitoring

Add detailed logging to understand what's happening in the loop:

```python
# In categorize_with_error_handling
self.logger.debug(f"Agent iteration {iteration}: Calling tools...")
self.logger.debug(f"Tool response: {response_text[:200]}...")
```

## Implementation Priority

1. **High Priority**: Update system prompt (Fix 2) - Quick and low risk
2. **High Priority**: Add debugging logs - Essential for understanding the issue
3. **Medium Priority**: Simplify tool output (Fix 1) - May require testing
4. **Low Priority**: Implement tool call tracking (Fix 3) - More complex change

## Testing Plan

1. Create a minimal test case that reproduces the iteration loop
2. Apply fixes incrementally and test each one
3. Monitor API call count and execution time
4. Verify that confidence scores are properly calculated
5. Ensure fallback to Category 5 only happens on actual errors

## Success Criteria

- Agent completes categorization in < 10 seconds
- Makes <= 5 API calls per categorization
- Produces confidence scores > 0% for valid inputs
- No iteration loop errors
- Maintains GAMP-5 compliance

## Next Steps

1. Implement high-priority fixes first
2. Add comprehensive logging
3. Test with various URS documents
4. Monitor Phoenix traces if available
5. Consider migrating to a more robust agent pattern if issues persist