"""
Integration examples and utilities for the GAMP-5 compliant event logging system.

This module demonstrates how to integrate the structured event logging system
with existing LlamaIndex workflows and provides helper functions for
common integration patterns.
"""

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from llama_index.core.workflow import (
    Context,
    StartEvent,
    StopEvent,
    Workflow,
    step,
)

from ..core.events import (
    GAMPCategorizationEvent,
    GAMPCategory,
    PlanningEvent,
    ValidationEvent,
    ValidationStatus,
)
from .config import Config, get_config
from .event_logging import EventStreamHandler, setup_event_logging


class EventLoggingMixin:
    """
    Mixin class to add event logging capabilities to workflows.
    
    Provides methods to easily integrate GAMP-5 compliant logging
    into any LlamaIndex workflow.
    """

    def __init__(self, *args, **kwargs):
        """Initialize event logging mixin."""
        super().__init__(*args, **kwargs)
        self.event_handler: EventStreamHandler | None = None
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")

    def setup_event_logging(self, config: Config | None = None) -> None:
        """Setup event logging for this workflow."""
        # Ensure logger is available
        if not hasattr(self, "logger"):
            self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")

        try:
            self.event_handler = setup_event_logging(config)
            self.logger.info("Event logging enabled for workflow")
        except Exception as e:
            self.logger.error(f"Failed to setup event logging: {e}")
            self.event_handler = None

    def log_workflow_event(
        self,
        ctx: Context,
        event_type: str,
        message: str,
        payload: dict[str, Any] | None = None,
        level: str = "INFO"
    ) -> None:
        """
        Log a workflow event with compliance metadata.
        
        Args:
            ctx: Workflow context
            event_type: Type of event
            message: Event message
            payload: Optional event payload
            level: Log level (DEBUG, INFO, WARNING, ERROR)
        """
        if not self.event_handler:
            return

        try:
            # Create structured event data
            event_data = {
                "event_type": event_type,
                "event_id": str(uuid4()),
                "timestamp": datetime.now(UTC).isoformat(),
                "workflow_context": {
                    "workflow_class": self.__class__.__name__,
                    "step": getattr(ctx, "_current_step", "unknown"),
                    "correlation_id": getattr(ctx, "_correlation_id", str(uuid4()))
                },
                "payload": {
                    "message": message,
                    "level": level,
                    **(payload or {})
                }
            }

            # Write to context stream (LlamaIndex pattern)
            ctx.write_event_to_stream(event_data)

            # Log through standard logging
            log_level = getattr(logging, level.upper(), logging.INFO)
            self.logger.log(log_level, f"[{event_type}] {message}")

        except Exception as e:
            self.logger.error(f"Error logging workflow event: {e}")

    def log_agent_interaction(
        self,
        ctx: Context,
        agent_type: str,
        request_data: dict[str, Any],
        result_data: dict[str, Any] | None = None,
        success: bool = True,
        error_message: str | None = None
    ) -> None:
        """Log agent interaction events."""
        # Log request
        self.log_workflow_event(
            ctx,
            "AgentRequestEvent",
            f"Agent request: {agent_type}",
            {
                "agent_type": agent_type,
                "request_data": request_data,
                "timestamp": datetime.now(UTC).isoformat()
            }
        )

        # Log result if provided
        if result_data is not None or error_message:
            self.log_workflow_event(
                ctx,
                "AgentResultEvent",
                f"Agent result: {agent_type} - {'Success' if success else 'Failed'}",
                {
                    "agent_type": agent_type,
                    "result_data": result_data or {},
                    "success": success,
                    "error_message": error_message,
                    "processing_time": 0.0  # Would be calculated in real implementation
                },
                level="INFO" if success else "ERROR"
            )


