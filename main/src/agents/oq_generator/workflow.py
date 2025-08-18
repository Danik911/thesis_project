"""
OQ Test Generation Workflow implementation.

This module implements the complete OQ test generation workflow using
LlamaIndex event-driven architecture with pharmaceutical compliance
and regulatory validation requirements.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from llama_index.core.llms import LLM
from llama_index.core.workflow import Context, StartEvent, StopEvent, Workflow, step
from src.compliance_validation.metadata_injector import get_metadata_injector
from src.config.llm_config import LLMConfig
from src.core.events import ConsultationRequiredEvent

from .events import OQTestGenerationEvent, OQTestSuiteEvent
from .generator import OQTestGenerationError
from .generator_v2 import create_oq_test_generator_v2
from .models import OQTestSuite


class OQTestGenerationWorkflow(Workflow):
    """
    OQ test generation workflow step in the pharmaceutical validation system.
    
    This workflow handles the generation of Operational Qualification test suites
    based on GAMP categorization and context from upstream agents, ensuring
    pharmaceutical compliance and regulatory requirements.
    """

    def __init__(
        self,
        llm: LLM = None,
        timeout: int = 600,  # 10 minutes for test generation
        verbose: bool = False,
        enable_validation: bool = True,
        oq_generation_event: OQTestGenerationEvent = None
    ):
        """
        Initialize OQ test generation workflow.
        
        Args:
            llm: LlamaIndex LLM instance for generation
            timeout: Maximum time for workflow execution
            verbose: Enable verbose logging
            enable_validation: Enable comprehensive validation
            oq_generation_event: Pre-configured event for test generation
        """
        super().__init__(timeout=timeout, verbose=verbose)

        # Store LLM configuration
        self.llm = llm or LLMConfig.get_llm()

        # Configuration
        self.verbose = verbose
        self.enable_validation = enable_validation
        self.oq_generation_event = oq_generation_event

        # Initialize components
        self.logger = logging.getLogger(__name__)
        self._test_generator = None

    @step
    async def start_oq_generation(
        self,
        ctx: Context,
        ev: StartEvent
    ) -> OQTestSuiteEvent | ConsultationRequiredEvent:
        """
        Start the OQ generation workflow from a StartEvent.
        
        This step gets the OQ generation event from the constructor and
        immediately begins the generation process.
        
        Args:
            ctx: Workflow context
            ev: StartEvent (automatically created by LlamaIndex)
            
        Returns:
            OQTestSuiteEvent with generated test suite or
            ConsultationRequiredEvent if generation fails
        """
        self.logger.info("Starting OQ test generation workflow")

        # Get the event from constructor
        if not self.oq_generation_event:
            raise OQTestGenerationError(
                "No OQ generation event provided to workflow",
                {
                    "error": "oq_generation_event not set in constructor",
                    "workflow_state": "initialization_failed"
                }
            )

        # Run generation implementation
        return await self._generate_oq_test_suite_impl(ctx, self.oq_generation_event)

    @step
    async def complete_oq_generation(
        self,
        ctx: Context,
        ev: OQTestSuiteEvent
    ) -> StopEvent:
        """
        Complete the OQ generation workflow.
        
        This step handles final processing of the generated test suite,
        including saving to output files and final validation.
        
        Args:
            ctx: Workflow context
            ev: OQTestSuiteEvent with generated test suite
            
        Returns:
            StopEvent to end workflow
        """
        try:
            # Save test suite to structured output
            output_file = await self._save_test_suite_to_file(ev.test_suite)
            
            self.logger.info(f"OQ test suite saved to: {output_file}")
            
            # Store final results in context
            await ctx.set("output_file", output_file)
            await ctx.set("final_test_suite", ev.test_suite)
            
            return StopEvent(
                result={
                    "test_suite": ev.test_suite,
                    "output_file": str(output_file),
                    "test_count": len(ev.test_suite.tests),
                    "generation_status": "success"
                }
            )

        except Exception as e:
            self.logger.error(f"Error completing OQ generation: {e}")
            
            return StopEvent(
                result={
                    "error": str(e),
                    "generation_status": "failed_completion"
                }
            )

    @step
    async def handle_consultation(
        self,
        ctx: Context,
        ev: ConsultationRequiredEvent
    ) -> StopEvent:
        """
        Handle consultation required events by returning failure result.
        
        This step processes consultation events and returns appropriate
        error information for the calling system to handle.
        
        Args:
            ctx: Workflow context
            ev: ConsultationRequiredEvent with error details
            
        Returns:
            StopEvent with failure information
        """
        self.logger.error(f"OQ generation requires consultation: {ev.consultation_type}")
        
        # Store consultation context
        await ctx.set("consultation_event", ev)
        
        return StopEvent(
            result={
                "error": ev.message,
                "consultation_type": ev.consultation_type,
                "consultation_context": ev.context,
                "generation_status": "consultation_required",
                "requires_human_intervention": ev.requires_immediate_attention
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
            # Initialize test generator with timeout configuration
            if not self._test_generator:
                # Use enhanced V2 generator with async support
                workflow_timeout = getattr(self, "timeout", 600)  # Default 10 minutes
                generation_timeout = int(workflow_timeout * 0.8)

                # Use async V2 generator for DeepSeek V3 - no LLM parameter needed
                self._test_generator = create_oq_test_generator_v2(
                    verbose=self.verbose,
                    generation_timeout=generation_timeout
                )

            # Store generation context
            await ctx.set("generation_event", ev)

            # Generate test suite using structured output
            self.logger.info(
                f"Generating {ev.required_test_count} OQ tests for {ev.document_metadata.get('name', 'Unknown')}"
            )

            # Track processing time for ALCOA+ metadata
            generation_start = datetime.now().timestamp()

            # CRITICAL: Use async generator (V2) with correct context data access
            context_data = ev.aggregated_context if hasattr(ev, 'aggregated_context') else {}
            
            test_suite = await self._test_generator.generate_oq_test_suite(
                gamp_category=ev.gamp_category,
                urs_content=ev.urs_content,
                document_name=ev.document_metadata.get("name", "Unknown Document"),
                context_data=context_data,
                config=None  # Use default config since event doesn't have oq_config
            )

            # Track generation time
            processing_time = datetime.now().timestamp() - generation_start

            # Inject ALCOA+ metadata for regulatory compliance
            test_suite = await self._inject_alcoa_metadata(test_suite, ev, processing_time)

            # Validate test suite quality if enabled
            if self.enable_validation:
                quality_issues = await self._validate_test_suite_quality(test_suite, ev)
                
                if quality_issues:
                    self.logger.warning(f"Quality issues detected: {quality_issues}")
                    
                    # For now, proceed with generation but log issues
                    # In the future, could trigger consultation or regeneration
                    test_suite.metadata["quality_issues"] = quality_issues

            self.logger.info(
                f"Successfully generated {len(test_suite.tests)} OQ tests "
                f"for GAMP Category {ev.gamp_category.value}"
            )

            # Store in context for potential downstream steps
            await ctx.set("generated_test_suite", test_suite)
            
            # Return test suite event to be handled by completion step
            return OQTestSuiteEvent(test_suite=test_suite)

        except Exception as e:
            self.logger.error(f"Unexpected error in OQ generation: {e}")
            
            # Return consultation event for human intervention
            return ConsultationRequiredEvent(
                consultation_type="oq_generation_system_error",
                context={
                    "error_message": f"OQ generation failed with system error: {str(e)}",
                    "error": str(e),
                    "gamp_category": str(ev.gamp_category.value),
                    "document": ev.document_metadata.get("name", "Unknown"),
                    "required_tests": ev.required_test_count,
                    "event_attributes": [attr for attr in dir(ev) if not attr.startswith('_')],
                    "error_type": type(e).__name__,
                    "requires_immediate_attention": True
                },
                urgency="high",
                required_expertise=["OQ_generation", "GAMP_validation", "System_error_analysis"],
                triggering_step="oq_generation_system_error"
            )

    async def _inject_alcoa_metadata(
        self,
        test_suite: OQTestSuite,
        event: OQTestGenerationEvent,
        processing_time: float
    ) -> OQTestSuite:
        """
        Inject ALCOA+ metadata for regulatory compliance.
        
        Args:
            test_suite: Generated test suite
            event: Original generation event
            processing_time: Time taken for generation
            
        Returns:
            Test suite with ALCOA+ metadata
        """
        try:
            metadata_injector = get_metadata_injector()
            
            # Inject comprehensive ALCOA+ metadata
            enhanced_suite = await metadata_injector.inject_oq_metadata(
                test_suite=test_suite,
                generation_context={
                    "gamp_category": event.gamp_category.value,
                    "document_name": event.document_metadata.get("name", "Unknown"),
                    "processing_time": processing_time,
                    "generation_timestamp": datetime.now().isoformat(),
                    "context_sources": list(event.aggregated_context.keys()) if hasattr(event, 'aggregated_context') else [],
                    "test_strategy": event.test_strategy if hasattr(event, 'test_strategy') else {}
                }
            )
            
            return enhanced_suite
            
        except Exception as e:
            self.logger.warning(f"Failed to inject ALCOA+ metadata: {e}")
            # Return original suite if metadata injection fails
            return test_suite

    async def _validate_test_suite_quality(
        self,
        test_suite: OQTestSuite,
        event: OQTestGenerationEvent
    ) -> list[str]:
        """
        Validate test suite quality against pharmaceutical standards.
        
        Args:
            test_suite: Generated test suite
            event: Original generation event
            
        Returns:
            List of quality issues found
        """
        issues = []
        
        # Check test count meets requirements
        if len(test_suite.tests) < event.required_test_count:
            issues.append(
                f"Test count ({len(test_suite.tests)}) below requirement ({event.required_test_count})"
            )

        # Check for essential fields in tests
        for i, test in enumerate(test_suite.tests):
            if not test.test_id:
                issues.append(f"Test {i+1} missing test_id")
            
            if not test.test_description:
                issues.append(f"Test {i+1} missing description")
            
            if not test.expected_result:
                issues.append(f"Test {i+1} missing expected result")
            
            # Check GAMP category consistency
            if hasattr(test, 'gamp_category') and test.gamp_category != str(event.gamp_category.value):
                issues.append(f"Test {i+1} GAMP category mismatch")
            
            # Check estimated execution time is present
            if not hasattr(test, 'estimated_execution_time') or not test.estimated_execution_time:
                issues.append(f"Test {i+1} missing estimated_execution_time")

        return issues

    async def _save_test_suite_to_file(self, test_suite: OQTestSuite) -> Path:
        """
        Save test suite to structured output file.
        
        Args:
            test_suite: Generated test suite
            
        Returns:
            Path to saved file
        """
        from src.shared.output_manager import get_output_manager
        
        output_manager = get_output_manager()
        
        # Generate timestamp for unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create filename with test suite ID
        filename = f"test_suite_{test_suite.suite_id}_{timestamp}.json"
        
        # Save to test_suites directory
        output_file = await output_manager.save_test_suite(
            test_suite=test_suite,
            filename=filename,
            category="test_suites"
        )
        
        return output_file


# Helper function for external workflow integration
async def run_oq_generation_workflow(
    oq_event: OQTestGenerationEvent,
    llm: LLM = None,
    timeout: int = 600,
    verbose: bool = False
) -> dict[str, Any]:
    """
    Run the OQ generation workflow with provided event.
    
    Args:
        oq_event: OQ test generation event
        llm: LLM instance to use
        timeout: Maximum execution time
        verbose: Enable verbose logging
        
    Returns:
        Workflow results with test suite or error information
    """
    workflow = OQTestGenerationWorkflow(
        llm=llm,
        timeout=timeout,
        verbose=verbose,
        oq_generation_event=oq_event
    )
    
    try:
        # Run workflow with StartEvent
        result = await workflow.run()
        return result
        
    except Exception as e:
        logging.error(f"OQ generation workflow failed: {e}")
        return {
            "error": str(e),
            "generation_status": "workflow_failed"
        }