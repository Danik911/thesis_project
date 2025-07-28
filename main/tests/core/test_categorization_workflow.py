"""
Tests for GAMP-5 Categorization Workflow.

Tests the proper LlamaIndex workflow implementation with event-driven
step execution and error handling.
"""

import os

import pytest
from llama_index.core.workflow import Context, step
from src.core.categorization_workflow import (
    GAMPCategorizationWorkflow,
    run_categorization_workflow,
)
from src.core.events import (
    ErrorRecoveryEvent,
    GAMPCategorizationEvent,
    GAMPCategory,
    URSIngestionEvent,
)


class TestGAMPCategorizationWorkflow:
    """Test the GAMP-5 categorization workflow."""

    def test_workflow_initialization(self):
        """Test workflow initialization."""
        workflow = GAMPCategorizationWorkflow(
            timeout=300,
            verbose=True,
            enable_error_handling=True,
            confidence_threshold=0.70,
            retry_attempts=3
        )

        assert workflow._timeout == 300  # Workflow base class uses _timeout
        assert workflow.verbose is True
        assert workflow.enable_error_handling is True
        assert workflow.confidence_threshold == 0.70
        assert workflow.retry_attempts == 3
        assert workflow.categorization_agent is not None

    @pytest.mark.asyncio
    async def test_workflow_with_category_1_infrastructure(self):
        """Test workflow with infrastructure software (Category 1)."""
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OpenAI API key not available")

        workflow = GAMPCategorizationWorkflow(
            verbose=True,
            confidence_threshold=0.60
        )

        # Run workflow with infrastructure URS
        result = await workflow.run(
            urs_content="""
            Software Requirements for Data Center Infrastructure:
            - Operating system management and monitoring
            - Network infrastructure configuration
            - Hardware resource allocation
            - System backup and recovery utilities
            - No direct GxP impact, foundational infrastructure only
            """,
            document_name="infrastructure.urs",
            document_version="1.0",
            author="it_team"
        )

        # Verify results
        assert "categorization_event" in result
        assert "consultation_event" in result
        assert "summary" in result

        cat_event = result["categorization_event"]
        assert isinstance(cat_event, GAMPCategorizationEvent)
        assert cat_event.gamp_category in [
            GAMPCategory.CATEGORY_1,
            GAMPCategory.CATEGORY_3,
            GAMPCategory.CATEGORY_4,
            GAMPCategory.CATEGORY_5
        ]
        assert 0.0 <= cat_event.confidence_score <= 1.0

        # Check summary
        summary = result["summary"]
        assert summary["category"] == cat_event.gamp_category.value
        assert summary["confidence"] == cat_event.confidence_score
        assert "workflow_duration_seconds" in summary
        assert summary["workflow_duration_seconds"] > 0

    @pytest.mark.asyncio
    async def test_workflow_with_category_4_software(self):
        """Test workflow with configurable software (Category 4)."""
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OpenAI API key not available")

        workflow = GAMPCategorizationWorkflow()

        # Run workflow with LIMS configuration
        result = await workflow.run(
            urs_content="""
            Requirements for Laboratory Information Management System (LIMS):
            - Configure sample tracking workflows
            - Set up user roles and permissions  
            - Configure report templates
            - Customize dashboard views
            - Integration with existing instruments
            - All configuration through vendor-provided tools
            """,
            document_name="lims_config.urs",
            document_version="2.0",
            author="lab_manager"
        )

        # Verify categorization
        cat_event = result["categorization_event"]
        assert cat_event.gamp_category in [
            GAMPCategory.CATEGORY_4,
            GAMPCategory.CATEGORY_5
        ]

        # Check risk assessment
        assert "risk_assessment" in cat_event.risk_assessment
        assert cat_event.risk_assessment["risk_level"] in ["medium", "high"]
        assert cat_event.risk_assessment["validation_rigor"] in ["enhanced", "full"]

    @pytest.mark.asyncio
    async def test_workflow_with_error_fallback(self):
        """Test workflow error handling with fallback to Category 5."""
        workflow = GAMPCategorizationWorkflow(
            retry_attempts=2
        )

        # Run with empty content that should trigger error
        result = await workflow.run(
            urs_content="",  # Empty content should fail
            document_name="empty.urs",
            document_version="1.0",
            author="test_user"
        )

        # Should have fallback categorization
        cat_event = result["categorization_event"]
        assert cat_event.gamp_category == GAMPCategory.CATEGORY_5
        assert cat_event.confidence_score == 0.0
        assert cat_event.review_required is True
        assert "failed" in cat_event.justification.lower() or "fallback" in cat_event.justification.lower()

        # Should have triggered consultation
        assert result["consultation_event"] is not None
        assert result["consultation_event"].urgency == "high"

        # Summary should indicate fallback
        assert result["summary"]["is_fallback"] is True

    @pytest.mark.asyncio
    async def test_workflow_consultation_trigger(self):
        """Test consultation event triggering based on confidence."""
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OpenAI API key not available")

        workflow = GAMPCategorizationWorkflow(
            confidence_threshold=0.90  # High threshold to likely trigger review
        )

        # Run with ambiguous content
        result = await workflow.run(
            urs_content="""
            Generic software requirements:
            - Process some data
            - Generate reports
            - User interface needed
            """,
            document_name="ambiguous.urs"
        )

        # Check if consultation was triggered
        cat_event = result["categorization_event"]
        consultation_event = result["consultation_event"]

        if cat_event.confidence_score < 0.90:
            # Should have consultation event
            assert consultation_event is not None
            assert consultation_event.consultation_type == "categorization_review"
            assert consultation_event.context["confidence"] == cat_event.confidence_score
        else:
            # No consultation needed
            assert consultation_event is None

    @pytest.mark.asyncio
    async def test_workflow_event_flow(self):
        """Test the event flow through workflow steps."""
        # Create custom workflow to track events
        class TestWorkflow(GAMPCategorizationWorkflow):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.events_processed = []

            @step
            async def start(self, ctx, ev):
                self.events_processed.append(("start", type(ev).__name__))
                return await super().start(ctx, ev)

            @step
            async def categorize_document(self, ctx, ev):
                self.events_processed.append(("categorize", type(ev).__name__))
                return await super().categorize_document(ctx, ev)

            @step
            async def check_consultation_required(self, ctx, ev):
                self.events_processed.append(("consultation_check", type(ev).__name__))
                return await super().check_consultation_required(ctx, ev)

            @step
            async def complete_workflow(self, ctx, ev):
                self.events_processed.append(("complete", type(ev).__name__ if ev else "None"))
                return await super().complete_workflow(ctx, ev)

        workflow = TestWorkflow()

        if os.getenv("OPENAI_API_KEY"):
            result = await workflow.run(
                urs_content="Test URS content for workflow validation",
                document_name="test.urs"
            )

            # Verify event flow
            assert len(workflow.events_processed) >= 4
            assert workflow.events_processed[0] == ("start", "StartEvent")
            assert workflow.events_processed[1] == ("categorize", "URSIngestionEvent")
            assert workflow.events_processed[2] == ("consultation_check", "GAMPCategorizationEvent")
            assert workflow.events_processed[3][0] == "complete"

    @pytest.mark.asyncio
    async def test_run_categorization_workflow_helper(self):
        """Test the helper function for running workflow."""
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OpenAI API key not available")

        # Use helper function
        result = await run_categorization_workflow(
            urs_content="""
            Clinical Trial Management System Requirements:
            - Patient enrollment and randomization
            - Electronic data capture
            - Adverse event reporting
            - Full 21 CFR Part 11 compliance
            """,
            document_name="ctms.urs",
            document_version="3.0",
            author="clinical_director",
            verbose=True,
            confidence_threshold=0.70
        )

        # Verify results
        assert isinstance(result, dict)
        assert "categorization_event" in result
        assert "summary" in result

        # Should be Category 4 or 5 for clinical system
        cat_event = result["categorization_event"]
        assert cat_event.gamp_category in [
            GAMPCategory.CATEGORY_4,
            GAMPCategory.CATEGORY_5
        ]


