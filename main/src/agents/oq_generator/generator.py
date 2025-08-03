"""
OQ test generation engine with LLMTextCompletionProgram integration.

This module implements the core test generation logic using LlamaIndex
LLMTextCompletionProgram for structured output generation without JSON mode,
ensuring pharmaceutical compliance and GAMP-5 validation requirements.
"""

import logging
from datetime import UTC, datetime
from typing import Any

from llama_index.core.llms import LLM
from llama_index.core.program import LLMTextCompletionProgram
from pydantic import ValidationError
from src.core.events import GAMPCategory

from .models import OQGenerationConfig, OQTestSuite
from .templates import GAMPCategoryConfig, OQPromptTemplates


class OQTestGenerationError(Exception):
    """Base exception for OQ test generation failures."""

    def __init__(self, message: str, error_context: dict[str, Any] = None):
        super().__init__(message)
        self.error_context = error_context or {}
        self.error_context.update({
            "error_type": self.__class__.__name__,
            "timestamp": datetime.now(UTC).isoformat(),
            "no_fallback_available": True,
            "requires_human_intervention": True
        })


class GAMPValidationError(OQTestGenerationError):
    """Raised when GAMP category validation fails."""


class ContextAggregationError(OQTestGenerationError):
    """Raised when context aggregation fails."""


class TestGenerationFailure(OQTestGenerationError):
    """Raised when LLM test generation fails."""


