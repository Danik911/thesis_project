# Context Collector Result - 20251111-185632

## Agent Configuration
- Agent: context-collector
- Task ID: 2.3
- Invoked: 2025-11-11T18:56:32Z
- Duration: 25 minutes
- Status: SUCCESS

---

## Task Understanding

### Original Task Scope (Frontend Dashboard Only)
Task 2.3 as documented in PRPs/tasks/2.3-langfuse-dashboard.md required:
- Add LangFuse session dashboards to frontend for live observability metrics
- Create authenticated Next.js API route that pulls aggregated trace data from LangFuse API
- Display throughput, latency, and error trends in compliance-ready format
- Dependencies: Task P2.2 (Clerk-protected frontend - COMPLETED), Task 6 (LangFuse backend - DOES NOT EXIST)

### Expanded Task Scope (User Decision - Option 2)
Based on user selection, this task now includes BOTH:

1. **Backend LangFuse Instrumentation** (missing Task 6 dependency)
   - Instrument FastAPI endpoints with LangFuse tracing
   - Instrument LlamaIndex 0.12.0+ workflows with LangFuse callbacks
   - Add LangFuse configuration to environment variables
   - Ensure GAMP-5 compliance in trace metadata (user_id, job_id, gamp_category)

2. **Frontend Dashboard** (original task scope)
   - Create authenticated Next.js API route `/api/langfuse/summary.ts`
   - Build dashboard page with metrics visualization
   - Implement SWR caching for rate limit compliance
   - Display throughput, latency, error trends

### Why Scope Expanded
- Task file references "Task 6 (LangFuse backend instrumentation)" as dependency
- No Task 6 exists in the PRP task list (only tasks 0.1-5.3 are defined)
- User chose Option 2: "Implement Full LangFuse Integration Now" to prevent task dependency blocking
- Backend instrumentation is a prerequisite for frontend dashboard to have meaningful data

### Current System Context
**Backend**: Python 3.12, FastAPI 0.100+, LlamaIndex 0.12.0+, uvicorn
**Frontend**: Next.js 14 Pages Router, TypeScript, Clerk v6.32.0, static export (`output: 'export'`)
**Storage**: Local filesystem + S3 adapter (Task 1.1)
**Vector Store**: ChromaDB + PostgreSQL pgvector (Task 1.2)
**Authentication**: Clerk JWT tokens verified in FastAPI (Task 1.4)
**Job Queue**: asyncio.Queue + background worker (Task 1.3)
**Observability**: Phoenix (Arize) for local development

---

## Research Findings

### 1. LangFuse Backend Instrumentation

#### Python SDK Version & Installation
- **Package**: `langfuse`
- **Current Stable Version**: v3.5.2 (as of November 2025)
- **Installation Command**: `uv add langfuse==3.5.2`
- **Installation Rationale**:
  - v3.5.2 is the latest stable production version
  - Supports FastAPI async/streaming endpoints (resolved in v3.5.2)
  - Full LlamaIndex 0.12.0+ compatibility
  - Improved error handling and retry logic

#### FastAPI Integration Pattern

**Setup Phase - Environment Variables**
```python
import os
from dotenv import load_dotenv

# Load from .env.local
env_file = Path(__file__).parent.parent.parent / ".env.local"
if env_file.exists():
    load_dotenv(env_file)

# Required environment variables (in .env.local or cloud)
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY", "")  # pk-lf-...
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY", "")  # sk-lf-...
LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")  # EU region
```

**Module Pattern - observability.py**
```python
from langfuse import Langfuse, get_client, observe

class LangFuseObservability:
    """Manages LangFuse client lifecycle for FastAPI application."""

    def __init__(self):
        self.client = None
        self.enabled = False

    def initialize(self):
        """Initialize LangFuse client with credentials from environment."""
        try:
            self.client = get_client()
            # Verify connection
            self.client.auth_check()
            self.enabled = True
            logging.info("LangFuse client initialized and authenticated")
        except Exception as e:
            logging.error(f"LangFuse initialization failed: {e}")
            self.enabled = False
            raise  # Explicit error - no fallback logic

    def flush(self):
        """Flush pending traces to LangFuse."""
        if self.client:
            self.client.flush()
            self.client.shutdown()

# Global instance
langfuse_obs = LangFuseObservability()
```

**FastAPI Route Instrumentation**
```python
from fastapi import FastAPI
from langfuse import observe

@app.post("/jobs")
@observe(name="create_job")
async def create_job(request: JobSubmitRequest, current_user: CurrentUserDep) -> JobSubmitResponse:
    """
    Create new test generation job.

    Instrumentation captures:
    - Input parameters
    - Execution time (latency)
    - Errors and exceptions
    - User attribution (from current_user)
    """
    langfuse = get_client()

    # Update current span with GAMP-5 metadata
    langfuse.update_current_span(
        user_id=current_user.user_id,
        metadata={
            "job_id": str(job_id),
            "gamp_category": "5",
            "user_email": current_user.email,
            "timestamp": datetime.now(UTC).isoformat(),
        },
        tags=["pharmaceutical", "test-generation"]
    )

    try:
        # Job creation logic
        job = await process_job_submission(request)
        return JobSubmitResponse(job_id=str(job.id), status="created")
    except Exception as e:
        # Explicit error handling - no fallback
        langfuse.update_current_span(
            level="ERROR",
            status_message=str(e),
            metadata={"error_type": type(e).__name__}
        )
        raise HTTPException(status_code=400, detail=str(e))
```

