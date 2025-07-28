"""
Integration tests for GAMP-5 categorization workflow step.

Tests the integration of the categorization agent as a workflow step,
including proper event handling, error recovery, and state propagation.
"""

import os

import pytest
from llama_index.core.workflow import Context, StartEvent, StopEvent, Workflow, step
from src.agents.categorization.workflow_integration import (
    CategorizationWorkflowStep,
    categorization_workflow_step,
)
from src.core.events import (
    GAMPCategorizationEvent,
    GAMPCategory,
    URSIngestionEvent,
)


class MockContext(Context):
    """Mock context for testing without full workflow."""

    def __init__(self):
        self._storage = {}

    async def get(self, key: str, default=None):
        """Get value from context."""
        return self._storage.get(key, default)

    async def set(self, key: str, value: any, **kwargs):
        """Set value in context."""
        self._storage[key] = value

    def write_event_to_stream(self, event):
        """Mock event stream writing."""


class TestCategorizationWorkflowStep:
    """Test the CategorizationWorkflowStep class."""

    def test_initialization(self):
        """Test workflow step initialization."""
        step = CategorizationWorkflowStep(
            enable_error_handling=True,
            confidence_threshold=0.70,
            verbose=True,
            retry_attempts=3
        )

        assert step.enable_error_handling is True
        assert step.confidence_threshold == 0.70
        assert step.verbose is True
        assert step.retry_attempts == 3
        assert step.agent is None
        assert step.error_handler is None

    def test_output_schema(self):
        """Test output schema definition."""
        step = CategorizationWorkflowStep()
        schema = step.get_output_schema()

        # Verify schema structure
        assert schema["event_type"] == "GAMPCategorizationEvent"
        assert "fields" in schema
        assert "compliance" in schema

        # Verify key fields
        fields = schema["fields"]
        assert "gamp_category" in fields
        assert "confidence_score" in fields
        assert "justification" in fields
        assert "risk_assessment" in fields
        assert "review_required" in fields

        # Verify compliance flags
        compliance = schema["compliance"]
        assert compliance["alcoa_plus"] is True
        assert compliance["cfr_part_11"] is True
        assert compliance["gamp_5"] is True

    @pytest.mark.asyncio
    async def test_process_urs_document_success(self):
        """Test successful URS document processing."""
        # Skip if no API key
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OpenAI API key not available")

        step = CategorizationWorkflowStep(
            enable_error_handling=True,
            confidence_threshold=0.60,
            verbose=True
        )

        # Test with Category 1 infrastructure software
        urs_content = """
        Software Requirements for Data Center Infrastructure:
        - Operating system management and monitoring
        - Network infrastructure configuration
        - Hardware resource allocation
        - System backup and recovery utilities
        """

        context = MockContext()

        result = await step.process_urs_document(
            urs_content=urs_content,
            document_name="test_infrastructure.urs",
            document_version="1.0",
            author="test_user",
            context=context
        )

        # Verify result
        assert isinstance(result, GAMPCategorizationEvent)
        assert result.gamp_category in [GAMPCategory.CATEGORY_1, GAMPCategory.CATEGORY_3, GAMPCategory.CATEGORY_4, GAMPCategory.CATEGORY_5]
        assert 0.0 <= result.confidence_score <= 1.0
        assert result.justification != ""
        assert isinstance(result.risk_assessment, dict)
        assert result.categorized_by.startswith("gamp_categorization_agent_")

        # Verify context was updated
        stored_result = await context.get("categorization_result")
        assert stored_result is not None
        assert stored_result["category"] == result.gamp_category.value
        assert stored_result["confidence"] == result.confidence_score

    @pytest.mark.asyncio
    async def test_process_urs_document_with_retry(self):
        """Test URS processing with retry on failure."""
        step = CategorizationWorkflowStep(
            enable_error_handling=True,
            retry_attempts=2
        )

        # Test with invalid content that should trigger fallback
        urs_content = ""  # Empty content should fail

        result = await step.process_urs_document(
            urs_content=urs_content,
            document_name="empty.urs",
            document_version="1.0",
            author="test_user"
        )

        # Should return fallback Category 5
        assert result.gamp_category == GAMPCategory.CATEGORY_5
        assert result.confidence_score == 0.0
        # Check that it's a fallback due to error (either retry failure or tool error)
        assert ("FALLBACK TO CATEGORY 5" in result.justification or
                "failed after" in result.justification)
        assert result.review_required is True
        assert result.risk_assessment["risk_level"] == "high"
        assert result.risk_assessment["validation_rigor"] == "full"

    def test_risk_level_determination(self):
        """Test risk level determination logic."""
        step = CategorizationWorkflowStep()

        assert step._determine_risk_level(GAMPCategory.CATEGORY_1) == "low"
        assert step._determine_risk_level(GAMPCategory.CATEGORY_3) == "low"
        assert step._determine_risk_level(GAMPCategory.CATEGORY_4) == "medium"
        assert step._determine_risk_level(GAMPCategory.CATEGORY_5) == "high"

    def test_validation_rigor_determination(self):
        """Test validation rigor determination logic."""
        step = CategorizationWorkflowStep()

        assert step._determine_validation_rigor(GAMPCategory.CATEGORY_1) == "minimal"
        assert step._determine_validation_rigor(GAMPCategory.CATEGORY_3) == "standard"
        assert step._determine_validation_rigor(GAMPCategory.CATEGORY_4) == "enhanced"
        assert step._determine_validation_rigor(GAMPCategory.CATEGORY_5) == "full"


