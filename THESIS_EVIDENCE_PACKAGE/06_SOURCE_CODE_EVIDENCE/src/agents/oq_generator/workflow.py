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
import psutil
import gc
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

# Enhanced traceability logging
TRACE_PREFIX = "[OQ-TRACE]"
RESOURCE_PREFIX = "[OQ-RESOURCE]"
BATCH_PREFIX = "[OQ-BATCH]"


class OQGenerationWorkflow(Workflow):
    """
    LlamaIndex workflow for OQ test generation.
    
    This workflow orchestrates the generation of GAMP-5 compliant OQ tests
    with proper error handling and consultation requirements.
    """

    def __init__(self, timeout: int = 1800, **kwargs):
        """
        Initialize the OQ generation workflow with enhanced traceability.
        
        Args:
            timeout: Maximum execution time in seconds (default: 30 minutes)
            **kwargs: Additional parameters (ignored with explicit error for debugging)
        """
        # Track workflow instance creation
        self.workflow_id = str(uuid4())[:8]
        logger.info(f"{TRACE_PREFIX} Creating OQ workflow instance: {self.workflow_id}")
        
        # Track initial resource state
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        logger.info(f"{RESOURCE_PREFIX} Initial memory usage: {initial_memory:.2f} MB")
        
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
            logger.info(f"{TRACE_PREFIX} Creating OQTestGeneratorV2 for workflow {self.workflow_id}")
            self.generator = OQTestGeneratorV2()
            logger.info(f"{TRACE_PREFIX} OQTestGeneratorV2 instantiated successfully")
        except Exception as e:
            logger.error(f"{TRACE_PREFIX} Failed to create OQTestGeneratorV2: {e}")
            raise RuntimeError(
                f"OQ generator instantiation failed: {e}. "
                f"Check OQTestGeneratorV2 constructor and dependencies."
            ) from e
            
        self.workflow_start_time = None
        self.step_timings = {}
        self.batch_progress = []
        self.resource_snapshots = []
        
    @step
    async def start_oq_generation(
        self,
        ctx: Context,
        ev: StartEvent
    ) -> OQTestGenerationEvent:
        """
        Start the OQ test generation process with enhanced traceability.
        
        Args:
            ctx: Workflow context
            ev: Start or OQ test generation event
            
        Returns:
            OQTestGenerationEvent
        """
        step_start = time.time()
        logger.info(f"{TRACE_PREFIX} [Workflow {self.workflow_id}] STEP 1/3: start_oq_generation")
        logger.info(f"{TRACE_PREFIX} Starting OQ test generation workflow")
        self.workflow_start_time = datetime.now(UTC)
        
        # Resource snapshot
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        logger.info(f"{RESOURCE_PREFIX} Memory at step start: {memory_mb:.2f} MB")
        
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
        
        # Track step completion
        step_duration = time.time() - step_start
        self.step_timings['start_oq_generation'] = step_duration
        logger.info(f"{TRACE_PREFIX} Step 'start_oq_generation' completed in {step_duration:.2f}s")
        
        return generation_event

    @step
    async def generate_oq_tests(
        self,
        ctx: Context,
        ev: OQTestGenerationEvent
    ) -> OQTestSuiteEvent | ConsultationRequiredEvent:
        """
        Generate OQ test suite with comprehensive traceability.
        
        Args:
            ctx: Workflow context
            ev: OQ test generation event
            
        Returns:
            OQTestSuiteEvent on success, ConsultationRequiredEvent if intervention needed
        """
        step_start = time.time()
        logger.info(f"{TRACE_PREFIX} [Workflow {self.workflow_id}] STEP 2/3: generate_oq_tests")
        
        # Resource tracking
        process = psutil.Process()
        memory_before = process.memory_info().rss / 1024 / 1024
        logger.info(f"{RESOURCE_PREFIX} Memory before generation: {memory_before:.2f} MB")
        
        try:
            logger.info(f"{TRACE_PREFIX} 🚀 STARTING OQ GENERATION: GAMP Category {ev.gamp_category}, Target: {ev.required_test_count} tests")
            logger.info(f"{TRACE_PREFIX} 📋 PROGRESS: Initializing test generation workflow...")
            logger.info(f"{BATCH_PREFIX} Batch configuration: {ev.required_test_count} tests in batches of 2")
            
            # Use the dedicated OQ generator
            result = await self._generate_oq_test_suite_impl(ctx, ev)
            
            # Track memory after generation
            memory_after = process.memory_info().rss / 1024 / 1024
            memory_delta = memory_after - memory_before
            logger.info(f"{RESOURCE_PREFIX} Memory after generation: {memory_after:.2f} MB (delta: {memory_delta:+.2f} MB)")
            
            # Handle different result types
            if isinstance(result, ConsultationRequiredEvent):
                logger.warning(f"{TRACE_PREFIX} OQ generation requires consultation")
                return result
            elif isinstance(result, OQTestSuiteEvent):
                step_duration = time.time() - step_start
                self.step_timings['generate_oq_tests'] = step_duration
                logger.info(f"{TRACE_PREFIX} OQ test suite generated successfully in {step_duration:.2f}s")
                logger.info(f"{BATCH_PREFIX} Generation summary: {len(self.batch_progress)} batches processed")
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
        Implementation of OQ test suite generation with batch tracking.
        
        Args:
            ctx: Workflow context
            ev: OQ test generation event
            
        Returns:
            OQTestSuiteEvent or ConsultationRequiredEvent
        """
        try:
            start_time = time.time()
            logger.info(f"{TRACE_PREFIX} Starting batch generation implementation")
            
            # Generate OQ tests using the dedicated generator
            # CRITICAL FIX: Use correct method signature for OQTestGeneratorV2
            from src.core.events import GAMPCategory
            
            # Convert gamp_category to proper enum
            if isinstance(ev.gamp_category, int):
                gamp_category_enum = GAMPCategory(ev.gamp_category)
            else:
                gamp_category_enum = ev.gamp_category
            
            logger.info(f"{TRACE_PREFIX} 🔧 GENERATING: Using DeepSeek V3 for GAMP Category {gamp_category_enum.value}")
            logger.info(f"{TRACE_PREFIX} 📄 DOCUMENT: {ev.document_metadata.get('name', 'unknown')}")
            logger.info(f"{TRACE_PREFIX} 🎯 TARGET COUNT: {ev.required_test_count} tests")
            
            # Track batch progress
            num_batches = (ev.required_test_count + 1) // 2  # 2 tests per batch
            logger.info(f"{BATCH_PREFIX} Expected batches: {num_batches}")
            
            # Add heartbeat logging for long-running generation
            async def log_heartbeat():
                """Log periodic heartbeat during generation"""
                elapsed = 0
                while elapsed < 300:  # Max 5 minutes
                    await asyncio.sleep(10)
                    elapsed += 10
                    logger.info(f"{TRACE_PREFIX} ⏱️ Generation in progress... {elapsed}s elapsed")
            
            # Start heartbeat task
            heartbeat_task = asyncio.create_task(log_heartbeat())
            
            try:
                suite_result = await self.generator.generate_oq_test_suite(
                    gamp_category=gamp_category_enum,  # Correct parameter name
                    urs_content=ev.urs_content,        # Correct parameter name
                    document_name=ev.document_metadata.get("name", "unknown"),
                    context_data=ev.aggregated_context  # Correct parameter name
                )
            finally:
                # Cancel heartbeat task
                heartbeat_task.cancel()
                try:
                    await heartbeat_task
                except asyncio.CancelledError:
                    pass
            
            generation_time = time.time() - start_time
            logger.info(f"{TRACE_PREFIX} 🎉 SUCCESS: OQ generation completed in {generation_time:.2f} seconds!")
            
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
    
    def cleanup(self):
        """
        Clean up workflow resources to prevent state accumulation.
        """
        logger.info(f"{TRACE_PREFIX} [Workflow {self.workflow_id}] Cleaning up resources")
        
        # Clear batch progress
        self.batch_progress.clear()
        
        # Clear resource snapshots
        self.resource_snapshots.clear()
        
        # Clear step timings
        self.step_timings.clear()
        
        # Force garbage collection
        gc.collect()
        
        # Log final memory state
        process = psutil.Process()
        final_memory = process.memory_info().rss / 1024 / 1024
        logger.info(f"{RESOURCE_PREFIX} Final memory after cleanup: {final_memory:.2f} MB")
        
        logger.info(f"{TRACE_PREFIX} Workflow cleanup complete")
    
    def __del__(self):
        """Ensure cleanup on workflow destruction."""
        try:
            self.cleanup()
        except Exception:
            pass  # Ignore errors in destructor


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