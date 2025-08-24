#!/usr/bin/env uv run python
"""
Phoenix Direct Client Monitor (GraphQL Bypass)
Workaround for broken GraphQL API - uses direct Phoenix client for trace access

This script bypasses the broken GraphQL layer and accesses trace data directly
via the Phoenix Python client, providing the same monitoring functionality
as the original phoenix_monitoring.py script.
"""

import json
import sys
import time
from datetime import UTC, datetime, timedelta

import pandas as pd
import phoenix as px


class PhoenixDirectMonitor:
    """Monitor Phoenix traces using direct client (bypassing GraphQL)."""

    def __init__(self, phoenix_url: str = "http://localhost:6006"):
        """Initialize direct Phoenix monitor."""
        self.phoenix_url = phoenix_url
        print("🔧 Using Direct Client Mode (GraphQL Bypass)")
        print(f"📊 Phoenix URL: {phoenix_url}")

        try:
            self.client = px.Client(endpoint=phoenix_url)
            print("✅ Phoenix client initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize Phoenix client: {e}")
            print("🚨 Ensure Phoenix server is running at localhost:6006")
            sys.exit(1)

    def get_trace_summary(self, hours_back: int = 24) -> dict:
        """Get comprehensive trace summary for the last N hours."""
        try:
            print(f"📊 Retrieving spans data (last {hours_back} hours)...")
            spans_df = self.client.get_spans_dataframe()

            if len(spans_df) == 0:
                return {
                    "phoenix_url": self.phoenix_url,
                    "total_spans": 0,
                    "recent_spans": 0,
                    "message": "No traces found in database",
                    "time_range_hours": hours_back,
                }

            # Filter recent spans
            cutoff_time = datetime.now(UTC) - timedelta(hours=hours_back)
            recent_spans = spans_df[spans_df["start_time"] > cutoff_time]

            summary = {
                "phoenix_url": self.phoenix_url,
                "method": "direct_client_bypass",
                "total_spans": len(spans_df),
                "recent_spans": len(recent_spans),
                "time_range_hours": hours_back,
                "cutoff_time": cutoff_time.isoformat(),
                "span_breakdown": {},
                "workflow_traces": {},
                "performance_metrics": {},
                "data_integrity": {
                    "columns_available": list(spans_df.columns),
                    "trace_count": spans_df["trace_id"].nunique(),
                    "earliest_trace": spans_df["start_time"].min().isoformat(),
                    "latest_trace": spans_df["start_time"].max().isoformat(),
                }
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
            return {
                "error": str(e),
                "phoenix_url": self.phoenix_url,
                "method": "direct_client_bypass",
                "error_type": type(e).__name__
            }

    def get_workflow_execution_details(self, workflow_name: str = "GAMP") -> dict:
        """Get detailed execution information for a specific workflow."""
        try:
            print(f"🔍 Analyzing {workflow_name} workflow executions...")
            spans_df = self.client.get_spans_dataframe()

            if len(spans_df) == 0:
                return {"message": f"No trace data available for {workflow_name} analysis"}

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
                "method": "direct_client_bypass",
                "total_executions": len(executions),
                "executions": executions[-5:]  # Last 5 executions
            }

        except Exception as e:
            return {
                "error": str(e),
                "method": "direct_client_bypass",
                "error_type": type(e).__name__
            }

    def monitor_real_time(self, interval_seconds: int = 30, duration_minutes: int = 10):
        """Monitor Phoenix traces in real-time using direct client."""
        print("🚀 Starting Real-Time Phoenix Monitoring (Direct Client Mode)")
        print(f"📊 Phoenix URL: {self.phoenix_url}")
        print(f"🔄 Monitoring for {duration_minutes} minutes, checking every {interval_seconds} seconds")
        print("🔧 Bypassing broken GraphQL API")
        print("="*70)

        end_time = datetime.now() + timedelta(minutes=duration_minutes)
        last_span_count = 0

        while datetime.now() < end_time:
            try:
                summary = self.get_trace_summary(hours_back=1)
                current_span_count = summary.get("recent_spans", 0)
                new_spans = current_span_count - last_span_count

                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] Spans: {current_span_count} (+{new_spans}) [Direct Client]")

                if new_spans > 0:
                    recent_operations = summary.get("span_breakdown", {})
                    top_operations = list(recent_operations.items())[:3]
                    print(f"  Recent operations: {top_operations}")

                last_span_count = current_span_count
                time.sleep(interval_seconds)

            except KeyboardInterrupt:
                print("\n🛑 Monitoring stopped by user")
                break
            except Exception as e:
                print(f"❌ Error during monitoring: {e}")
                print("🔄 Retrying in 10 seconds...")
                time.sleep(10)

        print("✅ Monitoring completed")

    def export_traces_report(self, output_file: str = "phoenix_traces_report_direct.json"):
        """Export comprehensive traces report to JSON file using direct client."""
        try:
            print("📊 Generating comprehensive trace report...")

            report = {
                "generated_at": datetime.now(UTC).isoformat(),
                "phoenix_url": self.phoenix_url,
                "method": "direct_client_bypass",
                "graphql_status": "bypassed_due_to_errors",
                "summary_24h": self.get_trace_summary(hours_back=24),
                "summary_1h": self.get_trace_summary(hours_back=1),
                "gamp_workflow_details": self.get_workflow_execution_details("GAMP"),
                "context_provider_details": self.get_workflow_execution_details("context"),
            }

            with open(output_file, "w") as f:
                json.dump(report, f, indent=2, default=str)

            print(f"✅ Report exported to: {output_file}")
            return output_file

        except Exception as e:
            print(f"❌ Error exporting report: {e}")
            return None

    def validate_trace_access(self):
        """Validate that trace data is accessible via direct client."""
        print("\n🔍 Validating Direct Client Trace Access")
        print("-" * 50)

        try:
            spans_df = self.client.get_spans_dataframe()
            print(f"✅ Successfully retrieved {len(spans_df)} spans")

            if len(spans_df) > 0:
                print(f"📊 Unique traces: {spans_df['trace_id'].nunique()}")
                print(f"📅 Date range: {spans_df['start_time'].min()} to {spans_df['start_time'].max()}")
                print(f"📋 Available columns: {list(spans_df.columns)}")

                # Show sample spans
                print("\n📝 Sample Spans:")
                for idx, (_, row) in enumerate(spans_df.head(3).iterrows()):
                    print(f"   {idx+1}. {row['name']} (trace: {row['trace_id'][:8]}...)")

                print("\n✅ Direct client access working - GraphQL bypass successful!")
                return True
            print("⚠️ No spans found in database")
            print("🔧 This may indicate an empty database or connection issues")
            return False

        except Exception as e:
            print(f"❌ Direct client access failed: {e}")
            print("🚨 This indicates a deeper Phoenix connectivity issue")
            return False


