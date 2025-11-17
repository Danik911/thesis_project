# Langfuse Dashboard Navigation Guide

## Project Dashboard Structure

**Base URL**: `https://cloud.langfuse.com/project/cmhuwhcfe006yad06cqfub107`

### Main Sections

1. **Traces** (`/traces`)
   - List of all traces
   - Filters: user_id, session_id, tags, time range
   - Sortable by timestamp, duration, cost

2. **Sessions** (`/sessions`)
   - Grouped traces by session_id
   - Shows session-level aggregates

3. **Users** (`/users`)
   - Traces grouped by user_id
   - User activity overview

4. **Metrics** (`/metrics`)
   - Cost analytics
   - Token usage charts
   - Latency distribution

5. **Settings** (`/settings`)
   - API keys
   - Project configuration
   - Team members

### Trace Detail View

**URL**: `https://cloud.langfuse.com/trace/{trace_id}`

**Structure**:
- Header: Trace ID, timestamp, duration, cost
- Metadata: user_id, session_id, tags
- Span tree: Nested observations with timing
- Expand/collapse controls

### Common Selectors (Estimated)

**Note**: Langfuse UI may change. Use accessibility snapshot to verify.

```
Traces table: [data-testid="traces-table"]
Trace row: [data-testid="trace-row"]
Filter button: [data-testid="filter-button"]
Expand all: [aria-label="Expand all"]
Metric cards: [data-testid="metric-card"]
```

### Authentication

**Login URL**: `https://cloud.langfuse.com/auth/login`

**Authentication flow**:
1. Clerk-based authentication (email/password or OAuth)
2. Session persists in cookies
3. API keys do NOT work for dashboard access (API only)

**Recommendation**: Login manually before running dashboard automation.

### Tips

1. **Refresh rate**: Dashboard auto-refreshes every 30 seconds
2. **Pagination**: Default 50 traces per page
3. **Deep links**: Trace URLs are shareable (auth required)
4. **Export**: Use API (`langfuse-extraction` skill) for bulk export
