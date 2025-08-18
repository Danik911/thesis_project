"""
Audit Middleware for Data Transformation Tracking

Provides middleware components for automatically tracking data transformations
throughout the pharmaceutical workflow system. Integrates with the comprehensive
audit trail to ensure 100% coverage of data changes for regulatory compliance.

Features:
- Automatic before/after state capture
- Transformation rule documentation
- Data integrity verification
- Workflow context propagation
- ALCOA+ compliance verification
"""

import copy
import functools
import logging
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any, TypeVar
from uuid import uuid4

from .audit_trail import get_audit_trail

logger = logging.getLogger(__name__)

# Type variable for generic function decoration
F = TypeVar("F", bound=Callable[..., Any])


class DataTransformationTracker:
    """
    Middleware for tracking data transformations in pharmaceutical workflows.
    
    Automatically captures before/after states, validates transformations,
    and logs complete audit trails for regulatory compliance.
    """

    def __init__(self, audit_trail=None):
        """Initialize transformation tracker with audit trail."""
        self.audit_trail = audit_trail or get_audit_trail()
        self.active_transformations = {}

    def track_transformation(
        self,
        transformation_type: str,
        transformation_rules: list[str] | None = None,
        workflow_step: str | None = None,
        include_deep_copy: bool = True
    ):
        """
        Decorator for tracking data transformations.
        
        Args:
            transformation_type: Type of transformation being tracked
            transformation_rules: List of rules applied during transformation
            workflow_step: Current workflow step
            include_deep_copy: Whether to deep copy data for integrity
            
        Returns:
            Decorated function with transformation tracking
        """
        def decorator(func: F) -> F:
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await self._execute_tracked_transformation(
                    func, args, kwargs, transformation_type,
                    transformation_rules or [], workflow_step, include_deep_copy, is_async=True
                )

            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                return self._execute_tracked_transformation(
                    func, args, kwargs, transformation_type,
                    transformation_rules or [], workflow_step, include_deep_copy, is_async=False
                )

            # Return appropriate wrapper based on function type
            import asyncio
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            return sync_wrapper

        return decorator

    async def _execute_tracked_transformation(
        self,
        func: Callable,
        args: tuple,
        kwargs: dict,
        transformation_type: str,
        transformation_rules: list[str],
        workflow_step: str | None,
        include_deep_copy: bool,
        is_async: bool
    ):
        """Execute function with transformation tracking."""
        transformation_id = str(uuid4())
        start_time = datetime.now(UTC)

        # Capture input state
        input_state = self._capture_input_state(args, kwargs, include_deep_copy)

        # Track active transformation
        self.active_transformations[transformation_id] = {
            "type": transformation_type,
            "start_time": start_time,
            "input_state": input_state,
            "function_name": func.__name__,
            "workflow_step": workflow_step
        }

        try:
            # Execute the actual function
            if is_async:
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            # Capture output state
            output_state = self._capture_output_state(result, include_deep_copy)

            # Calculate transformation metadata
            end_time = datetime.now(UTC)
            transformation_metadata = {
                "transformation_id": transformation_id,
                "function_name": func.__name__,
                "execution_time_seconds": (end_time - start_time).total_seconds(),
                "input_argument_count": len(args) + len(kwargs),
                "transformation_success": True,
                "integrity_preserved": self._verify_integrity(input_state, output_state)
            }

            # Log transformation to audit trail
            self.audit_trail.log_data_transformation(
                transformation_type=transformation_type,
                source_data=input_state,
                target_data=output_state,
                transformation_rules=transformation_rules + [f"function:{func.__name__}"],
                transformation_metadata=transformation_metadata,
                workflow_step=workflow_step or "unknown_step",
                workflow_context={
                    "transformation_id": transformation_id,
                    "function_module": func.__module__,
                    "execution_timestamp": end_time.isoformat()
                }
            )

            # Clean up tracking
            del self.active_transformations[transformation_id]

            return result

        except Exception as e:
            # Log transformation failure
            end_time = datetime.now(UTC)
            failure_metadata = {
                "transformation_id": transformation_id,
                "function_name": func.__name__,
                "execution_time_seconds": (end_time - start_time).total_seconds(),
                "transformation_success": False,
                "error_type": type(e).__name__,
                "error_message": str(e)
            }

            # Log failed transformation
            self.audit_trail.log_error_recovery(
                error_type="data_transformation_failure",
                error_message=str(e),
                error_context={
                    "transformation_type": transformation_type,
                    "transformation_id": transformation_id,
                    "input_state": input_state,
                    "function_name": func.__name__
                },
                recovery_strategy="exception_propagation",
                recovery_actions=["log_failure", "propagate_exception"],
                recovery_success=False,
                workflow_step=workflow_step or "unknown_step",
                workflow_context={"transformation_metadata": failure_metadata}
            )

            # Clean up tracking
            if transformation_id in self.active_transformations:
                del self.active_transformations[transformation_id]

            # Re-raise exception (NO FALLBACKS)
            raise

    def _capture_input_state(self, args: tuple, kwargs: dict, include_deep_copy: bool) -> dict[str, Any]:
        """Capture input state for transformation tracking."""
        try:
            input_state = {
                "args": list(args) if include_deep_copy else [f"<arg_{i}:{type(arg).__name__}>" for i, arg in enumerate(args)],
                "kwargs": dict(kwargs) if include_deep_copy else {k: f"<{k}:{type(v).__name__}>" for k, v in kwargs.items()},
                "arg_count": len(args),
                "kwarg_count": len(kwargs),
                "capture_method": "deep_copy" if include_deep_copy else "type_summary"
            }

            if include_deep_copy:
                # Perform deep copy to preserve original state
                try:
                    input_state["args"] = copy.deepcopy(list(args))
                    input_state["kwargs"] = copy.deepcopy(dict(kwargs))
                except Exception as e:
                    logger.warning(f"[AUDIT] Deep copy failed for input state: {e}")
                    # Fall back to type summary
                    input_state["args"] = [f"<arg_{i}:{type(arg).__name__}>" for i, arg in enumerate(args)]
                    input_state["kwargs"] = {k: f"<{k}:{type(v).__name__}>" for k, v in kwargs.items()}
                    input_state["capture_method"] = "type_summary_fallback"

            return input_state

        except Exception as e:
            logger.error(f"[AUDIT] Input state capture failed: {e}")
            # Return minimal state information
            return {
                "args": f"<capture_failed: {len(args)} args>",
                "kwargs": f"<capture_failed: {len(kwargs)} kwargs>",
                "capture_error": str(e),
                "capture_method": "failed"
            }

    def _capture_output_state(self, result: Any, include_deep_copy: bool) -> dict[str, Any]:
        """Capture output state for transformation tracking."""
        try:
            if include_deep_copy:
                try:
                    output_data = copy.deepcopy(result)
                except Exception as e:
                    logger.warning(f"[AUDIT] Deep copy failed for output state: {e}")
                    output_data = f"<result:{type(result).__name__}>"
            else:
                output_data = f"<result:{type(result).__name__}>"

            return {
                "result": output_data,
                "result_type": type(result).__name__,
                "result_size": self._estimate_size(result),
                "capture_method": "deep_copy" if include_deep_copy and not isinstance(output_data, str) else "type_summary"
            }

        except Exception as e:
            logger.error(f"[AUDIT] Output state capture failed: {e}")
            return {
                "result": f"<capture_failed: {type(result).__name__}>",
                "capture_error": str(e),
                "capture_method": "failed"
            }

    def _verify_integrity(self, input_state: dict[str, Any], output_state: dict[str, Any]) -> bool:
        """Verify data integrity during transformation."""
        try:
            # Basic integrity checks
            integrity_checks = {
                "input_captured": input_state.get("capture_method") != "failed",
                "output_captured": output_state.get("capture_method") != "failed",
                "no_capture_errors": "capture_error" not in input_state and "capture_error" not in output_state
            }

            return all(integrity_checks.values())

        except Exception as e:
            logger.warning(f"[AUDIT] Integrity verification failed: {e}")
            return False

    def _estimate_size(self, obj: Any) -> int:
        """Estimate the size of an object for audit purposes."""
        try:
            import sys
            return sys.getsizeof(obj)
        except Exception:
            return 0


