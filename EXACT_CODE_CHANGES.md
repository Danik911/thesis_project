# Exact Code Changes Required

## File 1: `main/src/core/unified_workflow.py`

### Location
**Function:** `complete_workflow()`
**Around line:** 2353

### Current Code (BROKEN)
```python
        self.logger.info(f"[COMPLETE] Unified workflow completed with status: {status}")
        if total_time:
            self.logger.info(f"[TIMING] Total processing time: {total_time.total_seconds():.2f} seconds")
        flush_output()

        # Enhanced Phoenix Observability - temporarily disabled for testing
        # if self.enable_phoenix:
        #     ...

        return StopEvent(result=final_results)
```

### Fixed Code
```python
        self.logger.info(f"[COMPLETE] Unified workflow completed with status: {status}")
        if total_time:
            self.logger.info(f"[TIMING] Total processing time: {total_time.total_seconds():.2f} seconds")
        flush_output()

        # Enhanced Phoenix Observability - temporarily disabled for testing
        # if self.enable_phoenix:
        #     ...

        # ADD THESE 3 LINES:
        # Add top-level gamp_category for worker_executor compatibility
        if categorization_result:
            final_results["gamp_category"] = categorization_result.gamp_category.value
        else:
            final_results["gamp_category"] = None

        return StopEvent(result=final_results)
```

### Explanation
The workflow builds a `final_results` dictionary that contains:
- Nested: `final_results["categorization"]["gamp_category"]` = 5 (integer)
- Missing: `final_results["gamp_category"]` = (not defined)

The worker expects the latter. These 3 lines add it at the top level.

---

## Why `categorization_result` Is Available

In the `complete_workflow()` function (around line 2221), the code does:
```python
categorization_result = await safe_context_get(ctx, "categorization_result", None)
```

This is already in scope and contains the GAMP categorization with the `.gamp_category.value` attribute (an integer).

---

## No Changes to Other Files

The following files do NOT need changes:
- `main/api/worker_executor.py` - Code is correct, just receives None due to missing key
- `main/src/adapters/local_adapter.py` - Validation logic is correct
- `main/src/adapters/chroma_adapter.py` - No changes needed
- `main/src/adapters/s3_adapter.py` - No changes needed

---

## Testing the Fix

### Before Running Workflow
1. Open `main/src/core/unified_workflow.py`
2. Go to line 2353 (search for "return StopEvent(result=final_results)")
3. Add the 3 lines above as shown in "Fixed Code" section
4. Save file

### Running Workflow
```bash
# In project root directory
uv run python main/main.py
```

### Verify Success
Check logs for:
```
✅ Test suite saved successfully to output/test_suites/test_suite_*.json
```

Check metadata file:
```
# File: output/test_suites/test_suite_*.json.meta.json
{
  "gamp_category": "5",  # Should be integer-as-string, NOT "None"
  "job_id": "...",
  "created_at": "...",
  ...
}
```

---

## Line-by-Line Change

**Location:** `main/src/core/unified_workflow.py`, line 2353

**BEFORE (1 line):**
```python
        return StopEvent(result=final_results)
```

**AFTER (5 lines):**
```python
        # Add top-level gamp_category for worker_executor compatibility
        if categorization_result:
            final_results["gamp_category"] = categorization_result.gamp_category.value
        else:
            final_results["gamp_category"] = None

        return StopEvent(result=final_results)
```

This is a **4-line insertion** before the existing return statement.

---

## Trace Through the Fix

### Old Execution Path (BROKEN)
```
unified_workflow.py returns:
  {
    "categorization": {"gamp_category": 5},
    "test_suite": "...",
    ...
    # NO top-level "gamp_category"
  }
    ↓
worker_executor.py line 152:
  gamp_category = result.get("gamp_category")  # None (key not found)
    ↓
worker_executor.py line 172:
  "gamp_category": str(None)  # "None" (string)
    ↓
local_adapter.py line 100:
  int("None")  # ❌ ValueError!
```

### New Execution Path (FIXED)
```
unified_workflow.py returns:
  {
    "categorization": {"gamp_category": 5},
    "gamp_category": 5,  # ✅ NEW: Top-level key added
    "test_suite": "...",
    ...
  }
    ↓
worker_executor.py line 152:
  gamp_category = result.get("gamp_category")  # 5 (found!)
    ↓
worker_executor.py line 172:
  "gamp_category": str(5)  # "5" (valid string)
    ↓
local_adapter.py line 100:
  int("5")  # ✅ 5 (validation passes!)
```

---

## Commit Message

```
Fix: Add top-level gamp_category to workflow results for artifact persistence

The unified_workflow returns gamp_category nested under "categorization" key,
but worker_executor expects it at the top level. This caused the worker to
receive None, convert it to string "None", and fail validation.

Fixed by adding 3 lines to complete_workflow() to expose gamp_category at
top level of result dictionary.

Fixes: OQ generation workflow fails when saving artifacts with ValueError on
metadata validation.

Impact: Artifacts now persist correctly with valid GAMP-5 metadata.
```