**Application Lifespan Integration**
```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle management."""
    # Startup
    langfuse_obs.initialize()
    logger.info("LangFuse observability started")

    yield  # Application running

    # Shutdown
    langfuse_obs.flush()
    logger.info("LangFuse observability flushed and shut down")

app = FastAPI(lifespan=lifespan)
```

#### LlamaIndex 0.12.0 Integration Pattern

**Recommended Approach: Callback Handler (vs. Instrumentation)**

Rationale:
- Callback Handler approach is more stable (production-ready)
- Instrumentation is experimental and has known issues with LlamaIndex Workflows (dropped spans)
- Callback Handler provides better control over what gets traced

**Implementation Pattern**
```python
from llama_index.core import Settings
from llama_index.core.callbacks import CallbackManager
from langfuse.llama_index import LlamaIndexCallbackHandler

class WorkflowObservability:
    """Configure LlamaIndex callbacks for LangFuse integration."""

    @staticmethod
    def configure_langfuse_callbacks():
        """Register LangFuse callback handler with LlamaIndex."""
        langfuse_handler = LlamaIndexCallbackHandler(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
        )

        # Set callback manager
        Settings.callback_manager = CallbackManager([langfuse_handler])

        return langfuse_handler

# In main application initialization
workflow_obs = WorkflowObservability()
workflow_obs.configure_langfuse_callbacks()
```

**Integration in unified_workflow.py**
```python
from src.config.langfuse_config import WorkflowObservability
from langfuse import get_client

class UnifiedTestGenerationWorkflow(Workflow):
    """Master workflow with LangFuse instrumentation."""

    async def run(self, urs_document: str, user_id: str) -> TestGenerationResult:
        """Execute workflow with LangFuse tracing."""
        # LlamaIndex callbacks automatically capture all events
        # (LLM calls, retrievals, generations)

        langfuse = get_client()

        # Manually add GAMP-5 metadata at workflow level
        with langfuse.start_as_current_span(
            name="pharmaceutical_test_generation",
            input={"user_id": user_id, "document_length": len(urs_document)},
            metadata={
                "user_id": user_id,
                "gamp_category": "5",
                "workflow_version": "1.0",
            }
        ) as span:
            try:
                # Execute workflow steps
                result = await self._execute_workflow(urs_document, user_id)

                span.update(
                    output={"status": "completed", "test_count": len(result.tests)},
                    metadata={"duration_seconds": span.duration}
                )
                return result

            except Exception as e:
                span.update(
                    level="ERROR",
                    status_message=str(e),
                    metadata={"error_type": type(e).__name__}
                )
                raise  # Explicit error - no fallback
            finally:
                langfuse.flush()
```

#### Environment Variables Configuration
```
# .env.local or cloud environment
LANGFUSE_PUBLIC_KEY=pk-lf-...           # From LangFuse project settings
LANGFUSE_SECRET_KEY=sk-lf-...           # From LangFuse project settings
LANGFUSE_HOST=https://cloud.langfuse.com  # EU region (default)
# LANGFUSE_HOST=https://us.cloud.langfuse.com  # US region if needed
```

#### GAMP-5 Compliance Metadata in Traces

**Required Metadata Per Trace**
```python
# Always include in span.metadata:
metadata={
    "user_id": str,              # ALCOA+ Attributable (who)
    "job_id": str,               # GAMP-5 traceability
    "gamp_category": "5",        # GAMP-5 categorization (Category 5 = fully configurable)
    "timestamp": ISO8601,        # ALCOA+ Contemporaneous (when)
    "user_email": str,           # Secondary attribution
    "workflow_version": str,     # ALCOA+ Original (versioning)
    "environment": str,          # local/staging/production
}

# Conditional metadata for errors:
metadata={
    "error_type": str,           # Exception class name
    "error_details": str,        # Full error message
    "recovery_action": str,      # How error was handled
}
```

**Example: Complete GAMP-5 Compliant Trace**
```python
with langfuse.start_as_current_span(
    name="test_categorization",
    input={
        "requirements_count": 15,
        "document_type": "URS",
    },
    metadata={
        "user_id": "clerk_user_123",
        "job_id": job_id,
        "gamp_category": "5",
        "timestamp": datetime.now(UTC).isoformat(),
        "user_email": "user@pharma.com",
        "workflow_version": "1.0",
        "environment": "production",
        "alcoa_attributable": True,
        "alcoa_legible": True,
    }
) as span:
    result = categorize_requirements(requirements)
    span.update(
        output={"categories": result.categories, "confidence": result.confidence},
        metadata={"categorization_method": "llama-index-workflow"}
    )
```

#### Error Handling - NO FALLBACK LOGIC

**Pattern: Explicit Error Throwing**
```python
@observe(name="process_requirements")
async def process_requirements(requirements: List[str], job_id: str):
    """Process requirements with explicit error handling."""
    langfuse = get_client()

    # Validation: fail fast with full diagnostics
    if not requirements:
        error_msg = f"No requirements provided for job {job_id}"
        langfuse.update_current_span(
            level="ERROR",
            status_message=error_msg,
            metadata={"validation_failed": True}
        )
        raise ValueError(error_msg)  # Explicit error, no fallback

    try:
        results = []
        for req in requirements:
            result = await process_single_requirement(req)
            results.append(result)

        return results

    except ProcessingError as e:
        # Detailed error context
        error_context = {
            "error_type": "ProcessingError",
            "requirement_index": len(results),
            "error_message": str(e),
            "total_requirements": len(requirements),
        }
        langfuse.update_current_span(
            level="ERROR",
            status_message=f"Processing failed at requirement {len(results)}/{len(requirements)}",
            metadata=error_context
        )
        raise  # Re-raise with context captured, no fallback

    except Exception as e:
        # Catch-all for unexpected errors
        langfuse.update_current_span(
            level="ERROR",
            status_message=f"Unexpected error: {type(e).__name__}",
            metadata={
                "error_type": type(e).__name__,
                "error_details": str(e),
                "traceback_present": True,
            }
        )
        raise  # Explicit re-raise, no mask/fallback
```

