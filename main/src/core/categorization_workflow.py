"""
GAMP-5 Categorization Workflow - LlamaIndex Implementation

This module implements the GAMP-5 categorization workflow following the 
LlamaIndex Workflow pattern. It provides event-driven categorization
with error handling, confidence scoring, and human consultation triggers.
"""

from typing import Optional, Dict, Any, Union
from datetime import datetime, UTC
import logging

from llama_index.core.workflow import Workflow, StartEvent, StopEvent, Context, step
from llama_index.core.agent.workflow import FunctionAgent

from src.core.events import (
    URSIngestionEvent,
    GAMPCategorizationEvent,
    GAMPCategory,
    ErrorRecoveryEvent,
    ConsultationRequiredEvent,
    AgentRequestEvent,
    AgentResultEvent
)
from src.agents.categorization import (
    create_gamp_categorization_agent,
    categorize_with_structured_output,
    CategorizationWorkflowStep
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
        confidence_threshold: float = 0.60,
        retry_attempts: int = 2
    ):
        """
        Initialize the categorization workflow.
        
        Args:
            timeout: Maximum time to wait for workflow completion
            verbose: Enable verbose logging
            enable_error_handling: Enable comprehensive error handling
            confidence_threshold: Minimum confidence before triggering review
            retry_attempts: Number of retry attempts on failure
        """
        super().__init__(timeout=timeout, verbose=verbose)
        self.enable_error_handling = enable_error_handling
        self.confidence_threshold = confidence_threshold
        self.retry_attempts = retry_attempts
        self.verbose = verbose  # Store verbose flag
        self.logger = logging.getLogger(__name__)
        
        # Initialize categorization agent
        self.categorization_agent = None
        self._initialize_agent()
    
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
        urs_content = getattr(ev, 'urs_content', '')
        document_name = getattr(ev, 'document_name', 'unknown.urs')
        document_version = getattr(ev, 'document_version', '1.0')
        author = getattr(ev, 'author', 'system')
        digital_signature = getattr(ev, 'digital_signature', None)
        
        # Store workflow metadata in context
        await ctx.set("workflow_start_time", datetime.now(UTC))
        await ctx.set("document_metadata", {
            "name": document_name,
            "version": document_version,
            "author": author,
            "content_length": len(urs_content)
        })
        
        # Log workflow start
        self.logger.info(f"Starting GAMP-5 categorization for document: {document_name}")
        
        # Create and return URSIngestionEvent
        return URSIngestionEvent(
            urs_content=urs_content,
            document_name=document_name,
            document_version=document_version,
            author=author,
            digital_signature=digital_signature
        )
    
    @step
    async def categorize_document(
        self, 
        ctx: Context, 
        ev: URSIngestionEvent
    ) -> Union[GAMPCategorizationEvent, ErrorRecoveryEvent]:
        """
        Perform GAMP-5 categorization on the URS document.
        
        This step uses the categorization agent to analyze the document
        and determine its GAMP category with confidence scoring.
        
        Args:
            ctx: Workflow context
            ev: URS ingestion event
            
        Returns:
            GAMPCategorizationEvent or ErrorRecoveryEvent on failure
        """
        # Store ingestion event in context
        await ctx.set("urs_ingestion_event", ev)
        
        # Log categorization start
        self.logger.info(f"Categorizing document: {ev.document_name}")
        
        # Attempt categorization with retries
        last_error = None
        
        for attempt in range(self.retry_attempts):
            try:
                # Use structured output method for reliability
                result = categorize_with_structured_output(
                    agent=self.categorization_agent,
                    urs_content=ev.urs_content,
                    document_name=ev.document_name
                )
                
                # Create categorization event from result
                categorization_event = self._create_categorization_event(
                    result, ev.document_name, ev.author
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
                
                return categorization_event
                
            except Exception as e:
                last_error = e
                self.logger.warning(
                    f"Categorization attempt {attempt + 1} failed: {str(e)}"
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
        
        return ErrorRecoveryEvent(
            error_type="categorization_failure",
            error_message=f"Failed after {self.retry_attempts} attempts: {str(last_error)}",
            error_context={
                "document_name": ev.document_name,
                "document_version": ev.document_version,
                "content_length": len(ev.urs_content),
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
        
        return fallback_event
    
    @step
    async def check_consultation_required(
        self,
        ctx: Context,
        ev: GAMPCategorizationEvent
    ) -> Optional[ConsultationRequiredEvent]:
        """
        Check if human consultation is required based on categorization results.
        
        This step evaluates the confidence score and review flag to determine
        if human expert review is needed.
        
        Args:
            ctx: Workflow context
            ev: Categorization event
            
        Returns:
            ConsultationRequiredEvent if review needed, None otherwise
        """
        # Store categorization event in context for final step
        await ctx.set("final_categorization_event", ev)
        
        # Check if consultation is required
        if ev.review_required:
            doc_metadata = await ctx.get("document_metadata", {})
            
            # Determine urgency based on confidence
            urgency = "high" if ev.confidence_score < 0.5 else "normal"
            
            # Log consultation requirement
            self.logger.info(
                f"Human consultation required for {doc_metadata.get('name', 'unknown')} "
                f"(confidence: {ev.confidence_score:.2%})"
            )
            
            return ConsultationRequiredEvent(
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
        
        # No consultation needed
        return None
    
    @step
    async def complete_workflow(
        self,
        ctx: Context,
        ev: Optional[ConsultationRequiredEvent]
    ) -> StopEvent:
        """
        Complete the categorization workflow.
        
        This final step packages all results and returns them via StopEvent.
        
        Args:
            ctx: Workflow context
            ev: Optional consultation event
            
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
            "consultation_event": ev,
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
) -> Dict[str, Any]:
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