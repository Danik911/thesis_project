"""
Integration Tests for Parallel Agent Execution System

This module provides comprehensive tests for the parallel agent execution
system, including individual agent testing, coordination testing, and
end-to-end workflow validation with realistic scenarios.
"""

import asyncio
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest
from src.agents.parallel import (
    ContextProviderAgent,
    ResearchAgent,
    SMEAgent,
    create_agent_registry,
    create_agents_for_coordination,
)
from src.agents.planner.coordination import AgentCoordinationConfig, AgentCoordinator
from src.agents.planner.strategy_generator import TestStrategyResult
from src.core.events import (
    AgentRequestEvent,
    AgentResultEvent,
    GAMPCategory,
    ValidationStatus,
)


class TestContextProviderAgent:
    """Test Context Provider Agent functionality."""

    @pytest.fixture
    def context_provider_agent(self):
        """Create test context provider agent."""
        return ContextProviderAgent(verbose=True, enable_phoenix=False)

    @pytest.fixture
    def sample_context_request(self):
        """Create sample context provider request."""
        return AgentRequestEvent(
            agent_type="context_provider",
            request_data={
                "gamp_category": "4",
                "test_strategy": {
                    "validation_rigor": "enhanced",
                    "test_types": ["functional_testing", "integration_testing"],
                    "estimated_count": 25
                },
                "document_sections": ["requirements", "validation_procedures", "risk_assessment"],
                "search_scope": {"domains": ["pharmaceutical", "gmp"]},
                "context_depth": "comprehensive"
            },
            priority="high",
            timeout_seconds=120,
            requesting_step="test_setup",
            correlation_id=uuid4()
        )

    @pytest.mark.asyncio
    async def test_context_provider_basic_processing(self, context_provider_agent, sample_context_request):
        """Test basic context provider processing."""
        result = await context_provider_agent.process_request(sample_context_request)

        assert isinstance(result, AgentResultEvent)
        assert result.agent_type == "context_provider"
        assert result.success
        assert result.correlation_id == sample_context_request.correlation_id
        assert result.validation_status == ValidationStatus.VALIDATED

        # Verify result data structure
        result_data = result.result_data
        assert "retrieved_documents" in result_data
        assert "context_quality" in result_data
        assert "assembled_context" in result_data
        assert "confidence_score" in result_data

        # Verify context quality
        assert result_data["context_quality"] in ["high", "medium", "low"]
        assert isinstance(result_data["confidence_score"], float)
        assert 0.0 <= result_data["confidence_score"] <= 1.0

    @pytest.mark.asyncio
    async def test_context_provider_timeout_handling(self, context_provider_agent):
        """Test context provider timeout handling."""
        timeout_request = AgentRequestEvent(
            agent_type="context_provider",
            request_data={
                "gamp_category": "5",
                "test_strategy": {"test_types": []},
                "document_sections": [],
                "search_scope": {}
            },
            timeout_seconds=0.001,  # Very short timeout
            requesting_step="timeout_test",
            correlation_id=uuid4()
        )

        result = await context_provider_agent.process_request(timeout_request)

        assert not result.success
        assert "timeout" in result.error_message.lower()
        assert result.validation_status == ValidationStatus.REJECTED
        assert "error" in result.result_data

    @pytest.mark.asyncio
    async def test_context_provider_performance_stats(self, context_provider_agent, sample_context_request):
        """Test context provider performance tracking."""
        # Process multiple requests
        for _ in range(3):
            await context_provider_agent.process_request(sample_context_request)

        stats = context_provider_agent.get_performance_stats()

        assert stats["total_requests"] == 3
        assert stats["successful_requests"] == 3
        assert stats["avg_processing_time"] > 0
        assert isinstance(stats["avg_processing_time"], float)


