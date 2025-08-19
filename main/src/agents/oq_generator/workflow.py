"""
OQ Test Generation Workflow

This module implements the GAMP-5 compliant OQ test generation workflow
using LlamaIndex workflows for structured pharmaceutical test creation.
"""

import asyncio
import json
import logging
import time
import traceback
from datetime import datetime, UTC
from typing import Dict, Any, Optional
from uuid import uuid4

from llama_index.core.workflow import Context, StartEvent, StopEvent, Workflow, step

from .events import (
    OQTestGenerationEvent,
    OQTestSuiteEvent
)
from src.core.events import ConsultationRequiredEvent
from src.agents.oq_generator.generator_v2 import OQTestGeneratorV2


logger = logging.getLogger(__name__)


class OQGenerationWorkflow(Workflow):
    """
    LlamaIndex workflow for OQ test generation.
    
    This workflow orchestrates the generation of GAMP-5 compliant OQ tests
    with proper error handling and consultation requirements.
    """

    def __init__(self, timeout: int = 1800, **kwargs):
        """
        Initialize the OQ generation workflow.
        
        Args:
            timeout: Maximum execution time in seconds (default: 30 minutes)
            **kwargs: Additional parameters (ignored with explicit error for debugging)
        """
        # NO FALLBACKS: Explicitly reject unexpected parameters with diagnostic info
        if kwargs:
            unexpected_params = list(kwargs.keys())
            raise TypeError(
                f"OQGenerationWorkflow.__init__() got unexpected keyword arguments: {unexpected_params}. "
                f"This workflow only accepts 'timeout' parameter. "
                f"Check calling code for incorrect parameter passing. "
                f"Common issue: passing 'llm' parameter which is not supported by this workflow."
            )
        
        super().__init__(timeout=timeout)
        
        # NO FALLBACKS: Ensure generator creation succeeds
        try:
            self.generator = OQTestGeneratorV2()
            logger.info("OQTestGeneratorV2 instantiated successfully")
        except Exception as e:
            logger.error(f"Failed to create OQTestGeneratorV2: {e}")
            raise RuntimeError(
                f"OQ generator instantiation failed: {e}. "
                f"Check OQTestGeneratorV2 constructor and dependencies."
            ) from e
            
        self.workflow_start_time = None
        
    @step
    async def start_oq_generation(
        self,
        ctx: Context,
        ev: StartEvent
    ) -> OQTestGenerationEvent:
        """
        Start the OQ test generation process.
        
        Args:
            ctx: Workflow context
            ev: Start or OQ test generation event
            
        Returns:
            OQTestGenerationEvent
        """
        logger.info("Starting OQ test generation workflow")
        self.workflow_start_time = datetime.now(UTC)
        
        # Handle StartEvent by extracting relevant data with defensive programming
        try:
            # Handle different ways of accessing StartEvent data
            if hasattr(ev, 'data'):
                # Direct attribute access
                data = ev.data if ev.data is not None else {}
            elif hasattr(ev, 'get'):
                # Dictionary-like access
                data = ev.get("data", {})
            elif hasattr(ev, '__dict__') and 'data' in ev.__dict__:
                # Direct dict access
                data = ev.__dict__.get('data', {})
            else:
                # Last resort - check for any data-like attributes
                logger.warning(f"StartEvent has no standard data access. Attributes: {dir(ev)}")
                data = {}
            
            if not data:
                logger.warning("StartEvent contains empty data dictionary")
                
        except Exception as e:
            logger.error(f"Error extracting data from StartEvent: {e}")
            raise RuntimeError(
                f"Failed to process StartEvent in OQ generation workflow. "
                f"Error: {e}, "
                f"StartEvent type: {type(ev)}, "
                f"This may indicate LlamaIndex version compatibility issues."
            ) from e
        
        generation_event = OQTestGenerationEvent(
                gamp_category=data.get("gamp_category", 3),
                urs_content=data.get("urs_content", ""),
                document_metadata=data.get("document_metadata", {}),
                required_test_count=data.get("required_test_count", 5),  # PERFORMANCE: Keep low default for fast generation
                test_strategy=data.get("test_strategy", {}),
                aggregated_context=data.get("agent_results", {}),
                categorization_confidence=data.get("categorization_confidence", 0.8),
                event_id=uuid4(),
                timestamp=datetime.now(UTC),
                correlation_id=data.get("correlation_id", uuid4())
        )
            
        # Store the event for later use
        await ctx.set("generation_event", generation_event)
        
        return generation_event

    @step
    async def generate_oq_tests(
        self,
        ctx: Context,
        ev: OQTestGenerationEvent
    ) -> OQTestSuiteEvent | ConsultationRequiredEvent:
        """
        Generate OQ test suite using the dedicated generator.
        
        Args:
            ctx: Workflow context
            ev: OQ test generation event
            
        Returns:
            OQTestSuiteEvent on success, ConsultationRequiredEvent if intervention needed
        """
        try:
            logger.info(f"🚀 STARTING OQ GENERATION: GAMP Category {ev.gamp_category}, Target: {ev.required_test_count} tests")
            logger.info(f"📋 PROGRESS: Initializing test generation workflow...")
            
            # Use the dedicated OQ generator
            result = await self._generate_oq_test_suite_impl(ctx, ev)
            
            # Handle different result types
            if isinstance(result, ConsultationRequiredEvent):
                logger.warning("OQ generation requires consultation")
                return result
            elif isinstance(result, OQTestSuiteEvent):
                logger.info("OQ test suite generated successfully")
                return result
            else:
                # Fallback: create consultation event
                logger.error("Unexpected result type from OQ generation")
                return ConsultationRequiredEvent(
                    consultation_type="oq_generation_system_error",
                    context={
                        "error": f"Unexpected result type: {type(result)}",
                        "gamp_category": ev.gamp_category,
                        "timestamp": datetime.now(UTC).isoformat()
                    },
                    urgency="high",
                    required_expertise=["system_admin", "qa_engineer"],
                    triggering_step="generate_oq_tests",
                    consultation_id=uuid4()
                )
                
        except Exception as e:
            logger.error(f"Unexpected error in OQ generation: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            return ConsultationRequiredEvent(
                consultation_type="oq_generation_system_error",
                context={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "gamp_category": ev.gamp_category,
                    "traceback": traceback.format_exc(),
                    "timestamp": datetime.now(UTC).isoformat()
                },
                urgency="high",
                required_expertise=["system_admin", "qa_engineer"],
                triggering_step="generate_oq_tests",
                consultation_id=uuid4()
            )

    @step
    async def complete_oq_generation(
        self,
        ctx: Context,
        ev: OQTestSuiteEvent
    ) -> StopEvent:
        """
        Complete the OQ generation workflow with successful test suite.
        
        Args:
            ctx: Workflow context
            ev: OQ test suite event
            
        Returns:
            StopEvent with test suite results
        """
        logger.info(f"OQ generation workflow completed successfully with {ev.test_suite.total_test_count} tests")
        
        # Calculate workflow duration
        workflow_duration = None
        if self.workflow_start_time:
            workflow_duration = (datetime.now(UTC) - self.workflow_start_time).total_seconds()
        
        # Store the test suite in context
        await ctx.set("generated_test_suite", ev.test_suite)
        
        return StopEvent(
            result={
                "status": "completed_successfully",
                "test_suite": ev.test_suite,
                "full_event": ev,  # Include full event for backward compatibility
                "total_tests": ev.test_suite.total_test_count,
                "suite_id": ev.test_suite.suite_id,
                "gamp_category": ev.test_suite.gamp_category,
                "workflow_duration": workflow_duration,
                "generation_successful": ev.generation_successful
            }
        )

    @step
    async def handle_consultation(
        self,
        ctx: Context,
        ev: ConsultationRequiredEvent
    ) -> StopEvent:
        """
        Handle consultation requirements by stopping workflow.
        
        Args:
            ctx: Workflow context
            ev: Consultation required event
            
        Returns:
            StopEvent with consultation details
        """
        logger.warning(f"Consultation required: {ev.consultation_type}")
        
        # Store consultation context
        await ctx.set("consultation_event", ev)
        
        return StopEvent(
            result={
                "consultation_type": ev.consultation_type,
                "consultation_context": ev.context,
                "generation_status": "consultation_required",
                "urgency": ev.urgency,
                "required_expertise": ev.required_expertise,
                "consultation_id": str(ev.consultation_id),
                "triggering_step": ev.triggering_step
            }
        )

    async def _generate_oq_test_suite_impl(
        self,
        ctx: Context,
        ev: OQTestGenerationEvent
    ) -> OQTestSuiteEvent | ConsultationRequiredEvent:
        """
        Implementation of OQ test suite generation.
        
        Args:
            ctx: Workflow context
            ev: OQ test generation event
            
        Returns:
            OQTestSuiteEvent or ConsultationRequiredEvent
        """
        try:
            start_time = time.time()
            
            # Generate OQ tests using the dedicated generator
            # CRITICAL FIX: Use correct method signature for OQTestGeneratorV2
            from src.core.events import GAMPCategory
            
            # Convert gamp_category to proper enum
            if isinstance(ev.gamp_category, int):
                gamp_category_enum = GAMPCategory(ev.gamp_category)
            else:
                gamp_category_enum = ev.gamp_category
            
            logger.info(f"🔧 GENERATING: Using DeepSeek V3 for GAMP Category {gamp_category_enum.value}")
            logger.info(f"📄 DOCUMENT: {ev.document_metadata.get('name', 'unknown')}")
            logger.info(f"🎯 TARGET COUNT: {ev.required_test_count} tests")
            
            suite_result = await self.generator.generate_oq_test_suite(
                gamp_category=gamp_category_enum,  # Correct parameter name
                urs_content=ev.urs_content,        # Correct parameter name
                document_name=ev.document_metadata.get("name", "unknown"),
                context_data=ev.aggregated_context  # Correct parameter name
            )
            
            generation_time = time.time() - start_time
            logger.info(f"🎉 SUCCESS: OQ generation completed in {generation_time:.2f} seconds!")
            
            # Check if generation was successful
            # CRITICAL FIX: Check OQTestSuite object, not dictionary
            if not suite_result:
                logger.error("OQ generation returned None result")
                return ConsultationRequiredEvent(
                    consultation_type="oq_generation_empty_result",
                    context={
                        "error": "Generation returned None result",
                        "gamp_category": ev.gamp_category,
                        "generation_time": generation_time,
                        "timestamp": datetime.now(UTC).isoformat()
                    },
                    urgency="normal",
                    required_expertise=["qa_engineer"],
                    triggering_step="_generate_oq_test_suite_impl",
                    consultation_id=uuid4()
                )
            
            # Validate OQTestSuite object
            if not hasattr(suite_result, 'test_cases') or not suite_result.test_cases:
                logger.error(f"OQ generation returned invalid result type: {type(suite_result)}")
                return ConsultationRequiredEvent(
                    consultation_type="oq_generation_invalid_result", 
                    context={
                        "error": "Generation returned object without test_cases",
                        "result_type": str(type(suite_result)),
                        "gamp_category": ev.gamp_category,
                        "generation_time": generation_time,
                        "timestamp": datetime.now(UTC).isoformat()
                    },
                    urgency="normal",
                    required_expertise=["qa_engineer"],
                    triggering_step="_generate_oq_test_suite_impl",
                    consultation_id=uuid4()
                )
            
            # Create successful result event
            logger.info(f"✅ COMPLETE: Successfully generated {len(suite_result.test_cases)} test cases for {ev.document_metadata.get('name', 'document')}")
            logger.info(f"📊 SUMMARY: Suite ID: {suite_result.suite_id}, GAMP Category: {gamp_category_enum.value}, Generation Time: {generation_time:.2f}s")
            
            return OQTestSuiteEvent(
                test_suite=suite_result,
                generation_metadata={
                    "generation_time_seconds": generation_time,
                    "workflow_duration": (
                        datetime.now(UTC) - self.workflow_start_time
                    ).total_seconds() if self.workflow_start_time else None,
                    "gamp_category": ev.gamp_category,
                    "num_test_cases": len(suite_result.test_cases),  # FIXED: Use OQTestSuite attribute
                    "generator_version": "v2"
                },
                generation_successful=True,
                compliance_validation={"gamp5_compliant": True},
                event_id=uuid4(),
                timestamp=datetime.now(UTC),
                correlation_id=ev.correlation_id
            )
            
        except Exception as e:
            logger.error(f"Error in OQ test suite generation implementation: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            return ConsultationRequiredEvent(
                consultation_type="oq_generation_implementation_error",
                context={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "gamp_category": ev.gamp_category,
                    "traceback": traceback.format_exc(),
                    "timestamp": datetime.now(UTC).isoformat()
                },
                urgency="high",
                required_expertise=["system_admin", "qa_engineer"],
                triggering_step="_generate_oq_test_suite_impl",
                consultation_id=uuid4()
            )


