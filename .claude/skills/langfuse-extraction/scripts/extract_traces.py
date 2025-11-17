#!/usr/bin/env python3
"""
Extract traces from Langfuse Cloud API.

Usage:
    python extract_traces.py --hours 24 --output recent.json
    python extract_traces.py --trace-id abc123 --detailed
    python extract_traces.py --user-id user_xxx --session-id job_yyy
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from typing import Optional

try:
    from langfuse import Langfuse
except ImportError:
    print("Error: langfuse package not installed")
    print("Run: uv add langfuse")
    sys.exit(1)


def extract_by_time_range(hours: int, output: str, tags: list = None):
    """Extract traces from last N hours."""
    langfuse = Langfuse()

    from_time = datetime.now() - timedelta(hours=hours)
    traces = langfuse.api.trace.list(
        from_timestamp=from_time.isoformat(),
        tags=tags or ["pharmaceutical", "gamp5"],
        limit=1000
    )

    results = [
        {
            "trace_id": t.id,
            "timestamp": t.timestamp,
            "user_id": t.user_id,
            "session_id": t.session_id,
            "duration_ms": t.duration,
            "status": t.status,
            "total_cost": t.total_cost or 0.0,
            "input_tokens": t.usage.input if t.usage else 0,
            "output_tokens": t.usage.output if t.usage else 0,
            "metadata": t.metadata
        }
        for t in traces.data
    ]

    with open(output, "w") as f:
        json.dump(results, f, indent=2)

    print(f"Extracted {len(results)} traces to {output}")


def extract_detailed_trace(trace_id: str, output: Optional[str] = None):
    """Extract single trace with all observations."""
    langfuse = Langfuse()
    trace = langfuse.api.trace.get(trace_id)

    result = {
        "trace_id": trace.id,
        "timestamp": trace.timestamp,
        "user_id": trace.user_id,
        "session_id": trace.session_id,
        "duration_ms": trace.duration,
        "total_cost": trace.total_cost or 0.0,
        "observations": [
            {
                "id": obs.id,
                "type": obs.type,
                "name": obs.name,
                "latency_ms": obs.latency,
                "input": obs.input,
                "output": obs.output,
                "usage": {
                    "input_tokens": obs.usage.input if obs.usage else 0,
                    "output_tokens": obs.usage.output if obs.usage else 0,
                    "cost": obs.calculated_total_cost or 0.0
                },
                "metadata": obs.metadata
            }
            for obs in trace.observations
        ]
    }

    if output:
        with open(output, "w") as f:
            json.dump(result, f, indent=2)
        print(f"Extracted trace {trace_id} to {output}")
    else:
        print(json.dumps(result, indent=2))


def extract_by_user_session(
    user_id: str,
    session_id: Optional[str] = None,
    output: Optional[str] = None
):
    """Extract traces for specific user/session."""
    langfuse = Langfuse()

    filters = {"user_id": user_id}
    if session_id:
        filters["session_id"] = session_id

    traces = langfuse.api.trace.list(**filters)

    results = [
        {
            "trace_id": t.id,
            "timestamp": t.timestamp,
            "duration_ms": t.duration,
            "status": t.status,
            "metadata": t.metadata
        }
        for t in traces.data
    ]

    if output:
        with open(output, "w") as f:
            json.dump(results, f, indent=2)
        print(f"Extracted {len(results)} traces to {output}")
    else:
        print(json.dumps(results, indent=2))


def main():
    parser = argparse.ArgumentParser(description='Extract Langfuse traces')
    parser.add_argument('--hours', type=int, help='Extract last N hours')
    parser.add_argument('--trace-id', help='Extract specific trace')
    parser.add_argument('--user-id', help='Filter by user ID')
    parser.add_argument('--session-id', help='Filter by session ID')
    parser.add_argument('--detailed', action='store_true', help='Include observations')
    parser.add_argument('--output', help='Output file path')
    parser.add_argument('--tags', nargs='+', help='Filter by tags')

    args = parser.parse_args()

    if args.trace_id:
        extract_detailed_trace(args.trace_id, args.output)
    elif args.user_id:
        extract_by_user_session(args.user_id, args.session_id, args.output)
    elif args.hours:
        output = args.output or f"traces_last_{args.hours}h.json"
        extract_by_time_range(args.hours, output, args.tags)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
