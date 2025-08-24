"""
Monitoring system for workflow performance and observability.

This module provides comprehensive monitoring capabilities for the pharmaceutical
test generation workflow, including performance metrics, step timing, and 
Phoenix AI integration for regulatory compliance traceability.
"""

import logging
import time
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from .models import MonitoringConfiguration


class MonitoringEventType(str, Enum):
    """Types of monitoring events for workflow observability."""
    WORKFLOW_START = "workflow_start"
    WORKFLOW_END = "workflow_end"
    STEP_START = "step_start"
    STEP_END = "step_end"
    AGENT_START = "agent_start"
    AGENT_END = "agent_end"
    ERROR_OCCURRED = "error_occurred"
    PERFORMANCE_METRIC = "performance_metric"


class PerformanceMetrics(BaseModel):
    """Performance metrics for workflow monitoring."""
    total_execution_time: float = Field(default=0.0, description="Total execution time in seconds")
    step_times: dict[str, float] = Field(default_factory=dict, description="Individual step execution times")
    memory_usage: float | None = Field(default=None, description="Memory usage in MB")
    cpu_usage: float | None = Field(default=None, description="CPU usage percentage")
    agent_performance: dict[str, dict[str, float]] = Field(default_factory=dict, description="Agent performance metrics")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class MonitoringEvent(BaseModel):
    """Individual monitoring event with metadata."""
    event_type: MonitoringEventType = Field(..., description="Type of monitoring event")
    event_data: dict[str, Any] = Field(default_factory=dict, description="Event-specific data")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    step_name: str | None = Field(default=None, description="Associated workflow step")
    agent_type: str | None = Field(default=None, description="Associated agent type")
    duration: float | None = Field(default=None, description="Duration in seconds")
    success: bool = Field(default=True, description="Whether operation was successful")