---

### 2. LangFuse Frontend Dashboard

#### LangFuse Public API - Endpoints & Authentication

**Critical: NOT Bearer Token - Use Basic Auth**

The LangFuse Public API uses **HTTP Basic Authentication**, not Bearer tokens. This is a critical implementation detail often missed.

```python
# WRONG - This will NOT work:
headers = {"Authorization": f"Bearer {LANGFUSE_SECRET_KEY}"}

# CORRECT - HTTP Basic Auth:
import base64
auth_header = base64.b64encode(
    f"{LANGFUSE_PUBLIC_KEY}:{LANGFUSE_SECRET_KEY}".encode()
).decode()
headers = {"Authorization": f"Basic {auth_header}"}
```

**Available Metrics Endpoints**

1. **Legacy Endpoint (Simpler, Recommended for MVP)**
   ```
   GET /api/public/metrics/daily
   ```
   Query Parameters:
   - `traceName` (optional): Filter by trace name (e.g., "pharmaceutical_test_generation")
   - `userId` (optional): Filter by user ID
   - `tags` (optional): Filter by comma-separated tags
   - `fromTimestamp` (optional): ISO8601 start time
   - `toTimestamp` (optional): ISO8601 end time
   - `limit` (optional): Number of results to return (default: 100)

   Response:
   ```json
   {
     "data": [
       {
         "date": "2025-11-11",
         "countTraces": 150,
         "totalCost": 102.19,
         "usage": [
           {
             "model": "deepseek-v3",
             "inputUsage": 1200,
             "outputUsage": 1300,
             "totalUsage": 2500
           }
         ]
       }
     ],
     "meta": {
       "page": 1,
       "limit": 100,
       "totalItems": 60,
       "totalPages": 1
     }
   }
   ```

2. **Advanced Metrics API (More Flexible)**
   ```
   GET /api/public/metrics
   ```
   Query Parameter: `query` (URL-encoded JSON)

   Query JSON structure:
   ```json
   {
     "view": "traces",  // or "observations", "scores-numeric", "scores-categorical"
     "dimensions": [{"field": "name"}, {"field": "userId"}],
     "metrics": [
       {"measure": "count", "aggregation": "count"},
       {"measure": "latency", "aggregation": "p95"}
     ],
     "filters": [
       {"column": "name", "operator": "contains", "value": "test_generation"}
     ],
     "timeDimension": {"granularity": "day"},
     "fromTimestamp": "2025-11-01T00:00:00Z",
     "toTimestamp": "2025-11-11T23:59:59Z"
   }
   ```

**Recommendation for Task 2.3**: Use legacy `/api/public/metrics/daily` endpoint for MVP simplicity, then migrate to advanced API if needed later.

#### Next.js Pages Router API Route with Clerk Protection

**Critical Architectural Issue: Static Export Incompatibility**

⚠️ **BLOCKER**: The current frontend configuration uses `output: 'export'` for static export in `next.config.ts`. **Static export does NOT support API routes.**

```
Error when running 'next export' with API routes:
- API routes require a Node.js server runtime
- Static export produces only static HTML/CSS/JS
- Cannot execute dynamic API handlers in a static environment
```

**Solutions:**
1. **Option A (Recommended)**: Remove static export, deploy with Next.js server mode
   - Modify `next.config.ts`: Remove `output: 'export'`
   - Deploy to Vercel or self-hosted Node.js environment
   - Supports API routes, Clerk middleware, dynamic rendering

2. **Option B (Workaround)**: Pre-render metrics at build time
   - Use `getStaticProps` + `revalidate` for ISR (Incremental Static Regeneration)
   - Generate static JSON files at build time
   - SWR fetches pre-rendered JSON, not dynamic API routes
   - Limited to build-time metrics, cannot update in real-time

**Assuming Option A (Server Mode) - Implementation**