class GAMP5EventLoggingWorkflow(Workflow, EventLoggingMixin):
    """
    Example workflow demonstrating GAMP-5 compliant event logging integration.
    
    Shows how to integrate the structured event logging system with
    a pharmaceutical validation workflow.
    """

    def __init__(self, timeout: int = 300, enable_logging: bool = True):
        """Initialize the workflow with event logging."""
        super().__init__(timeout=timeout)

        # Initialize logger first
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")

        if enable_logging:
            self.setup_event_logging()

        self.logger.info("GAMP5EventLoggingWorkflow initialized")

    @step
    async def start_processing(self, ctx: Context, ev: StartEvent) -> GAMPCategorizationEvent:
        """Demonstrate categorization with event logging."""
        self.log_workflow_event(
            ctx,
            "WorkflowStartEvent",
            "Starting GAMP-5 categorization workflow",
            {
                "document_name": ev.data.get("document_name", "unknown"),
                "document_version": ev.data.get("document_version", "1.0"),
                "author": ev.data.get("author", "system")
            }
        )

        # Simulate categorization process
        await asyncio.sleep(0.1)  # Simulate processing time

        # Create categorization event
        categorization_event = GAMPCategorizationEvent(
            gamp_category=GAMPCategory.CATEGORY_5,
            confidence_score=0.85,
            justification="Custom pharmaceutical application requiring full validation",
            risk_assessment={
                "risk_level": "High",
                "complexity": "High",
                "regulatory_impact": "Critical"
            },
            categorized_by="gamp5_categorization_agent"
        )

        # Log categorization result
        self.log_workflow_event(
            ctx,
            "GAMPCategorizationEvent",
            f"GAMP categorization completed: Category {categorization_event.gamp_category.value}",
            {
                "gamp_category": categorization_event.gamp_category.value,
                "confidence_score": categorization_event.confidence_score,
                "review_required": categorization_event.review_required,
                "justification": categorization_event.justification[:100] + "..."
            }
        )

        return categorization_event

    @step
    async def planning_phase(self, ctx: Context, ev: GAMPCategorizationEvent) -> PlanningEvent:
        """Demonstrate planning with event logging."""
        self.log_workflow_event(
            ctx,
            "PlanningPhaseStart",
            "Starting test planning based on GAMP categorization",
            {
                "gamp_category": ev.gamp_category.value,
                "confidence_score": ev.confidence_score
            }
        )

        # Simulate agent interaction
        self.log_agent_interaction(
            ctx,
            "planner_agent",
            {
                "gamp_category": ev.gamp_category.value,
                "risk_assessment": ev.risk_assessment,
                "requirements": ["functional_testing", "security_testing", "performance_testing"]
            },
            {
                "test_strategy": "comprehensive_validation",
                "estimated_test_count": 45,
                "required_test_types": ["unit", "integration", "system", "acceptance"]
            }
        )

        # Create planning event
        planning_event = PlanningEvent(
            test_strategy={
                "approach": "risk_based_testing",
                "coverage_target": 95,
                "automation_level": "high"
            },
            required_test_types=["unit", "integration", "system", "acceptance"],
            compliance_requirements=["GAMP-5", "21 CFR Part 11", "ALCOA+"],
            estimated_test_count=45,
            planner_agent_id="planner_agent_v1.0",
            gamp_category=ev.gamp_category
        )

        self.log_workflow_event(
            ctx,
            "PlanningEvent",
            f"Test planning completed: {planning_event.estimated_test_count} tests planned",
            {
                "test_strategy": planning_event.test_strategy,
                "required_test_types": planning_event.required_test_types,
                "compliance_requirements": planning_event.compliance_requirements
            }
        )

        return planning_event

    @step
    async def validation_phase(self, ctx: Context, ev: PlanningEvent) -> ValidationEvent:
        """Demonstrate validation with event logging."""
        self.log_workflow_event(
            ctx,
            "ValidationPhaseStart",
            "Starting validation of test planning results",
            {
                "estimated_test_count": ev.estimated_test_count,
                "compliance_requirements": ev.compliance_requirements
            }
        )

        # Simulate validation process with potential issues
        validation_issues = []

        # Check compliance requirements
        if "GAMP-5" not in ev.compliance_requirements:
            validation_issues.append({
                "issue_type": "COMPLIANCE_GAP",
                "description": "GAMP-5 compliance not explicitly addressed",
                "severity": "HIGH"
            })

        # Create validation event
        validation_event = ValidationEvent(
            validation_type="test_planning_validation",
            validation_results={
                "compliance_check": "PASSED" if not validation_issues else "ISSUES_FOUND",
                "test_coverage": 95.5,
                "risk_coverage": 98.2
            },
            compliance_score=0.95 if not validation_issues else 0.75,
            issues_found=validation_issues,
            alcoa_compliance={
                "attributable": True,
                "legible": True,
                "contemporaneous": True,
                "original": True,
                "accurate": True
            },
            cfr_part11_compliance={
                "electronic_signature": False,
                "audit_trail": True,
                "tamper_evident": True,
                "record_integrity": True
            },
            validator_id="validation_agent_v1.0",
            validation_status=ValidationStatus.VALIDATED if not validation_issues else ValidationStatus.REQUIRES_REVIEW
        )

        # Log validation results
        log_level = "INFO" if not validation_issues else "WARNING"
        self.log_workflow_event(
            ctx,
            "ValidationEvent",
            f"Validation completed: {validation_event.validation_status.value}",
            {
                "validation_type": validation_event.validation_type,
                "compliance_score": validation_event.compliance_score,
                "issues_count": len(validation_issues),
                "alcoa_compliance": validation_event.alcoa_compliance,
                "cfr_part11_compliance": validation_event.cfr_part11_compliance
            },
            level=log_level
        )

        return validation_event

    @step
    async def complete_workflow(self, ctx: Context, ev: ValidationEvent) -> StopEvent:
        """Complete the workflow with final logging."""
        self.log_workflow_event(
            ctx,
            "WorkflowCompletionEvent",
            f"Workflow completed with status: {ev.validation_status.value}",
            {
                "final_validation_status": ev.validation_status.value,
                "compliance_score": ev.compliance_score,
                "issues_found": len(ev.issues_found),
                "workflow_duration": "calculated_in_real_implementation"
            }
        )

        # Generate summary
        summary = {
            "validation_status": ev.validation_status.value,
            "compliance_score": ev.compliance_score,
            "issues_found": ev.issues_found,
            "alcoa_compliance": ev.alcoa_compliance,
            "cfr_part11_compliance": ev.cfr_part11_compliance,
            "workflow_completed": True
        }

        return StopEvent(result=summary)


