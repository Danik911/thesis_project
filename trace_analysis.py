#!/usr/bin/env python3
"""Phoenix Trace Analysis for DeepSeek V3 End-to-End Test"""

import json
from collections import defaultdict


def analyze_traces():
    trace_file = r"C:\Users\anteb\Desktop\Courses\Projects\thesis_project\main\logs\traces\all_spans_20250809_190741.jsonl"
    chromadb_file = r"C:\Users\anteb\Desktop\Courses\Projects\thesis_project\main\logs\traces\chromadb_spans_20250809_190741.jsonl"

    # Load all spans
    spans = []
    try:
        with open(trace_file, encoding="utf-8") as f:
            for line in f:
                try:
                    spans.append(json.loads(line.strip()))
                except:
                    continue
    except FileNotFoundError:
        print(f"ERROR: Could not find trace file: {trace_file}")
        return

    print("="*80)
    print("PHOENIX TRACE FORENSIC ANALYSIS - DEEPSEEK V3 END-TO-END TEST")
    print("="*80)

    print(f"\nCONFIRMED: Total spans analyzed: {len(spans)}")

    # Analyze agent workflows
    agent_counts = defaultdict(int)
    workflow_types = defaultdict(int)
    error_count = 0
    status_codes = defaultdict(int)
    llm_calls = 0

    for span in spans:
        # Count agent types
        name = span.get("name", "")
        if "Workflow" in name:
            workflow_name = name.split(".")[0] if "." in name else name
            agent_counts[workflow_name] += 1

        # Count LLM calls
        attributes = span.get("attributes", {})
        if "llm.provider" in attributes or "llm.system" in attributes:
            llm_calls += 1

        # Check status
        status = span.get("status", {})
        status_code = status.get("status_code", "UNKNOWN")
        status_codes[status_code] += 1

        if status_code != "OK":
            error_count += 1

    print(f"CONFIRMED: Error count: {error_count}")
    print(f"CONFIRMED: LLM API calls: {llm_calls}")

    print("\nCONFIRMED: Status code distribution:")
    for status, count in sorted(status_codes.items()):
        print(f"  {status}: {count} spans")

    print("\nCONFIRMED: Agent workflow execution counts:")
    for agent, count in sorted(agent_counts.items()):
        print(f"  {agent}: {count} spans")

    # Analyze ChromaDB operations
    chromadb_spans = []
    try:
        with open(chromadb_file, encoding="utf-8") as f:
            for line in f:
                try:
                    chromadb_spans.append(json.loads(line.strip()))
                except:
                    continue
        print(f"\nCONFIRMED: ChromaDB spans analyzed: {len(chromadb_spans)}")

        # Analyze ChromaDB operations
        db_operations = defaultdict(int)
        total_duration = 0
        query_count = 0

        for span in chromadb_spans:
            attributes = span.get("attributes", {})
            operation = attributes.get("vector_db.operation", "unknown")
            db_operations[operation] += 1

            # Calculate duration
            duration_ns = span.get("duration_ns", 0)
            if duration_ns > 0:
                total_duration += duration_ns / 1_000_000  # Convert to ms

            if "query" in operation.lower():
                query_count += 1

        print("CONFIRMED: ChromaDB operation breakdown:")
        for op, count in sorted(db_operations.items()):
            print(f"  {op}: {count} operations")

        if query_count > 0:
            avg_duration = total_duration / len(chromadb_spans) if chromadb_spans else 0
            print(f"CONFIRMED: Average ChromaDB operation duration: {avg_duration:.2f}ms")

    except FileNotFoundError:
        print(f"WARNING: ChromaDB spans file not found: {chromadb_file}")

    # Look for specific patterns
    print("\nCONFIRMED: Key workflow patterns identified:")

    # Check for categorization
    categorization_spans = [s for s in spans if "categorization" in s.get("name", "").lower()]
    print(f"  Categorization operations: {len(categorization_spans)}")

    # Check for OQ generation
    oq_spans = [s for s in spans if "oq" in s.get("name", "").lower() or "generation" in s.get("name", "").lower()]
    print(f"  OQ generation operations: {len(oq_spans)}")

    # Check for tools
    tool_spans = [s for s in spans if s.get("span_type") == "tool"]
    print(f"  Tool executions: {len(tool_spans)}")

    print("\n" + "="*80)
    print("FORENSIC ANALYSIS COMPLETE")
    print("="*80)

if __name__ == "__main__":
    analyze_traces()
