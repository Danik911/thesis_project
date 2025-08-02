"""
Planner Agent Workflow - LlamaIndex Implementation

This module implements the Test Generation Orchestrator workflow following LlamaIndex
Workflow patterns. It orchestrates test generation planning based on GAMP-5 categorization,
creates planning context, and coordinates parallel agent execution.

Key Features:
- Event-driven workflow orchestration
- GAMP-category-specific planning logic
- Parallel agent coordination with error handling
- Comprehensive audit trail for regulatory compliance
- Human consultation triggers for complex scenarios
- Integration with existing categorization workflow

Workflow Steps:
1. Receive GAMPCategorizationEvent
2. Generate comprehensive test strategy
3. Coordinate parallel agent execution requests
4. Process and synchronize agent results
5. Handle errors with fallback strategies
6. Emit PlanningEvent for downstream workflow
"""

import logging
from datetime import UTC, datetime
from typing import Any

from llama_index.core.llms import LLM
from llama_index.core.workflow import Context, StartEvent, StopEvent, Workflow, step
from llama_index.llms.openai import OpenAI
from src.core.events import (
    AgentRequestEvent,
    AgentResultEvent,
    ConsultationRequiredEvent,
    GAMPCategorizationEvent,
    PlanningEvent,
)

from .agent import create_planner_agent
from .coordination import AgentCoordinationConfig


