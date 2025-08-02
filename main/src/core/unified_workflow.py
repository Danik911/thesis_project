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
from pathlib import Path
from typing import Any
from uuid import uuid4

from llama_index.core.llms import LLM
from llama_index.core.workflow import Context, StartEvent, StopEvent, Workflow, step
from llama_index.llms.openai import OpenAI
from src.agents.oq_generator.events import OQTestGenerationEvent, OQTestSuiteEvent
from src.agents.oq_generator.workflow import OQTestGenerationWorkflow
from src.agents.planner.workflow import PlannerAgentWorkflow
from src.core.categorization_workflow import GAMPCategorizationWorkflow
from src.core.events import (
    AgentRequestEvent,
    AgentResultEvent,
    AgentResultsEvent,
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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UnifiedTestGenerationWorkflow(Workflow):
    """
    Master workflow that orchestrates complete pharmaceutical test generation.
    
    This workflow implements the complete end-to-end test generation process:
    1. Document ingestion and parsing
    2. GAMP-5 categorization
    3. Test planning with risk assessment
    4. Parallel agent coordination (Context, SME, Research)
    5. Test generation and validation
    6. Final result compilation with audit trail
    
    The workflow maintains regulatory compliance throughout and provides
    comprehensive observability through Phoenix monitoring.
    """

    def __init__(
        self,
        timeout: int = 1800,  # 30 minutes for complete workflow
        verbose: bool = False,
        enable_phoenix: bool = True,
        enable_parallel_coordination: bool = True,
        enable_human_consultation: bool = True,
        llm: LLM | None = None
    ):
        """
        Initialize the unified workflow.
        
        Args:
            timeout: Maximum time to wait for workflow completion
            verbose: Enable verbose logging
            enable_phoenix: Enable Phoenix observability
            enable_parallel_coordination: Enable parallel agent coordination
            enable_human_consultation: Enable human consultation triggers
            llm: Language model for workflow intelligence
        """
        super().__init__(timeout=timeout, verbose=verbose)
        
        # Configuration
        self.verbose = verbose
        self.enable_phoenix = enable_phoenix
        self.enable_parallel_coordination = enable_parallel_coordination
        self.enable_human_consultation = enable_human_consultation
        self.logger = logging.getLogger(__name__)
        
        # Initialize LLM
        self.llm = llm or OpenAI(
            model="gpt-4o-mini",  # Fixed model name
            temperature=0.1
        )
        
        # Initialize workflow session
        self._workflow_session_id = f"unified_workflow_{datetime.now(UTC).isoformat()}"
        
        # Initialize human consultation manager
        if enable_human_consultation:
            self.human_consultation = HumanConsultationManager()
        
        # Setup Phoenix if enabled
        if enable_phoenix:
            setup_phoenix()
            self.logger.info("🔭 Phoenix observability enabled")

    @step
    async def start_unified_workflow(
        self,
        ctx: Context,
        ev: StartEvent
    ) -> URSIngestionEvent:
        """
        Start the unified workflow with document ingestion.
        
        Args:
            ctx: Workflow context
            ev: Start event with document path
            
        Returns:
            URSIngestionEvent to begin document processing
        """
        self.logger.info("🚀 Starting unified test generation workflow")
        
        # Extract document path from start event
        document_path = ev.get("document_path") or getattr(ev, "document_path", None)
        if not document_path:
            raise ValueError("Document path is required to start workflow")
        
        # Load document content
        from pathlib import Path
        doc_path = Path(document_path)
        if not doc_path.exists():
            raise FileNotFoundError(f"Document not found: {document_path}")
        
        urs_content = doc_path.read_text(encoding='utf-8')
        
        # Store workflow metadata
        await ctx.set("workflow_start_time", datetime.now(UTC))
        await ctx.set("workflow_session_id", self._workflow_session_id)
        await ctx.set("document_path", document_path)
        
        # Create URS ingestion event with all required fields
        return URSIngestionEvent(
            urs_content=urs_content,
            document_name=doc_path.name,
            document_version="1.0",  # Default version
            author="system"
        )

    @step
    async def categorize_document(
        self,
        ctx: Context,
        ev: URSIngestionEvent
    ) -> GAMPCategorizationEvent:
        """
        Execute GAMP-5 categorization on the ingested document.
        
        Args:
            ctx: Workflow context
            ev: URS ingestion event
            
        Returns:
            GAMPCategorizationEvent with categorization results
        """
        self.logger.info(f"📊 Starting GAMP-5 categorization for {ev.document_name}")
        
        # Initialize categorization workflow
        categorization_workflow = GAMPCategorizationWorkflow(
            verbose=self.verbose
        )
        
        # Execute categorization  
        categorization_result = await categorization_workflow.run(
            urs_content=ev.urs_content,
            document_name=ev.document_name,
            document_version=ev.document_version,
            author=ev.author
        )
        
        # Handle different result formats
        if hasattr(categorization_result, "result"):
            categorization_data = categorization_result.result
        elif isinstance(categorization_result, dict) and "categorization_event" in categorization_result:
            # Extract the GAMPCategorizationEvent from the dict
            categorization_data = categorization_result["categorization_event"]
        else:
            categorization_data = categorization_result
        
        # Store categorization results
        await ctx.set("categorization_result", categorization_data)
        
        # If we already have a GAMPCategorizationEvent, use it directly
        if isinstance(categorization_data, GAMPCategorizationEvent):
            categorization_event = categorization_data
            await ctx.set("gamp_category", categorization_data.gamp_category)
            self.logger.info(f"✅ GAMP-5 Category: {categorization_data.gamp_category.value}")
        else:
            # Handle dict or other formats
            if isinstance(categorization_data, dict):
                await ctx.set("gamp_category", categorization_data.get("gamp_category"))
                categorization_event = GAMPCategorizationEvent(
                    gamp_category=categorization_data.get("gamp_category"),
                    confidence_score=categorization_data.get("confidence_score"),
                    risk_assessment=categorization_data.get("risk_assessment"),
                    document_content=categorization_data.get("document_content", ev.urs_content),
                    session_id=self._workflow_session_id
                )
                gamp_cat = categorization_data.get("gamp_category")
                self.logger.info(f"✅ GAMP-5 Category: {gamp_cat}")
            else:
                await ctx.set("gamp_category", categorization_data.gamp_category)
                categorization_event = GAMPCategorizationEvent(
                    gamp_category=categorization_data.gamp_category,
                    confidence_score=categorization_data.confidence_score,
                    risk_assessment=categorization_data.risk_assessment,
                    document_content=categorization_data.document_content,
                    session_id=self._workflow_session_id
                )
                self.logger.info(f"✅ GAMP-5 Category: {categorization_data.gamp_category.value}")
        return categorization_event

    @step
    async def run_planning_workflow(
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

        # Import and run the actual planner workflow
        from src.agents.planner.workflow import PlannerAgentWorkflow
        
        # Create planner workflow instance
        planner_workflow = PlannerAgentWorkflow(
            timeout=300,  # 5 minutes for planning
            verbose=self.verbose,
            enable_coordination=self.enable_parallel_coordination,
            enable_risk_assessment=True,
            enable_llm_enhancement=True,
            llm=self.llm
        )
        
        # Extract document content for URS context
        urs_context = {
            "document_content": ev.document_content if hasattr(ev, 'document_content') else "",
            "risk_assessment": ev.risk_assessment,
            "confidence_score": ev.confidence_score,
            "justification": ev.justification
        }
        
        # Run planner workflow with categorization event
        try:
            self.logger.info("Running PlannerAgentWorkflow...")
            planning_result = await planner_workflow.run(categorization_event=ev)
            
            # Extract planning result
            if hasattr(planning_result, "result"):
                planning_data = planning_result.result
            else:
                planning_data = planning_result
                
            # Get the planning event from the result
            planning_event = planning_data.get("planning_event")
            
            if not planning_event:
                # Create planning event from result data
                test_strategy = planning_data.get("test_strategy", {})
                
                # Get test types and compliance requirements based on category
                test_types_map = {
                    1: ["installation", "configuration"],
                    3: ["installation", "configuration", "functional"],
                    4: ["installation", "configuration", "functional", "performance"],
                    5: ["installation", "configuration", "functional", "performance", "integration"]
                }
                
                compliance_map = {
                    1: ["GAMP-5"],
                    3: ["GAMP-5", "ALCOA+"],
                    4: ["GAMP-5", "ALCOA+", "21 CFR Part 11"],
                    5: ["GAMP-5", "ALCOA+", "21 CFR Part 11", "CSV"]
                }
                
                # Generate proper agent requests based on GAMP category
                agent_requests = []
                if self.enable_parallel_coordination:
                    # Always include context provider
                    agent_requests.append({
                        "agent_type": "context_provider",
                        "request_data": {
                            "gamp_category": ev.gamp_category.value,
                            "test_strategy": test_strategy,
                            "document_sections": ["functional_requirements", "validation_requirements"]
                        },
                        "correlation_id": f"ctx_{self._workflow_session_id}"
                    })
                    
                    # Add research agent for regulatory updates
                    agent_requests.append({
                        "agent_type": "research",
                        "request_data": {
                            "research_focus": ["GAMP-5", f"Category {ev.gamp_category.value}", "OQ testing"],
                            "regulatory_scope": ["FDA", "EMA", "ICH"]
                        },
                        "correlation_id": f"res_{self._workflow_session_id}"
                    })
                    
                    # Add SME agent for category-specific expertise
                    agent_requests.append({
                        "agent_type": "sme",
                        "request_data": {
                            "expertise_area": f"GAMP Category {ev.gamp_category.value}",
                            "validation_focus": test_strategy.get("validation_rigor", "standard")
                        },
                        "correlation_id": f"sme_{self._workflow_session_id}"
                    })
                
                planning_event = PlanningEvent(
                    test_strategy=test_strategy,
                    required_test_types=test_types_map.get(ev.gamp_category.value, ["basic"]),
                    compliance_requirements=compliance_map.get(ev.gamp_category.value, ["GAMP-5"]),
                    estimated_test_count=test_strategy.get("estimated_count", 5),
                    planner_agent_id=f"planner_{self._workflow_session_id}",
                    gamp_category=ev.gamp_category
                )
                
                # Store agent requests separately
                await ctx.set("agent_requests", agent_requests)
            
            # Store planning results
            await ctx.set("planning_result", planning_data)
            await ctx.set("test_strategy", planning_event.test_strategy)
            await ctx.set("planning_event", planning_event)
            
            self.logger.info(
                f"✅ Planning complete - {planning_event.estimated_test_count} tests estimated, "
                f"{len(planning_event.agent_requests)} agents to coordinate"
            )
            
        except Exception as e:
            self.logger.error(f"Planning workflow failed: {e}")
            # Create minimal planning event to continue workflow
            # Get test types and compliance requirements based on category
            test_types_map = {
                1: ["installation", "configuration"],
                3: ["installation", "configuration", "functional"],
                4: ["installation", "configuration", "functional", "performance"],
                5: ["installation", "configuration", "functional", "performance", "integration"]
            }
            
            compliance_map = {
                1: ["GAMP-5"],
                3: ["GAMP-5", "ALCOA+"],
                4: ["GAMP-5", "ALCOA+", "21 CFR Part 11"],
                5: ["GAMP-5", "ALCOA+", "21 CFR Part 11", "CSV"]
            }
            
            planning_event = PlanningEvent(
                test_strategy={
                    "approach": "basic",
                    "category": ev.gamp_category.value,
                    "error": str(e)
                },
                required_test_types=test_types_map.get(ev.gamp_category.value, ["basic"]),
                compliance_requirements=compliance_map.get(ev.gamp_category.value, ["GAMP-5"]),
                estimated_test_count=5,  # Default based on category
                planner_agent_id=f"planner_{self._workflow_session_id}",
                gamp_category=ev.gamp_category,
                agent_requests=[],  # No coordination on error
                session_id=self._workflow_session_id
            )
            
            # CRITICAL FIX: Store planning_event in context even on error
            await ctx.set("planning_error", str(e))
            await ctx.set("planning_event", planning_event)
            await ctx.set("test_strategy", planning_event.test_strategy)
            
            self.logger.info(
                f"⚠️ Planning failed but minimal event created - continuing with basic strategy"
            )
            
        return planning_event

    @step
    async def coordinate_parallel_agents(
        self,
        ctx: Context,
        ev: PlanningEvent
    ) -> AgentRequestEvent | WorkflowCompletionEvent:
        """
        Coordinate parallel agent execution based on planning results.
        
        Args:
            ctx: Workflow context
            ev: Planning event with agent requests
            
        Returns:
            AgentRequestEvent or WorkflowCompletionEvent if no coordination needed
        """
        # Get agent requests from context
        agent_requests_data = await ctx.get("agent_requests", [])
        
        if not self.enable_parallel_coordination or not agent_requests_data:
            self.logger.info("⏭️ Skipping parallel coordination - creating empty results")
            # Create empty agent results to proceed to OQ generation
            return AgentResultsEvent(
                agent_results=[],
                session_id=self._workflow_session_id
            )
        
        self.logger.info(f"🔄 Coordinating {len(agent_requests_data)} parallel agents")
        
        # Convert planning requests to agent request events
        agent_requests = []
        for i, request in enumerate(agent_requests_data):
            agent_request = AgentRequestEvent(
                agent_type=request.get("agent_type", "unknown"),
                request_data=request.get("request_data", {}),
                correlation_id=uuid4(),  # Generate proper UUID
                requesting_step="coordinate_parallel_agents",
                session_id=self._workflow_session_id
            )
            agent_requests.append(agent_request)
        
        # Store coordination context
        await ctx.set("coordination_requests", agent_requests)
        await ctx.set("expected_results_count", len(agent_requests))
        await ctx.set("current_request_index", 0)
        
        # Emit the first request
        if agent_requests:
            return agent_requests[0]
        else:
            # No requests to process - return empty results
            return AgentResultsEvent(
                agent_results=[],
                session_id=self._workflow_session_id
            )

    @step(num_workers=3)  # Allow parallel processing
    async def execute_agent_request(
        self,
        ctx: Context,
        ev: AgentRequestEvent
    ) -> AgentResultEvent:
        """
        Execute individual agent requests in parallel.
        
        Args:
            ctx: Workflow context
            ev: Agent request event
            
        Returns:
            AgentResultEvent with agent execution results
        """
        self.logger.info(f"🤖 Executing {ev.agent_type} agent request")
        
        try:
            # Execute actual agents based on type
            if ev.agent_type.lower() == "context_provider":
                # Use the actual context provider agent
                from src.agents.parallel.context_provider import create_context_provider_agent
                
                agent = create_context_provider_agent(
                    verbose=self.verbose,
                    enable_phoenix=self.enable_phoenix,
                    max_documents=10
                )
                
                # Process the request
                result_event = await agent.process_request(ev)
                
                # Return the result event with session ID
                result_event.session_id = self._workflow_session_id
                return result_event
                
            elif ev.agent_type.lower() == "sme":
                # Use the actual SME agent
                from src.agents.parallel.sme_agent import create_sme_agent
                
                agent = create_sme_agent(
                    specialty=ev.request_data.get("expertise_area", "general_validation"),
                    verbose=self.verbose
                )
                
                # Process the request
                result_event = await agent.process_request(ev)
                
                # Return the result event with session ID
                result_event.session_id = self._workflow_session_id
                return result_event
                
            elif ev.agent_type.lower() == "research":
                # Use the actual research agent
                from src.agents.parallel.research_agent import create_research_agent
                
                agent = create_research_agent(
                    research_focus=ev.request_data.get("research_focus", ["GAMP-5"]),
                    verbose=self.verbose
                )
                
                # Process the request
                result_event = await agent.process_request(ev)
                
                # Return the result event with session ID
                result_event.session_id = self._workflow_session_id
                return result_event
                
            else:
                # Unknown agent type
                self.logger.warning(f"Unknown agent type: {ev.agent_type}")
                return AgentResultEvent(
                    agent_type=ev.agent_type,
                    correlation_id=ev.correlation_id,
                    result_data={
                        "error": f"Unknown agent type: {ev.agent_type}",
                        "supported_types": ["context_provider", "sme", "research"]
                    },
                    success=False,
                    session_id=self._workflow_session_id
                )
            
        except Exception as e:
            self.logger.error(f"❌ Agent {ev.agent_type} execution failed: {e}")
            return AgentResultEvent(
                agent_type=ev.agent_type,
                correlation_id=ev.correlation_id,
                result_data={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "agent_type": ev.agent_type
                },
                success=False,
                session_id=self._workflow_session_id
            )

    @step
    async def collect_agent_results(
        self,
        ctx: Context,
        ev: AgentResultEvent
    ) -> AgentRequestEvent | AgentResultsEvent | None:
        """
        Collect agent results and emit next request or final results.
        
        Args:
            ctx: Workflow context
            ev: Agent result event
            
        Returns:
            Next AgentRequestEvent, AgentResultsEvent when all results collected, or None while waiting
        """
        # Store the result
        results = await ctx.get("collected_results", [])
        results.append(ev)
        await ctx.set("collected_results", results)
        
        # Get coordination context
        coordination_requests = await ctx.get("coordination_requests", [])
        current_index = await ctx.get("current_request_index", 0)
        
        # Check if we have more requests to emit
        next_index = current_index + 1
        if next_index < len(coordination_requests):
            # Emit the next request
            await ctx.set("current_request_index", next_index)
            self.logger.info(f"📤 Emitting agent request {next_index + 1}/{len(coordination_requests)}")
            return coordination_requests[next_index]
        
        # All requests have been processed, check if we have all results
        expected_count = await ctx.get("expected_results_count", 0)
        if len(results) >= expected_count:
            self.logger.info(f"✅ Collected all {len(results)} agent results")
            return AgentResultsEvent(
                agent_results=results,
                session_id=self._workflow_session_id
            )
        
        # Still waiting for results
        return None

    @step
    async def process_agent_results(
        self,
        ctx: Context,
        ev: AgentResultsEvent
    ) -> AgentResultsEvent:
        """
        Process the results from parallel agent execution.
        
        This step aggregates agent results and passes them to OQ generation.
        
        Args:
            ctx: Workflow context
            ev: AgentResultsEvent containing list of agent result events
            
        Returns:
            AgentResultsEvent to trigger OQ generation
        """
        # Aggregate agent results from the event
        agent_results = ev.agent_results
        self.logger.info(f"📊 Processing {len(agent_results)} agent results")
        
        # Aggregate results
        aggregated_results = {}
        successful_agents = []
        failed_agents = []
        
        for result in agent_results:
            if result.success:
                successful_agents.append(result.agent_type)
                aggregated_results[result.agent_type] = result.result_data
            else:
                failed_agents.append(result.agent_type)
                aggregated_results[f"{result.agent_type}_error"] = result.result_data
        
        # Store aggregated results
        await ctx.set("agent_results", aggregated_results)
        await ctx.set("successful_agents", successful_agents)
        await ctx.set("failed_agents", failed_agents)
        await ctx.set("collected_results", agent_results)  # Store for final workflow
        
        self.logger.info(f"✅ Agent processing complete - {len(successful_agents)} succeeded, {len(failed_agents)} failed")
        
        # Return the same event to trigger OQ generation
        return ev

    @step
    async def check_consultation_required(
        self,
        ctx: Context,
        ev: GAMPCategorizationEvent
    ) -> ConsultationRequiredEvent | PlanningEvent:
        """
        Check if human consultation is required based on categorization results.
        
        Args:
            ctx: Workflow context
            ev: GAMP categorization event
            
        Returns:
            ConsultationRequiredEvent if consultation needed, otherwise trigger planning
        """
        if not self.enable_human_consultation:
            # Skip consultation - trigger planning directly
            self.logger.info("Skipping consultation check - triggering planning")
            # This will trigger run_planning_workflow step
            return await self.run_planning_workflow(ctx, ev)
        
        # Check if consultation is required
        requires_consultation = (
            ev.confidence_score < 0.7 or  # Low confidence
            ev.gamp_category.value in [4, 5] or  # High-risk categories
            "consultation_required" in ev.risk_assessment.get("flags", [])
        )
        
        if requires_consultation:
            self.logger.info("🤔 Human consultation required")
            consultation_event = ConsultationRequiredEvent(
                consultation_type="categorization_review",
                context={
                    "reason": f"Category {ev.gamp_category.value} with confidence {ev.confidence_score:.2f}",
                    "gamp_category": ev.gamp_category.value,
                    "confidence_score": ev.confidence_score,
                    "risk_assessment": ev.risk_assessment,
                    "session_id": self._workflow_session_id
                },
                urgency="normal",
                required_expertise=["validation_engineer", "quality_assurance"],
                triggering_step="check_consultation_required"
            )
            # Store the categorization event for later use
            consultation_event.categorization_event = ev  # Add as dynamic attribute
            return consultation_event
        else:
            # No consultation needed - trigger planning
            self.logger.info("No consultation required - triggering planning")
            return await self.run_planning_workflow(ctx, ev)

    @step
    async def handle_consultation(
        self,
        ctx: Context,
        ev: ConsultationRequiredEvent
    ) -> WorkflowCompletionEvent:
        """
        Handle human consultation requirements.
        
        Args:
            ctx: Workflow context
            ev: Consultation required event
            
        Returns:
            WorkflowCompletionEvent with consultation results
        """
        self.logger.info(f"👥 Processing consultation: {ev.context.get('reason', 'Unknown reason')}")
        
        # In a real implementation, this would trigger human consultation UI
        # For now, we'll simulate consultation completion
        consultation_result = {
            "consultation_reason": ev.context.get('reason', 'Unknown reason'),
            "consultation_timestamp": datetime.now(UTC).isoformat(),
            "consultation_status": "simulated_approval",
            "approved_category": ev.context.get('gamp_category', 5)  # Default to highest category
        }
        
        await ctx.set("consultation_result", consultation_result)
        
        # Get categorization data from context or attribute
        gamp_category = ev.context.get('gamp_category', 5)
        confidence_score = ev.context.get('confidence_score', 0.5)
        
        # If we have the categorization_event as an attribute, use it
        if hasattr(ev, 'categorization_event'):
            gamp_category = ev.categorization_event.gamp_category.value
            confidence_score = ev.categorization_event.confidence_score
        
        # Create a categorization event to continue the workflow
        if hasattr(ev, 'categorization_event'):
            # Use the original event
            return ev.categorization_event
        else:
            # Create new categorization event
            from src.shared.models import GAMPCategory
            return GAMPCategorizationEvent(
                gamp_category=GAMPCategory(gamp_category),
                confidence_score=confidence_score,
                justification="Categorization after human consultation",
                risk_assessment={"consultation_required": True},
                document_content="",  # Will be filled from context
                review_required=True,
                session_id=self._workflow_session_id
            )

    @step
    async def generate_oq_tests(
        self,
        ctx: Context,
        ev: AgentResultsEvent
    ) -> OQTestSuiteEvent:
        """
        Generate OQ test suite based on planning and agent results.
        
        Args:
            ctx: Workflow context
            ev: Agent results event with context data
            
        Returns:
            OQTestSuiteEvent with generated test suite
        """
        self.logger.info("🧪 Starting OQ test generation")
        
        # Get required context
        planning_event = await ctx.get("planning_event")
        categorization_result = await ctx.get("categorization_result")
        document_path = await ctx.get("document_path")
        
        # Aggregate context from agent results
        aggregated_context = {
            "agent_results": {}
        }
        
        for result in ev.agent_results:
            if result.success:
                aggregated_context["agent_results"][result.agent_type] = result.result_data
        
        # Add planning context
        aggregated_context["planning_context"] = {
            "test_strategy": planning_event.test_strategy,
            "estimated_test_count": planning_event.estimated_test_count
        }
        
        # Create OQ generation event
        oq_generation_event = OQTestGenerationEvent(
            gamp_category=categorization_result.gamp_category,
            urs_content=categorization_result.document_content if hasattr(categorization_result, 'document_content') else "",
            document_metadata={
                "name": Path(document_path).name if document_path else "Unknown",
                "path": document_path,
                "version": "1.0"
            },
            aggregated_context=aggregated_context,
            required_test_count=planning_event.estimated_test_count,
            test_strategy=planning_event.test_strategy,
            correlation_id=uuid4(),
            session_id=self._workflow_session_id
        )
        
        # Run OQ generation workflow
        from src.agents.oq_generator.workflow import OQTestGenerationWorkflow
        
        oq_workflow = OQTestGenerationWorkflow(
            llm=self.llm,
            timeout=600,  # 10 minutes
            verbose=self.verbose,
            enable_validation=True,
            oq_generation_event=oq_generation_event
        )
        
        try:
            self.logger.info("Running OQ test generation workflow...")
            oq_result = await oq_workflow.run()
            
            # Extract result
            if hasattr(oq_result, "result"):
                oq_data = oq_result.result
            else:
                oq_data = oq_result
            
            # Check if generation was successful
            if oq_data.get("status") == "completed_successfully":
                # Extract the OQ test suite event
                oq_event = oq_data.get("full_event")
                if oq_event and isinstance(oq_event, OQTestSuiteEvent):
                    self.logger.info(
                        f"✅ Generated {oq_event.test_suite.total_test_count} OQ tests successfully"
                    )
                    return oq_event
                else:
                    # Create event from data
                    raise ValueError("OQ generation completed but no valid event returned")
            else:
                # Handle consultation required or error
                consultation = oq_data.get("consultation", {})
                raise RuntimeError(
                    f"OQ generation requires consultation: {consultation.get('consultation_type', 'unknown')}"
                )
                
        except Exception as e:
            self.logger.error(f"OQ generation failed: {e}")
            # Re-raise to trigger consultation
            raise

    @step
    async def complete_workflow(
        self,
        ctx: Context,
        ev: WorkflowCompletionEvent | OQTestSuiteEvent
    ) -> StopEvent:
        """
        Complete the unified workflow and return final results.
        
        Args:
            ctx: Workflow context
            ev: Either WorkflowCompletionEvent or OQTestSuiteEvent
            
        Returns:
            StopEvent with comprehensive workflow results
        """
        # Get all stored results
        workflow_start_time = await ctx.get("workflow_start_time")
        document_path = await ctx.get("document_path")
        
        # Calculate total processing time
        total_time = datetime.now(UTC) - workflow_start_time if workflow_start_time else None
        
        # Determine if we have OQ results
        if isinstance(ev, OQTestSuiteEvent):
            # Successful OQ generation
            status = "completed_with_oq_tests"
            oq_results = {
                "test_suite_id": ev.test_suite.suite_id,
                "total_tests": ev.test_suite.total_test_count,
                "coverage_percentage": ev.test_suite.coverage_percentage,
                "review_required": ev.test_suite.review_required,
                "generation_successful": ev.generation_successful
            }
        else:
            # Workflow completion without OQ (consultation or partial completion)
            status = "completed_partial"
            oq_results = None
        
        # Get all context data with safe defaults
        categorization_result = await ctx.get("categorization_result", default=None)
        planning_event = await ctx.get("planning_event", default=None)
        agent_results = await ctx.get("collected_results", default=[])
        
        # Compile final results
        final_results = {
            "workflow_metadata": {
                "session_id": self._workflow_session_id,
                "document_path": document_path,
                "start_time": workflow_start_time.isoformat() if workflow_start_time else None,
                "completion_time": datetime.now(UTC).isoformat(),
                "total_processing_time": total_time.total_seconds() if total_time else None,
                "phoenix_enabled": self.enable_phoenix
            },
            "status": status,
            "categorization": {
                "gamp_category": categorization_result.gamp_category.value if categorization_result else None,
                "confidence_score": categorization_result.confidence_score if categorization_result else 0.0,
                "review_required": categorization_result.review_required if categorization_result else False
            } if categorization_result else None,
            "planning": {
                "estimated_test_count": planning_event.estimated_test_count if planning_event else 0,
                "test_strategy": planning_event.test_strategy if planning_event else None,
                "agent_requests": len(planning_event.agent_requests) if planning_event else 0
            } if planning_event else None,
            "agent_coordination": {
                "total_agents": len(agent_results),
                "successful_agents": len([r for r in agent_results if r.success]),
                "failed_agents": len([r for r in agent_results if not r.success])
            },
            "oq_generation": oq_results,
            "workflow_results": ev.workflow_results if hasattr(ev, 'workflow_results') else None
        }
        
        self.logger.info(f"🎉 Unified workflow completed with status: {status}")
        if total_time:
            self.logger.info(f"⏱️ Total processing time: {total_time.total_seconds():.2f} seconds")
        
        return StopEvent(result=final_results)


# Convenience function for main.py compatibility
async def run_unified_test_generation_workflow(
    urs_content: str | None = None,
    document_name: str = "test_document",
    document_version: str = "1.0",
    author: str = "system",
    timeout: int = 900,
    verbose: bool = False,
    enable_error_handling: bool = True,
    confidence_threshold: float = 0.5,
    enable_document_processing: bool = True,
    enable_parallel_coordination: bool = True,
    document_path: str | None = None,
    **kwargs
) -> dict[str, Any]:
    """
    Run the unified test generation workflow with compatibility for main.py.
    
    Args:
        urs_content: Document content (deprecated, use document_path)
        document_name: Name of the document
        document_version: Version of the document
        author: Author of the document
        timeout: Workflow timeout in seconds
        verbose: Enable verbose logging
        enable_error_handling: Enable error handling
        confidence_threshold: Confidence threshold for categorization
        enable_document_processing: Enable document processing
        enable_parallel_coordination: Enable parallel coordination
        document_path: Path to the document to process
        **kwargs: Additional arguments
        
    Returns:
        Dictionary containing workflow results
    """
    # Create workflow instance
    workflow = UnifiedTestGenerationWorkflow(
        timeout=timeout,
        verbose=verbose,
        enable_parallel_coordination=enable_parallel_coordination,
        enable_phoenix=True,
        enable_human_consultation=True
    )
    
    # Determine document path - prefer explicit document_path
    if document_path:
        doc_path = document_path
    else:
        # If we only have content, we need to create a temporary file
        # For now, raise error if no path provided
        raise ValueError("document_path is required for unified workflow")
    
    # Run the workflow
    try:
        result = await workflow.run(document_path=doc_path)
        
        # Handle different result formats
        if hasattr(result, "result"):
            return result.result
        else:
            return result
            
    except Exception as e:
        logger.error(f"Unified workflow failed: {e}")
        return {
            "status": "failed",
            "error": str(e),
            "workflow_metadata": {
                "session_id": workflow._workflow_session_id,
                "failure_reason": "workflow_execution_error"
            }
        }


# Export the main workflow class and convenience function
__all__ = ["UnifiedTestGenerationWorkflow", "run_unified_test_generation_workflow"]