async def handle_hitl_consultation(
    event: Any,
    handler: Any
) -> bool:
    """
    Handle human-in-the-loop consultation during workflow execution.
    
    This function detects ConsultationRequiredEvent and prompts the user
    for input, then creates and sends a HumanResponseEvent back to the workflow.
    
    Args:
        event: The workflow event to check
        handler: The workflow handler to send events to
        
    Returns:
        True if consultation was handled, False otherwise
    """
    # Import here to avoid circular imports
    import sys

    from ..core.events import ConsultationRequiredEvent, HumanResponseEvent
    from ..shared.output_manager import safe_print

    # Check if this is a consultation required event
    if not isinstance(event, ConsultationRequiredEvent):
        return False

    # Check if running in interactive terminal
    if not sys.stdin.isatty():
        safe_print("[WARNING]  Non-interactive terminal detected - HITL consultation will timeout")
        return False

    safe_print("\n" + "="*60)
    safe_print("[HUMAN] HUMAN CONSULTATION REQUIRED")
    safe_print("="*60)
    safe_print(f"Consultation Type: {event.consultation_type}")
    safe_print(f"Urgency: {event.urgency}")
    safe_print(f"Required Expertise: {', '.join(event.required_expertise)}")
    safe_print("")
    safe_print("Context:")
    for key, value in event.context.items():
        safe_print(f"  {key}: {value}")
    safe_print("")

    try:
        # Handle different consultation types
        if "categorization" in event.consultation_type.lower():
            safe_print("Please provide GAMP categorization decision:")
            safe_print("Available categories: 1 (Infrastructure), 3 (Non-configured), 4 (Configured), 5 (Custom)")

            user_input = input("Enter GAMP category (1, 3, 4, 5): ").strip()
            if user_input not in ["1", "3", "4", "5"]:
                safe_print("[ERROR] Invalid category. Using conservative default (Category 5)")
                gamp_category = 5
            else:
                gamp_category = int(user_input)

            rationale = input("Enter decision rationale: ").strip()
            if not rationale:
                rationale = f"Human decision: GAMP Category {gamp_category}"

            confidence_input = input("Enter confidence level (0.0-1.0) [default: 0.8]: ").strip()
            try:
                confidence = float(confidence_input) if confidence_input else 0.8
                confidence = max(0.0, min(1.0, confidence))  # Clamp to valid range
            except ValueError:
                confidence = 0.8

            # Create response data
            response_data = {
                "gamp_category": gamp_category,
                "risk_assessment": {
                    "risk_level": "HIGH" if gamp_category >= 4 else "MEDIUM"
                }
            }

        else:
            # Generic consultation handling
            safe_print("Please provide your consultation response:")
            user_input = input("Enter your decision/response: ").strip()
            rationale = input("Enter decision rationale: ").strip()

            if not user_input:
                safe_print("[ERROR] No input provided - consultation will timeout")
                return False

            if not rationale:
                rationale = f"Human decision: {user_input}"

            confidence_input = input("Enter confidence level (0.0-1.0) [default: 0.8]: ").strip()
            try:
                confidence = float(confidence_input) if confidence_input else 0.8
                confidence = max(0.0, min(1.0, confidence))
            except ValueError:
                confidence = 0.8

            response_data = {"decision": user_input}

        # Get user details
        user_id = input("Enter your user ID [default: cli_user]: ").strip() or "cli_user"
        user_role = input("Enter your role [default: validation_engineer]: ").strip() or "validation_engineer"

        # Create HumanResponseEvent
        human_response = HumanResponseEvent(
            response_type="decision",
            response_data=response_data,
            user_id=user_id,
            user_role=user_role,
            decision_rationale=rationale,
            confidence_level=confidence,
            consultation_id=event.consultation_id,
            session_id=event.consultation_id,  # Use consultation_id as session_id for simplicity
            approval_level="user"
        )

        # Send the response event to the workflow
        handler.ctx.send_event(human_response)

        safe_print("[SUCCESS] Human response recorded and sent to workflow")
        safe_print("="*60)

        return True

    except (EOFError, KeyboardInterrupt):
        safe_print("\n👋 Consultation cancelled by user - workflow will timeout")
        return False
    except Exception as e:
        safe_print(f"[ERROR] Error processing consultation: {e}")
        return False


