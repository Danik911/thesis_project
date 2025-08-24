#!/usr/bin/env python
"""
Export Phoenix traces for Task 42 evidence collection.

This script collects all Phoenix trace data and cross-validation results
for the thesis evidence package.
"""

import json
import shutil
from datetime import datetime, UTC
from pathlib import Path
import sys

def export_phoenix_traces():
    """Export Phoenix traces and CV results for Task 42."""
    
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    
    # Create evidence directory
    evidence_dir = Path(f"THESIS_EVIDENCE_PACKAGE/01_TEST_EXECUTION_EVIDENCE/task42_phoenix_export_{timestamp}")
    evidence_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"[EXPORT] Creating evidence package in: {evidence_dir}")
    
    # 1. Copy all Phoenix trace files
    traces_dir = Path("logs/traces")
    if traces_dir.exists():
        trace_files = list(traces_dir.glob("*.jsonl"))
        print(f"[EXPORT] Found {len(trace_files)} trace files")
        
        # Create traces subdirectory
        export_traces_dir = evidence_dir / "phoenix_traces"
        export_traces_dir.mkdir(exist_ok=True)
        
        # Copy trace files
        for trace_file in trace_files:
            dest = export_traces_dir / trace_file.name
            shutil.copy2(trace_file, dest)
            
        print(f"[EXPORT] Copied {len(trace_files)} trace files to {export_traces_dir}")
    
    # 2. Copy CV checkpoint files
    checkpoint_dirs = list(Path(".").glob("**/checkpoints"))
    total_checkpoints = 0
    
    if checkpoint_dirs:
        export_checkpoints_dir = evidence_dir / "cv_checkpoints"
        export_checkpoints_dir.mkdir(exist_ok=True)
        
        for checkpoint_dir in checkpoint_dirs:
            checkpoint_files = list(checkpoint_dir.glob("*.json"))
            for checkpoint_file in checkpoint_files:
                dest = export_checkpoints_dir / checkpoint_file.name
                shutil.copy2(checkpoint_file, dest)
                total_checkpoints += 1
                
        print(f"[EXPORT] Copied {total_checkpoints} checkpoint files")
    
    # 3. Copy task42 result files
    task42_dirs = list(Path("THESIS_EVIDENCE_PACKAGE/01_TEST_EXECUTION_EVIDENCE").glob("task42_*"))
    
    if task42_dirs:
        export_results_dir = evidence_dir / "cv_results"
        export_results_dir.mkdir(exist_ok=True)
        
        for task42_dir in task42_dirs:
            # Copy JSON result files
            result_files = list(task42_dir.glob("*.json"))
            for result_file in result_files:
                dest = export_results_dir / f"{task42_dir.name}_{result_file.name}"
                shutil.copy2(result_file, dest)
                
        print(f"[EXPORT] Copied results from {len(task42_dirs)} Task 42 execution directories")
    
    # 4. Analyze trace statistics
    total_spans = 0
    trace_summary = {
        "export_timestamp": timestamp,
        "trace_files": len(trace_files) if traces_dir.exists() else 0,
        "checkpoint_files": total_checkpoints,
        "task42_executions": len(task42_dirs) if task42_dirs else 0,
        "spans_by_file": {}
    }
    
    if traces_dir.exists():
        for trace_file in trace_files:
            with open(trace_file, 'r') as f:
                lines = f.readlines()
                trace_summary["spans_by_file"][trace_file.name] = len(lines)
                total_spans += len(lines)
    
    trace_summary["total_spans"] = total_spans
    
    # Save summary
    summary_file = evidence_dir / "export_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(trace_summary, f, indent=2)
    
    print("\n" + "=" * 80)
    print("TASK 42 EVIDENCE EXPORT COMPLETE")
    print("=" * 80)
    print(f"Evidence Directory: {evidence_dir}")
    print(f"Total Trace Files: {trace_summary['trace_files']}")
    print(f"Total Spans Captured: {total_spans:,}")
    print(f"Checkpoint Files: {total_checkpoints}")
    print(f"Task 42 Executions: {trace_summary['task42_executions']}")
    print("=" * 80)
    
    # Create final report
    report = {
        "task_42_evidence_export": {
            "export_date": timestamp,
            "evidence_location": str(evidence_dir),
            "phoenix_monitoring": {
                "total_spans": total_spans,
                "trace_files": trace_summary['trace_files'],
                "average_spans_per_file": total_spans // trace_summary['trace_files'] if trace_summary['trace_files'] > 0 else 0
            },
            "cross_validation": {
                "checkpoint_files": total_checkpoints,
                "execution_attempts": trace_summary['task42_executions']
            },
            "thesis_requirement": {
                "target_spans": 2210,
                "achievement_percentage": (total_spans / 2210 * 100) if total_spans > 0 else 0,
                "status": "EXCEEDED" if total_spans > 2210 else "IN_PROGRESS"
            }
        }
    }
    
    # Save final report
    report_file = evidence_dir / "task42_evidence_report.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nFinal report saved to: {report_file}")
    print(f"Thesis requirement achievement: {report['task_42_evidence_export']['thesis_requirement']['achievement_percentage']:.1f}%")
    
    return evidence_dir

if __name__ == "__main__":
    export_phoenix_traces()