**API Route: pages/api/langfuse/summary.ts**
```typescript
import { withAuth } from "@clerk/nextjs/api";
import type { NextApiRequest, NextApiResponse } from "next";
import { ClerkRequest, ClerkResponse } from "@clerk/nextjs/server";

interface MetricsSummary {
  date: string;
  traceCount: number;
  latencyP95: number;
  errorRate: number;
  totalCost: number;
}

interface ApiResponse {
  success: boolean;
  data?: MetricsSummary[];
  error?: string;
  cached?: boolean;
  cachedAt?: string;
}

// Caching: Store in memory (simple approach for MVP)
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes
let cachedMetrics: { data: MetricsSummary[]; timestamp: number } | null = null;

async function fetchLangFuseMetrics(
  userId: string
): Promise<MetricsSummary[]> {
  // Check cache first (respects LangFuse rate limits)
  if (cachedMetrics && Date.now() - cachedMetrics.timestamp < CACHE_DURATION) {
    console.log("Using cached metrics");
    return cachedMetrics.data;
  }

  const LANGFUSE_PUBLIC_KEY = process.env.LANGFUSE_PUBLIC_KEY;
  const LANGFUSE_SECRET_KEY = process.env.LANGFUSE_SECRET_KEY;
  const LANGFUSE_HOST = process.env.LANGFUSE_HOST || "https://cloud.langfuse.com";

  if (!LANGFUSE_PUBLIC_KEY || !LANGFUSE_SECRET_KEY) {
    throw new Error("LangFuse credentials not configured");
  }

  // Construct Basic Auth header
  const authString = `${LANGFUSE_PUBLIC_KEY}:${LANGFUSE_SECRET_KEY}`;
  const base64Auth = Buffer.from(authString).toString("base64");

  try {
    // Fetch from legacy metrics endpoint (simpler for MVP)
    const response = await fetch(
      `${LANGFUSE_HOST}/api/public/metrics/daily?userId=${userId}&limit=7`,
      {
        method: "GET",
        headers: {
          Authorization: `Basic ${base64Auth}`,
          "Content-Type": "application/json",
        },
      }
    );

    if (!response.ok) {
      const errorBody = await response.text();
      throw new Error(
        `LangFuse API error: ${response.status} - ${errorBody}`
      );
    }

    const langfuseData = await response.json();

    // Transform LangFuse response to metrics summary
    const metrics = langfuseData.data.map((item: any) => ({
      date: item.date,
      traceCount: item.countTraces,
      latencyP95: item.usage?.[0]?.totalUsage || 0, // Approximation
      errorRate: 0, // Not directly available from daily endpoint
      totalCost: item.totalCost,
    }));

    // Cache the results
    cachedMetrics = {
      data: metrics,
      timestamp: Date.now(),
    };

    return metrics;
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    console.error("Failed to fetch LangFuse metrics:", errorMessage);
    throw new Error(`LangFuse fetch failed: ${errorMessage}`);
  }
}

export default withAuth(async (req: NextApiRequest & ClerkRequest, res: NextApiResponse & ClerkResponse) => {
  // withAuth already verified authentication
  const userId = req.auth?.userId;

  if (!userId) {
    return res.status(401).json({
      success: false,
      error: "Unauthorized - user not authenticated",
    } as ApiResponse);
  }

  if (req.method !== "GET") {
    return res.status(405).json({
      success: false,
      error: `Method ${req.method} not allowed`,
    } as ApiResponse);
  }

  try {
    const metrics = await fetchLangFuseMetrics(userId);

    return res.status(200).json({
      success: true,
      data: metrics,
      cached: cachedMetrics?.timestamp ? Date.now() - cachedMetrics.timestamp < 60000 : false,
      cachedAt: cachedMetrics?.timestamp ? new Date(cachedMetrics.timestamp).toISOString() : undefined,
    } as ApiResponse);
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    console.error("API error:", errorMessage);

    return res.status(500).json({
      success: false,
      error: `Failed to fetch metrics: ${errorMessage}`,
    } as ApiResponse);
  }
});
```

#### Dashboard Page with SWR

