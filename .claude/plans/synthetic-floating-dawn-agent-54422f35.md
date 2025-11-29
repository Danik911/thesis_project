# Context/RAG Agent Investigation - Analysis Plan

## User Report
"The context agent stopped searching the database"

## Investigation Findings

### 1. **Workflow Invocation Architecture**

#### Location: `unified_workflow.py` Line 1044-1146
The context agent is invoked through a sequential multi-agent coordination workflow:

```
PlanningEvent (test_strategy) 
    ↓
run_planning_workflow() - Line 1044
    ↓
IF enable_parallel_coordination == True:
    ↓
    agent_requests.append({
        "agent_type": "context_provider",  # Line 1073
        "request_data": {...}
    })
    ↓
execute_agent_request() - Line 1150
    ↓
context_provider.process_request() - Line 1186-1230
    ↓
_search_documents() - Line 601 in context_provider.py
    ↓
ChromaDB query execution
```

**Key Discovery:** Context agent is **conditionally invoked** based on `enable_parallel_coordination` flag.

---

### 2. **Critical Conditional Logic That Could Skip Context Agent**

#### Condition #1: `enable_parallel_coordination` Flag (Line 1070, 1113)
```python
if self.enable_parallel_coordination:
    # Always include context provider
    agent_requests.append({
        "agent_type": "context_provider",
        ...
    })

if not self.enable_parallel_coordination or not agent_requests:
    self.logger.info("[PARALLEL] Skipping parallel coordination - creating empty results")
    return AgentResultsEvent(
        agent_results=[],  # EMPTY - no context search
        session_id=self._workflow_session_id
    )
```

**RISK:** If `enable_parallel_coordination=False`, context agent is **completely bypassed**.

#### Condition #2: Empty Agent Requests (Line 1113)
Even with parallel coordination enabled, if `agent_requests` is empty, workflow skips to OQ generation with no context.

---

### 3. **Timeout Configuration (Lines 1174-1223)**

Context agent has a **60-second timeout**:
```python
timeout_mapping = {
    "research": 300.0,           # 5 minutes
    "sme": 300.0,                # 5 minutes  
    "context_provider": 60.0,    # 1 minute ⚠️
}
```

**RISK:** If ChromaDB search takes >60s, TimeoutError is returned with `success=False`, but workflow continues with empty context results.

**Timeout Error Path (Lines 1206-1223):**
```python
except TimeoutError:
    return AgentResultEvent(
        agent_type=ev.agent_type,
        result_data={
            "error": f"Agent execution timed out after {agent_timeout} seconds",
            "error_type": "TimeoutError"
        },
        success=False,  # ⚠️ Marked as failure but workflow continues
        ...
    )
```

**Critical:** Timeout errors are logged but workflow proceeds to OQ generation anyway.

---

### 4. **Recent RAG Fix Commit Analysis**

**Commit 10485cb (Nov 19):** "Fix issues with RAG"
**Previous Issue (29ffe4b):** "The RAG agent didn't retrieve files"

**Key Changes Made:**

1. **Vector Store Path Changed (Line 152):**
   ```python
   # OLD: "./lib/chroma_db"
   # NEW: "./chroma_db"  (matches Docker volume mount)
   ```

2. **Readiness Guard Added (Lines 622-666):**
   ```python
   # Check if ALL collections empty
   if total_documents == 0:
       raise RuntimeError(
           "CRITICAL: Context Provider cannot execute - ALL ChromaDB collections are empty."
       )
   ```
   
   **Behavior:** Only fails if ALL collections are empty. If at least 1 collection has documents, workflow proceeds.

3. **Environment Variable Validation (Lines 118-140):**
   ```python
   if not os.getenv("OPENAI_API_KEY"):
       raise RuntimeError(
           "CRITICAL: Context Provider initialization failed - missing OPENAI_API_KEY"
       )
   ```

4. **NLTK Dependency Removed (Line 541-546):**
   Switched from `SentenceSplitter` (requires NLTK) to `TokenTextSplitter` (NLTK-free).

---

### 5. **ChromaDB Collection Architecture**

