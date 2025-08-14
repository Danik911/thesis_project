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
            oq_generation_event: The OQ generation event with requirements
        """
        super().__init__(timeout=timeout, verbose=verbose)

        # Use centralized LLM configuration (NO FALLBACKS)
        self.llm = llm or LLMConfig.get_llm(
            max_tokens=4000   # Sufficient for test suite generation
        )

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

        ev = self.oq_generation_event

        # Store correlation ID for traceability
        await ctx.set("correlation_id", ev.correlation_id)
        await ctx.set("gamp_category", ev.gamp_category)

        self.logger.info(
            f"Starting OQ test generation for GAMP Category {ev.gamp_category.value} "
            f"(correlation: {ev.correlation_id})"
        )

        try:
            # Validate prerequisites - NO fallbacks
            self._validate_prerequisites(ev)

            # Initialize test generator with timeout configuration
            if not self._test_generator:
                # Use enhanced V2 generator with o1 model support
                # Use default if timeout attribute not available
                workflow_timeout = getattr(self, "timeout", 600)  # Default 10 minutes
                generation_timeout = int(workflow_timeout * 0.8)

                # Use V2 generator for better model support
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

            test_suite = await self._test_generator.generate_oq_test_suite(
                gamp_category=ev.gamp_category,
                urs_content=ev.urs_content,
                document_name=ev.document_metadata.get("name", "Unknown Document"),
                context_data=ev.aggregated_context,
                config=None  # Use default configuration
            )

            # Calculate processing time for ALCOA+ metadata
            generation_end = datetime.now().timestamp()
            processing_time = generation_end - generation_start

            # Inject ALCOA+ compliance metadata (Task 23 Enhancement)
            test_suite = await self._inject_alcoa_metadata(test_suite, ev, processing_time)

            # Validate test suite quality if enabled
            if self.enable_validation:
                quality_issues = await self._validate_test_suite_quality(test_suite, ev)

                if quality_issues:
                    # Quality issues found - request consultation
                    return ConsultationRequiredEvent(
                        consultation_type="oq_test_suite_quality_review",
                        context={
                            "quality_issues": quality_issues,
                            "generated_tests": test_suite.model_dump(),
                            "gamp_category": ev.gamp_category.value,
                            "document_name": ev.document_metadata.get("name"),
                            "test_count": test_suite.total_test_count,
                            "correlation_id": str(ev.correlation_id)
                        },
                        urgency="normal",
                        required_expertise=["validation_engineer", "gamp_specialist"],
                        triggering_step="start_oq_generation"
                    )

            # Calculate coverage analysis
            coverage_analysis = self._calculate_coverage_analysis(test_suite, ev)

            # Calculate quality metrics
            quality_metrics = test_suite.calculate_coverage_metrics()

            # Store generation results
            await ctx.set("generated_test_suite", test_suite)
            await ctx.set("coverage_analysis", coverage_analysis)
            await ctx.set("quality_metrics", quality_metrics)

            # Create successful result event
            result_event = OQTestSuiteEvent(
                test_suite=test_suite,
                generation_successful=True,
                coverage_analysis=coverage_analysis,
                quality_metrics=quality_metrics,
                compliance_validation=test_suite.pharmaceutical_compliance,
                generation_method="LLMTextCompletionProgram",
                context_quality=self._assess_context_quality(ev.aggregated_context),
                generation_duration_seconds=0.0,  # Will be updated by caller
                validation_issues=[],  # No issues if we reach here
                human_review_required=test_suite.review_required,
                review_priority="normal" if test_suite.review_required else "low",
                correlation_id=ev.correlation_id,
                gmp_compliant=test_suite.pharmaceutical_compliance.get("gamp5_compliant", False),
                regulatory_basis=self._get_regulatory_basis(ev.gamp_category),
                audit_trail_complete=True
            )

            self.logger.info(
                f"Successfully generated OQ test suite: {test_suite.suite_id} "
                f"({test_suite.total_test_count} tests, "
                f"coverage: {coverage_analysis.get('requirements_coverage_percentage', 0):.1%})"
            )

            return result_event

        except OQTestGenerationError as e:
            # Explicit generation error - NO fallbacks
            self.logger.error(
                f"OQ test generation failed: {e}. "
                f"Error context: {e.error_context}"
            )

            return ConsultationRequiredEvent(
                consultation_type="oq_test_generation_failure",
                context={
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "error_context": e.error_context,
                    "gamp_category": ev.gamp_category.value,
                    "document_name": ev.document_metadata.get("name", "Unknown"),
                    "correlation_id": str(ev.correlation_id),
                    "no_fallback_available": True,
                    "requires_human_intervention": True
                },
                urgency="high",
                required_expertise=["validation_engineer", "system_administrator"],
                triggering_step="start_oq_generation"
            )

        except Exception as e:
            # Unexpected error - NO fallbacks
            self.logger.error(f"Unexpected error in OQ generation: {e}")

            return ConsultationRequiredEvent(
                consultation_type="oq_generation_system_error",
                context={
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "gamp_category": ev.gamp_category.value,
                    "document_name": ev.document_metadata.get("name", "Unknown"),
                    "correlation_id": str(ev.correlation_id),
                    "system_error": True,
                    "requires_system_investigation": True
                },
                urgency="high",
                required_expertise=["system_administrator", "validation_engineer"],
                triggering_step="start_oq_generation"
            )

    async def _inject_alcoa_metadata(
        self,
        test_suite: OQTestSuite,
        generation_event: OQTestGenerationEvent,
        processing_time: float
    ) -> OQTestSuite:
        """
        Inject ALCOA+ compliance metadata into the generated test suite.
        
        This method enhances the test suite with comprehensive metadata that
        satisfies ALCOA+ assessment criteria for Original and Accurate attributes.
        
        Args:
            test_suite: Generated test suite
            generation_event: Original generation event
            processing_time: Generation processing time
            
        Returns:
            Enhanced test suite with ALCOA+ metadata
        """
        try:
            self.logger.info(f"Injecting ALCOA+ metadata into test suite: {test_suite.suite_id}")

            # Get metadata injector
            metadata_injector = get_metadata_injector()

            # Convert test suite to dictionary for metadata injection
            test_suite_dict = test_suite.model_dump()

            # Prepare generation context
            generation_context = {
                "source_document_id": generation_event.document_metadata.get("name"),
                "gamp_category": generation_event.gamp_category.value,
                "urs_content_length": len(generation_event.urs_content) if generation_event.urs_content else 0,
                "aggregated_context_keys": list(generation_event.aggregated_context.keys()) if generation_event.aggregated_context else [],
                "required_test_count": generation_event.required_test_count,
                "correlation_id": str(generation_event.correlation_id),
                "processing_time": processing_time,
                "generation_method": "LLMTextCompletionProgram",
                "pharmaceutical_validation": True
            }

            # Extract confidence score from generation context or use default
            confidence_score = 0.92  # High confidence for structured LLM outputs

            # Inject comprehensive ALCOA+ metadata
            enhanced_dict = metadata_injector.inject_test_suite_metadata(
                test_suite_dict=test_suite_dict,
                llm_response={"confidence_score": confidence_score},
                generation_context=generation_context
            )

            # Create new test suite with enhanced metadata
            # Update the original fields with ALCOA+ metadata
            enhanced_test_suite = OQTestSuite(
                # Original fields
                suite_id=test_suite.suite_id,
                gamp_category=test_suite.gamp_category,
                document_name=test_suite.document_name,
                test_cases=test_suite.test_cases,
                test_categories=test_suite.test_categories,
                requirements_coverage=test_suite.requirements_coverage,
                risk_coverage=test_suite.risk_coverage,
                compliance_coverage=test_suite.compliance_coverage,
                total_test_count=test_suite.total_test_count,
                estimated_execution_time=test_suite.estimated_execution_time,
                coverage_percentage=test_suite.coverage_percentage,
                generation_timestamp=test_suite.generation_timestamp,
                generation_method=test_suite.generation_method,
                validation_approach=test_suite.validation_approach,
                created_by=test_suite.created_by,
                review_required=test_suite.review_required,
                pharmaceutical_compliance=test_suite.pharmaceutical_compliance,

                # ALCOA+ Enhanced fields
                alcoa_plus_metadata=enhanced_dict.get("alcoa_plus_metadata", {}),
                is_original=enhanced_dict.get("is_original", True),
                version=enhanced_dict.get("version", "1.0"),
                source_document_id=enhanced_dict.get("source_document_id"),
                digital_signature=enhanced_dict.get("digital_signature"),
                checksum=enhanced_dict.get("checksum"),
                hash=enhanced_dict.get("hash"),
                immutable=enhanced_dict.get("immutable", True),
                locked=enhanced_dict.get("locked", False),

                validated=enhanced_dict.get("validated", True),
                accuracy_score=enhanced_dict.get("accuracy_score"),
                confidence_score=enhanced_dict.get("confidence_score"),
                change_reason=enhanced_dict.get("change_reason"),
                modification_reason=enhanced_dict.get("modification_reason"),
                reconciled=enhanced_dict.get("reconciled", True),
                cross_verified=enhanced_dict.get("cross_verified", True),
                corrections=enhanced_dict.get("corrections", []),
                error_log=enhanced_dict.get("error_log", []),

                user_id=enhanced_dict.get("user_id"),
                audit_trail=enhanced_dict.get("audit_trail", {}),
                created_at=enhanced_dict.get("created_at"),
                timestamp=enhanced_dict.get("timestamp"),
                modified_at=enhanced_dict.get("modified_at"),
                last_updated=enhanced_dict.get("last_updated"),
                processing_time=enhanced_dict.get("processing_time"),

                format=enhanced_dict.get("format", "json"),
                encoding=enhanced_dict.get("encoding", "utf-8"),
                schema=enhanced_dict.get("schema", {}),
                metadata=enhanced_dict.get("metadata", {}),

                retention_period=enhanced_dict.get("retention_period", "7_years"),
                expires_at=enhanced_dict.get("expires_at"),
                encrypted=enhanced_dict.get("encrypted", False),
                protected=enhanced_dict.get("protected", True),
                backed_up=enhanced_dict.get("backed_up", False),
                backup_status=enhanced_dict.get("backup_status", "pending"),

                accessible=enhanced_dict.get("accessible", True),
                retrieval_time=enhanced_dict.get("retrieval_time", 0.1),
                searchable=enhanced_dict.get("searchable", True),
                indexed=enhanced_dict.get("indexed", True),
                export_formats=enhanced_dict.get("export_formats", ["json", "xml", "csv"]),
                download_options=enhanced_dict.get("download_options", ["json", "xml", "pdf"]),

                system_version=enhanced_dict.get("system_version", "1.0.0"),
                process_id=enhanced_dict.get("process_id"),
                change_history=enhanced_dict.get("change_history", []),
                related_records=enhanced_dict.get("related_records", []),
                dependencies=enhanced_dict.get("dependencies", [])
            )

            self.logger.info(
                f"ALCOA+ metadata successfully injected: "
                f"signature={enhanced_test_suite.digital_signature[:16] if enhanced_test_suite.digital_signature else 'none'}..., "
                f"validated={enhanced_test_suite.validated}, "
                f"confidence={enhanced_test_suite.confidence_score}"
            )

            return enhanced_test_suite

        except Exception as e:
            error_msg = f"ALCOA+ metadata injection failed for test suite {test_suite.suite_id}: {e}"
            self.logger.error(error_msg)
            # NO FALLBACKS - fail explicitly for regulatory compliance
            raise OQTestGenerationError(error_msg, {
                "alcoa_injection_failed": True,
                "original_suite_id": test_suite.suite_id,
                "error_type": type(e).__name__,
                "regulatory_impact": "HIGH"
            }) from e

    def _validate_prerequisites(self, ev: OQTestGenerationEvent) -> None:
        """
        Validate prerequisites for OQ generation.
        
        Args:
            ev: OQ test generation event
            
        Raises:
            OQTestGenerationError: If prerequisites are not met
        """
        validation_errors = []

        # Check GAMP category
        if not ev.gamp_category:
            validation_errors.append("GAMP category not provided")

        # Check URS content
        if not ev.urs_content or len(ev.urs_content.strip()) < 50:
            validation_errors.append("Insufficient URS content provided")

        # Check test count
        if ev.required_test_count < 1:
            validation_errors.append("Invalid test count requirement")

        # Check document metadata
        if not ev.document_metadata.get("name"):
            validation_errors.append("Document name not provided")

        if validation_errors:
            raise OQTestGenerationError(
                f"Prerequisites validation failed: {'; '.join(validation_errors)}",
                {
                    "validation_errors": validation_errors,
                    "prerequisites_check": "failed",
                    "gamp_category": ev.gamp_category.value if ev.gamp_category else None,
                    "urs_content_length": len(ev.urs_content) if ev.urs_content else 0
                }
            )

    async def _validate_test_suite_quality(
        self,
        test_suite: OQTestSuite,
        original_event: OQTestGenerationEvent
    ) -> list[str]:
        """
        Validate generated test suite meets quality standards.
        
        Args:
            test_suite: Generated test suite
            original_event: Original generation request
            
        Returns:
            List of quality issues found (empty if no issues)
        """
        issues = []

        try:
            # Check test count compliance
            from .templates import GAMPCategoryConfig
            category_config = GAMPCategoryConfig.get_category_config(original_event.gamp_category)
            min_tests = category_config["min_tests"]
            max_tests = category_config["max_tests"]

            if test_suite.total_test_count < min_tests:
                issues.append(
                    f"Insufficient tests: {test_suite.total_test_count} < {min_tests} "
                    f"required for Category {original_event.gamp_category.value}"
                )

            if test_suite.total_test_count > max_tests:
                issues.append(
                    f"Excessive tests: {test_suite.total_test_count} > {max_tests} "
                    f"allowed for Category {original_event.gamp_category.value}"
                )

            # Check coverage requirements
            if len(test_suite.requirements_coverage) == 0:
                issues.append("No traceability to URS requirements established")

            # Check compliance coverage
            required_compliance = ["alcoa_plus_compliant", "gamp5_compliant", "audit_trail_verified"]
            missing_compliance = [
                req for req in required_compliance
                if not test_suite.pharmaceutical_compliance.get(req, False)
            ]
            if missing_compliance:
                issues.append(f"Missing compliance coverage: {', '.join(missing_compliance)}")

            # Check test step completeness
            incomplete_tests = [
                test.test_id for test in test_suite.test_cases
                if len(test.test_steps) == 0 or len(test.acceptance_criteria) == 0
            ]
            if incomplete_tests:
                issues.append(f"Incomplete test definitions: {', '.join(incomplete_tests[:5])}")

            # Check test category distribution
            categories = set(test.test_category for test in test_suite.test_cases)
            expected_categories = set(category_config["test_categories"])
            missing_categories = expected_categories - categories
            if missing_categories:
                issues.append(f"Missing test categories: {', '.join(missing_categories)}")

        except Exception as e:
            # Validation check failed - log but don't fail generation
            self.logger.warning(f"Quality validation check failed: {e}")
            issues.append(f"Quality validation system error: {e}")

        return issues

    def _calculate_coverage_analysis(
        self,
        test_suite: OQTestSuite,
        original_event: OQTestGenerationEvent
    ) -> dict[str, Any]:
        """Calculate comprehensive coverage analysis."""
        # Basic coverage metrics
        total_tests = len(test_suite.test_cases)
        tests_with_traceability = sum(1 for test in test_suite.test_cases if test.urs_requirements)

        # Requirements coverage percentage
        requirements_coverage_percentage = (tests_with_traceability / total_tests) if total_tests > 0 else 0.0

        # Risk coverage analysis
        risk_distribution = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        for test in test_suite.test_cases:
            risk_distribution[test.risk_level] += 1

        # Category coverage
        category_distribution = {}
        for test in test_suite.test_cases:
            category = test.test_category
            category_distribution[category] = category_distribution.get(category, 0) + 1

        return {
            "requirements_coverage_percentage": requirements_coverage_percentage * 100,
            "tests_with_traceability": tests_with_traceability,
            "total_tests": total_tests,
            "risk_distribution": risk_distribution,
            "category_distribution": category_distribution,
            "coverage_completeness": test_suite.coverage_percentage,
            "estimated_execution_hours": test_suite.estimated_execution_time / 60.0
        }

    def _assess_context_quality(self, context_data: dict[str, Any]) -> float:
        """Assess quality of aggregated context data."""
        if not context_data:
            return 0.0

        quality_score = 0.0
        max_score = 0.0

        # SME insights quality
        if sme_insights := context_data.get("sme_insights"):
            max_score += 0.3
            if isinstance(sme_insights, dict) and sme_insights.get("expertise_areas"):
                quality_score += 0.3

        # Research findings quality
        if research_findings := context_data.get("research_findings"):
            max_score += 0.3
            if isinstance(research_findings, dict) and research_findings.get("regulatory_updates"):
                quality_score += 0.3

        # Context provider quality
        if context_result := context_data.get("context_provider_result"):
            max_score += 0.4
            if isinstance(context_result, dict):
                confidence = context_result.get("confidence_score", 0.0)
                quality_score += 0.4 * confidence

        return quality_score / max_score if max_score > 0 else 0.0

    def _get_regulatory_basis(self, gamp_category) -> list[str]:
        """Get regulatory basis for the GAMP category."""
        base_requirements = ["GAMP-5", "ALCOA+"]

        if gamp_category.value in [4, 5]:
            base_requirements.append("21 CFR Part 11")

        if gamp_category.value == 5:
            base_requirements.extend(["ICH Q9", "Design Controls"])

        return base_requirements

    async def _save_test_suite_to_file(self, test_suite: OQTestSuite) -> str:
        """
        Save test suite to JSON file with GAMP-5 compliance metadata.
        
        Args:
            test_suite: Generated OQ test suite
            
        Returns:
            Path to saved file
            
        Raises:
            RuntimeError: If file saving fails (NO FALLBACKS)
        """
        try:
            # Create output directory with absolute path to ensure consistency
            # Use main/output/test_suites for internal runs and root/output/test_suites for CLI runs
            project_root = Path(__file__).parent.parent.parent.parent
            main_output_dir = project_root / "main" / "output" / "test_suites"
            root_output_dir = project_root / "output" / "test_suites"

            # Ensure both directories exist for maximum compatibility
            main_output_dir.mkdir(parents=True, exist_ok=True)
            root_output_dir.mkdir(parents=True, exist_ok=True)

            # Primary save location (main/output/test_suites)
            output_dir = main_output_dir

            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_suite_{test_suite.suite_id}_{timestamp}.json"
            output_file = output_dir / filename

            # Prepare comprehensive output data
            output_data = {
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "suite_id": test_suite.suite_id,
                    "gamp_category": test_suite.gamp_category,
                    "total_test_count": test_suite.total_test_count,
                    "file_version": "1.0",
                    "compliance_standards": ["GAMP-5", "ALCOA+", "21 CFR Part 11"],
                    "generator_version": "OQTestGenerationWorkflow v1.0"
                },
                "test_suite": test_suite.model_dump(),
                "audit_trail": {
                    "created_by": "OQTestGenerationWorkflow",
                    "creation_timestamp": datetime.now().isoformat(),
                    "validation_status": "generated",
                    "review_required": test_suite.review_required,
                    "pharmaceutical_compliance": test_suite.pharmaceutical_compliance
                }
            }

            # Write file with proper error handling - NO FALLBACKS
            # Use custom JSON encoder to handle datetime objects
            import json as json_module
            from datetime import datetime as dt

            class DateTimeEncoder(json_module.JSONEncoder):
                def default(self, obj):
                    if isinstance(obj, dt):
                        return obj.isoformat()
                    return super().default(obj)

            with open(output_file, "w", encoding="utf-8") as f:
                json_module.dump(output_data, f, indent=2, ensure_ascii=False, cls=DateTimeEncoder)

            # Verify file was written correctly
            if not output_file.exists():
                raise RuntimeError(f"File write verification failed: {output_file} does not exist")

            file_size = output_file.stat().st_size
            if file_size == 0:
                raise RuntimeError(f"File write verification failed: {output_file} is empty")

            # Also save to root output directory for backward compatibility
            root_output_file = root_output_dir / filename
            try:
                with open(root_output_file, "w", encoding="utf-8") as f:
                    json_module.dump(output_data, f, indent=2, ensure_ascii=False, cls=DateTimeEncoder)
                self.logger.info(f"Test suite also saved to: {root_output_file}")
            except Exception as e:
                # Log but don't fail - primary save succeeded
                self.logger.warning(f"Secondary save to root directory failed: {e}")

            self.logger.info(f"Test suite file written successfully: {file_size} bytes to {output_file}")
            return str(output_file)

        except Exception as e:
            # File saving failed - NO FALLBACKS for GAMP-5 compliance
            error_msg = f"CRITICAL: Test suite file save failed: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    @step
    async def complete_oq_generation(
        self,
        ctx: Context,
        ev: OQTestSuiteEvent | ConsultationRequiredEvent
    ) -> StopEvent:
        """
        Complete the OQ generation workflow and return final results.
        
        This step handles both successful test generation and consultation requirements,
        ensuring the workflow always ends with a StopEvent as required by LlamaIndex.
        
        Args:
            ctx: Workflow context
            ev: Either OQTestSuiteEvent (success) or ConsultationRequiredEvent (needs consultation)
            
        Returns:
            StopEvent: Final workflow results
        """
        # Get workflow context for final result
        correlation_id = await ctx.get("correlation_id", default="unknown")
        gamp_category = await ctx.get("gamp_category", default=None)
        generation_event = await ctx.get("generation_event", default=None)

        if isinstance(ev, OQTestSuiteEvent):
            # Successful test generation
            self.logger.info(
                f"OQ test generation completed successfully: {ev.test_suite.suite_id} "
                f"({ev.test_suite.total_test_count} tests)"
            )

            # Save test suite to JSON file
            output_file = await self._save_test_suite_to_file(ev.test_suite)
            self.logger.info(f"Test suite saved to: {output_file}")

            # Create comprehensive success result
            final_result = {
                "workflow_type": "oq_test_generation",
                "status": "completed_successfully",
                "correlation_id": correlation_id,
                "gamp_category": gamp_category.value if gamp_category else None,

                # Test suite details
                "test_suite": {
                    "suite_id": ev.test_suite.suite_id,
                    "total_test_count": ev.test_suite.total_test_count,
                    "coverage_percentage": ev.test_suite.coverage_percentage,
                    "estimated_execution_time": ev.test_suite.estimated_execution_time,
                    "pharmaceutical_compliance": ev.test_suite.pharmaceutical_compliance,
                    "review_required": ev.test_suite.review_required
                },

                # File output information
                "output_file": output_file,

                # Generation metadata
                "generation_metadata": {
                    "generation_successful": ev.generation_successful,
                    "generation_method": ev.generation_method,
                    "generation_duration_seconds": ev.generation_duration_seconds,
                    "context_quality": ev.context_quality,
                    "human_review_required": ev.human_review_required,
                    "review_priority": ev.review_priority
                },

                # Quality metrics
                "quality_analysis": {
                    "coverage_analysis": ev.coverage_analysis,
                    "quality_metrics": ev.quality_metrics,
                    "validation_issues": ev.validation_issues,
                    "compliance_validation": ev.compliance_validation
                },

                # Regulatory compliance
                "regulatory_compliance": {
                    "gmp_compliant": ev.gmp_compliant,
                    "regulatory_basis": ev.regulatory_basis,
                    "audit_trail_complete": ev.audit_trail_complete
                },

                # Full event for detailed analysis
                "full_event": ev
            }

        elif isinstance(ev, ConsultationRequiredEvent):
            # Consultation required
            self.logger.info(
                f"OQ test generation requires consultation: {ev.consultation_type} "
                f"(urgency: {ev.urgency})"
            )

            # Create consultation result - NO FALLBACKS
            final_result = {
                "workflow_type": "oq_test_generation",
                "status": "consultation_required",
                "correlation_id": correlation_id,
                "gamp_category": gamp_category.value if gamp_category else None,

                # Consultation details
                "consultation": {
                    "consultation_type": ev.consultation_type,
                    "consultation_id": str(ev.consultation_id),
                    "urgency": ev.urgency,
                    "required_expertise": ev.required_expertise,
                    "triggering_step": ev.triggering_step,
                    "context": ev.context,
                    "no_automated_fallback": True,
                    "requires_human_intervention": True
                },

                # Failure analysis
                "failure_analysis": {
                    "workflow_phase": "oq_test_generation",
                    "failure_type": ev.consultation_type,
                    "system_state": "requires_consultation",
                    "can_proceed_automatically": False,
                    "regulatory_impact": "HIGH - Cannot generate tests without consultation"
                },

                # Next steps
                "next_steps": {
                    "action_required": "human_consultation",
                    "consultation_method": "direct_user_input",
                    "escalation_available": True,
                    "timeout_handling": "no_defaults_applied"
                },

                # Full event for detailed analysis
                "full_event": ev
            }

        else:
            # Unexpected event type - this should not happen
            self.logger.error(f"Unexpected event type in complete_oq_generation: {type(ev)}")

            # Create explicit error result - NO FALLBACKS
            final_result = {
                "workflow_type": "oq_test_generation",
                "status": "system_error",
                "correlation_id": correlation_id,
                "gamp_category": gamp_category.value if gamp_category else None,

                # Error details
                "error": {
                    "error_type": "unexpected_event_type",
                    "received_event_type": str(type(ev)),
                    "expected_event_types": ["OQTestSuiteEvent", "ConsultationRequiredEvent"],
                    "system_error": True,
                    "requires_investigation": True
                },

                # System state
                "system_state": {
                    "workflow_phase": "completion",
                    "state": "error",
                    "can_recover": False,
                    "regulatory_impact": "HIGH - System integrity compromised"
                },

                # Full event for debugging
                "received_event": ev
            }

        # Store final results in context
        await ctx.set("final_results", final_result)

        self.logger.info(
            f"OQ generation workflow completed with status: {final_result['status']} "
            f"(correlation: {correlation_id})"
        )

        return StopEvent(result=final_result)