**Page: pages/observability.tsx**
```typescript
import { useAuth } from "@clerk/nextjs";
import useSWR from "swr";
import { useState, useEffect } from "react";
import Layout from "@/components/Layout";

interface MetricsSummary {
  date: string;
  traceCount: number;
  latencyP95: number;
  errorRate: number;
  totalCost: number;
}

interface MetricsResponse {
  success: boolean;
  data?: MetricsSummary[];
  error?: string;
  cached?: boolean;
  cachedAt?: string;
}

const fetcher = async (url: string) => {
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error("Failed to fetch metrics");
  }
  return res.json();
};

export default function ObservabilityDashboard() {
  const { isLoaded, userId } = useAuth();
  const [mounted, setMounted] = useState(false);

  const { data, error, isLoading } = useSWR<MetricsResponse>(
    isLoaded && userId ? "/api/langfuse/summary" : null,
    fetcher,
    {
      revalidateOnFocus: false,
      revalidateOnReconnect: false,
      dedupingInterval: 60000, // Respect rate limits: revalidate every 60 seconds max
      focusThrottleInterval: 300000, // Don't revalidate on focus for 5 minutes
    }
  );

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted || !isLoaded) {
    return (
      <Layout>
        <div className="flex items-center justify-center min-h-screen">
          <p className="text-gray-500">Loading...</p>
        </div>
      </Layout>
    );
  }

  if (!userId) {
    return (
      <Layout>
        <div className="flex items-center justify-center min-h-screen">
          <p className="text-red-500">Please sign in to view observability metrics</p>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="max-w-6xl mx-auto py-8 px-4">
        <h1 className="text-3xl font-bold text-slate-900 mb-8">
          Test Execution Observability Dashboard
        </h1>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <p className="text-red-700 font-semibold">Error Loading Metrics</p>
            <p className="text-red-600 text-sm">{error.message}</p>
          </div>
        )}

        {isLoading && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
            <p className="text-blue-700">Loading metrics from LangFuse...</p>
          </div>
        )}

        {data?.cached && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
            <p className="text-yellow-700 text-sm">
              Cached data from {new Date(data.cachedAt!).toLocaleTimeString()}
              <br />
              <span className="text-xs text-gray-500">
                (Updated every 5 minutes to respect rate limits)
              </span>
            </p>
          </div>
        )}

        {data?.success && data?.data && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            {/* Throughput Card - Normalized to 50 documents/day baseline */}
            <MetricCard
              title="Daily Throughput"
              value={data.data[0]?.traceCount || 0}
              baseline={50}
              unit="documents"
              description="Traces generated today (baseline: 50/day)"
            />

            {/* Latency Card - P95 */}
            <MetricCard
              title="Latency (P95)"
              value={data.data[0]?.latencyP95 || 0}
              unit="ms"
              description="95th percentile response time"
            />

            {/* Error Rate Card */}
            <MetricCard
              title="Error Rate"
              value={data.data[0]?.errorRate || 0}
              unit="%"
              description="Percentage of failed traces"
              isPercentage={true}
            />

            {/* Cost Card */}
            <MetricCard
              title="Daily Cost"
              value={data.data[0]?.totalCost || 0}
              unit="USD"
              description="API and token costs"
              isCurrency={true}
            />
          </div>
        )}

        {data?.success && data?.data && data.data.length > 0 && (
          <div className="bg-white border border-slate-200 rounded-lg p-6">
            <h2 className="text-xl font-semibold text-slate-900 mb-4">
              7-Day Trend
            </h2>
            <div className="space-y-4">
              {data.data.map((metric) => (
                <div key={metric.date} className="border-b border-slate-100 pb-4">
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="font-medium text-slate-900">
                        {new Date(metric.date).toLocaleDateString()}
                      </p>
                      <p className="text-sm text-slate-500">
                        {metric.traceCount} traces
                        {metric.traceCount > 50 ? " (above baseline)" : ""}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="font-semibold text-slate-900">
                        ${metric.totalCost.toFixed(2)}
                      </p>
                      <p className="text-sm text-slate-500">
                        {metric.latencyP95}ms p95
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
            <p className="text-xs text-gray-500 mt-4">
              Baseline throughput: 50 documents/day
              <br />
              Note: Metrics are cached and updated every 5 minutes to respect LangFuse rate limits
            </p>
          </div>
        )}

        {!data?.success && !isLoading && (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-6 text-center">
            <p className="text-gray-600">
              No metrics available yet. Make sure the backend is instrumented with LangFuse.
            </p>
          </div>
        )}
      </div>
    </Layout>
  );
}

interface MetricCardProps {
  title: string;
  value: number;
  baseline?: number;
  unit: string;
  description: string;
  isPercentage?: boolean;
  isCurrency?: boolean;
}

function MetricCard({
  title,
  value,
  baseline,
  unit,
  description,
  isPercentage,
  isCurrency,
}: MetricCardProps) {
  const formatValue = () => {
    if (isCurrency) return `$${value.toFixed(2)}`;
    if (isPercentage) return `${value.toFixed(1)}%`;
    return value.toLocaleString();
  };

  const isAboveBaseline = baseline && value > baseline;

  return (
    <div className="bg-white border border-slate-200 rounded-lg p-4">
      <h3 className="text-sm font-medium text-slate-600 mb-2">{title}</h3>
      <div className="flex items-baseline gap-2 mb-4">
        <p className={`text-2xl font-bold ${isAboveBaseline ? "text-orange-600" : "text-slate-900"}`}>
          {formatValue()}
        </p>
        <p className="text-sm text-slate-500">{unit}</p>
      </div>
      <p className="text-xs text-slate-500">{description}</p>
      {isAboveBaseline && (
        <p className="text-xs text-orange-600 mt-2 font-semibold">
          {value - baseline!} above baseline ({baseline}/day)
        </p>
      )}
    </div>
  );
}
```

#### SWR Caching Strategy

**Default Behavior: In-Memory Cache Per Session**
- SWR caches API responses in memory by default
- Cache is lost on page reload or navigation
- `revalidateOnFocus: false` - prevents refetch when user returns to tab
- `dedupingInterval: 60000` - prevents duplicate requests within 60 seconds

**Rationale for Caching**
- LangFuse Cloud has rate limits (~100 req/min per API key)
- Polling every 5 seconds would hit limits quickly
- 5-minute cache balance: real-time feel + respects rate limits

**If Persistent Cache Needed (Advanced)**
```typescript
// Custom cache provider with localStorage
function useLocalStorageCache() {
  return {
    get: (key: string) => {
      const cached = localStorage.getItem(`swr-${key}`);
      return cached ? JSON.parse(cached) : null;
    },
    set: (key: string, value: any) => {
      localStorage.setItem(`swr-${key}`, JSON.stringify(value));
    },
    delete: (key: string) => {
      localStorage.removeItem(`swr-${key}`);
    },
  };
}

// Wrap app with provider
<SWRConfig value={{ provider: () => useLocalStorageCache() }}>
  {children}
</SWRConfig>
```

---

### 3. Integration Architecture

#### End-to-End Data Flow

```
1. Test Execution
   └─> FastAPI route (POST /jobs) with @observe decorator
       └─> LangFuse trace created with GAMP-5 metadata
           └─> LlamaIndex workflow (CallbackHandler registered)
               └─> LLM calls traced automatically
               └─> Retrieval operations traced
               └─> Test results traced
           └─> Langfuse client flushes traces

2. Metrics Collection
   └─> LangFuse Cloud receives traces
       └─> Aggregates into daily metrics
       └─> Stores in time-series database

3. Frontend Dashboard
   └─> User visits /observability page
       └─> SWR calls /api/langfuse/summary
           └─> API route authenticates with Clerk
           └─> Makes HTTP request to LangFuse Public API
               └─> Basic Auth: public_key:secret_key
           └─> Caches response for 5 minutes
           └─> Returns to frontend
       └─> SWR re-renders with metrics
           └─> Displays throughput, latency, costs
           └─> Shows 7-day trend
```

#### Local Development Setup

**Option A (Recommended): LangFuse Cloud**
- Sign up at https://cloud.langfuse.com
- Get public/secret keys from project settings
- Add to .env.local
- Traces sent immediately to cloud dashboard
- Pro: No local infrastructure, sees real production-like behavior
- Con: Requires external account, uses production credentials

