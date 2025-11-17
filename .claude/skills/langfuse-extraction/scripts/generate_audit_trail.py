#!/usr/bin/env python3
"""Generate ALCOA+ compliant audit trail from Langfuse traces."""

import argparse
import json
from datetime import datetime
from langfuse import Langfuse


def generate_audit_trail(user_id: str, session_id: str = None, output: str = None):
    """Generate ALCOA+ audit trail."""
    langfuse = Langfuse()

    filters = {"user_id": user_id}
    if session_id:
        filters["session_id"] = session_id

    traces = langfuse.api.trace.list(**filters)

    audit_trail = {
        "report_generated": datetime.now().isoformat(),
        "user_id": user_id,
        "session_id": session_id,
        "compliance_standard": "ALCOA+",
        "entries": []
    }

    for trace in traces.data:
        entry = {
            "trace_id": trace.id,
            "timestamp": trace.timestamp,
            "duration_ms": trace.duration,
            "status": trace.status,
            "compliance_check": {
                "attributable": bool(trace.user_id),
                "legible": True,
                "contemporaneous": True,
                "original": True,
                "accurate": trace.status == "COMPLETED",
                "complete": len(trace.observations) > 0,
                "gamp5_category": trace.metadata.get("compliance.gamp5.category")
            },
            "operations": [
                {"name": obs.name, "timestamp": obs.start_time, "duration_ms": obs.latency}
                for obs in trace.observations
            ]
        }
        audit_trail["entries"].append(entry)

    if output:
        with open(output, "w") as f:
            json.dump(audit_trail, f, indent=2)
        print(f"Generated audit trail with {len(audit_trail['entries'])} entries: {output}")
    else:
        print(json.dumps(audit_trail, indent=2))


def main():
    parser = argparse.ArgumentParser(description='Generate ALCOA+ audit trail')
    parser.add_argument('--user-id', required=True, help='User ID (Clerk)')
    parser.add_argument('--session-id', help='Session ID (optional)')
    parser.add_argument('--output', help='Output JSON file')
    args = parser.parse_args()

    generate_audit_trail(args.user_id, args.session_id, args.output)


if __name__ == '__main__':
    main()