class TestWorkflowIntegration(Workflow):
    """Test workflow for integration testing."""

    @step
    async def process_urs(self, ctx: Context, ev: StartEvent) -> None:
        """Start workflow with URS ingestion."""
        # Create URS ingestion event
        urs_event = URSIngestionEvent(
            urs_content=ev.urs_content,
            document_name=ev.document_name,
            document_version=ev.document_version,
            author=ev.author,
            digital_signature=None
        )

        # Call categorization step
        result = await categorization_workflow_step(ctx, urs_event)

        # Unpack results
        categorization_event, error_event, consultation_event = result

        # Store results in context
        await ctx.set("categorization_event", categorization_event)
        await ctx.set("error_event", error_event)
        await ctx.set("consultation_event", consultation_event)

        # Return results
        return StopEvent(result={
            "categorization": categorization_event,
            "error": error_event,
            "consultation": consultation_event
        })


class TestCategorizationWorkflowStepFunction:
    """Test the workflow step function."""

    @pytest.mark.asyncio
    async def test_workflow_step_success(self):
        """Test successful workflow step execution."""
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OpenAI API key not available")

        # Create workflow instance
        workflow = TestWorkflowIntegration()

        # Test with clear Category 4 software
        result = await workflow.run(
            urs_content="""
            Requirements for Laboratory Information Management System (LIMS):
            - Configure sample tracking workflows
            - Set up user roles and permissions  
            - Configure report templates
            - Customize dashboard views
            - Integration with existing instruments
            """,
            document_name="lims_config.urs",
            document_version="2.0",
            author="lab_manager"
        )

        # Verify results
        assert "categorization" in result
        assert "error" in result
        assert "consultation" in result

        cat_event = result["categorization"]
        assert isinstance(cat_event, GAMPCategorizationEvent)
        assert cat_event.gamp_category in [GAMPCategory.CATEGORY_4, GAMPCategory.CATEGORY_5]

        # Should not have error event on success
        assert result["error"] is None

        # Consultation event depends on confidence
        if cat_event.review_required:
            assert result["consultation"] is not None
            assert result["consultation"].consultation_type == "categorization_review"
        else:
            assert result["consultation"] is None

    @pytest.mark.asyncio
    async def test_workflow_step_with_error(self):
        """Test workflow step with error handling."""
        # Create a minimal context for testing
        ctx = MockContext()

        # Create URS event with invalid content
        urs_event = URSIngestionEvent(
            urs_content="",  # Empty content should trigger error
            document_name="error_test.urs",
            document_version="1.0",
            author="test_user",
            digital_signature=None
        )

        # Call step function directly
        result = await categorization_workflow_step(ctx, urs_event)

        # Unpack results
        cat_event, error_event, consultation_event = result

        # Verify fallback categorization
        assert cat_event.gamp_category == GAMPCategory.CATEGORY_5
        assert cat_event.confidence_score == 0.0
        assert cat_event.review_required is True

        # Should NOT have error event because structured output handles errors internally
        # The error is converted to a fallback categorization event
        assert error_event is None  # No error event because error was handled internally

        # Should have consultation event due to review_required flag
        assert consultation_event is not None
        assert consultation_event.consultation_type == "categorization_review"
        # Urgency is high because confidence is 0.0 (< 0.5)
        assert consultation_event.urgency == "high"
        assert "gamp_5_expert" in consultation_event.required_expertise

    @pytest.mark.asyncio
    async def test_workflow_step_consultation_trigger(self):
        """Test consultation event triggering based on confidence."""
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OpenAI API key not available")

        ctx = MockContext()

        # Create URS with ambiguous content that might trigger low confidence
        urs_event = URSIngestionEvent(
            urs_content="""
            Generic software requirements:
            - Do some processing
            - Store some data
            - Generate reports
            """,
            document_name="ambiguous.urs",
            document_version="1.0",
            author="test_user",
            digital_signature=None
        )

        result = await categorization_workflow_step(ctx, urs_event)
        cat_event, error_event, consultation_event = result

        # If review is required, consultation event should be present
        if cat_event.review_required:
            assert consultation_event is not None
            assert consultation_event.consultation_type == "categorization_review"
            assert consultation_event.context["category"] == cat_event.gamp_category.value
            assert consultation_event.context["confidence"] == cat_event.confidence_score

            # Urgency based on confidence
            if cat_event.confidence_score < 0.5:
                assert consultation_event.urgency == "high"
            else:
                assert consultation_event.urgency == "normal"
        else:
            assert consultation_event is None