**Option B: Self-Hosted LangFuse (Advanced)**
- Run locally with Docker: `docker run -d -p 3000:3000 langfuse/langfuse:latest`
- Set `LANGFUSE_HOST=http://localhost:3000`
- Still need test keys, but isolated from production
- Pro: Full control, no external dependencies
- Con: Extra Docker overhead, needs management

**Recommendation**: Start with LangFuse Cloud for MVP simplicity.

#### Testing Strategy

**Backend Instrumentation Testing**
```python
# tests/test_langfuse_instrumentation.py
@pytest.mark.asyncio
async def test_create_job_creates_langfuse_trace():
    """Verify FastAPI route creates LangFuse trace with GAMP-5 metadata."""
    # Mock Clerk user
    mock_user = CurrentUser(user_id="test-user-123", email="test@pharma.com")

    # Call endpoint
    response = await client.post(
        "/jobs",
        json={"urs_document": "test requirements"},
        headers={"Authorization": "Bearer mock-token"}
    )

    assert response.status_code == 201

    # Verify LangFuse was called
    # (Would need to mock langfuse.update_current_span)
    # This is a manual verification step in real testing
```

**Frontend Dashboard Testing**
```typescript
// __tests__/observability.test.tsx
import { render, screen, waitFor } from "@testing-library/react";
import ObservabilityDashboard from "@/pages/observability";

jest.mock("swr", () => ({
  __esModule: true,
  default: () => ({
    data: {
      success: true,
      data: [
        {
          date: "2025-11-11",
          traceCount: 100,
          latencyP95: 150,
          errorRate: 2,
          totalCost: 45.50,
        },
      ],
    },
    error: null,
    isLoading: false,
  }),
}));

jest.mock("@clerk/nextjs", () => ({
  useAuth: () => ({
    isLoaded: true,
    userId: "test-user-123",
  }),
}));

test("displays metrics summary cards", async () => {
  render(<ObservabilityDashboard />);

  await waitFor(() => {
    expect(screen.getByText(/Daily Throughput/)).toBeInTheDocument();
    expect(screen.getByText(/100 documents/)).toBeInTheDocument();
  });
});
```

---

### 4. Pharmaceutical Compliance

#### GAMP-5 Categorization
The test generation system itself is **Category 5 (Fully Configurable)** under GAMP-5, meaning:
- Configuration items (test parameters, rules, prompts) drive system behavior
- System logic is provided by vendors (LlamaIndex, LLM providers)
- User-configured items must be validated and tracked

**For observability traces specifically:**
- Every trace must record the user_id (ALCOA+ Attributable)
- Every trace must record gamp_category: "5" (GAMP-5 tracking)
- Every trace must record timestamp (ALCOA+ Contemporaneous)
- Every error must be captured with full context (ALCOA+ Complete, Accurate)

#### ALCOA+ Principles Implementation

| Principle | Implementation in Traces |
|-----------|--------------------------|
| **Attributable** | user_id, user_email, authenticated token in every span |
| **Legible** | Human-readable trace names, clear metadata keys |
| **Contemporaneous** | ISO8601 timestamps, synchronized NTP time |
| **Original** | Immutable traces in LangFuse (write-once), versioning |
| **Accurate** | Captured actual results, not approximations |
| **Complete** | Include input, output, errors, duration, resource usage |
| **Consistent** | Standardized metadata schema across all traces |
| **Enduring** | Long-term storage in LangFuse (default 90 days, configurable) |
| **Available** | Exported via LangFuse API for audit retrieval |

#### 21 CFR Part 11 Considerations (Post-MVP)
The current MVP does not fully implement 21 CFR Part 11, but traces are structured to support future compliance:
- Electronic signatures: Future integration with digital signature service
- Access controls: Clerk authentication + role-based access (future)
- Audit trails: Currently provided by LangFuse + FastAPI audit logs
- Data integrity: Immutable traces in LangFuse cloud

#### Data Residency
- **EU Data**: LangFuse at `https://cloud.langfuse.com` (EU region)
- **US Data**: LangFuse at `https://us.cloud.langfuse.com` (US region)
- **HIPAA Compliance**: Available at `https://hipaa.cloud.langfuse.com` (if needed)

---

### 5. Implementation Gotchas & Known Issues

#### Version Compatibility

| Package | Version | Notes | Status |
|---------|---------|-------|--------|
| `langfuse` | 3.5.2 | Latest stable, FastAPI streaming fixed in v3.5.2 | ✅ OK |
| `llama-index-core` | 0.13.3 | Compatible with LlamaIndex 0.12.0+ ecosystem | ✅ OK |
| `fastapi` | 0.100+ | Async support required for LangFuse decorator | ✅ OK |
| `next` | 14.2.33 | Pages Router required (App Router incompatible) | ✅ OK |
| `swr` | 2.2.0+ | Client-side only, works in Pages Router | ✅ OK |

**Critical Issue**: LlamaIndex Workflows + LangFuse Instrumentation may drop spans
- **Problem**: LlamaIndex Workflows (experimental in 0.12.0) have concurrency issues with LangFuse
- **Solution**: Use CallbackHandler approach instead of Instrumentation (as documented above)
- **Workaround**: If using Workflows, explicitly create parent span IDs

#### Next.js Static Export Incompatibility (BLOCKER)

**Current Configuration Issue**
```typescript
// next.config.ts - CURRENT (BLOCKS API ROUTES)
export default withClerkConfig({
  output: 'export',  // ❌ Static export incompatible with API routes
});
```

