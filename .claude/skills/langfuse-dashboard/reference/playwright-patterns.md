# Playwright MCP Patterns for Langfuse Dashboard

## Pattern 1: Navigate and Screenshot

```python
# Navigate to dashboard
mcp__playwright__browser_navigate(
    url="https://cloud.langfuse.com/project/cmhuwhcfe006yad06cqfub107/traces"
)

# CRITICAL: Wait for React app to load
mcp__playwright__browser_wait_for(time=5)

# Take screenshot
mcp__playwright__browser_take_screenshot(
    fullPage=True,
    filename="dashboard.png"
)
```

## Pattern 2: Extract Metrics via JavaScript

```python
metrics = mcp__playwright__browser_evaluate(
    function="""
    () => {
        const traces = document.querySelectorAll('[data-testid="trace-row"]');
        return {
            trace_count: traces.length,
            first_trace_id: traces[0]?.dataset.traceId || null
        };
    }
    """
)
```

## Pattern 3: Click and Wait

```python
# Click button
mcp__playwright__browser_click(
    element="Filter button",
    ref="[data-testid='filter-button']"
)

# Wait for action to complete
mcp__playwright__browser_wait_for(time=2)

# Capture result
mcp__playwright__browser_take_screenshot(filename="after_click.png")
```

## Pattern 4: Navigate to Specific Trace

```python
trace_id = "abc123"

mcp__playwright__browser_navigate(
    url=f"https://cloud.langfuse.com/trace/{trace_id}"
)

mcp__playwright__browser_wait_for(time=5)

# Expand all spans
try:
    mcp__playwright__browser_click(
        element="Expand all",
        ref="[aria-label='Expand all']"
    )
except:
    pass  # Button may not exist

mcp__playwright__browser_take_screenshot(
    fullPage=True,
    filename=f"trace_{trace_id}.png"
)
```

## Pattern 5: Accessibility Snapshot (Best for Data)

```python
# Better than screenshot for extracting structured data
snapshot = mcp__playwright__browser_snapshot()

# Returns accessibility tree with role/name/value
# Parse snapshot.children to find specific elements
```

## Critical Best Practices

1. **Always wait after navigate**: React apps need time to render
2. **Use accessibility snapshot for data**: More reliable than DOM queries
3. **Handle auth separately**: Login manually before automation
4. **Increase timeouts for slow networks**: `time=10` if needed
5. **Use fullPage=True** for documentation screenshots
