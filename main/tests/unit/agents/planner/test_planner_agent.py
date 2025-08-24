"""
Tests for Planner Agent functionality.

This module tests the core planner agent functionality including:
- Test strategy generation
- Agent coordination
- Risk assessment
- LLM enhancement
- Error handling
"""

from unittest.mock import Mock, patch

import pytest
from src.agents.planner.agent import create_planner_agent
from src.agents.planner.strategy_generator import TestStrategyResult
from src.core.events import GAMPCategorizationEvent, GAMPCategory


class TestPlannerAgent:
    """Test cases for PlannerAgent class."""

    @pytest.fixture
    def mock_categorization_event(self):
        """Create mock categorization event for testing."""
        return GAMPCategorizationEvent(
            gamp_category=GAMPCategory.CATEGORY_4,
            confidence_score=0.85,
            justification="Configured LIMS system with custom workflows",
            risk_assessment={
                "risk_level": "medium",
                "complexity_factors": {
                    "has_integrations": True,
                    "custom_requirements": 15
                }
            },
            categorized_by="test_categorizer"
        )

    @pytest.fixture
    def planner_agent(self):
        """Create planner agent for testing."""
        return create_planner_agent(verbose=False)

    def test_agent_initialization(self):
        """Test planner agent initialization."""
        agent = create_planner_agent(
            enable_coordination=True,
            enable_risk_assessment=True,
            verbose=False
        )

        assert agent is not None
        assert agent.enable_coordination is True
        assert agent.enable_risk_assessment is True
        assert agent.strategy_generator is not None
        assert agent.agent_coordinator is not None
        assert agent.function_agent is not None

    def test_generate_test_strategy(self, planner_agent, mock_categorization_event):
        """Test test strategy generation."""
        strategy = planner_agent.generate_test_strategy(
            categorization_event=mock_categorization_event,
            urs_context={"has_integrations": True, "integration_complexity": "medium"},
            constraints={"max_timeline_days": 45}
        )

        assert isinstance(strategy, TestStrategyResult)
        assert strategy.validation_rigor == "enhanced"  # Category 4
        assert strategy.estimated_count > 0
        assert strategy.timeline_estimate_days > 0
        assert "integration_testing" in strategy.test_types
        assert len(strategy.sme_requirements) > 0
        assert len(strategy.compliance_requirements) > 0

    def test_coordinate_parallel_agents(self, planner_agent, mock_categorization_event):
        """Test parallel agent coordination."""
        # Generate strategy first
        strategy = planner_agent.generate_test_strategy(mock_categorization_event)

        # Coordinate agents
        requests = planner_agent.coordinate_parallel_agents(
            test_strategy=strategy,
            gamp_category=mock_categorization_event.gamp_category,
            urs_context={"has_integrations": True}
        )

        assert len(requests) > 0

        # Check that we have different agent types
        agent_types = [req.agent_type for req in requests]
        assert "context_provider" in agent_types
        assert "sme_agent" in agent_types
        assert "research_agent" in agent_types

        # Check request structure
        for request in requests:
            assert hasattr(request, "agent_type")
            assert hasattr(request, "request_data")
            assert hasattr(request, "priority")
            assert hasattr(request, "correlation_id")

    def test_create_planning_event(self, planner_agent, mock_categorization_event):
        """Test planning event creation."""
        strategy = planner_agent.generate_test_strategy(mock_categorization_event)

        planning_event = planner_agent.create_planning_event(
            test_strategy=strategy,
            gamp_category=mock_categorization_event.gamp_category
        )

        assert planning_event.gamp_category == GAMPCategory.CATEGORY_4
        assert planning_event.estimated_test_count == strategy.estimated_count
        assert planning_event.required_test_types == strategy.test_types
        assert planning_event.compliance_requirements == strategy.compliance_requirements
        assert planning_event.test_strategy is not None

    def test_strategy_enhancement_for_low_confidence(self, planner_agent):
        """Test strategy enhancement for low confidence categorization."""
        low_confidence_event = GAMPCategorizationEvent(
            gamp_category=GAMPCategory.CATEGORY_4,
            confidence_score=0.65,  # Low confidence
            justification="Uncertain categorization due to mixed indicators",
            risk_assessment={"risk_level": "high"},
            categorized_by="test_categorizer",
            review_required=True
        )

        with patch.object(planner_agent.function_agent, "chat") as mock_chat:
            mock_chat.return_value = Mock(__str__=lambda x: "Increase test count by 20% and extend timeline")

            strategy = planner_agent.generate_test_strategy(low_confidence_event)

            # Should trigger LLM enhancement due to low confidence
            assert mock_chat.called
            assert strategy.estimated_count > 30  # Base Category 4 is 30

    def test_agent_coordination_disabled(self):
        """Test agent behavior when coordination is disabled."""
        agent = create_planner_agent(enable_coordination=False)

        mock_event = GAMPCategorizationEvent(
            gamp_category=GAMPCategory.CATEGORY_3,
            confidence_score=0.9,
            justification="Standard COTS application",
            risk_assessment={"risk_level": "low"},
            categorized_by="test_categorizer"
        )

        strategy = agent.generate_test_strategy(mock_event)
        requests = agent.coordinate_parallel_agents(
            test_strategy=strategy,
            gamp_category=mock_event.gamp_category
        )

        assert len(requests) == 0  # No coordination when disabled

    def test_validate_strategy_compatibility(self, planner_agent):
        """Test strategy compatibility validation."""
        compatibility = planner_agent.validate_strategy_compatibility(
            primary_category=GAMPCategory.CATEGORY_4,
            secondary_categories=[GAMPCategory.CATEGORY_5]
        )

        assert "is_compatible" in compatibility
        assert "conflicts" in compatibility
        assert "recommendations" in compatibility
        assert "merged_requirements" in compatibility

    def test_error_handling_in_strategy_generation(self, planner_agent):
        """Test error handling during strategy generation."""
        invalid_event = GAMPCategorizationEvent(
            gamp_category=GAMPCategory.CATEGORY_5,
            confidence_score=0.0,  # Invalid confidence
            justification="Error case testing",
            risk_assessment={},
            categorized_by="test_categorizer"
        )

        # Should not raise exception, should handle gracefully
        strategy = planner_agent.generate_test_strategy(invalid_event)

        assert strategy is not None
        assert strategy.estimated_count > 0