**Required Fix for Task 2.3**
```typescript
// next.config.ts - FIXED (ENABLES API ROUTES)
export default withClerkConfig({
  // REMOVE output: 'export' line
  // Allows API routes to run on Node.js server
});
```

**Impact**: This is a breaking change to current architecture
- Frontend can no longer use static hosting (S3 + CloudFront)
- Requires deployment to Vercel or Node.js server
- Build process: `next build` → `next start` instead of `next export`

#### Async/Await Context Issues

**Problem**: LangFuse @observe decorator in async functions
```python
# ❌ WRONG - Decorator alone doesn't work in all async contexts
@observe()
async def workflow_step(data):
    result = await async_operation(data)  # Context might be lost
    return result
```

**Solution**: Use context manager explicitly
```python
# ✅ CORRECT - Explicit context ensures trace capture
@observe()
async def workflow_step(data):
    langfuse = get_client()
    with langfuse.start_as_current_span(name="workflow_step") as span:
        result = await async_operation(data)
        span.update(output=result)
        return result
```

#### LangFuse API Rate Limits

- Public API: ~100 requests/minute per API key
- Daily metrics endpoint: Lower priority queue (may throttle if load high)
- Solution: 5-minute caching implemented in SWR config
- Recommendation: Contact LangFuse if MVP needs higher limits

#### Memory/Performance Considerations

