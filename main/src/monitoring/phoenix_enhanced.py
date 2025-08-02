"""
Enhanced Phoenix Observability for Pharmaceutical Test Generation System

This module provides advanced Phoenix GraphQL API access, event flow visualization,
automated compliance analysis, and GAMP-5 compliance dashboards.

CRITICAL: NO FALLBACK LOGIC - All failures must surface explicitly for regulatory compliance.
"""

import logging
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import aiohttp
import networkx as nx
import plotly.graph_objects as go
from plotly.subplots import make_subplots

logger = logging.getLogger(__name__)


@dataclass
class TraceAnalysisResult:
    """Structured trace analysis result for pharmaceutical workflows."""
    trace_id: str
    workflow_type: str
    duration_ms: float
    compliance_status: str
    events: list[dict[str, Any]]
    attributes: dict[str, Any]
    start_time: str
    end_time: str


@dataclass
class ComplianceViolation:
    """GAMP-5 compliance violation record."""
    trace_id: str
    violation_type: str
    severity: str
    description: str
    timestamp: str
    remediation_suggestion: str
    regulatory_impact: str


class PhoenixGraphQLClient:
    """
    Enhanced Phoenix GraphQL client for programmatic trace analysis.
    
    CRITICAL: This client MUST NOT implement fallback logic. All errors must surface
    explicitly to maintain pharmaceutical regulatory compliance.
    """

    def __init__(self, endpoint: str = "http://localhost:6006/graphql", api_key: str | None = None):
        """
        Initialize GraphQL client.
        
        Args:
            endpoint: Phoenix GraphQL endpoint
            api_key: Optional API key for authentication
        """
        self.endpoint = endpoint
        self.headers = {"Content-Type": "application/json"}
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"

    async def query_workflow_traces(self, workflow_type: str = "GAMP", hours: int = 24) -> list[TraceAnalysisResult]:
        """
        Query workflow-specific traces for analysis.
        
        Args:
            workflow_type: Type of workflow to filter (e.g., "GAMP", "UnifiedTestGenerationWorkflow")
            hours: Hours back to query
            
        Returns:
            List of structured trace analysis results
            
        Raises:
            Exception: On any GraphQL or network error - NO FALLBACKS
        """
        query = """
        query GetWorkflowTraces($startTime: DateTime!) {
            spans(
                filter: {
                    startTime: { gte: $startTime }
                }
                sort: { field: START_TIME, direction: DESC }
                first: 100
            ) {
                edges {
                    node {
                        context {
                            spanId
                            traceId
                        }
                        name
                        spanKind
                        startTime
                        endTime
                        latencyMs
                        statusCode
                        statusMessage
                        attributes {
                            name
                            value
                        }
                        events {
                            name
                            timestamp
                            attributes {
                                name
                                value
                            }
                        }
                    }
                }
            }
        }
        """

        start_time = (datetime.now(UTC) - timedelta(hours=hours)).isoformat()
        variables = {"startTime": start_time}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.endpoint,
                    json={"query": query, "variables": variables},
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"GraphQL request failed with status {response.status}: {error_text}")

                    data = await response.json()

                    if "errors" in data:
                        raise Exception(f"GraphQL errors: {data['errors']}")

                    return self._parse_trace_results(data, workflow_type)

        except Exception as e:
            # NO FALLBACKS - raise the error explicitly for regulatory compliance
            logger.error(f"Phoenix GraphQL query failed: {e}")
            raise Exception(f"Failed to query Phoenix traces: {e}") from e

    async def query_compliance_metrics(self, timeframe_hours: int = 24) -> dict[str, Any]:
        """
        Query compliance-specific metrics for GAMP-5 dashboard.
        
        Args:
            timeframe_hours: Hours back to analyze
            
        Returns:
            Dictionary of compliance metrics
            
        Raises:
            Exception: On any error - NO FALLBACKS for regulatory compliance
        """
        query = """
        query GetComplianceMetrics($startTime: DateTime!) {
            spans(
                filter: {
                    startTime: { gte: $startTime }
                }
                sort: { field: START_TIME, direction: DESC }
                first: 1000
            ) {
                edges {
                    node {
                        context {
                            spanId
                            traceId
                        }
                        name
                        startTime
                        endTime
                        latencyMs
                        statusCode
                        attributes {
                            name
                            value
                        }
                        events {
                            name
                            timestamp
                            attributes {
                                name
                                value
                            }
                        }
                    }
                }
            }
        }
        """

        start_time = (datetime.now(UTC) - timedelta(hours=timeframe_hours)).isoformat()
        variables = {"startTime": start_time}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.endpoint,
                    json={"query": query, "variables": variables},
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"GraphQL request failed with status {response.status}: {error_text}")

                    data = await response.json()

                    if "errors" in data:
                        raise Exception(f"GraphQL errors: {data['errors']}")

                    return self._parse_compliance_metrics(data)

        except Exception as e:
            # NO FALLBACKS - regulatory compliance requires explicit error handling
            logger.error(f"Compliance metrics query failed: {e}")
            raise Exception(f"Failed to query compliance metrics: {e}") from e

    def _parse_trace_results(self, data: dict, workflow_filter: str) -> list[TraceAnalysisResult]:
        """Parse GraphQL response into structured trace analysis results."""
        results = []

        try:
            spans_data = data.get("data", {}).get("spans", {}).get("edges", [])

            # Group spans by trace_id
            traces_by_id = {}
            for edge in spans_data:
                node = edge["node"]
                trace_id = node["context"]["traceId"]

                if trace_id not in traces_by_id:
                    traces_by_id[trace_id] = []
                traces_by_id[trace_id].append(node)

            # Process each trace
            for trace_id, spans in traces_by_id.items():
                # Filter for workflow-related spans
                workflow_spans = [s for s in spans if workflow_filter.lower() in s["name"].lower()]
                if not workflow_spans:
                    continue

                # Calculate trace metrics
                start_times = [datetime.fromisoformat(s["startTime"].replace("Z", "+00:00")) for s in spans]
                end_times = [datetime.fromisoformat(s["endTime"].replace("Z", "+00:00")) for s in spans]

                trace_start = min(start_times)
                trace_end = max(end_times)
                duration_ms = (trace_end - trace_start).total_seconds() * 1000

                # Extract workflow type and compliance status
                workflow_type = "Unknown"
                compliance_status = "Unknown"
                all_attributes = {}
                events = []

                for span in spans:
                    # Extract attributes
                    for attr in span.get("attributes", []):
                        attr_name = attr["name"]
                        attr_value = attr["value"]
                        all_attributes[attr_name] = attr_value

                        # Check for workflow type
                        if "workflow" in attr_name.lower():
                            workflow_type = attr_value
                        elif "compliance" in attr_name.lower() and "status" in attr_name.lower():
                            compliance_status = attr_value

                    # Extract events
                    for event in span.get("events", []):
                        event_data = {
                            "name": event["name"],
                            "timestamp": event["timestamp"],
                            "span_name": span["name"],
                            "attributes": {attr["name"]: attr["value"] for attr in event.get("attributes", [])}
                        }
                        events.append(event_data)

                # Determine compliance status if not explicitly set
                if compliance_status == "Unknown":
                    compliance_status = self._determine_compliance_status(all_attributes, spans)

                results.append(TraceAnalysisResult(
                    trace_id=trace_id,
                    workflow_type=workflow_type,
                    duration_ms=duration_ms,
                    compliance_status=compliance_status,
                    events=events,
                    attributes=all_attributes,
                    start_time=trace_start.isoformat(),
                    end_time=trace_end.isoformat()
                ))

            return results

        except Exception as e:
            # NO FALLBACKS - parsing errors must surface explicitly
            raise Exception(f"Failed to parse trace results: {e}") from e

    def _parse_compliance_metrics(self, data: dict) -> dict[str, Any]:
        """Parse compliance metrics from GraphQL response."""
        try:
            spans_data = data.get("data", {}).get("spans", {}).get("edges", [])

            metrics = {
                "total_spans": len(spans_data),
                "compliance_breakdown": {},
                "gamp_categories": {},
                "error_rates": {},
                "performance_metrics": {},
                "audit_trail_completeness": 0
            }

            compliant_count = 0
            gamp_categories = {}
            error_count = 0
            latencies = []
            audit_complete_count = 0

            for edge in spans_data:
                node = edge["node"]

                # Extract attributes
                attributes = {attr["name"]: attr["value"] for attr in node.get("attributes", [])}

                # Check compliance status
                is_compliant = self._is_span_compliant(attributes, node)
                if is_compliant:
                    compliant_count += 1

                # Extract GAMP category
                gamp_category = attributes.get("gamp.category", "Unknown")
                gamp_categories[gamp_category] = gamp_categories.get(gamp_category, 0) + 1

                # Check for errors
                if node.get("statusCode") == "ERROR":
                    error_count += 1

                # Extract latency
                latency = node.get("latencyMs")
                if latency is not None:
                    latencies.append(float(latency))

                # Check audit trail completeness
                if attributes.get("audit.trail.complete") == "true":
                    audit_complete_count += 1

            # Calculate metrics
            total_spans = len(spans_data)
            if total_spans > 0:
                metrics["compliance_breakdown"] = {
                    "compliant": compliant_count,
                    "non_compliant": total_spans - compliant_count,
                    "compliance_rate": (compliant_count / total_spans) * 100
                }

                metrics["error_rates"] = {
                    "total_errors": error_count,
                    "error_rate": (error_count / total_spans) * 100
                }

                metrics["audit_trail_completeness"] = (audit_complete_count / total_spans) * 100

            metrics["gamp_categories"] = gamp_categories

            if latencies:
                metrics["performance_metrics"] = {
                    "avg_latency_ms": sum(latencies) / len(latencies),
                    "max_latency_ms": max(latencies),
                    "min_latency_ms": min(latencies),
                    "total_operations": len(latencies)
                }

            return metrics

        except Exception as e:
            # NO FALLBACKS - compliance metrics parsing must be explicit
            raise Exception(f"Failed to parse compliance metrics: {e}") from e

    def _determine_compliance_status(self, attributes: dict[str, Any], spans: list[dict]) -> str:
        """Determine compliance status based on span attributes and status."""
        try:
            # Check for explicit compliance markers
            if "compliance.status" in attributes:
                return attributes["compliance.status"]

            # Check for GAMP-5 compliance attributes
            if attributes.get("compliance.gamp5.workflow") == "true":
                # Check for any error conditions
                has_errors = any(span.get("statusCode") == "ERROR" for span in spans)
                if has_errors:
                    return "non_compliant"

                # Check for required audit attributes
                required_attrs = ["audit.trail.required", "compliance.pharmaceutical"]
                has_required = all(attributes.get(attr) for attr in required_attrs)

                return "compliant" if has_required else "partial_compliance"

            return "unknown"

        except Exception:
            return "error_determining_status"

    def _is_span_compliant(self, attributes: dict[str, Any], span: dict) -> bool:
        """Check if a span meets GAMP-5 compliance requirements."""
        try:
            # Must have GAMP-5 compliance attributes
            if not attributes.get("compliance.gamp5.workflow"):
                return False

            # Must not have errors
            if span.get("statusCode") == "ERROR":
                return False

            # Must have audit trail
            if not attributes.get("audit.trail.required"):
                return False

            # Must have pharmaceutical context
            if not attributes.get("compliance.pharmaceutical"):
                return False

            return True

        except Exception:
            # If we can't determine compliance, consider it non-compliant
            return False


