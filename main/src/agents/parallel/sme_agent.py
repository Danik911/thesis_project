"""
Subject Matter Expert (SME) Agent - Pharmaceutical Domain Validation

This module implements the SME Agent responsible for providing domain expertise
and validation guidance for pharmaceutical test generation. The agent specializes
in specific pharmaceutical domains and provides expert recommendations for
test strategies, compliance validation, and risk assessment.

Key Features:
- Domain-specific pharmaceutical expertise
- GAMP-5 compliance validation
- Risk assessment and mitigation strategies
- Test strategy recommendations
- Regulatory requirement validation
- Integration with parallel execution workflow
"""

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.llms import LLM
from llama_index.core.tools import FunctionTool
from llama_index.llms.openai import OpenAI
from pydantic import BaseModel, Field
from src.core.events import AgentRequestEvent, AgentResultEvent, ValidationStatus


class SMEAgentRequest(BaseModel):
    """Request model for SME Agent."""
    specialty: str
    test_focus: str
    compliance_level: str
    domain_knowledge: list[str] = Field(default_factory=list)
    validation_focus: list[str] = Field(default_factory=list)
    risk_factors: dict[str, Any] = Field(default_factory=dict)
    categorization_context: dict[str, Any] = Field(default_factory=dict)
    correlation_id: UUID
    timeout_seconds: int = 180


class SMEAgentResponse(BaseModel):
    """Response model for SME Agent."""
    specialty: str
    recommendations: list[dict[str, Any]] = Field(default_factory=list)
    compliance_assessment: dict[str, Any] = Field(default_factory=dict)
    risk_analysis: dict[str, Any] = Field(default_factory=dict)
    validation_guidance: list[dict[str, Any]] = Field(default_factory=list)
    domain_insights: dict[str, Any] = Field(default_factory=dict)
    confidence_score: float = 0.0
    expert_opinion: str = ""
    regulatory_considerations: list[dict[str, Any]] = Field(default_factory=list)
    processing_metadata: dict[str, Any] = Field(default_factory=dict)


