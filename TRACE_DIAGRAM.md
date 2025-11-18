# Langfuse Trace Execution Flow Diagram

## Complete Workflow Execution (5 Minutes 13 Seconds)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  START: execute_workflow                                                 │
│  Job ID: 11bf3e3b-22ef-4126-8061-e2a49f52c353                           │
│  Timestamp: 2025-11-18T09:44:59.924Z                                     │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
        ┌─────────────────┐  ┌────────────────┐  ┌──────────────────┐
        │ GAMP-5          │  │ ChromaDB       │  │ Parallel Agents  │
        │ Categorization  │  │ Vector Search  │  │ Context          │
        │                 │  │                │  │ Collection       │
        │ Span ID:        │  │ Span ID:       │  │                  │
        │ fd2c2a70...     │  │ 4c7f9de9...    │  │ Span ID:         │
        │ Duration: 1ms   │  │ Duration:      │  │ Multiple         │
        │ Status: ✅      │  │ 1500+ms        │  │ Status: ✅       │
        │                 │  │ Status: ✅     │  │                  │
        │ Result:         │  │ (0 results)    │  │ Retrieved all    │
        │ Category: 5     │  │                │  │ agent data       │
        └─────────────────┘  └────────────────┘  └──────────────────┘
                    │               │               │
                    └───────────────┼───────────────┘
                                    │
                    ┌───────────────▼───────────────┐
                    │ Parallel Agent Results        │
                    │ Merged into Context           │
                    │ Status: ✅ SUCCESS            │
                    └───────────────┬───────────────┘
                                    │
                ┌───────────────────┼───────────────────┐
                │                   │                   │
                ▼                   ▼                   ▼
    ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐
    │ Planning Step    │  │ Test Case        │  │ OQ Test Script │
    │                  │  │ Generation       │  │ Generation     │
    │ Creates strategy │  │                  │  │                │
    │ Estimates tests  │  │ Span ID:         │  │ Span ID:       │
    │                  │  │ e9055b6fba52... │  │ e3859952...    │
    │ Status: ✅       │  │                  │  │                │
    │                  │  │ Duration:        │  │ Duration: 36ms │
    │ CRITICAL:        │  │ 143,841ms        │  │ Status: ✅     │
    │ Approved         │  │ (2m 24s)         │  │                │
    │ Category: 5      │  │                  │  │ RESULT:        │
    └──────────────────┘  │ 4x LLM calls     │  │ OQ Scripts     │
                          │ (deepseek-v3.1)  │  │ Generated      │
                          │                  │  └────────────────┘
                          │ Status: ✅       │
                          │                  │
                          │ RESULT:          │
                          │ Test cases       │
                          │ written to       │
                          │ /output/         │
                          │ test_suites/     │
                          └──────────────────┘
                                    │
                    ┌───────────────▼───────────────┐
                    │ Test Suite Completion         │
                    │ Span: 596004f685eac25d        │
                    │ complete_workflow()           │
                    │                               │
                    │ ✅ Tests generated            │
                    │ ✅ ALCOA+ records created     │
                    │ ✅ Electronic signatures      │
                    │ ✅ Test suite YAML prepared   │
                    │                               │
                    │ Now attempting:               │
                    │ Save artifact to storage      │
                    └───────────────┬───────────────┘
                                    │
                ┌───────────────────▼───────────────────┐
                │  ARTIFACT PERSISTENCE (worker_executor)│
                │  Line 181: await save_artifact()      │
                │                                        │
                │  Metadata prepared:                   │
                │  {                                    │
                │    "job_id": "11bf3e3b...",           │
                │    "gamp_category": str(None),        │
                │    "artifact_type": "test_suite",     │
                │    ...                                │
                │  }                                    │
                └───────────────┬───────────────────────┘
                                    │
                ┌───────────────────▼───────────────────┐
                │  LocalStorageAdapter Validation       │
                │  Line 100: int("None")                │
                │                                        │
                │  ValueError!                          │
                │  "invalid literal for int() with      │
                │   base 10: 'None'"                    │
                │                                        │
                │  ❌ VALIDATION FAILED                 │
                └───────────────┬───────────────────────┘
                                    │
                ┌───────────────────▼───────────────────┐
                │  WORKFLOW MARKED AS FAILED             │
                │  Status: ERROR                        │
                │  Status Message: CRITICAL: Invalid     │
                │  GAMP category in metadata            │
                │                                        │
                │  ❌ BUT: Tests still exist in         │
                │     /output/test_suites/              │
                │     (unsaved to persistent storage)   │
                └───────────────────────────────────────┘
