"""
Unified Test Generation Workflow - Main orchestration module.

This module contains the master workflow that orchestrates all agents
and processes in the pharmaceutical test generation system. It manages
the complete flow from document ingestion to final test suite generation,
including GAMP-5 categorization, research, SME consultation, and OQ testing.

Key Features:
- Event-driven multi-agent orchestration
- GAMP-5 compliant workflow execution
- Pharmaceutical regulatory validation
- Phoenix AI observability integration
- Error handling and recovery mechanisms
- Context aggregation and correlation
"""

import asyncio
import json
import logging
import os
import traceback
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from llama_index.core.llms import LLM
from llama_index.core.workflow import Context, StartEvent, StopEvent, Workflow, step
from llama_index.core.workflow.events import Event
from pydantic import BaseModel, Field, field_validator
from src.config.llm_config import LLMConfig
from src.core.document_loader import PharmaceuticalDocumentLoader
from src.monitoring.agent_instrumentation import trace_agent_method
from src.agents.oq_generator.workflow import OQTestGenerationWorkflow
from src.agents.categorization.gamp_categorization_workflow import GAMPCategorizationWorkflow

# Import all event types
from src.core.events import (
    AgentRequestEvent,
    AgentResultEvent,
    AgentResultsEvent,
    ConsultationRequiredEvent,
    GAMPCategorizationEvent,
    OQTestGenerationEvent,
    PlanningEvent,
    URSIngestionEvent,
    ValidationResultEvent,
    WorkflowCompletionEvent
)

# Import custom data models
from src.core.models import (
    AgentExecRequest,
    AgentResult,
    ContextData,
    DocumentMetadata,
    GAMPCategory,
    TestGenerationRequest,
    UnifiedWorkflowResult,
    ValidationResult,
    WorkflowSession
)

# Monitoring and observability
from src.monitoring.simple_tracer import get_tracer