class TestSMEAgent:
    """Test SME Agent functionality."""

    @pytest.fixture
    def sme_agent(self):
        """Create test SME agent."""
        return SMEAgent(
            specialty="pharmaceutical_validation",
            verbose=True,
            enable_phoenix=False
        )

    @pytest.fixture
    def sample_sme_request(self):
        """Create sample SME request."""
        return AgentRequestEvent(
            agent_type="sme_agent",
            request_data={
                "specialty": "pharmaceutical_validation",
                "test_focus": "functional_testing",
                "compliance_level": "enhanced",
                "domain_knowledge": ["gmp", "gamp_5", "data_integrity"],
                "validation_focus": ["regulatory_compliance", "risk_assessment"],
                "risk_factors": {
                    "technical_factors": ["integrations", "complexity"],
                    "regulatory_factors": ["fda_approval", "data_integrity"]
                },
                "categorization_context": {
                    "gamp_category": "4",
                    "confidence_score": 0.85
                }
            },
            priority="high",
            timeout_seconds=120,
            requesting_step="test_setup",
            correlation_id=uuid4()
        )

    @pytest.mark.asyncio
    async def test_sme_agent_basic_processing(self, sme_agent, sample_sme_request):
        """Test basic SME agent processing."""
        result = await sme_agent.process_request(sample_sme_request)

        assert isinstance(result, AgentResultEvent)
        assert result.agent_type == "sme_agent"
        assert result.success
        assert result.correlation_id == sample_sme_request.correlation_id

        # Verify result data structure
        result_data = result.result_data
        assert "specialty" in result_data
        assert "recommendations" in result_data
        assert "compliance_assessment" in result_data
        assert "risk_analysis" in result_data
        assert "confidence_score" in result_data

        # Verify SME specialty
        assert result_data["specialty"] == "pharmaceutical_validation"

        # Verify recommendations structure
        recommendations = result_data["recommendations"]
        assert isinstance(recommendations, list)
        for rec in recommendations:
            assert "category" in rec
            assert "priority" in rec
            assert "recommendation" in rec

    @pytest.mark.asyncio
    async def test_sme_agent_compliance_assessment(self, sme_agent, sample_sme_request):
        """Test SME agent compliance assessment."""
        result = await sme_agent.process_request(sample_sme_request)

        compliance_assessment = result.result_data["compliance_assessment"]

        assert "applicable_standards" in compliance_assessment
        assert "compliance_gaps" in compliance_assessment
        assert "required_controls" in compliance_assessment
        assert "certainty_score" in compliance_assessment

        # Should include key pharmaceutical standards
        standards = compliance_assessment["applicable_standards"]
        assert any("GAMP" in std for std in standards)
        assert any("21 CFR" in std for std in standards)

    @pytest.mark.asyncio
    async def test_sme_agent_different_specialties(self):
        """Test SME agent with different specialties."""
        specialties = ["pharmaceutical_validation", "quality_assurance", "regulatory_affairs"]

        for specialty in specialties:
            agent = SMEAgent(specialty=specialty, enable_phoenix=False)

            request = AgentRequestEvent(
                agent_type="sme_agent",
                request_data={
                    "specialty": specialty,
                    "test_focus": "compliance",
                    "compliance_level": "standard"
                },
                requesting_step="specialty_test",
                correlation_id=uuid4()
            )

            result = await agent.process_request(request)

            assert result.success
            assert result.result_data["specialty"] == specialty


