"""
Agent Coordination for Parallel Execution

This module implements coordination logic for orchestrating parallel agent execution
in the test generation workflow. It manages requests to Context Provider, SME, and
Research agents while maintaining proper error handling and timeout management.

Key Features:
- Parallel agent request generation
- Agent type prioritization and resource allocation
- Timeout and retry management
- Result correlation and synchronization
- Error handling with partial failure recovery
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from src.core.events import (
    AgentRequestEvent,
    AgentResultEvent,
    GAMPCategory,
)

from .strategy_generator import TestStrategyResult


@dataclass
class AgentCoordinationConfig:
    """Configuration for agent coordination."""
    max_parallel_agents: int = 10
    default_timeout_seconds: int = 180
    retry_attempts: int = 2
    partial_failure_threshold: float = 0.7  # 70% success rate required
    enable_fallback_agents: bool = True
    priority_weighting: bool = True


@dataclass
class CoordinationRequest:
    """Individual agent coordination request."""
    agent_type: str
    request_data: dict[str, Any]
    priority: str
    timeout_seconds: int
    correlation_id: str
    retry_count: int = 0
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(UTC)


@dataclass
class CoordinationResult:
    """Result of agent coordination."""
    successful_requests: list[AgentResultEvent]
    failed_requests: list[tuple[CoordinationRequest, str]]
    partial_failures: list[tuple[CoordinationRequest, AgentResultEvent]]
    coordination_summary: dict[str, Any]
    requires_human_consultation: bool = False
    consultation_context: dict[str, Any] | None = None


class AgentCoordinator:
    """
    Coordinates parallel agent execution for test generation workflow.
    
    This class manages the orchestration of multiple specialized agents including:
    - Context Provider Agent (RAG/CAG for documentation retrieval)
    - SME Agents (Domain specialists for pharmaceutical expertise)
    - Research Agent (Regulatory updates and compliance requirements)
    """

    def __init__(self, config: AgentCoordinationConfig | None = None, verbose: bool = False):
        """Initialize the agent coordinator."""
        self.config = config or AgentCoordinationConfig()
        self.verbose = verbose
        self._active_requests: dict[str, CoordinationRequest] = {}
        self._agent_capabilities = self._initialize_agent_capabilities()
        self._priority_weights = {
            "critical": 1.0,
            "high": 0.8,
            "medium": 0.6,
            "low": 0.4,
            "background": 0.2
        }

    def generate_coordination_requests(
        self,
        test_strategy: TestStrategyResult,
        gamp_category: GAMPCategory,
        urs_context: dict[str, Any] | None = None,
        categorization_context: dict[str, Any] | None = None
    ) -> list[AgentRequestEvent]:
        """
        Generate coordinated requests for parallel agent execution.
        
        Args:
            test_strategy: Generated test strategy from strategy generator
            gamp_category: GAMP category for the system
            urs_context: Optional URS analysis context
            categorization_context: Optional categorization context
            
        Returns:
            List of agent request events for parallel execution
        """
        if self.verbose:
            print(f"Generating coordination requests for GAMP Category {gamp_category.value}")

        requests = []

        # Generate Context Provider Agent request
        context_request = self._create_context_provider_request(
            test_strategy, gamp_category, urs_context
        )
        requests.append(context_request)

        # Generate SME Agent requests
        sme_requests = self._create_sme_agent_requests(
            test_strategy, gamp_category, categorization_context
        )
        requests.extend(sme_requests)

        # Generate Research Agent request
        research_request = self._create_research_agent_request(
            test_strategy, gamp_category, categorization_context
        )
        requests.append(research_request)

        # Store active requests for tracking
        for request in requests:
            coordination_req = CoordinationRequest(
                agent_type=request.agent_type,
                request_data=request.request_data,
                priority=request.priority,
                timeout_seconds=request.timeout_seconds or self.config.default_timeout_seconds,
                correlation_id=str(request.correlation_id)
            )
            self._active_requests[str(request.correlation_id)] = coordination_req

        if self.verbose:
            print(f"Generated {len(requests)} coordination requests")

        return requests

    def process_agent_results(
        self,
        results: list[AgentResultEvent],
        expected_correlations: list[str]
    ) -> CoordinationResult:
        """
        Process and analyze agent results for completeness and quality.
        
        Args:
            results: List of agent result events
            expected_correlations: Expected correlation IDs
            
        Returns:
            CoordinationResult with analysis and recommendations
        """
        if self.verbose:
            print(f"Processing {len(results)} agent results")

        successful_requests = []
        failed_requests = []
        partial_failures = []

        # Categorize results
        for result in results:
            correlation_id = str(result.correlation_id)
            request = self._active_requests.get(correlation_id)

            if not request:
                continue

            if result.success:
                # Check for partial failures (successful but incomplete)
                if self._is_partial_failure(result):
                    partial_failures.append((request, result))
                else:
                    successful_requests.append(result)
            else:
                failed_requests.append((request, result.error_message or "Unknown error"))

        # Calculate success metrics
        total_expected = len(expected_correlations)
        total_received = len(results)
        successful_count = len(successful_requests)

        success_rate = successful_count / total_expected if total_expected > 0 else 0

        # Determine if human consultation is required
        requires_consultation = (
            success_rate < self.config.partial_failure_threshold or
            len(failed_requests) > total_expected * 0.3 or
            self._has_critical_failures(failed_requests)
        )

        # Generate coordination summary
        summary = {
            "total_expected": total_expected,
            "total_received": total_received,
            "successful_count": successful_count,
            "failed_count": len(failed_requests),
            "partial_failure_count": len(partial_failures),
            "success_rate": success_rate,
            "coordination_timestamp": datetime.now(UTC).isoformat(),
            "agent_performance": self._analyze_agent_performance(results)
        }

        consultation_context = None
        if requires_consultation:
            consultation_context = {
                "failed_agents": [req.agent_type for req, _ in failed_requests],
                "partial_failures": [req.agent_type for req, _ in partial_failures],
                "success_rate": success_rate,
                "critical_failures": self._identify_critical_failures(failed_requests),
                "recommendation": self._generate_consultation_recommendation(
                    successful_requests, failed_requests, partial_failures
                )
            }

        return CoordinationResult(
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            partial_failures=partial_failures,
            coordination_summary=summary,
            requires_human_consultation=requires_consultation,
            consultation_context=consultation_context
        )

    def generate_retry_requests(
        self,
        failed_requests: list[tuple[CoordinationRequest, str]],
        max_retries: int | None = None
    ) -> list[AgentRequestEvent]:
        """
        Generate retry requests for failed agent executions.
        
        Args:
            failed_requests: List of failed requests with error messages
            max_retries: Maximum retry attempts (uses config default if None)
            
        Returns:
            List of retry agent request events
        """
        max_retries = max_retries or self.config.retry_attempts
        retry_requests = []

        for request, error_message in failed_requests:
            if request.retry_count < max_retries:
                # Create retry request with modified parameters
                retry_request = self._create_retry_request(request, error_message)
                if retry_request:
                    retry_requests.append(retry_request)

                    # Update tracking
                    request.retry_count += 1
                    self._active_requests[request.correlation_id] = request

        if self.verbose:
            print(f"Generated {len(retry_requests)} retry requests")

        return retry_requests

    def _create_context_provider_request(
        self,
        test_strategy: TestStrategyResult,
        gamp_category: GAMPCategory,
        urs_context: dict[str, Any] | None
    ) -> AgentRequestEvent:
        """Create request for Context Provider Agent."""
        request_data = {
            "gamp_category": gamp_category.value,
            "test_strategy": {
                "validation_rigor": test_strategy.validation_rigor,
                "test_types": test_strategy.test_types,
                "focus_areas": test_strategy.focus_areas
            },
            "document_sections": self._determine_required_sections(gamp_category),
            "search_scope": self._determine_search_scope(test_strategy, urs_context),
            "context_depth": "comprehensive" if gamp_category == GAMPCategory.CATEGORY_5 else "standard"
        }

        return AgentRequestEvent(
            agent_type="context_provider",
            request_data=request_data,
            priority="high",
            timeout_seconds=self.config.default_timeout_seconds,
            requesting_step="planner_coordination",
            correlation_id=uuid4()
        )

    def _create_sme_agent_requests(
        self,
        test_strategy: TestStrategyResult,
        gamp_category: GAMPCategory,
        categorization_context: dict[str, Any] | None
    ) -> list[AgentRequestEvent]:
        """Create requests for SME Agents."""
        requests = []
        sme_requirements = test_strategy.sme_requirements

        for i, sme_req in enumerate(sme_requirements):
            request_data = {
                "specialty": sme_req["specialty"],
                "test_focus": (test_strategy.focus_areas[i]
                              if i < len(test_strategy.focus_areas)
                              else "general_validation"),
                "compliance_level": self._get_compliance_level(gamp_category),
                "domain_knowledge": sme_req.get("domain_knowledge", []),
                "validation_focus": sme_req.get("validation_focus", []),
                "risk_factors": test_strategy.risk_factors,
                "categorization_context": categorization_context or {}
            }

            # Determine priority based on SME requirement priority
            priority = sme_req.get("priority", "medium")

            # Adjust timeout based on complexity
            timeout = self.config.default_timeout_seconds
            if gamp_category == GAMPCategory.CATEGORY_5:
                timeout = int(timeout * 1.5)  # More time for complex analysis

            request = AgentRequestEvent(
                agent_type="sme_agent",
                request_data=request_data,
                priority=priority,
                timeout_seconds=timeout,
                requesting_step="planner_coordination",
                correlation_id=uuid4()
            )

            requests.append(request)

        return requests

    def _create_research_agent_request(
        self,
        test_strategy: TestStrategyResult,
        gamp_category: GAMPCategory,
        categorization_context: dict[str, Any] | None
    ) -> AgentRequestEvent:
        """Create request for Research Agent."""
        # Determine research areas based on compliance requirements
        research_areas = ["gamp_5_updates", "validation_guidelines"]

        if "21_cfr_part_11" in test_strategy.compliance_requirements:
            research_areas.append("21_cfr_part_11_updates")

        if "alcoa_plus" in test_strategy.compliance_requirements:
            research_areas.append("data_integrity_guidelines")

        if gamp_category == GAMPCategory.CATEGORY_5:
            research_areas.extend(["custom_software_guidance", "cybersecurity_updates"])

        request_data = {
            "research_areas": research_areas,
            "gamp_category": gamp_category.value,
            "compliance_requirements": test_strategy.compliance_requirements,
            "risk_level": test_strategy.risk_factors.get("risk_level", "medium"),
            "focus_areas": test_strategy.focus_areas,
            "validation_rigor": test_strategy.validation_rigor,
            "categorization_context": categorization_context or {}
        }

        return AgentRequestEvent(
            agent_type="research_agent",
            request_data=request_data,
            priority="low",  # Research is important but not blocking
            timeout_seconds=int(self.config.default_timeout_seconds * 1.3),  # More time for research
            requesting_step="planner_coordination",
            correlation_id=uuid4()
        )

    def _determine_required_sections(self, gamp_category: GAMPCategory) -> list[str]:
        """Determine required document sections based on GAMP category."""
        base_sections = ["functional_requirements", "technical_specifications"]

        if gamp_category in [GAMPCategory.CATEGORY_4, GAMPCategory.CATEGORY_5]:
            base_sections.extend([
                "system_architecture",
                "integration_requirements",
                "security_requirements",
                "data_management"
            ])

        if gamp_category == GAMPCategory.CATEGORY_5:
            base_sections.extend([
                "custom_development_requirements",
                "validation_requirements",
                "regulatory_requirements"
            ])

        return base_sections

    def _determine_search_scope(
        self,
        test_strategy: TestStrategyResult,
        urs_context: dict[str, Any] | None
    ) -> dict[str, Any]:
        """Determine search scope for context retrieval."""
        scope = {
            "include_regulatory": True,
            "include_standards": True,
            "include_best_practices": True,
            "depth_level": "standard"
        }

        # Enhance scope based on test strategy
        if test_strategy.validation_rigor == "full":
            scope["depth_level"] = "comprehensive"
            scope["include_historical_data"] = True

        if "security_testing" in test_strategy.focus_areas:
            scope["include_security_guidance"] = True

        if urs_context:
            if urs_context.get("has_clinical_data", False):
                scope["include_clinical_guidelines"] = True

            if urs_context.get("has_manufacturing_processes", False):
                scope["include_manufacturing_standards"] = True

        return scope

    def _get_compliance_level(self, gamp_category: GAMPCategory) -> str:
        """Get compliance level string for SME agents."""
        compliance_mapping = {
            GAMPCategory.CATEGORY_1: "basic",
            GAMPCategory.CATEGORY_3: "standard",
            GAMPCategory.CATEGORY_4: "enhanced",
            GAMPCategory.CATEGORY_5: "comprehensive"
        }
        return compliance_mapping.get(gamp_category, "standard")

    def _is_partial_failure(self, result: AgentResultEvent) -> bool:
        """Check if a successful result is actually a partial failure."""
        if not result.success:
            return False

        result_data = result.result_data

        # Check for incomplete data indicators
        if "incomplete" in result_data.get("status", "").lower():
            return True

        if result_data.get("confidence_score", 1.0) < 0.6:
            return True

        if result_data.get("data_completeness", 1.0) < 0.8:
            return True

        # Check agent-specific indicators
        if result.agent_type == "context_provider":
            if len(result_data.get("retrieved_documents", [])) == 0:
                return True

        elif result.agent_type == "sme_agent":
            if not result_data.get("recommendations", []):
                return True

        elif result.agent_type == "research_agent":
            if not result_data.get("research_findings", []):
                return True

        return False

    def _has_critical_failures(self, failed_requests: list[tuple[CoordinationRequest, str]]) -> bool:
        """Check if any critical agent failures occurred."""
        critical_agents = ["context_provider"]  # Context Provider is critical

        for request, _ in failed_requests:
            if request.agent_type in critical_agents:
                return True

        return False

    def _identify_critical_failures(self, failed_requests: list[tuple[CoordinationRequest, str]]) -> list[str]:
        """Identify critical failure types."""
        critical_failures = []

        for request, error_message in failed_requests:
            if request.agent_type == "context_provider":
                critical_failures.append("Context retrieval failure - may impact all test generation")

            if "timeout" in error_message.lower():
                critical_failures.append(f"{request.agent_type} timeout - may indicate resource constraints")

            if "authentication" in error_message.lower() or "authorization" in error_message.lower():
                critical_failures.append(f"{request.agent_type} access failure - credential issues")

        return critical_failures

    def _analyze_agent_performance(self, results: list[AgentResultEvent]) -> dict[str, Any]:
        """Analyze performance metrics for agents."""
        performance = {}

        agent_types = set(result.agent_type for result in results)

        for agent_type in agent_types:
            agent_results = [r for r in results if r.agent_type == agent_type]

            if agent_results:
                avg_processing_time = sum(r.processing_time for r in agent_results) / len(agent_results)
                success_rate = sum(1 for r in agent_results if r.success) / len(agent_results)

                performance[agent_type] = {
                    "count": len(agent_results),
                    "success_rate": success_rate,
                    "avg_processing_time": avg_processing_time,
                    "performance_rating": self._calculate_performance_rating(success_rate, avg_processing_time)
                }

        return performance

    def _calculate_performance_rating(self, success_rate: float, avg_time: float) -> str:
        """Calculate performance rating based on success rate and time."""
        if success_rate >= 0.95 and avg_time <= 60:
            return "excellent"
        if success_rate >= 0.85 and avg_time <= 120:
            return "good"
        if success_rate >= 0.70 and avg_time <= 180:
            return "acceptable"
        return "needs_improvement"

    def _generate_consultation_recommendation(
        self,
        successful: list[AgentResultEvent],
        failed: list[tuple[CoordinationRequest, str]],
        partial: list[tuple[CoordinationRequest, AgentResultEvent]]
    ) -> str:
        """Generate human consultation recommendation."""
        recommendations = []

        if len(failed) > 0:
            failed_types = [req.agent_type for req, _ in failed]
            recommendations.append(f"Agent failures: {', '.join(set(failed_types))}")

        if len(partial) > 0:
            partial_types = [req.agent_type for req, _ in partial]
            recommendations.append(f"Partial failures: {', '.join(set(partial_types))}")

        success_rate = len(successful) / (len(successful) + len(failed) + len(partial))
        if success_rate < 0.5:
            recommendations.append("Consider manual intervention for test strategy development")
        elif success_rate < 0.7:
            recommendations.append("Review and validate partial results before proceeding")

        return "; ".join(recommendations) if recommendations else "Review coordination results"

    def _create_retry_request(
        self,
        original_request: CoordinationRequest,
        error_message: str
    ) -> AgentRequestEvent | None:
        """Create retry request with adjusted parameters."""
        # Determine if retry is worthwhile
        if "timeout" in error_message.lower():
            # Increase timeout for retry
            timeout = min(original_request.timeout_seconds * 1.5, 600)  # Cap at 10 minutes
        elif "rate limit" in error_message.lower():
            # Add delay, handled by caller
            timeout = original_request.timeout_seconds
        else:
            # Generic error - use original timeout
            timeout = original_request.timeout_seconds

        # Create new correlation ID for retry
        new_correlation_id = uuid4()

        return AgentRequestEvent(
            agent_type=original_request.agent_type,
            request_data=original_request.request_data,
            priority="high",  # Increase priority for retries
            timeout_seconds=int(timeout),
            requesting_step="planner_coordination_retry",
            correlation_id=new_correlation_id
        )

    def _initialize_agent_capabilities(self) -> dict[str, dict[str, Any]]:
        """Initialize agent capabilities for coordination planning."""
        return {
            "context_provider": {
                "capabilities": ["document_retrieval", "rag_search", "context_assembly"],
                "max_concurrent": 2,
                "avg_response_time": 45,
                "reliability_score": 0.95
            },
            "sme_agent": {
                "capabilities": ["domain_analysis", "expert_recommendations", "validation_guidance"],
                "max_concurrent": 3,
                "avg_response_time": 90,
                "reliability_score": 0.88
            },
            "research_agent": {
                "capabilities": ["regulatory_research", "standard_lookup", "compliance_guidance"],
                "max_concurrent": 1,
                "avg_response_time": 120,
                "reliability_score": 0.82
            }
        }