class SMEAgent:
    """
    Subject Matter Expert Agent for pharmaceutical domain validation.
    
    This agent provides specialized expertise in pharmaceutical domains including:
    1. Regulatory compliance validation (FDA, EMA, ICH)
    2. GAMP-5 category-specific guidance
    3. Risk assessment and mitigation strategies
    4. Test strategy recommendations
    5. Domain-specific best practices
    
    The agent supports multiple specialties and integrates with parallel
    execution workflows for comprehensive test generation support.
    """

    def __init__(
        self,
        specialty: str = "pharmaceutical_validation",
        llm: LLM | None = None,
        verbose: bool = False,
        enable_phoenix: bool = True,
        confidence_threshold: float = 0.7,
        max_recommendations: int = 10
    ):
        """
        Initialize the SME Agent.
        
        Args:
            specialty: SME specialty area
            llm: Language model for expert analysis
            verbose: Enable verbose logging
            enable_phoenix: Enable Phoenix AI instrumentation
            confidence_threshold: Minimum confidence for recommendations
            max_recommendations: Maximum number of recommendations
        """
        self.specialty = specialty
        self.llm = llm or OpenAI(model="gpt-4.1-mini-2025-04-14")
        self.verbose = verbose
        self.enable_phoenix = enable_phoenix
        self.confidence_threshold = confidence_threshold
        self.max_recommendations = max_recommendations
        self.logger = logging.getLogger(__name__)

        # Initialize domain knowledge base
        self.domain_knowledge = self._initialize_domain_knowledge()

        # Initialize function agent with SME tools
        self.function_agent = self._create_function_agent()

        # Performance tracking
        self._expertise_stats = {
            "total_consultations": 0,
            "high_confidence_recommendations": 0,
            "avg_processing_time": 0.0,
            "specialty_focus": specialty
        }

    async def process_request(self, request_event: AgentRequestEvent) -> AgentResultEvent:
        """
        Process an SME consultation request.
        
        Args:
            request_event: Agent request event containing domain consultation requirements
            
        Returns:
            AgentResultEvent with expert recommendations and analysis
        """
        start_time = datetime.now(UTC)
        self._expertise_stats["total_consultations"] += 1

        try:
            # Parse request data
            request_data = SMEAgentRequest(
                **request_event.request_data,
                correlation_id=request_event.correlation_id
            )

            if self.verbose:
                self.logger.info(
                    f"Processing SME consultation for {request_data.specialty} specialty "
                    f"with {request_data.compliance_level} compliance level"
                )

            # Execute SME analysis with timeout
            sme_response = await asyncio.wait_for(
                self._execute_sme_analysis(request_data),
                timeout=request_data.timeout_seconds
            )

            # Calculate processing time
            processing_time = (datetime.now(UTC) - start_time).total_seconds()

            # Update performance stats
            if sme_response.confidence_score >= self.confidence_threshold:
                self._expertise_stats["high_confidence_recommendations"] += 1
            self._update_performance_stats(processing_time)

            if self.verbose:
                self.logger.info(
                    f"SME analysis completed: {len(sme_response.recommendations)} recommendations, "
                    f"confidence: {sme_response.confidence_score:.2%}, "
                    f"processing time: {processing_time:.2f}s"
                )

            return AgentResultEvent(
                agent_type="sme_agent",
                result_data=sme_response.model_dump(),
                success=True,
                processing_time=processing_time,
                correlation_id=request_event.correlation_id,
                validation_status=ValidationStatus.VALIDATED
            )

        except TimeoutError:
            processing_time = (datetime.now(UTC) - start_time).total_seconds()
            error_msg = f"SME analysis timeout after {processing_time:.1f}s"

            self.logger.error(f"SME Agent timeout: {error_msg}")

            return AgentResultEvent(
                agent_type="sme_agent",
                result_data={"error": "timeout", "partial_analysis": {}},
                success=False,
                error_message=error_msg,
                processing_time=processing_time,
                correlation_id=request_event.correlation_id,
                validation_status=ValidationStatus.REJECTED
            )

        except Exception as e:
            processing_time = (datetime.now(UTC) - start_time).total_seconds()
            error_msg = f"SME analysis failed: {e!s}"

            self.logger.error(f"SME Agent error: {error_msg}")

            return AgentResultEvent(
                agent_type="sme_agent",
                result_data={"error": str(e), "error_type": type(e).__name__},
                success=False,
                error_message=error_msg,
                processing_time=processing_time,
                correlation_id=request_event.correlation_id,
                validation_status=ValidationStatus.REJECTED
            )

    async def _execute_sme_analysis(self, request: SMEAgentRequest) -> SMEAgentResponse:
        """Execute the SME analysis process."""
        # Initialize response
        response = SMEAgentResponse(specialty=request.specialty)

        # Step 1: Compliance Assessment
        compliance_assessment = await self._assess_compliance(request)
        response.compliance_assessment = compliance_assessment

        # Step 2: Risk Analysis
        risk_analysis = await self._analyze_risks(request)
        response.risk_analysis = risk_analysis

        # Step 3: Generate Recommendations
        recommendations = await self._generate_recommendations(request, compliance_assessment, risk_analysis)
        response.recommendations = recommendations

        # Step 4: Validation Guidance
        validation_guidance = await self._provide_validation_guidance(request, recommendations)
        response.validation_guidance = validation_guidance

        # Step 5: Domain Insights
        domain_insights = await self._generate_domain_insights(request)
        response.domain_insights = domain_insights

        # Step 6: Regulatory Considerations
        regulatory_considerations = await self._assess_regulatory_considerations(request)
        response.regulatory_considerations = regulatory_considerations

        # Step 7: Expert Opinion
        expert_opinion = await self._formulate_expert_opinion(request, recommendations, risk_analysis)
        response.expert_opinion = expert_opinion

        # Step 8: Calculate Confidence Score
        confidence_score = self._calculate_confidence_score(
            recommendations, compliance_assessment, risk_analysis
        )
        response.confidence_score = confidence_score

        # Step 9: Add Processing Metadata
        response.processing_metadata = {
            "specialty_applied": request.specialty,
            "analysis_depth": request.compliance_level,
            "domain_knowledge_used": len(request.domain_knowledge),
            "confidence_factors": {
                "recommendation_strength": len(recommendations),
                "risk_clarity": risk_analysis.get("clarity_score", 0.5),
                "compliance_certainty": compliance_assessment.get("certainty_score", 0.5)
            },
            "processing_timestamp": datetime.now(UTC).isoformat()
        }

        return response

    async def _assess_compliance(self, request: SMEAgentRequest) -> dict[str, Any]:
        """Assess compliance requirements and gaps."""
        compliance_assessment = {
            "level": request.compliance_level,
            "applicable_standards": [],
            "compliance_gaps": [],
            "required_controls": [],
            "certainty_score": 0.0
        }

        # Determine applicable standards based on specialty and compliance level
        if request.specialty in ["pharmaceutical_validation", "quality_assurance"]:
            compliance_assessment["applicable_standards"].extend([
                "GAMP-5", "21 CFR Part 11", "ICH Q7", "EU GMP Annex 11"
            ])

        if request.compliance_level in ["enhanced", "comprehensive"]:
            compliance_assessment["applicable_standards"].extend([
                "ISO 27001", "NIST Cybersecurity Framework", "FDA Data Integrity Guidance"
            ])

        # Assess compliance gaps based on categorization context
        gamp_category = request.categorization_context.get("gamp_category", "unknown")
        confidence_score = request.categorization_context.get("confidence_score", 1.0)

        if confidence_score < 0.8:
            compliance_assessment["compliance_gaps"].append({
                "gap": "Categorization uncertainty",
                "impact": "high",
                "recommendation": "Conduct additional categorization review with SME input"
            })

        if gamp_category == "5":
            compliance_assessment["required_controls"].extend([
                "Custom software validation",
                "Source code review",
                "Configuration management",
                "Change control procedures"
            ])

        # Calculate certainty score
        certainty_factors = [
            len(compliance_assessment["applicable_standards"]) / 5,  # Normalize to 5 standards
            1.0 - len(compliance_assessment["compliance_gaps"]) / 3,  # Penalize gaps
            confidence_score  # Use categorization confidence
        ]
        compliance_assessment["certainty_score"] = sum(certainty_factors) / len(certainty_factors)

        return compliance_assessment

    async def _analyze_risks(self, request: SMEAgentRequest) -> dict[str, Any]:
        """Analyze risks and provide mitigation strategies."""
        risk_analysis = {
            "identified_risks": [],
            "risk_level": "medium",
            "mitigation_strategies": [],
            "critical_concerns": [],
            "clarity_score": 0.0
        }

        # Analyze risks from request context
        risk_factors = request.risk_factors

        # Technical risks
        if "integrations" in risk_factors.get("technical_factors", []):
            risk_analysis["identified_risks"].append({
                "category": "technical",
                "risk": "Integration complexity",
                "probability": "medium",
                "impact": "high",
                "mitigation": "Comprehensive integration testing strategy"
            })

        # Regulatory risks
        if request.compliance_level == "comprehensive":
            risk_analysis["identified_risks"].append({
                "category": "regulatory",
                "risk": "Regulatory compliance gaps",
                "probability": "low",
                "impact": "critical",
                "mitigation": "Enhanced validation and documentation procedures"
            })

        # Data integrity risks
        if "data_handling" in request.validation_focus:
            risk_analysis["identified_risks"].append({
                "category": "data_integrity",
                "risk": "ALCOA+ compliance concerns",
                "probability": "medium",
                "impact": "high",
                "mitigation": "Implement comprehensive audit trail and data validation"
            })

        # Determine overall risk level
        high_impact_risks = [r for r in risk_analysis["identified_risks"] if r["impact"] in ["high", "critical"]]
        if len(high_impact_risks) > 2:
            risk_analysis["risk_level"] = "high"
        elif len(high_impact_risks) > 0:
            risk_analysis["risk_level"] = "medium"
        else:
            risk_analysis["risk_level"] = "low"

        # Generate mitigation strategies
        for risk in risk_analysis["identified_risks"]:
            if risk["impact"] in ["high", "critical"]:
                risk_analysis["mitigation_strategies"].append({
                    "strategy": risk["mitigation"],
                    "priority": "high" if risk["impact"] == "critical" else "medium",
                    "timeline": "immediate" if risk["probability"] == "high" else "planned"
                })

        # Calculate clarity score
        risk_analysis["clarity_score"] = min(len(risk_analysis["identified_risks"]) / 5, 1.0)

        return risk_analysis

    async def _generate_recommendations(
        self,
        request: SMEAgentRequest,
        compliance_assessment: dict[str, Any],
        risk_analysis: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Generate expert recommendations."""
        recommendations = []

        # Compliance-based recommendations
        if compliance_assessment["compliance_gaps"]:
            for gap in compliance_assessment["compliance_gaps"]:
                recommendations.append({
                    "category": "compliance",
                    "priority": "high",
                    "recommendation": gap["recommendation"],
                    "rationale": f"Address {gap['gap']} to ensure regulatory compliance",
                    "implementation_effort": "medium",
                    "expected_benefit": "regulatory_compliance"
                })

        # Risk-based recommendations
        for strategy in risk_analysis["mitigation_strategies"]:
            recommendations.append({
                "category": "risk_mitigation",
                "priority": strategy["priority"],
                "recommendation": strategy["strategy"],
                "rationale": "Mitigate identified risk factors",
                "implementation_effort": "medium",
                "expected_benefit": "risk_reduction"
            })

        # Domain-specific recommendations based on specialty
        if request.specialty == "pharmaceutical_validation":
            recommendations.extend([
                {
                    "category": "validation",
                    "priority": "high",
                    "recommendation": "Implement risk-based validation approach following GAMP-5 principles",
                    "rationale": "Ensure validation effort is proportional to system complexity and risk",
                    "implementation_effort": "high",
                    "expected_benefit": "regulatory_acceptance"
                },
                {
                    "category": "documentation",
                    "priority": "medium",
                    "recommendation": "Establish comprehensive traceability matrix linking requirements to tests",
                    "rationale": "Demonstrate complete validation coverage for regulatory review",
                    "implementation_effort": "medium",
                    "expected_benefit": "audit_readiness"
                }
            ])

        elif request.specialty == "quality_assurance":
            recommendations.extend([
                {
                    "category": "quality",
                    "priority": "high",
                    "recommendation": "Implement continuous quality monitoring throughout validation lifecycle",
                    "rationale": "Early detection and correction of quality issues",
                    "implementation_effort": "medium",
                    "expected_benefit": "quality_improvement"
                }
            ])

        # Limit recommendations and sort by priority
        priority_order = {"high": 3, "medium": 2, "low": 1}
        recommendations.sort(key=lambda x: priority_order.get(x["priority"], 0), reverse=True)

        return recommendations[:self.max_recommendations]

    async def _provide_validation_guidance(
        self,
        request: SMEAgentRequest,
        recommendations: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Provide specific validation guidance."""
        guidance = []

        # Test strategy guidance
        if request.test_focus in ["functional_testing", "integration_testing"]:
            guidance.append({
                "area": "test_strategy",
                "guidance": f"Focus on {request.test_focus} with emphasis on user scenarios and business processes",
                "key_considerations": [
                    "User acceptance criteria validation",
                    "Business process workflow testing",
                    "Data flow validation"
                ],
                "success_criteria": "All critical user scenarios validated successfully"
            })

        # Compliance guidance
        if request.compliance_level in ["enhanced", "comprehensive"]:
            guidance.append({
                "area": "compliance_validation",
                "guidance": "Implement enhanced compliance validation procedures",
                "key_considerations": [
                    "Audit trail completeness verification",
                    "Electronic signature validation",
                    "Data integrity controls testing"
                ],
                "success_criteria": "Full compliance with applicable regulatory standards"
            })

        # Risk-based guidance
        for rec in recommendations:
            if rec["category"] == "risk_mitigation":
                guidance.append({
                    "area": "risk_management",
                    "guidance": rec["recommendation"],
                    "key_considerations": [rec["rationale"]],
                    "success_criteria": f"Achieve {rec['expected_benefit']}"
                })

        return guidance

    async def _generate_domain_insights(self, request: SMEAgentRequest) -> dict[str, Any]:
        """Generate domain-specific insights."""
        insights = {
            "specialty_focus": request.specialty,
            "key_expertise_areas": self.domain_knowledge.get(request.specialty, {}).get("expertise_areas", []),
            "industry_trends": [],
            "best_practices": [],
            "common_pitfalls": []
        }

        # Add specialty-specific insights
        if request.specialty == "pharmaceutical_validation":
            insights["industry_trends"] = [
                "Increased focus on continuous validation",
                "AI/ML validation framework development",
                "Risk-based validation approach adoption"
            ]
            insights["best_practices"] = [
                "Implement automated validation where possible",
                "Maintain comprehensive validation master plans",
                "Regular validation effectiveness reviews"
            ]
            insights["common_pitfalls"] = [
                "Over-validation of low-risk systems",
                "Inadequate change control procedures",
                "Insufficient documentation of validation rationale"
            ]

        return insights

    async def _assess_regulatory_considerations(self, request: SMEAgentRequest) -> list[dict[str, Any]]:
        """Assess regulatory considerations."""
        considerations = []

        # GAMP-5 considerations
        gamp_category = request.categorization_context.get("gamp_category", "unknown")
        if gamp_category != "unknown":
            considerations.append({
                "regulation": "GAMP-5",
                "consideration": f"Category {gamp_category} validation requirements",
                "impact": "high",
                "action_required": f"Implement Category {gamp_category} validation approach",
                "timeline": "validation_phase"
            })

        # 21 CFR Part 11 considerations
        if request.compliance_level in ["enhanced", "comprehensive"]:
            considerations.append({
                "regulation": "21 CFR Part 11",
                "consideration": "Electronic records and signatures compliance",
                "impact": "high",
                "action_required": "Validate electronic record controls and audit trail",
                "timeline": "implementation_phase"
            })

        # Data integrity considerations
        if "data_handling" in request.validation_focus:
            considerations.append({
                "regulation": "FDA Data Integrity Guidance",
                "consideration": "ALCOA+ data integrity principles",
                "impact": "medium",
                "action_required": "Implement data integrity controls and validation",
                "timeline": "design_phase"
            })

        return considerations

    async def _formulate_expert_opinion(
        self,
        request: SMEAgentRequest,
        recommendations: list[dict[str, Any]],
        risk_analysis: dict[str, Any]
    ) -> str:
        """Formulate expert opinion summary."""
        high_priority_recs = len([r for r in recommendations if r["priority"] == "high"])
        risk_level = risk_analysis["risk_level"]

        opinion_parts = []

        # Risk assessment opinion
        if risk_level == "high":
            opinion_parts.append("The system presents elevated validation risks requiring comprehensive mitigation strategies.")
        elif risk_level == "medium":
            opinion_parts.append("The system has manageable validation risks with appropriate controls.")
        else:
            opinion_parts.append("The system presents low validation risk with standard controls sufficient.")

        # Recommendation urgency
        if high_priority_recs > 3:
            opinion_parts.append("Multiple high-priority recommendations require immediate attention.")
        elif high_priority_recs > 0:
            opinion_parts.append("Key recommendations should be addressed during validation planning.")

        # Compliance opinion
        compliance_level = request.compliance_level
        if compliance_level == "comprehensive":
            opinion_parts.append("Enhanced compliance validation procedures are essential for regulatory acceptance.")

        # Overall recommendation
        if risk_level == "high" or high_priority_recs > 3:
            opinion_parts.append("Recommend phased validation approach with early risk mitigation focus.")
        else:
            opinion_parts.append("Standard validation approach should be sufficient with recommended enhancements.")

        return " ".join(opinion_parts)

    def _calculate_confidence_score(
        self,
        recommendations: list[dict[str, Any]],
        compliance_assessment: dict[str, Any],
        risk_analysis: dict[str, Any]
    ) -> float:
        """Calculate confidence score for SME analysis."""
        # Base confidence from recommendation strength
        recommendation_factor = min(len(recommendations) / self.max_recommendations, 1.0)

        # Compliance certainty factor
        compliance_factor = compliance_assessment.get("certainty_score", 0.5)

        # Risk clarity factor
        risk_factor = risk_analysis.get("clarity_score", 0.5)

        # Domain knowledge factor (higher confidence for specialized domains)
        domain_factor = 0.9 if self.specialty in self.domain_knowledge else 0.6

        # Combine factors
        confidence = (
            recommendation_factor * 0.3 +
            compliance_factor * 0.3 +
            risk_factor * 0.2 +
            domain_factor * 0.2
        )

        return min(confidence, 1.0)

    def _initialize_domain_knowledge(self) -> dict[str, Any]:
        """Initialize domain knowledge base."""
        return {
            "pharmaceutical_validation": {
                "expertise_areas": [
                    "GAMP-5 compliance", "21 CFR Part 11", "Computer System Validation",
                    "Risk-based validation", "Process validation", "Analytical method validation"
                ],
                "regulatory_focus": ["FDA", "EMA", "ICH"],
                "validation_experience": "extensive"
            },
            "quality_assurance": {
                "expertise_areas": [
                    "Quality management systems", "CAPA processes", "Quality risk management",
                    "Validation lifecycle management", "Regulatory compliance"
                ],
                "regulatory_focus": ["ISO 9001", "ICH Q8-Q12", "FDA Quality Metrics"],
                "validation_experience": "comprehensive"
            },
            "regulatory_affairs": {
                "expertise_areas": [
                    "Regulatory submission strategy", "Compliance assessment",
                    "Regulatory change management", "Global regulatory requirements"
                ],
                "regulatory_focus": ["FDA", "EMA", "Health Canada", "PMDA"],
                "validation_experience": "regulatory_focused"
            }
        }

    def _create_function_agent(self) -> FunctionAgent:
        """Create function agent with SME tools."""
        tools = [
            self._create_compliance_assessment_tool(),
            self._create_risk_analysis_tool(),
            self._create_validation_guidance_tool()
        ]

        system_prompt = f"""You are a Subject Matter Expert in {self.specialty}.
Your responsibilities:
1. Validate test strategies against regulatory requirements
2. Ensure GAMP-5 category compliance  
3. Assess risk factors and mitigation strategies
4. Provide domain-specific recommendations

Always maintain pharmaceutical regulatory standards and provide evidence-based recommendations."""

        return FunctionAgent(
            tools=tools,
            llm=self.llm,
            verbose=self.verbose,
            system_prompt=system_prompt
        )

    def _create_compliance_assessment_tool(self) -> FunctionTool:
        """Create compliance assessment tool."""
        def assess_compliance_requirements(gamp_category: str, regulatory_scope: list[str]) -> dict[str, Any]:
            """
            Assess compliance requirements for given GAMP category and scope.
            
            Args:
                gamp_category: GAMP software category
                regulatory_scope: List of applicable regulations
            
            Returns:
                Compliance assessment results
            """
            assessment = {
                "category": gamp_category,
                "applicable_regulations": regulatory_scope,
                "validation_rigor": "standard",
                "critical_controls": []
            }

            if gamp_category in ["4", "5"]:
                assessment["validation_rigor"] = "enhanced"
                assessment["critical_controls"].extend([
                    "Configuration management",
                    "Change control",
                    "Security controls"
                ])

            return assessment

        return FunctionTool.from_defaults(fn=assess_compliance_requirements)

    def _create_risk_analysis_tool(self) -> FunctionTool:
        """Create risk analysis tool."""
        def analyze_validation_risks(system_complexity: str, regulatory_impact: str, data_criticality: str) -> dict[str, Any]:
            """
            Analyze validation risks based on system characteristics.
            
            Args:
                system_complexity: System complexity level
                regulatory_impact: Regulatory impact level
                data_criticality: Data criticality level
            
            Returns:
                Risk analysis results
            """
            risk_factors = {
                "complexity_risk": system_complexity,
                "regulatory_risk": regulatory_impact,
                "data_risk": data_criticality,
                "overall_risk": "medium"
            }

            high_risk_factors = sum(1 for factor in [system_complexity, regulatory_impact, data_criticality] if factor == "high")

            if high_risk_factors >= 2:
                risk_factors["overall_risk"] = "high"
            elif high_risk_factors == 0:
                risk_factors["overall_risk"] = "low"

            return risk_factors

        return FunctionTool.from_defaults(fn=analyze_validation_risks)

    def _create_validation_guidance_tool(self) -> FunctionTool:
        """Create validation guidance tool."""
        def provide_validation_guidance(test_types: list[str], compliance_level: str) -> dict[str, Any]:
            """
            Provide validation guidance for specified test types and compliance level.
            
            Args:
                test_types: List of test types to validate
                compliance_level: Required compliance level
            
            Returns:
                Validation guidance
            """
            guidance = {
                "test_types": test_types,
                "compliance_level": compliance_level,
                "validation_approach": "risk_based",
                "key_activities": []
            }

            for test_type in test_types:
                if test_type == "functional_testing":
                    guidance["key_activities"].append("User acceptance criteria validation")
                elif test_type == "integration_testing":
                    guidance["key_activities"].append("Interface validation and data flow testing")
                elif test_type == "security_testing":
                    guidance["key_activities"].append("Access control and data protection validation")

            return guidance

        return FunctionTool.from_defaults(fn=provide_validation_guidance)

    def _update_performance_stats(self, processing_time: float) -> None:
        """Update performance statistics."""
        current_avg = self._expertise_stats["avg_processing_time"]
        total_consultations = self._expertise_stats["total_consultations"]

        # Calculate new average
        new_avg = ((current_avg * (total_consultations - 1)) + processing_time) / total_consultations
        self._expertise_stats["avg_processing_time"] = new_avg

    def get_expertise_stats(self) -> dict[str, Any]:
        """Get current expertise statistics."""
        return self._expertise_stats.copy()


def create_sme_agent(
    specialty: str = "pharmaceutical_validation",
    llm: LLM | None = None,
    verbose: bool = False,
    enable_phoenix: bool = True,
    confidence_threshold: float = 0.7,
    max_recommendations: int = 10
) -> SMEAgent:
    """
    Create an SME Agent instance.
    
    Args:
        specialty: SME specialty area
        llm: Language model for expert analysis
        verbose: Enable verbose logging
        enable_phoenix: Enable Phoenix AI instrumentation
        confidence_threshold: Minimum confidence for recommendations
        max_recommendations: Maximum number of recommendations
    
    Returns:
        Configured SMEAgent instance
    """
    return SMEAgent(
        specialty=specialty,
        llm=llm,
        verbose=verbose,
        enable_phoenix=enable_phoenix,
        confidence_threshold=confidence_threshold,
        max_recommendations=max_recommendations
    )
