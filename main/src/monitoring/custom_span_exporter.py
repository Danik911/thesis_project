"""
Custom OpenTelemetry span exporter that captures ALL spans including ChromaDB operations.

This module implements a custom span processor and exporter that saves all spans
to local JSONL files, ensuring no spans are lost due to Phoenix's selective persistence.
"""

import json
import logging
from datetime import datetime
from pathlib import Path

from opentelemetry.sdk.trace import ReadableSpan, SpanProcessor

logger = logging.getLogger(__name__)


class LocalFileSpanExporter(SpanProcessor):
    """
    Custom span processor that exports ALL spans to local JSONL files.
    
    This ensures we capture ChromaDB and other instrumentation spans that
    Phoenix doesn't persist to its database.
    """

    def __init__(self, output_dir: Path | str | None = None):
        """
        Initialize the local file span exporter.
        
        Args:
            output_dir: Directory to save trace files. Defaults to logs/traces/
        """
        self.output_dir = Path(output_dir) if output_dir else Path("logs/traces")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Create a new file for this session
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.trace_file = self.output_dir / f"all_spans_{timestamp}.jsonl"
        self.chromadb_file = self.output_dir / f"chromadb_spans_{timestamp}.jsonl"

        logger.info(f"LocalFileSpanExporter initialized - saving to: {self.trace_file}")

    def on_start(self, span: ReadableSpan, parent_context=None) -> None:
        """Called when a span is started. We don't need to do anything here."""

    def on_end(self, span: ReadableSpan) -> None:
        """
        Called when a span ends. Export it to our local file.
        
        Args:
            span: The span that just ended
        """
        try:
            # Convert span to a serializable format
            span_data = self._span_to_dict(span)

            # Write to main trace file
            with open(self.trace_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(span_data, default=str) + "\n")

            # Also write ChromaDB spans to separate file for easier analysis
            span_name = span.name.lower()
            if any(keyword in span_name for keyword in ["chromadb", "vector", "collection", "embed"]):
                with open(self.chromadb_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(span_data, default=str) + "\n")
                logger.debug(f"Captured ChromaDB span: {span.name}")

        except Exception as e:
            logger.error(f"Failed to export span {span.name}: {e}")

    def shutdown(self) -> None:
        """Shutdown the exporter."""
        logger.info(f"LocalFileSpanExporter shutdown - traces saved to: {self.trace_file}")

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        """Force flush any pending spans. We write immediately so nothing to flush."""
        return True

    def _span_to_dict(self, span: ReadableSpan) -> dict:
        """
        Convert a ReadableSpan to a dictionary format similar to Phoenix exports.
        
        Args:
            span: The span to convert
            
        Returns:
            Dictionary representation of the span
        """
        # Extract attributes
        attributes = {}
        if span.attributes:
            for key, value in span.attributes.items():
                # Convert attribute names to strings
                attr_key = str(key)
                # Handle different value types
                if isinstance(value, (str, int, float, bool)):
                    attributes[attr_key] = value
                else:
                    attributes[attr_key] = str(value)

        # Extract events
        events = []
        if span.events:
            for event in span.events:
                event_data = {
                    "name": event.name,
                    "timestamp": event.timestamp,
                    "attributes": {}
                }
                if event.attributes:
                    for key, value in event.attributes.items():
                        event_data["attributes"][str(key)] = value
                events.append(event_data)

        # Build span dictionary
        span_dict = {
            "span_id": format(span.context.span_id, "016x"),
            "trace_id": format(span.context.trace_id, "032x"),
            "parent_id": format(span.parent.span_id, "016x") if span.parent else None,
            "name": span.name,
            "kind": span.kind.name,
            "start_time": span.start_time,
            "end_time": span.end_time,
            "duration_ns": span.end_time - span.start_time if span.end_time else None,
            "status": {
                "status_code": span.status.status_code.name,
                "description": span.status.description
            },
            "attributes": attributes,
            "events": events,
            "links": [],  # Links not commonly used in our system
            "resource": {},  # Resource attributes if needed

            # Add pharmaceutical compliance markers
            "pharmaceutical_system": True,
            "exporter": "LocalFileSpanExporter",
            "capture_time": datetime.now().isoformat()
        }

        # Add specific fields for ChromaDB operations
        if "chromadb" in span.name.lower():
            span_dict["span_type"] = "vector_database"
            span_dict["database_type"] = "chromadb"

            # Extract ChromaDB specific attributes
            if "vector_db.operation" in attributes:
                span_dict["operation"] = attributes["vector_db.operation"]
            if "chromadb.query.result_count" in attributes:
                span_dict["result_count"] = attributes["chromadb.query.result_count"]
            if "chromadb.query.avg_distance" in attributes:
                span_dict["avg_distance"] = attributes["chromadb.query.avg_distance"]

        # Add LLM fields if this is an LLM span
        elif any(llm_key in span.name.lower() for llm_key in ["llm", "chat", "completion", "openai"]):
            span_dict["span_type"] = "llm"

            # Extract LLM specific attributes
            if "llm.token_count.prompt" in attributes:
                span_dict["prompt_tokens"] = attributes["llm.token_count.prompt"]
            if "llm.token_count.completion" in attributes:
                span_dict["completion_tokens"] = attributes["llm.token_count.completion"]
            if "llm.model_name" in attributes:
                span_dict["model"] = attributes["llm.model_name"]

        # Add workflow fields
        elif "workflow" in span.name.lower():
            span_dict["span_type"] = "workflow"
            if "workflow.type" in attributes:
                span_dict["workflow_type"] = attributes["workflow.type"]

        # Add tool fields
        elif "tool" in span.name.lower():
            span_dict["span_type"] = "tool"
            if "tool.name" in attributes:
                span_dict["tool_name"] = attributes["tool.name"]
            if "tool.category" in attributes:
                span_dict["tool_category"] = attributes["tool.category"]

        return span_dict


def add_local_span_exporter(tracer_provider, output_dir: Path | str | None = None):
    """
    Add the local file span exporter to an existing tracer provider.
    
    This should be called after Phoenix setup to ensure we capture all spans.
    
    Args:
        tracer_provider: The OpenTelemetry tracer provider
        output_dir: Optional custom output directory
    """
    try:
        exporter = LocalFileSpanExporter(output_dir)
        tracer_provider.add_span_processor(exporter)
        logger.info("✅ Added LocalFileSpanExporter to capture ALL spans including ChromaDB")
        return exporter
    except Exception as e:
        logger.error(f"Failed to add local span exporter: {e}")
        return None
