"""
Planner Agent - Test Generation Orchestrator

This module implements the core planner agent that orchestrates pharmaceutical test
generation based on GAMP-5 categorization. The agent creates comprehensive test
strategies and coordinates parallel agent execution while maintaining regulatory
compliance and audit trail requirements.

Key Features:
- GAMP-category-driven test strategy generation
- Intelligent parallel agent coordination
- Risk-based planning with adaptive strategies
- Comprehensive error handling and recovery
- Full audit trail for regulatory compliance
- Integration with LlamaIndex workflow patterns

Usage:
    # Create planner agent
    agent = create_planner_agent(
        enable_coordination=True,
        enable_risk_assessment=True
    )
    
    # Generate test strategy
    strategy = agent.generate_test_strategy(categorization_event, urs_context)
    
    # Coordinate agent execution
    requests = agent.coordinate_agents(strategy, gamp_category)
"""

import json
from typing import Any
from uuid import uuid4

from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.llms import LLM
from llama_index.core.tools import FunctionTool
from llama_index.llms.openai import OpenAI
from src.core.events import (
    AgentRequestEvent,
    AgentResultEvent,
    ConsultationRequiredEvent,
    GAMPCategorizationEvent,
    GAMPCategory,
    PlanningEvent,
)
from src.monitoring.phoenix_config import instrument_tool

from .coordination import AgentCoordinationConfig, AgentCoordinator, CoordinationResult
from .gamp_strategies import get_category_strategy, validate_strategy_compatibility
from .strategy_generator import GAMPStrategyGenerator, TestStrategyResult