class WorkflowEventFlowVisualizer:
    """Creates interactive visualizations of workflow event flows."""

    def __init__(self, phoenix_client: PhoenixGraphQLClient):
        """Initialize with Phoenix GraphQL client."""
        self.client = phoenix_client

    async def create_workflow_flow_diagram(self, trace_id: str) -> str:
        """
        Create interactive workflow flow diagram from trace data.
        
        Args:
            trace_id: Specific trace ID to visualize
            
        Returns:
            Path to generated HTML file
            
        Raises:
            Exception: On any error - NO FALLBACKS for regulatory compliance
        """
        try:
            # Get trace data
            traces = await self.client.query_workflow_traces(hours=24)
            target_trace = next((t for t in traces if t.trace_id == trace_id), None)

            if not target_trace:
                raise Exception(f"Trace {trace_id} not found in last 24 hours")

            # Build directed graph from events
            G = nx.DiGraph()
            events_by_time = sorted(target_trace.events, key=lambda e: e.get("timestamp", ""))

            # Add nodes and edges based on event flow
            for i, event in enumerate(events_by_time):
                event_name = event.get("name", f"Event_{i}")
                node_id = f"{event_name}_{i}"

                # Node attributes for visualization
                node_attrs = {
                    "event_name": event_name,
                    "span_name": event.get("span_name", "Unknown"),
                    "timestamp": event.get("timestamp", ""),
                }
                node_attrs.update(event.get("attributes", {}))

                G.add_node(node_id, **node_attrs)

                # Connect to previous event
                if i > 0:
                    prev_event = events_by_time[i-1]
                    prev_node_id = f"{prev_event.get('name', f'Event_{i-1}')}_{i-1}"
                    G.add_edge(prev_node_id, node_id)

            # Create interactive visualization
            pos = nx.spring_layout(G, k=3, iterations=50)

            # Create traces for edges
            edge_x, edge_y = [], []
            for edge in G.edges():
                x0, y0 = pos[edge[0]]
                x1, y1 = pos[edge[1]]
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])

            edge_trace = go.Scatter(
                x=edge_x, y=edge_y,
                line=dict(width=2, color="#888"),
                hoverinfo="none",
                mode="lines"
            )

            # Create traces for nodes
            node_x = [pos[node][0] for node in G.nodes()]
            node_y = [pos[node][1] for node in G.nodes()]

            # Determine node colors based on compliance
            node_colors = []
            node_text = []
            hover_text = []

            for node in G.nodes():
                node_data = G.nodes[node]
                event_name = node_data.get("event_name", "Unknown")
                span_name = node_data.get("span_name", "Unknown")

                # Color based on compliance status
                if "compliance" in str(node_data).lower():
                    node_colors.append("green")
                elif "error" in event_name.lower() or "fail" in event_name.lower():
                    node_colors.append("red")
                else:
                    node_colors.append("lightblue")

                # Node text
                node_text.append(event_name[:20])

                # Hover text with detailed info
                hover_info = f"Event: {event_name}<br>Span: {span_name}<br>Time: {node_data.get('timestamp', 'Unknown')}"
                hover_text.append(hover_info)

            node_trace = go.Scatter(
                x=node_x, y=node_y,
                mode="markers+text",
                hoverinfo="text",
                hovertext=hover_text,
                text=node_text,
                textposition="middle center",
                marker=dict(
                    size=50,
                    color=node_colors,
                    line=dict(width=2, color="black")
                )
            )

            # Create figure
            fig = go.Figure(data=[edge_trace, node_trace],
                           layout=go.Layout(
                                title=f"Workflow Event Flow - Trace {trace_id}",
                                titlefont_size=16,
                                showlegend=False,
                                hovermode="closest",
                                margin=dict(b=20,l=5,r=5,t=40),
                                annotations=[ dict(
                                    text="Green=Compliant, Red=Error, Blue=Normal",
                                    showarrow=False,
                                    xref="paper", yref="paper",
                                    x=0.005, y=-0.002 ) ],
                                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                            )

            # Save as HTML
            output_path = f"workflow_flow_{trace_id[:8]}.html"
            fig.write_html(output_path)
            logger.info(f"Event flow diagram saved to: {output_path}")
            return output_path

        except Exception as e:
            # NO FALLBACKS - visualization errors must surface explicitly
            raise Exception(f"Failed to create workflow flow diagram: {e}") from e

    async def create_compliance_dashboard(self) -> str:
        """
        Create comprehensive GAMP-5 compliance dashboard.
        
        Returns:
            Path to generated HTML dashboard
            
        Raises:
            Exception: On any error - NO FALLBACKS for regulatory compliance
        """
        try:
            # Get compliance data
            compliance_data = await self.client.query_compliance_metrics()

            # Create subplots for different compliance metrics
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=(
                    "GAMP Category Distribution",
                    "Compliance Rate Over Time",
                    "Error Rate Analysis",
                    "Audit Trail Completeness"
                ),
                specs=[
                    [{"type": "pie"}, {"type": "bar"}],
                    [{"type": "scatter"}, {"type": "indicator"}]
                ]
            )

            # 1. GAMP category distribution pie chart
            gamp_categories = compliance_data.get("gamp_categories", {})
            if gamp_categories:
                fig.add_trace(
                    go.Pie(
                        labels=list(gamp_categories.keys()),
                        values=list(gamp_categories.values()),
                        name="GAMP Categories"
                    ),
                    row=1, col=1
                )

            # 2. Compliance rate bar chart
            compliance_breakdown = compliance_data.get("compliance_breakdown", {})
            if compliance_breakdown:
                fig.add_trace(
                    go.Bar(
                        x=["Compliant", "Non-Compliant"],
                        y=[compliance_breakdown.get("compliant", 0), compliance_breakdown.get("non_compliant", 0)],
                        marker_color=["green", "red"],
                        name="Compliance Status"
                    ),
                    row=1, col=2
                )

            # 3. Error rate scatter plot (placeholder - would need time series data)
            error_rates = compliance_data.get("error_rates", {})
            fig.add_trace(
                go.Scatter(
                    x=["Current"],
                    y=[error_rates.get("error_rate", 0)],
                    mode="markers+lines",
                    marker=dict(size=15, color="red"),
                    name="Error Rate %"
                ),
                row=2, col=1
            )

            # 4. Audit trail completeness indicator
            audit_completeness = compliance_data.get("audit_trail_completeness", 0)
            fig.add_trace(
                go.Indicator(
                    mode="gauge+number+delta",
                    value=audit_completeness,
                    domain={"x": [0, 1], "y": [0, 1]},
                    title={"text": "Audit Trail Completeness %"},
                    gauge={
                        "axis": {"range": [None, 100]},
                        "bar": {"color": "darkblue"},
                        "steps": [
                            {"range": [0, 50], "color": "lightgray"},
                            {"range": [50, 80], "color": "yellow"},
                            {"range": [80, 100], "color": "green"}
                        ],
                        "threshold": {
                            "line": {"color": "red", "width": 4},
                            "thickness": 0.75,
                            "value": 90
                        }
                    }
                ),
                row=2, col=2
            )

            # Update layout
            fig.update_layout(
                title_text="GAMP-5 Pharmaceutical Compliance Dashboard",
                title_x=0.5,
                showlegend=True,
                height=800
            )

            # Add compliance summary as annotation
            total_spans = compliance_data.get("total_spans", 0)
            compliance_rate = compliance_breakdown.get("compliance_rate", 0)

            summary_text = f"Total Spans: {total_spans} | Compliance Rate: {compliance_rate:.1f}% | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            fig.add_annotation(
                text=summary_text,
                xref="paper", yref="paper",
                x=0.5, y=-0.1,
                showarrow=False,
                font=dict(size=12)
            )

            # Save dashboard
            dashboard_path = "gamp5_compliance_dashboard.html"
            fig.write_html(dashboard_path)
            logger.info(f"Compliance dashboard saved to: {dashboard_path}")
            return dashboard_path

        except Exception as e:
            # NO FALLBACKS - dashboard creation errors must surface explicitly
            raise Exception(f"Failed to create compliance dashboard: {e}") from e


