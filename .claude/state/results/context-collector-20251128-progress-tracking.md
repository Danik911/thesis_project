# Context Collector Result - Real-Time Progress Tracking Research

## Agent Configuration
- **Agent**: context-collector
- **Task ID**: Ad-hoc research (not from PRP workflow)
- **Invoked**: 2025-11-28
- **Duration**: ~45 minutes
- **Status**: SUCCESS

## Task Understanding
Research best practices for implementing real-time progress tracking in a long-running (6-9 minute) pharmaceutical test generation workflow with multiple agent stages (categorization, planning, generation, validation). Current system uses 5-second polling; goal is to provide granular, real-time progress updates to improve UX while maintaining GAMP-5 compliance.

---

## Research Findings

### 1. Backend Progress Patterns Comparison

#### ✅ **RECOMMENDED: Server-Sent Events (SSE)**
**Why SSE for this use case:**
- **Unidirectional streaming** (server→client) - perfect for progress updates
- **Automatic reconnection** - browser handles dropped connections
- **Lower overhead** than WebSocket - no bidirectional handshake
- **HTTP/1.1 compatible** - works through corporate firewalls
- **Built-in FastAPI support** - `StreamingResponse` with async generators

**Pattern:**
```python
from fastapi.responses import StreamingResponse
import asyncio

async def progress_generator(job_id: str):
    """Async generator that yields SSE-formatted progress updates"""
    async for progress in get_job_progress_stream(job_id):
        # SSE format: "data: {json}\n\n"
        yield f"data: {json.dumps(progress)}\n\n"
    yield "event: complete\ndata: {\"status\": \"done\"}\n\n"

@app.get("/jobs/{job_id}/progress-stream")
async def stream_job_progress(job_id: str):
    return StreamingResponse(
        progress_generator(job_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )
```

**Frontend (React EventSource):**
```typescript
const eventSource = new EventSource(`/jobs/${jobId}/progress-stream`);

eventSource.onmessage = (event) => {
    const progress = JSON.parse(event.data);
    setWorkflowProgress(progress);
};

eventSource.addEventListener('complete', () => {
    eventSource.close();
});
```

