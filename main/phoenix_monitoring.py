#!/usr/bin/env uv run python
"""
Phoenix Monitoring Script
Programmatic access to Phoenix traces for workflow monitoring and analysis
"""

import json
from datetime import UTC, datetime, timedelta

import pandas as pd
import phoenix as px


class PhoenixMonitor:
    """Monitor Phoenix traces for pharmaceutical workflow analysis."""

    def __init__(self, phoenix_url: str = "http://localhost:6006"):
        """Initialize Phoenix monitor."""
        self.client = px.Client(endpoint=phoenix_url)
        self.phoenix_url = phoenix_url

    def get_trace_summary(self, hours_back: int = 24) -> dict:
        """Get comprehensive trace summary for the last N hours."""
        try:
            spans_df = self.client.get_spans_dataframe()

            # Filter recent spans
            cutoff_time = datetime.now(UTC) - timedelta(hours=hours_back)
            recent_spans = spans_df[spans_df["start_time"] > cutoff_time]

            summary = {
                "phoenix_url": self.phoenix_url,
                "total_spans": len(spans_df),
                "recent_spans": len(recent_spans),
                "time_range_hours": hours_back,
                "cutoff_time": cutoff_time.isoformat(),
                "span_breakdown": {},
                "workflow_traces": {},
                "performance_metrics": {}
            }

            if len(recent_spans) > 0:
                # Span breakdown
                summary["span_breakdown"] = recent_spans["name"].value_counts().to_dict()

                # Time range
                summary["earliest_trace"] = recent_spans["start_time"].min().isoformat()
                summary["latest_trace"] = recent_spans["start_time"].max().isoformat()

                # Workflow-specific traces
                gamp_traces = recent_spans[recent_spans["name"].str.contains(
                    "GAMP|categorization|context|workflow", case=False, na=False
                )]

                if len(gamp_traces) > 0:
                    summary["workflow_traces"] = {
                        "gamp_workflow_spans": len(gamp_traces),
                        "workflow_operations": gamp_traces["name"].value_counts().to_dict(),
                        "avg_duration_ms": gamp_traces.get("latency_ms", pd.Series()).mean()
                    }

                # Performance metrics
                if "latency_ms" in recent_spans.columns:
                    summary["performance_metrics"] = {
                        "avg_latency_ms": recent_spans["latency_ms"].mean(),
                        "max_latency_ms": recent_spans["latency_ms"].max(),
                        "min_latency_ms": recent_spans["latency_ms"].min()
                    }

            return summary

        except Exception as e:
            return {"error": str(e), "phoenix_url": self.phoenix_url}

    def get_workflow_execution_details(self, workflow_name: str = "GAMP") -> dict:
        """Get detailed execution information for a specific workflow."""
        try:
            spans_df = self.client.get_spans_dataframe()

            # Filter workflow-related spans
            workflow_spans = spans_df[spans_df["name"].str.contains(
                workflow_name, case=False, na=False
            )]

            if len(workflow_spans) == 0:
                return {"message": f"No traces found for workflow: {workflow_name}"}

            # Group by trace_id to get complete workflow executions
            executions = []
            for trace_id in workflow_spans["trace_id"].unique():
                trace_spans = workflow_spans[workflow_spans["trace_id"] == trace_id]

                execution = {
                    "trace_id": trace_id,
                    "start_time": trace_spans["start_time"].min().isoformat(),
                    "end_time": trace_spans["start_time"].max().isoformat(),
                    "total_spans": len(trace_spans),
                    "operations": trace_spans["name"].tolist(),
                    "duration_breakdown": {}
                }

                if "latency_ms" in trace_spans.columns:
                    execution["total_duration_ms"] = trace_spans["latency_ms"].sum()
                    execution["duration_breakdown"] = dict(
                        zip(trace_spans["name"], trace_spans["latency_ms"], strict=False)
                    )

                executions.append(execution)

            return {
                "workflow_name": workflow_name,
                "total_executions": len(executions),
                "executions": executions[-5:]  # Last 5 executions
            }

        except Exception as e:
            return {"error": str(e)}

    def monitor_real_time(self, interval_seconds: int = 30, duration_minutes: int = 10):
        """Monitor Phoenix traces in real-time."""
        import time

        print("Starting real-time Phoenix monitoring...")
        print(f"Phoenix UI: {self.phoenix_url}")
        print(f"Monitoring for {duration_minutes} minutes, checking every {interval_seconds} seconds")
        print("="*60)

        end_time = datetime.now() + timedelta(minutes=duration_minutes)
        last_span_count = 0

        while datetime.now() < end_time:
            try:
                summary = self.get_trace_summary(hours_back=1)
                current_span_count = summary.get("recent_spans", 0)
                new_spans = current_span_count - last_span_count

                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] Spans: {current_span_count} (+{new_spans})")

                if new_spans > 0:
                    recent_operations = summary.get("span_breakdown", {})
                    top_operations = list(recent_operations.items())[:3]
                    print(f"  Recent operations: {top_operations}")

                last_span_count = current_span_count
                time.sleep(interval_seconds)

            except KeyboardInterrupt:
                print("\nMonitoring stopped by user")
                break
            except Exception as e:
                print(f"Error during monitoring: {e}")
                time.sleep(interval_seconds)

        print("Monitoring completed")

    def export_traces_report(self, output_file: str = "phoenix_traces_report.json"):
        """Export comprehensive traces report to JSON file."""
        try:
            report = {
                "generated_at": datetime.now(UTC).isoformat(),
                "phoenix_url": self.phoenix_url,
                "summary_24h": self.get_trace_summary(hours_back=24),
                "summary_1h": self.get_trace_summary(hours_back=1),
                "gamp_workflow_details": self.get_workflow_execution_details("GAMP"),
                "context_provider_details": self.get_workflow_execution_details("context"),
            }

            with open(output_file, "w") as f:
                json.dump(report, f, indent=2, default=str)

            print(f"Report exported to: {output_file}")
            return output_file

        except Exception as e:
            print(f"Error exporting report: {e}")
            return None


def main():
    """Main function for command-line usage."""
    import argparse

    parser = argparse.ArgumentParser(description="Phoenix Trace Monitor")
    parser.add_argument("--url", default="http://localhost:6006",
                       help="Phoenix server URL")
    parser.add_argument("--summary", action="store_true",
                       help="Show trace summary")
    parser.add_argument("--workflow", type=str, default="GAMP",
                       help="Show workflow execution details")
    parser.add_argument("--monitor", action="store_true",
                       help="Start real-time monitoring")
    parser.add_argument("--export", type=str,
                       help="Export traces report to file")
    parser.add_argument("--hours", type=int, default=24,
                       help="Hours back to analyze (default: 24)")

    args = parser.parse_args()

    monitor = PhoenixMonitor(phoenix_url=args.url)

    if args.summary:
        summary = monitor.get_trace_summary(hours_back=args.hours)
        print("Phoenix Trace Summary")
        print("="*50)
        print(json.dumps(summary, indent=2, default=str))

    if args.workflow:
        details = monitor.get_workflow_execution_details(args.workflow)
        print(f"{args.workflow} Workflow Details")
        print("="*50)
        print(json.dumps(details, indent=2, default=str))

    if args.monitor:
        monitor.monitor_real_time()

    if args.export:
        monitor.export_traces_report(args.export)


if __name__ == "__main__":
    main()