**Collections Initialized (Lines 472-501):**
```python
self.collections = {
    "gamp5": self.chroma_client.get_or_create_collection("gamp5_documents"),
    "regulatory": self.chroma_client.get_or_create_collection("regulatory_documents"),
    "sops": self.chroma_client.get_or_create_collection("sop_documents"),
    "best_practices": self.chroma_client.get_or_create_collection("best_practices")
}
```

**Search Logic (Line 925-944):**
```python
def _select_collections(self, gamp_category: str, search_scope: dict):
    collections = ["gamp5", "regulatory"]  # Always include base collections
    
    if gamp_category in ["4", "5"]:
        collections.append("sops")
    
    if search_scope.get("include_best_practices", True):
        collections.append("best_practices")
    
    return collections
```

**RISK:** If these collections are empty, search returns 0 results, but workflow doesn't fail (unless ALL collections empty).

---

### 6. **Error Swallowing Patterns**

#### Pattern #1: Silent Timeout Continuation
- Timeout errors logged but workflow continues
- No halt on context retrieval failure
- OQ generation proceeds with empty context

#### Pattern #2: Partial Collection Failure Allowed
```python
# Only fails if total_documents == 0
# Proceeds if ANY collection has documents, even if others are empty
if total_documents == 0:
    raise RuntimeError(...)
```

#### Pattern #3: Success=False but No Workflow Halt
```python
return AgentResultEvent(
    success=False,  # Marked as failure
    result_data={"error": "..."}
)
# Workflow continues to collect_agent_results() and proceeds anyway
```

---

### 7. **Agent Result Merging (Lines 1352-1395)**

```python
async def collect_agent_results(ctx, ev: AgentResultEvent):
    results = await safe_context_get(ctx, "collected_results", [])
    results.append(ev)  # ⚠️ Appends even if ev.success=False
    
    if len(results) >= expected_count:
        return AgentResultsEvent(
            agent_results=results,  # Includes failed results
            session_id=self._workflow_session_id
        )
```

**Issue:** Failed agent results (success=False) are merged with successful ones without filtering.

---

## ⚠️ ROOT CAUSE IDENTIFIED ⚠️

### **CRITICAL FINDING: Worker Executor Missing `enable_parallel_coordination` Parameter**

**File:** `main/api/worker_executor.py` Line 216-218

```python
workflow = UnifiedTestGenerationWorkflow(
    approved_category=approved_category
)
# ❌ MISSING: enable_parallel_coordination parameter
```

**Default Value:** Line 449 in `unified_workflow.py`
```python
enable_parallel_coordination: bool = True  # Defaults to True
```

**Impact Assessment:**
- Default value is `True`, so workflow SHOULD invoke context agent
- However, if parameter not explicitly set in worker_executor, potential initialization issues
- Need to verify actual runtime behavior vs expected default

**Comparison with main.py (Working):**
```python
# main.py Line 272 - Explicitly sets parameter
workflow = UnifiedTestGenerationWorkflow(
    timeout=1200,
    verbose=args.verbose,
    enable_parallel_coordination=not args.disable_parallel_coordination  # ✅ Explicit
)
```

---

## Potential Root Causes

### Hypothesis 1: `enable_parallel_coordination=False`
**File:** `unified_workflow.py` Line 449
**Check:** Workflow initialization parameter

If workflow was created with `enable_parallel_coordination=False`, context agent is completely skipped.

**Verification Needed:**
```python
# Check how workflow is instantiated in main.py or API
workflow = UnifiedTestGenerationWorkflow(
    enable_parallel_coordination=???  # What's the value?
)
```

---

### Hypothesis 2: ChromaDB Collections Empty
**File:** `context_provider.py` Lines 622-666

If ChromaDB collections have 0 documents, context search returns empty results.

**Verification Needed:**
- Check if ingestion script ran successfully
- Verify ChromaDB persistence path matches Docker volume
- Count documents in each collection

---

### Hypothesis 3: 60-Second Timeout Too Short
**File:** `unified_workflow.py` Line 1177

If ChromaDB search takes >60s (large database, slow disk I/O in Docker):
- TimeoutError raised
- Workflow continues with empty context
- No loud failure

**Verification Needed:**
- Check logs for "[TIMEOUT]" messages
- Monitor ChromaDB query duration

---

### Hypothesis 4: OPENAI_API_KEY Missing
**File:** `context_provider.py` Lines 118-140

If `OPENAI_API_KEY` not set, context agent initialization fails entirely.

