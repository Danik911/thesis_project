"""  
Unit tests for OQ generation workflow integration.

Tests the event-driven orchestration, context aggregation, and error handling
of the OQ test generation workflow.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from llama_index.core.workflow import Context
from llama_index.llms.openai import OpenAI

from src.agents.oq_generator.workflow import OQTestGenerationWorkflow
from src.agents.oq_generator.events import OQTestGenerationEvent, OQTestSuiteEvent
from src.agents.oq_generator.models import OQTestSuite, OQTestCase, TestStep
from src.agents.oq_generator.generator import OQTestGenerationError
from src.core.events import GAMPCategory, ConsultationRequiredEvent


class TestOQTestGenerationWorkflow:
    """Test OQ test generation workflow functionality."""

    @pytest.fixture
    def workflow(self):
        """Create workflow instance for testing."""
        llm = OpenAI(model="gpt-4o-mini", temperature=0.1)
        return OQTestGenerationWorkflow(llm=llm, verbose=True)

    @pytest.fixture
    def mock_context(self):
        """Create mock workflow context."""
        context = AsyncMock(spec=Context)
        context.set = AsyncMock()
        context.get = AsyncMock()
        context.store = AsyncMock()
        return context

    @pytest.fixture
    def valid_generation_event(self):
        """Create valid OQ test generation event."""
        return OQTestGenerationEvent(
            gamp_category=GAMPCategory.CATEGORY_4,
            urs_content="Sample URS content with detailed requirements for testing the system functionality and compliance requirements.",
            document_metadata={"name": "Test URS Document", "version": "1.0"},
            required_test_count=18,
            test_strategy={"approach": "risk_based", "focus": "configuration_verification"},
            compliance_requirements=["GAMP-5", "21 CFR Part 11"],
            aggregated_context={
                "sme_insights": {"expertise_areas": {"validation": 0.9}},
                "research_findings": {"regulatory_updates": ["New guidance"]},
                "context_provider_result": {"confidence_score": 0.85}
            },
            correlation_id=uuid4()
        )

    @pytest.fixture
    def valid_test_suite(self):
        """Create valid test suite for testing."""
        test_steps = [
            TestStep(
                step_number=1,
                action="Initialize system and verify installation",
                expected_result="System initializes successfully"
            )
        ]
        
        test_cases = []
        for i in range(18):  # Category 4 test count
            test_case = OQTestCase(
                test_id=f"OQ-{i+1:03d}",
                test_name=f"Configuration Test {i+1}",
                test_category="functional",
                gamp_category=4,
                objective=f"Verify system configuration aspect {i+1}",
                test_steps=test_steps,
                acceptance_criteria=[f"Configuration {i+1} verified"]
            )
            test_cases.append(test_case)
        
        return OQTestSuite(
            suite_id="OQ-SUITE-0001",
            gamp_category=4,
            document_name="Test Document",
            test_cases=test_cases,
            total_test_count=18
        )

    @pytest.mark.asyncio
    async def test_successful_generation(self, workflow, mock_context, valid_generation_event, valid_test_suite):
        """Test successful OQ test generation."""
        # Mock the test generator
        with patch.object(workflow, '_test_generator') as mock_generator:
            mock_generator.generate_oq_test_suite.return_value = valid_test_suite
            
            # Execute workflow step
            result = await workflow.generate_oq_tests(mock_context, valid_generation_event)
            
            # Verify result
            assert isinstance(result, OQTestSuiteEvent)
            assert result.generation_successful is True
            assert result.test_suite == valid_test_suite
            assert result.correlation_id == valid_generation_event.correlation_id
            
            # Verify context was set
            mock_context.set.assert_called()

    @pytest.mark.asyncio
    async def test_prerequisites_validation_failure(self, workflow, mock_context):
        """Test workflow fails with invalid prerequisites."""
        # Create invalid event (missing URS content)
        invalid_event = OQTestGenerationEvent(
            gamp_category=GAMPCategory.CATEGORY_4,
            urs_content="",  # Empty content
            document_metadata={},  # No name
            required_test_count=0,  # Invalid count
            correlation_id=uuid4()
        )
        
        # Execute workflow step
        result = await workflow.generate_oq_tests(mock_context, invalid_event)
        
        # Should return consultation request
        assert isinstance(result, ConsultationRequiredEvent)
        assert result.consultation_type == "oq_test_generation_failure"
        assert result.urgency == "high"
        assert "Prerequisites validation failed" in result.context.get("error_message", "")

    @pytest.mark.asyncio
    async def test_generation_error_handling(self, workflow, mock_context, valid_generation_event):
        """Test handling of generation errors with NO fallbacks."""
        # Mock generator to raise error
        mock_generator = MagicMock()
        mock_generator.generate_oq_test_suite.side_effect = OQTestGenerationError(
            "Test generation failed", 
            {"error_type": "LLMGenerationError"}
        )
        
        with patch.object(workflow, '_test_generator', mock_generator):
            # Execute workflow step
            result = await workflow.generate_oq_tests(mock_context, valid_generation_event)
            
            # Should return consultation request, NO fallbacks
            assert isinstance(result, ConsultationRequiredEvent)
            assert result.consultation_type == "oq_test_generation_failure"
            assert result.context["no_fallback_available"] is True
            assert result.context["requires_human_intervention"] is True

    @pytest.mark.asyncio
    async def test_quality_validation_issues(self, workflow, mock_context, valid_generation_event):
        """Test handling of quality validation issues."""
        # Create test suite with quality issues (wrong count)
        invalid_test_suite = OQTestSuite(
            suite_id="OQ-SUITE-0002",
            gamp_category=4,
            document_name="Test Document",
            test_cases=[],  # Empty test cases - quality issue
            total_test_count=0
        )
        
        # Mock generator to return invalid suite
        mock_generator = MagicMock()
        mock_generator.generate_oq_test_suite.return_value = invalid_test_suite
        
        with patch.object(workflow, '_test_generator', mock_generator):
            # Execute workflow step
            result = await workflow.generate_oq_tests(mock_context, valid_generation_event)
            
            # Should request consultation for quality issues
            assert isinstance(result, ConsultationRequiredEvent)
            assert result.consultation_type == "oq_test_suite_quality_review"
            assert "validation_engineer" in result.required_expertise

    @pytest.mark.asyncio
    async def test_context_quality_assessment(self, workflow, mock_context, valid_generation_event, valid_test_suite):
        """Test context quality assessment functionality."""
        # Mock generator
        mock_generator = MagicMock()
        mock_generator.generate_oq_test_suite.return_value = valid_test_suite
        
        with patch.object(workflow, '_test_generator', mock_generator):
            # Execute workflow step
            result = await workflow.generate_oq_tests(mock_context, valid_generation_event)
            
            # Verify context quality was assessed
            assert isinstance(result, OQTestSuiteEvent)
            assert 0.0 <= result.context_quality <= 1.0

    @pytest.mark.asyncio
    async def test_coverage_analysis_calculation(self, workflow, mock_context, valid_generation_event, valid_test_suite):
        """Test coverage analysis calculation."""
        # Add traceability to some test cases
        valid_test_suite.test_cases[0].urs_requirements = ["REQ-001", "REQ-002"]
        valid_test_suite.test_cases[1].urs_requirements = ["REQ-003"]
        
        # Mock generator
        mock_generator = MagicMock()
        mock_generator.generate_oq_test_suite.return_value = valid_test_suite
        
        with patch.object(workflow, '_test_generator', mock_generator):
            # Execute workflow step
            result = await workflow.generate_oq_tests(mock_context, valid_generation_event)
            
            # Verify coverage analysis
            assert isinstance(result, OQTestSuiteEvent)
            coverage = result.coverage_analysis
            assert "requirements_coverage_percentage" in coverage
            assert "tests_with_traceability" in coverage
            assert coverage["tests_with_traceability"] == 2  # Two tests have traceability

    @pytest.mark.asyncio
    async def test_regulatory_basis_assignment(self, workflow, mock_context, valid_generation_event, valid_test_suite):
        """Test regulatory basis assignment based on GAMP category."""
        # Mock generator
        mock_generator = MagicMock()
        mock_generator.generate_oq_test_suite.return_value = valid_test_suite
        
        with patch.object(workflow, '_test_generator', mock_generator):
            # Execute workflow step
            result = await workflow.generate_oq_tests(mock_context, valid_generation_event)
            
            # Verify regulatory basis for Category 4
            assert isinstance(result, OQTestSuiteEvent)
            regulatory_basis = result.regulatory_basis
            assert "GAMP-5" in regulatory_basis
            assert "ALCOA+" in regulatory_basis
            assert "21 CFR Part 11" in regulatory_basis  # Should be included for Category 4

    @pytest.mark.asyncio
    async def test_category_5_regulatory_requirements(self, workflow, mock_context, valid_test_suite):
        """Test Category 5 includes additional regulatory requirements."""
        # Create Category 5 event
        category_5_event = OQTestGenerationEvent(
            gamp_category=GAMPCategory.CATEGORY_5,
            urs_content="Category 5 custom application requirements",
            document_metadata={"name": "Custom App URS"},
            required_test_count=27,
            correlation_id=uuid4()
        )
        
        # Update test suite for Category 5
        valid_test_suite.gamp_category = 5
        for test_case in valid_test_suite.test_cases:
            test_case.gamp_category = 5
        
        # Mock generator
        mock_generator = MagicMock()
        mock_generator.generate_oq_test_suite.return_value = valid_test_suite
        
        with patch.object(workflow, '_test_generator', mock_generator):
            # Execute workflow step
            result = await workflow.generate_oq_tests(mock_context, category_5_event)
            
            # Verify additional requirements for Category 5
            assert isinstance(result, OQTestSuiteEvent)
            regulatory_basis = result.regulatory_basis
            assert "ICH Q9" in regulatory_basis
            assert "Design Controls" in regulatory_basis

    @pytest.mark.asyncio
    async def test_workflow_timeout_handling(self, workflow):
        """Test workflow timeout configuration."""
        # Verify timeout is set appropriately for OQ generation
        assert workflow.timeout == 600  # 10 minutes
        
        # Verify verbose mode
        assert workflow.verbose is True

    def test_workflow_initialization(self):
        """Test workflow initialization with custom parameters."""
        custom_llm = OpenAI(model="gpt-4", temperature=0.2)
        
        workflow = OQTestGenerationWorkflow(
            llm=custom_llm,
            timeout=900,  # 15 minutes
            verbose=False,
            enable_validation=False
        )
        
        assert workflow.llm == custom_llm
        assert workflow.timeout == 900
        assert workflow.verbose is False
        assert workflow.enable_validation is False

    def test_default_llm_initialization(self):
        """Test workflow with default LLM initialization."""
        workflow = OQTestGenerationWorkflow()
        
        # Should create default OpenAI LLM
        assert workflow.llm is not None
        assert isinstance(workflow.llm, OpenAI)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])