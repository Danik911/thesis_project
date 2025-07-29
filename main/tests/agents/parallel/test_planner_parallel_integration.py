"""
Integration Tests for Planner Workflow with Parallel Agent Execution

This module tests the integration between the planner workflow and the
parallel agent execution system, ensuring proper coordination and
workflow orchestration.
"""

import pytest
from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

from llama_index.core.workflow import Context
from src.agents.planner.workflow import PlannerAgentWorkflow
from src.agents.planner.coordination import AgentCoordinationConfig
from src.agents.parallel import create_agents_for_coordination
from src.core.events import (
    AgentRequestEvent,
    AgentResultEvent,
    GAMPCategorizationEvent,
    GAMPCategory,
    PlanningEvent,
    ValidationStatus
)


class TestPlannerParallelIntegration:
    """Test integration between planner workflow and parallel agents."""
    
    @pytest.fixture
    def coordination_config(self):
        """Create coordination configuration."""
        return AgentCoordinationConfig(
            max_parallel_agents=5,
            default_timeout_seconds=60,
            partial_failure_threshold=0.6,
            enable_fallback_agents=True
        )
    
    @pytest.fixture
    def planner_workflow(self, coordination_config):
        """Create planner workflow with coordination enabled."""
        return PlannerAgentWorkflow(
            timeout=120,
            verbose=True,
            enable_coordination=True,
            coordination_config=coordination_config,
            enable_llm_enhancement=False  # Disable for consistent testing
        )
    
    @pytest.fixture
    def sample_categorization_event(self):
        """Create sample GAMP categorization event."""
        return GAMPCategorizationEvent(
            gamp_category=GAMPCategory.CATEGORY_4,
            confidence_score=0.85,
            justification="Configured pharmaceutical system with customizations",
            risk_assessment={
                "technical_risk": "medium",
                "regulatory_risk": "high",
                "data_criticality": "high"
            },
            validation_requirements=[
                "Functional testing of all business processes",
                "Integration testing with external systems",
                "Data integrity validation",
                "User acceptance testing"
            ],
            recommended_test_types=[
                "functional_testing",
                "integration_testing", 
                "security_testing",
                "performance_testing"
            ],
            compliance_considerations=[
                "21 CFR Part 11 electronic records compliance",
                "GMP data integrity requirements",
                "Audit trail completeness"
            ]
        )
    
    @pytest.mark.asyncio
    async def test_planner_workflow_start_planning(self, planner_workflow, sample_categorization_event):
        """Test planner workflow start planning step."""
        # Create mock context
        context = Mock(spec=Context)
        context.set = AsyncMock()
        context.get = AsyncMock(return_value=None)
        
        # Execute start planning step
        planning_event = await planner_workflow.start_planning(
            ctx=context,
            ev=sample_categorization_event
        )
        
        # Verify planning event creation
        assert isinstance(planning_event, PlanningEvent)
        assert planning_event.gamp_category == GAMPCategory.CATEGORY_4
        assert planning_event.test_strategy is not None
        
        # Verify test strategy properties
        test_strategy = planning_event.test_strategy
        assert test_strategy.estimated_count > 0
        assert test_strategy.timeline_estimate_days > 0
        assert test_strategy.validation_rigor in ["standard", "enhanced", "comprehensive"]
        assert len(test_strategy.test_types) > 0
        
        # Verify context was set
        context.set.assert_called()
        set_calls = [call[0][0] for call in context.set.call_args_list]
        assert "categorization_event" in set_calls
        assert "test_strategy" in set_calls
        assert "planning_event" in set_calls
    
    @pytest.mark.asyncio
    async def test_planner_workflow_coordinate_parallel_agents(self, planner_workflow, sample_categorization_event):
        """Test planner workflow parallel agent coordination."""
        # Setup context with planning data
        context = Mock(spec=Context)
        context.set = AsyncMock()
        context.get = AsyncMock()
        
        # Configure context.get to return expected data
        def context_get_side_effect(key, default=None):
            if key == "categorization_event":
                return sample_categorization_event
            elif key == "test_strategy":
                return Mock(
                    estimated_count=25,
                    timeline_estimate_days=12,
                    validation_rigor="enhanced",
                    test_types=["functional_testing", "integration_testing"],
                    risk_level="medium"
                )
            elif key == "urs_context":
                return {"system_type": "configured", "domain": "pharmaceutical"}
            else:
                return default
        
        context.get.side_effect = context_get_side_effect
        
        # Create mock planning event
        planning_event = PlanningEvent(
            gamp_category=GAMPCategory.CATEGORY_4,
            test_strategy=context_get_side_effect("test_strategy"),
            planning_context={"source": "test"}
        )
        
        # Execute coordination step
        result = await planner_workflow.coordinate_parallel_agents(
            ctx=context,
            ev=planning_event
        )
        
        # Should return list of agent request events
        assert isinstance(result, list)
        assert len(result) > 0
        
        # Verify agent request events
        agent_types = []
        for request in result:
            assert isinstance(request, AgentRequestEvent)
            assert request.agent_type in ["context_provider", "sme_agent", "research_agent"]
            assert request.correlation_id is not None
            assert request.request_data is not None
            agent_types.append(request.agent_type)
        
        # Should have at least context provider, SME, and research agents
        assert "context_provider" in agent_types
        assert "sme_agent" in agent_types
        assert "research_agent" in agent_types
    
    @pytest.mark.asyncio
    async def test_planner_workflow_collect_agent_results(self, planner_workflow):
        """Test planner workflow agent result collection."""
        # Create mock context
        context = Mock(spec=Context)
        context.set = AsyncMock()
        context.get = AsyncMock()
        
        # Mock collect_events to simulate agent results
        expected_count = 3
        mock_results = [
            AgentResultEvent(
                agent_type="context_provider",
                result_data={
                    "retrieved_documents": [{"title": "GAMP-5 Guidelines"}],
                    "context_quality": "high",
                    "confidence_score": 0.88
                },
                success=True,
                processing_time=2.5,
                correlation_id=uuid4(),
                validation_status=ValidationStatus.VALIDATED
            ),
            AgentResultEvent(
                agent_type="sme_agent", 
                result_data={
                    "specialty": "pharmaceutical_validation",
                    "recommendations": [
                        {"category": "validation", "priority": "high"}
                    ],
                    "confidence_score": 0.82
                },
                success=True,
                processing_time=3.1,
                correlation_id=uuid4(),
                validation_status=ValidationStatus.VALIDATED
            ),
            AgentResultEvent(
                agent_type="research_agent",
                result_data={
                    "regulatory_updates": [
                        {"source": "FDA", "title": "Software Validation Guidance"}
                    ],
                    "confidence_score": 0.75
                },
                success=True,
                processing_time=4.2,
                correlation_id=uuid4(),
                validation_status=ValidationStatus.VALIDATED
            )
        ]
        
        # Configure context mocks
        context.get.side_effect = lambda key, default=None: {
            "expected_agent_count": expected_count
        }.get(key, default)
        
        context.collect_events = Mock(return_value=mock_results)
        
        # Set up planner workflow with mock coordination requests
        planner_workflow._coordination_requests = [
            Mock(correlation_id=result.correlation_id) for result in mock_results
        ]
        planner_workflow._expected_agent_results = expected_count
        
        # Create sample agent result event
        sample_result = mock_results[0]
        
        # Execute collect results step
        with patch.object(planner_workflow, '_finalize_planning') as mock_finalize:
            mock_finalize.return_value = Mock()  # Mock StopEvent
            
            result = await planner_workflow.collect_agent_results(
                ctx=context,
                ev=sample_result
            )
        
        # Verify collection occurred
        context.collect_events.assert_called_once()
        
        # Verify coordination processing
        mock_finalize.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_end_to_end_planner_parallel_execution(self):
        """Test end-to-end execution with real parallel agents (mocked LLM calls)."""
        # Create planner workflow
        config = AgentCoordinationConfig(default_timeout_seconds=30)
        workflow = PlannerAgentWorkflow(
            enable_coordination=True,
            coordination_config=config,
            verbose=True
        )
        
        # Create GAMP categorization event
        categorization_event = GAMPCategorizationEvent(
            gamp_category=GAMPCategory.CATEGORY_4,
            confidence_score=0.88,
            justification="Configured clinical trial system",
            risk_assessment={
                "technical_risk": "medium",
                "regulatory_risk": "high", 
                "data_criticality": "high"
            },
            validation_requirements=[
                "Patient data validation",
                "Regulatory compliance testing",
                "Integration testing"
            ],
            recommended_test_types=[
                "functional_testing",
                "integration_testing",
                "security_testing"
            ]
        )
        
        # Create workflow context
        context = Mock(spec=Context)
        stored_data = {}
        
        async def mock_set(key, value):
            stored_data[key] = value
        
        async def mock_get(key, default=None):
            return stored_data.get(key, default)
        
        context.set = mock_set
        context.get = mock_get
        
        # Execute start planning
        planning_event = await workflow.start_planning(
            ctx=context,
            ev=categorization_event
        )
        
        assert isinstance(planning_event, PlanningEvent)
        assert planning_event.gamp_category == GAMPCategory.CATEGORY_4
        
        # Execute parallel agent coordination
        coordination_result = await workflow.coordinate_parallel_agents(
            ctx=context,
            ev=planning_event
        )
        
        # Should return agent request events
        assert isinstance(coordination_result, list)
        assert len(coordination_result) >= 3
        
        # Verify agent types
        agent_types = {req.agent_type for req in coordination_result}
        assert "context_provider" in agent_types
        assert "sme_agent" in agent_types
        assert "research_agent" in agent_types
        
        # Simulate agent execution with mocked agents
        with patch('src.agents.parallel.create_agents_for_coordination') as mock_create_agents:
            # Create mock agents
            mock_agents = {
                "context_provider": AsyncMock(),
                "sme_agent": AsyncMock(),
                "research_agent": AsyncMock()
            }
            
            # Configure mock agent responses
            for agent_type, mock_agent in mock_agents.items():
                mock_agent.process_request.return_value = AgentResultEvent(
                    agent_type=agent_type,
                    result_data={f"{agent_type}_data": "success"},
                    success=True,
                    processing_time=1.5,
                    correlation_id=uuid4(),
                    validation_status=ValidationStatus.VALIDATED
                )
            
            mock_create_agents.return_value = mock_agents
            
            # Execute agents (simulated)
            agent_results = []
            for request in coordination_result:
                mock_agent = mock_agents[request.agent_type]
                result = await mock_agent.process_request(request)
                result.correlation_id = request.correlation_id  # Ensure correlation
                agent_results.append(result)
            
            # Mock context for result collection
            context.collect_events = Mock(return_value=agent_results)
            
            # Execute result collection
            with patch.object(workflow, '_finalize_planning') as mock_finalize:
                mock_finalize.return_value = Mock()  # Mock StopEvent
                
                final_result = await workflow.collect_agent_results(
                    ctx=context,
                    ev=agent_results[0]
                )
            
            # Verify workflow completion
            mock_finalize.assert_called_once()
            
            # Verify all agents were called
            for mock_agent in mock_agents.values():
                mock_agent.process_request.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_planner_workflow_error_handling(self, planner_workflow, sample_categorization_event):
        """Test planner workflow error handling during coordination."""
        # Create context that will cause coordination error
        context = Mock(spec=Context)
        context.set = AsyncMock()
        context.get = AsyncMock()
        
        # Configure context to return invalid data that causes error
        def error_context_get(key, default=None):
            if key == "categorization_event":
                return sample_categorization_event
            elif key == "test_strategy":
                # Return None to trigger error
                return None
            else:
                return default
        
        context.get.side_effect = error_context_get
        
        planning_event = PlanningEvent(
            gamp_category=GAMPCategory.CATEGORY_4,
            test_strategy=None,  # This should cause error
            planning_context={}
        )
        
        # Execute coordination with error condition
        result = await planner_workflow.coordinate_parallel_agents(
            ctx=context,
            ev=planning_event
        )
        
        # Should return consultation required event due to error
        from src.core.events import ConsultationRequiredEvent
        assert isinstance(result, ConsultationRequiredEvent)
        assert result.consultation_type == "coordination_error"
        assert result.urgency == "high"
        assert "system_engineer" in result.required_expertise
    
    @pytest.mark.asyncio
    async def test_planner_workflow_coordination_disabled(self, sample_categorization_event):
        """Test planner workflow when coordination is disabled."""
        # Create workflow with coordination disabled
        workflow = PlannerAgentWorkflow(
            enable_coordination=False,
            verbose=True
        )
        
        # Create mock context
        context = Mock(spec=Context)
        context.set = AsyncMock()
        context.get = AsyncMock(return_value=None)
        
        # Execute start planning
        planning_event = await workflow.start_planning(
            ctx=context,
            ev=sample_categorization_event
        )
        
        # Execute coordination (should be skipped)
        result = await workflow.coordinate_parallel_agents(
            ctx=context,
            ev=planning_event
        )
        
        # Should return consultation event indicating coordination disabled
        from src.core.events import ConsultationRequiredEvent
        assert isinstance(result, ConsultationRequiredEvent)
        assert result.consultation_type == "coordination_disabled"
        assert result.urgency == "low"


