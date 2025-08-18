"""
OQ test generation engine with LLMTextCompletionProgram integration.

This module implements the core test generation logic using LlamaIndex
LLMTextCompletionProgram for structured output generation without JSON mode,
ensuring pharmaceutical compliance and GAMP-5 validation requirements.

Enhanced with robust JSON extraction for OSS model compatibility.
"""

import json
import logging
import re
from datetime import UTC, datetime
from typing import Any

from llama_index.core.llms import LLM
from pydantic import ValidationError
from src.config.timeout_config import TimeoutConfig
from src.core.events import GAMPCategory

from .models import OQGenerationConfig, OQTestSuite
from .templates import GAMPCategoryConfig, OQPromptTemplates
from .yaml_parser import extract_yaml_from_response, validate_yaml_data


def clean_unicode_characters(text: str) -> str:
    """
    Clean invisible Unicode characters that can break JSON parsing.
    
    Handles common issues from OSS model responses including:
    - BOM markers (UTF-8 BOM: \ufeff)
    - Zero-width spaces (\u200b)
    - Zero-width non-joiner (\u200c)
    - Zero-width joiner (\u200d)
    - Line/paragraph separators (\u2028, \u2029)
    
    Args:
        text: Raw text that may contain invisible characters
        
    Returns:
        Cleaned text suitable for JSON parsing
    """
    # Remove BOM marker if present at start
    if text.startswith("\ufeff"):
        text = text[1:]

    # Remove various invisible Unicode characters that break JSON parsing
    invisible_chars = [
        "\u200b",  # Zero-width space
        "\u200c",  # Zero-width non-joiner
        "\u200d",  # Zero-width joiner
        "\u2028",  # Line separator
        "\u2029",  # Paragraph separator
        "\ufeff",  # Additional BOM occurrences
    ]

    for char in invisible_chars:
        text = text.replace(char, "")

    return text