def main():
    """Main function for direct client monitoring."""
    import argparse

    parser = argparse.ArgumentParser(description="Phoenix Direct Client Monitor (GraphQL Bypass)")
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
    parser.add_argument("--validate", action="store_true",
                       help="Validate trace access")

    args = parser.parse_args()

    print("🔧 Phoenix Direct Client Monitor")
    print("=" * 50)
    print("⚠️  WORKAROUND MODE: Bypassing broken GraphQL API")
    print("✅ Using direct Phoenix client for trace access")
    print()

    monitor = PhoenixDirectMonitor(phoenix_url=args.url)

    if args.validate:
        monitor.validate_trace_access()

    if args.summary:
        summary = monitor.get_trace_summary(hours_back=args.hours)
        print("\n📊 Phoenix Trace Summary (Direct Client)")
        print("="*60)
        print(json.dumps(summary, indent=2, default=str))

    if args.workflow:
        details = monitor.get_workflow_execution_details(args.workflow)
        print(f"\n🔍 {args.workflow} Workflow Details (Direct Client)")
        print("="*60)
        print(json.dumps(details, indent=2, default=str))

    if args.monitor:
        monitor.monitor_real_time()

    if args.export:
        monitor.export_traces_report(args.export)

    # If no arguments, show basic validation
    if not any([args.summary, args.workflow, args.monitor, args.export, args.validate]):
        monitor.validate_trace_access()


if __name__ == "__main__":
    main()