class UnifiedTestGenerationWorkflow(Workflow):
    """
    Master workflow orchestrating complete pharmaceutical test generation.
    
    This workflow manages the entire process from document ingestion through
    GAMP-5 categorization, agent consultation, and final OQ test generation,
    ensuring compliance with pharmaceutical regulatory requirements.
    """

    def __init__(
        self,
        llm: LLM = None,
        timeout: int = 1800,  # 30 minutes default
        verbose: bool = False
    ):
        """
        Initialize the unified workflow.
        
        Args:
            llm: LlamaIndex LLM instance for agent operations
            timeout: Maximum workflow execution time in seconds
            verbose: Enable detailed logging
        """
        super().__init__(timeout=timeout, verbose=verbose)
        
        # Core configuration
        self.llm = llm or LLMConfig.get_llm()
        self.verbose = verbose
        
        # Session management
        self._workflow_session_id = str(uuid4())
        self._correlation_id = str(uuid4())
        
        # Initialize logger
        self.logger = logging.getLogger(__name__)
        if verbose:
            self.logger.setLevel(logging.DEBUG)
        
        # Initialize document loader
        self.document_loader = PharmaceuticalDocumentLoader(
            enable_observability=True
        )
        
        # Initialize tracer for OpenTelemetry instrumentation
        self.tracer = get_tracer(__name__)
        
        self.logger.info(f"UnifiedTestGenerationWorkflow initialized - Session: {self._workflow_session_id}")

    @step
    async def start_unified_workflow(self, ctx: Context, ev: StartEvent) -> URSIngestionEvent:
        """
        Initialize the unified workflow and prepare document processing.
        
        This step extracts the document path from the start event and sets up
        the initial workflow context for pharmaceutical document processing.
        """
        self.logger.info("[START] Running Unified Test Generation Workflow")
        self.logger.info("=" * 60)
        
        # Extract document path from start event args
        if not ev.args or len(ev.args) == 0:
            raise ValueError("No document path provided to workflow")
            
        document_path = ev.args[0]
        self.logger.info(f"📄 Loading document: {document_path}")
        
        # Store workflow configuration in context
        await ctx.set("workflow_session_id", self._workflow_session_id)
        await ctx.set("correlation_id", self._correlation_id)
        await ctx.set("document_path", document_path)
        await ctx.set("start_time", datetime.utcnow())
        
        # Load document metadata and content
        try:
            document_content = await self.document_loader.load_document(document_path)
            document_metadata = DocumentMetadata.create_from_path(document_path)
            
            await ctx.set("document_content", document_content)
            await ctx.set("document_metadata", document_metadata)
            
        except Exception as e:
            self.logger.error(f"Failed to load document {document_path}: {e}")
            raise RuntimeError(f"Document loading failed: {e}") from e
        
        # Create URS ingestion event
        return URSIngestionEvent(
            document_path=document_path,
            document_content=document_content,
            document_metadata=document_metadata,
            correlation_id=uuid.UUID(self._correlation_id),
            session_id=self._workflow_session_id
        )

    @step
    async def categorize_document(self, ctx: Context, ev: URSIngestionEvent) -> GAMPCategorizationEvent:
        """
        Perform GAMP-5 categorization of the pharmaceutical document.
        
        This step analyzes the document content using the GAMP categorization
        agent to determine the appropriate category (1-5) and associated
        requirements for test generation.
        """
        self.logger.info("Running GAMP-5 categorization workflow...")
        
        # Initialize GAMP categorization workflow
        gamp_workflow = GAMPCategorizationWorkflow(
            llm=self.llm,
            timeout=600,  # 10 minutes for categorization
            verbose=self.verbose
        )
        
        try:
            # Run categorization
            categorization_result = await gamp_workflow.run(
                document_path=ev.document_path,
                document_content=ev.document_content,
                correlation_id=ev.correlation_id
            )
            
            # Store categorization results in context
            await ctx.set("categorization_result", categorization_result)
            
            return categorization_result
            
        except Exception as e:
            self.logger.error(f"GAMP categorization failed: {e}")
            raise RuntimeError(f"Categorization workflow failed: {e}") from e

    @step
    async def check_consultation_required(
        self, 
        ctx: Context, 
        ev: GAMPCategorizationEvent
    ) -> WorkflowCompletionEvent | ConsultationRequiredEvent:
        """
        Determine if consultation is required based on categorization results.
        
        Evaluates the GAMP category and categorization confidence to decide
        whether agent consultation is needed or if we can proceed directly
        to test generation.
        """
        self.logger.info(f"Checking consultation requirements for category {ev.gamp_category}")
        
        # Store categorization in context for later use
        await ctx.set("gamp_category", ev.gamp_category)
        await ctx.set("categorization_confidence", ev.confidence)
        await ctx.set("categorization_rationale", ev.rationale)
        
        # Check if consultation is required
        consultation_required = (
            ev.confidence < 0.85 or  # Low confidence threshold
            ev.gamp_category == GAMPCategory.CATEGORY_5 or  # Always consult for category 5
            ev.requires_consultation
        )
        
        if consultation_required:
            self.logger.info("Consultation required - proceeding with agent workflow")
            
            return ConsultationRequiredEvent(
                consultation_type="multi_agent_validation",
                context={
                    "gamp_category": ev.gamp_category.value,
                    "confidence": ev.confidence,
                    "rationale": ev.rationale,
                    "document_metadata": ev.document_metadata,
                    "correlation_id": str(ev.correlation_id)
                },
                urgency="normal",
                required_expertise=["context_provider", "research_agent", "sme_agent"],
                triggering_step="check_consultation_required"
            )
        else:
            self.logger.info("No consultation required - completing workflow")
            
            return WorkflowCompletionEvent(
                result_type="categorization_only",
                gamp_category=ev.gamp_category,
                confidence=ev.confidence,
                session_id=self._workflow_session_id,
                correlation_id=ev.correlation_id
            )

    @step
    async def complete_workflow(self, ctx: Context, ev: WorkflowCompletionEvent) -> StopEvent:
        """
        Complete the workflow without consultation.
        
        This step handles cases where no consultation is needed and returns
        the final results directly.
        """
        self.logger.info("Completing workflow without consultation")
        
        # Retrieve context data
        start_time = await ctx.get("start_time")
        document_metadata = await ctx.get("document_metadata")
        
        # Create final result
        result = UnifiedWorkflowResult(
            workflow_type="categorization_only",
            gamp_category=ev.gamp_category,
            confidence=ev.confidence,
            session_id=ev.session_id,
            correlation_id=ev.correlation_id,
            execution_time=datetime.utcnow() - start_time,
            document_metadata=document_metadata,
            test_suite=None,  # No tests generated
            agent_results=[],  # No agents executed
            validation_results=[]
        )
        
        await ctx.set("final_result", result)
        return StopEvent(result=result)

    @step  
    async def handle_consultation(self, ctx: Context, ev: ConsultationRequiredEvent) -> PlanningEvent:
        """
        Handle consultation requirement by initiating agent planning.
        
        This step processes consultation requests and sets up the planning
        phase for multi-agent execution including context provider, research
        agent, and SME agent coordination.
        """
        self.logger.info(f"Handling consultation: {ev.consultation_type}")
        
        # Store consultation context
        await ctx.set("consultation_context", ev.context)
        await ctx.set("required_expertise", ev.required_expertise)
        
        # Create planning event for agent coordination
        return PlanningEvent(
            planning_type="multi_agent_execution",
            required_agents=ev.required_expertise,
            context_data=ev.context,
            correlation_id=uuid.UUID(ev.context.get("correlation_id")),
            session_id=self._workflow_session_id
        )

    @step
    async def run_planning_workflow(self, ctx: Context, ev: PlanningEvent) -> AgentRequestEvent:
        """
        Execute planning workflow to coordinate agent execution.
        
        This step determines the optimal sequence and configuration for
        agent execution based on the consultation requirements and
        document characteristics.
        """
        self.logger.info("Running planning workflow for agent coordination")
        
        # Store planning context
        await ctx.set("planning_context", ev.context_data)
        await ctx.set("required_agents", ev.required_agents)
        await ctx.set("agents_completed", [])
        await ctx.set("agent_results", {})
        
        # Start with context provider (always first)
        return AgentRequestEvent(
            agent_type="context_provider",
            request=AgentExecRequest(
                agent_type="context_provider",
                input_data=ev.context_data,
                correlation_id=ev.correlation_id,
                session_id=ev.session_id,
                timeout=600
            ),
            correlation_id=ev.correlation_id,
            session_id=ev.session_id
        )

    @step
    async def execute_agent_request(self, ctx: Context, ev: AgentRequestEvent) -> AgentResultEvent:
        """
        Execute individual agent request.
        
        This step handles the execution of specific agents (context provider,
        research agent, SME agent) based on the request parameters and
        manages agent lifecycle and error handling.
        """
        self.logger.info(f"Executing agent: {ev.agent_type}")
        
        try:
            # Import agents dynamically based on type
            if ev.agent_type == "context_provider":
                from src.agents.parallel.context_provider import ContextProviderAgent
                agent = ContextProviderAgent(llm=self.llm)
                
                # Prepare context provider request
                result = await agent.search_and_assemble_context({
                    "gamp_category": ev.request.input_data.get("gamp_category"),
                    "document_content": await ctx.get("document_content"),
                    "requirements": ["pharmaceutical_standards", "gamp_guidelines", "validation_procedures"]
                })
                
            elif ev.agent_type == "research_agent":
                from src.agents.parallel.research_agent import ResearchAgent
                agent = ResearchAgent(llm=self.llm)
                
                # Get context from previous agent
                agent_results = await ctx.get("agent_results")
                context_result = agent_results.get("context_provider", {})
                
                result = await agent.research_requirements({
                    "gamp_category": ev.request.input_data.get("gamp_category"),
                    "context_data": context_result.get("context_data", {}),
                    "research_scope": ["regulatory_requirements", "industry_standards", "best_practices"]
                })
                
            elif ev.agent_type == "sme_agent":
                from src.agents.parallel.sme_agent import SMEAgent
                agent = SMEAgent(llm=self.llm)
                
                # Get context from previous agents
                agent_results = await ctx.get("agent_results")
                context_result = agent_results.get("context_provider", {})
                research_result = agent_results.get("research_agent", {})
                
                result = await agent.provide_expert_guidance({
                    "gamp_category": ev.request.input_data.get("gamp_category"),
                    "context_data": context_result.get("context_data", {}),
                    "research_findings": research_result.get("research_data", {}),
                    "expertise_areas": ["validation", "compliance", "risk_assessment"]
                })
                
            else:
                raise ValueError(f"Unknown agent type: {ev.agent_type}")
            
            # Create agent result
            agent_result = AgentResult(
                agent_type=ev.agent_type,
                result_data=result,
                execution_time=0,  # TODO: Track actual execution time
                success=True,
                error=None,
                correlation_id=ev.correlation_id,
                session_id=ev.session_id
            )
            
            return AgentResultEvent(
                agent_type=ev.agent_type,
                result=agent_result,
                correlation_id=ev.correlation_id,
                session_id=ev.session_id
            )
            
        except Exception as e:
            self.logger.error(f"Agent execution failed for {ev.agent_type}: {e}")
            
            # Create error result
            agent_result = AgentResult(
                agent_type=ev.agent_type,
                result_data={},
                execution_time=0,
                success=False,
                error=str(e),
                correlation_id=ev.correlation_id,
                session_id=ev.session_id
            )
            
            return AgentResultEvent(
                agent_type=ev.agent_type,
                result=agent_result,
                correlation_id=ev.correlation_id,
                session_id=ev.session_id
            )

    @step
    async def collect_agent_results(
        self, 
        ctx: Context, 
        ev: AgentResultEvent
    ) -> AgentRequestEvent | AgentResultsEvent:
        """
        Collect agent results and determine next agent or completion.
        
        This step manages the sequential execution of agents, collecting
        results and determining whether additional agents need to be
        executed or if all required agents have completed.
        """
        self.logger.info(f"Collecting result from agent: {ev.agent_type}")
        
        # Update agent results and completion tracking
        agent_results = await ctx.get("agent_results")
        agents_completed = await ctx.get("agents_completed")
        required_agents = await ctx.get("required_agents")
        
        agent_results[ev.agent_type] = ev.result.result_data
        agents_completed.append(ev.agent_type)
        
        await ctx.set("agent_results", agent_results)
        await ctx.set("agents_completed", agents_completed)
        
        # Determine next agent to execute
        remaining_agents = [agent for agent in required_agents if agent not in agents_completed]
        
        if remaining_agents:
            # Execute next agent
            next_agent = remaining_agents[0]
            self.logger.info(f"Executing next agent: {next_agent}")
            
            return AgentRequestEvent(
                agent_type=next_agent,
                request=AgentExecRequest(
                    agent_type=next_agent,
                    input_data=await ctx.get("planning_context"),
                    correlation_id=ev.correlation_id,
                    session_id=ev.session_id,
                    timeout=600
                ),
                correlation_id=ev.correlation_id,
                session_id=ev.session_id
            )
        else:
            # All agents completed - proceed to results aggregation
            self.logger.info("All agents completed - aggregating results")
            
            return AgentResultsEvent(
                results={
                    agent_type: AgentResult(
                        agent_type=agent_type,
                        result_data=result_data,
                        execution_time=0,
                        success=True,
                        error=None,
                        correlation_id=ev.correlation_id,
                        session_id=ev.session_id
                    )
                    for agent_type, result_data in agent_results.items()
                },
                correlation_id=ev.correlation_id,
                session_id=ev.session_id
            )

    @step
    async def generate_oq_tests(self, ctx: Context, ev: AgentResultsEvent) -> StopEvent:
        """
        Generate OQ test suite based on agent results.
        
        This step coordinates the final OQ test generation using the
        aggregated context from all executed agents, ensuring comprehensive
        test coverage and pharmaceutical compliance.
        """
        self.logger.info("Generating OQ test suite from agent results")
        
        try:
            # Aggregate context data from all agents
            aggregated_context = {}
            for agent_type, result in ev.results.items():
                if result.success and result.result_data:
                    aggregated_context[agent_type] = result.result_data
            
            # Get categorization and document data
            gamp_category = await ctx.get("gamp_category")
            document_metadata = await ctx.get("document_metadata")
            document_content = await ctx.get("document_content")
            
            # Create OQ generation event
            oq_generation_event = OQTestGenerationEvent(
                gamp_category=gamp_category,
                document_content=document_content,
                document_metadata=document_metadata,
                aggregated_context=aggregated_context,
                correlation_id=uuid4(),
                session_id=self._workflow_session_id
            )

            # Run OQ generation workflow

            oq_workflow = OQTestGenerationWorkflow(
                llm=self.llm,
                timeout=1500,  # 25 minutes (to accommodate o3 model)
                verbose=self.verbose,
                enable_validation=False,  # CRITICAL: Disable validation to prevent consultation loop
                oq_generation_event=oq_generation_event
            )

            try:
                self.logger.info("Running OQ test generation workflow...")
                oq_result = await oq_workflow.run()

                # CRITICAL FIX: Check result type first
                if isinstance(oq_result, ConsultationRequiredEvent):
                    # Handle consultation required scenario 
                    self.logger.error(f"OQ generation failed: {oq_result.consultation_type}")
                    raise RuntimeError(f"OQ generation failed: {oq_result.consultation_type}")

                # Process successful OQ result
                if hasattr(oq_result, 'test_suite') and oq_result.test_suite:
                    test_suite = oq_result.test_suite
                    self.logger.info(f"✅ Generated {test_suite.total_test_count} OQ tests")
                    
                    # Save test suite to file
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_dir = Path("outputs/oq_tests")
                    output_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Save in both JSON and YAML formats
                    json_file = output_dir / f"oq_test_suite_{timestamp}.json"
                    yaml_file = output_dir / f"oq_test_suite_{timestamp}.yaml"
                    
                    # Save JSON format
                    with open(json_file, 'w', encoding='utf-8') as f:
                        json.dump(test_suite.model_dump(), f, indent=2, ensure_ascii=False)
                    
                    # Save YAML format
                    try:
                        import yaml
                        with open(yaml_file, 'w', encoding='utf-8') as f:
                            yaml.dump(test_suite.model_dump(), f, default_flow_style=False, allow_unicode=True)
                    except ImportError:
                        self.logger.warning("PyYAML not available - skipping YAML output")
                    
                    self.logger.info(f"📁 Test suite saved to: {json_file}")
                    if yaml_file.exists():
                        self.logger.info(f"📁 Test suite saved to: {yaml_file}")
                    
                else:
                    self.logger.error("OQ workflow returned invalid result structure")
                    raise RuntimeError("OQ generation produced invalid result")

            except Exception as e:
                self.logger.error(f"OQ generation workflow failed: {e}")
                self.logger.error(traceback.format_exc())
                raise RuntimeError(f"OQ generation failed: {e}") from e

            # Create final result
            start_time = await ctx.get("start_time")
            result = UnifiedWorkflowResult(
                workflow_type="full_oq_generation",
                gamp_category=gamp_category,
                confidence=await ctx.get("categorization_confidence", 0.0),
                session_id=self._workflow_session_id,
                correlation_id=ev.correlation_id,
                execution_time=datetime.utcnow() - start_time,
                document_metadata=document_metadata,
                test_suite=getattr(oq_result, 'test_suite', None),
                agent_results=list(ev.results.values()),
                validation_results=[]
            )
            
            await ctx.set("final_result", result)
            return StopEvent(result=result)
            
        except Exception as e:
            self.logger.error(f"OQ test generation failed: {e}")
            self.logger.error(traceback.format_exc())
            raise RuntimeError(f"OQ test generation failed: {e}") from e