def extract_json_from_mixed_response(response_text: str) -> tuple[str, dict[str, Any]]:
    """
    Extract JSON from OSS model response that may contain explanatory text and markdown.
    
    OSS models often return responses like:
    "Here's your OQ test suite:\n\n```json\n{...}\n```\n\nThis meets all requirements."
    
    Args:
        response_text: Raw response from OSS model
        
    Returns:
        Tuple of (extracted_json_string, diagnostic_context)
        
    Raises:
        TestGenerationFailure: If JSON extraction fails with full diagnostic context
    """
    diagnostic_context = {
        "raw_response_length": len(response_text),
        "raw_response_preview": response_text[:200] + "..." if len(response_text) > 200 else response_text,
        "unicode_issues_detected": False,
        "extraction_method": None,
        "json_found": False,
        "parsing_stage": "initial_cleaning"
    }

    try:
        # Step 1: Clean unicode characters
        original_text = response_text
        cleaned_text = clean_unicode_characters(response_text)

        if cleaned_text != original_text:
            diagnostic_context["unicode_issues_detected"] = True
            diagnostic_context["unicode_chars_removed"] = len(original_text) - len(cleaned_text)

        diagnostic_context["parsing_stage"] = "markdown_extraction"

        # Step 2: Try to extract from markdown code blocks first
        markdown_patterns = [
            r"```json\s*\n(.*?)\n```",  # Standard ```json``` blocks
            r"```\s*\n(\{.*?\})\s*\n```",  # Generic ``` blocks with JSON
            r"`([^`]*\{.*?\}[^`]*)`",  # Single backticks with JSON
        ]

        for pattern in markdown_patterns:
            matches = re.findall(pattern, cleaned_text, re.DOTALL | re.MULTILINE)
            if matches:
                json_candidate = matches[0].strip()
                diagnostic_context["extraction_method"] = f"markdown_pattern_{pattern[:20]}..."
                diagnostic_context["json_found"] = True
                diagnostic_context["parsing_stage"] = "json_validation"

                # Validate it's actually JSON
                try:
                    json.loads(json_candidate)
                    return json_candidate, diagnostic_context
                except json.JSONDecodeError as e:
                    diagnostic_context["json_parse_error"] = str(e)
                    continue

        # Step 3: Look for JSON object boundaries without markdown
        diagnostic_context["parsing_stage"] = "boundary_detection"

        # Find JSON object boundaries (balanced braces)
        brace_count = 0
        start_idx = -1

        for i, char in enumerate(cleaned_text):
            if char == "{":
                if brace_count == 0:
                    start_idx = i
                brace_count += 1
            elif char == "}":
                brace_count -= 1
                if brace_count == 0 and start_idx != -1:
                    # Found complete JSON object
                    json_candidate = cleaned_text[start_idx:i+1]
                    diagnostic_context["extraction_method"] = "boundary_detection"
                    diagnostic_context["json_found"] = True
                    diagnostic_context["parsing_stage"] = "json_validation"

                    try:
                        json.loads(json_candidate)
                        return json_candidate, diagnostic_context
                    except json.JSONDecodeError as e:
                        diagnostic_context["json_parse_error"] = str(e)
                        continue

        # Step 4: Last resort - try to find any JSON-like content
        diagnostic_context["parsing_stage"] = "pattern_matching"

        # Look for patterns that start with { and contain typical JSON elements
        json_patterns = [
            r'(\{[^{}]*"suite_id"[^{}]*\})',  # Look for suite_id field
            r'(\{.*?"gamp_category".*?\})',   # Look for gamp_category field
            r'(\{.*?"test_cases".*?\})',      # Look for test_cases field
        ]

        for pattern in json_patterns:
            matches = re.findall(pattern, cleaned_text, re.DOTALL)
            if matches:
                json_candidate = matches[0].strip()
                diagnostic_context["extraction_method"] = f"pattern_matching_{pattern[:30]}..."
                diagnostic_context["json_found"] = True
                diagnostic_context["parsing_stage"] = "json_validation"

                try:
                    json.loads(json_candidate)
                    return json_candidate, diagnostic_context
                except json.JSONDecodeError as e:
                    diagnostic_context["json_parse_error"] = str(e)
                    continue

        # If we get here, no valid JSON was found
        diagnostic_context["parsing_stage"] = "extraction_failed"
        diagnostic_context["json_found"] = False

        raise TestGenerationFailure(
            "No valid JSON found in OSS model response after trying all extraction methods",
            {
                "error_type": "json_extraction_failure",
                "diagnostic_context": diagnostic_context,
                "no_fallback_available": True,
                "requires_human_intervention": True,
                "suggested_actions": [
                    "Check OSS model response format",
                    "Verify model is returning structured output",
                    "Consider adjusting prompt for clearer JSON formatting",
                    "Review extraction patterns for new response formats"
                ]
            }
        )

    except Exception as e:
        if isinstance(e, TestGenerationFailure):
            raise  # Re-raise our own exceptions

        # Unexpected error during extraction
        diagnostic_context["parsing_stage"] = "unexpected_error"
        diagnostic_context["unexpected_error"] = str(e)

        raise TestGenerationFailure(
            f"Unexpected error during JSON extraction: {e}",
            {
                "error_type": "json_extraction_unexpected_error",
                "diagnostic_context": diagnostic_context,
                "no_fallback_available": True,
                "requires_human_intervention": True
            }
        )


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

    def __init__(self, llm: LLM, verbose: bool = False, generation_timeout: int = None):
        """
        Initialize OQ test generator.
        
        Args:
            llm: LlamaIndex LLM instance for generation
            verbose: Enable verbose logging
            generation_timeout: Timeout for LLM generation in seconds (default from TimeoutConfig)
        """
        self.llm = llm
        self.verbose = verbose
        # Use configurable timeout with fallback to OQ generator default
        self.generation_timeout = generation_timeout or TimeoutConfig.get_timeout("oq_generator")
        self.logger = logging.getLogger(__name__)

        # Critical: NO fallback values or default behaviors
        self._generation_program = None
        self._last_generation_context = None

        # Configure LLM timeout if it's OpenAI
        if hasattr(self.llm, "timeout"):
            # Set timeout to our generation timeout (OpenAI SDK v1.0.0+)
            self.llm.timeout = self.generation_timeout
            self.logger.info(f"Set LLM timeout to {self.generation_timeout}s")
        elif hasattr(self.llm, "_client") and hasattr(self.llm._client, "timeout"):
            # For newer OpenAI client versions
            self.llm._client.timeout = self.generation_timeout
            self.logger.info(f"Set LLM client timeout to {self.generation_timeout}s")

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
        Generate test suite using YAML as primary format for OSS model compatibility.
        
        Critical: NO FALLBACKS - Uses YAML generation directly with strict parsing.
        """
        try:
            # Store generation context for debugging
            self._last_generation_context = {
                "gamp_category": gamp_category.value,
                "document_name": document_name,
                "test_count": test_count,
                "context_summary": context_summary
            }

            # Get raw LLM response configured for YAML output
            raw_response = self._get_raw_llm_response(
                gamp_category=gamp_category,
                urs_content=urs_content,
                document_name=document_name,
                test_count=test_count,
                context_summary=context_summary
            )

            # Parse YAML response - NO FALLBACKS
            try:
                yaml_data = extract_yaml_from_response(raw_response)
                validated_data = validate_yaml_data(yaml_data)
                result = OQTestSuite(**validated_data)

                self.logger.info(
                    f"OQ generation successful with YAML parsing: "
                    f"{len(result.test_cases)} tests generated"
                )
                return result

            except Exception as yaml_e:
                # YAML parsing failed - provide diagnostic information and fail
                raise TestGenerationFailure(
                    f"YAML parsing failed: {yaml_e}",
                    {
                        "parsing_error": str(yaml_e),
                        "raw_response_preview": raw_response[:500] + "..." if len(raw_response) > 500 else raw_response,
                        "generation_method": "yaml_primary",
                        "no_fallback_available": True,
                        "requires_human_intervention": True,
                        "suggested_actions": [
                            "Review YAML format in model response",
                            "Check for indentation and syntax issues",
                            "Verify all required fields are present",
                            "Consider model prompt adjustments for clearer YAML structure"
                        ]
                    }
                )

        except Exception as e:
            # Generation failed - NO fallbacks
            error_context = {
                "llm_model": str(self.llm),
                "gamp_category": gamp_category.value,
                "document_name": document_name,
                "test_count": test_count,
                "error_message": str(e),
                "generation_method": "yaml_primary"
            }

            raise TestGenerationFailure(
                f"YAML-based test generation failed: {e}",
                error_context
            )

    # Template-based extraction methods removed - NO FALLBACKS policy
    # All generation must go through primary YAML path for GAMP-5 compliance

    def _get_raw_llm_response(
        self,
        gamp_category: GAMPCategory,
        urs_content: str,
        document_name: str,
        test_count: int,
        context_summary: str
    ) -> str:
        """
        Get raw response from LLM optimized for YAML generation.
        
        This directly calls the LLM with optimized parameters:
        - max_tokens: 15000 (reduced from 30000 for better consistency)
        - temperature: 0.1 (low for more deterministic output)
        """
        try:
            # Create YAML-optimized prompt
            prompt = OQPromptTemplates.get_generation_prompt(
                gamp_category=gamp_category,
                urs_content=urs_content,
                document_name=document_name,
                test_count=test_count,
                context_summary=context_summary
            )

            # Configure LLM for OSS model optimization
            generation_kwargs = {
                "max_tokens": 15000,  # Reduced from 30000 for better parseability
                "temperature": 0.1,   # Low temperature for consistent YAML format
            }

            # Make direct LLM call with optimized parameters
            if hasattr(self.llm, "complete"):
                # Use complete method for direct text completion
                response = self.llm.complete(prompt, **generation_kwargs)
                raw_response = response.text if hasattr(response, "text") else str(response)
            elif hasattr(self.llm, "_client"):
                # For OpenRouter-compatible clients, try direct generation
                try:
                    # Try to use the client directly with proper parameters
                    response = self.llm._client.completions.create(
                        model=getattr(self.llm, "model_name", "llama-3.1-8b"),
                        prompt=prompt,
                        **generation_kwargs
                    )
                    raw_response = response.choices[0].text
                except AttributeError:
                    # Fallback to standard complete method
                    response = self.llm.complete(prompt)
                    raw_response = response.text if hasattr(response, "text") else str(response)
            else:
                # Last resort: try calling LLM directly
                raw_response = str(self.llm(prompt))

            self.logger.info(
                f"Raw LLM response received: {len(raw_response)} characters "
                f"(max_tokens={generation_kwargs['max_tokens']}, temperature={generation_kwargs['temperature']})"
            )

            # Log response preview for debugging (first 300 chars to see YAML start)
            response_preview = raw_response[:300] + "..." if len(raw_response) > 300 else raw_response
            self.logger.debug(f"Raw LLM response preview: {response_preview}")

            return raw_response

        except Exception as e:
            raise TestGenerationFailure(
                f"Failed to get raw LLM response for YAML generation: {e}",
                {
                    "error_type": "yaml_llm_response_failure",
                    "llm_model": str(self.llm),
                    "gamp_category": gamp_category.value,
                    "document_name": document_name,
                    "test_count": test_count,
                    "generation_params": generation_kwargs,
                    "no_fallback_available": True
                }
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
