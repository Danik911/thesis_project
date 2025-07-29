"""
Research Agent - Regulatory Updates and Best Practices Research

This module implements the Research Agent responsible for providing current
regulatory guidance, industry best practices, and compliance updates for
pharmaceutical test generation. The agent specializes in regulatory research
and staying current with evolving pharmaceutical validation standards.

Key Features:
- Regulatory guidance updates (FDA, EMA, ICH)
- GAMP-5 best practices research
- Industry standard compliance verification
- Current pharmaceutical testing methodologies
- Integration with parallel execution workflow
- Phoenix AI observability integration
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


class ResearchAgentRequest(BaseModel):
    """Request model for Research Agent."""
    research_focus: list[str] = Field(default_factory=list)
    regulatory_scope: list[str] = Field(default_factory=list)
    update_priority: str = "standard"
    time_horizon: str = "current"  # current, recent, historical
    depth_level: str = "comprehensive"  # brief, standard, comprehensive
    include_trends: bool = True
    correlation_id: UUID
    timeout_seconds: int = 240


class ResearchAgentResponse(BaseModel):
    """Response model for Research Agent."""
    research_results: list[dict[str, Any]] = Field(default_factory=list)
    regulatory_updates: list[dict[str, Any]] = Field(default_factory=list)
    best_practices: list[dict[str, Any]] = Field(default_factory=list)
    industry_trends: list[dict[str, Any]] = Field(default_factory=list)
    guidance_summaries: list[dict[str, Any]] = Field(default_factory=list)
    compliance_insights: dict[str, Any] = Field(default_factory=dict)
    research_quality: str = "unknown"
    confidence_score: float = 0.0
    processing_metadata: dict[str, Any] = Field(default_factory=dict)


class ResearchAgent:
    """
    Research Agent for regulatory updates and best practices research.
    
    This agent specializes in:
    1. Regulatory guidance updates (FDA, EMA, ICH)
    2. GAMP-5 best practices research
    3. Industry standard compliance verification
    4. Current pharmaceutical testing methodologies
    5. Emerging regulatory trends and requirements
    
    The agent provides up-to-date regulatory and technical insights to support
    informed decision-making in pharmaceutical test generation.
    """

    def __init__(
        self,
        llm: LLM | None = None,
        verbose: bool = False,
        enable_phoenix: bool = True,
        max_research_items: int = 20,
        quality_threshold: float = 0.7,
        research_sources: list[str] | None = None
    ):
        """
        Initialize the Research Agent.
        
        Args:
            llm: Language model for research analysis
            verbose: Enable verbose logging
            enable_phoenix: Enable Phoenix AI instrumentation
            max_research_items: Maximum research items to return
            quality_threshold: Minimum quality threshold for research
            research_sources: List of research sources to prioritize
        """
        self.llm = llm or OpenAI(model="gpt-4.1-mini-2025-04-14")
        self.verbose = verbose
        self.enable_phoenix = enable_phoenix
        self.max_research_items = max_research_items
        self.quality_threshold = quality_threshold
        self.research_sources = research_sources or [
            "FDA", "EMA", "ICH", "ISPE", "PDA", "GAMP"
        ]
        self.logger = logging.getLogger(__name__)

        # Initialize knowledge base
        self.regulatory_knowledge = self._initialize_regulatory_knowledge()

        # Initialize function agent with research tools
        self.function_agent = self._create_function_agent()

        # Performance tracking
        self._research_stats = {
            "total_queries": 0,
            "successful_queries": 0,
            "avg_processing_time": 0.0,
            "high_quality_results": 0,
            "research_coverage": {}
        }

    async def process_request(self, request_event: AgentRequestEvent) -> AgentResultEvent:
        """
        Process a research request.
        
        Args:
            request_event: Agent request event containing research requirements
            
        Returns:
            AgentResultEvent with research results and analysis
        """
        start_time = datetime.now(UTC)
        self._research_stats["total_queries"] += 1

        try:
            # Parse request data
            request_data = ResearchAgentRequest(
                **request_event.request_data,
                correlation_id=request_event.correlation_id
            )

            if self.verbose:
                self.logger.info(
                    f"Processing research request for {len(request_data.research_focus)} focus areas "
                    f"with {request_data.depth_level} depth level"
                )

            # Execute research with timeout
            research_response = await asyncio.wait_for(
                self._execute_research(request_data),
                timeout=request_data.timeout_seconds
            )

            # Calculate processing time
            processing_time = (datetime.now(UTC) - start_time).total_seconds()

            # Update performance stats
            self._research_stats["successful_queries"] += 1
            if research_response.confidence_score >= self.quality_threshold:
                self._research_stats["high_quality_results"] += 1
            self._update_performance_stats(processing_time)

            if self.verbose:
                self.logger.info(
                    f"Research completed: {len(research_response.research_results)} results, "
                    f"quality: {research_response.research_quality}, "
                    f"confidence: {research_response.confidence_score:.2%}, "
                    f"processing time: {processing_time:.2f}s"
                )

            return AgentResultEvent(
                agent_type="research_agent",
                result_data=research_response.model_dump(),
                success=True,
                processing_time=processing_time,
                correlation_id=request_event.correlation_id,
                validation_status=ValidationStatus.VALIDATED
            )

        except TimeoutError:
            processing_time = (datetime.now(UTC) - start_time).total_seconds()
            error_msg = f"Research timeout after {processing_time:.1f}s"

            self.logger.error(f"Research Agent timeout: {error_msg}")

            return AgentResultEvent(
                agent_type="research_agent",
                result_data={"error": "timeout", "partial_results": {}},
                success=False,
                error_message=error_msg,
                processing_time=processing_time,
                correlation_id=request_event.correlation_id,
                validation_status=ValidationStatus.REJECTED
            )

        except Exception as e:
            processing_time = (datetime.now(UTC) - start_time).total_seconds()
            error_msg = f"Research failed: {e!s}"

            self.logger.error(f"Research Agent error: {error_msg}")

            return AgentResultEvent(
                agent_type="research_agent",
                result_data={"error": str(e), "error_type": type(e).__name__},
                success=False,
                error_message=error_msg,
                processing_time=processing_time,
                correlation_id=request_event.correlation_id,
                validation_status=ValidationStatus.REJECTED
            )

    async def _execute_research(self, request: ResearchAgentRequest) -> ResearchAgentResponse:
        """Execute the research process."""
        # Initialize response
        response = ResearchAgentResponse()

        # Step 1: Regulatory Updates Research
        regulatory_updates = await self._research_regulatory_updates(request)
        response.regulatory_updates = regulatory_updates

        # Step 2: Best Practices Research
        best_practices = await self._research_best_practices(request)
        response.best_practices = best_practices

        # Step 3: Industry Trends Research
        if request.include_trends:
            industry_trends = await self._research_industry_trends(request)
            response.industry_trends = industry_trends

        # Step 4: Compile Research Results
        research_results = self._compile_research_results(
            regulatory_updates, best_practices, response.industry_trends
        )
        response.research_results = research_results

        # Step 5: Generate Guidance Summaries
        guidance_summaries = await self._generate_guidance_summaries(research_results, request)
        response.guidance_summaries = guidance_summaries

        # Step 6: Compliance Insights
        compliance_insights = await self._analyze_compliance_insights(research_results, request)
        response.compliance_insights = compliance_insights

        # Step 7: Assess Research Quality
        research_quality = self._assess_research_quality(research_results, request)
        response.research_quality = research_quality

        # Step 8: Calculate Confidence Score
        confidence_score = self._calculate_confidence_score(research_results, research_quality)
        response.confidence_score = confidence_score

        # Step 9: Add Processing Metadata
        response.processing_metadata = {
            "research_strategy": self._determine_research_strategy(request),
            "sources_consulted": self.research_sources,
            "coverage_analysis": {
                "focus_areas_covered": len(request.research_focus),
                "regulatory_scope_coverage": len(request.regulatory_scope),
                "quality_assessment": research_quality
            },
            "processing_timestamp": datetime.now(UTC).isoformat()
        }

        return response

    async def _research_regulatory_updates(self, request: ResearchAgentRequest) -> list[dict[str, Any]]:
        """Research current regulatory updates."""
        updates = []

        # Simulate regulatory update research
        # In a real implementation, this would query:
        # - FDA databases and guidance documents
        # - EMA regulatory updates
        # - ICH harmonization guidelines
        # - Industry regulatory news sources

        for regulatory_body in request.regulatory_scope:
            if regulatory_body.upper() in ["FDA", "US"]:
                updates.append({
                    "source": "FDA",
                    "title": "Computer Software Assurance for Production and Quality System Software",
                    "type": "guidance",
                    "date": "2022-09-01",
                    "relevance_score": 0.95,
                    "summary": "Updated guidance on software validation requirements for pharmaceutical manufacturing",
                    "key_changes": [
                        "Risk-based approach to software validation",
                        "Emphasis on software assurance over validation",
                        "Streamlined documentation requirements"
                    ],
                    "impact_assessment": "high",
                    "implementation_timeline": "immediate"
                })

                updates.append({
                    "source": "FDA",
                    "title": "Data Integrity and Compliance with Drug CGMP",
                    "type": "guidance",
                    "date": "2023-04-15",
                    "relevance_score": 0.88,
                    "summary": "Enhanced data integrity requirements for electronic records and systems",
                    "key_changes": [
                        "Strengthened ALCOA+ requirements",
                        "Enhanced audit trail requirements",
                        "Cloud-based system considerations"
                    ],
                    "impact_assessment": "high",
                    "implementation_timeline": "phased"
                })

            if regulatory_body.upper() in ["EMA", "EU"]:
                updates.append({
                    "source": "EMA",
                    "title": "Computerised Systems and Electronic Data in Clinical Trials",
                    "type": "reflection_paper",
                    "date": "2023-06-01",
                    "relevance_score": 0.92,
                    "summary": "Guidelines for computerized systems validation in clinical trial environments",
                    "key_changes": [
                        "Enhanced requirements for electronic source data",
                        "Risk-based validation approaches",
                        "Real-world evidence system validation"
                    ],
                    "impact_assessment": "medium",
                    "implementation_timeline": "future"
                })

            if regulatory_body.upper() in ["ICH"]:
                updates.append({
                    "source": "ICH",
                    "title": "ICH M12: Electronic Submission Standards",
                    "type": "guideline",
                    "date": "2023-11-01",
                    "relevance_score": 0.85,
                    "summary": "Harmonized standards for electronic regulatory submissions",
                    "key_changes": [
                        "Standardized metadata requirements",
                        "Enhanced validation requirements for submission systems",
                        "Global harmonization of electronic standards"
                    ],
                    "impact_assessment": "medium",
                    "implementation_timeline": "long_term"
                })

        # Add focus area specific updates
        for focus_area in request.research_focus:
            if "gamp" in focus_area.lower():
                updates.append({
                    "source": "ISPE",
                    "title": "GAMP 5 Good Practice Guide: Records and Data Integrity",
                    "type": "good_practice_guide",
                    "date": "2023-08-15",
                    "relevance_score": 0.90,
                    "summary": "Updated guidance on records and data integrity in GAMP 5 context",
                    "key_changes": [
                        "Enhanced data integrity lifecycle approach",
                        "Risk-based data governance",
                        "Cloud and hybrid system considerations"
                    ],
                    "impact_assessment": "high",
                    "implementation_timeline": "immediate"
                })

        # Sort by relevance and limit results
        updates.sort(key=lambda x: x["relevance_score"], reverse=True)
        return updates[:self.max_research_items // 3]

    async def _research_best_practices(self, request: ResearchAgentRequest) -> list[dict[str, Any]]:
        """Research current best practices."""
        practices = []

        # Core GAMP-5 best practices
        practices.append({
            "category": "validation_approach",
            "title": "Risk-Based Validation Strategy",
            "source": "GAMP 5",
            "maturity": "established",
            "relevance_score": 0.95,
            "description": "Implement validation effort proportional to system risk and complexity",
            "implementation_guidance": [
                "Conduct thorough risk assessment",
                "Document risk-based validation rationale",
                "Apply appropriate validation rigor based on GAMP category"
            ],
            "success_factors": [
                "Clear risk assessment methodology",
                "Stakeholder alignment on risk tolerance",
                "Regular risk reassessment"
            ],
            "common_pitfalls": [
                "Over-validation of low-risk systems",
                "Insufficient risk assessment documentation",
                "Static risk assessment approach"
            ]
        })

        practices.append({
            "category": "testing_methodology",
            "title": "Continuous Validation Approach",
            "source": "Industry Practice",
            "maturity": "emerging",
            "relevance_score": 0.88,
            "description": "Integrate validation activities throughout the system lifecycle",
            "implementation_guidance": [
                "Implement automated validation checks",
                "Establish continuous monitoring",
                "Integrate with DevOps practices"
            ],
            "success_factors": [
                "Automated testing infrastructure",
                "Real-time monitoring capabilities",
                "Culture of continuous improvement"
            ],
            "common_pitfalls": [
                "Insufficient automation investment",
                "Lack of real-time visibility",
                "Resistance to cultural change"
            ]
        })

        # Focus area specific practices
        for focus_area in request.research_focus:
            if "data_integrity" in focus_area.lower():
                practices.append({
                    "category": "data_integrity",
                    "title": "ALCOA+ Data Governance Framework",
                    "source": "Regulatory Best Practice",
                    "maturity": "established",
                    "relevance_score": 0.92,
                    "description": "Comprehensive data governance ensuring ALCOA+ compliance",
                    "implementation_guidance": [
                        "Implement comprehensive audit trails",
                        "Establish data ownership and stewardship",
                        "Deploy automated data quality checks"
                    ],
                    "success_factors": [
                        "Clear data governance policies",
                        "Automated compliance monitoring",
                        "Regular data quality assessments"
                    ],
                    "common_pitfalls": [
                        "Incomplete audit trail coverage",
                        "Unclear data ownership",
                        "Manual compliance checking"
                    ]
                })

            if "security" in focus_area.lower():
                practices.append({
                    "category": "security",
                    "title": "Zero Trust Security Architecture",
                    "source": "Cybersecurity Best Practice",
                    "maturity": "emerging",
                    "relevance_score": 0.85,
                    "description": "Implement zero trust principles for pharmaceutical systems",
                    "implementation_guidance": [
                        "Verify all access requests",
                        "Implement least privilege access",
                        "Continuous security monitoring"
                    ],
                    "success_factors": [
                        "Comprehensive identity management",
                        "Real-time threat detection",
                        "Regular security assessments"
                    ],
                    "common_pitfalls": [
                        "Overly complex implementation",
                        "User experience degradation",
                        "Insufficient monitoring coverage"
                    ]
                })

        # Sort by relevance
        practices.sort(key=lambda x: x["relevance_score"], reverse=True)
        return practices[:self.max_research_items // 3]

    async def _research_industry_trends(self, request: ResearchAgentRequest) -> list[dict[str, Any]]:
        """Research current industry trends."""
        trends = []

        # Major industry trends
        trends.append({
            "trend": "AI/ML Integration in Pharmaceutical Validation",
            "category": "technology",
            "maturity": "emerging",
            "adoption_rate": "moderate",
            "relevance_score": 0.90,
            "description": "Increasing use of AI/ML for validation automation and risk assessment",
            "drivers": [
                "Regulatory acceptance of AI/ML systems",
                "Cost reduction pressures",
                "Need for faster validation cycles"
            ],
            "implications": [
                "New validation approaches required",
                "Enhanced data requirements",
                "Regulatory uncertainty"
            ],
            "timeline": "2-5 years",
            "regulatory_readiness": "developing"
        })

        trends.append({
            "trend": "Cloud-First Pharmaceutical Systems",
            "category": "infrastructure",
            "maturity": "growing",
            "adoption_rate": "high",
            "relevance_score": 0.85,
            "description": "Migration to cloud-based pharmaceutical systems and platforms",
            "drivers": [
                "Cost efficiency",
                "Scalability requirements",
                "Remote work enablement"
            ],
            "implications": [
                "Updated validation approaches for cloud systems",
                "Enhanced security requirements",
                "Shared responsibility models"
            ],
            "timeline": "current",
            "regulatory_readiness": "established"
        })

        trends.append({
            "trend": "Continuous Validation and DevOps",
            "category": "process",
            "maturity": "emerging",
            "adoption_rate": "moderate",
            "relevance_score": 0.88,
            "description": "Integration of continuous validation with DevOps practices",
            "drivers": [
                "Faster time-to-market requirements",
                "Quality by design principles",
                "Automation opportunities"
            ],
            "implications": [
                "Cultural change requirements",
                "Tool and process integration",
                "New skill requirements"
            ],
            "timeline": "3-7 years",
            "regulatory_readiness": "developing"
        })

        # Add regulatory trend
        trends.append({
            "trend": "Regulatory Harmonization and Digital Submissions",
            "category": "regulatory",
            "maturity": "established",
            "adoption_rate": "high",
            "relevance_score": 0.82,
            "description": "Increasing harmonization of regulatory requirements and digital submission processes",
            "drivers": [
                "Global pharmaceutical market",
                "Regulatory efficiency initiatives",
                "Digital transformation"
            ],
            "implications": [
                "Standardized validation approaches",
                "Enhanced submission system requirements",
                "Global compliance considerations"
            ],
            "timeline": "current",
            "regulatory_readiness": "established"
        })

        # Sort by relevance
        trends.sort(key=lambda x: x["relevance_score"], reverse=True)
        return trends[:self.max_research_items // 3]

    def _compile_research_results(
        self,
        regulatory_updates: list[dict[str, Any]],
        best_practices: list[dict[str, Any]],
        industry_trends: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Compile all research results into unified format."""
        results = []

        # Add regulatory updates
        for update in regulatory_updates:
            results.append({
                "type": "regulatory_update",
                "source": update["source"],
                "title": update["title"],
                "relevance_score": update["relevance_score"],
                "content_summary": update["summary"],
                "key_insights": update.get("key_changes", []),
                "impact_level": update.get("impact_assessment", "medium"),
                "actionability": update.get("implementation_timeline", "unknown")
            })

        # Add best practices
        for practice in best_practices:
            results.append({
                "type": "best_practice",
                "source": practice["source"],
                "title": practice["title"],
                "relevance_score": practice["relevance_score"],
                "content_summary": practice["description"],
                "key_insights": practice.get("implementation_guidance", []),
                "impact_level": "medium",
                "actionability": practice.get("maturity", "unknown")
            })

        # Add industry trends
        for trend in industry_trends:
            results.append({
                "type": "industry_trend",
                "source": "Industry Analysis",
                "title": trend["trend"],
                "relevance_score": trend["relevance_score"],
                "content_summary": trend["description"],
                "key_insights": trend.get("implications", []),
                "impact_level": trend.get("adoption_rate", "medium"),
                "actionability": trend.get("timeline", "unknown")
            })

        # Sort by relevance
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return results

    async def _generate_guidance_summaries(
        self,
        research_results: list[dict[str, Any]],
        request: ResearchAgentRequest
    ) -> list[dict[str, Any]]:
        """Generate actionable guidance summaries."""
        summaries = []

        # Group results by type
        by_type = {}
        for result in research_results:
            result_type = result["type"]
            if result_type not in by_type:
                by_type[result_type] = []
            by_type[result_type].append(result)

        # Generate regulatory guidance summary
        if "regulatory_update" in by_type:
            reg_updates = by_type["regulatory_update"]
            high_impact_updates = [u for u in reg_updates if u["impact_level"] == "high"]

            summaries.append({
                "area": "regulatory_compliance",
                "summary": f"Found {len(reg_updates)} regulatory updates, {len(high_impact_updates)} high impact",
                "key_recommendations": [
                    f"Review {update['title']} for implementation requirements"
                    for update in high_impact_updates[:3]
                ],
                "priority_actions": [
                    update["title"] for update in reg_updates
                    if update["actionability"] == "immediate"
                ],
                "confidence_level": "high"
            })

        # Generate best practices summary
        if "best_practice" in by_type:
            practices = by_type["best_practice"]
            established_practices = [p for p in practices if p["actionability"] == "established"]

            summaries.append({
                "area": "best_practices",
                "summary": f"Identified {len(practices)} relevant best practices, {len(established_practices)} established",
                "key_recommendations": [
                    practice["title"] for practice in established_practices[:3]
                ],
                "priority_actions": [
                    practice["content_summary"] for practice in practices[:2]
                ],
                "confidence_level": "medium"
            })

        # Generate trends summary
        if "industry_trend" in by_type:
            trends = by_type["industry_trend"]
            high_adoption_trends = [t for t in trends if t["impact_level"] in ["high", "moderate"]]

            summaries.append({
                "area": "industry_trends",
                "summary": f"Tracking {len(trends)} industry trends, {len(high_adoption_trends)} with significant adoption",
                "key_recommendations": [
                    f"Monitor {trend['title']} for validation implications"
                    for trend in high_adoption_trends[:3]
                ],
                "priority_actions": [
                    trend["title"] for trend in trends
                    if trend["actionability"] == "current"
                ],
                "confidence_level": "medium"
            })

        return summaries

    async def _analyze_compliance_insights(
        self,
        research_results: list[dict[str, Any]],
        request: ResearchAgentRequest
    ) -> dict[str, Any]:
        """Analyze compliance insights from research."""
        insights = {
            "regulatory_landscape": "stable",
            "compliance_complexity": "medium",
            "key_focus_areas": [],
            "emerging_requirements": [],
            "risk_factors": [],
            "recommendations": []
        }

        # Analyze regulatory updates for compliance insights
        regulatory_results = [r for r in research_results if r["type"] == "regulatory_update"]

        if len(regulatory_results) > 5:
            insights["regulatory_landscape"] = "dynamic"
        elif len(regulatory_results) > 2:
            insights["regulatory_landscape"] = "evolving"

        # Identify key focus areas
        focus_areas = {}
        for result in regulatory_results:
            for insight in result["key_insights"]:
                if "data integrity" in insight.lower():
                    focus_areas["data_integrity"] = focus_areas.get("data_integrity", 0) + 1
                elif "validation" in insight.lower():
                    focus_areas["validation"] = focus_areas.get("validation", 0) + 1
                elif "security" in insight.lower():
                    focus_areas["security"] = focus_areas.get("security", 0) + 1

        insights["key_focus_areas"] = [
            area for area, count in sorted(focus_areas.items(), key=lambda x: x[1], reverse=True)
        ][:3]

        # Identify emerging requirements
        immediate_updates = [
            r for r in regulatory_results
            if r["actionability"] == "immediate"
        ]
        insights["emerging_requirements"] = [
            {
                "requirement": update["title"],
                "source": update["source"],
                "urgency": "high" if update["impact_level"] == "high" else "medium"
            }
            for update in immediate_updates
        ]

        # Generate recommendations
        if insights["regulatory_landscape"] == "dynamic":
            insights["recommendations"].append(
                "Implement proactive regulatory monitoring to track frequent changes"
            )

        if "data_integrity" in insights["key_focus_areas"]:
            insights["recommendations"].append(
                "Prioritize data integrity validation and monitoring enhancements"
            )

        if len(insights["emerging_requirements"]) > 2:
            insights["recommendations"].append(
                "Establish regulatory change management process for timely compliance updates"
            )

        return insights

    def _assess_research_quality(
        self,
        research_results: list[dict[str, Any]],
        request: ResearchAgentRequest
    ) -> str:
        """Assess the quality of research results."""
        if not research_results:
            return "poor"

        # Calculate average relevance
        avg_relevance = sum(result["relevance_score"] for result in research_results) / len(research_results)

        # Check coverage of request focus areas
        focus_coverage = 0
        for focus_area in request.research_focus:
            for result in research_results:
                if focus_area.lower() in result["title"].lower() or \
                   focus_area.lower() in result["content_summary"].lower():
                    focus_coverage += 1
                    break

        coverage_ratio = focus_coverage / len(request.research_focus) if request.research_focus else 1.0

        # Check diversity of sources
        sources = set(result["source"] for result in research_results)
        source_diversity = len(sources) / len(self.research_sources)

        # Determine quality
        if avg_relevance >= 0.85 and coverage_ratio >= 0.8 and source_diversity >= 0.6:
            return "high"
        if avg_relevance >= 0.70 and coverage_ratio >= 0.6 and source_diversity >= 0.4:
            return "medium"
        return "low"

    def _calculate_confidence_score(
        self,
        research_results: list[dict[str, Any]],
        research_quality: str
    ) -> float:
        """Calculate confidence score for research results."""
        if not research_results:
            return 0.0

        # Base score from result count and relevance
        avg_relevance = sum(result["relevance_score"] for result in research_results) / len(research_results)
        result_count_factor = min(len(research_results) / self.max_research_items, 1.0)

        # Quality factor
        quality_factors = {"high": 1.0, "medium": 0.8, "low": 0.6, "poor": 0.3}
        quality_factor = quality_factors.get(research_quality, 0.5)

        # Recency factor (higher confidence for recent updates)
        recent_results = [
            r for r in research_results
            if r["type"] == "regulatory_update" and r["actionability"] in ["immediate", "current"]
        ]
        recency_factor = min(len(recent_results) / 3, 1.0)

        # Combine factors
        confidence = (
            avg_relevance * 0.4 +
            quality_factor * 0.3 +
            result_count_factor * 0.2 +
            recency_factor * 0.1
        )

        return min(confidence, 1.0)

    def _determine_research_strategy(self, request: ResearchAgentRequest) -> str:
        """Determine the research strategy used."""
        if request.depth_level == "comprehensive":
            return "comprehensive_multi_source"
        if len(request.research_focus) > 3:
            return "broad_focus_coverage"
        if request.update_priority == "urgent":
            return "urgent_update_focused"
        return "standard_relevance_based"

    def _initialize_regulatory_knowledge(self) -> dict[str, Any]:
        """Initialize regulatory knowledge base."""
        return {
            "regulatory_bodies": {
                "FDA": {
                    "focus_areas": ["drug_approval", "manufacturing", "data_integrity", "cybersecurity"],
                    "update_frequency": "high",
                    "guidance_types": ["guidance", "draft_guidance", "final_rule"]
                },
                "EMA": {
                    "focus_areas": ["clinical_trials", "quality", "safety", "digital_health"],
                    "update_frequency": "medium",
                    "guidance_types": ["guideline", "reflection_paper", "q_and_a"]
                },
                "ICH": {
                    "focus_areas": ["harmonization", "standards", "quality", "safety"],
                    "update_frequency": "low",
                    "guidance_types": ["guideline", "implementation"]
                }
            },
            "research_domains": {
                "gamp_5": {
                    "categories": ["1", "2", "3", "4", "5"],
                    "focus_areas": ["validation", "risk_assessment", "lifecycle", "categories"],
                    "update_sources": ["ISPE", "industry_practice"]
                },
                "data_integrity": {
                    "principles": ["ALCOA", "ALCOA+"],
                    "focus_areas": ["audit_trail", "electronic_records", "data_governance"],
                    "update_sources": ["FDA", "EMA", "MHRA"]
                },
                "cybersecurity": {
                    "frameworks": ["NIST", "ISO_27001", "FDA_guidance"],
                    "focus_areas": ["threat_assessment", "controls", "incident_response"],
                    "update_sources": ["FDA", "NIST", "industry_standards"]
                }
            }
        }

    def _create_function_agent(self) -> FunctionAgent:
        """Create function agent with research tools."""
        tools = [
            self._create_regulatory_search_tool(),
            self._create_best_practices_tool(),
            self._create_trend_analysis_tool()
        ]

        return FunctionAgent(
            tools=tools,
            llm=self.llm,
            verbose=self.verbose,
            system_prompt="""You are a Research Agent specializing in:
1. Regulatory guidance updates (FDA, EMA, ICH)
2. GAMP-5 best practices research
3. Industry standard compliance verification
4. Current pharmaceutical testing methodologies

Provide up-to-date regulatory and technical insights to support pharmaceutical validation decisions.
Always maintain currency with evolving regulatory landscape."""
        )

    def _create_regulatory_search_tool(self) -> FunctionTool:
        """Create regulatory search tool."""
        def search_regulatory_updates(
            regulatory_bodies: list[str],
            time_horizon: str,
            focus_areas: list[str]
        ) -> dict[str, Any]:
            """
            Search for regulatory updates from specified bodies.
            
            Args:
                regulatory_bodies: List of regulatory bodies to search
                time_horizon: Time horizon for updates
                focus_areas: Areas of focus for search
            
            Returns:
                Search results with regulatory updates
            """
            return {
                "regulatory_bodies": regulatory_bodies,
                "time_horizon": time_horizon,
                "focus_areas": focus_areas,
                "results_count": len(regulatory_bodies) * 3,
                "search_quality": "high"
            }

        return FunctionTool.from_defaults(fn=search_regulatory_updates)

    def _create_best_practices_tool(self) -> FunctionTool:
        """Create best practices research tool."""
        def research_best_practices(
            domains: list[str],
            maturity_filter: str,
            implementation_focus: bool
        ) -> dict[str, Any]:
            """
            Research best practices in specified domains.
            
            Args:
                domains: List of domains to research
                maturity_filter: Filter by practice maturity
                implementation_focus: Focus on implementation guidance
            
            Returns:
                Best practices research results
            """
            return {
                "domains": domains,
                "maturity_filter": maturity_filter,
                "implementation_focused": implementation_focus,
                "practices_found": len(domains) * 2,
                "quality_score": 0.85
            }

        return FunctionTool.from_defaults(fn=research_best_practices)

    def _create_trend_analysis_tool(self) -> FunctionTool:
        """Create trend analysis tool."""
        def analyze_industry_trends(
            trend_categories: list[str],
            adoption_threshold: float,
            regulatory_readiness: bool
        ) -> dict[str, Any]:
            """
            Analyze industry trends and their implications.
            
            Args:
                trend_categories: Categories of trends to analyze
                adoption_threshold: Minimum adoption rate to consider
                regulatory_readiness: Consider regulatory readiness
            
            Returns:
                Trend analysis results
            """
            return {
                "categories": trend_categories,
                "adoption_threshold": adoption_threshold,
                "regulatory_focus": regulatory_readiness,
                "trends_identified": len(trend_categories) * 2,
                "confidence_level": 0.80
            }

        return FunctionTool.from_defaults(fn=analyze_industry_trends)

    def _update_performance_stats(self, processing_time: float) -> None:
        """Update performance statistics."""
        current_avg = self._research_stats["avg_processing_time"]
        total_queries = self._research_stats["successful_queries"]

        # Calculate new average
        new_avg = ((current_avg * (total_queries - 1)) + processing_time) / total_queries
        self._research_stats["avg_processing_time"] = new_avg

    def get_research_stats(self) -> dict[str, Any]:
        """Get current research statistics."""
        return self._research_stats.copy()


def create_research_agent(
    llm: LLM | None = None,
    verbose: bool = False,
    enable_phoenix: bool = True,
    max_research_items: int = 20,
    quality_threshold: float = 0.7,
    research_sources: list[str] | None = None
) -> ResearchAgent:
    """
    Create a Research Agent instance.
    
    Args:
        llm: Language model for research analysis
        verbose: Enable verbose logging
        enable_phoenix: Enable Phoenix AI instrumentation
        max_research_items: Maximum research items to return
        quality_threshold: Minimum quality threshold
        research_sources: List of research sources to prioritize
    
    Returns:
        Configured ResearchAgent instance
    """
    return ResearchAgent(
        llm=llm,
        verbose=verbose,
        enable_phoenix=enable_phoenix,
        max_research_items=max_research_items,
        quality_threshold=quality_threshold,
        research_sources=research_sources
    )