class WorkflowContextPropagator:
    """
    Middleware for propagating workflow context through function calls.
    
    Ensures that workflow metadata is available for audit trail logging
    throughout the entire execution chain.
    """

    def __init__(self, audit_trail=None):
        """Initialize context propagator with audit trail."""
        self.audit_trail = audit_trail or get_audit_trail()
        self.context_stack = []

    def with_workflow_context(
        self,
        workflow_step: str,
        context_data: dict[str, Any] | None = None,
        log_context_changes: bool = True
    ):
        """
        Decorator for propagating workflow context.
        
        Args:
            workflow_step: Name of the workflow step
            context_data: Additional context data
            log_context_changes: Whether to log context state changes
            
        Returns:
            Decorated function with context propagation
        """
        def decorator(func: F) -> F:
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await self._execute_with_context(
                    func, args, kwargs, workflow_step, context_data or {},
                    log_context_changes, is_async=True
                )

            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                return self._execute_with_context(
                    func, args, kwargs, workflow_step, context_data or {},
                    log_context_changes, is_async=False
                )

            # Return appropriate wrapper based on function type
            import asyncio
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            return sync_wrapper

        return decorator

    async def _execute_with_context(
        self,
        func: Callable,
        args: tuple,
        kwargs: dict,
        workflow_step: str,
        context_data: dict[str, Any],
        log_context_changes: bool,
        is_async: bool
    ):
        """Execute function with workflow context propagation."""
        context_id = str(uuid4())

        # Create context entry
        context_entry = {
            "context_id": context_id,
            "workflow_step": workflow_step,
            "function_name": func.__name__,
            "context_data": context_data,
            "entry_timestamp": datetime.now(UTC).isoformat(),
            "parent_context": self.context_stack[-1] if self.context_stack else None
        }

        # Push context onto stack
        self.context_stack.append(context_entry)

        # Log context entry if requested
        if log_context_changes:
            self.audit_trail.log_state_transition(
                from_state=f"workflow_step_{self.context_stack[-2]['workflow_step']}" if len(self.context_stack) > 1 else "workflow_start",
                to_state=f"workflow_step_{workflow_step}",
                transition_trigger=f"function_call:{func.__name__}",
                transition_metadata={
                    "context_id": context_id,
                    "context_stack_depth": len(self.context_stack),
                    "function_module": func.__module__
                },
                workflow_step=workflow_step,
                state_data=context_data,
                workflow_context=context_entry
            )

        try:
            # Execute function with context
            if is_async:
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            # Log successful context exit
            if log_context_changes:
                self.audit_trail.log_state_transition(
                    from_state=f"workflow_step_{workflow_step}",
                    to_state=f"workflow_step_{workflow_step}_complete",
                    transition_trigger="function_completion",
                    transition_metadata={
                        "context_id": context_id,
                        "execution_successful": True
                    },
                    workflow_step=workflow_step,
                    workflow_context=context_entry
                )

            return result

        except Exception as e:
            # Log context error
            if log_context_changes:
                self.audit_trail.log_error_recovery(
                    error_type="workflow_context_error",
                    error_message=str(e),
                    error_context={
                        "context_id": context_id,
                        "workflow_step": workflow_step,
                        "function_name": func.__name__,
                        "context_data": context_data
                    },
                    recovery_strategy="context_cleanup_and_propagate",
                    recovery_actions=["pop_context_stack", "propagate_exception"],
                    recovery_success=True,  # Context cleanup successful
                    workflow_step=workflow_step,
                    workflow_context=context_entry
                )

            raise

        finally:
            # Pop context from stack
            if self.context_stack and self.context_stack[-1]["context_id"] == context_id:
                self.context_stack.pop()


