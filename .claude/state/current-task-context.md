# Current Task Context: 2.3

## Task File
PRPs/tasks/2.3-langfuse-dashboard.md

## Task Content
# Task P2.3 – Extend LangFuse Dashboard Integration

## What to Do
- Add LangFuse session dashboards to frontend for live observability metrics.
- Create authenticated API route that pulls aggregated trace data from LangFuse API and caches results.
- Display throughput, latency, and error trends in compliance-ready format.

## Dependencies
- Requires LangFuse backend instrumentation (Task 6) and Clerk-protected frontend (Task P2.2).

## Best Practices
- Use ISR or SWR caching to limit API requests and respect LangFuse rate limits.
- Present metrics normalized to the 50 documents/day throughput requirement, flagging deviations.
- Keep metric descriptions inline to ensure compliance reviewers understand each chart.

## Code Example
```tsx
// app/api/langfuse/summary/route.ts
import { NextResponse } from 'next/server';
import { cache } from 'react';

const fetchLangFuseSummary = cache(async () => {
  const res = await fetch('https://cloud.langfuse.com/api/public/metrics', {
    headers: {
      Authorization: `Bearer ${process.env.LANGFUSE_PUBLIC_KEY}:${process.env.LANGFUSE_SECRET_KEY}`,
    },
  });
  if (!res.ok) throw new Error('LangFuse metrics fetch failed');
  return res.json();
});

export async function GET() {
  const data = await fetchLangFuseSummary();
  return NextResponse.json(data);
}
```

## Links
- [LangFuse Metrics API](https://langfuse.com/docs/api/reference)

## Testing Strategy
- Add Next.js API integration tests using `jest-fetch-mock` to validate error handling.
- Snapshot test dashboard components to detect visualization regressions.
- Validate caching by calling endpoint twice and confirming only one LangFuse request.

## Common Issues to Avoid
- Exposing LangFuse secret via client-side fetch; keep requests on the server.
- Forgetting to guard metrics routes with Clerk middleware.
- Overloading dashboard with raw traces instead of high-level metrics for audit review.

## Task Metadata
- Task ID: 2.3
- Phase: Phase 2 - Backend Abstraction
- Started: 2025-11-11T00:00:00Z
- Workflow Status: INITIALIZED

## Scope Expansion
**User Decision:** Option 2 - Implement Full LangFuse Integration Now
This task now includes:
1. Backend LangFuse instrumentation (FastAPI + LlamaIndex workflows)
2. Frontend dashboard with authenticated API routes
3. End-to-end observability integration
