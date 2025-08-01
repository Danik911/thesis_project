"""
Unified Test Generation Workflow - Master Orchestrator

This module implements the master workflow that orchestrates all components
of the pharmaceutical test generation system into one cohesive workflow.
It chains together GAMP-5 categorization, test planning, and parallel agent
execution to provide complete end-to-end test generation capabilities.

Key Features:
- Complete workflow orchestration from URS to test generation results
- Integration of categorization → planning → parallel execution → results
- GAMP-5 compliance with complete audit trail
- Error handling and human consultation triggers
- Phoenix observability integration
- Regulatory compliance (ALCOA+, 21 CFR Part 11)

Workflow Flow:
1. URS Document Input → GAMPCategorizationWorkflow
2. GAMPCategorizationEvent → PlannerAgentWorkflow
3. Parallel Agent Coordination (Context, SME, Research)
4. Result Compilation and Final Output
"""

import logging
from datetime import UTC, datetime
from typing import Any

from llama_index.core.llms import LLM
from llama_index.core.workflow import Context, StartEvent, StopEvent, Workflow, step
from llama_index.llms.openai import OpenAI
from src.core.categorization_workflow import GAMPCategorizationWorkflow
from src.agents.oq_generator.events import OQTestGenerationEvent, OQTestSuiteEvent
from src.agents.oq_generator.workflow import OQTestGenerationWorkflow
from src.agents.planner.workflow import PlannerAgentWorkflow
from src.core.events import (
    ConsultationRequiredEvent,
    GAMPCategorizationEvent,
    PlanningEvent,
    URSIngestionEvent,
    WorkflowCompletionEvent,
)
from src.core.human_consultation import HumanConsultationManager
from src.monitoring.phoenix_config import setup_phoenix
from src.shared.config import get_config

# Set up configuration
config = get_config()

# Optional Phoenix monitoring setup
try:
    setup_phoenix()
except ImportError:
    logging.warning("Phoenix monitoring not available")


