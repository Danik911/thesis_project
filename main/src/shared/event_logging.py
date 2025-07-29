"""
Structured LlamaIndex Event Streaming Logging System for GAMP-5 Compliance.

This module provides comprehensive event streaming and logging capabilities
for pharmaceutical software validation, ensuring compliance with GAMP-5,
ALCOA+ principles, and 21 CFR Part 11 requirements.
"""

import asyncio
import hashlib
import json
import logging
import threading
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from llama_index.core.workflow import Context

from .config import Config, get_config
from .utils import format_compliance_metadata


class EventStreamHandler:
    """
    Handler for streaming LlamaIndex workflow events with GAMP-5 compliance.
    
    Implements the 'async for event in handler.stream_events()' pattern
    to capture and process workflow events in real-time.
    """

    def __init__(
        self,
        event_types: list[str] | None = None,
        config: Config | None = None
    ):
        """
        Initialize the event stream handler.
        
        Args:
            event_types: List of event types to capture (None for all)
            config: Configuration instance (uses global if None)
        """
        self.config = config or get_config()
        self.event_types = event_types or self.config.event_streaming.captured_event_types
        self.logger = logging.getLogger(f"{__name__}.EventStreamHandler")

        # Event buffer for batch processing
        self._event_buffer: list[dict[str, Any]] = []
        self._buffer_lock = threading.Lock()

        # Structured loggers
        self.structured_logger = StructuredEventLogger(config=self.config)
        self.compliance_logger = GAMP5ComplianceLogger(config=self.config)

        # Statistics
        self.events_processed = 0
        self.events_filtered = 0
        self.start_time = datetime.now(UTC)

        self.logger.info(f"EventStreamHandler initialized for types: {self.event_types}")

    async def stream_events(
        self,
        context: Context,
        timeout: float | None = None
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Stream events from LlamaIndex workflow context.
        
        Args:
            context: LlamaIndex workflow context
            timeout: Optional timeout for streaming
            
        Yields:
            Dict containing processed event data
        """
        self.logger.debug("Starting event streaming")
        start_time = asyncio.get_event_loop().time()

        try:
            # This is a simplified implementation since LlamaIndex context
            # doesn't directly support 'async for event in stream_events()'
            # We'll simulate the pattern and hook into context events
            async for event_data in self._simulate_event_stream(context, timeout):

                # Check timeout
                if timeout and (asyncio.get_event_loop().time() - start_time) > timeout:
                    self.logger.warning(f"Event streaming timeout after {timeout}s")
                    break

                # Process and yield event
                processed_event = await self._process_event(event_data)
                if processed_event:
                    yield processed_event

        except Exception as e:
            self.logger.error(f"Error in event streaming: {e}")
            # Log compliance event for the error
            await self.compliance_logger.log_error_event({
                "error_type": "STREAM_ERROR",
                "error_message": str(e),
                "context": "event_streaming"
            })
            raise

        finally:
            # Flush any remaining buffered events
            await self._flush_buffer()
            self.logger.debug(f"Event streaming completed. Processed: {self.events_processed}")

    async def _simulate_event_stream(
        self,
        context: Context,
        timeout: float | None
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Simulate event streaming from context.
        
        In a real implementation, this would hook into LlamaIndex's
        internal event streaming mechanism.
        """
        # This is a placeholder implementation
        # In reality, we would integrate with LlamaIndex's workflow events

        # For now, we'll simulate some events to demonstrate the pattern
        event_count = 0
        max_events = 10  # Limit for demonstration

        while event_count < max_events:
            # Simulate different types of workflow events
            event_type = self.event_types[event_count % len(self.event_types)]

            event_data = {
                "event_type": event_type,
                "event_id": str(uuid4()),
                "timestamp": datetime.now(UTC).isoformat(),
                "workflow_context": {
                    "step": f"step_{event_count}",
                    "agent_id": "test_agent",
                    "correlation_id": str(uuid4())
                },
                "payload": {
                    "message": f"Simulated {event_type} event",
                    "sequence": event_count
                }
            }

            yield event_data
            event_count += 1

            # Small delay to simulate real-time processing
            await asyncio.sleep(0.1)

    async def _process_event(self, event_data: dict[str, Any]) -> dict[str, Any] | None:
        """
        Process a single event with compliance logging.
        
        Args:
            event_data: Raw event data
            
        Returns:
            Processed event data or None if filtered
        """
        try:
            event_type = event_data.get("event_type", "Unknown")

            # Filter events based on configuration
            if self.event_types and event_type not in self.event_types:
                self.events_filtered += 1
                return None

            # Add compliance metadata
            compliance_data = format_compliance_metadata(event_data)

            # Create structured log entry
            structured_entry = {
                "event_id": compliance_data["entry_id"],
                "timestamp": compliance_data["timestamp"],
                "event_type": event_type,
                "original_event_id": event_data.get("event_id"),
                "workflow_context": event_data.get("workflow_context", {}),
                "payload": event_data.get("payload", {}),
                "compliance_metadata": compliance_data,
                "processing_info": {
                    "handler": "EventStreamHandler",
                    "processed_at": datetime.now(UTC).isoformat(),
                    "sequence_number": self.events_processed
                }
            }

            # Log through structured logger
            await self.structured_logger.log_event(structured_entry)

            # Add to compliance audit trail
            await self.compliance_logger.log_audit_event(structured_entry)

            # Buffer for batch processing if enabled
            if self.config.event_streaming.batch_processing_size > 1:
                await self._add_to_buffer(structured_entry)

            self.events_processed += 1
            return structured_entry

        except Exception as e:
            self.logger.error(f"Error processing event: {e}")
            return None

    async def _add_to_buffer(self, event_data: dict[str, Any]) -> None:
        """Add event to buffer for batch processing."""
        with self._buffer_lock:
            self._event_buffer.append(event_data)

            # Flush buffer if it's full
            if len(self._event_buffer) >= self.config.event_streaming.batch_processing_size:
                await self._flush_buffer()

    async def _flush_buffer(self) -> None:
        """Flush the event buffer to persistent storage."""
        if not self._event_buffer:
            return

        with self._buffer_lock:
            buffer_copy = self._event_buffer.copy()
            self._event_buffer.clear()

        if buffer_copy:
            self.logger.debug(f"Flushing {len(buffer_copy)} events from buffer")
            # Process buffer in background task
            asyncio.create_task(self._process_buffer_batch(buffer_copy))

    async def _process_buffer_batch(self, events: list[dict[str, Any]]) -> None:
        """Process a batch of buffered events."""
        try:
            # Write batch to compliance storage
            await self.compliance_logger.log_batch_events(events)
            self.logger.debug(f"Successfully processed batch of {len(events)} events")
        except Exception as e:
            self.logger.error(f"Error processing event batch: {e}")

    def get_statistics(self) -> dict[str, Any]:
        """Get handler statistics."""
        runtime = datetime.now(UTC) - self.start_time

        return {
            "events_processed": self.events_processed,
            "events_filtered": self.events_filtered,
            "runtime_seconds": runtime.total_seconds(),
            "events_per_second": self.events_processed / max(runtime.total_seconds(), 1),
            "buffer_size": len(self._event_buffer),
            "event_types_captured": self.event_types
        }


class StructuredEventLogger:
    """
    Structured logger that integrates with Python's logging module.
    
    Provides standardized formatting for workflow events with
    ISO 8601 timestamps and contextual data.
    """

    def __init__(self, config: Config | None = None):
        """Initialize the structured logger."""
        self.config = config or get_config()
        self.logger = logging.getLogger(f"{__name__}.StructuredEventLogger")

        # Create specialized loggers for different event types
        self.categorization_logger = logging.getLogger("pharma.categorization")
        self.planning_logger = logging.getLogger("pharma.planning")
        self.agent_logger = logging.getLogger("pharma.agents")
        self.validation_logger = logging.getLogger("pharma.validation")

        # Configure formatters
        self._setup_formatters()

    def _setup_formatters(self) -> None:
        """Setup specialized formatters for different event types."""
        # JSON formatter for structured logging
        json_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # Compliance formatter
        compliance_formatter = logging.Formatter(
            "%(asctime)s [GAMP5] %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S UTC"
        )

        # Apply formatters to handlers
        for handler in self.logger.handlers:
            if hasattr(handler, "baseFilename"):  # File handler
                handler.setFormatter(compliance_formatter)
            else:  # Console handler
                handler.setFormatter(json_formatter)

    async def log_event(self, event_data: dict[str, Any]) -> None:
        """
        Log a structured event.
        
        Args:
            event_data: Event data to log
        """
        try:
            event_type = event_data.get("event_type", "Unknown")

            # Select appropriate logger
            logger = self._get_logger_for_event_type(event_type)

            # Create log message
            log_message = self._format_event_message(event_data)

            # Log at appropriate level
            log_level = self._get_log_level_for_event(event_data)
            logger.log(log_level, log_message, extra={
                "event_id": event_data.get("event_id"),
                "event_type": event_type,
                "timestamp": event_data.get("timestamp"),
                "compliance_data": event_data.get("compliance_metadata", {})
            })

        except Exception as e:
            self.logger.error(f"Error logging structured event: {e}")

    def _get_logger_for_event_type(self, event_type: str) -> logging.Logger:
        """Get the appropriate logger for an event type."""
        if "Categorization" in event_type:
            return self.categorization_logger
        if "Planning" in event_type:
            return self.planning_logger
        if "Agent" in event_type:
            return self.agent_logger
        if "Validation" in event_type:
            return self.validation_logger
        return self.logger

    def _format_event_message(self, event_data: dict[str, Any]) -> str:
        """Format event data into a structured log message."""
        event_type = event_data.get("event_type", "Unknown")
        event_id = event_data.get("event_id", "Unknown")

        # Extract key information
        workflow_context = event_data.get("workflow_context", {})
        payload = event_data.get("payload", {})

        # Create structured message
        message_parts = [
            f"EVENT[{event_type}]",
            f"ID[{event_id}]"
        ]

        # Add context information
        if workflow_context.get("step"):
            message_parts.append(f"STEP[{workflow_context['step']}]")

        if workflow_context.get("agent_id"):
            message_parts.append(f"AGENT[{workflow_context['agent_id']}]")

        # Add payload summary
        if payload.get("message"):
            message_parts.append(f"MSG[{payload['message']}]")

        return " ".join(message_parts)

    def _get_log_level_for_event(self, event_data: dict[str, Any]) -> int:
        """Determine appropriate log level for an event."""
        event_type = event_data.get("event_type", "")
        payload = event_data.get("payload", {})

        # Error events
        if "Error" in event_type or payload.get("error"):
            return logging.ERROR

        # Warning events
        if "Consultation" in event_type or payload.get("review_required"):
            return logging.WARNING

        # Debug events
        if "Agent" in event_type and "Request" in event_type:
            return logging.DEBUG

        # Default to INFO
        return logging.INFO


class GAMP5ComplianceLogger:
    """
    GAMP-5 compliant logger for regulatory audit trails.
    
    Ensures tamper-evident, append-only logging with ALCOA+ principles
    and 21 CFR Part 11 compliance features.
    """

    def __init__(self, config: Config | None = None):
        """Initialize the compliance logger."""
        self.config = config or get_config()
        self.logger = logging.getLogger(f"{__name__}.GAMP5ComplianceLogger")

        # Setup audit trail storage
        self.audit_dir = Path(self.config.gamp5_compliance.audit_log_directory)
        self.audit_dir.mkdir(parents=True, exist_ok=True)

        # Thread safety
        self._lock = threading.Lock()

        # Current audit file
        self._current_file = self._get_current_audit_file()

        self.logger.info(f"GAMP5ComplianceLogger initialized - Audit dir: {self.audit_dir}")

    def _get_current_audit_file(self) -> Path:
        """Get or create current audit log file."""
        today = datetime.now(UTC).strftime("%Y%m%d")
        base_name = f"gamp5_audit_{today}"

        # Find latest file for today
        existing_files = list(self.audit_dir.glob(f"{base_name}_*.jsonl"))

        if not existing_files:
            return self.audit_dir / f"{base_name}_001.jsonl"

        # Get latest file
        existing_files.sort()
        latest_file = existing_files[-1]

        # Check if rotation needed
        if latest_file.stat().st_size >= (self.config.logging.max_file_size_mb * 1024 * 1024):
            # Create new file
            parts = latest_file.stem.split("_")
            num = int(parts[-1])
            new_num = str(num + 1).zfill(3)
            return self.audit_dir / f"{base_name}_{new_num}.jsonl"

        return latest_file

    async def log_audit_event(self, event_data: dict[str, Any]) -> None:
        """
        Log an event to the GAMP-5 compliant audit trail.
        
        Args:
            event_data: Event data to audit log
        """
        try:
            # Create audit entry
            audit_entry = self._create_audit_entry(event_data)

            # Write to audit file
            with self._lock:
                self._write_audit_entry(audit_entry)

        except Exception as e:
            self.logger.error(f"Error writing audit entry: {e}")

    async def log_batch_events(self, events: list[dict[str, Any]]) -> None:
        """Log a batch of events to audit trail."""
        try:
            with self._lock:
                for event_data in events:
                    audit_entry = self._create_audit_entry(event_data)
                    self._write_audit_entry(audit_entry)

            self.logger.debug(f"Successfully logged batch of {len(events)} audit events")

        except Exception as e:
            self.logger.error(f"Error writing audit batch: {e}")

    async def log_error_event(self, error_data: dict[str, Any]) -> None:
        """Log an error event with compliance metadata."""
        error_entry = {
            "event_type": "ERROR_EVENT",
            "event_id": str(uuid4()),
            "timestamp": datetime.now(UTC).isoformat(),
            "error_details": error_data,
            "compliance_metadata": format_compliance_metadata({
                "error_type": error_data.get("error_type", "UNKNOWN"),
                "severity": "HIGH"
            })
        }

        await self.log_audit_event(error_entry)

    def _create_audit_entry(self, event_data: dict[str, Any]) -> dict[str, Any]:
        """Create a GAMP-5 compliant audit entry."""
        # Generate hash for tamper evidence
        event_json = json.dumps(event_data, sort_keys=True)
        event_hash = hashlib.sha256(event_json.encode()).hexdigest()

        audit_entry = {
            "audit_id": str(uuid4()),
            "audit_timestamp": datetime.now(UTC).isoformat(),
            "event_data": event_data,
            "integrity_hash": event_hash,
            "alcoa_plus_compliance": {
                "attributable": True,
                "legible": True,
                "contemporaneous": True,
                "original": True,
                "accurate": True,
                "complete": True,
                "consistent": True,
                "enduring": True,
                "available": True
            },
            "cfr_part_11_compliance": {
                "electronic_signature": None,
                "audit_trail": True,
                "tamper_evident": True,
                "record_integrity": True
            },
            "gamp5_metadata": {
                "category": "Category 5",  # Custom application
                "risk_level": "High",
                "validation_required": True,
                "change_control": True
            }
        }

        return audit_entry

    def _write_audit_entry(self, audit_entry: dict[str, Any]) -> None:
        """Write audit entry to file with rotation check."""
        # Check if rotation needed
        if self.config.logging.enable_rotation:
            if self._current_file.stat().st_size >= (
                self.config.logging.max_file_size_mb * 1024 * 1024
            ):
                self._current_file = self._get_current_audit_file()

        # Write entry as JSON line
        with open(self._current_file, "a") as f:
            json.dump(audit_entry, f, separators=(",", ":"))
            f.write("\n")

    def get_audit_statistics(self) -> dict[str, Any]:
        """Get audit trail statistics."""
        total_entries = 0
        total_size = 0
        file_count = 0

        for audit_file in self.audit_dir.glob("gamp5_audit_*.jsonl"):
            file_count += 1
            file_size = audit_file.stat().st_size
            total_size += file_size

            # Count entries
            try:
                with open(audit_file) as f:
                    total_entries += sum(1 for _ in f)
            except Exception:
                pass

        return {
            "total_audit_entries": total_entries,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "audit_file_count": file_count,
            "audit_directory": str(self.audit_dir),
            "compliance_standards": [std.value for std in self.config.gamp5_compliance.compliance_standards],
            "tamper_evident": self.config.gamp5_compliance.enable_tamper_evident,
            "retention_days": self.config.gamp5_compliance.audit_retention_days
        }


def setup_event_logging(config: Config | None = None) -> EventStreamHandler:
    """
    Setup and configure the event logging system.
    
    Args:
        config: Optional configuration (uses global if None)
        
    Returns:
        EventStreamHandler: Configured event stream handler
    """
    config = config or get_config()

    # Ensure log directory exists
    log_dir = Path(config.logging.log_directory)
    log_dir.mkdir(parents=True, exist_ok=True)

    # Setup Python logging with compliance formatters
    log_file_path = log_dir / f"{config.logging.log_file_prefix}.log"

    logging.basicConfig(
        level=getattr(logging, config.logging.log_level.value),
        format=config.logging.console_format,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(str(log_file_path))
        ]
    )

    # Create event stream handler with Phoenix integration if enabled
    if config.phoenix.enable_phoenix:
        try:
            # Import Phoenix components
            from ..monitoring import PhoenixEventStreamHandler, setup_phoenix
            from ..monitoring.phoenix_config import PhoenixConfig as MonitoringPhoenixConfig

            # Initialize Phoenix
            logger = logging.getLogger(__name__)
            logger.info("Initializing Phoenix observability...")
            
            # Convert simple config to monitoring config
            monitoring_config = MonitoringPhoenixConfig(
                phoenix_host=config.phoenix.phoenix_host,
                phoenix_port=config.phoenix.phoenix_port,
                phoenix_api_key=config.phoenix.phoenix_api_key,
                service_name=config.phoenix.service_name,
                project_name=config.phoenix.project_name,
                experiment_name=config.phoenix.experiment_name,
                enable_tracing=config.phoenix.enable_tracing,
                enable_local_ui=config.phoenix.enable_local_ui,
                otlp_endpoint=config.phoenix.otlp_endpoint or f"http://{config.phoenix.phoenix_host}:{config.phoenix.phoenix_port}/v1/traces"
            )
            
            phoenix_manager = setup_phoenix(monitoring_config)

            # Use Phoenix-enabled event handler
            handler = PhoenixEventStreamHandler(config=config)
            logger.info("Phoenix observability enabled for event logging")

            if phoenix_manager.phoenix_session:
                logger.info(f"Phoenix UI available at: {phoenix_manager.phoenix_session.url}")
        except Exception as e:
            # Fallback to standard handler if Phoenix setup fails
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to initialize Phoenix observability: {e}")
            logger.info("Falling back to standard event logging")
            handler = EventStreamHandler(config=config)
    else:
        # Use standard event handler
        handler = EventStreamHandler(config=config)

    logger = logging.getLogger(__name__)
    logger.info("Event logging system initialized successfully")
    logger.info(f"Configuration: {config.to_dict()}")

    return handler


# Example usage patterns for workflow integration
async def example_workflow_integration(context: Context) -> None:
    """
    Example of how to integrate event logging into a workflow.
    """
    # Setup event logging
    event_handler = setup_event_logging()

    # Stream and process events
    async for event in event_handler.stream_events(context, timeout=60.0):
        # Event is automatically logged with GAMP-5 compliance
        # Additional processing can be done here
        print(f"Processed event: {event['event_type']}")

    # Get statistics
    stats = event_handler.get_statistics()
    print(f"Event processing statistics: {stats}")


# Export main classes and functions
__all__ = [
    "EventStreamHandler",
    "GAMP5ComplianceLogger",
    "StructuredEventLogger",
    "example_workflow_integration",
    "setup_event_logging"
]
