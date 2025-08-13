"""
GAMP-5 Categorization Workflow - LlamaIndex Implementation

This module implements the GAMP-5 categorization workflow following the 
LlamaIndex Workflow pattern. It provides event-driven categorization
with error handling, confidence scoring, and human consultation triggers.
"""

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

from llama_index.core.workflow import Context, StartEvent, StopEvent, Workflow, step
from src.agents.categorization import (
    create_gamp_categorization_agent,
)
from src.agents.categorization.agent import categorize_with_structured_output
from src.core.events import (
    ConsultationRequiredEvent,
    DocumentProcessedEvent,
    ErrorRecoveryEvent,
    GAMPCategorizationEvent,
    GAMPCategory,
    URSIngestionEvent,
    WorkflowCompletionEvent,
)
from src.monitoring.phoenix_config import (
    enhance_workflow_span_with_compliance,
    get_current_span,
)


class GAMPCategorizationWorkflow(Workflow):
    """
    Workflow for GAMP-5 software categorization.
    
    This workflow processes URS documents to determine their GAMP-5 category,
    which drives the validation rigor for pharmaceutical test generation.
    
    Workflow steps:
    1. Ingest URS document (StartEvent or URSIngestionEvent)
    2. Perform categorization with confidence scoring
    3. Handle errors with Category 5 fallback
    4. Trigger human consultation if needed
    5. Return categorization result (StopEvent)
    """

    def __init__(
        self,
        timeout: int = 300,
        verbose: bool = False,
        enable_error_handling: bool = True,
        confidence_threshold: float = 0.40,
        retry_attempts: int = 2,
        enable_document_processing: bool = False
    ):
        """
        Initialize the categorization workflow.
        
        Args:
            timeout: Maximum time to wait for workflow completion
            verbose: Enable verbose logging
            enable_error_handling: Enable comprehensive error handling
            confidence_threshold: Minimum confidence before triggering review
            retry_attempts: Number of retry attempts on failure
            enable_document_processing: Enable LlamaParse document processing
        """
        super().__init__(timeout=timeout, verbose=verbose)
        self.enable_error_handling = enable_error_handling
        self.confidence_threshold = confidence_threshold
        self.retry_attempts = retry_attempts
        self.verbose = verbose  # Store verbose flag
        self.enable_document_processing = enable_document_processing
        self.logger = logging.getLogger(__name__)

        # Initialize categorization agent
        self.categorization_agent = None
        self._initialize_agent()

        # Initialize document processor if enabled
        self.document_processor = None
        if self.enable_document_processing:
            self._initialize_document_processor()

    def _initialize_agent(self) -> None:
        """Initialize the categorization agent."""
        try:
            self.categorization_agent = create_gamp_categorization_agent(
                enable_error_handling=self.enable_error_handling,
                confidence_threshold=self.confidence_threshold,
                verbose=self.verbose
            )
            self.logger.info("Categorization agent initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize categorization agent: {e}")
            raise

    def _initialize_document_processor(self) -> None:
        """Initialize the document processor if enabled."""
        try:
            from src.document_processing import DocumentProcessor
            self.document_processor = DocumentProcessor(verbose=self.verbose)
            self.logger.info("Document processor initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize document processor: {e}")
            # Document processing is optional, so just log the error
            self.enable_document_processing = False

    @step
    async def start(self, ctx: Context, ev: StartEvent) -> URSIngestionEvent:
        """
        Start the categorization workflow.
        
        This step handles both direct StartEvent (with URS content) and
        converts it to URSIngestionEvent for processing.
        
        Args:
            ctx: Workflow context
            ev: Start event containing URS document data
            
        Returns:
            URSIngestionEvent for categorization processing
        """
        # Extract URS data from StartEvent
        urs_content = getattr(ev, "urs_content", "")
        document_name = getattr(ev, "document_name", "unknown.urs")
        document_version = getattr(ev, "document_version", "1.0")
        author = getattr(ev, "author", "system")
        digital_signature = getattr(ev, "digital_signature", None)

        # Store workflow metadata in context
        await ctx.set("workflow_start_time", datetime.now(UTC))
        await ctx.set("document_metadata", {
            "name": document_name,
            "version": document_version,
            "author": author,
            "content_length": len(urs_content)
        })

        # Enhance current span with pharmaceutical compliance metadata
        current_span = get_current_span()
        if current_span:
            enhance_workflow_span_with_compliance(
                current_span,
                workflow_type="gamp5_categorization",
                document_name=document_name,
                document_version=document_version,
                workflow_phase="start",
                pharmaceutical_process="categorization",
                gamp_category_determination=True,
                regulatory_significance="critical"
            )

        # Log workflow start
        self.logger.info(f"Starting GAMP-5 categorization for document: {document_name}")

        # Create URSIngestionEvent
        urs_event = URSIngestionEvent(
            urs_content=urs_content,
            document_name=document_name,
            document_version=document_version,
            author=author,
            digital_signature=digital_signature
        )

        # Emit event to stream for logging
        ctx.write_event_to_stream(urs_event)

        return urs_event

    @step
    async def process_document(
        self,
        ctx: Context,
        ev: URSIngestionEvent
    ) -> DocumentProcessedEvent | None:
        """
        Process document with LlamaParse if enabled.
        
        This optional step processes the document to extract structured data
        including sections, metadata, charts, and requirements.
        
        Args:
            ctx: Workflow context
            ev: URS ingestion event
            
        Returns:
            DocumentProcessedEvent if processing enabled and successful,
            None if processing disabled (allows original event to continue)
        """
        # If document processing is not enabled, skip this step
        if not self.enable_document_processing or not self.document_processor:
            self.logger.info("Document processing not enabled, skipping processing step")
            return None  # Let original URSIngestionEvent continue to categorization

        self.logger.info(f"Processing document: {ev.document_name}")

        try:
            # Check if content is file path or actual content
            from pathlib import Path
            if ev.urs_content.startswith("/") or "\\" in ev.urs_content[:10]:
                # Likely a file path
                file_path = Path(ev.urs_content)
                if file_path.exists():
                    # Process from file
                    result = self.document_processor.process_document(
                        file_path=file_path,
                        document_name=ev.document_name,
                        document_version=ev.document_version,
                        author=ev.author
                    )
                else:
                    # Treat as content - create temp file
                    result = await self._process_from_content(ev)
            else:
                # Process from content
                result = await self._process_from_content(ev)

            # Store processed document in context
            await ctx.set("processed_document", result)

            # Create DocumentProcessedEvent
            doc_event = DocumentProcessedEvent(
                document_id=result["document_id"],
                document_name=ev.document_name,
                document_version=ev.document_version,
                metadata=result["metadata"],
                content=result["content"],
                sections=result["sections"],
                charts=result["charts"],
                tables=result["tables"],
                requirements=result["requirements"],
                processing_info=result["processing_info"]
            )

            # Emit document processed event to stream
            ctx.write_event_to_stream(doc_event)

            return doc_event

        except Exception as e:
            self.logger.warning(f"Document processing failed: {e}, continuing with raw content")
            # On failure, skip processing step
            return None

    async def _process_from_content(self, ev: URSIngestionEvent) -> dict[str, Any]:
        """Process document from raw content."""
        import tempfile
        from pathlib import Path

        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".txt",
            delete=False
        ) as tmp_file:
            tmp_file.write(ev.urs_content)
            tmp_path = Path(tmp_file.name)

        try:
            # Process temporary file
            result = self.document_processor.process_document(
                file_path=tmp_path,
                document_name=ev.document_name,
                document_version=ev.document_version,
                author=ev.author,
                use_cache=False  # Don't cache temporary files
            )
        finally:
            # Clean up temporary file
            tmp_path.unlink(missing_ok=True)

        return result

    @step
    async def categorize_document(
        self,
        ctx: Context,
        ev: URSIngestionEvent | DocumentProcessedEvent
    ) -> GAMPCategorizationEvent | ErrorRecoveryEvent:
        """
        Perform GAMP-5 categorization on the URS document.
        
        This step uses the categorization agent to analyze the document
        and determine its GAMP category with confidence scoring.
        
        Enhanced with comprehensive data transformation tracking for audit trail.
        
        Args:
            ctx: Workflow context
            ev: URS ingestion event
            
        Returns:
            GAMPCategorizationEvent or ErrorRecoveryEvent on failure
        """
        # Initialize comprehensive audit trail for data transformation tracking
        from src.core.audit_trail import get_audit_trail
        audit_trail = get_audit_trail()
        
        # Capture input data transformation
        input_data = {
            "event_type": type(ev).__name__,
            "urs_content": ev.urs_content if hasattr(ev, 'urs_content') else None,
            "document_name": getattr(ev, 'document_name', 'unknown'),
            "content_length": len(ev.urs_content) if hasattr(ev, 'urs_content') and ev.urs_content else 0,
            "input_timestamp": datetime.now(UTC).isoformat()
        }
        # Store event in context
        await ctx.set("categorization_input_event", ev)

        # Extract content based on event type
        if isinstance(ev, DocumentProcessedEvent):
            # Use processed document - create formatted input
            urs_content = self._create_categorization_input(ev)
            document_name = ev.document_name
            author = ev.metadata.get("author", "system")
            self.logger.info(f"Categorizing processed document: {document_name}")
        else:
            # Use raw URS content
            urs_content = ev.urs_content
            document_name = ev.document_name
            author = ev.author
            self.logger.info(f"Categorizing raw document: {document_name}")
        
        # Validate URS content is not empty
        if not urs_content or not urs_content.strip():
            self.logger.error(f"Empty URS content for document: {document_name}")
            # Log the event details for debugging
            self.logger.error(f"Event type: {type(ev).__name__}")
            if hasattr(ev, 'urs_content'):
                self.logger.error(f"Event urs_content length: {len(ev.urs_content) if ev.urs_content else 0}")
            
            # Return error recovery event with Category 5 fallback
            return ErrorRecoveryEvent(
                error_type="empty_content",
                error_message="URS content is empty or whitespace only",
                recovery_strategy="default_to_category_5",
                context={"document_name": document_name}
            )
        
        self.logger.info(f"URS content length: {len(urs_content)} characters")

        # Attempt categorization with retries
        last_error = None

        for attempt in range(self.retry_attempts):
            try:
                # Use structured output categorization for reliable results
                result = categorize_with_structured_output(
                    agent=self.categorization_agent,
                    urs_content=urs_content,
                    document_name=document_name
                )

                # Result is already a GAMPCategorizationEvent from LLM-based function
                categorization_event = result

                # Capture output data transformation
                output_data = {
                    "gamp_category": categorization_event.gamp_category.value,
                    "gamp_category_name": categorization_event.gamp_category.name,
                    "confidence_score": categorization_event.confidence_score,
                    "review_required": categorization_event.review_required,
                    "justification": categorization_event.justification[:500] + "..." if len(categorization_event.justification) > 500 else categorization_event.justification,
                    "risk_assessment": categorization_event.risk_assessment,
                    "categorized_by": categorization_event.categorized_by,
                    "output_timestamp": datetime.now(UTC).isoformat(),
                    "is_fallback": categorization_event.confidence_score == 0.0
                }

                # Log comprehensive data transformation
                audit_trail.log_data_transformation(
                    transformation_type="urs_to_gamp_categorization",
                    source_data=input_data,
                    target_data=output_data,
                    transformation_rules=[
                        "gamp_5_categorization_rules",
                        "llm_structured_output_analysis",
                        "confidence_scoring_validation",
                        "risk_assessment_generation"
                    ],
                    transformation_metadata={
                        "transformation_method": "llm_categorization_agent",
                        "agent_type": "gamp_categorization",
                        "workflow_step": "categorize_document",
                        "attempt_number": attempt + 1,
                        "processing_successful": True,
                        "confidence_threshold_met": categorization_event.confidence_score >= 0.5
                    },
                    workflow_step="gamp_categorization",
                    workflow_context={
                        "document_name": document_name,
                        "author": author,
                        "workflow_type": "GAMPCategorizationWorkflow",
                        "regulatory_standards": ["GAMP-5", "21_CFR_Part_11"]
                    }
                )

                # Store result in context
                await ctx.set("categorization_result", {
                    "category": categorization_event.gamp_category.value,
                    "confidence": categorization_event.confidence_score,
                    "review_required": categorization_event.review_required,
                    "justification": categorization_event.justification,
                    "is_fallback": categorization_event.confidence_score == 0.0  # Mark as fallback if confidence is 0
                })

                # Log success
                self.logger.info(
                    f"Categorization successful: Category {categorization_event.gamp_category.value}, "
                    f"Confidence: {categorization_event.confidence_score:.2%}"
                )

                # Emit event to stream for logging
                ctx.write_event_to_stream(categorization_event)

                return categorization_event

            except Exception as e:
                last_error = e
                self.logger.warning(
                    f"Categorization attempt {attempt + 1} failed: {e!s}"
                )

                # Store error in context
                await ctx.set(f"categorization_error_{attempt}", {
                    "error": str(e),
                    "attempt": attempt + 1,
                    "timestamp": datetime.now(UTC).isoformat()
                })

        # All retries failed - create error recovery event
        self.logger.error(
            f"Categorization failed after {self.retry_attempts} attempts"
        )

        error_event = ErrorRecoveryEvent(
            error_type="categorization_failure",
            error_message=f"Failed after {self.retry_attempts} attempts: {last_error!s}",
            error_context={
                "document_name": document_name,
                "document_version": getattr(ev, "document_version", "1.0"),
                "content_length": len(urs_content),
                "attempts": self.retry_attempts
            },
            recovery_strategy="fallback_to_category_5",
            recovery_actions=[
                "Log all error details",
                "Create Category 5 fallback",
                "Request human review",
                "Continue with conservative validation"
            ],
            failed_step="categorization",
            severity="high",
            auto_recoverable=True
        )

        # Emit error event to stream
        ctx.write_event_to_stream(error_event)

        return error_event

    @step
    async def handle_error_recovery(
        self,
        ctx: Context,
        ev: ErrorRecoveryEvent
    ) -> GAMPCategorizationEvent:
        """
        Handle categorization errors with conservative fallback.
        
        This step creates a Category 5 categorization event when
        the primary categorization fails.
        
        Args:
            ctx: Workflow context
            ev: Error recovery event
            
        Returns:
            GAMPCategorizationEvent with Category 5 fallback
        """
        # Get document metadata
        doc_metadata = await ctx.get("document_metadata", {})
        urs_event = await ctx.get("urs_ingestion_event", None)

        # Log error recovery
        self.logger.info(
            f"Executing error recovery for {doc_metadata.get('name', 'unknown')}"
        )

        # Create conservative fallback event
        fallback_event = GAMPCategorizationEvent(
            gamp_category=GAMPCategory.CATEGORY_5,
            confidence_score=0.0,
            justification=(
                f"Categorization failed: {ev.error_message}. "
                "Defaulting to Category 5 (Custom Applications) as the most "
                "conservative approach requiring full validation."
            ),
            risk_assessment={
                "software_type": "unknown",
                "risk_level": "high",
                "validation_rigor": "full",
                "error_details": ev.error_message,
                "recovery_strategy": ev.recovery_strategy
            },
            categorized_by=f"error_recovery_{doc_metadata.get('name', 'unknown')}",
            review_required=True
        )

        # Store fallback in context
        await ctx.set("categorization_result", {
            "category": 5,
            "confidence": 0.0,
            "review_required": True,
            "justification": fallback_event.justification,
            "is_fallback": True
        })

        # Emit fallback event to stream
        ctx.write_event_to_stream(fallback_event)

        return fallback_event

    @step
    async def check_consultation_required(
        self,
        ctx: Context,
        ev: GAMPCategorizationEvent
    ) -> WorkflowCompletionEvent:
        """
        Check if human consultation is required based on categorization results.
        
        This step evaluates the confidence score and review flag to determine
        if human expert review is needed.
        
        Args:
            ctx: Workflow context
            ev: Categorization event
            
        Returns:
            WorkflowCompletionEvent with optional consultation information
        """
        # Store categorization event in context for final step
        await ctx.set("final_categorization_event", ev)

        # Check if consultation is required
        consultation_event = None
        if ev.review_required:
            doc_metadata = await ctx.get("document_metadata", {})

            # Determine urgency based on confidence
            urgency = "high" if ev.confidence_score < 0.5 else "normal"

            # Log consultation requirement
            self.logger.info(
                f"Human consultation required for {doc_metadata.get('name', 'unknown')} "
                f"(confidence: {ev.confidence_score:.2%})"
            )

            consultation_event = ConsultationRequiredEvent(
                consultation_type="categorization_review",
                context={
                    "category": ev.gamp_category.value,
                    "confidence": ev.confidence_score,
                    "justification": ev.justification,
                    "document_name": doc_metadata.get("name", "unknown"),
                    "risk_assessment": ev.risk_assessment
                },
                urgency=urgency,
                required_expertise=["gamp_5_expert", "validation_specialist"],
                triggering_step="categorization"
            )

            # Emit consultation event to stream
            ctx.write_event_to_stream(consultation_event)

        # Create completion event
        completion_event = WorkflowCompletionEvent(
            consultation_event=consultation_event,
            ready_for_completion=True,
            triggering_step="check_consultation_required"
        )

        # Emit completion event to stream
        ctx.write_event_to_stream(completion_event)

        return completion_event

    @step
    async def complete_workflow(
        self,
        ctx: Context,
        ev: WorkflowCompletionEvent
    ) -> StopEvent:
        """
        Complete the categorization workflow.
        
        This final step packages all results and returns them via StopEvent.
        
        Args:
            ctx: Workflow context
            ev: Workflow completion event
            
        Returns:
            StopEvent with complete workflow results
        """
        # Get all workflow results
        categorization_event = await ctx.get("final_categorization_event")
        categorization_result = await ctx.get("categorization_result")
        workflow_start = await ctx.get("workflow_start_time")

        # Calculate workflow duration
        workflow_duration = (datetime.now(UTC) - workflow_start).total_seconds()

        # Build result dictionary
        result = {
            "categorization_event": categorization_event,
            "consultation_event": ev.consultation_event,
            "summary": {
                "category": categorization_result["category"],
                "confidence": categorization_result["confidence"],
                "review_required": categorization_result["review_required"],
                "is_fallback": categorization_result.get("is_fallback", False),
                "workflow_duration_seconds": workflow_duration
            }
        }

        # Log workflow completion
        self.logger.info(
            f"Workflow completed in {workflow_duration:.2f}s - "
            f"Category: {result['summary']['category']}, "
            f"Confidence: {result['summary']['confidence']:.2%}"
        )

        return StopEvent(result=result)

    def _create_categorization_event(
        self,
        result: Any,
        document_name: str,
        author: str
    ) -> GAMPCategorizationEvent:
        """
        Create GAMPCategorizationEvent from categorization result.
        
        Args:
            result: Categorization result object
            document_name: Name of the document
            author: Author of the document
            
        Returns:
            GAMPCategorizationEvent instance
        """
        # Extract risk assessment from result
        risk_assessment = {
            "software_type": getattr(result, "software_type", "unknown"),
            "risk_level": self._determine_risk_level(result.gamp_category),
            "validation_rigor": self._determine_validation_rigor(result.gamp_category),
            "confidence_factors": getattr(result, "confidence_factors", {})
        }

        # Create event
        return GAMPCategorizationEvent(
            gamp_category=result.gamp_category,
            confidence_score=result.confidence_score,
            justification=result.justification,
            risk_assessment=risk_assessment,
            categorized_by=f"gamp_categorization_workflow_{document_name}",
            review_required=result.review_required
        )

    def _create_categorization_input(self, processed_event: DocumentProcessedEvent) -> str:
        """
        Create formatted input for GAMP-5 categorization from processed document.
        
        Args:
            processed_event: Document processed event
            
        Returns:
            Formatted text suitable for categorization
        """
        lines = []

        # Add document header
        lines.append(f"DOCUMENT: {processed_event.document_name}")
        lines.append(f"VERSION: {processed_event.document_version}")
        lines.append(f"TYPE: {processed_event.metadata.get('document_type', 'URS')}")
        lines.append("")

        # Add high-importance sections
        high_importance_sections = [
            s for s in processed_event.sections
            if s.get("importance") == "high"
        ]

        if high_importance_sections:
            lines.append("## KEY SECTIONS")
            for section in high_importance_sections[:5]:  # Top 5 sections
                lines.append(f"\n### {section['title']}")
                # Limit content to 500 chars per section
                content = section["content"][:500]
                if len(section["content"]) > 500:
                    content += "..."
                lines.append(content)
            lines.append("")

        # Add requirements summary
        if processed_event.requirements:
            lines.append("## REQUIREMENTS SUMMARY")
            lines.append(f"Total Requirements: {len(processed_event.requirements)}")
            lines.append("\nKey Requirements:")
            for req in processed_event.requirements[:10]:  # Top 10
                lines.append(f"- [{req['id']}] {req['text']}")
            lines.append("")

        # Add technical indicators
        lines.append("## TECHNICAL INDICATORS")

        # From processing info
        proc_info = processed_event.processing_info
        lines.append(f"- Page Count: {proc_info.get('page_count', 0)}")
        lines.append(f"- Contains Charts/Diagrams: {proc_info.get('chart_count', 0) > 0}")
        lines.append(f"- Contains Tables: {proc_info.get('table_count', 0) > 0}")
        lines.append(f"- Requirement Count: {proc_info.get('requirement_count', 0)}")

        # From metadata
        if processed_event.metadata.get("compliance_standards"):
            lines.append(f"- Compliance Standards: {', '.join(processed_event.metadata['compliance_standards'])}")

        # Analyze content for software indicators
        content_lower = processed_event.content.lower()
        software_indicators = {
            "LIMS": "lims" in content_lower or "laboratory information" in content_lower,
            "ERP": "erp" in content_lower or "enterprise resource" in content_lower,
            "MES": "mes" in content_lower or "manufacturing execution" in content_lower,
            "Custom Development": "custom" in content_lower or "bespoke" in content_lower,
            "COTS": "cots" in content_lower or "off-the-shelf" in content_lower,
            "Configuration": "configuration" in content_lower or "configure" in content_lower
        }

        lines.append("\nSoftware Type Indicators:")
        for indicator, present in software_indicators.items():
            if present:
                lines.append(f"- {indicator}: Yes")

        # Add chart summary if relevant
        if processed_event.charts:
            lines.append("\n## VISUAL ELEMENTS")
            chart_types = {}
            for chart in processed_event.charts:
                chart_type = chart.get("type", "unknown")
                chart_types[chart_type] = chart_types.get(chart_type, 0) + 1

            for chart_type, count in chart_types.items():
                lines.append(f"- {chart_type}: {count}")

        return "\n".join(lines)

    def _determine_risk_level(self, category: GAMPCategory) -> str:
        """Determine risk level based on GAMP category."""
        risk_mapping = {
            GAMPCategory.CATEGORY_1: "low",
            GAMPCategory.CATEGORY_3: "low",
            GAMPCategory.CATEGORY_4: "medium",
            GAMPCategory.CATEGORY_5: "high"
        }
        return risk_mapping.get(category, "high")

    def _determine_validation_rigor(self, category: GAMPCategory) -> str:
        """Determine validation rigor based on GAMP category."""
        rigor_mapping = {
            GAMPCategory.CATEGORY_1: "minimal",
            GAMPCategory.CATEGORY_3: "standard",
            GAMPCategory.CATEGORY_4: "enhanced",
            GAMPCategory.CATEGORY_5: "full"
        }
        return rigor_mapping.get(category, "full")