class TestResearchAgent:
    """Test Research Agent functionality."""

    @pytest.fixture
    def research_agent(self):
        """Create test research agent."""
        return ResearchAgent(verbose=True, enable_phoenix=False)

    @pytest.fixture
    def sample_research_request(self):
        """Create sample research request."""
        return AgentRequestEvent(
            agent_type="research_agent",
            request_data={
                "research_focus": ["gamp_5", "data_integrity", "fda_guidance"],
                "regulatory_scope": ["FDA", "EMA", "ICH"],
                "update_priority": "high",
                "time_horizon": "current",
                "depth_level": "comprehensive",
                "include_trends": True
            },
            priority="medium",
            timeout_seconds=180,
            requesting_step="test_setup",
            correlation_id=uuid4()
        )

    @pytest.mark.asyncio
    async def test_research_agent_basic_processing(self, research_agent, sample_research_request):
        """Test basic research agent processing."""
        result = await research_agent.process_request(sample_research_request)

        assert isinstance(result, AgentResultEvent)
        assert result.agent_type == "research_agent"
        assert result.success
        assert result.correlation_id == sample_research_request.correlation_id

        # Verify result data structure
        result_data = result.result_data
        assert "research_results" in result_data
        assert "regulatory_updates" in result_data
        assert "best_practices" in result_data
        assert "industry_trends" in result_data
        assert "guidance_summaries" in result_data
        assert "compliance_insights" in result_data
        assert "confidence_score" in result_data

    @pytest.mark.asyncio
    async def test_research_agent_regulatory_updates(self, research_agent, sample_research_request):
        """Test research agent regulatory updates."""
        result = await research_agent.process_request(sample_research_request)

        regulatory_updates = result.result_data["regulatory_updates"]

        assert isinstance(regulatory_updates, list)
        assert len(regulatory_updates) > 0

        # Verify regulatory update structure
        for update in regulatory_updates:
            assert "source" in update
            assert "title" in update
            assert "relevance_score" in update
            assert "summary" in update
            assert update["source"] in ["FDA", "EMA", "ICH", "ISPE"]

    @pytest.mark.asyncio
    async def test_research_agent_focus_areas(self, research_agent):
        """Test research agent with different focus areas."""
        focus_areas = [
            ["gamp_5", "validation"],
            ["data_integrity", "alcoa"],
            ["cybersecurity", "risk_management"]
        ]

        for focus in focus_areas:
            request = AgentRequestEvent(
                agent_type="research_agent",
                request_data={
                    "research_focus": focus,
                    "regulatory_scope": ["FDA"],
                    "depth_level": "standard"
                },
                requesting_step="focus_area_test",
                correlation_id=uuid4()
            )

            result = await research_agent.process_request(request)

            assert result.success
            research_results = result.result_data["research_results"]

            # Should have relevant results for focus areas
            relevant_results = [
                r for r in research_results
                if any(area.lower() in r["title"].lower() for area in focus)
            ]
            assert len(relevant_results) > 0