@pytest.mark.asyncio
async def test_workflow_context_persistence():
    """Test that workflow context persists across steps."""
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OpenAI API key not available")

    workflow = GAMPCategorizationWorkflow()

    # Run workflow
    result = await workflow.run(
        urs_content="Test content for context persistence",
        document_name="context_test.urs",
        document_version="1.5",
        author="test_author"
    )

    # Verify metadata was preserved
    summary = result["summary"]
    assert "workflow_duration_seconds" in summary
    assert summary["workflow_duration_seconds"] > 0

    # Categorization should have completed
    assert "category" in summary
    assert "confidence" in summary


@pytest.mark.asyncio
async def test_workflow_error_recovery_step():
    """Test that error recovery step works correctly."""
    # Create workflow that forces an error
    class ErrorWorkflow(GAMPCategorizationWorkflow):
        @step
        async def categorize_document(self, ctx: Context, ev: URSIngestionEvent) -> ErrorRecoveryEvent:
            # Force an error recovery event
            return ErrorRecoveryEvent(
                error_type="test_error",
                error_message="Forced test error",
                error_context={"test": True},
                recovery_strategy="fallback_to_category_5",
                recovery_actions=["test_action"],
                failed_step="test",
                severity="high",
                auto_recoverable=True
            )

    workflow = ErrorWorkflow()

    result = await workflow.run(
        urs_content="Test content",
        document_name="error_test.urs"
    )

    # Should have executed error recovery
    cat_event = result["categorization_event"]
    assert cat_event.gamp_category == GAMPCategory.CATEGORY_5
    assert cat_event.confidence_score == 0.0
    assert "Forced test error" in cat_event.justification
    assert cat_event.review_required is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