class PlannerAgentWorkflow(Workflow):
    """
    Orchestrates test generation planning based on GAMP-5 categorization.
    
    This workflow processes GAMP categorization results to create comprehensive
    test strategies and coordinate parallel agent execution for pharmaceutical
    test generation. It maintains regulatory compliance and provides complete
    audit trails.
    
    Workflow steps:
    1. Start planning from GAMP categorization
    2. Generate test strategy based on category and risk assessment
    3. Coordinate parallel agent execution (Context Provider, SME, Research)
    4. Collect and process agent results with error handling
    5. Create final planning event for downstream workflow
    """

    def __init__(
        self,
        timeout: int = 600,  # 10 minutes for complex planning
        verbose: bool = False,
        enable_coordination: bool = True,
        enable_risk_assessment: bool = True,
        enable_llm_enhancement: bool = True,
        coordination_config: AgentCoordinationConfig | None = None,
        llm: LLM | None = None
    ):
        """
        Initialize the planner workflow.
        
        Args:
            timeout: Maximum time to wait for workflow completion
            verbose: Enable verbose logging
            enable_coordination: Enable parallel agent coordination
            enable_risk_assessment: Enable risk-based planning
            enable_llm_enhancement: Enable LLM-powered strategy enhancement
            coordination_config: Configuration for agent coordination
            llm: Language model for planning intelligence
        """
        super().__init__(timeout=timeout, verbose=verbose)
        self.enable_coordination = enable_coordination
        self.enable_risk_assessment = enable_risk_assessment
        self.enable_llm_enhancement = enable_llm_enhancement
        self.verbose = verbose
        self.logger = logging.getLogger(__name__)

        # Initialize LLM
        self.llm = llm or OpenAI(model="gpt-4o-mini")

        # Initialize planner agent
        self.planner_agent = create_planner_agent(
            llm=self.llm,
            enable_coordination=enable_coordination,
            enable_risk_assessment=enable_risk_assessment,
            coordination_config=coordination_config or AgentCoordinationConfig(),
            verbose=verbose
        )

        # Workflow state tracking
        self._workflow_session_id = None
        self._coordination_requests = []
        self._expected_agent_results = 0

    @step
    async def initialize_from_start_event(
        self,
        ctx: Context,
        ev: StartEvent
    ) -> GAMPCategorizationEvent:
        """
        Initialize planning workflow from StartEvent.
        
        This step handles the workflow.run() call and extracts the 
        categorization_event parameter to begin planning.
        
        Args:
            ctx: Workflow context
            ev: StartEvent containing workflow parameters
            
        Returns:
            GAMPCategorizationEvent to start planning process
        """
        # Extract categorization event from StartEvent parameters
        categorization_event = ev.get("categorization_event")

        if not categorization_event:
            raise ValueError(
                "PlannerAgentWorkflow requires 'categorization_event' parameter. "
                "Call workflow.run(categorization_event=your_event)"
            )

        if not isinstance(categorization_event, GAMPCategorizationEvent):
            raise TypeError(
                f"Expected GAMPCategorizationEvent, got {type(categorization_event)}. "
                "Ensure the categorization_event parameter is a valid GAMPCategorizationEvent instance."
            )

        self.logger.info(
            f"Initialized planner workflow with GAMP Category {categorization_event.gamp_category.value}"
        )

        return categorization_event

    @step
    async def start_planning(
        self,
        ctx: Context,
        ev: GAMPCategorizationEvent
    ) -> PlanningEvent:
        """
        Start planning process from GAMP categorization.
        
        This step receives the GAMP categorization results and initiates
        the test strategy generation process.
        
        Args:
            ctx: Workflow context
            ev: GAMP categorization event
            
        Returns:
            PlanningEvent with initial strategy
        """
        # Initialize workflow session
        self._workflow_session_id = f"planning_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"

        # Store categorization event in context
        await ctx.set("categorization_event", ev)
        await ctx.set("workflow_start_time", datetime.now(UTC))
        await ctx.set("session_id", self._workflow_session_id)

        # Log planning start
        self.logger.info(
            f"Starting test generation planning for GAMP Category {ev.gamp_category.value} "
            f"(confidence: {ev.confidence_score:.2%})"
        )

        # Extract URS context if available
        urs_context = await ctx.get("urs_context", None)
        constraints = await ctx.get("planning_constraints", None)

        # Generate test strategy
        test_strategy = self.planner_agent.generate_test_strategy(
            categorization_event=ev,
            urs_context=urs_context,
            constraints=constraints
        )

        # Store strategy in context
        await ctx.set("test_strategy", test_strategy)

        # Create planning event
        planning_event = self.planner_agent.create_planning_event(
            test_strategy=test_strategy,
            gamp_category=ev.gamp_category
        )

        # Store planning event
        await ctx.set("planning_event", planning_event)

        self.logger.info(
            f"Generated test strategy: {test_strategy.estimated_count} tests, "
            f"{test_strategy.timeline_estimate_days} days, "
            f"{test_strategy.validation_rigor} rigor"
        )

        return planning_event

    @step
    async def coordinate_parallel_agents(
        self,
        ctx: Context,
        ev: PlanningEvent
    ) -> list[AgentRequestEvent] | ConsultationRequiredEvent | StopEvent:
        """
        Coordinate parallel agent execution based on planning context.
        
        This step creates and dispatches requests for parallel agent execution
        including Context Provider, SME, and Research agents.
        
        Args:
            ctx: Workflow context
            ev: Planning event with strategy
            
        Returns:
            List of agent request events or consultation event if coordination disabled
        """
        if not self.enable_coordination:
            self.logger.info("Agent coordination disabled, skipping parallel execution")
            return ConsultationRequiredEvent(
                consultation_type="coordination_disabled",
                context={"reason": "coordination_disabled_in_workflow"},
                urgency="low",
                required_expertise=["manual_planning"],
                triggering_step="planner_coordination"
            )

        # Get context data
        categorization_event = await ctx.get("categorization_event")
        test_strategy = await ctx.get("test_strategy")
        urs_context = await ctx.get("urs_context", None)

        # Generate coordination requests
        try:
            coordination_requests = self.planner_agent.coordinate_parallel_agents(
                test_strategy=test_strategy,
                gamp_category=categorization_event.gamp_category,
                urs_context=urs_context,
                categorization_context={
                    "confidence_score": categorization_event.confidence_score,
                    "justification": categorization_event.justification,
                    "risk_assessment": categorization_event.risk_assessment
                }
            )

            # Store coordination data
            self._coordination_requests = coordination_requests
            self._expected_agent_results = len(coordination_requests)

            await ctx.set("coordination_requests", coordination_requests)
            await ctx.set("expected_agent_count", len(coordination_requests))

            # Check if no agents need coordination - complete immediately
            if len(coordination_requests) == 0:
                self.logger.info("No parallel agents required - completing planning immediately")
                return await self._finalize_planning(ctx, [])

            # Log coordination
            agent_types = [req.agent_type for req in coordination_requests]
            self.logger.info(
                f"Coordinating {len(coordination_requests)} agents: {', '.join(set(agent_types))}"
            )

            return coordination_requests

        except Exception as e:
            self.logger.error(f"Agent coordination failed: {e}")

            # Create error recovery event
            return ConsultationRequiredEvent(
                consultation_type="coordination_error",
                context={
                    "error_message": str(e),
                    "gamp_category": categorization_event.gamp_category.value,
                    "strategy_summary": {
                        "test_count": test_strategy.estimated_count,
                        "rigor": test_strategy.validation_rigor
                    }
                },
                urgency="high",
                required_expertise=["system_engineer", "planning_specialist"],
                triggering_step="planner_coordination"
            )

    @step(num_workers=3)  # Allow parallel processing of agent results
    async def collect_agent_results(
        self,
        ctx: Context,
        ev: AgentResultEvent
    ) -> StopEvent | None:
        """
        Collect and synchronize parallel agent results.
        
        This step waits for all agent responses and processes them for
        completeness and quality before proceeding.
        
        Args:
            ctx: Workflow context
            ev: Agent result event
            
        Returns:
            StopEvent when all results collected, None while waiting
        """
        # Get expected count
        expected_count = await ctx.get("expected_agent_count", 0)

        if expected_count == 0:
            # No agents were coordinated, skip collection
            return await self._finalize_planning(ctx, [])

        # Collect events until we have all expected results
        ready = ctx.collect_events(ev, [AgentResultEvent] * expected_count)
        if ready is None:
            return None  # Still waiting for more results

        self.logger.info(f"Collected {len(ready)} agent results")

        # Process agent results
        try:
            expected_correlations = [str(req.correlation_id) for req in self._coordination_requests]
            coordination_result = self.planner_agent.process_agent_results(
                results=ready,
                expected_correlations=expected_correlations
            )

            # Store coordination results
            await ctx.set("coordination_result", coordination_result)

            # Handle coordination errors if needed
            error_response = self.planner_agent.handle_coordination_errors(coordination_result)
            if error_response:
                if isinstance(error_response, list):
                    # Retry requests - would need additional workflow steps
                    self.logger.warning("Agent failures detected, but retries not implemented in this workflow")
                else:
                    # Consultation required
                    await ctx.set("consultation_required", error_response)

            return await self._finalize_planning(ctx, ready)

        except Exception as e:
            self.logger.error(f"Error processing agent results: {e}")

            # Continue with partial results
            return await self._finalize_planning(ctx, ready)

    @step
    async def handle_consultation_required(
        self,
        ctx: Context,
        ev: ConsultationRequiredEvent
    ) -> StopEvent:
        """
        Handle cases where human consultation is required.
        
        This step processes consultation events and creates appropriate
        final planning results with consultation flags.
        
        Args:
            ctx: Workflow context
            ev: Consultation required event
            
        Returns:
            StopEvent with consultation information
        """
        self.logger.info(f"Human consultation required: {ev.consultation_type}")

        # Store consultation event
        await ctx.set("consultation_required", ev)

        # Get existing planning data
        planning_event = await ctx.get("planning_event")
        test_strategy = await ctx.get("test_strategy")
        workflow_start = await ctx.get("workflow_start_time")

        # Calculate workflow duration
        duration = (datetime.now(UTC) - workflow_start).total_seconds()

        # Create final result with consultation flag
        result = {
            "planning_event": planning_event,
            "consultation_event": ev,
            "test_strategy": test_strategy,
            "coordination_summary": {
                "consultation_required": True,
                "consultation_type": ev.consultation_type,
                "consultation_urgency": ev.urgency,
                "required_expertise": ev.required_expertise
            },
            "workflow_summary": {
                "session_id": self._workflow_session_id,
                "duration_seconds": duration,
                "status": "consultation_required",
                "completion_timestamp": datetime.now(UTC).isoformat()
            }
        }

        return StopEvent(result=result)

    async def _finalize_planning(
        self,
        ctx: Context,
        agent_results: list[AgentResultEvent]
    ) -> StopEvent:
        """
        Finalize planning workflow with all collected results.
        
        Args:
            ctx: Workflow context
            agent_results: Collected agent results
            
        Returns:
            StopEvent with complete planning results
        """
        # Get all workflow data
        planning_event = await ctx.get("planning_event")
        test_strategy = await ctx.get("test_strategy")
        categorization_event = await ctx.get("categorization_event")
        coordination_result = await ctx.get("coordination_result", None)
        consultation_event = await ctx.get("consultation_required", None)
        workflow_start = await ctx.get("workflow_start_time")

        # Calculate workflow duration
        duration = (datetime.now(UTC) - workflow_start).total_seconds()

        # Merge agent results into planning context
        merged_agent_data = self._merge_agent_results(agent_results)

        # Update planning event with agent results
        if merged_agent_data and planning_event:
            # Enhance planning event with agent insights
            planning_event.test_strategy["agent_insights"] = merged_agent_data

        # Create comprehensive result
        result = {
            "planning_event": planning_event,
            "test_strategy": test_strategy,
            "categorization_event": categorization_event,
            "agent_results": {
                "successful_count": len([r for r in agent_results if r.success]),
                "failed_count": len([r for r in agent_results if not r.success]),
                "total_count": len(agent_results),
                "merged_data": merged_agent_data
            },
            "coordination_summary": coordination_result.coordination_summary if coordination_result else {},
            "consultation_event": consultation_event,
            "workflow_summary": {
                "session_id": self._workflow_session_id,
                "duration_seconds": duration,
                "status": "completed",
                "completion_timestamp": datetime.now(UTC).isoformat(),
                "gamp_category": categorization_event.gamp_category.value,
                "test_count": test_strategy.estimated_count,
                "timeline_days": test_strategy.timeline_estimate_days
            }
        }

        # Log completion
        status = "with consultation required" if consultation_event else "successfully"
        self.logger.info(
            f"Planning workflow completed {status} in {duration:.2f}s - "
            f"Category {categorization_event.gamp_category.value}, "
            f"{test_strategy.estimated_count} tests, "
            f"{len(agent_results)} agent results"
        )

        return StopEvent(result=result)

    def _merge_agent_results(self, agent_results: list[AgentResultEvent]) -> dict[str, Any]:
        """
        Merge agent results into consolidated insights.
        
        Args:
            agent_results: List of agent result events
            
        Returns:
            Merged agent insights
        """
        merged = {
            "context_provider": {},
            "sme_agents": [],
            "research_agent": {},
            "summary": {
                "total_agents": len(agent_results),
                "successful_agents": len([r for r in agent_results if r.success]),
                "insights_quality": "high" if len(agent_results) > 2 else "limited"
            }
        }

        for result in agent_results:
            if not result.success:
                continue

            if result.agent_type == "context_provider":
                merged["context_provider"] = {
                    "retrieved_documents": result.result_data.get("retrieved_documents", []),
                    "context_quality": result.result_data.get("context_quality", "unknown"),
                    "search_coverage": result.result_data.get("search_coverage", 0.0)
                }

            elif result.agent_type == "sme_agent":
                merged["sme_agents"].append({
                    "specialty": result.result_data.get("specialty", "unknown"),
                    "recommendations": result.result_data.get("recommendations", []),
                    "confidence": result.result_data.get("confidence_score", 0.0),
                    "validation_focus": result.result_data.get("validation_focus", [])
                })

            elif result.agent_type == "research_agent":
                merged["research_agent"] = {
                    "research_findings": result.result_data.get("research_findings", []),
                    "regulatory_updates": result.result_data.get("regulatory_updates", []),
                    "compliance_guidance": result.result_data.get("compliance_guidance", []),
                    "research_quality": result.result_data.get("research_quality", "unknown")
                }

        return merged


# Convenience function for running the workflow
async def run_planner_workflow(
    categorization_event: GAMPCategorizationEvent,
    urs_context: dict[str, Any] | None = None,
    planning_constraints: dict[str, Any] | None = None,
    **kwargs
) -> dict[str, Any]:
    """
    Run the planner agent workflow.
    
    Args:
        categorization_event: GAMP categorization results
        urs_context: Optional URS analysis context
        planning_constraints: Optional planning constraints
        **kwargs: Additional workflow configuration
        
    Returns:
        Dictionary with complete planning results
    """
    # Create workflow instance
    workflow = PlannerAgentWorkflow(**kwargs)

    # Prepare initial context
    initial_context = {}
    if urs_context:
        initial_context["urs_context"] = urs_context
    if planning_constraints:
        initial_context["planning_constraints"] = planning_constraints

    # Run workflow
    result = await workflow.run(categorization_event, **initial_context)

    return result