async def run_workflow_with_event_logging(
    workflow: Workflow,
    event_handler: EventStreamHandler,
    **kwargs
) -> tuple[Any, list[dict[str, Any]]]:
    """
    Run a LlamaIndex workflow with event logging integration.
    
    This function properly integrates any workflow with the event logging system
    by capturing events from the workflow handler's stream_events() method.
    
    Args:
        workflow: LlamaIndex workflow instance
        event_handler: EventStreamHandler instance for processing events
        **kwargs: Arguments to pass to workflow.run()
        
    Returns:
        Tuple of (workflow_result, captured_events)
    """
    from llama_index.core.workflow import StopEvent

    # Start the workflow - returns a WorkflowHandler (Future-like object)
    handler = workflow.run(**kwargs)

    # Process events as they stream
    events_captured = []
    result = None

    async for event in handler.stream_events():
        # Convert LlamaIndex event to our event format
        event_data = {
            "event_type": event.__class__.__name__,
            "event_id": str(getattr(event, "event_id", uuid4())),
            "timestamp": getattr(event, "timestamp", datetime.now(UTC)).isoformat() if hasattr(getattr(event, "timestamp", None), "isoformat") else str(getattr(event, "timestamp", datetime.now(UTC))),
            "workflow_context": {
                "workflow_class": workflow.__class__.__name__,
                "step": getattr(event, "step", "unknown"),
                "agent_id": getattr(event, "agent_id", "unknown"),
                "correlation_id": str(getattr(event, "correlation_id", uuid4()))
            },
            "payload": {}
        }

        # Extract event-specific data
        if hasattr(event, "__dict__"):
            for key, value in event.__dict__.items():
                if not key.startswith("_") and key not in ["event_id", "timestamp", "step", "agent_id", "correlation_id"]:
                    # Convert complex objects to strings for logging
                    if isinstance(value, (str, int, float, bool, dict, list)):
                        event_data["payload"][key] = value
                    else:
                        event_data["payload"][key] = str(value)

        # Handle HITL consultation if required
        consultation_handled = await handle_hitl_consultation(event, handler)

        # Process through event handler
        processed_event = await event_handler._process_event(event_data)
        if processed_event:
            events_captured.append(processed_event)

        # Check if this is the final result
        if isinstance(event, StopEvent):
            result = event.result

    return result, events_captured