class TestPlannerAgentFactory:
    """Test cases for planner agent factory function."""

    def test_create_planner_agent_defaults(self):
        """Test planner agent creation with defaults."""
        agent = create_planner_agent()

        assert agent.enable_coordination is True
        assert agent.enable_risk_assessment is True
        assert agent.llm is not None
        assert agent.strategy_generator is not None
        assert agent.agent_coordinator is not None

    def test_create_planner_agent_custom_config(self):
        """Test planner agent creation with custom configuration."""
        from src.agents.planner.coordination import AgentCoordinationConfig

        config = AgentCoordinationConfig(
            max_parallel_agents=5,
            default_timeout_seconds=120,
            partial_failure_threshold=0.8
        )

        agent = create_planner_agent(
            enable_coordination=True,
            enable_risk_assessment=False,
            coordination_config=config,
            verbose=True
        )

        assert agent.enable_coordination is True
        assert agent.enable_risk_assessment is False
        assert agent.verbose is True
        assert agent.agent_coordinator.config.max_parallel_agents == 5

    def test_create_planner_agent_with_custom_llm(self):
        """Test planner agent creation with custom LLM."""
        from llama_index.llms.openai import OpenAI

        custom_llm = OpenAI(model="gpt-4o-mini")
        agent = create_planner_agent(llm=custom_llm)

        assert agent.llm == custom_llm


@pytest.mark.asyncio
class TestPlannerAgentAsync:
    """Async test cases for planner agent."""

    async def test_agent_state_management(self):
        """Test agent state management across multiple operations."""
        agent = create_planner_agent()

        event1 = GAMPCategorizationEvent(
            gamp_category=GAMPCategory.CATEGORY_3,
            confidence_score=0.9,
            justification="First test",
            risk_assessment={"risk_level": "low"},
            categorized_by="test"
        )

        event2 = GAMPCategorizationEvent(
            gamp_category=GAMPCategory.CATEGORY_5,
            confidence_score=0.75,
            justification="Second test",
            risk_assessment={"risk_level": "high"},
            categorized_by="test"
        )

        # Generate strategies for both
        strategy1 = agent.generate_test_strategy(event1)
        strategy2 = agent.generate_test_strategy(event2)

        # Ensure state is properly managed
        assert strategy1.validation_rigor == "standard"  # Category 3
        assert strategy2.validation_rigor == "full"      # Category 5
        assert strategy1.estimated_count < strategy2.estimated_count

        # Check that current strategy is updated
        assert agent._current_strategy == strategy2  # Should be the last one