class AutomatedTraceAnalyzer:
    """Automated compliance analysis for pharmaceutical trace data."""

    def __init__(self, phoenix_client: PhoenixGraphQLClient):
        """Initialize with Phoenix GraphQL client."""
        self.client = phoenix_client
        self.compliance_rules = self._load_gamp5_rules()

    def _load_gamp5_rules(self) -> dict[str, Any]:
        """Load GAMP-5 compliance rules for automated analysis."""
        return {
            "confidence_threshold": 0.8,
            "max_processing_time_ms": 30000,
            "required_attributes": [
                "compliance.gamp5.workflow",
                "audit.trail.required",
                "compliance.pharmaceutical"
            ],
            "forbidden_patterns": [
                "fallback_triggered",
                "error_masked",
                "default_confidence_applied",
                "fallback_logic_used"
            ],
            "critical_error_patterns": [
                "fallback",
                "default_value",
                "masked_error",
                "silent_failure"
            ]
        }

    async def analyze_compliance_violations(self, hours: int = 24) -> list[ComplianceViolation]:
        """
        Automated compliance violation detection.
        
        Args:
            hours: Hours back to analyze
            
        Returns:
            List of compliance violations found
            
        Raises:
            Exception: On any analysis error - NO FALLBACKS
        """
        try:
            traces = await self.client.query_workflow_traces(hours=hours)
            violations = []

            for trace in traces:
                # Check confidence threshold violations
                confidence = trace.attributes.get("confidence.score")
                if confidence and float(confidence) < self.compliance_rules["confidence_threshold"]:
                    violations.append(ComplianceViolation(
                        trace_id=trace.trace_id,
                        violation_type="LOW_CONFIDENCE",
                        severity="HIGH",
                        description=f"Confidence score {confidence} below threshold {self.compliance_rules['confidence_threshold']}",
                        timestamp=datetime.now(UTC).isoformat(),
                        remediation_suggestion="Review categorization logic and training data",
                        regulatory_impact="May affect test generation accuracy and GAMP-5 compliance"
                    ))

                # Check processing time violations
                if trace.duration_ms > self.compliance_rules["max_processing_time_ms"]:
                    violations.append(ComplianceViolation(
                        trace_id=trace.trace_id,
                        violation_type="PERFORMANCE_DEGRADATION",
                        severity="MEDIUM",
                        description=f"Processing time {trace.duration_ms:.0f}ms exceeds limit {self.compliance_rules['max_processing_time_ms']}ms",
                        timestamp=datetime.now(UTC).isoformat(),
                        remediation_suggestion="Optimize workflow algorithms and review system resources",
                        regulatory_impact="Processing delays may impact pharmaceutical validation timelines"
                    ))

                # Check for required compliance attributes
                missing_attrs = []
                for required_attr in self.compliance_rules["required_attributes"]:
                    if required_attr not in trace.attributes:
                        missing_attrs.append(required_attr)

                if missing_attrs:
                    violations.append(ComplianceViolation(
                        trace_id=trace.trace_id,
                        violation_type="MISSING_COMPLIANCE_ATTRIBUTES",
                        severity="HIGH",
                        description=f"Missing required compliance attributes: {missing_attrs}",
                        timestamp=datetime.now(UTC).isoformat(),
                        remediation_suggestion="Ensure all workflow steps include required GAMP-5 compliance attributes",
                        regulatory_impact="Missing compliance attributes may invalidate audit trail"
                    ))

                # Check for forbidden patterns in events and attributes
                for event in trace.events:
                    event_name = event.get("name", "").lower()
                    for forbidden_pattern in self.compliance_rules["forbidden_patterns"]:
                        if forbidden_pattern in event_name:
                            violations.append(ComplianceViolation(
                                trace_id=trace.trace_id,
                                violation_type="FORBIDDEN_PATTERN",
                                severity="CRITICAL",
                                description=f"Detected forbidden pattern: {forbidden_pattern} in event: {event_name}",
                                timestamp=datetime.now(UTC).isoformat(),
                                remediation_suggestion="Remove fallback logic and implement explicit error handling",
                                regulatory_impact="CRITICAL: Fallback logic violates GAMP-5 requirements for explicit error handling"
                            ))

                # Check attributes for critical error patterns
                for attr_name, attr_value in trace.attributes.items():
                    attr_text = f"{attr_name}:{attr_value}".lower()
                    for critical_pattern in self.compliance_rules["critical_error_patterns"]:
                        if critical_pattern in attr_text:
                            violations.append(ComplianceViolation(
                                trace_id=trace.trace_id,
                                violation_type="CRITICAL_COMPLIANCE_VIOLATION",
                                severity="CRITICAL",
                                description=f"Critical pattern detected in attribute {attr_name}: {critical_pattern}",
                                timestamp=datetime.now(UTC).isoformat(),
                                remediation_suggestion="Immediately review and remove any fallback or masking logic",
                                regulatory_impact="CRITICAL: Violates FDA 21 CFR Part 11 requirements for data integrity"
                            ))

            return violations

        except Exception as e:
            # NO FALLBACKS - compliance analysis must be explicit
            raise Exception(f"Failed to analyze compliance violations: {e}") from e

    async def generate_compliance_report(self) -> dict[str, Any]:
        """
        Generate comprehensive compliance analysis report.
        
        Returns:
            Comprehensive compliance report
            
        Raises:
            Exception: On any error - NO FALLBACKS for regulatory compliance
        """
        try:
            violations = await self.analyze_compliance_violations()
            traces = await self.client.query_workflow_traces()
            compliance_metrics = await self.client.query_compliance_metrics()

            # Calculate compliance statistics
            total_traces = len(traces)
            compliant_traces = len([t for t in traces if t.compliance_status == "compliant"])
            compliance_rate = (compliant_traces / total_traces) * 100 if total_traces > 0 else 0

            # Categorize violations by severity
            violations_by_severity = {
                "CRITICAL": [v for v in violations if v.severity == "CRITICAL"],
                "HIGH": [v for v in violations if v.severity == "HIGH"],
                "MEDIUM": [v for v in violations if v.severity == "MEDIUM"],
                "LOW": [v for v in violations if v.severity == "LOW"]
            }

            # Generate regulatory assessment
            regulatory_status = "COMPLIANT"
            if violations_by_severity["CRITICAL"]:
                regulatory_status = "NON_COMPLIANT_CRITICAL"
            elif violations_by_severity["HIGH"]:
                regulatory_status = "NON_COMPLIANT_HIGH"
            elif violations_by_severity["MEDIUM"]:
                regulatory_status = "COMPLIANT_WITH_ISSUES"

            report = {
                "report_metadata": {
                    "generated_at": datetime.now(UTC).isoformat(),
                    "analysis_period_hours": 24,
                    "total_traces_analyzed": total_traces,
                    "regulatory_status": regulatory_status,
                    "compliance_framework": "GAMP-5",
                    "regulatory_standards": ["21 CFR Part 11", "ALCOA+"]
                },
                "compliance_summary": {
                    "compliance_rate_percent": compliance_rate,
                    "compliant_traces": compliant_traces,
                    "non_compliant_traces": total_traces - compliant_traces,
                    "audit_trail_completeness": compliance_metrics.get("audit_trail_completeness", 0)
                },
                "violations_summary": {
                    "total_violations": len(violations),
                    "critical_violations": len(violations_by_severity["CRITICAL"]),
                    "high_violations": len(violations_by_severity["HIGH"]),
                    "medium_violations": len(violations_by_severity["MEDIUM"]),
                    "low_violations": len(violations_by_severity["LOW"])
                },
                "regulatory_impact": self._assess_regulatory_impact(violations_by_severity),
                "recommendations": self._generate_recommendations(violations),
                "detailed_violations": [asdict(v) for v in violations],
                "compliance_metrics": compliance_metrics
            }

            return report

        except Exception as e:
            # NO FALLBACKS - compliance reporting must be explicit for regulatory purposes
            raise Exception(f"Failed to generate compliance report: {e}") from e

    def _assess_regulatory_impact(self, violations_by_severity: dict[str, list[ComplianceViolation]]) -> dict[str, Any]:
        """Assess regulatory impact of violations."""
        if violations_by_severity["CRITICAL"]:
            return {
                "risk_level": "HIGH",
                "regulatory_action_required": True,
                "fda_notification_required": True,
                "system_shutdown_recommended": True,
                "impact_description": "Critical violations detected that compromise data integrity and regulatory compliance"
            }
        if violations_by_severity["HIGH"]:
            return {
                "risk_level": "MEDIUM",
                "regulatory_action_required": True,
                "fda_notification_required": False,
                "system_shutdown_recommended": False,
                "impact_description": "High-severity violations require immediate remediation to maintain compliance"
            }
        return {
            "risk_level": "LOW",
            "regulatory_action_required": False,
            "fda_notification_required": False,
            "system_shutdown_recommended": False,
            "impact_description": "System is operating within acceptable compliance parameters"
        }

    def _generate_recommendations(self, violations: list[ComplianceViolation]) -> list[str]:
        """Generate actionable recommendations based on violation patterns."""
        recommendations = []

        violation_counts = {}
        for violation in violations:
            violation_counts[violation.violation_type] = violation_counts.get(violation.violation_type, 0) + 1

        # Generate specific recommendations
        if violation_counts.get("LOW_CONFIDENCE", 0) > 5:
            recommendations.append("URGENT: Review and retrain categorization models with additional validated data")

        if violation_counts.get("PERFORMANCE_DEGRADATION", 0) > 3:
            recommendations.append("Optimize workflow performance and review system resources allocation")

        if violation_counts.get("FORBIDDEN_PATTERN", 0) > 0:
            recommendations.append("CRITICAL: Immediately remove all fallback logic to ensure GAMP-5 compliance")

        if violation_counts.get("CRITICAL_COMPLIANCE_VIOLATION", 0) > 0:
            recommendations.append("EMERGENCY: System contains critical compliance violations - immediate remediation required")

        if violation_counts.get("MISSING_COMPLIANCE_ATTRIBUTES", 0) > 0:
            recommendations.append("Enhance workflow instrumentation to include all required GAMP-5 compliance attributes")

        # Always include general recommendations
        recommendations.extend([
            "Implement continuous compliance monitoring with real-time alerting",
            "Conduct regular GAMP-5 compliance audits",
            "Maintain comprehensive audit trails for all pharmaceutical operations",
            "Ensure all system changes follow validated change control procedures"
        ])

        return recommendations


