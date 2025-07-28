"""
Agent instrumentation helpers for Phoenix observability.

This module provides decorators and utilities to instrument LlamaIndex agents
with Phoenix tracing, ensuring all agent actions are observable.
"""

import functools
from typing import Any, Callable, TypeVar, cast

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

# Type variable for generic decorator
F = TypeVar('F', bound=Callable[..., Any])


def trace_agent_method(
    span_name: str | None = None,
    attributes: dict[str, Any] | None = None,
    record_exception: bool = True
) -> Callable[[F], F]:
    """
    Decorator to trace agent methods with Phoenix.
    
    Args:
        span_name: Optional span name (defaults to method name)
        attributes: Additional attributes to add to span
        record_exception: Whether to record exceptions in spans
        
    Returns:
        Decorated function with tracing
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get tracer
            tracer = trace.get_tracer(__name__)
            
            # Determine span name
            name = span_name or f"{func.__module__}.{func.__name__}"
            
            # Start span
            with tracer.start_as_current_span(name) as span:
                # Add default attributes
                span.set_attribute("agent.method", func.__name__)
                span.set_attribute("agent.module", func.__module__)
                
                # Add custom attributes
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)
                
                # Extract agent context if available
                if args and hasattr(args[0], '__class__'):
                    agent_instance = args[0]
                    span.set_attribute("agent.class", agent_instance.__class__.__name__)
                    
                    # Add agent-specific attributes
                    if hasattr(agent_instance, 'agent_id'):
                        span.set_attribute("agent.id", agent_instance.agent_id)
                    if hasattr(agent_instance, 'gamp_category'):
                        span.set_attribute("agent.gamp_category", agent_instance.gamp_category)
                
                try:
                    # Execute the method
                    result = await func(*args, **kwargs)
                    
                    # Add result attributes if applicable
                    if isinstance(result, dict):
                        if 'success' in result:
                            span.set_attribute("agent.result.success", result['success'])
                        if 'error' in result:
                            span.set_attribute("agent.result.error", str(result['error']))
                    
                    return result
                    
                except Exception as e:
                    # Record exception
                    if record_exception:
                        span.record_exception(e)
                        span.set_status(
                            Status(StatusCode.ERROR, str(e))
                        )
                    raise
        
        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get tracer
            tracer = trace.get_tracer(__name__)
            
            # Determine span name
            name = span_name or f"{func.__module__}.{func.__name__}"
            
            # Start span
            with tracer.start_as_current_span(name) as span:
                # Add default attributes
                span.set_attribute("agent.method", func.__name__)
                span.set_attribute("agent.module", func.__module__)
                
                # Add custom attributes
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)
                
                # Extract agent context if available
                if args and hasattr(args[0], '__class__'):
                    agent_instance = args[0]
                    span.set_attribute("agent.class", agent_instance.__class__.__name__)
                    
                    # Add agent-specific attributes
                    if hasattr(agent_instance, 'agent_id'):
                        span.set_attribute("agent.id", agent_instance.agent_id)
                    if hasattr(agent_instance, 'gamp_category'):
                        span.set_attribute("agent.gamp_category", agent_instance.gamp_category)
                
                try:
                    # Execute the method
                    result = func(*args, **kwargs)
                    
                    # Add result attributes if applicable
                    if isinstance(result, dict):
                        if 'success' in result:
                            span.set_attribute("agent.result.success", result['success'])
                        if 'error' in result:
                            span.set_attribute("agent.result.error", str(result['error']))
                    
                    return result
                    
                except Exception as e:
                    # Record exception
                    if record_exception:
                        span.record_exception(e)
                        span.set_status(
                            Status(StatusCode.ERROR, str(e))
                        )
                    raise
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return cast(F, async_wrapper)
        else:
            return cast(F, sync_wrapper)
    
    return decorator


def trace_workflow_step(
    step_name: str,
    gamp_category: str | None = None,
    compliance_required: bool = True
) -> Callable[[F], F]:
    """
    Decorator specifically for workflow steps with compliance tracking.
    
    Args:
        step_name: Name of the workflow step
        gamp_category: GAMP category if applicable
        compliance_required: Whether this step requires compliance tracking
        
    Returns:
        Decorated function with workflow tracing
    """
    attributes = {
        "workflow.step_name": step_name,
        "workflow.compliance_required": compliance_required
    }
    
    if gamp_category:
        attributes["workflow.gamp_category"] = gamp_category
    
    return trace_agent_method(
        span_name=f"workflow.{step_name}",
        attributes=attributes
    )


class InstrumentedAgent:
    """
    Mixin class to add Phoenix instrumentation to agents.
    
    Add this as a base class to automatically instrument agent methods.
    """
    
    def __init__(self, *args: Any, **kwargs: Any):
        """Initialize instrumented agent."""
        super().__init__(*args, **kwargs)
        self._tracer = trace.get_tracer(self.__class__.__module__)
        
    def create_span(self, name: str, **attributes: Any) -> trace.Span:
        """
        Create a new span for manual instrumentation.
        
        Args:
            name: Span name
            **attributes: Span attributes
            
        Returns:
            Span instance
        """
        span = self._tracer.start_span(name)
        
        # Add agent context
        span.set_attribute("agent.class", self.__class__.__name__)
        if hasattr(self, 'agent_id'):
            span.set_attribute("agent.id", self.agent_id)
        
        # Add custom attributes
        for key, value in attributes.items():
            span.set_attribute(key, value)
            
        return span
    
    def add_event(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        """
        Add an event to the current span.
        
        Args:
            name: Event name
            attributes: Event attributes
        """
        current_span = trace.get_current_span()
        if current_span and current_span.is_recording():
            current_span.add_event(name, attributes=attributes or {})


# Import asyncio only when needed
import asyncio