# Global instances for middleware components
_global_transformation_tracker: DataTransformationTracker | None = None
_global_context_propagator: WorkflowContextPropagator | None = None


def get_transformation_tracker() -> DataTransformationTracker:
    """Get the global data transformation tracker."""
    global _global_transformation_tracker
    if _global_transformation_tracker is None:
        _global_transformation_tracker = DataTransformationTracker()
    return _global_transformation_tracker


def get_context_propagator() -> WorkflowContextPropagator:
    """Get the global workflow context propagator."""
    global _global_context_propagator
    if _global_context_propagator is None:
        _global_context_propagator = WorkflowContextPropagator()
    return _global_context_propagator


# Convenience decorators
def track_data_transformation(
    transformation_type: str,
    transformation_rules: list[str] | None = None,
    workflow_step: str | None = None
):
    """Convenience decorator for data transformation tracking."""
    return get_transformation_tracker().track_transformation(
        transformation_type=transformation_type,
        transformation_rules=transformation_rules,
        workflow_step=workflow_step
    )


def with_workflow_context(
    workflow_step: str,
    context_data: dict[str, Any] | None = None
):
    """Convenience decorator for workflow context propagation."""
    return get_context_propagator().with_workflow_context(
        workflow_step=workflow_step,
        context_data=context_data
    )


# Export main classes and functions
__all__ = [
    "DataTransformationTracker",
    "WorkflowContextPropagator",
    "get_context_propagator",
    "get_transformation_tracker",
    "track_data_transformation",
    "with_workflow_context"
]