class WorkflowMonitor:
    """
    Comprehensive monitoring system for workflow operations.
    
    Provides performance monitoring, step timing, and integration with
    Phoenix AI for pharmaceutical compliance observability.
    """

    def __init__(self, config: MonitoringConfiguration | None = None):
        self.config = config or MonitoringConfiguration()
        self.logger = logging.getLogger(self.__class__.__name__)

        # Monitoring state
        self.events: list[MonitoringEvent] = []
        self.active_steps: dict[str, float] = {}
        self.performance_metrics = PerformanceMetrics()
        self.workflow_start_time: float | None = None

        if self.config.enable_phoenix_tracing:
            self._initialize_phoenix_integration()

    def _initialize_phoenix_integration(self) -> None:
        """Initialize Phoenix AI integration for LLM call tracing."""
        try:
            # Phoenix integration would be initialized here
            # For now, we'll just log that it's enabled
            self.logger.info("Phoenix AI tracing enabled for workflow monitoring")
        except Exception as e:
            self.logger.warning(f"Phoenix AI integration failed: {e}")

    def start_workflow_monitoring(self, workflow_name: str) -> None:
        """Start monitoring for a workflow execution."""
        self.workflow_start_time = time.time()

        event = MonitoringEvent(
            event_type=MonitoringEventType.WORKFLOW_START,
            event_data={"workflow_name": workflow_name},
            timestamp=datetime.now(UTC)
        )

        self.events.append(event)

        if self.config.performance_monitoring:
            self.logger.info(f"Started monitoring workflow: {workflow_name}")

    def end_workflow_monitoring(self, workflow_name: str, success: bool = True) -> None:
        """End monitoring for a workflow execution."""
        end_time = time.time()

        if self.workflow_start_time:
            total_time = end_time - self.workflow_start_time
            self.performance_metrics.total_execution_time = total_time

        event = MonitoringEvent(
            event_type=MonitoringEventType.WORKFLOW_END,
            event_data={
                "workflow_name": workflow_name,
                "total_execution_time": self.performance_metrics.total_execution_time
            },
            timestamp=datetime.now(UTC),
            duration=self.performance_metrics.total_execution_time,
            success=success
        )

        self.events.append(event)

        if self.config.performance_monitoring:
            self.logger.info(
                f"Completed monitoring workflow: {workflow_name} "
                f"(Duration: {self.performance_metrics.total_execution_time:.2f}s)"
            )

    def start_step_monitoring(self, step_name: str) -> None:
        """Start monitoring for a workflow step."""
        start_time = time.time()
        self.active_steps[step_name] = start_time

        if self.config.step_timing_enabled:
            event = MonitoringEvent(
                event_type=MonitoringEventType.STEP_START,
                event_data={"step_name": step_name},
                step_name=step_name,
                timestamp=datetime.now(UTC)
            )
            self.events.append(event)

    def end_step_monitoring(self, step_name: str, success: bool = True) -> float:
        """End monitoring for a workflow step and return duration."""
        end_time = time.time()
        start_time = self.active_steps.pop(step_name, end_time)
        duration = end_time - start_time

        # Store step timing
        self.performance_metrics.step_times[step_name] = duration

        if self.config.step_timing_enabled:
            event = MonitoringEvent(
                event_type=MonitoringEventType.STEP_END,
                event_data={"step_name": step_name},
                step_name=step_name,
                duration=duration,
                success=success,
                timestamp=datetime.now(UTC)
            )
            self.events.append(event)

            self.logger.info(f"Step '{step_name}' completed in {duration:.2f}s")

        return duration

    def start_agent_monitoring(self, agent_type: str, step_name: str | None = None) -> None:
        """Start monitoring for an agent execution."""
        start_time = time.time()
        agent_key = f"{agent_type}_{step_name}" if step_name else agent_type
        self.active_steps[agent_key] = start_time

        event = MonitoringEvent(
            event_type=MonitoringEventType.AGENT_START,
            event_data={"agent_type": agent_type},
            step_name=step_name,
            agent_type=agent_type,
            timestamp=datetime.now(UTC)
        )
        self.events.append(event)

    def end_agent_monitoring(
        self,
        agent_type: str,
        step_name: str | None = None,
        success: bool = True,
        result_data: dict[str, Any] | None = None
    ) -> float:
        """End monitoring for an agent execution and return duration."""
        end_time = time.time()
        agent_key = f"{agent_type}_{step_name}" if step_name else agent_type
        start_time = self.active_steps.pop(agent_key, end_time)
        duration = end_time - start_time

        # Store agent performance
        if agent_type not in self.performance_metrics.agent_performance:
            self.performance_metrics.agent_performance[agent_type] = {}

        self.performance_metrics.agent_performance[agent_type][step_name or "default"] = duration

        event_data = {"agent_type": agent_type}
        if result_data:
            event_data.update(result_data)

        event = MonitoringEvent(
            event_type=MonitoringEventType.AGENT_END,
            event_data=event_data,
            step_name=step_name,
            agent_type=agent_type,
            duration=duration,
            success=success,
            timestamp=datetime.now(UTC)
        )
        self.events.append(event)

        self.logger.info(f"Agent '{agent_type}' completed in {duration:.2f}s")

        return duration

    def record_error(
        self,
        error: Exception,
        step_name: str | None = None,
        agent_type: str | None = None,
        context: dict[str, Any] | None = None
    ) -> None:
        """Record an error event for monitoring."""
        event_data = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {}
        }

        event = MonitoringEvent(
            event_type=MonitoringEventType.ERROR_OCCURRED,
            event_data=event_data,
            step_name=step_name,
            agent_type=agent_type,
            success=False,
            timestamp=datetime.now(UTC)
        )

        self.events.append(event)
        self.logger.error(f"Error recorded: {error} (Step: {step_name}, Agent: {agent_type})")

    def get_performance_summary(self) -> dict[str, Any]:
        """Get comprehensive performance summary."""
        return {
            "total_execution_time": self.performance_metrics.total_execution_time,
            "step_times": self.performance_metrics.step_times,
            "agent_performance": self.performance_metrics.agent_performance,
            "total_events": len(self.events),
            "error_count": len([e for e in self.events if not e.success]),
            "timestamp": datetime.now(UTC).isoformat()
        }

    def get_monitoring_events(
        self,
        event_type: MonitoringEventType | None = None,
        step_name: str | None = None
    ) -> list[MonitoringEvent]:
        """Get filtered monitoring events."""
        events = self.events

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        if step_name:
            events = [e for e in events if e.step_name == step_name]

        return events