# Convenience function for running the workflow
async def run_categorization_workflow(
    urs_content: str,
    document_name: str,
    document_version: str = "1.0",
    author: str = "system",
    **kwargs
) -> dict[str, Any]:
    """
    Run the GAMP-5 categorization workflow.
    
    Args:
        urs_content: URS document content
        document_name: Name of the document
        document_version: Version of the document
        author: Author of the document
        **kwargs: Additional workflow configuration
        
    Returns:
        Dictionary with categorization results
    """
    # Create workflow instance
    workflow = GAMPCategorizationWorkflow(**kwargs)

    # Run workflow
    result = await workflow.run(
        urs_content=urs_content,
        document_name=document_name,
        document_version=document_version,
        author=author
    )

    return result


async def main():
    """Main entry point for testing the categorization workflow."""
    import logging
    from pathlib import Path

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Test with a sample document
    test_document_path = Path(__file__).parent.parent.parent.parent / "simple_test_data.md"

    if test_document_path.exists():
        print(f"📄 Loading test document: {test_document_path}")
        test_content = test_document_path.read_text()
    else:
        print("📝 Using default test content")
        test_content = """
        # Pharmaceutical System URS
        
        ## System Overview
        This document describes requirements for a Laboratory Information Management System (LIMS).
        
        ## Requirements
        - The system shall manage laboratory test results
        - The system shall ensure 21 CFR Part 11 compliance
        - The system shall provide audit trails for all data changes
        """

    print("\n🚀 Running GAMP-5 Categorization Workflow")
    print("=" * 60)

    try:
        # Run the workflow
        result = await run_categorization_workflow(
            urs_content=test_content,
            document_name="test_urs.md",
            enable_error_handling=True,
            verbose=True,
            confidence_threshold=0.60
        )

        # Display results
        if result:
            summary = result.get("summary", {})
            print("\n✅ Categorization Complete!")
            print(f"  - Category: {summary.get('category', 'Unknown')}")
            print(f"  - Confidence: {summary.get('confidence', 0):.1%}")
            print(f"  - Review Required: {summary.get('review_required', False)}")
            print(f"  - Is Fallback: {summary.get('is_fallback', False)}")
            print(f"  - Duration: {summary.get('workflow_duration_seconds', 0):.2f}s")

            # Show categorization details
            cat_event = result.get("categorization_event")
            if cat_event:
                print("\n📋 Categorization Details:")
                print(f"  - Justification: {cat_event.justification[:200]}...")
                if cat_event.risk_assessment:
                    print(f"  - Risk Level: {cat_event.risk_assessment.get('risk_level', 'Unknown')}")
                    print(f"  - Validation Approach: {cat_event.risk_assessment.get('validation_approach', 'Unknown')}")

            # Show consultation details if required
            consult_event = result.get("consultation_event")
            if consult_event:
                print("\n🤝 Consultation Required:")
                print(f"  - Type: {consult_event.consultation_type}")
                print(f"  - Urgency: {consult_event.urgency}")
                print(f"  - Required Expertise: {', '.join(consult_event.required_expertise)}")

        else:
            print("\n❌ Workflow failed to produce results")

    except Exception as e:
        print(f"\n❌ Error running workflow: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