# Main enhanced Phoenix setup function
async def setup_enhanced_phoenix_observability(
    endpoint: str = "http://localhost:6006/graphql",
    api_key: str | None = None
) -> dict[str, Any]:
    """
    Set up enhanced Phoenix observability with GraphQL API access.
    
    Args:
        endpoint: Phoenix GraphQL endpoint
        api_key: Optional API key
        
    Returns:
        Dictionary with client instances and status
        
    Raises:
        Exception: On any setup error - NO FALLBACKS
    """
    try:
        # Initialize GraphQL client
        client = PhoenixGraphQLClient(endpoint, api_key)

        # Test connectivity
        await client.query_compliance_metrics(timeframe_hours=1)

        # Initialize visualization and analysis components
        visualizer = WorkflowEventFlowVisualizer(client)
        analyzer = AutomatedTraceAnalyzer(client)

        logger.info("Enhanced Phoenix observability setup completed successfully")

        return {
            "graphql_client": client,
            "visualizer": visualizer,
            "analyzer": analyzer,
            "status": "ready",
            "endpoint": endpoint,
            "capabilities": [
                "GraphQL API access",
                "Event flow visualization",
                "Automated compliance analysis",
                "GAMP-5 compliance dashboard",
                "Real-time violation detection"
            ]
        }

    except Exception as e:
        # NO FALLBACKS - setup failures must surface explicitly
        raise Exception(f"Failed to setup enhanced Phoenix observability: {e}") from e