```

---

## The Bug in Metadata Flow

```
┌─────────────────────────────────────────────────────────────┐
│ unified_workflow.py - complete_workflow() function          │
│                                                              │
│ Builds final_results dict:                                  │
│ {                                                            │
│   "categorization": {                                        │
│     "category": 5,                                           │
│     "gamp_category": 5,  ← Value is here (nested)           │
│     ...                                                      │
│   },                                                         │
│   "test_suite": "...",                                       │
│   "test_suite_yaml": "...",                                  │
│   # NO TOP-LEVEL "gamp_category" ← MISSING!                │
│ }                                                            │
│                                                              │
│ return StopEvent(result=final_results)                       │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│ worker_executor.py - execute_workflow() function            │
│                                                              │
│ Line 152:                                                    │
│ gamp_category = workflow_result.get("gamp_category")        │
│                 ↓                                             │
│                 None (key not found!)                        │
│                                                              │
│ Line 172:                                                    │
│ artifact_metadata = {                                        │
│   "gamp_category": str(gamp_category),                       │
│                    ↓                                          │
│                    str(None)                                 │
│                    ↓                                          │
│                    "None" (string literal) ← BUG!            │
│   ...                                                        │
│ }                                                            │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│ local_adapter.py - _validate_metadata() function            │
│                                                              │
│ Line 100:                                                    │
│ category = int(metadata["gamp_category"])                    │
│            ↓                                                  │
│            int("None")                                       │
│            ↓                                                  │
│            ValueError! ❌                                    │
│                                                              │
│ Message: "invalid literal for int() with base 10: 'None'"   │
└──────────────────────────────────────────────────────────────┘
```

---

## The Fix in Metadata Flow

```
┌─────────────────────────────────────────────────────────────┐
│ unified_workflow.py - complete_workflow() function          │
│                                                              │
│ Builds final_results dict:                                  │
│ {                                                            │
│   "categorization": {                                        │
│     "category": 5,                                           │
│     "gamp_category": 5,                                      │
│     ...                                                      │
│   },                                                         │
│   "test_suite": "...",                                       │
│   "test_suite_yaml": "...",                                  │
│ }                                                            │
│                                                              │
│ # ADD THESE 3 LINES:                                         │
│ if categorization_result:                                    │
│   final_results["gamp_category"] = \                         │
│     categorization_result.gamp_category.value                │
│ else:                                                        │
│   final_results["gamp_category"] = None                      │
│                                                              │
│ NOW the dict has:                                            │
│ {                                                            │
│   ...                                                        │
│   "gamp_category": 5,  ← TOP-LEVEL KEY ADDED! ✅             │
│ }                                                            │
│                                                              │
│ return StopEvent(result=final_results)                       │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│ worker_executor.py - execute_workflow() function            │
│                                                              │
│ Line 152:                                                    │
│ gamp_category = workflow_result.get("gamp_category")        │
│                 ↓                                             │
│                 5 (found!) ✅                                 │
│                                                              │
│ Line 172:                                                    │
│ artifact_metadata = {                                        │
│   "gamp_category": str(gamp_category),                       │
│                    ↓                                          │
│                    str(5)                                    │
│                    ↓                                          │
│                    "5" (valid string) ✅                      │
│   ...                                                        │
│ }                                                            │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│ local_adapter.py - _validate_metadata() function            │
│                                                              │
│ Line 100:                                                    │
│ category = int(metadata["gamp_category"])                    │
│            ↓                                                  │
│            int("5")                                          │
│            ↓                                                  │
│            5 (valid integer) ✅                              │
│                                                              │
│ Validation passes! ✅                                        │
│ Artifact saved successfully!                                 │
└──────────────────────────────────────────────────────────────┘
```

---

## Timeline Visualization

```
09:44:59  ┌─ Workflow Start
          │
09:45:05  ├─ GAMP Categorization Complete (✅ Category 5)
          │
09:45:07  ├─ Parallel Agents Start
          │
09:47:49  ├─ OQ Test Case Generation Start
          │
09:50:00  ├─ DeepSeek LLM Processing...
          │
09:50:13  ├─ OQ Test Scripts Generated (✅ Tests Exist)
          │
09:50:13  ├─ Test Suite Completion
          │  ├─ ALCOA+ Records Created (✅)
          │  ├─ Electronic Signatures Applied (✅)
          │  ├─ Test Suite YAML Prepared (✅)
          │  └─ Ready to Save Artifacts
          │
09:50:13+ ├─ Artifact Persistence Attempt
          │  ├─ Extract gamp_category from results
          │  ├─ gamp_category = workflow_result.get("gamp_category")
          │  ├─ Result: None (key not in dict)
          │  ├─ Convert: str(None) = "None"
          │  ├─ Pass to LocalStorageAdapter
          │  └─ Validation Error: int("None") fails
          │
09:50:14  └─ ❌ WORKFLOW FAILED

          ⚠️  Tests Generated Successfully
          ⚠️  Artifacts NOT Persisted
          ⚠️  GAMP-5 Audit Trail Incomplete
```

---

## Summary

**The Bug:** Missing top-level `gamp_category` key in workflow result
**The Symptom:** `str(None)` creates string `"None"` which fails int() validation
**The Fix:** Add 3 lines to expose `gamp_category` at top level
**The Outcome:** Metadata validates correctly, artifacts persist, audit trail complete