async def demonstrate_event_logging_integration():
    """
    Demonstrate the event logging system integration.
    
    This function shows how to use the GAMP-5 compliant event logging
    system in a real workflow scenario.
    """
    print("[TEST] GAMP-5 Event Logging System Demonstration")
    print("=" * 60)

    # Setup configuration
    config = get_config()
    config.logging.log_level = "DEBUG"
    config.gamp5_compliance.enable_compliance_logging = True
    config.event_streaming.enable_event_streaming = True

    print(f"Configuration: {config.to_dict()}")
    print()

    # Create and run workflow
    workflow = GAMP5EventLoggingWorkflow(enable_logging=True)

    # Prepare start event data
    start_data = {
        "document_name": "pharma_test_system_urs.md",
        "document_version": "2.1",
        "author": "validation_engineer",
        "urs_content": "Sample URS content for pharmaceutical system validation..."
    }

    try:
        print("[START] Running workflow with event logging...")
        result = await workflow.run(data=start_data)
        print("[SUCCESS] Workflow completed successfully")
        print(f"Result: {result}")

        # Get event handler statistics
        if workflow.event_handler:
            stats = workflow.event_handler.get_statistics()
            print("\n[DATA] Event Processing Statistics:")
            print(f"  - Events Processed: {stats['events_processed']}")
            print(f"  - Events Filtered: {stats['events_filtered']}")
            print(f"  - Runtime: {stats['runtime_seconds']:.2f}s")
            print(f"  - Events/Second: {stats['events_per_second']:.2f}")

            # Get compliance statistics
            compliance_stats = workflow.event_handler.compliance_logger.get_audit_statistics()
            print("\n🔒 Compliance Audit Statistics:")
            print(f"  - Total Audit Entries: {compliance_stats['total_audit_entries']}")
            print(f"  - Audit Files: {compliance_stats['audit_file_count']}")
            print(f"  - Total Size: {compliance_stats['total_size_mb']:.2f} MB")
            print(f"  - Compliance Standards: {compliance_stats['compliance_standards']}")

        return result

    except Exception as e:
        print(f"[ERROR] Workflow failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def create_event_logging_test_script():
    """Create a standalone test script for the event logging system."""
    test_script_content = '''#!/usr/bin/env python3
"""
Test script for GAMP-5 compliant event logging system.
"""

import asyncio
import sys
from pathlib import Path

# Add main directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from main.src.shared.event_logging_integration import demonstrate_event_logging_integration

async def main():
    """Run the event logging demonstration."""
    print("Starting GAMP-5 Event Logging System Test")
    print("=" * 50)
    
    result = await demonstrate_event_logging_integration()
    
    if result:
        print("\\n[SUCCESS] Event logging test completed successfully")
        print("[FILE] Check logs/ directory for generated audit files")
    else:
        print("\\n[ERROR] Event logging test failed")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
'''

    script_path = Path("test_event_logging.py")
    script_path.write_text(test_script_content)
    script_path.chmod(0o755)

    return str(script_path)


# Helper functions for common integration patterns

def log_gamp_categorization(
    ctx: Context,
    category: GAMPCategory,
    confidence: float,
    justification: str,
    logger_instance: logging.Logger | None = None
) -> None:
    """Helper to log GAMP categorization events."""
    logger = logger_instance or logging.getLogger(__name__)

    event_data = {
        "event_type": "GAMPCategorizationEvent",
        "category": category.value,
        "confidence": confidence,
        "justification": justification,
        "timestamp": datetime.now(UTC).isoformat()
    }

    ctx.write_event_to_stream(event_data)
    logger.info(f"GAMP Categorization: Category {category.value} (confidence: {confidence:.1%})")


def log_validation_result(
    ctx: Context,
    validation_type: str,
    status: ValidationStatus,
    compliance_score: float,
    issues: list[dict[str, Any]],
    logger_instance: logging.Logger | None = None
) -> None:
    """Helper to log validation events."""
    logger = logger_instance or logging.getLogger(__name__)

    event_data = {
        "event_type": "ValidationEvent",
        "validation_type": validation_type,
        "status": status.value,
        "compliance_score": compliance_score,
        "issues_count": len(issues),
        "timestamp": datetime.now(UTC).isoformat()
    }

    ctx.write_event_to_stream(event_data)

    log_level = logging.INFO if status == ValidationStatus.VALIDATED else logging.WARNING
    logger.log(log_level, f"Validation {validation_type}: {status.value} (score: {compliance_score:.1%})")


# Helper function for running workflows with event logging
async def run_workflow_with_event_logging(
    workflow: Workflow,
    event_handler: EventStreamHandler,
    **kwargs
) -> tuple[Any, list[dict[str, Any]]]:
    """
    Run a workflow and capture all events through the event logging system.
    
    This function properly integrates LlamaIndex workflow event streaming
    with the Task 15 event logging system.
    
    Args:
        workflow: The LlamaIndex workflow to run
        event_handler: The EventStreamHandler for processing events
        **kwargs: Arguments to pass to workflow.run()
        
    Returns:
        Tuple of (result, processed_events) where:
        - result: The workflow result from StopEvent
        - processed_events: List of all events processed by the handler
    
    Example:
        ```python
        workflow = GAMPCategorizationWorkflow()
        event_handler = setup_event_logging()
        
        result, events = await run_workflow_with_event_logging(
            workflow,
            event_handler,
            urs_content="...",
            document_name="test.urs"
        )
        ```
    """
    processed_events = []
    result = None

    # Start the workflow
    handler = workflow.run(**kwargs)

    # Stream and process events
    async for event in handler.stream_events():
        # Convert LlamaIndex event to our format
        event_data = {
            "event_type": event.__class__.__name__,
            "event_id": str(uuid4()),
            "timestamp": datetime.now(UTC).isoformat(),
            "workflow_context": {
                "workflow_class": workflow.__class__.__name__,
                "step": getattr(event, "step", "unknown"),
                "agent_id": getattr(event, "agent_id", "unknown"),
                "correlation_id": str(getattr(event, "correlation_id", uuid4()))
            },
            "payload": {}
        }

        # Extract event attributes
        if hasattr(event, "__dict__"):
            for key, value in event.__dict__.items():
                if not key.startswith("_"):
                    # Handle different value types
                    if isinstance(value, (str, int, float, bool, dict, list)):
                        event_data["payload"][key] = value
                    else:
                        event_data["payload"][key] = str(value)

        # Process through event handler
        processed_event = await event_handler._process_event(event_data)
        if processed_event:
            processed_events.append(processed_event)

        # Extract result from StopEvent
        if hasattr(event, "result"):
            result = event.result

    return result, processed_events


# Export integration utilities
__all__ = [
    "EventLoggingMixin",
    "GAMP5EventLoggingWorkflow",
    "create_event_logging_test_script",
    "demonstrate_event_logging_integration",
    "log_gamp_categorization",
    "log_validation_result",
    "run_workflow_with_event_logging"
]