class PlannerAgent:
    """
    Core planner agent for test generation orchestration.
    
    This agent serves as the central coordinator for pharmaceutical test generation,
    creating strategies based on GAMP-5 categorization and orchestrating parallel
    agent execution for comprehensive test development.
    """

    def __init__(
        self,
        llm: LLM | None = None,
        strategy_generator: GAMPStrategyGenerator | None = None,
        agent_coordinator: AgentCoordinator | None = None,
        enable_coordination: bool = True,
        enable_risk_assessment: bool = True,
        verbose: bool = False
    ):
        """
        Initialize the planner agent.
        
        Args:
            llm: Language model for planning intelligence
            strategy_generator: Test strategy generator
            agent_coordinator: Agent coordination manager
            enable_coordination: Enable parallel agent coordination
            enable_risk_assessment: Enable risk-based planning
            verbose: Enable verbose logging
        """
        self.llm = llm or OpenAI(model="gpt-4.1-mini-2025-04-14")
        self.strategy_generator = strategy_generator or GAMPStrategyGenerator(verbose=verbose)
        self.agent_coordinator = agent_coordinator or AgentCoordinator(verbose=verbose)
        self.enable_coordination = enable_coordination
        self.enable_risk_assessment = enable_risk_assessment
        self.verbose = verbose

        # Initialize function agent with planning tools
        self.function_agent = self._create_function_agent()

        # Planning state
        self._planning_session_id = None
        self._current_strategy = None
        self._coordination_requests = []

    def generate_test_strategy(
        self,
        categorization_event: GAMPCategorizationEvent,
        urs_context: dict[str, Any] | None = None,
        constraints: dict[str, Any] | None = None
    ) -> TestStrategyResult:
        """
        Generate comprehensive test strategy based on GAMP categorization.
        
        Args:
            categorization_event: GAMP categorization results
            urs_context: Optional URS analysis context
            constraints: Optional project constraints
            
        Returns:
            TestStrategyResult with complete strategy
        """
        if self.verbose:
            print(f"Generating test strategy for Category {categorization_event.gamp_category.value}")

        # Generate strategy using strategy generator
        strategy = self.strategy_generator.generate_test_strategy(
            categorization_event=categorization_event,
            urs_context=urs_context,
            constraints=constraints
        )

        # Store current strategy
        self._current_strategy = strategy
        self._planning_session_id = str(uuid4())

        # Enhance strategy with LLM intelligence if needed
        if categorization_event.review_required or categorization_event.confidence_score < 0.8:
            strategy = self._enhance_strategy_with_llm(strategy, categorization_event, urs_context)

        if self.verbose:
            print(f"Generated strategy with {strategy.estimated_count} tests over {strategy.timeline_estimate_days} days")

        return strategy

    def coordinate_parallel_agents(
        self,
        test_strategy: TestStrategyResult,
        gamp_category: GAMPCategory,
        urs_context: dict[str, Any] | None = None,
        categorization_context: dict[str, Any] | None = None
    ) -> list[AgentRequestEvent]:
        """
        Coordinate parallel agent execution based on test strategy.
        
        Args:
            test_strategy: Generated test strategy
            gamp_category: GAMP category
            urs_context: Optional URS context
            categorization_context: Optional categorization context
            
        Returns:
            List of agent request events
        """
        if not self.enable_coordination:
            if self.verbose:
                print("Agent coordination disabled")
            return []

        # Generate coordination requests
        requests = self.agent_coordinator.generate_coordination_requests(
            test_strategy=test_strategy,
            gamp_category=gamp_category,
            urs_context=urs_context,
            categorization_context=categorization_context
        )

        # Store requests for tracking
        self._coordination_requests = requests

        return requests

    def process_agent_results(
        self,
        results: list[AgentResultEvent],
        expected_correlations: list[str] | None = None
    ) -> CoordinationResult:
        """
        Process results from parallel agent execution.
        
        Args:
            results: Agent result events
            expected_correlations: Expected correlation IDs
            
        Returns:
            CoordinationResult with analysis
        """
        if not self.enable_coordination:
            return CoordinationResult(
                successful_requests=results,
                failed_requests=[],
                partial_failures=[],
                coordination_summary={"message": "coordination_disabled"}
            )

        # Use stored correlations if not provided
        if expected_correlations is None:
            expected_correlations = [str(req.correlation_id) for req in self._coordination_requests]

        return self.agent_coordinator.process_agent_results(results, expected_correlations)

    def create_planning_event(
        self,
        test_strategy: TestStrategyResult,
        gamp_category: GAMPCategory,
        coordination_requests: list[AgentRequestEvent] | None = None
    ) -> PlanningEvent:
        """
        Create planning event for downstream workflow.
        
        Args:
            test_strategy: Generated test strategy
            gamp_category: GAMP category
            coordination_requests: Optional coordination requests
            
        Returns:
            PlanningEvent for workflow
        """
        # Convert strategy to dictionary format
        strategy_dict = {
            "validation_rigor": test_strategy.validation_rigor,
            "test_types": test_strategy.test_types,
            "focus_areas": test_strategy.focus_areas,
            "estimated_count": test_strategy.estimated_count,
            "timeline_days": test_strategy.timeline_estimate_days,
            "resource_requirements": test_strategy.resource_requirements,
            "quality_gates": test_strategy.quality_gates,
            "deliverables": test_strategy.deliverables,
            "assumptions": test_strategy.assumptions,
            "strategy_rationale": test_strategy.strategy_rationale
        }

        # Add coordination information if available
        if coordination_requests:
            strategy_dict["coordination_summary"] = {
                "total_agents": len(coordination_requests),
                "agent_types": list(set(req.agent_type for req in coordination_requests)),
                "planning_session_id": self._planning_session_id
            }

        return PlanningEvent(
            test_strategy=strategy_dict,
            required_test_types=test_strategy.test_types,
            compliance_requirements=test_strategy.compliance_requirements,
            estimated_test_count=test_strategy.estimated_count,
            planner_agent_id=f"planner_agent_{self._planning_session_id}",
            gamp_category=gamp_category
        )

    def handle_coordination_errors(
        self,
        coordination_result: CoordinationResult,
        retry_failed: bool = True
    ) -> list[AgentRequestEvent] | ConsultationRequiredEvent | None:
        """
        Handle coordination errors with retry and escalation logic.
        
        Args:
            coordination_result: Result from agent coordination
            retry_failed: Whether to retry failed requests
            
        Returns:
            Retry requests, consultation event, or None
        """
        if not coordination_result.failed_requests and not coordination_result.requires_human_consultation:
            return None

        # Generate retry requests for failed agents
        if retry_failed and coordination_result.failed_requests:
            retry_requests = self.agent_coordinator.generate_retry_requests(
                coordination_result.failed_requests
            )
            if retry_requests:
                return retry_requests

        # Create consultation event if needed
        if coordination_result.requires_human_consultation:
            return ConsultationRequiredEvent(
                consultation_type="agent_coordination_failure",
                context=coordination_result.consultation_context or {},
                urgency="high" if len(coordination_result.failed_requests) > 2 else "normal",
                required_expertise=["system_engineer", "validation_specialist"],
                triggering_step="planner_coordination"
            )

        return None

    def validate_strategy_compatibility(
        self,
        primary_category: GAMPCategory,
        secondary_categories: list[GAMPCategory] | None = None
    ) -> dict[str, Any]:
        """
        Validate strategy compatibility for mixed GAMP categories.
        
        Args:
            primary_category: Primary GAMP category
            secondary_categories: Optional secondary categories
            
        Returns:
            Compatibility validation results
        """
        return validate_strategy_compatibility(primary_category, secondary_categories)

    def _create_function_agent(self) -> FunctionAgent:
        """Create function agent with planning tools."""
        tools = [
            self._create_strategy_analysis_tool(),
            self._create_risk_assessment_tool(),
            self._create_resource_optimization_tool(),
            self._create_timeline_estimation_tool()
        ]

        return FunctionAgent(
            tools=tools,
            llm=self.llm,
            verbose=self.verbose,
            max_iterations=10
        )

    def _enhance_strategy_with_llm(
        self,
        strategy: TestStrategyResult,
        categorization_event: GAMPCategorizationEvent,
        urs_context: dict[str, Any] | None
    ) -> TestStrategyResult:
        """Enhance strategy using LLM intelligence for complex cases."""
        if self.verbose:
            print("Enhancing strategy with LLM analysis")

        # Prepare context for LLM
        context = {
            "gamp_category": categorization_event.gamp_category.value,
            "confidence_score": categorization_event.confidence_score,
            "justification": categorization_event.justification,
            "risk_assessment": categorization_event.risk_assessment,
            "current_strategy": {
                "test_types": strategy.test_types,
                "estimated_count": strategy.estimated_count,
                "focus_areas": strategy.focus_areas,
                "timeline_days": strategy.timeline_estimate_days
            },
            "urs_context": urs_context or {}
        }

        # Use function agent to analyze and enhance
        prompt = f"""
        Analyze the following test strategy for a GAMP Category {categorization_event.gamp_category.value} system
        and provide recommendations for enhancement, especially given the confidence score of {categorization_event.confidence_score:.1%}.
        
        Context: {json.dumps(context, indent=2)}
        
        Focus on:
        1. Test coverage gaps based on low confidence indicators
        2. Additional risk mitigation strategies
        3. Resource optimization opportunities
        4. Timeline adjustment recommendations
        5. Quality gate enhancements
        
        Provide specific, actionable recommendations that maintain regulatory compliance.
        """

        try:
            # FunctionAgent uses run() method, not chat()
            response = self.function_agent.run(user_msg=prompt)

            # Parse LLM recommendations and apply to strategy
            recommendations = self._parse_llm_recommendations(str(response))
            enhanced_strategy = self._apply_recommendations(strategy, recommendations)

            return enhanced_strategy

        except Exception as e:
            if self.verbose:
                print(f"LLM enhancement failed: {e}, using original strategy")
            return strategy

    def _parse_llm_recommendations(self, llm_response: str) -> dict[str, Any]:
        """Parse LLM response for strategy recommendations."""
        # Simple parsing logic - in production, would use more sophisticated NLP
        recommendations = {
            "additional_test_types": [],
            "test_count_adjustment": 0,
            "timeline_adjustment": 0,
            "additional_focus_areas": [],
            "risk_mitigation": []
        }

        response_lower = llm_response.lower()

        # Look for test type recommendations
        if "security test" in response_lower:
            recommendations["additional_test_types"].append("security_testing")
        if "performance test" in response_lower:
            recommendations["additional_test_types"].append("performance_testing")
        if "regression test" in response_lower:
            recommendations["additional_test_types"].append("regression_testing")

        # Look for count adjustments
        if "increase" in response_lower and "test" in response_lower:
            if "20%" in response_lower:
                recommendations["test_count_adjustment"] = 0.2
            elif "30%" in response_lower:
                recommendations["test_count_adjustment"] = 0.3
            else:
                recommendations["test_count_adjustment"] = 0.15

        # Look for timeline adjustments
        if "extend" in response_lower and ("timeline" in response_lower or "time" in response_lower):
            recommendations["timeline_adjustment"] = 0.2

        return recommendations

    def _apply_recommendations(
        self,
        strategy: TestStrategyResult,
        recommendations: dict[str, Any]
    ) -> TestStrategyResult:
        """Apply LLM recommendations to strategy."""
        # Create enhanced strategy
        enhanced_strategy = TestStrategyResult(
            validation_rigor=strategy.validation_rigor,
            test_types=strategy.test_types + recommendations.get("additional_test_types", []),
            compliance_requirements=strategy.compliance_requirements,
            estimated_count=int(strategy.estimated_count * (1 + recommendations.get("test_count_adjustment", 0))),
            focus_areas=strategy.focus_areas + recommendations.get("additional_focus_areas", []),
            sme_requirements=strategy.sme_requirements,
            timeline_estimate_days=int(strategy.timeline_estimate_days * (1 + recommendations.get("timeline_adjustment", 0))),
            resource_requirements=strategy.resource_requirements,
            risk_factors=strategy.risk_factors,
            quality_gates=strategy.quality_gates,
            deliverables=strategy.deliverables,
            assumptions=strategy.assumptions + ["Strategy enhanced with LLM analysis"],
            strategy_rationale=strategy.strategy_rationale + " Enhanced with AI-powered analysis for low-confidence categorization."
        )

        return enhanced_strategy

    def _create_strategy_analysis_tool(self) -> FunctionTool:
        """Create strategy analysis tool."""
        @instrument_tool("strategy_analysis", "planning", critical=True, gamp_category=True)
        def analyze_strategy(test_count: int, gamp_category: int, risk_level: str) -> dict[str, Any]:
            """
            Analyze test strategy for completeness and optimization opportunities.
            
            Args:
                test_count: Number of tests in strategy
                gamp_category: GAMP category (1, 3, 4, 5)
                risk_level: Risk level (low, medium, high)
                
            Returns:
                Analysis results with recommendations
            """
            category_enum = GAMPCategory(gamp_category)
            base_strategy = get_category_strategy(category_enum)

            analysis = {
                "coverage_assessment": "adequate" if test_count >= base_strategy.estimated_count else "insufficient",
                "risk_alignment": "aligned" if risk_level == base_strategy.risk_level else "misaligned",
                "recommendations": []
            }

            if test_count < base_strategy.estimated_count:
                analysis["recommendations"].append(f"Increase test count to minimum {base_strategy.estimated_count}")

            if risk_level == "high" and gamp_category < 4:
                analysis["recommendations"].append("Consider elevated category approach due to high risk")

            return analysis

        return FunctionTool.from_defaults(fn=analyze_strategy)

    def _create_risk_assessment_tool(self) -> FunctionTool:
        """Create risk assessment tool."""
        def assess_risk_factors(confidence_score: float, has_integrations: bool, regulatory_impact: str) -> dict[str, Any]:
            """
            Assess risk factors for test strategy planning.
            
            Args:
                confidence_score: Categorization confidence (0.0-1.0)
                has_integrations: Whether system has integrations
                regulatory_impact: Regulatory impact level (low, medium, high)
                
            Returns:
                Risk assessment with mitigation strategies
            """
            risk_level = "low"
            mitigation_strategies = []

            # Assess confidence risk
            if confidence_score < 0.7:
                risk_level = "high"
                mitigation_strategies.append("Request expert categorization review")
                mitigation_strategies.append("Use conservative Category 5 approach")
            elif confidence_score < 0.8:
                risk_level = "medium"
                mitigation_strategies.append("Additional validation review")

            # Assess integration risk
            if has_integrations:
                if risk_level == "low":
                    risk_level = "medium"
                mitigation_strategies.append("Include comprehensive integration testing")

            # Assess regulatory risk
            if regulatory_impact == "high":
                risk_level = "high"
                mitigation_strategies.append("Enhanced compliance validation")
                mitigation_strategies.append("Regulatory expert consultation")

            return {
                "overall_risk_level": risk_level,
                "mitigation_strategies": mitigation_strategies,
                "additional_testing_needed": len(mitigation_strategies) > 2
            }

        return FunctionTool.from_defaults(fn=assess_risk_factors)

    def _create_resource_optimization_tool(self) -> FunctionTool:
        """Create resource optimization tool."""
        def optimize_resources(test_count: int, timeline_days: int, team_size: int) -> dict[str, Any]:
            """
            Optimize resource allocation for test strategy.
            
            Args:
                test_count: Number of tests planned
                timeline_days: Timeline in days
                team_size: Available team size
                
            Returns:
                Resource optimization recommendations
            """
            tests_per_person_per_day = 0.8  # Conservative estimate
            required_person_days = test_count / tests_per_person_per_day
            available_person_days = team_size * timeline_days

            optimization = {
                "resource_utilization": min(required_person_days / available_person_days, 1.0),
                "recommendations": []
            }

            if required_person_days > available_person_days:
                shortage = required_person_days - available_person_days
                optimization["recommendations"].append(f"Resource shortage: {shortage:.1f} person-days")
                optimization["recommendations"].append("Consider extending timeline or adding resources")
            elif available_person_days > required_person_days * 1.5:
                optimization["recommendations"].append("Resource surplus: consider parallel execution or additional testing")

            return optimization

        return FunctionTool.from_defaults(fn=optimize_resources)

    def _create_timeline_estimation_tool(self) -> FunctionTool:
        """Create timeline estimation tool."""
        def estimate_timeline(test_count: int, gamp_category: int, has_integrations: bool) -> dict[str, Any]:
            """
            Estimate realistic timeline for test execution.
            
            Args:
                test_count: Number of tests
                gamp_category: GAMP category
                has_integrations: Whether system has integrations
                
            Returns:
                Timeline estimation with breakdown
            """
            base_days_per_test = {1: 0.5, 3: 1.0, 4: 1.5, 5: 2.0}.get(gamp_category, 2.0)

            execution_days = test_count * base_days_per_test

            # Add integration overhead
            if has_integrations:
                execution_days *= 1.2

            # Add planning and review overhead
            overhead_factor = {1: 0.2, 3: 0.3, 4: 0.4, 5: 0.5}.get(gamp_category, 0.5)
            total_days = execution_days * (1 + overhead_factor)

            return {
                "total_timeline_days": int(total_days),
                "execution_days": int(execution_days),
                "overhead_days": int(total_days - execution_days),
                "breakdown": {
                    "planning": int(total_days * 0.2),
                    "execution": int(execution_days),
                    "review": int(total_days * 0.1),
                    "documentation": int(total_days * 0.1)
                }
            }

        return FunctionTool.from_defaults(fn=estimate_timeline)


def create_planner_agent(
    llm: LLM | None = None,
    enable_coordination: bool = True,
    enable_risk_assessment: bool = True,
    coordination_config: AgentCoordinationConfig | None = None,
    verbose: bool = False
) -> PlannerAgent:
    """
    Create a planner agent with specified configuration.
    
    Args:
        llm: Language model for planning intelligence
        enable_coordination: Enable parallel agent coordination
        enable_risk_assessment: Enable risk-based planning
        coordination_config: Configuration for agent coordination
        verbose: Enable verbose logging
        
    Returns:
        Configured PlannerAgent instance
    """
    # Use default LLM if not provided
    if llm is None:
        llm = OpenAI(model="gpt-4.1-mini-2025-04-14")

    # Create strategy generator
    strategy_generator = GAMPStrategyGenerator(verbose=verbose)

    # Create agent coordinator
    config = coordination_config or AgentCoordinationConfig()
    agent_coordinator = AgentCoordinator(config=config, verbose=verbose)

    return PlannerAgent(
        llm=llm,
        strategy_generator=strategy_generator,
        agent_coordinator=agent_coordinator,
        enable_coordination=enable_coordination,
        enable_risk_assessment=enable_risk_assessment,
        verbose=verbose
    )