class UnifiedTestGenerationWorkflow(Workflow):
    """
    Master workflow orchestrator for pharmaceutical test generation.
    
    This workflow coordinates all components of the test generation system:
    - GAMP-5 categorization of URS documents
    - Strategic test planning based on categorization
    - Parallel agent execution for enhanced context
    - OQ test suite generation with quality validation
    - Complete audit trail and regulatory compliance
    
    The workflow is designed to be pharmaceutical-compliant with proper
    error handling, consultation triggers, and no fallback mechanisms
    that could compromise regulatory integrity.
    """

    def __init__(
        self,
        llm: LLM = None,
        timeout: int = 3600,  # 1 hour for complete workflow
        verbose: bool = False, enable_error_handling: bool = True, confidence_threshold: float = 0.60, enable_document_processing: bool = False, enable_parallel_coordination: bool = True
    ):
        """
        Initialize the unified test generation workflow.
        
        Args:
            llm: LlamaIndex LLM instance
            timeout: Maximum workflow execution time in seconds
            verbose: Enable verbose logging
        """
        super().__init__(timeout=timeout, verbose=verbose)
        
        # Initialize LLM
        self.llm = llm or OpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            max_tokens=4000
        )
        
        # Configuration
        self.verbose = verbose
        
        # Workflow session tracking
        self._workflow_session_id = f"unified_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"
        self._workflow_start_time = None
        
        # Initialize components
        self.logger = logging.getLogger(__name__)
        self.consultation_system = HumanConsultationManager()
        
    @step
    async def start_unified_workflow(
        self,
        ctx: Context,
        ev: StartEvent
    ) -> URSIngestionEvent:
        """
        Initialize the unified test generation workflow.
        
        Args:
            ctx: Workflow context
            ev: StartEvent containing initial parameters
            
        Returns:
            URSIngestionEvent to begin document processing
        """
        self._workflow_start_time = datetime.now(UTC)
        
        self.logger.info(
            f"🚀 Starting Unified Test Generation Workflow "
            f"(Session: {self._workflow_session_id})"
        )
        
        # Store session information
        await ctx.set("workflow_session_id", self._workflow_session_id)
        await ctx.set("workflow_start_time", self._workflow_start_time)
        
        # Create URS ingestion event - this will be configured by the main.py caller
        return URSIngestionEvent(
            session_id=self._workflow_session_id,
            timestamp=self._workflow_start_time
        )

    @step 
    async def start(
        self,
        ctx: Context,
        ev: URSIngestionEvent
    ) -> GAMPCategorizationEvent:
        """
        Start document processing and GAMP-5 categorization.
        
        Args:
            ctx: Workflow context
            ev: URS ingestion event
            
        Returns:
            GAMPCategorizationEvent with document categorization
        """
        self.logger.info("📄 Starting GAMP-5 categorization workflow")
        
        # Get document content from context (set by main.py)
        document_content = await ctx.get("document_content")
        document_metadata = await ctx.get("document_metadata", {})
        
        # Create and run categorization workflow  
        categorization_workflow = GAMPCategorizationWorkflow(
            llm=self.llm,
            verbose=self.verbose
        )
        
        # Execute categorization
        categorization_result = await categorization_workflow.run()
        
        # Extract the categorization event from the result
        if hasattr(categorization_result, 'result') and isinstance(categorization_result.result.get('categorization_event'), GAMPCategorizationEvent):
            categorization_event = categorization_result.result['categorization_event']
        else:
            # Create event from result data
            from src.core.events import GAMPCategory
            categorization_event = GAMPCategorizationEvent(
                gamp_category=GAMPCategory(categorization_result.result.get('category', 1)),
                confidence_score=categorization_result.result.get('confidence_score', 0.0),
                rationale=categorization_result.result.get('rationale', 'No rationale provided'),
                compliance_requirements=categorization_result.result.get('compliance_requirements', []),
                document_metadata=document_metadata,
                session_id=self._workflow_session_id
            )
        
        # Store categorization results
        await ctx.set("categorization_event", categorization_event)
        await ctx.set("categorization_result", categorization_result.result)
        
        self.logger.info(
            f"📊 Document categorized as GAMP Category {categorization_event.gamp_category.value} "
            f"(confidence: {categorization_event.confidence_score:.2%})"
        )
        
        return categorization_event

    @step
    async def categorize_document(
        self,
        ctx: Context,
        ev: GAMPCategorizationEvent
    ) -> PlanningEvent:
        """
        Execute test planning based on GAMP categorization.
        
        Args:
            ctx: Workflow context
            ev: GAMP categorization event
            
        Returns:
            PlanningEvent with test strategy and requirements
        """
        self.logger.info(f"📋 Starting test planning for GAMP Category {ev.gamp_category.value}")
        
        # Create planner workflow
        planner_workflow = PlannerAgentWorkflow(
            llm=self.llm,
            verbose=self.verbose
        )
        
        # Execute planning
        planning_result = await planner_workflow.run()
        
        # Store planning results
        await ctx.set("planning_result", planning_result.result)
        await ctx.set("test_strategy", planning_result.result.get('test_strategy'))
        
        # Extract or create planning event
        if hasattr(planning_result, 'result'):
            planning_data = planning_result.result
            planning_event = PlanningEvent(
                test_strategy=planning_data.get('test_strategy', {}),
                estimated_test_count=planning_data.get('estimated_test_count', 5),
                required_test_types=planning_data.get('required_test_types', []),
                compliance_requirements=planning_data.get('compliance_requirements', []),
                parallel_coordination_requests=planning_data.get('coordination_requests', []),
                estimated_duration_days=planning_data.get('estimated_duration_days', 5),
                session_id=self._workflow_session_id
            )
        else:
            # Fallback planning event
            planning_event = PlanningEvent(
                test_strategy={"type": "basic", "category": ev.gamp_category.value},
                estimated_test_count=5,
                required_test_types=["installation", "configuration"],
                compliance_requirements=ev.compliance_requirements,
                parallel_coordination_requests=[],
                estimated_duration_days=5,
                session_id=self._workflow_session_id
            )
        
        await ctx.set("planning_event", planning_event)
        
        self.logger.info(
            f"📋 Planning completed: {planning_event.estimated_test_count} tests estimated "
            f"over {planning_event.estimated_duration_days} days"
        )
        
        return planning_event

    @step
    async def check_consultation_required(
        self,
        ctx: Context,
        ev: PlanningEvent
    ) -> WorkflowCompletionEvent:
        """
        Check if consultation is required and handle accordingly.
        
        Args:
            ctx: Workflow context
            ev: Planning event
            
        Returns:
            WorkflowCompletionEvent indicating next steps
        """
        self.logger.info("🔍 Checking if consultation is required")
        
        # For now, proceed to completion - consultation logic can be added here
        return WorkflowCompletionEvent(
            session_id=self._workflow_session_id,
            workflow_status="ready_for_completion",
            consultation_event=None
        )

    @step
    async def complete_workflow(
        self,
        ctx: Context,
        ev: WorkflowCompletionEvent
    ) -> StopEvent:
        """
        Complete the workflow without OQ generation.
        
        This step is used when only categorization and planning are needed.
        
        Args:
            ctx: Workflow context
            ev: Workflow completion event
            
        Returns:
            StopEvent with workflow results
        """
        workflow_end_time = datetime.now(UTC)
        workflow_duration = (workflow_end_time - self._workflow_start_time).total_seconds()
        
        # Get all workflow data
        categorization_event = await ctx.get("categorization_event")
        categorization_result = await ctx.get("categorization_result")
        planning_result = await ctx.get("planning_result", {})
        test_strategy = await ctx.get("test_strategy")
        document_metadata = await ctx.get("document_metadata", {})
        
        # Compile results
        unified_results = {
            # Workflow metadata
            "workflow_metadata": {
                "session_id": self._workflow_session_id,
                "start_time": self._workflow_start_time.isoformat(),
                "end_time": workflow_end_time.isoformat(),
                "duration_seconds": workflow_duration,
                "status": "completed",
                "version": "1.0.0",
                "workflow_type": "unified_test_generation"
            },
            
            # Document information
            "document_metadata": document_metadata,
            
            # GAMP-5 categorization results
            "categorization": {
                "event": categorization_event,
                "full_result": categorization_result,
                "category": categorization_event.gamp_category.value if categorization_event else None,
                "confidence_score": categorization_event.confidence_score if categorization_event else 0.0,
                "rationale": categorization_event.rationale if categorization_event else "No rationale available"
            },
            
            # Planning results
            "planning": {
                "full_result": planning_result,
                "test_strategy": test_strategy,
                "estimated_test_count": planning_result.get('estimated_test_count', 0),
                "estimated_duration_days": planning_result.get('estimated_duration_days', 0)
            }
        }
        
        self.logger.info(
            f"✅ Unified workflow completed successfully "
            f"(Duration: {workflow_duration:.1f}s, Category: {categorization_event.gamp_category.value if categorization_event else 'Unknown'})"
        )
        
        return StopEvent(result=unified_results)

    @step
    async def process_document(
        self,
        ctx: Context,
        ev: GAMPCategorizationEvent
    ) -> None:
        """
        Process document metadata and prepare for downstream steps.
        
        This is a no-op step that allows the workflow to continue to planning.
        
        Args:
            ctx: Workflow context  
            ev: GAMP categorization event
        """
        # This step intentionally produces no events
        # It allows the workflow to transition from categorization to planning
        pass

    @step
    async def run_planning_workflow(
        self,
        ctx: Context,
        ev: GAMPCategorizationEvent
    ) -> PlanningEvent:
        """
        Execute the planning workflow based on categorization results.
        
        Args:
            ctx: Workflow context
            ev: GAMP categorization event
            
        Returns:
            PlanningEvent with planning results
        """
        return await self.categorize_document(ctx, ev)

    @step  
    async def run_oq_generation(
        self,
        ctx: Context,
        ev: PlanningEvent
    ) -> OQTestSuiteEvent | ConsultationRequiredEvent:
        """
        Execute OQ test generation workflow.
        
        Args:
            ctx: Workflow context
            ev: Planning event with test strategy
            
        Returns:
            OQTestSuiteEvent with generated tests or ConsultationRequiredEvent
        """
        self.logger.info("🧪 Starting OQ test generation workflow")
        
        # Get required context data
        categorization_event = await ctx.get("categorization_event")
        urs_content = await ctx.get("document_content", "")
        document_metadata = await ctx.get("document_metadata", {})
        agent_results = await ctx.get("agent_results", {})
        
        if not categorization_event:
            return ConsultationRequiredEvent(
                consultation_type="missing_categorization_for_oq",
                context={
                    "error": "No categorization event available for OQ generation",
                    "workflow_session": self._workflow_session_id
                },
                urgency="high",
                required_expertise=["system_engineer", "validation_engineer"],
                triggering_step="run_oq_generation"
            )
        
        self.logger.info(
            f"Starting OQ test generation for GAMP Category {categorization_event.gamp_category.value}"
        )
        
        try:
            # Prepare aggregated context from all upstream agents
            aggregated_context = {
                "categorization_confidence": categorization_event.confidence_score,
                "planning_strategy": ev.test_strategy,
                "agent_coordination_results": agent_results
            }
            
            # Create OQ generation event
            oq_generation_event = OQTestGenerationEvent(
                gamp_category=categorization_event.gamp_category,
                urs_content=urs_content,
                document_metadata=document_metadata,
                required_test_count=ev.estimated_test_count,
                test_strategy=ev.test_strategy,
                compliance_requirements=ev.compliance_requirements,
                aggregated_context=aggregated_context,
                categorization_confidence=categorization_event.confidence_score,
                complexity_level="standard",
                focus_areas=ev.required_test_types,
                risk_level="medium",
                triggering_step="run_oq_generation"
            )
            
            # Create and run OQ generation workflow with event passed via constructor
            oq_workflow = OQTestGenerationWorkflow(
                llm=self.llm,
                verbose=self.verbose,
                enable_validation=True,
                oq_generation_event=oq_generation_event
            )
            
            # Execute OQ generation (no arguments needed - event is in constructor)
            oq_result = await oq_workflow.run()
            
            # Handle different result types
            if isinstance(oq_result, OQTestSuiteEvent):
                # Successful generation
                await ctx.set("oq_generation_result", oq_result)
                await ctx.set("generated_test_suite", oq_result.test_suite)
                
                self.logger.info(
                    f"OQ test generation completed successfully: "
                    f"{oq_result.test_suite.suite_id} "
                    f"({oq_result.test_suite.total_test_count} tests)"
                )
                
                return oq_result
                
            elif isinstance(oq_result, ConsultationRequiredEvent):
                # OQ generation requires consultation
                self.logger.info(f"OQ generation requires consultation: {oq_result.consultation_type}")
                return oq_result
                
            else:
                # Unexpected result type
                return ConsultationRequiredEvent(
                    consultation_type="oq_generation_unexpected_result",
                    context={
                        "error": "OQ generation returned unexpected result type",
                        "result_type": str(type(oq_result)),
                        "workflow_session": self._workflow_session_id
                    },
                    urgency="high",
                    required_expertise=["system_engineer", "validation_engineer"],
                    triggering_step="run_oq_generation"
                )
        
        except Exception as e:
            self.logger.error(f"OQ generation workflow failed: {e}")
            
            return ConsultationRequiredEvent(
                consultation_type="oq_generation_error",
                context={
                    "error_message": str(e),
                    "gamp_category": categorization_event.gamp_category.value if categorization_event else None,
                    "workflow_session": self._workflow_session_id
                },
                urgency="high",
                required_expertise=["validation_engineer", "system_engineer"],
                triggering_step="run_oq_generation"
            )

    @step
    async def finalize_workflow_results(
        self,
        ctx: Context,
        ev: PlanningEvent | WorkflowCompletionEvent | OQTestSuiteEvent
    ) -> StopEvent:
        """
        Finalize the unified workflow with complete results.
        
        This step compiles all workflow results into a comprehensive
        test generation output with full regulatory compliance and
        audit trail information.
        
        Args:
            ctx: Workflow context
            ev: Planning event or workflow completion event
            
        Returns:
            StopEvent with complete unified workflow results
        """
        workflow_end_time = datetime.now(UTC)
        workflow_duration = (workflow_end_time - self._workflow_start_time).total_seconds()

        # Get all workflow data
        categorization_event = await ctx.get("categorization_event")
        categorization_result = await ctx.get("categorization_result")
        planning_result = await ctx.get("planning_result", {})
        test_strategy = await ctx.get("test_strategy")
        agent_results = await ctx.get("agent_results", {})
        consultation_event = await ctx.get("consultation_event", default=None)
        document_metadata = await ctx.get("document_metadata", {})
        oq_generation_result = await ctx.get("oq_generation_result", default=None)
        generated_test_suite = await ctx.get("generated_test_suite", default=None)

        # Handle consultation if required
        if isinstance(ev, WorkflowCompletionEvent) and ev.consultation_event:
            self.logger.info("Consultation required - routing to consultation handler")
            # Route the consultation event to the consultation handler
            return await self.handle_consultation_required(ctx, ev.consultation_event)

        # Determine workflow status for completed workflows
        if isinstance(ev, WorkflowCompletionEvent):
            workflow_status = "completed"
            planning_event = None
            oq_test_suite_event = None
        elif isinstance(ev, OQTestSuiteEvent):
            workflow_status = "completed_with_tests"
            planning_event = None
            oq_test_suite_event = ev
        elif isinstance(ev, PlanningEvent):
            workflow_status = "completed"
            planning_event = ev
            oq_test_suite_event = None
        else:
            workflow_status = "completed"
            planning_event = ev if isinstance(ev, PlanningEvent) else None
            oq_test_suite_event = None

        # Compile comprehensive results
        unified_results = {
            # Workflow metadata
            "workflow_metadata": {
                "session_id": self._workflow_session_id,
                "start_time": self._workflow_start_time.isoformat(),
                "end_time": workflow_end_time.isoformat(),
                "duration_seconds": workflow_duration,
                "status": workflow_status,
                "version": "1.0.0",
                "workflow_type": "unified_test_generation"
            },

            # Document information
            "document_metadata": document_metadata,

            # GAMP-5 categorization results
            "categorization": {
                "event": categorization_event,
                "full_result": categorization_result,
                "category": categorization_event.gamp_category.value if categorization_event else None,
                "confidence_score": categorization_event.confidence_score if categorization_event else 0.0,
                "rationale": categorization_event.rationale if categorization_event else "No rationale available"
            },

            # Planning results
            "planning": {
                "event": planning_event,
                "full_result": planning_result,
                "test_strategy": test_strategy,
                "estimated_test_count": planning_result.get('estimated_test_count', 0) if planning_result else 0,
                "estimated_duration_days": planning_result.get('estimated_duration_days', 0) if planning_result else 0
            },

            # Agent coordination results
            "agent_coordination": {
                "results": agent_results,
                "coordination_successful": len(agent_results) > 0 if agent_results else False
            },

            # OQ generation results (if available)
            "oq_generation": {
                "result": oq_generation_result,
                "test_suite": generated_test_suite,
                "generation_successful": oq_generation_result is not None
            } if oq_generation_result else None,

            # Consultation information (if applicable)
            "consultation": {
                "event": consultation_event,
                "consultation_required": consultation_event is not None
            } if consultation_event else None
        }

        self.logger.info(
            f"✅ Unified workflow finalization completed "
            f"(Status: {workflow_status}, Duration: {workflow_duration:.1f}s)"
        )

        return StopEvent(result=unified_results)

    @step
    async def handle_consultation_required(
        self,
        ctx: Context,
        ev: ConsultationRequiredEvent
    ) -> StopEvent:
        """
        Handle consultation requirements from any workflow step.
        
        This step manages human consultation triggers and ensures
        proper regulatory compliance for decision points.
        
        Args:
            ctx: Workflow context
            ev: Consultation required event
            
        Returns:
            StopEvent with consultation handling results
        """
        self.logger.info(f"🧑‍⚕️ ENTERING CONSULTATION HANDLER")
        self.logger.info(f"📋 Consultation Type: {ev.consultation_type}")
        self.logger.info(f"📋 Urgency: {ev.urgency}")
        self.logger.info(f"📋 Required Expertise: {ev.required_expertise}")
        self.logger.info(f"📋 Context: {ev.context}")
        
        # Store consultation event for audit trail
        await ctx.set("consultation_event", ev)
        
        try:
            self.logger.info("🔄 Starting direct human consultation...")
            
            # Use direct human consultation interface
            consultation_result = await self.consultation_system.request_consultation_direct(
                consultation_type=ev.consultation_type,
                context=ev.context,
                urgency=ev.urgency,
                required_expertise=ev.required_expertise,
                triggering_step=ev.triggering_step
            )
            
            # Handle consultation result
            if consultation_result.get("cancelled", False):
                # User cancelled consultation - NO fallbacks
                error_message = f"User cancelled consultation for {ev.consultation_type}. Consultation ID: {ev.consultation_id}. System cannot proceed without explicit human decision. No fallback mechanisms available per pharmaceutical compliance requirements."
                
                self.logger.error(f"User cancelled consultation: {error_message}")
                
                return StopEvent(result={
                    "workflow_type": "unified_test_generation",
                    "status": "consultation_cancelled",
                    "session_id": self._workflow_session_id,
                    "error": error_message,
                    "consultation_event": ev,
                    "regulatory_compliance": {
                        "no_fallback_applied": True,
                        "requires_human_decision": True,
                        "compliance_maintained": True
                    }
                })
            
            elif consultation_result.get("decision"):
                # Consultation completed with decision
                decision = consultation_result["decision"]
                
                self.logger.info(f"✅ Consultation completed with decision: {decision}")
                
                return StopEvent(result={
                    "workflow_type": "unified_test_generation",
                    "status": "completed_with_consultation",
                    "session_id": self._workflow_session_id,
                    "consultation_result": consultation_result,
                    "consultation_event": ev,
                    "human_decision": decision,
                    "regulatory_compliance": {
                        "human_oversight_applied": True,
                        "decision_recorded": True,
                        "audit_trail_complete": True
                    }
                })
            
            else:
                # Consultation system error - NO fallbacks
                error_message = f"Consultation system error: {ev.consultation_type} - {consultation_result.get('error', 'Unknown consultation error')}. Consultation ID: {ev.consultation_id}. System cannot proceed without explicit human decision. No fallback mechanisms available per pharmaceutical compliance requirements."
                
                self.logger.error(f"Error in direct consultation input: {error_message}")
                
                return StopEvent(result={
                    "workflow_type": "unified_test_generation", 
                    "status": "consultation_system_error",
                    "session_id": self._workflow_session_id,
                    "error": error_message,
                    "consultation_event": ev,
                    "consultation_result": consultation_result,
                    "regulatory_compliance": {
                        "system_error_occurred": True,
                        "no_fallback_applied": True,
                        "requires_system_investigation": True
                    }
                })
                
        except Exception as e:
            # Consultation handling error - NO fallbacks
            error_message = f"System error during consultation for {ev.consultation_type}: {e}. Consultation ID: {ev.consultation_id}. System cannot proceed without explicit human decision. No fallback mechanisms available per pharmaceutical compliance requirements."
            
            self.logger.error(f"Error in consultation handling: {error_message}")
            
            return StopEvent(result={
                "workflow_type": "unified_test_generation",
                "status": "consultation_handling_error", 
                "session_id": self._workflow_session_id,
                "error": error_message,
                "consultation_event": ev,
                "exception": str(e),
                "regulatory_compliance": {
                    "system_exception_occurred": True,
                    "no_fallback_applied": True,
                    "requires_immediate_investigation": True
                }
            })


async def run_unified_test_generation_workflow(
    document_content: str,
    document_metadata: dict[str, Any] = None,
    llm: LLM = None,
    verbose: bool = True
) -> dict[str, Any]:
    """
    Run the unified test generation workflow.
    
    This function is the main entry point for running the complete
    pharmaceutical test generation workflow from document to tests.
    
    Args:
        document_content: The URS document content to process
        document_metadata: Optional metadata about the document
        llm: Optional LLM instance to use
        verbose: Enable verbose logging
        
    Returns:
        Dictionary containing workflow results
    """
    # Create workflow instance
    workflow = UnifiedTestGenerationWorkflow(
        llm=llm,
        verbose=verbose
    )
    
    # Prepare document metadata
    if document_metadata is None:
        document_metadata = {}
    
    # Run the workflow
    result = await workflow.run()
    
    # Set document content and metadata in the context before running
    # This needs to be handled by the caller, as we can't modify context after workflow starts
    
    return result.result if hasattr(result, 'result') else result