class TestParallelAgentCoordination:
    """Test parallel agent coordination."""

    @pytest.fixture
    def agent_coordinator(self):
        """Create test agent coordinator."""
        config = AgentCoordinationConfig(
            max_parallel_agents=5,
            default_timeout_seconds=60,
            partial_failure_threshold=0.6
        )
        return AgentCoordinator(config=config, verbose=True)

    @pytest.fixture
    def test_strategy(self):
        """Create test strategy."""
        return TestStrategyResult(
            estimated_count=20,
            timeline_estimate_days=10,
            validation_rigor="enhanced",
            test_types=["functional_testing", "integration_testing"],
            compliance_requirements=["GAMP-5", "21 CFR Part 11"],
            focus_areas=["functional_validation", "integration_testing"],
            sme_requirements=[{"specialty": "pharmaceutical_validation", "priority": "high"}],
            resource_requirements={"testers": 3, "sme_hours": 40},
            risk_factors={"technical_risk": "medium", "regulatory_risk": "high"},
            quality_gates=[{"gate": "functional_complete", "criteria": "100% pass rate"}],
            deliverables=["test_results", "validation_report"],
            assumptions=["URS analysis complete", "Environment available"],
            strategy_rationale="Risk-based validation approach for GAMP Category 4 system"
        )

    @pytest.mark.asyncio
    async def test_coordination_request_generation(self, agent_coordinator, test_strategy):
        """Test coordination request generation."""
        requests = agent_coordinator.generate_coordination_requests(
            test_strategy=test_strategy,
            gamp_category=GAMPCategory.CATEGORY_4,
            urs_context={"system_type": "configured"},
            categorization_context={"confidence_score": 0.85}
        )

        assert isinstance(requests, list)
        assert len(requests) >= 3  # At least context, SME, and research

        # Verify request types
        agent_types = [req.agent_type for req in requests]
        assert "context_provider" in agent_types
        assert "sme_agent" in agent_types
        assert "research_agent" in agent_types

        # Verify request structure
        for request in requests:
            assert isinstance(request, AgentRequestEvent)
            assert request.agent_type in ["context_provider", "sme_agent", "research_agent"]
            assert request.correlation_id is not None
            assert request.timeout_seconds > 0
            assert request.request_data is not None

    @pytest.mark.asyncio
    async def test_end_to_end_parallel_execution(self):
        """Test end-to-end parallel agent execution."""
        # Create agents
        agents = create_agents_for_coordination(
            verbose=True,
            enable_phoenix=False
        )

        # Create coordinator
        coordinator = AgentCoordinator(verbose=True)

        # Create test strategy
        test_strategy = TestStrategyResult(
            estimated_count=15,
            timeline_estimate_days=8,
            validation_rigor="standard",
            test_types=["functional_testing"],
            compliance_requirements=["GAMP-5"],
            focus_areas=["functional_validation"],
            sme_requirements=[{"specialty": "pharmaceutical_validation", "priority": "medium"}],
            resource_requirements={"testers": 2, "sme_hours": 20},
            risk_factors={"technical_risk": "low", "regulatory_risk": "medium"},
            quality_gates=[{"gate": "functional_complete", "criteria": "95% pass rate"}],
            deliverables=["test_results"],
            assumptions=["System available", "Standard validation approach"],
            strategy_rationale="Standard validation for GAMP Category 3 system"
        )

        # Generate requests
        requests = coordinator.generate_coordination_requests(
            test_strategy=test_strategy,
            gamp_category=GAMPCategory.CATEGORY_3,
            urs_context={"system_type": "infrastructure"},
            categorization_context={"confidence_score": 0.90}
        )

        # Execute agents in parallel
        async def execute_agent(request: AgentRequestEvent) -> AgentResultEvent:
            agent = agents[request.agent_type]
            return await agent.process_request(request)

        # Run parallel execution
        tasks = [execute_agent(req) for req in requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        valid_results = [r for r in results if isinstance(r, AgentResultEvent)]

        assert len(valid_results) >= 2  # At least 2 should succeed

        # Process results through coordinator
        expected_correlations = [str(req.correlation_id) for req in requests]
        coordination_result = coordinator.process_agent_results(
            results=valid_results,
            expected_correlations=expected_correlations
        )

        # Verify coordination result - agents may be classified as partial failures due to confidence thresholds
        total_working_agents = len(coordination_result.successful_requests) + len(coordination_result.partial_failures)
        assert total_working_agents > 0
        assert coordination_result.coordination_summary is not None

        # Verify that agents are functioning (either successful or partial success)
        working_rate = total_working_agents / len(requests)
        assert working_rate >= 0.5  # At least 50% of agents functioning

    @pytest.mark.asyncio
    async def test_parallel_execution_with_failures(self, agent_coordinator, test_strategy):
        """Test parallel execution with simulated failures."""
        # Generate requests
        requests = agent_coordinator.generate_coordination_requests(
            test_strategy=test_strategy,
            gamp_category=GAMPCategory.CATEGORY_5,
            categorization_context={"confidence_score": 0.75}
        )

        # Simulate mixed results (some success, some failure)
        results = []
        for i, request in enumerate(requests):
            if i % 2 == 0:  # Even indices succeed
                result = AgentResultEvent(
                    agent_type=request.agent_type,
                    result_data={"test": "success"},
                    success=True,
                    processing_time=1.0,
                    correlation_id=request.correlation_id,
                    validation_status=ValidationStatus.VALIDATED
                )
            else:  # Odd indices fail
                result = AgentResultEvent(
                    agent_type=request.agent_type,
                    result_data={"error": "simulated failure"},
                    success=False,
                    error_message="Simulated agent failure",
                    processing_time=0.5,
                    correlation_id=request.correlation_id,
                    validation_status=ValidationStatus.REJECTED
                )
            results.append(result)

        # Process results
        expected_correlations = [str(req.correlation_id) for req in requests]
        coordination_result = agent_coordinator.process_agent_results(
            results=results,
            expected_correlations=expected_correlations
        )

        # Verify handling of mixed results
        assert len(coordination_result.successful_requests) > 0
        assert len(coordination_result.failed_requests) > 0

        # Check if consultation is required based on failure rate
        success_rate = len(coordination_result.successful_requests) / len(requests)
        if success_rate < agent_coordinator.config.partial_failure_threshold:
            assert coordination_result.requires_human_consultation


class TestAgentFactory:
    """Test agent factory functionality."""

    def test_create_agents_for_coordination(self):
        """Test agent creation for coordination."""
        agents = create_agents_for_coordination(
            verbose=False,
            enable_phoenix=False
        )

        assert isinstance(agents, dict)
        assert "context_provider" in agents
        assert "sme_agent" in agents
        assert "research_agent" in agents

        # Verify agent types
        assert isinstance(agents["context_provider"], ContextProviderAgent)
        assert isinstance(agents["sme_agent"], SMEAgent)
        assert isinstance(agents["research_agent"], ResearchAgent)

    def test_agent_registry(self):
        """Test agent registry functionality."""
        registry = create_agent_registry(verbose=False)

        # Test getting agents
        context_agent = registry.get_context_provider_agent()
        sme_agent = registry.get_sme_agent()
        research_agent = registry.get_research_agent()

        assert isinstance(context_agent, ContextProviderAgent)
        assert isinstance(sme_agent, SMEAgent)
        assert isinstance(research_agent, ResearchAgent)

        # Test getting by type
        context_agent2 = registry.get_agent_by_type("context_provider")
        assert context_agent2 is context_agent  # Should be same instance

        # Test invalid agent type
        with pytest.raises(ValueError):
            registry.get_agent_by_type("invalid_agent")


class TestParallelAgentPerformance:
    """Test parallel agent performance and resource usage."""

    @pytest.mark.asyncio
    async def test_concurrent_agent_execution(self):
        """Test concurrent execution of multiple agents."""
        agents = create_agents_for_coordination(enable_phoenix=False)

        # Create multiple requests for each agent type
        requests_per_agent = 3
        all_requests = []

        for agent_type in ["context_provider", "sme_agent", "research_agent"]:
            for i in range(requests_per_agent):
                request = AgentRequestEvent(
                    agent_type=agent_type,
                    request_data=self._get_test_request_data(agent_type),
                    requesting_step="performance_test",
                    correlation_id=uuid4(),
                    timeout_seconds=30
                )
                all_requests.append((agent_type, request))

        # Execute all requests concurrently
        start_time = datetime.now(UTC)

        async def execute_request(agent_type: str, request: AgentRequestEvent):
            agent = agents[agent_type]
            return await agent.process_request(request)

        tasks = [execute_request(agent_type, req) for agent_type, req in all_requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        end_time = datetime.now(UTC)
        total_time = (end_time - start_time).total_seconds()

        # Verify results
        successful_results = [r for r in results if isinstance(r, AgentResultEvent) and r.success]

        assert len(successful_results) >= len(all_requests) * 0.8  # At least 80% success
        assert total_time < 60  # Should complete within reasonable time

        # Verify concurrent execution was actually faster than sequential
        # (This is a rough check - concurrent should be significantly faster)
        expected_sequential_time = sum(r.processing_time for r in successful_results if hasattr(r, "processing_time"))
        assert total_time < expected_sequential_time * 0.8  # At least 20% faster

    def _get_test_request_data(self, agent_type: str) -> dict[str, Any]:
        """Get test request data for agent type."""
        if agent_type == "context_provider":
            return {
                "gamp_category": "4",
                "test_strategy": {"test_types": ["functional_testing"]},
                "document_sections": ["requirements"],
                "search_scope": {}
            }
        if agent_type == "sme_agent":
            return {
                "specialty": "pharmaceutical_validation",
                "test_focus": "compliance",
                "compliance_level": "standard"
            }
        if agent_type == "research_agent":
            return {
                "research_focus": ["gamp_5"],
                "regulatory_scope": ["FDA"],
                "depth_level": "standard"
            }
        return {}


@pytest.mark.integration
class TestParallelAgentIntegration:
    """Integration tests for parallel agent system."""

    @pytest.mark.asyncio
    async def test_full_parallel_workflow_integration(self):
        """Test full integration with realistic pharmaceutical scenario."""
        # Simulate a realistic pharmaceutical system validation scenario
        test_scenario = {
            "system_name": "Clinical Trial Management System",
            "gamp_category": GAMPCategory.CATEGORY_4,
            "regulatory_scope": ["FDA", "EMA"],
            "compliance_requirements": ["GAMP-5", "21 CFR Part 11", "GCP"],
            "risk_factors": ["patient_safety", "data_integrity", "regulatory_compliance"]
        }

        # Create test strategy
        test_strategy = TestStrategyResult(
            estimated_count=35,
            timeline_estimate_days=15,
            validation_rigor="enhanced",
            test_types=["functional_testing", "integration_testing", "security_testing"],
            risk_level="high",
            dependencies=["urs_analysis", "risk_assessment"],
            recommendations=[
                "Implement comprehensive validation approach",
                "Focus on data integrity validation",
                "Include security testing for patient data"
            ],
            compliance_requirements=test_scenario["compliance_requirements"]
        )

        # Create coordination system
        coordinator = AgentCoordinator(verbose=True)
        agents = create_agents_for_coordination(enable_phoenix=False)

        # Generate and execute coordination requests
        requests = coordinator.generate_coordination_requests(
            test_strategy=test_strategy,
            gamp_category=test_scenario["gamp_category"],
            urs_context={
                "system_name": test_scenario["system_name"],
                "system_type": "configured_clinical_system",
                "regulatory_scope": test_scenario["regulatory_scope"]
            },
            categorization_context={
                "confidence_score": 0.88,
                "risk_factors": test_scenario["risk_factors"]
            }
        )

        # Execute agents in parallel
        tasks = []
        for request in requests:
            agent = agents[request.agent_type]
            task = agent.process_request(request)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)
        valid_results = [r for r in results if isinstance(r, AgentResultEvent)]

        # Process coordination results
        expected_correlations = [str(req.correlation_id) for req in requests]
        coordination_result = coordinator.process_agent_results(
            results=valid_results,
            expected_correlations=expected_correlations
        )

        # Verify comprehensive results
        assert len(coordination_result.successful_requests) >= 2

        # Verify each agent type contributed
        agent_types_completed = {r.agent_type for r in coordination_result.successful_requests}
        assert len(agent_types_completed) >= 2

        # Validate result quality for pharmaceutical context
        for result in coordination_result.successful_requests:
            assert result.validation_status == ValidationStatus.VALIDATED

            if result.agent_type == "context_provider":
                # Verify pharmaceutical context was retrieved
                context_data = result.result_data.get("assembled_context", {})
                assert "regulatory_requirements" in context_data

            elif result.agent_type == "sme_agent":
                # Verify pharmaceutical expertise was applied
                recommendations = result.result_data.get("recommendations", [])
                assert len(recommendations) > 0
                compliance_assessment = result.result_data.get("compliance_assessment", {})
                assert "applicable_standards" in compliance_assessment

            elif result.agent_type == "research_agent":
                # Verify regulatory research was conducted
                regulatory_updates = result.result_data.get("regulatory_updates", [])
                guidance_summaries = result.result_data.get("guidance_summaries", [])
                assert len(regulatory_updates) > 0 or len(guidance_summaries) > 0

        # Verify coordination summary contains pharmaceutical insights
        summary = coordination_result.coordination_summary
        assert "agent_performance" in summary
        assert "success_rate" in summary
        assert summary["success_rate"] >= 0.5