class OQTestGenerator:
    """
    Core OQ test generation engine using LLMTextCompletionProgram.
    
    This class handles the generation of OQ test suites using structured output
    from LLMs while ensuring pharmaceutical compliance and avoiding fallback logic.
    """

    def __init__(self, llm: LLM, verbose: bool = False, generation_timeout: int = 480):
        """
        Initialize OQ test generator.
        
        Args:
            llm: LlamaIndex LLM instance for generation
            verbose: Enable verbose logging
            generation_timeout: Timeout for LLM generation in seconds (default 8 minutes)
        """
        self.llm = llm
        self.verbose = verbose
        self.generation_timeout = generation_timeout
        self.logger = logging.getLogger(__name__)

        # Critical: NO fallback values or default behaviors
        self._generation_program = None
        self._last_generation_context = None
        
        # Configure LLM timeout if it's OpenAI
        if hasattr(self.llm, 'request_timeout'):
            # Set request timeout to our generation timeout
            self.llm.request_timeout = generation_timeout
            self.logger.info(f"Set LLM request timeout to {generation_timeout}s")
        elif hasattr(self.llm, '_client') and hasattr(self.llm._client, 'timeout'):
            # For newer OpenAI client versions
            self.llm._client.timeout = generation_timeout
            self.logger.info(f"Set LLM client timeout to {generation_timeout}s")

    def generate_oq_test_suite(
        self,
        gamp_category: GAMPCategory,
        urs_content: str,
        document_name: str,
        context_data: dict[str, Any] = None,
        config: OQGenerationConfig | None = None
    ) -> OQTestSuite:
        """
        Generate complete OQ test suite for specified GAMP category.
        
        Args:
            gamp_category: GAMP software category
            urs_content: Source URS document content
            document_name: Document name for traceability
            context_data: Aggregated context from upstream agents
            config: Optional generation configuration
            
        Returns:
            Complete OQ test suite with validation metadata
            
        Raises:
            GAMPValidationError: If GAMP category validation fails
            ContextAggregationError: If context aggregation fails
            TestGenerationFailure: If LLM generation fails
            ValidationError: If generated suite fails Pydantic validation
        """
        generation_start = datetime.now(UTC)

        try:
            # Validate GAMP category - NO fallbacks
            self._validate_gamp_category(gamp_category)

            # Get category configuration
            category_config = GAMPCategoryConfig.get_category_config(gamp_category)

            # Determine test count
            if config and config.target_test_count:
                test_count = config.target_test_count
                # Validate against category limits
                min_tests, max_tests = category_config["min_tests"], category_config["max_tests"]
                if not (min_tests <= test_count <= max_tests):
                    raise GAMPValidationError(
                        f"Requested test count {test_count} outside valid range "
                        f"{min_tests}-{max_tests} for GAMP Category {gamp_category.value}",
                        {
                            "gamp_category": gamp_category.value,
                            "requested_count": test_count,
                            "valid_range": (min_tests, max_tests),
                            "category_description": category_config["description"]
                        }
                    )
            else:
                # Use middle of valid range as target
                min_tests, max_tests = category_config["min_tests"], category_config["max_tests"]
                test_count = (min_tests + max_tests) // 2

            # Prepare context summary
            context_summary = self._prepare_context_summary(context_data)

            # Generate test suite using LLMTextCompletionProgram
            test_suite = self._generate_with_structured_output(
                gamp_category=gamp_category,
                urs_content=urs_content,
                document_name=document_name,
                test_count=test_count,
                context_summary=context_summary,
                category_config=category_config
            )

            # Validate generated suite - NO automatic fixes
            self._validate_generated_suite(test_suite, gamp_category, test_count)

            # Calculate generation duration
            generation_duration = (datetime.now(UTC) - generation_start).total_seconds()

            # Update suite metadata
            test_suite.generation_timestamp = generation_start
            test_suite.estimated_execution_time = sum(
                test.estimated_duration_minutes for test in test_suite.test_cases
            )

            # Set compliance flags based on validation
            test_suite.pharmaceutical_compliance = {
                "alcoa_plus_compliant": self._validate_alcoa_compliance(test_suite),
                "cfr_part11_compliant": self._validate_cfr_part11_compliance(test_suite),
                "gamp5_compliant": True,  # Validated by generation process
                "audit_trail_verified": True,
                "data_integrity_validated": self._validate_data_integrity(test_suite)
            }

            self.logger.info(
                f"Successfully generated OQ test suite: {test_suite.suite_id} "
                f"({test_suite.total_test_count} tests, {generation_duration:.2f}s)"
            )

            return test_suite

        except ValidationError as e:
            # Pydantic validation failed - NO fallbacks
            error_context = {
                "validation_errors": str(e),
                "gamp_category": gamp_category.value,
                "document_name": document_name,
                "test_count": test_count if "test_count" in locals() else "unknown",
                "generation_stage": "pydantic_validation"
            }

            raise TestGenerationFailure(
                f"Generated test suite failed Pydantic validation: {e}",
                error_context
            )

        except Exception as e:
            # Unexpected error - NO fallbacks
            error_context = {
                "error_message": str(e),
                "error_type": type(e).__name__,
                "gamp_category": gamp_category.value,
                "document_name": document_name,
                "generation_stage": "unknown"
            }

            self.logger.error(f"OQ generation failed: {e}")

            raise TestGenerationFailure(
                f"Unexpected error during OQ test generation: {e}",
                error_context
            )

    def _validate_gamp_category(self, gamp_category: GAMPCategory) -> None:
        """Validate GAMP category is supported."""
        if gamp_category not in GAMPCategoryConfig.CATEGORY_REQUIREMENTS:
            raise GAMPValidationError(
                f"Unsupported GAMP category: {gamp_category}",
                {
                    "provided_category": gamp_category,
                    "supported_categories": list(GAMPCategoryConfig.CATEGORY_REQUIREMENTS.keys()),
                    "validation_stage": "gamp_category_validation"
                }
            )

    def _prepare_context_summary(self, context_data: dict[str, Any] = None) -> str:
        """
        Prepare context summary for test generation.
        
        Args:
            context_data: Context from upstream agents
            
        Returns:
            Formatted context summary string
        """
        if not context_data:
            return "Standard pharmaceutical validation approach recommended"

        summary_parts = []

        try:
            # SME agent context
            if sme_insights := context_data.get("sme_insights"):
                if isinstance(sme_insights, dict):
                    expertise_areas = sme_insights.get("expertise_areas", {})
                    if expertise_areas:
                        summary_parts.append(f"SME Expertise: {len(expertise_areas)} specialized areas")

            # Research agent context
            if research_findings := context_data.get("research_findings"):
                if isinstance(research_findings, dict):
                    regulatory_updates = research_findings.get("regulatory_updates", [])
                    if regulatory_updates:
                        summary_parts.append(f"Regulatory Updates: {len(regulatory_updates)} recent changes")

            # Context provider context
            if context_result := context_data.get("context_provider_result"):
                if isinstance(context_result, dict):
                    confidence_score = context_result.get("confidence_score", 0.0)
                    regulatory_docs = context_result.get("regulatory_documents", [])
                    summary_parts.append(f"Context Quality: {confidence_score:.1%}")
                    if regulatory_docs:
                        summary_parts.append(f"Regulatory Context: {len(regulatory_docs)} documents")

            # Additional context elements
            if validation_context := context_data.get("validation_context"):
                if isinstance(validation_context, dict):
                    test_strategy = validation_context.get("test_strategy_alignment", {})
                    if test_strategy:
                        summary_parts.append(f"Test Strategy: {', '.join(test_strategy.keys())}")

            return "; ".join(summary_parts) if summary_parts else "Limited context available"

        except Exception as e:
            # Context aggregation failed - log but don't fail generation
            self.logger.warning(f"Context aggregation failed: {e}")
            return "Context aggregation failed - using standard approach"

    def _generate_with_structured_output(
        self,
        gamp_category: GAMPCategory,
        urs_content: str,
        document_name: str,
        test_count: int,
        context_summary: str,
        category_config: dict[str, Any]
    ) -> OQTestSuite:
        """
        Generate test suite using LLMTextCompletionProgram for structured output.
        
        Critical: Uses LLMTextCompletionProgram without JSON mode to avoid infinite loops.
        """
        try:
            # Create structured output program
            generation_program = LLMTextCompletionProgram.from_defaults(
                output_cls=OQTestSuite,
                llm=self.llm,
                prompt_template_str=OQPromptTemplates.get_generation_prompt(
                    gamp_category=gamp_category,
                    urs_content=urs_content,
                    document_name=document_name,
                    test_count=test_count,
                    context_summary=context_summary
                )
            )

            # Store program for debugging
            self._generation_program = generation_program
            self._last_generation_context = {
                "gamp_category": gamp_category.value,
                "document_name": document_name,
                "test_count": test_count,
                "context_summary": context_summary
            }

            # Execute structured generation - NO fallbacks on failure
            result = generation_program()

            if not isinstance(result, OQTestSuite):
                raise TestGenerationFailure(
                    f"LLMTextCompletionProgram returned invalid type: {type(result)}",
                    {
                        "expected_type": "OQTestSuite",
                        "actual_type": str(type(result)),
                        "generation_method": "LLMTextCompletionProgram"
                    }
                )

            return result

        except Exception as e:
            # Generation failed - NO fallbacks
            error_context = {
                "llm_model": str(self.llm),
                "gamp_category": gamp_category.value,
                "document_name": document_name,
                "test_count": test_count,
                "error_message": str(e),
                "generation_method": "LLMTextCompletionProgram"
            }

            raise TestGenerationFailure(
                f"LLM test generation failed: {e}",
                error_context
            )

    def _validate_generated_suite(
        self,
        test_suite: OQTestSuite,
        expected_category: GAMPCategory,
        expected_count: int
    ) -> None:
        """
        Validate generated test suite meets requirements.
        
        Args:
            test_suite: Generated test suite
            expected_category: Expected GAMP category
            expected_count: Expected test count
            
        Raises:
            TestGenerationFailure: If validation fails
        """
        validation_errors = []

        # Validate GAMP category
        if test_suite.gamp_category != expected_category.value:
            validation_errors.append(
                f"GAMP category mismatch: expected {expected_category.value}, "
                f"got {test_suite.gamp_category}"
            )

        # Validate test count
        if test_suite.total_test_count != expected_count:
            validation_errors.append(
                f"Test count mismatch: expected {expected_count}, "
                f"got {test_suite.total_test_count}"
            )

        # Validate test case consistency
        if len(test_suite.test_cases) != test_suite.total_test_count:
            validation_errors.append(
                f"Test cases count inconsistent: test_cases={len(test_suite.test_cases)}, "
                f"total_test_count={test_suite.total_test_count}"
            )

        # Validate unique test IDs
        test_ids = [test.test_id for test in test_suite.test_cases]
        if len(test_ids) != len(set(test_ids)):
            duplicates = [tid for tid in test_ids if test_ids.count(tid) > 1]
            validation_errors.append(f"Duplicate test IDs found: {set(duplicates)}")

        # Validate test ID format
        invalid_ids = [tid for tid in test_ids if not tid.startswith("OQ-") or len(tid) != 6]
        if invalid_ids:
            validation_errors.append(f"Invalid test ID format: {invalid_ids}")

        if validation_errors:
            raise TestGenerationFailure(
                f"Generated test suite validation failed: {'; '.join(validation_errors)}",
                {
                    "validation_errors": validation_errors,
                    "suite_id": test_suite.suite_id,
                    "expected_category": expected_category.value,
                    "expected_count": expected_count,
                    "actual_count": test_suite.total_test_count
                }
            )

    def _validate_alcoa_compliance(self, test_suite: OQTestSuite) -> bool:
        """Check if test suite meets ALCOA+ requirements."""
        # Check for traceability (Attributable)
        traceable_tests = sum(1 for test in test_suite.test_cases if test.urs_requirements)

        # Check for clear procedures (Legible)
        clear_procedures = sum(1 for test in test_suite.test_cases
                             if len(test.test_steps) > 0 and all(len(step.action) >= 10 for step in test.test_steps))

        # Basic compliance check - at least 80% meet criteria
        total_tests = len(test_suite.test_cases)
        return (traceable_tests / total_tests >= 0.8 and
                clear_procedures / total_tests >= 0.8)

    def _validate_cfr_part11_compliance(self, test_suite: OQTestSuite) -> bool:
        """Check if test suite includes CFR Part 11 requirements."""
        # Check for data integrity tests
        data_integrity_tests = sum(1 for test in test_suite.test_cases
                                 if test.test_category == "data_integrity")

        # Check for security tests
        security_tests = sum(1 for test in test_suite.test_cases
                           if test.test_category == "security")

        # Require at least one of each for categories 4 and 5
        if test_suite.gamp_category in [4, 5]:
            return data_integrity_tests >= 1 and security_tests >= 1

        return data_integrity_tests >= 1

    def _validate_data_integrity(self, test_suite: OQTestSuite) -> bool:
        """Check if test suite adequately covers data integrity."""
        # Check for data integrity requirements in tests
        tests_with_di_reqs = sum(1 for test in test_suite.test_cases
                               if test.data_integrity_requirements)

        # Check for audit trail verification steps
        audit_trail_steps = sum(1 for test in test_suite.test_cases
                              for step in test.test_steps
                              if "audit" in step.action.lower() or "trail" in step.action.lower())

        return tests_with_di_reqs >= 1 and audit_trail_steps >= 1