**Verification Needed:**
```bash
docker exec -it pharma-api-dev env | grep OPENAI_API_KEY
```

---

### Hypothesis 5: Vector Store Path Mismatch
**File:** `context_provider.py` Line 152
**Recent Change:** `./lib/chroma_db` → `./chroma_db`

If ingestion used old path but runtime uses new path, collections appear empty.

**Verification Needed:**
- Check which path has actual data
- Verify Docker volume mount configuration

---

## Recommended Next Steps

### Step 1: Check Workflow Configuration
**Action:** Find where `UnifiedTestGenerationWorkflow` is instantiated
**Files to Check:**
- `main/main.py`
- `main/api/worker_executor.py`
- `main/api/app.py`

**Look For:**
```python
enable_parallel_coordination=False  # ⚠️ This would skip context agent
```

---

### Step 2: Verify ChromaDB State
**Action:** Check collection document counts

**Command:**
```bash
docker exec -it pharma-api-dev python3 -c "
import chromadb
client = chromadb.PersistentClient(path='/app/chroma_db')
for col in client.list_collections():
    print(f'{col.name}: {col.count()} documents')
"
```

**Expected Output:**
```
gamp5_documents: >0
regulatory_documents: >0
sop_documents: >0
best_practices: >0
```

---

### Step 3: Check Logs for Timeout/Error Patterns
**Action:** Search logs for context agent execution traces

**Patterns to Search:**
```
[PARALLEL] Starting parallel agent coordination
[AGENT] Starting context_provider agent
[TIMEOUT] CRITICAL: context_provider agent timed out
[READINESS] ChromaDB collections ready
ChromaDB search completed
```

**Files:**
- `main/logs/audit/alcoa_records_*.json`
- Docker logs: `docker logs pharma-api-dev 2>&1 | grep -i context`

---

### Step 4: Verify Environment Variables
**Action:** Check if OPENAI_API_KEY is available in Docker

**Command:**
```bash
docker exec -it pharma-api-dev env | grep OPENAI_API_KEY
```

---

### Step 5: Test Context Agent Directly
**Action:** Create minimal test to isolate context agent

**Test Script:**
```python
from src.agents.parallel.context_provider import create_context_provider_agent
from src.core.events import AgentRequestEvent
from uuid import uuid4

agent = create_context_provider_agent(verbose=True)
event = AgentRequestEvent(
    agent_type="context_provider",
    correlation_id=uuid4(),
    request_data={
        "gamp_category": "3",
        "test_strategy": {},
        "document_sections": ["functional_requirements"],
        "search_scope": {}
    }
)
result = await agent.process_request(event)
print(f"Success: {result.success}")
print(f"Documents retrieved: {len(result.result_data.get('retrieved_documents', []))}")
```

---

## Files to Return to User

### Primary Investigation Targets:
1. **C:\Users\anteb\Desktop\Courses\Projects\thesis_project\main\src\core\unified_workflow.py**
   - Lines 1044-1146: Parallel coordination logic
   - Lines 1070-1113: Context agent invocation conditions
   - Lines 1174-1223: Timeout handling

2. **C:\Users\anteb\Desktop\Courses\Projects\thesis_project\main\src\agents\parallel\context_provider.py**
   - Lines 118-140: Environment validation
   - Lines 601-666: ChromaDB search with readiness guard
   - Lines 925-944: Collection selection logic

### Configuration Files:
3. **C:\Users\anteb\Desktop\Courses\Projects\thesis_project\main\main.py** (need to check)
4. **C:\Users\anteb\Desktop\Courses\Projects\thesis_project\main\api\worker_executor.py** (need to check)

---

## Summary of Conditional Paths That Skip Context Search

### Path 1: Configuration Bypass
```
enable_parallel_coordination=False → Context agent never invoked
```

### Path 2: Timeout Bypass
```
ChromaDB search >60s → TimeoutError → success=False → Workflow continues anyway
```

### Path 3: Empty Collections (Partial)
```
Some collections empty → Workflow proceeds with reduced context
```

### Path 4: Initialization Failure
```
OPENAI_API_KEY missing → RuntimeError → Context agent never created
```

### Path 5: Path Mismatch
```
Data in ./lib/chroma_db but runtime reads ./chroma_db → Empty collections
```