@pytest.mark.asyncio
async def test_full_workflow_integration():
    """Test full workflow integration with multiple steps."""
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OpenAI API key not available")

    class FullTestWorkflow(Workflow):
        """Extended workflow for comprehensive testing."""

        @step
        async def ingest_urs(self, ctx: Context, ev: StartEvent) -> URSIngestionEvent:
            """Ingest URS document."""
            return URSIngestionEvent(
                urs_content=ev.urs_content,
                document_name=ev.document_name,
                document_version=ev.document_version,
                author=ev.author,
                digital_signature="test_signature"
            )

        @step
        async def categorize(self, ctx: Context, ev: URSIngestionEvent) -> None:
            """Categorize the URS document."""
            result = await categorization_workflow_step(ctx, ev)
            cat_event, error_event, consultation_event = result

            # Store events
            await ctx.set("all_events", {
                "urs_ingestion": ev,
                "categorization": cat_event,
                "error": error_event,
                "consultation": consultation_event
            })

            # Simulate downstream processing
            if not error_event:
                await ctx.set("next_step", "planning")
            else:
                await ctx.set("next_step", "error_recovery")

            return StopEvent(result=await ctx.get("all_events"))

    # Run workflow
    workflow = FullTestWorkflow()
    result = await workflow.run(
        urs_content="""
        Requirements for Clinical Trial Management System:
        - Patient enrollment and randomization
        - Electronic data capture (EDC)
        - Adverse event reporting
        - Regulatory compliance tracking
        - Full 21 CFR Part 11 compliance required
        """,
        document_name="ctms.urs",
        document_version="3.0",
        author="clinical_director"
    )

    # Verify complete workflow execution
    assert "urs_ingestion" in result
    assert "categorization" in result

    # Verify event chain
    urs_event = result["urs_ingestion"]
    cat_event = result["categorization"]

    assert urs_event.document_name == "ctms.urs"
    assert cat_event.gamp_category in [GAMPCategory.CATEGORY_4, GAMPCategory.CATEGORY_5]
    assert cat_event.risk_assessment["validation_rigor"] in ["enhanced", "full"]


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
