#!/usr/bin/env python3
"""Export Langfuse traces to pandas DataFrame/CSV."""

import argparse
import sys

try:
    from langfuse import Langfuse
    import pandas as pd
except ImportError as e:
    print(f"Error: {e}")
    print("Run: uv add langfuse pandas")
    sys.exit(1)


def export_to_dataframe(limit: int = 1000, output: str = "traces.csv"):
    """Export traces to pandas DataFrame."""
    langfuse = Langfuse()
    traces = langfuse.api.trace.list(limit=limit)

    records = []
    for trace in traces.data:
        records.append({
            "trace_id": trace.id,
            "timestamp": trace.timestamp,
            "duration_ms": trace.duration,
            "user_id": trace.user_id,
            "session_id": trace.session_id,
            "total_cost": trace.total_cost or 0.0,
            "input_tokens": trace.usage.input if trace.usage else 0,
            "output_tokens": trace.usage.output if trace.usage else 0,
            "status": trace.status,
            "gamp5_category": trace.metadata.get("compliance.gamp5.category") if trace.metadata else None,
            "tags": ",".join(trace.tags or [])
        })

    df = pd.DataFrame(records)

    if output.endswith('.csv'):
        df.to_csv(output, index=False)
        print(f"Exported {len(df)} traces to CSV: {output}")
    elif output.endswith('.parquet'):
        df.to_parquet(output, index=False)
        print(f"Exported {len(df)} traces to Parquet: {output}")
    else:
        df.to_json(output, orient='records', indent=2)
        print(f"Exported {len(df)} traces to JSON: {output}")

    # Print summary statistics
    print(f"\nSummary Statistics:")
    print(f"  Total traces: {len(df)}")
    print(f"  Total cost: ${df['total_cost'].sum():.4f}")
    print(f"  Total tokens: {df['input_tokens'].sum() + df['output_tokens'].sum()}")
    print(f"  Avg duration: {df['duration_ms'].mean():.0f}ms")


def main():
    parser = argparse.ArgumentParser(description='Export traces to DataFrame')
    parser.add_argument('--limit', type=int, default=1000, help='Max traces to export')
    parser.add_argument('--output', default='traces.csv', help='Output file (csv/parquet/json)')
    args = parser.parse_args()

    export_to_dataframe(args.limit, args.output)


if __name__ == '__main__':
    main()