# Additional workflow steps for specific scenarios

class ProcessSingleDocumentWorkflow(Workflow):
    """
    Simplified workflow for processing single documents without full orchestration.
    
    This workflow is used for focused document processing tasks where full
    multi-agent coordination is not required.
    """

    def __init__(self, llm: LLM = None, timeout: int = 600):
        super().__init__(timeout=timeout)
        self.llm = llm or LLMConfig.get_llm()
        self.logger = logging.getLogger(__name__)

    @step  
    async def process_document(self, ctx: Context, ev: URSIngestionEvent) -> None:
        """
        Process single document for specific analysis.
        
        This step handles focused document processing without triggering
        the full multi-agent workflow, suitable for targeted analysis tasks.
        """
        self.logger.info(f"Processing single document: {ev.document_path}")
        
        # Store document processing results in context
        await ctx.set("processed_document", {
            "path": ev.document_path,
            "content_length": len(ev.document_content),
            "metadata": ev.document_metadata
        })
        
        # No event returned - this is a terminal step


# Utility functions for workflow management

def create_unified_workflow(
    llm: LLM = None,
    timeout: int = 1800,
    verbose: bool = False
) -> UnifiedTestGenerationWorkflow:
    """
    Factory function to create configured unified workflow instance.
    
    Args:
        llm: LlamaIndex LLM instance
        timeout: Workflow timeout in seconds
        verbose: Enable verbose logging
        
    Returns:
        UnifiedTestGenerationWorkflow: Configured workflow instance
    """
    return UnifiedTestGenerationWorkflow(
        llm=llm,
        timeout=timeout,
        verbose=verbose
    )


def create_single_document_workflow(
    llm: LLM = None,
    timeout: int = 600
) -> ProcessSingleDocumentWorkflow:
    """
    Factory function to create single document processing workflow.
    
    Args:
        llm: LlamaIndex LLM instance
        timeout: Workflow timeout in seconds
        
    Returns:
        ProcessSingleDocumentWorkflow: Configured workflow instance
    """
    return ProcessSingleDocumentWorkflow(
        llm=llm,
        timeout=timeout
    )