# Create workflow instance for external use
oq_workflow = OQGenerationWorkflow()


async def run_oq_generation_workflow(
    categorized_requirements: Dict[str, Any],
    gamp_category: int,
    document_name: str,
    agent_results: Dict[str, Any],
    timeout: int = 1800
) -> Dict[str, Any]:
    """
    Run the OQ generation workflow with the provided parameters.
    
    Args:
        categorized_requirements: Structured requirements data
        gamp_category: GAMP-5 category (1-5)
        document_name: Name of source document
        agent_results: Results from parallel agents
        timeout: Maximum execution time in seconds
        
    Returns:
        Dictionary containing workflow results
    """
    workflow = OQGenerationWorkflow(timeout=timeout)
    
    try:
        # Create the generation event
        generation_event = OQTestGenerationEvent(
            gamp_category=gamp_category,
            urs_content="",  # Will be populated from categorized_requirements
            document_metadata={"name": document_name},
            required_test_count=5,
            test_strategy={},
            aggregated_context=agent_results,
            categorization_confidence=0.8,
            event_id=uuid4(),
            timestamp=datetime.now(UTC),
            correlation_id=uuid4()
        )
        
        # Run the workflow
        result = await workflow.run(data={
            "gamp_category": gamp_category,
            "urs_content": str(categorized_requirements),
            "document_metadata": {"name": document_name},
            "required_test_count": 5,
            "agent_results": agent_results,
            "correlation_id": uuid4()
        })
        
        return result
        
    except Exception as e:
        logger.error(f"Error running OQ generation workflow: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        return {
            "error": str(e),
            "error_type": type(e).__name__,
            "status": "workflow_error",
            "timestamp": datetime.now(UTC).isoformat(),
            "traceback": traceback.format_exc()
        }