@pytest.mark.integration
class TestRealParallelExecution:
    """Integration tests with real (but mocked LLM) parallel execution."""
    
    @pytest.mark.asyncio
    async def test_realistic_pharmaceutical_scenario(self):
        """Test realistic pharmaceutical validation scenario."""
        # Scenario: Large pharmaceutical company validating new clinical trial system
        scenario = {
            "system_name": "Global Clinical Trial Management System",
            "gamp_category": GAMPCategory.CATEGORY_5,  # Custom system
            "regulatory_regions": ["FDA", "EMA", "Health Canada"],
            "patient_data": True,
            "complexity": "high",
            "integration_points": ["EDC", "CTMS", "Safety Database", "Regulatory Submissions"]
        }
        
        # Create categorization event
        categorization_event = GAMPCategorizationEvent(
            gamp_category=scenario["gamp_category"],
            confidence_score=0.82,
            justification="Custom-built clinical trial system with significant customizations",
            risk_assessment={
                "technical_risk": "high",
                "regulatory_risk": "critical",
                "data_criticality": "critical",
                "patient_safety_impact": "high"
            },
            validation_requirements=[
                "Complete functional validation of all clinical workflows",
                "Integration testing with all external systems",
                "Comprehensive security and data integrity validation",
                "User acceptance testing with global user base",
                "Performance testing under peak loads",
                "Disaster recovery and business continuity testing"
            ],
            recommended_test_types=[
                "functional_testing",
                "integration_testing", 
                "security_testing",
                "performance_testing",
                "usability_testing",
                "disaster_recovery_testing"
            ],
            compliance_considerations=[
                "21 CFR Part 11 full compliance",
                "EU GDPR patient data protection",
                "ICH GCP compliance",
                "FDA CSV requirements",
                "Complete audit trail implementation"
            ]
        )
        
        # Create planner workflow with realistic configuration
        config = AgentCoordinationConfig(
            max_parallel_agents=10,
            default_timeout_seconds=120,
            partial_failure_threshold=0.8,  # High threshold for critical system
            enable_fallback_agents=True
        )
        
        workflow = PlannerAgentWorkflow(
            timeout=300,  # 5 minutes for complex planning
            enable_coordination=True,
            coordination_config=config,
            verbose=True
        )
        
        # Mock context for workflow execution
        context = Mock(spec=Context)
        workflow_data = {}
        
        async def mock_set(key, value):
            workflow_data[key] = value
        
        async def mock_get(key, default=None):
            return workflow_data.get(key, default)
        
        context.set = mock_set
        context.get = mock_get
        
        # Execute planning workflow
        planning_event = await workflow.start_planning(
            ctx=context,
            ev=categorization_event
        )
        
        # Verify comprehensive planning for Category 5 system
        assert planning_event.gamp_category == GAMPCategory.CATEGORY_5
        test_strategy = planning_event.test_strategy
        
        # Should have extensive testing for Category 5
        assert test_strategy.estimated_count >= 50  # Many tests for complex system
        assert test_strategy.timeline_estimate_days >= 20  # Extended timeline
        assert test_strategy.validation_rigor == "comprehensive"
        assert len(test_strategy.test_types) >= 4  # Multiple test types
        
        # Execute parallel coordination
        coordination_requests = await workflow.coordinate_parallel_agents(
            ctx=context,
            ev=planning_event
        )
        
        assert isinstance(coordination_requests, list)
        assert len(coordination_requests) >= 3
        
        # Should have specialized requests for pharmaceutical context
        request_data_analysis = {}
        for request in coordination_requests:
            request_data_analysis[request.agent_type] = request.request_data
        
        # Context provider should focus on pharmaceutical documentation
        if "context_provider" in request_data_analysis:
            context_data = request_data_analysis["context_provider"]
            assert context_data["gamp_category"] == "5"
            assert "pharmaceutical" in str(context_data).lower() or "clinical" in str(context_data).lower()
        
        # SME should focus on critical compliance
        if "sme_agent" in request_data_analysis:
            sme_data = request_data_analysis["sme_agent"]
            assert sme_data["compliance_level"] in ["enhanced", "comprehensive"]
            assert "pharmaceutical_validation" in sme_data.get("specialty", "")
        
        # Research should cover multiple regulatory regions
        if "research_agent" in request_data_analysis:
            research_data = request_data_analysis["research_agent"]
            regulatory_scope = research_data.get("regulatory_scope", [])
            assert len(regulatory_scope) >= 2  # Multiple regions
            assert any(region in regulatory_scope for region in ["FDA", "EMA"])
        
        # Simulate successful parallel execution
        mock_results = []
        for request in coordination_requests:
            result = AgentResultEvent(
                agent_type=request.agent_type,
                result_data={
                    "high_quality_results": True,
                    "pharmaceutical_context": True,
                    "regulatory_compliance": True,
                    "confidence_score": 0.85
                },
                success=True,
                processing_time=5.0,  # Realistic processing time
                correlation_id=request.correlation_id,
                validation_status=ValidationStatus.VALIDATED
            )
            mock_results.append(result)
        
        # Mock result collection
        context.collect_events = Mock(return_value=mock_results)
        workflow._coordination_requests = [
            Mock(correlation_id=r.correlation_id) for r in mock_results
        ]
        
        # Execute result collection
        with patch.object(workflow, '_finalize_planning') as mock_finalize:
            mock_finalize.return_value = Mock()
            
            final_result = await workflow.collect_agent_results(
                ctx=context,
                ev=mock_results[0]
            )
        
        # Verify successful completion
        mock_finalize.assert_called_once()
        
        # Verify coordination processing occurred
        assert workflow_data.get("expected_agent_count") == len(coordination_requests)
        
        # This test demonstrates that the parallel agent system can handle
        # realistic pharmaceutical validation scenarios with proper coordination
        # and comprehensive result processing.