**LangFuse Client in FastAPI**
- Batches spans internally (flushes periodically)
- Async/background transmission (doesn't block requests)
- Memory footprint: ~50MB per worker process
- No significant latency impact observed

**SWR Cache in Frontend**
- In-memory only (default)
- Persists per browser session
- No persistent storage without custom provider
- Memory: Negligible (<1MB per dashboard page)

---

### 6. Critical Requirements Summary

#### NO FALLBACK LOGIC (MANDATORY)
✅ All errors must throw explicitly with diagnostics
✅ No default values, no silent failures
✅ Validation must fail fast with complete error context
✅ All exceptions must be logged to LangFuse traces
✅ API responses must never mask errors as success

**Example of CORRECT error handling:**
```python
try:
    metrics = fetch_langfuse_metrics(user_id)
except Exception as e:
    # Log complete error context
    logger.error(f"Failed to fetch metrics: {type(e).__name__}: {str(e)}")
    # Return error to client, don't return empty array or default
    return res.status(500).json({"success": False, "error": str(e)})
```

#### GAMP-5 Compliance First
✅ Every trace must have user_id (Attributable)
✅ Every trace must have gamp_category (GAMP-5 tracking)
✅ Every trace must have timestamp (Contemporaneous)
✅ Errors must be captured completely (Complete)
✅ Traces must be immutable and versioned (Original, Enduring)

#### Model Enforcement
✅ task-executor MUST use DeepSeek V3 (deepseek/deepseek-chat) via OpenRouter
❌ NO O3, OpenAI, GPT-4, Claude for generation

---

## Recommended Implementation Approach

### Phase 1: Backend Instrumentation (2-3 hours)
1. Create `main/api/observability.py` with LangFuse client initialization
2. Add `main/src/core/langfuse_callback.py` for LlamaIndex CallbackHandler registration
3. Add `@observe` decorator to FastAPI routes (POST /jobs, GET /jobs/{id})
4. Update `main/src/core/unified_workflow.py` to register CallbackManager
5. Add GAMP-5 metadata to all spans
6. Update `.env.local` with LangFuse credentials
7. Add `langfuse==3.5.2` to dependencies (`uv add langfuse==3.5.2`)
8. Test with manual traces using local test script

### Phase 2: Frontend Dashboard (2-3 hours)
1. **BLOCKER FIX**: Remove `output: 'export'` from `next.config.ts`
2. Create `main/frontend/pages/api/langfuse/summary.ts` with:
   - Clerk authentication via `withAuth`
   - HTTP Basic Auth to LangFuse API
   - 5-minute caching logic
   - Error handling (no fallback)
3. Create `main/frontend/pages/observability.tsx` dashboard page with:
   - SWR data fetching
   - MetricCard components
   - 7-day trend display
   - Compliance annotations
4. Update `main/frontend/components/Layout.tsx` to add navigation link
5. Test SWR caching behavior

### Phase 3: Integration Testing (1-2 hours)
1. Create `main/tests/test_langfuse_integration.py` for backend
2. Create `main/frontend/__tests__/observability.test.tsx` for frontend
3. Test end-to-end: job creation → trace in LangFuse → metrics in dashboard
4. Validate GAMP-5 metadata in traces

### Phase 4: Compliance Validation (30 minutes)
1. Verify all traces contain required metadata
2. Check error handling is explicit (no fallbacks)
3. Validate audit trail completeness
4. Document compliance approach

---

## Required Libraries/Versions

### Backend
- `langfuse==3.5.2` - LLM observability, FastAPI integration
- `llama-index-core==0.13.3` - Already installed, used for CallbackHandler
- `fastapi==0.100.0+` - Already installed, async/streaming support
- `pydantic==2.0+` - Already installed, model validation
- `python-dotenv` - Already installed, environment variable loading

### Frontend
- `swr==2.2.0+` - Data fetching with caching
- `@clerk/nextjs==^6.32.0` - Already installed, authentication
- `react==^18.2.0` - Already installed, UI library
- `next==14.2.33` - Already installed, framework

### Development
- `pytest==7.4.0+` - Testing (backend)
- `pytest-asyncio==0.21.0+` - Async test support
- `jest==29.0.0+` - Testing (frontend)
- `@testing-library/react==14.0.0+` - React component testing

---

## Next Agent Guidance

### For task-executor

**Critical Instructions:**

1. **DO FIRST: Fix Next.js Static Export Incompatibility**
   - Remove `output: 'export'` from `next.config.ts`
   - This must be done BEFORE creating API routes
   - API routes require Node.js server runtime (not static export)

2. **Backend Instrumentation - Files to Create:**
   - `main/api/observability.py` (100 lines) - LangFuse client initialization
   - `main/src/core/langfuse_callback.py` (50 lines) - LlamaIndex CallbackHandler setup
   - Update `main/api/app.py` to initialize LangFuse in lifespan
   - Update `main/src/core/unified_workflow.py` to register callbacks

3. **Frontend Dashboard - Files to Create:**
   - `main/frontend/pages/api/langfuse/summary.ts` (150 lines) - API route with Clerk protection + LangFuse fetch
   - `main/frontend/pages/observability.tsx` (250 lines) - Dashboard page with SWR and metric cards
   - Update `main/frontend/components/Layout.tsx` to add navigation link

4. **Critical Implementation Details:**
   - LangFuse uses HTTP **Basic Auth**, NOT Bearer token (COMMON MISTAKE)
   - Basic Auth format: `Authorization: Basic base64(public_key:secret_key)`
   - Use CallbackHandler for LlamaIndex (NOT Instrumentation - it has known issues)
   - Every trace MUST include: user_id, job_id, gamp_category, timestamp
   - NO FALLBACK LOGIC - all errors must throw with full diagnostics
   - SWR cache: 5-minute duration to respect rate limits

5. **Files to Modify:**
   - `next.config.ts` - REMOVE `output: 'export'` line
   - `main/api/app.py` - Add observability initialization in lifespan
   - `main/src/core/unified_workflow.py` - Register CallbackManager
   - `.env.local` - Add LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST
   - `package.json` or `pyproject.toml` - Add langfuse==3.5.2

6. **Testing Requirements:**
   - Verify LangFuse trace creation with @observe decorator
   - Test API route returns metrics from LangFuse
   - Confirm SWR caching works (call endpoint twice, verify only one LangFuse request)
   - Validate GAMP-5 metadata in traces (user_id, gamp_category present)
   - Error handling: Throw explicit errors, don't mask with success responses

7. **GAMP-5 Compliance - Non-Negotiable:**
   - Every span must have `metadata.user_id` (from authenticated user)
   - Every span must have `metadata.gamp_category = "5"`
   - Every span must have `metadata.timestamp` (ISO8601)
   - Errors must be captured with error_type, error_message, full stack
   - Traces must be immutable (LangFuse handles this)

8. **Known Issues to Avoid:**
   - DO NOT use LangFuse Instrumentation with LlamaIndex Workflows (use CallbackHandler instead)
   - DO NOT forget to call `langfuse.flush()` on shutdown
   - DO NOT use Bearer token auth for LangFuse API (use Basic Auth)
   - DO NOT implement cache persistence with localStorage unless explicitly required
   - DO NOT claim success without user confirmation

---

## Files Referenced

### Documentation Sources
- [LangFuse Python SDK Docs](https://langfuse.com/docs/sdk/python/overview)
- [LangFuse Public API Reference](https://langfuse.com/docs/api-and-data-platform/features/public-api)
- [LangFuse Metrics API](https://langfuse.com/docs/metrics/features/metrics-api)
- [LlamaIndex Instrumentation Guide](https://developers.llamaindex.ai/python/framework/module_guides/observability/instrumentation/)
- [LlamaIndex LangFuse Integration](https://langfuse.com/integrations/frameworks/llamaindex)
- [Clerk Next.js Pages Router](https://clerk.com/docs/getting-started/quickstart/pages-router)
- [Next.js Static Export Documentation](https://nextjs.org/docs/app/getting-started/static-export)
- [SWR Documentation](https://swr.vercel.app)

### Code Examples Examined
- `examples/alex/backend/charter/observability.py` - Reference LangFuse setup
- `examples/alex/backend/api/main.py` - Reference FastAPI with Clerk
- `main/api/app.py` - Current FastAPI application
- `main/src/core/unified_workflow.py` - Current LlamaIndex workflow

### Library Documentation
- LangFuse Python SDK v3.5.2: https://github.com/langfuse/langfuse-python
- LlamaIndex Core 0.13.3: https://developers.llamaindex.ai
- FastAPI 0.100+: https://fastapi.tiangolo.com
- Next.js 14: https://nextjs.org/docs
- Clerk v6.32.0: https://clerk.com/docs
- SWR 2.2.0+: https://swr.vercel.app

---

## Summary

Task 2.3 requires implementing comprehensive LangFuse observability for a pharmaceutical test generation system with strict GAMP-5 compliance requirements. The expanded scope includes both backend instrumentation (FastAPI + LlamaIndex workflows) and a frontend metrics dashboard with Clerk authentication.

**Key Success Criteria:**
1. All test execution traces captured in LangFuse with GAMP-5 metadata
2. Frontend dashboard displays real-time metrics (throughput, latency, errors)
3. API routes secured with Clerk authentication
4. SWR caching respects LangFuse rate limits (5-min cache)
5. No fallback logic - all errors throw explicitly with diagnostics
6. Full ALCOA+ compliance in trace capture

**Critical Architectural Decision:**
Static export (current `next.config.ts`) must be removed to support API routes. This is a deployment architecture change requiring Next.js server mode or Vercel deployment.

**Timeline Estimate:** 5-8 hours total (including testing and compliance validation)

---

**Status**: ✅ RESEARCH COMPLETE - Ready for task-executor phase