**Production Library:** [sse-starlette](https://github.com/sysid/sse-starlette) - W3C compliant, auto-disconnect detection, graceful shutdown
```bash
uv add sse-starlette
```

#### ❌ **NOT RECOMMENDED: WebSocket**
- **Overkill** for one-way progress updates
- **Bidirectional overhead** unnecessary
- **More complex error handling** (ping/pong, manual reconnection)
- **Use case**: Chat applications, collaborative editing (NOT progress tracking)

#### ⚠️ **CURRENT: Polling (5s interval)**
**Problems:**
- **Delayed updates** - up to 5s lag
- **Resource waste** - 720 requests for 6-minute workflow
- **Poor UX** - feels unresponsive during critical stages
- **Database load** - constant SELECT queries

**Keep as fallback** - Some corporate networks block SSE

---

### 2. Worker-to-API Communication (Critical for Docker Architecture)

**Challenge:** Current architecture runs workflows in separate **Worker container**, not API container.

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Frontend  │─SSE──│ API Container│─???──│Worker Container│
│  (Next.js)  │      │  (FastAPI)   │      │ (LlamaIndex)  │
└─────────────┘      └──────────────┘      └─────────────┘
```

**Question:** How does Worker send progress to API for SSE streaming?

#### ✅ **RECOMMENDED: PostgreSQL NOTIFY/LISTEN**

**Why PostgreSQL:**
- **Already in stack** - No new infrastructure
- **Built-in Postgres feature** - NOTIFY/LISTEN channels
- **Async support** - psycopg3 async driver
- **GAMP-5 audit trail** - Progress events persist in database

**Architecture:**
```
Worker Container                  API Container                   Frontend
─────────────────                 ─────────────                   ────────
Workflow Step 1
  │
  ├─ UPDATE jobs SET progress='{"stage":"categorization","pct":20}'
  └─ NOTIFY progress_channel, '{"job_id":"abc","stage":"categorization","pct":20}'
                                      │
                                      │ LISTEN progress_channel
                                      ├─ Receive notification
                                      └─ SSE yield──────────────> EventSource updates UI
Workflow Step 2
  │
  ├─ UPDATE jobs SET progress='{"stage":"planning","pct":45}'
  └─ NOTIFY progress_channel, '{"job_id":"abc","stage":"planning","pct":45}'
                                      │
                                      └─ SSE yield──────────────> EventSource updates UI
```

**Implementation:**

**Worker (unified_workflow.py):**
```python
from psycopg import AsyncConnection
import json

class ProgressNotifier:
    """Helper to send progress updates via PostgreSQL NOTIFY"""

    def __init__(self, conn: AsyncConnection, job_id: str):
        self.conn = conn
        self.job_id = job_id

    async def notify_progress(self, stage: str, progress_pct: int, message: str):
        """Send progress update to PostgreSQL channel"""
        payload = {
            "job_id": self.job_id,
            "stage": stage,
            "progress_pct": progress_pct,
            "message": message,
            "timestamp": datetime.now(UTC).isoformat()
        }

        # GAMP-5: Update database for audit trail
        await self.conn.execute(
            "UPDATE jobs SET progress = $1, updated_at = NOW() WHERE job_id = $2",
            (json.dumps(payload), self.job_id)
        )

        # Real-time: Notify listening API instances
        await self.conn.execute(
            "NOTIFY progress_updates, $1",
            (json.dumps(payload),)
        )

# In UnifiedWorkflow
async def categorization_step(self, ctx: Context, ev: StartEvent):
    notifier = await safe_context_get(ctx, "progress_notifier")

    await notifier.notify_progress(
        stage="categorization",
        progress_pct=10,
        message="Analyzing URS document for GAMP-5 category..."
    )

    # ... workflow logic ...

    await notifier.notify_progress(
        stage="categorization",
        progress_pct=25,
        message=f"Categorized as GAMP-{category} (confidence: {confidence:.0%})"
    )
```

**API (app.py):**
```python
from psycopg import AsyncConnection
from sse_starlette.sse import EventSourceResponse
import asyncio

async def progress_event_generator(job_id: str, db_conn: AsyncConnection):
    """
    Listen to PostgreSQL NOTIFY channel and yield SSE events.

    GAMP-5 Compliance:
    - All progress events logged to Langfuse
    - Database audit trail maintained
    - NO FALLBACK LOGIC - errors propagate explicitly
    """
    # Subscribe to progress channel
    await db_conn.execute(f"LISTEN progress_updates")

    langfuse = get_langfuse_client()
    span = None
    if langfuse:
        span = langfuse.start_span(
            name="sse_progress_stream",
            metadata={"job_id": job_id}
        )

    try:
        async for notify in db_conn.notifies():
            payload = json.loads(notify.payload)

            # Filter for this job_id
            if payload["job_id"] != job_id:
                continue

            # Log to Langfuse for compliance
            if span:
                span.event(
                    name="progress_update",
                    input=payload
                )

            # Yield SSE event
            yield {
                "event": "progress",
                "data": json.dumps(payload)
            }

            # Stop streaming when workflow completes
            if payload.get("stage") == "complete":
                break

    except asyncio.CancelledError:
        # Client disconnected - clean up
        await db_conn.execute("UNLISTEN progress_updates")
        if span:
            span.update(output={"status": "client_disconnected"})
    finally:
        if span:
            span.end()
        if langfuse:
            langfuse.flush()

@app.get("/jobs/{job_id}/progress-stream")
async def stream_progress(
    job_id: str,
    db_conn: AsyncConnection = Depends(get_db_conn),
    user: CurrentUserDep = None
):
    """
    SSE endpoint for real-time workflow progress.

    NO FALLBACK LOGIC: Job must exist, user must be authorized.
    """
    # Verify job exists and user authorized
    job = await db_conn.fetchrow(
        "SELECT user_id FROM jobs WHERE job_id = $1", job_id
    )
    if not job:
        raise HTTPException(404, f"Job {job_id} not found")
    if job["user_id"] != user.sub:
        raise HTTPException(403, "Not authorized")

    return EventSourceResponse(
        progress_event_generator(job_id, db_conn),
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )
```

**Required Library:**
```bash
uv add sse-starlette
uv add psycopg[binary]  # Already installed
```

**Database Migration:**
```sql
-- Add progress column to jobs table
ALTER TABLE jobs ADD COLUMN progress JSONB;

-- Index for faster queries (optional)
CREATE INDEX idx_jobs_progress ON jobs USING GIN (progress);
```

#### Alternative: Redis Pub/Sub (if Redis added later)

**Pattern:**
```python
# Worker
await redis.publish(
    "progress_updates",
    json.dumps({"job_id": job_id, "stage": "...", "pct": 45})
)

# API
async def redis_progress_generator(job_id: str):
    pubsub = redis.pubsub()
    await pubsub.subscribe("progress_updates")
    async for message in pubsub.listen():
        if message["type"] == "message":
            payload = json.loads(message["data"])
            if payload["job_id"] == job_id:
                yield {"event": "progress", "data": message["data"]}
```

**Libraries:**
```bash
uv add redis[hiredis]
```

**Pros:** Faster than PostgreSQL NOTIFY (in-memory)
**Cons:** Additional infrastructure, no persistence, no audit trail

---

### 3. LlamaIndex Workflow Streaming Integration

**Built-in Feature:** LlamaIndex 0.12.0+ workflows have native event streaming via `Context.write_event_to_stream()`

**Official Docs:** [Streaming events - LlamaIndex](https://docs.llamaindex.ai/en/stable/understanding/workflows/stream/)

**Pattern:**
```python
from llama_index.core.workflow import Event

class ProgressEvent(Event):
    """Custom event for streaming progress updates"""
    stage: str
    progress_pct: int
    message: str
    job_id: str

class UnifiedWorkflow(Workflow):
    @step
    async def categorization_step(self, ctx: Context, ev: StartEvent) -> GAMPCategorizationEvent:
        # Stream progress to frontend via ctx
        ctx.write_event_to_stream(
            ProgressEvent(
                stage="categorization",
                progress_pct=10,
                message="Analyzing URS document...",
                job_id=self.job_id
            )
        )

        # ... GAMP-5 categorization logic ...

        ctx.write_event_to_stream(
            ProgressEvent(
                stage="categorization",
                progress_pct=25,
                message=f"Categorized as GAMP-{category}",
                job_id=self.job_id
            )
        )

        return GAMPCategorizationEvent(...)
```

**Worker Integration (worker.py):**
```python
async def process_job_worker(
    job_queue: asyncio.Queue,
    job_repository: dict,
    job_lock: asyncio.Lock,
    db_job_repo: PostgresJobRepository
):
    """
    Background worker that runs workflows and streams progress.

    Integration:
    1. LlamaIndex workflow streams to ctx
    2. Worker captures stream events
    3. Worker sends to PostgreSQL NOTIFY
    4. API LISTENs and forwards via SSE to frontend
    """
    while True:
        job_id = await job_queue.get()

        # Initialize workflow with progress notifier
        workflow = UnifiedWorkflow(timeout=600, verbose=True)

        # Setup database connection for NOTIFY
        db_conn = await get_async_db_connection()
        notifier = ProgressNotifier(db_conn, job_id)

        # Run workflow and capture stream
        handler = workflow.run(
            urs_content=urs_content,
            job_id=job_id
        )

        # Stream progress events from workflow to PostgreSQL
        async for event in handler.stream_events():
            if isinstance(event, ProgressEvent):
                # Forward to PostgreSQL NOTIFY channel
                await notifier.notify_progress(
                    stage=event.stage,
                    progress_pct=event.progress_pct,
                    message=event.message
                )

                # Also log to Langfuse for audit
                langfuse = get_langfuse_client()
                if langfuse:
                    langfuse.span(
                        name="workflow_progress",
                        input=event.model_dump()
                    )

        # Get final result
        result = await handler
```

**Workflow Progress Stages:**

For pharmaceutical 6-9 minute workflow:
```python
# Define progress checkpoints across multi-agent stages
PROGRESS_STAGES = {
    "categorization": {
        "start": 0,
        "analyzing_urs": 10,
        "ai_categorization": 20,
        "confidence_check": 25,
        "complete": 30
    },
    "planning": {
        "start": 30,
        "context_gathering": 40,
        "sme_analysis": 50,
        "test_plan_generation": 60,
        "complete": 70
    },
    "generation": {
        "start": 70,
        "oq_generation": 80,
        "validation": 90,
        "complete": 95
    },
    "finalization": {
        "start": 95,
        "audit_trail": 97,
        "storage": 99,
        "complete": 100
    }
}
```

**Usage in workflow:**
```python
@step
async def planning_step(self, ctx: Context, ev: GAMPCategorizationEvent):
    ctx.write_event_to_stream(ProgressEvent(
        stage="planning",
        progress_pct=PROGRESS_STAGES["planning"]["start"],
        message="Starting test planning phase..."
    ))

    # Context gathering
    ctx.write_event_to_stream(ProgressEvent(
        stage="planning",
        progress_pct=PROGRESS_STAGES["planning"]["context_gathering"],
        message="Gathering domain context from RAG..."
    ))

    # ... actual work ...
```

---

### 4. React Progress Bar Libraries

**Comparison for 6-9 minute determinate progress:**

| Library | Best For | Pros | Cons | Recommendation |
|---------|----------|------|------|----------------|
| **[Material UI (MUI)](https://mui.com/material-ui/react-progress/)** | Production apps | - Proven at scale<br>- Determinate/indeterminate<br>- Accessible<br>- Built-in animations | - Large bundle (if not already using MUI) | ✅ **RECOMMENDED** |
| **[React Aria (Adobe)](https://react-spectrum.adobe.com/react-aria/ProgressBar.html)** | Accessibility focus | - ARIA compliant<br>- Locale-aware formatting<br>- Headless (bring your own styles) | - More setup required | ✅ Good alternative |
| **[HeroUI/NextUI](https://www.heroui.com/docs/components/progress)** | Modern designs | - Beautiful defaults<br>- formatOptions for custom display | - Newer library (less battle-tested) | ⚠️ Consider for greenfield |
| **[react-component/progress](https://github.com/react-component/progress)** | Minimalist | - Tiny bundle<br>- SVG-based<br>- Circular + linear | - Less features | ⚠️ If bundle size critical |

#### ✅ **RECOMMENDED: Material UI Progress**

**Installation:**
```bash
cd main/frontend
npm install @mui/material @emotion/react @emotion/styled
```

**Implementation (components/WorkflowProgress.tsx):**
```typescript
import { LinearProgress, Box, Typography, Stepper, Step, StepLabel } from '@mui/material';
import { useEffect, useState } from 'react';

interface ProgressUpdate {
    stage: string;
    progress_pct: number;
    message: string;
    timestamp: string;
}

const WORKFLOW_STEPS = [
    { key: 'categorization', label: 'GAMP-5 Categorization' },
    { key: 'planning', label: 'Test Planning' },
    { key: 'generation', label: 'Test Generation' },
    { key: 'validation', label: 'Validation & Storage' }
];

export function WorkflowProgress({ jobId }: { jobId: string }) {
    const [progress, setProgress] = useState<ProgressUpdate | null>(null);
    const [eventSource, setEventSource] = useState<EventSource | null>(null);

    useEffect(() => {
        // Connect to SSE endpoint
        const apiUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8080';
        const es = new EventSource(`${apiUrl}/jobs/${jobId}/progress-stream`, {
            withCredentials: true
        });

        es.addEventListener('progress', (event) => {
            const data: ProgressUpdate = JSON.parse(event.data);
            setProgress(data);
        });

        es.addEventListener('complete', () => {
            es.close();
        });

        es.onerror = (error) => {
            console.error('[SSE] Connection error:', error);
            es.close();
            // Fallback to polling
            // TODO: Implement polling fallback for corporate networks
        };

        setEventSource(es);

        return () => {
            es.close();
        };
    }, [jobId]);

    if (!progress) {
        return (
            <Box>
                <LinearProgress variant="indeterminate" />
                <Typography variant="caption">Initializing workflow...</Typography>
            </Box>
        );
    }

    const activeStep = WORKFLOW_STEPS.findIndex(step => step.key === progress.stage);

    return (
        <Box sx={{ width: '100%' }}>
            {/* Stepper for high-level stages */}
            <Stepper activeStep={activeStep} sx={{ mb: 3 }}>
                {WORKFLOW_STEPS.map((step) => (
                    <Step key={step.key}>
                        <StepLabel>{step.label}</StepLabel>
                    </Step>
                ))}
            </Stepper>

            {/* Determinate progress bar */}
            <Box sx={{ mb: 1 }}>
                <LinearProgress
                    variant="determinate"
                    value={progress.progress_pct}
                    sx={{ height: 10, borderRadius: 5 }}
                />
            </Box>

            {/* Progress details */}
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2" color="text.secondary">
                    {progress.message}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                    {progress.progress_pct}%
                </Typography>
            </Box>

            {/* ALCOA+ compliance: Show timestamp */}
            <Typography variant="caption" color="text.disabled">
                Last updated: {new Date(progress.timestamp).toLocaleTimeString()}
            </Typography>
        </Box>
    );
}
```

**Best Practices for 6-9 Minute Operations:**

1. **Use Determinate Progress** (not indeterminate)
   - Gives users time estimation
   - Reduces anxiety ("is it still working?")
   - Shows measurable progress

2. **Combine Stepper + Progress Bar**
   - Stepper: High-level stages (categorization, planning, etc.)
   - Progress bar: Granular progress within stage (10% → 25%)

3. **Show Detailed Status Messages**
   ```
   [███████████░░░░░░░░] 45%
   Gathering domain context from RAG (3 of 7 documents)...
   Last updated: 14:32:15
   ```

4. **Handle SSE Disconnections**
   - Automatic reconnection (EventSource does this)
   - Fallback to polling if SSE blocked by network
   - Show connection status indicator

5. **ALCOA+ Compliance**
   - Display exact timestamps for audit trail
   - Show which agent/stage is active
   - Log all progress events to Langfuse

---

### 5. Langfuse Integration Strategy

**⚠️ CRITICAL: Langfuse is NOT for real-time progress tracking**

**Why:**
- **15-30 second ingestion delay** - traces/spans not immediately queryable
- **API is for analysis**, not live monitoring
- **Polling Langfuse API** would be worse than current job status polling

**Correct Usage:**

#### Use Langfuse for AUDIT TRAIL, NOT real-time updates

**Pattern:**
```python
# Worker: Log progress events to Langfuse
async def stream_progress_with_audit(workflow_handler, notifier, job_id):
    """
    Dual-stream pattern:
    1. Real-time: PostgreSQL NOTIFY → SSE → Frontend
    2. Audit: Langfuse trace → Compliance dashboard
    """
    langfuse = get_langfuse_client()
    trace = None

    if langfuse:
        trace = langfuse.start_trace(
            name="test_generation_workflow",
            input={"job_id": job_id},
            metadata={"gamp_category": "5"}
        )

    async for event in workflow_handler.stream_events():
        if isinstance(event, ProgressEvent):
            # REAL-TIME: Send to PostgreSQL for SSE
            await notifier.notify_progress(
                stage=event.stage,
                progress_pct=event.progress_pct,
                message=event.message
            )

            # AUDIT TRAIL: Log to Langfuse
            if trace:
                trace.span(
                    name=f"workflow_stage_{event.stage}",
                    input={
                        "stage": event.stage,
                        "progress_pct": event.progress_pct,
                        "message": event.message
                    },
                    metadata={
                        "alcoa_timestamp": event.timestamp,
                        "alcoa_attributable": True,
                        "alcoa_contemporaneous": True
                    }
                )

    if trace:
        trace.end()
        langfuse.flush()
```

**Post-Workflow Analysis:**

Use Langfuse Python SDK to query completed workflows:

```python
from langfuse import Langfuse

langfuse = Langfuse()

# Get trace for completed job
trace = langfuse.api.trace.get("trace-id-from-job-record")

# Extract all progress spans
progress_spans = [
    obs for obs in trace.observations
    if obs.name.startswith("workflow_stage_")
]

# Calculate stage durations for optimization
stage_durations = {
    span.name: (span.end_time - span.start_time).total_seconds()
    for span in progress_spans
}

# Example: "categorization took 45s, planning took 120s"
```

**Compliance Dashboard (Separate from Real-Time Progress):**

```typescript
// Fetch Langfuse trace AFTER workflow completes
async function fetchAuditTrail(jobId: string) {
    const job = await fetch(`/jobs/${jobId}`).then(r => r.json());
    const traceId = job.langfuse_trace_id;

    // Query Langfuse via backend proxy (not directly from frontend)
    const trace = await fetch(`/api/langfuse/traces/${traceId}`)
        .then(r => r.json());

    // Display ALCOA+ compliant audit trail
    return trace.observations.map(obs => ({
        stage: obs.name,
        timestamp: obs.start_time,
        duration: obs.end_time - obs.start_time,
        metadata: obs.metadata
    }));
}
```

---

### 6. Pharmaceutical Compliance Considerations

#### GAMP-5 Requirements for Progress Tracking

**Data Integrity (ALCOA+):**

| Principle | Implementation |
|-----------|----------------|
| **Attributable** | Log user_id, job_id with each progress event |
| **Legible** | Human-readable messages ("Analyzing URS...") |
| **Contemporaneous** | ISO 8601 timestamps (UTC) on every event |
| **Original** | PostgreSQL NOTIFY payload = source of truth |
| **Accurate** | NO FALLBACK LOGIC - progress must reflect actual workflow state |
| **Complete** | All stages logged (start, intermediate, complete, errors) |
| **Consistent** | Same progress_pct calculation across all agents |
| **Enduring** | Progress persisted in jobs.progress JSONB column |
| **Available** | SSE stream + database query both available |

#### NO FALLBACK LOGIC Compliance

**❌ FORBIDDEN:**
```python
# BAD: Fake progress when workflow stalls
if time_since_last_update > 30:
    yield {"progress_pct": last_pct + 5, "message": "Still processing..."}
```

**✅ REQUIRED:**
```python
# GOOD: Expose actual state, even if stalled
if time_since_last_update > 30:
    raise WorkflowTimeoutError(
        f"No progress for 30s. Last stage: {last_stage}, "
        f"Last progress: {last_pct}%. Check Langfuse trace."
    )
```

**Progress Calculation Must Be Deterministic:**

```python
def calculate_progress(stage: str, substage: str) -> int:
    """
    Deterministic progress calculation based on workflow state.

    NO FALLBACK LOGIC: If stage unknown, raise error (don't return 0).
    """
    if stage not in PROGRESS_STAGES:
        raise ValueError(
            f"Unknown workflow stage: {stage}. "
            f"Valid stages: {list(PROGRESS_STAGES.keys())}"
        )

    if substage not in PROGRESS_STAGES[stage]:
        raise ValueError(
            f"Unknown substage: {substage} in stage {stage}. "
            f"Valid substages: {list(PROGRESS_STAGES[stage].keys())}"
        )

    return PROGRESS_STAGES[stage][substage]
```

#### Audit Trail Requirements

**Database Schema:**
```sql
-- jobs table already has progress column (JSONB)
-- Add index for audit queries
CREATE INDEX idx_jobs_progress_audit ON jobs ((progress->>'stage'));

-- Audit query example
SELECT
    job_id,
    progress->>'stage' as stage,
    progress->>'progress_pct' as progress_pct,
    progress->>'message' as message,
    progress->>'timestamp' as event_timestamp,
    updated_at as db_timestamp
FROM jobs
WHERE job_id = 'abc123'
ORDER BY (progress->>'timestamp')::timestamp;
```

**Langfuse Trace Structure:**
```
Trace: test_generation_job_abc123
├─ Span: workflow_stage_categorization (45s)
│  ├─ Event: progress_update (t=0s, pct=10)
│  ├─ Event: progress_update (t=20s, pct=20)
│  └─ Event: progress_update (t=45s, pct=30)
├─ Span: workflow_stage_planning (120s)
│  ├─ Event: progress_update (t=45s, pct=40)
│  ├─ Event: progress_update (t=90s, pct=50)
│  └─ Event: progress_update (t=165s, pct=70)
└─ Span: workflow_stage_generation (90s)
   └─ Event: progress_update (t=255s, pct=100)
```

---

## Implementation Gotchas

### 1. **SSE Buffering Issues**

**Problem:** Nginx/Apache buffers SSE responses, delaying updates

**Solution:**
```nginx
# nginx.conf
location /jobs {
    proxy_pass http://api:8000;
    proxy_buffering off;  # Critical for SSE
    proxy_cache off;
    proxy_set_header Connection '';
    proxy_http_version 1.1;
    chunked_transfer_encoding off;
}
```

**FastAPI headers:**
```python
headers={
    "Cache-Control": "no-cache",
    "X-Accel-Buffering": "no",  # Tell nginx to not buffer
}
```

### 2. **PostgreSQL Connection Pooling**

**Problem:** NOTIFY/LISTEN requires dedicated connection (can't use pooled connection)

**Solution:**
```python
# Create separate connection for LISTEN (don't return to pool)
async def get_notify_connection():
    """
    Dedicated connection for PostgreSQL LISTEN.

    NOTE: This connection is NOT pooled - it stays open for SSE duration.
    """
    conn = await psycopg.AsyncConnection.connect(DATABASE_URL)
    return conn

@app.get("/jobs/{job_id}/progress-stream")
async def stream_progress(job_id: str):
    # Dedicated connection (not from pool)
    conn = await get_notify_connection()
    try:
        return EventSourceResponse(
            progress_event_generator(job_id, conn)
        )
    finally:
        await conn.close()
```

### 3. **EventSource Browser Limits**

**Problem:** Browsers limit concurrent EventSource connections (typically 6 per domain)

**Solution:**
- Close EventSource when workflow completes
- Reuse same connection for multiple progress updates
- Consider HTTP/2 (higher connection limit)

```typescript
useEffect(() => {
    const es = new EventSource(`/jobs/${jobId}/progress-stream`);

    es.addEventListener('complete', () => {
        es.close();  // Critical: Free up browser connection
    });

    return () => {
        es.close();  // Cleanup on component unmount
    };
}, [jobId]);
```

### 4. **Clerk JWT Token Expiration in SSE**

**Problem:** SSE connection lasts 6-9 minutes, Clerk JWT expires in 60 seconds

**Solution:**
```python
@app.get("/jobs/{job_id}/progress-stream")
async def stream_progress(
    job_id: str,
    user: CurrentUserDep  # Validates JWT at connection start
):
    # After initial auth, SSE stream continues without re-validating
    # This is acceptable for progress updates (read-only, low security risk)

    # For HIGH-SECURITY use cases, periodically check job ownership:
    async def progress_generator_with_auth_check():
        last_auth_check = time.time()
        async for progress in progress_event_generator(job_id):
            # Re-check authorization every 60 seconds
            if time.time() - last_auth_check > 60:
                job = await db.get_job(job_id)
                if job.user_id != user.sub:
                    raise HTTPException(403, "Authorization expired")
                last_auth_check = time.time()

            yield progress
```

### 5. **CORS for SSE**

**Problem:** EventSource requires CORS headers

**Solution (already implemented in app.py):**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,  # Critical for EventSource withCredentials
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Frontend:**
```typescript
// MUST use withCredentials for Clerk JWT cookies
const es = new EventSource(`${apiUrl}/progress-stream`, {
    withCredentials: true
});
```

---

## Recommended Architecture

### Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                           Frontend (Next.js)                        │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  WorkflowProgress Component                                 │    │
│  │  ┌──────────────────────────────────────────────────────┐  │    │
│  │  │ EventSource → GET /jobs/{id}/progress-stream        │  │    │
│  │  │   ↓ SSE events                                        │  │    │
│  │  │ [███████████░░░░░░░] 45%                            │  │    │
│  │  │ Gathering domain context (3/7 documents)...          │  │    │
│  │  │ Last updated: 14:32:15                               │  │    │
│  │  └──────────────────────────────────────────────────────┘  │    │
│  └────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
                              │ SSE (HTTP/1.1 long-lived connection)
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                       API Container (FastAPI)                       │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  @app.get("/jobs/{id}/progress-stream")                    │    │
│  │  async def stream_progress():                               │    │
│  │      conn = await get_notify_connection()                   │    │
│  │      await conn.execute("LISTEN progress_updates")          │    │
│  │      async for notify in conn.notifies():                   │    │
│  │          payload = json.loads(notify.payload)               │    │
│  │          if payload["job_id"] == job_id:                    │    │
│  │              yield SSE(data=payload)  # Stream to frontend  │    │
│  └────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
                              ↑ PostgreSQL NOTIFY
                              │
┌─────────────────────────────────────────────────────────────────────┐
│                    PostgreSQL Database                              │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  Channel: progress_updates                                  │    │
│  │  Payload: {"job_id":"abc","stage":"planning","pct":45}      │    │
│  ├────────────────────────────────────────────────────────────┤    │
│  │  Table: jobs                                                 │    │
│  │  ┌────────┬─────────┬──────────────────────────────────┐   │    │
│  │  │ job_id │ status  │ progress (JSONB)                 │   │    │
│  │  ├────────┼─────────┼──────────────────────────────────┤   │    │
│  │  │ abc123 │RUNNING  │{"stage":"planning","pct":45,...} │   │    │
│  │  └────────┴─────────┴──────────────────────────────────┘   │    │
│  └────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
                              ↑ UPDATE + NOTIFY
                              │
┌─────────────────────────────────────────────────────────────────────┐
│                   Worker Container (LlamaIndex)                     │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  UnifiedWorkflow                                            │    │
│  │  ┌────────────────────────────────────────────────────┐    │    │
│  │  │ @step categorization_step():                       │    │    │
│  │  │     ctx.write_event_to_stream(                     │    │    │
│  │  │         ProgressEvent(stage="categorization",      │    │    │
│  │  │                       pct=20, msg="...")           │    │    │
│  │  │     )                                               │    │    │
│  │  └────────────────────────────────────────────────────┘    │    │
│  │                         ↓                                    │    │
│  │  ┌────────────────────────────────────────────────────┐    │    │
│  │  │ Worker: async for event in handler.stream_events():│    │    │
│  │  │     if isinstance(event, ProgressEvent):           │    │    │
│  │  │         # 1. Update database                       │    │    │
│  │  │         await db.execute(                          │    │    │
│  │  │             "UPDATE jobs SET progress=$1",         │    │    │
│  │  │             json.dumps(event.dict())               │    │    │
│  │  │         )                                           │    │    │
│  │  │         # 2. Notify API containers                 │    │    │
│  │  │         await db.execute(                          │    │    │
│  │  │             "NOTIFY progress_updates, $1",         │    │    │
│  │  │             json.dumps(event.dict())               │    │    │
│  │  │         )                                           │    │    │
│  │  │         # 3. Log to Langfuse (audit trail)         │    │    │
│  │  │         langfuse.span(input=event.dict())          │    │    │
│  │  └────────────────────────────────────────────────────┘    │    │
│  └────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Migration Path from Current Polling

### Phase 1: Add PostgreSQL NOTIFY Support (No Frontend Changes)

**Duration:** 1-2 days

**Steps:**
1. Add `progress` JSONB column to jobs table
2. Update `worker.py` to send NOTIFY on progress updates
3. Keep existing polling working (no breaking changes)

**Files Modified:**
- `main/api/models.py` - Add progress field to JobRecord
- `main/api/worker.py` - Add ProgressNotifier class
- `main/src/core/unified_workflow.py` - Add ctx.write_event_to_stream()
- Database migration script

### Phase 2: Add SSE Endpoint (Parallel to Polling)

**Duration:** 1 day

**Steps:**
1. Add `/jobs/{job_id}/progress-stream` SSE endpoint
2. Install sse-starlette library
3. Implement progress_event_generator with LISTEN

**Files Modified:**
- `main/api/app.py` - New SSE endpoint
- `requirements.txt` / `pyproject.toml` - Add sse-starlette

### Phase 3: Frontend SSE Integration

**Duration:** 2-3 days

**Steps:**
1. Create WorkflowProgress component with EventSource
2. Add Material UI progress bar
3. Keep polling as fallback (detect SSE failures)
4. A/B test with select users

**Files Modified:**
- `main/frontend/components/WorkflowProgress.tsx` (new)
- `main/frontend/pages/generate.tsx` - Replace polling hook
- `package.json` - Add @mui/material

### Phase 4: Deprecate Polling (Keep as Fallback)

**Duration:** 1 week monitoring

**Steps:**
1. Monitor SSE success rate in production
2. If SSE success > 95%, make it primary
3. Keep polling as fallback for corporate networks
4. Add toggle in UI: "Use real-time updates (SSE)" checkbox

---

## Next Agent Guidance (for task-executor)

### Implementation Checklist

**Backend (Python):**
- [ ] Install sse-starlette: `uv add sse-starlette`
- [ ] Add progress JSONB column to jobs table
- [ ] Create ProgressNotifier class in worker.py
- [ ] Add ctx.write_event_to_stream() calls in unified_workflow.py
- [ ] Implement /jobs/{id}/progress-stream SSE endpoint in app.py
- [ ] Add PostgreSQL LISTEN connection management
- [ ] Configure nginx to disable buffering for SSE

**Frontend (TypeScript/React):**
- [ ] Install Material UI: `npm install @mui/material @emotion/react @emotion/styled`
- [ ] Create WorkflowProgress component with EventSource
- [ ] Add SSE error handling and polling fallback
- [ ] Integrate with existing generate.tsx page
- [ ] Add ALCOA+ timestamp display

**Testing:**
- [ ] Unit test ProgressNotifier.notify_progress()
- [ ] Integration test SSE endpoint with mock NOTIFY
- [ ] Frontend test EventSource connection/reconnection
- [ ] Load test: 10 concurrent SSE streams
- [ ] Test SSE through nginx proxy

**Compliance:**
- [ ] Verify all progress events logged to Langfuse
- [ ] Validate ALCOA+ principles in progress payloads
- [ ] Ensure NO FALLBACK LOGIC in progress calculations
- [ ] Test audit trail query performance

---

## Required Libraries/Versions

### Backend (Python)
```toml
[tool.poetry.dependencies]
sse-starlette = "^2.1.3"  # Production SSE library
psycopg = {extras = ["binary"], version = "^3.2.1"}  # Already installed
```

**Installation:**
```bash
cd main
uv add sse-starlette
```

**Version Notes:**
- sse-starlette 2.1.3+ - Auto disconnect detection, graceful shutdown
- psycopg 3.2.1+ - Async NOTIFY/LISTEN support

### Frontend (TypeScript)
```json
{
  "dependencies": {
    "@mui/material": "^6.1.6",
    "@emotion/react": "^11.13.5",
    "@emotion/styled": "^11.13.5"
  }
}
```

**Installation:**
```bash
cd main/frontend
npm install @mui/material @emotion/react @emotion/styled
```

**Version Notes:**
- MUI 6.x - Latest stable (React 18 compatible)
- Emotion 11.x - Peer dependency for MUI styling

### Database Migration
```sql
-- Add progress column (run via Alembic or direct SQL)
ALTER TABLE jobs ADD COLUMN progress JSONB DEFAULT '{}';

-- Optional: Index for faster queries
CREATE INDEX idx_jobs_progress_stage ON jobs ((progress->>'stage'));
```

---

## Files Referenced

### Official Documentation
- [LlamaIndex Workflow Streaming](https://docs.llamaindex.ai/en/stable/understanding/workflows/stream/)
- [LlamaIndex Event Streaming Video](https://www.youtube.com/watch?v=hf3_fuVdrpA)
- [Material UI Progress](https://mui.com/material-ui/react-progress/)
- [React Aria ProgressBar](https://react-spectrum.adobe.com/react-aria/ProgressBar.html)
- [FastAPI Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)
- [Langfuse Python SDK - Query Traces](https://langfuse.com/docs/query-traces)

### GitHub Examples
- [FastAPI SSE with Redis Pub/Sub Gist](https://gist.github.com/lbatteau/1bc7ae630d5b7844d58f038085590f97)
- [FastAPI Background Download SSE Gist](https://gist.github.com/bob-ross27/9089b23fe4e1d5bdede2a3c5386d6bea)
- [PostgreSQL NOTIFY/LISTEN SSE Example](https://github.com/v0id-user/Postgres-Reactive-SSE-Example)
- [sse-starlette Library](https://github.com/sysid/sse-starlette)
- [FastAPI SSE Event Streaming with Streamlit](https://github.com/sarthakkaushik/FASTAPI-SSE-Event-Streaming-with-Streamlit)

### Articles & Tutorials
- [Streaming AI Agent Responses with SSE (Medium)](https://akanuragkumar.medium.com/streaming-ai-agents-responses-with-server-sent-events-sse-a-technical-case-study-f3ac855d0755)
- [Server-Sent Events in FastAPI using Redis Pub/Sub (Deepdesk)](https://medium.com/deepdesk/server-sent-events-in-fastapi-using-redis-pub-sub-eba1dbfe8031)
- [Building Notifications System with SSE (Medium)](https://medium.com/@davidrp1996/bulding-a-notifications-system-wih-server-sent-events-sse-using-fastapi-and-redis-6eafdf7cf7fb)
- [Real-time Updates from Postgres using NOTIFY/LISTEN](https://tom.catshoek.dev/posts/postgres-sse/)
- [Deep Dive into LlamaIndex Workflow (Towards Data Science)](https://towardsdatascience.com/deep-dive-into-llamaindex-workflow-event-driven-llm-architecture-8011f41f851a/)
- [Build LLM Web App: FastAPI Background Tasks & SSE (DEV)](https://dev.to/zachary62/build-an-llm-web-app-in-python-from-scratch-part-4-fastapi-background-tasks-sse-21g4)

### Stack Overflow / Forums
- [Listen to PostgreSQL NOTIFY in FastAPI](https://stackoverflow.com/questions/74867151/listen-to-postgresql-notify-channel-in-fastapi)
- [How to trigger SSE with FastAPI](https://stackoverflow.com/questions/79418087/how-to-trigger-a-sse-with-fastapi)

---

## Summary & Recommendations

### ✅ **RECOMMENDED ARCHITECTURE**

**Pattern:** PostgreSQL NOTIFY/LISTEN + SSE + Material UI

**Why:**
1. **No new infrastructure** - Uses existing PostgreSQL
2. **Real-time updates** - Sub-second latency vs 5s polling
3. **GAMP-5 compliant** - Full audit trail in database + Langfuse
4. **Battle-tested** - SSE proven at scale, MUI used by thousands of apps
5. **Graceful degradation** - Falls back to polling if SSE blocked

**Architecture:**
```
LlamaIndex Workflow (ctx.write_event_to_stream)
    ↓
Worker (captures stream, sends PostgreSQL NOTIFY)
    ↓
PostgreSQL (progress_updates channel)
    ↓
API (LISTEN, converts to SSE)
    ↓
Frontend (EventSource, Material UI Progress)
```

**Effort Estimate:**
- Backend: 3-4 days (ProgressNotifier + SSE endpoint)
- Frontend: 2-3 days (WorkflowProgress component)
- Testing: 2 days (SSE edge cases, nginx config)
- **Total: 7-9 days** (1.5 - 2 sprints)

### 🎯 **SUCCESS CRITERIA**

- [ ] Progress updates visible within 500ms of workflow stage change
- [ ] SSE connection survives 6-9 minute workflow duration
- [ ] All progress events logged to Langfuse (ALCOA+ compliance)
- [ ] Polling fallback works if SSE blocked by corporate network
- [ ] NO FALLBACK LOGIC violations = 0
- [ ] User can see exact progress percentage (not just spinner)
- [ ] Nginx buffering disabled for SSE endpoints

---

**Status:** RESEARCH COMPLETE - Ready for implementation by task-executor
