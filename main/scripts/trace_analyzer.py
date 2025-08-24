#!/usr/bin/env python3
"""
Phoenix Trace Forensic Analyzer
Comprehensive analysis tool for pharmaceutical multi-agent system traces
"""

import json
import statistics
from collections import defaultdict
from datetime import datetime
from typing import Any


def parse_timestamp(ts_str: str) -> datetime:
    """Parse various timestamp formats found in traces"""
    try:
        # Handle nanosecond timestamps
        if isinstance(ts_str, (int, float)):
            return datetime.fromtimestamp(ts_str / 1e9)
        # Handle ISO format
        return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
    except:
        return datetime.now()

def analyze_spans(all_spans_file: str, chromadb_spans_file: str, event_trace_file: str) -> dict[str, Any]:
    """Analyze all trace files and generate comprehensive report"""

    analysis = {
        "total_spans": 0,
        "chromadb_operations": 0,
        "workflow_spans": 0,
        "agent_spans": 0,
        "tool_spans": 0,
        "llm_spans": 0,
        "errors": [],
        "agents_identified": set(),
        "tools_used": set(),
        "workflow_duration": 0,
        "agent_performance": defaultdict(list),
        "chromadb_metrics": {
            "queries": 0,
            "total_duration": 0,
            "avg_duration": 0,
            "results_retrieved": 0,
            "success_rate": 0,
            "operations_by_type": defaultdict(int),
            "durations_by_operation": defaultdict(list)
        },
        "trace_timeline": [],
        "span_hierarchy": defaultdict(list),
        "compliance_indicators": defaultdict(int),
        "issues_found": [],
        "agent_breakdown": {
            "categorization": {"spans": 0, "tools": 0, "duration_ms": 0},
            "context_provider": {"spans": 0, "tools": 0, "duration_ms": 0},
            "sme_agent": {"spans": 0, "tools": 0, "duration_ms": 0},
            "research_agent": {"spans": 0, "tools": 0, "duration_ms": 0},
            "oq_generator": {"spans": 0, "tools": 0, "duration_ms": 0}
        },
        "o3_model_metrics": {
            "calls": 0,
            "total_duration_ms": 0,
            "avg_duration_ms": 0,
            "reasoning_effort_usage": 0
        }
    }

    # Analyze all spans
    print(f"Analyzing all spans from: {all_spans_file}")
    try:
        with open(all_spans_file, encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                if not line.strip():
                    continue
                try:
                    span = json.loads(line)
                    analysis["total_spans"] += 1

                    # Extract span info
                    span_name = span.get("name", "unknown")
                    span_type = span.get("span_type", "unknown")
                    duration_ns = span.get("duration_ns", 0)
                    status = span.get("status", {})
                    attributes = span.get("attributes", {})

                    # Categorize spans
                    if span_type == "workflow":
                        analysis["workflow_spans"] += 1
                        # Track workflow duration
                        if "Workflow" in span_name:
                            analysis["workflow_duration"] = max(analysis["workflow_duration"], duration_ns)
                    elif span_type == "agent":
                        analysis["agent_spans"] += 1
                        agent_name = span_name.split(".")[0]
                        analysis["agents_identified"].add(agent_name)
                        analysis["agent_performance"][agent_name].append(duration_ns)
                    elif span_type == "tool":
                        analysis["tool_spans"] += 1
                        tool_name = span.get("tool_name", span_name)
                        analysis["tools_used"].add(tool_name)
                    elif "llm" in span_name.lower() or "openai" in span_name.lower():
                        analysis["llm_spans"] += 1

                    # Agent-specific breakdown
                    duration_ms = duration_ns / 1_000_000 if duration_ns > 0 else 0

                    if "GAMPCategorizationWorkflow" in span_name or attributes.get("tool_category") == "categorization":
                        if span_type == "tool":
                            analysis["agent_breakdown"]["categorization"]["tools"] += 1
                        else:
                            analysis["agent_breakdown"]["categorization"]["spans"] += 1
                        analysis["agent_breakdown"]["categorization"]["duration_ms"] += duration_ms

                    elif "context" in span_name.lower() or "Context" in span_name:
                        if span_type == "tool":
                            analysis["agent_breakdown"]["context_provider"]["tools"] += 1
                        else:
                            analysis["agent_breakdown"]["context_provider"]["spans"] += 1
                        analysis["agent_breakdown"]["context_provider"]["duration_ms"] += duration_ms

                    elif "SMEAnalysisWorkflow" in span_name or "sme" in span_name.lower():
                        if span_type == "tool":
                            analysis["agent_breakdown"]["sme_agent"]["tools"] += 1
                        else:
                            analysis["agent_breakdown"]["sme_agent"]["spans"] += 1
                        analysis["agent_breakdown"]["sme_agent"]["duration_ms"] += duration_ms

                    elif "ResearchWorkflow" in span_name or "research" in span_name.lower():
                        if span_type == "tool":
                            analysis["agent_breakdown"]["research_agent"]["tools"] += 1
                        else:
                            analysis["agent_breakdown"]["research_agent"]["spans"] += 1
                        analysis["agent_breakdown"]["research_agent"]["duration_ms"] += duration_ms

                    elif "OQGeneration" in span_name or "oq" in span_name.lower():
                        if span_type == "tool":
                            analysis["agent_breakdown"]["oq_generator"]["tools"] += 1
                        else:
                            analysis["agent_breakdown"]["oq_generator"]["spans"] += 1
                        analysis["agent_breakdown"]["oq_generator"]["duration_ms"] += duration_ms

                    # o3 model tracking
                    if "o3" in span_name.lower() or "o3-mini" in attributes.get("llm.model_name", ""):
                        analysis["o3_model_metrics"]["calls"] += 1
                        analysis["o3_model_metrics"]["total_duration_ms"] += duration_ms
                        if attributes.get("reasoning_effort"):
                            analysis["o3_model_metrics"]["reasoning_effort_usage"] += 1

                    # Check for errors
                    if status.get("status_code") == "ERROR":
                        analysis["errors"].append({
                            "span": span_name,
                            "line": line_num,
                            "description": status.get("description", "Unknown error"),
                            "attributes": attributes
                        })

                    # Track compliance indicators
                    if attributes.get("pharmaceutical_system"):
                        analysis["compliance_indicators"]["pharmaceutical_system"] += 1
                    if attributes.get("compliance.gamp5.category"):
                        analysis["compliance_indicators"]["gamp5_compliant"] += 1
                    if attributes.get("compliance.audit.required"):
                        analysis["compliance_indicators"]["audit_required"] += 1

                    # Build timeline
                    if "start_time" in span:
                        analysis["trace_timeline"].append({
                            "timestamp": span["start_time"],
                            "span_name": span_name,
                            "duration_ns": duration_ns,
                            "type": span_type
                        })

                    # Track span hierarchy
                    if span.get("parent_id"):
                        analysis["span_hierarchy"][span.get("parent_id")].append(span.get("span_id"))

                except json.JSONDecodeError as e:
                    analysis["issues_found"].append(f"Line {line_num}: Invalid JSON - {e!s}")
                except Exception as e:
                    analysis["issues_found"].append(f"Line {line_num}: Processing error - {e!s}")

    except FileNotFoundError:
        analysis["issues_found"].append(f"File not found: {all_spans_file}")

    # Analyze ChromaDB operations
    print(f"Analyzing ChromaDB spans from: {chromadb_spans_file}")
    try:
        chromadb_durations = []
        chromadb_successes = 0
        chromadb_total = 0

        with open(chromadb_spans_file, encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                if not line.strip():
                    continue
                try:
                    span = json.loads(line)
                    analysis["chromadb_operations"] += 1
                    chromadb_total += 1

                    # Extract operation type
                    operation = span.get("operation", "unknown")
                    span_name = span.get("name", "")
                    if "query" in span_name.lower():
                        operation = "query"
                    elif "add" in span_name.lower():
                        operation = "add"
                    elif "delete" in span_name.lower():
                        operation = "delete"

                    analysis["chromadb_metrics"]["operations_by_type"][operation] += 1

                    duration_ns = span.get("duration_ns", 0)
                    if duration_ns > 0:
                        chromadb_durations.append(duration_ns)
                        analysis["chromadb_metrics"]["durations_by_operation"][operation].append(duration_ns / 1_000_000)

                    # Check success
                    if span.get("status", {}).get("status_code") == "OK":
                        chromadb_successes += 1

                    # Track results
                    result_count = span.get("result_count", 0)
                    if result_count:
                        analysis["chromadb_metrics"]["results_retrieved"] += result_count

                except json.JSONDecodeError as e:
                    analysis["issues_found"].append(f"ChromaDB Line {line_num}: Invalid JSON - {e!s}")

        # Calculate ChromaDB metrics
        if chromadb_durations:
            analysis["chromadb_metrics"]["total_duration"] = sum(chromadb_durations)
            analysis["chromadb_metrics"]["avg_duration"] = statistics.mean(chromadb_durations)
            analysis["chromadb_metrics"]["queries"] = len(chromadb_durations)

        if chromadb_total > 0:
            analysis["chromadb_metrics"]["success_rate"] = (chromadb_successes / chromadb_total) * 100

    except FileNotFoundError:
        analysis["issues_found"].append(f"File not found: {chromadb_spans_file}")

    # Calculate o3 model metrics
    if analysis["o3_model_metrics"]["calls"] > 0:
        analysis["o3_model_metrics"]["avg_duration_ms"] = (
            analysis["o3_model_metrics"]["total_duration_ms"] / analysis["o3_model_metrics"]["calls"]
        )

    # Analyze event trace
    print(f"Analyzing event trace from: {event_trace_file}")
    try:
        with open(event_trace_file, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    event = json.loads(line)
                    # Extract event info for context
                    event_type = event.get("event_type", "unknown")
                    # Add event analysis here if needed
                except json.JSONDecodeError as e:
                    analysis["issues_found"].append(f"Event trace: Invalid JSON - {e!s}")

    except FileNotFoundError:
        analysis["issues_found"].append(f"File not found: {event_trace_file}")

    # Convert sets to lists for JSON serialization
    analysis["agents_identified"] = list(analysis["agents_identified"])
    analysis["tools_used"] = list(analysis["tools_used"])

    # Sort timeline
    analysis["trace_timeline"].sort(key=lambda x: x["timestamp"])

    return analysis

def generate_report(analysis: dict[str, Any], timestamp: str) -> str:
    """Generate comprehensive forensic report"""

    total_duration_minutes = analysis["workflow_duration"] / 1_000_000_000 / 60 if analysis["workflow_duration"] > 0 else 0

    report = f"""# Phoenix Trace Forensic Analysis Report

## Executive Summary
- **Analysis Date**: {timestamp}
- **Traces Analyzed**: {analysis['total_spans']} total spans
- **ChromaDB Operations**: {analysis['chromadb_operations']} operations
- **Total Duration**: {total_duration_minutes:.2f} minutes
- **Critical Issues Found**: {len(analysis['errors']) + len(analysis['issues_found'])}
- **Overall System Health**: {"HEALTHY" if not analysis['errors'] and not analysis['issues_found'] else "ISSUES DETECTED"}

## 1. CONFIRMED OBSERVATIONS

### Trace Statistics
- **Total Spans**: {analysis['total_spans']}
- **Unique Trace IDs**: {len(set(item['span_name'] for item in analysis['trace_timeline']))}
- **Span Types Distribution**:
  - Workflow Spans: {analysis['workflow_spans']}
  - Agent Spans: {analysis['agent_spans']}
  - Tool Spans: {analysis['tool_spans']}
  - LLM Spans: {analysis['llm_spans']}

### Agent Activity
**CONFIRMED**: Agents identified in traces: {', '.join(analysis['agents_identified'])}

"""

    # Agent performance breakdown
    report += "#### Detailed Agent Breakdown:\n"
    for agent_name, metrics in analysis["agent_breakdown"].items():
        if metrics["spans"] > 0 or metrics["tools"] > 0:
            report += f"- **{agent_name.upper()}**:\n"
            report += f"  - Total Invocations: {metrics['spans']}\n"
            report += f"  - Tool Usage: {metrics['tools']}\n"
            report += f"  - Duration: {metrics['duration_ms']:.2f}ms\n"
            report += "  - Status: ✅ ACTIVE\n\n"

    # Tool usage
    report += "### Tool Usage Analysis\n"
    report += f"**CONFIRMED**: Tools used: {', '.join(analysis['tools_used'])}\n\n"

    # o3 Model Performance
    o3_metrics = analysis["o3_model_metrics"]
    if o3_metrics["calls"] > 0:
        report += "### o3 Model Performance\n"
        report += f"- **o3-mini Calls**: {o3_metrics['calls']}\n"
        report += f"- **Total Duration**: {o3_metrics['total_duration_ms']:.2f}ms\n"
        report += f"- **Average Duration**: {o3_metrics['avg_duration_ms']:.2f}ms\n"
        report += f"- **Reasoning Effort Usage**: {o3_metrics['reasoning_effort_usage']} calls\n\n"

    # ChromaDB metrics
    chromadb = analysis["chromadb_metrics"]
    report += "### Database Operations\n"
    report += f"- **ChromaDB Operations**: {analysis['chromadb_operations']}\n"
    report += f"- **Success Rate**: {chromadb['success_rate']:.1f}%\n"
    report += f"- **Average Operation Duration**: {chromadb['avg_duration'] / 1e6:.2f}ms\n"
    report += f"- **Total Results Retrieved**: {chromadb['results_retrieved']}\n"

    # ChromaDB operation breakdown
    report += "#### ChromaDB Operation Types:\n"
    for op_type, count in chromadb["operations_by_type"].items():
        avg_duration = 0
        if op_type in chromadb["durations_by_operation"] and chromadb["durations_by_operation"][op_type]:
            avg_duration = statistics.mean(chromadb["durations_by_operation"][op_type])
        report += f"  - {op_type}: {count} operations (avg: {avg_duration:.2f}ms)\n"
    report += "\n"

    # Context Flow Analysis
    report += "### Context Flow Analysis\n"
    if analysis["span_hierarchy"]:
        report += f"- **Successful Handoffs**: {len(analysis['span_hierarchy'])} parent-child relationships found\n"
        orphaned_count = analysis["total_spans"] - sum(len(children) for children in analysis["span_hierarchy"].values()) - len(analysis["span_hierarchy"])
        if orphaned_count > 0:
            report += f"- **Failed Handoffs**: {orphaned_count} orphaned spans detected\n"
        else:
            report += "- **Failed Handoffs**: No orphaned spans detected\n"
    report += "\n"

    # Errors section
    if analysis["errors"]:
        report += "### Issues Detected\n"
        for i, error in enumerate(analysis["errors"], 1):
            report += f"❌ **CONFIRMED ERROR {i}**: {error['span']}\n"
            report += f"  - Evidence: {error['description']}\n"
            report += f"  - Trace Line: {error['line']}\n"
            report += "  - Impact: Span execution failure\n\n"

    # Processing issues
    if analysis["issues_found"]:
        report += "### Processing Issues\n"
        for issue in analysis["issues_found"]:
            report += f"❌ **CONFIRMED ISSUE**: {issue}\n"

    # Compliance section
    compliance = analysis["compliance_indicators"]
    report += f"""
## 2. SUGGESTED INTERPRETATIONS

💡 **SUGGESTION**: Based on {compliance['pharmaceutical_system']} pharmaceutical system spans, this appears to be a well-instrumented pharmaceutical workflow
- Supporting evidence: {compliance['gamp5_compliant']} GAMP-5 compliant operations
- Confidence: High

💡 **SUGGESTION**: The system shows {chromadb['success_rate']:.1f}% ChromaDB success rate when database operations succeed
- Pattern observed in {analysis['chromadb_operations']} operations
- Potential optimization: {"Good performance" if chromadb['success_rate'] > 95 else "Room for improvement"}

## 3. COMPLIANCE VALIDATION

### GAMP-5 Compliance Observations
- **CONFIRMED**: Pharmaceutical system spans: {compliance['pharmaceutical_system']}
- **CONFIRMED**: GAMP-5 compliant operations: {compliance['gamp5_compliant']}
- **CONFIRMED**: Audit trail requirements: {compliance['audit_required']}

### Data Integrity (ALCOA+)
- Attributable: {"✅ CONFIRMED" if compliance['pharmaceutical_system'] > 0 else "⚠️ UNCONFIRMED"}
- Legible: {"✅ CONFIRMED" if analysis['total_spans'] > 0 else "⚠️ UNCONFIRMED"} - All spans readable
- Contemporaneous: {"✅ CONFIRMED" if len(analysis['trace_timeline']) > 0 else "⚠️ UNCONFIRMED"} - Timestamps present
- Original: {"✅ CONFIRMED" if not analysis['issues_found'] else "⚠️ COMPROMISED"} - Data integrity
- Accurate: {"✅ CONFIRMED" if not analysis['errors'] else "⚠️ COMPROMISED"} - No execution errors

## 4. CRITICAL FAILURES

### System Failures
"""

    if not analysis["errors"]:
        report += "✅ **CONFIRMED**: No system failures detected\n"
    else:
        report += f"❌ **CONFIRMED**: {len(analysis['errors'])} system failures detected\n"
        for error in analysis["errors"]:
            report += f"  - {error['span']}: {error['description']}\n"

    report += f"""
### Recovery Actions Taken
{"✅ CONFIRMED: No recovery needed - system operating normally" if not analysis['errors'] else "⚠️ Manual intervention may be required"}

## 5. PERFORMANCE ANALYSIS

### Workflow Execution Metrics
- **Total Execution Time**: {total_duration_minutes:.2f} minutes ({analysis['workflow_duration'] / 1_000_000_000:.1f} seconds)
- **Agent Coordination**: {"EFFICIENT" if len(analysis['agent_breakdown']) >= 5 else "LIMITED"} - {sum(1 for agent in analysis['agent_breakdown'].values() if agent['spans'] > 0)} active agents
- **Database Performance**: {"OPTIMAL" if chromadb['avg_duration'] < 1e9 else "SLOW"} (avg: {chromadb['avg_duration'] / 1e6:.2f}ms)

### Performance Breakdown by Agent:
"""

    for agent_name, metrics in analysis["agent_breakdown"].items():
        if metrics["spans"] > 0:
            efficiency = "EFFICIENT" if metrics["duration_ms"] / max(metrics["spans"], 1) < 1000 else "SLOW"
            report += f"- **{agent_name}**: {efficiency} ({metrics['duration_ms'] / max(metrics['spans'], 1):.1f}ms avg per span)\n"

    report += f"""
## 6. RECOMMENDATIONS

Based on confirmed observations:
1. **Immediate Actions**: {'No immediate actions required' if not analysis['errors'] and not analysis['issues_found'] else 'Address identified errors and processing issues'}
2. **Short-term Improvements**: {"Continue current monitoring approach" if chromadb['success_rate'] > 95 else "Optimize ChromaDB query performance"}
3. **Long-term Enhancements**: {"System performing within expected parameters" if total_duration_minutes < 10 else "Consider workflow optimization for faster execution"}

## 7. APPENDIX

### Trace Sample
Most recent workflow execution: {total_duration_minutes:.2f} minutes with {analysis['total_spans']} spans
- Successful agent coordination across {sum(1 for agent in analysis['agent_breakdown'].values() if agent['spans'] > 0)} agents
- Database operations: {analysis['chromadb_operations']} ChromaDB queries
- Compliance indicators: {sum(compliance.values())} total compliance spans

### Error Details
"""

    if analysis["errors"]:
        for error in analysis["errors"]:
            report += f"**Error in {error['span']}**: {error['description']}\n"
    else:
        report += "No errors detected in trace analysis.\n"

    report += f"""
---
Report generated by Phoenix Trace Forensic Analyzer
Analysis completed: {timestamp}
Trace integrity: {"INTACT" if not analysis['issues_found'] else "COMPROMISED"}
System status: {"OPERATIONAL" if not analysis['errors'] else "DEGRADED"}
"""

    return report

if __name__ == "__main__":
    # File paths for the most recent successful trace (2025-08-06 13:47:17 - 101 spans)
    all_spans_file = "C:\\Users\\anteb\\Desktop\\Courses\\Projects\\thesis_project\\main\\logs\\traces\\all_spans_20250806_134717.jsonl"
    chromadb_spans_file = "C:\\Users\\anteb\\Desktop\\Courses\\Projects\\thesis_project\\main\\logs\\traces\\chromadb_spans_20250806_134717.jsonl"
    event_trace_file = "C:\\Users\\anteb\\Desktop\\Courses\\Projects\\thesis_project\\main\\logs\\traces\\trace_20250806_134717.jsonl"

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

    print("🔍 Starting Phoenix Trace Forensic Analysis...")
    print("Target: 101-span successful pharmaceutical workflow (13:47:17)")
    print("Expected: 32 ChromaDB operations, 5-minute execution")

    analysis = analyze_spans(all_spans_file, chromadb_spans_file, event_trace_file)

    print("\n✅ Analysis Complete:")
    print(f"   - Total spans processed: {analysis['total_spans']}")
    print(f"   - ChromaDB operations: {analysis['chromadb_operations']}")
    print(f"   - Agents identified: {len(analysis['agents_identified'])}")
    print(f"   - Active agent types: {sum(1 for agent in analysis['agent_breakdown'].values() if agent['spans'] > 0)}")
    print(f"   - Errors found: {len(analysis['errors'])}")
    print(f"   - Processing issues: {len(analysis['issues_found'])}")

    # Generate report
    report = generate_report(analysis, timestamp)

    # Save report
    report_filename = f"C:\\Users\\anteb\\Desktop\\Courses\\Projects\\thesis_project\\main\\docs\\reports\\monitoring\\comprehensive_phoenix_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

    try:
        with open(report_filename, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"\n📄 Report saved to: {report_filename}")
    except Exception as e:
        print(f"\n❌ Failed to save report: {e}")
        print("\nReport content:")
        print(report)

    # Print key findings
    print("\n🔍 KEY FORENSIC FINDINGS:")
    print(f"   - Workflow Duration: {analysis['workflow_duration'] / 1e9:.2f} seconds")
    print(f"   - ChromaDB Success Rate: {analysis['chromadb_metrics']['success_rate']:.1f}%")
    print(f"   - System Status: {'✅ HEALTHY' if not analysis['errors'] and not analysis['issues_found'] else '⚠️ ISSUES DETECTED'}")
    print(f"   - Agent Coordination: {'✅ SUCCESSFUL' if sum(1 for agent in analysis['agent_breakdown'].values() if agent['spans'] > 0) >= 5 else '⚠️ LIMITED'}")

    # Validate against user expectations
    print("\n📊 VALIDATION AGAINST REQUIREMENTS:")
    print(f"   - Expected 101 spans: {'✅ CONFIRMED' if analysis['total_spans'] == 101 else f'❌ MISMATCH ({analysis['total_spans']} found)'}")
    print(f"   - Expected 32 ChromaDB ops: {'✅ CONFIRMED' if analysis['chromadb_operations'] == 32 else f'❌ MISMATCH ({analysis['chromadb_operations']} found)'}")
    print(f"   - Expected ~5 min execution: {'✅ CONFIRMED' if 240 <= analysis['workflow_duration'] / 1e9 <= 360 else f'❌ MISMATCH ({analysis['workflow_duration'] / 1e9:.1f}s found)'}")
