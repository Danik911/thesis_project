#!/usr/bin/env python3
"""
Consolidate trace files from multiple locations into primary trace directory.
Ensures monitor-agent can find all execution traces for analysis.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.monitoring.trace_config import TraceConfig


def main():
    """Consolidate all trace files to primary location."""
    print("Trace Consolidation Utility")
    print("=" * 50)

    # Ensure directories exist
    TraceConfig.ensure_directories()

    # Show current configuration
    print(f"\nPrimary trace directory: {TraceConfig.PRIMARY_TRACE_DIR}")
    print(f"Phoenix export directory: {TraceConfig.PHOENIX_EXPORT_DIR}")
    print(f"Event log directory: {TraceConfig.EVENT_LOG_DIR}")

    # Find all trace files
    print("\nSearching for trace files...")
    all_traces = TraceConfig.get_all_trace_files()

    print(f"\nFound {len(all_traces)} trace files:")
    for trace_file in all_traces:
        print(f"  - {trace_file}")

    # Consolidate traces
    print("\nConsolidating traces to primary directory...")
    result = TraceConfig.consolidate_traces()

    print("\nConsolidation Results:")
    print(f"  - Files found: {result['files_found']}")
    print(f"  - Files moved: {result['files_moved']}")
    print(f"  - Errors: {len(result['errors'])}")

    if result["errors"]:
        print("\nErrors encountered:")
        for error in result["errors"]:
            print(f"  - {error['file']}: {error['error']}")

    # Final summary
    primary_traces = list(TraceConfig.PRIMARY_TRACE_DIR.glob("*.jsonl"))
    print(f"\nTotal traces in primary directory: {len(primary_traces)}")

    # List dates covered
    if primary_traces:
        print("\nTrace dates available:")
        dates = set()
        for trace in primary_traces:
            # Extract date from filename if possible
            name = trace.stem
            if "_" in name:
                date_part = name.split("_")[1] if len(name.split("_")) > 1 else name
                if len(date_part) >= 8:
                    dates.add(date_part[:8])

        for date in sorted(dates):
            print(f"  - {date}")


if __name__ == "__main__":
    main()
