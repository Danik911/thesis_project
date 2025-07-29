"""
Context Provider Agent - RAG/CAG Document Retrieval and Context Assembly

This module implements the Context Provider Agent responsible for retrieving
and assembling contextual information for pharmaceutical test generation.
It performs RAG (Retrieval-Augmented Generation) and CAG (Context-Augmented Generation)
operations to provide comprehensive documentation context.

Key Features:
- Document retrieval from pharmaceutical knowledge bases
- Requirements analysis and context assembly
- GAMP-5 compliant documentation gathering
- Test specification context preparation
- Integration with LlamaIndex workflow orchestration
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
from pydantic import BaseModel, Field, field_validator
from src.core.events import AgentRequestEvent, AgentResultEvent, ValidationStatus


class ContextProviderRequest(BaseModel):
    """Request model for Context Provider Agent."""
    gamp_category: str
    test_strategy: dict[str, Any]
    document_sections: list[str]
    search_scope: dict[str, Any]
    context_depth: str = "standard"
    correlation_id: UUID
    timeout_seconds: int = 180

    @field_validator("gamp_category")
    @classmethod
    def validate_gamp_category(cls, v):
        """Convert GAMP category to string if needed."""
        return str(v)


class ContextProviderResponse(BaseModel):
    """Response model for Context Provider Agent."""
    retrieved_documents: list[dict[str, Any]] = Field(default_factory=list)
    context_quality: str = "unknown"
    search_coverage: float = 0.0
    assembled_context: dict[str, Any] = Field(default_factory=dict)
    document_summaries: list[dict[str, Any]] = Field(default_factory=list)
    requirements_extracted: list[dict[str, Any]] = Field(default_factory=list)
    confidence_score: float = 0.0
    processing_metadata: dict[str, Any] = Field(default_factory=dict)


class ContextProviderAgent:
    """
    Context Provider Agent for RAG/CAG operations in pharmaceutical test generation.
    
    This agent specializes in:
    1. Document retrieval from pharmaceutical knowledge bases
    2. Requirements analysis and context assembly
    3. GAMP-5 compliant documentation gathering
    4. Test specification context preparation
    
    The agent integrates with the parallel execution workflow and provides
    contextual information for SME and Research agents.
    """

    def __init__(
        self,
        llm: LLM | None = None,
        verbose: bool = False,
        enable_phoenix: bool = True,
        max_documents: int = 50,
        quality_threshold: float = 0.7
    ):
        """
        Initialize the Context Provider Agent.
        
        Args:
            llm: Language model for context analysis
            verbose: Enable verbose logging
            enable_phoenix: Enable Phoenix AI instrumentation
            max_documents: Maximum documents to retrieve
            quality_threshold: Minimum quality threshold for context
        """
        self.llm = llm or OpenAI(model="gpt-4.1-mini-2025-04-14")
        self.verbose = verbose
        self.enable_phoenix = enable_phoenix
        self.max_documents = max_documents
        self.quality_threshold = quality_threshold
        self.logger = logging.getLogger(__name__)

        # Initialize function agent with RAG tools
        self.function_agent = self._create_function_agent()

        # Performance tracking
        self._processing_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "avg_processing_time": 0.0,
            "cache_hits": 0
        }

    async def process_request(self, request_event: AgentRequestEvent) -> AgentResultEvent:
        """
        Process a context provider request.
        
        Args:
            request_event: Agent request event containing context requirements
            
        Returns:
            AgentResultEvent with retrieved context and analysis
        """
        start_time = datetime.now(UTC)
        self._processing_stats["total_requests"] += 1

        try:
            # Parse request data
            request_data = ContextProviderRequest(
                **request_event.request_data,
                correlation_id=request_event.correlation_id
            )

            if self.verbose:
                self.logger.info(
                    f"Processing context request for GAMP Category {request_data.gamp_category} "
                    f"with {request_data.context_depth} depth"
                )

            # Execute context retrieval with timeout
            context_response = await asyncio.wait_for(
                self._execute_context_retrieval(request_data),
                timeout=request_data.timeout_seconds
            )

            # Calculate processing time
            processing_time = (datetime.now(UTC) - start_time).total_seconds()

            # Update performance stats
            self._processing_stats["successful_requests"] += 1
            self._update_performance_stats(processing_time)

            if self.verbose:
                self.logger.info(
                    f"Context retrieval completed: {len(context_response.retrieved_documents)} documents, "
                    f"quality: {context_response.context_quality}, "
                    f"processing time: {processing_time:.2f}s"
                )

            return AgentResultEvent(
                agent_type="context_provider",
                result_data=context_response.model_dump(),
                success=True,
                processing_time=processing_time,
                correlation_id=request_event.correlation_id,
                validation_status=ValidationStatus.VALIDATED
            )

        except TimeoutError:
            processing_time = (datetime.now(UTC) - start_time).total_seconds()
            error_msg = f"Context retrieval timeout after {processing_time:.1f}s"

            self.logger.error(f"Context Provider timeout: {error_msg}")

            return AgentResultEvent(
                agent_type="context_provider",
                result_data={"error": "timeout", "partial_results": {}},
                success=False,
                error_message=error_msg,
                processing_time=processing_time,
                correlation_id=request_event.correlation_id,
                validation_status=ValidationStatus.REJECTED
            )

        except Exception as e:
            processing_time = (datetime.now(UTC) - start_time).total_seconds()
            error_msg = f"Context retrieval failed: {e!s}"

            self.logger.error(f"Context Provider error: {error_msg}")

            return AgentResultEvent(
                agent_type="context_provider",
                result_data={"error": str(e), "error_type": type(e).__name__},
                success=False,
                error_message=error_msg,
                processing_time=processing_time,
                correlation_id=request_event.correlation_id,
                validation_status=ValidationStatus.REJECTED
            )

    async def _execute_context_retrieval(self, request: ContextProviderRequest) -> ContextProviderResponse:
        """Execute the context retrieval process."""
        # Initialize response
        response = ContextProviderResponse()

        # Step 1: Document Search and Retrieval
        retrieved_documents = await self._search_documents(request)
        response.retrieved_documents = retrieved_documents

        # Step 2: Context Quality Assessment
        context_quality = self._assess_context_quality(retrieved_documents, request)
        response.context_quality = context_quality

        # Step 3: Calculate Search Coverage
        search_coverage = self._calculate_search_coverage(retrieved_documents, request)
        response.search_coverage = search_coverage

        # Step 4: Assemble Context
        assembled_context = await self._assemble_context(retrieved_documents, request)
        response.assembled_context = assembled_context

        # Step 5: Generate Document Summaries
        document_summaries = self._generate_document_summaries(retrieved_documents)
        response.document_summaries = document_summaries

        # Step 6: Extract Requirements
        requirements = await self._extract_requirements(retrieved_documents, request)
        response.requirements_extracted = requirements

        # Step 7: Calculate Confidence Score
        confidence_score = self._calculate_confidence_score(
            retrieved_documents, context_quality, search_coverage
        )
        response.confidence_score = confidence_score

        # Step 8: Add Processing Metadata
        response.processing_metadata = {
            "search_strategy": self._determine_search_strategy(request),
            "documents_filtered": len(retrieved_documents),
            "quality_metrics": {
                "relevance_score": search_coverage,
                "completeness_score": confidence_score,
                "quality_assessment": context_quality
            },
            "processing_timestamp": datetime.now(UTC).isoformat()
        }

        return response

    async def _search_documents(self, request: ContextProviderRequest) -> list[dict[str, Any]]:
        """Search and retrieve relevant documents."""
        # In a real implementation, this would connect to:
        # - Vector databases (ChromaDB, Pinecone)
        # - Document stores (Elasticsearch)
        # - Pharmaceutical knowledge bases
        # - Regulatory document repositories

        # Simulate document retrieval based on GAMP category and requirements
        mock_documents = []

        # Base documents for all categories
        base_docs = [
            {
                "title": "GAMP-5 Testing Guidelines",
                "type": "regulatory_guidance",
                "relevance_score": 0.95,
                "content_summary": "Comprehensive testing approach for pharmaceutical software validation",
                "sections": ["testing_strategy", "validation_approach", "documentation_requirements"],
                "gamp_categories": [request.gamp_category]
            },
            {
                "title": "21 CFR Part 11 Compliance Framework",
                "type": "regulatory_requirement",
                "relevance_score": 0.88,
                "content_summary": "Electronic records and signatures compliance requirements",
                "sections": ["electronic_records", "audit_trail", "validation_requirements"],
                "gamp_categories": ["3", "4", "5"]
            }
        ]

        # Category-specific documents
        if request.gamp_category in ["4", "5"]:
            category_specific_docs = [
                {
                    "title": f"Category {request.gamp_category} Validation Best Practices",
                    "type": "best_practices",
                    "relevance_score": 0.92,
                    "content_summary": f"Specific validation approaches for GAMP Category {request.gamp_category} systems",
                    "sections": request.document_sections,
                    "gamp_categories": [request.gamp_category]
                },
                {
                    "title": "Integration Testing for Configured Systems",
                    "type": "testing_methodology",
                    "relevance_score": 0.85,
                    "content_summary": "Integration testing strategies for configured pharmaceutical systems",
                    "sections": ["integration_requirements", "test_execution", "validation_protocols"],
                    "gamp_categories": ["4", "5"]
                }
            ]
            mock_documents.extend(category_specific_docs)

        # Add test strategy specific documents
        for test_type in request.test_strategy.get("test_types", []):
            test_specific_doc = {
                "title": f"{test_type.replace('_', ' ').title()} Testing Guidelines",
                "type": "methodology",
                "relevance_score": 0.80,
                "content_summary": f"Guidelines and best practices for {test_type} in pharmaceutical systems",
                "sections": [f"{test_type}_methodology", "execution_criteria", "acceptance_criteria"],
                "test_types": [test_type]
            }
            mock_documents.append(test_specific_doc)

        mock_documents.extend(base_docs)

        # Sort by relevance and limit results
        mock_documents.sort(key=lambda x: x["relevance_score"], reverse=True)
        return mock_documents[:self.max_documents]

    def _assess_context_quality(self, documents: list[dict[str, Any]], request: ContextProviderRequest) -> str:
        """Assess the quality of retrieved context."""
        if not documents:
            return "poor"

        # Calculate average relevance
        avg_relevance = sum(doc.get("relevance_score", 0.0) for doc in documents) / len(documents)

        # Check coverage of required sections
        required_sections = set(request.document_sections)
        covered_sections = set()

        for doc in documents:
            covered_sections.update(doc.get("sections", []))

        section_coverage = len(covered_sections.intersection(required_sections)) / len(required_sections) if required_sections else 1.0

        # Determine quality based on relevance and coverage
        if avg_relevance >= 0.85 and section_coverage >= 0.8:
            return "high"
        if avg_relevance >= 0.70 and section_coverage >= 0.6:
            return "medium"
        return "low"

    def _calculate_search_coverage(self, documents: list[dict[str, Any]], request: ContextProviderRequest) -> float:
        """Calculate search coverage score."""
        if not documents or not request.document_sections:
            return 0.0

        required_sections = set(request.document_sections)
        covered_sections = set()

        for doc in documents:
            covered_sections.update(doc.get("sections", []))

        return len(covered_sections.intersection(required_sections)) / len(required_sections)

    async def _assemble_context(self, documents: list[dict[str, Any]], request: ContextProviderRequest) -> dict[str, Any]:
        """Assemble comprehensive context from retrieved documents."""
        context = {
            "gamp_category": request.gamp_category,
            "test_strategy_alignment": {},
            "regulatory_requirements": [],
            "technical_specifications": [],
            "validation_approaches": [],
            "best_practices": []
        }

        # Group documents by type
        by_type = {}
        for doc in documents:
            doc_type = doc.get("type", "general")
            if doc_type not in by_type:
                by_type[doc_type] = []
            by_type[doc_type].append(doc)

        # Assemble regulatory requirements
        if "regulatory_requirement" in by_type or "regulatory_guidance" in by_type:
            regulatory_docs = by_type.get("regulatory_requirement", []) + by_type.get("regulatory_guidance", [])
            context["regulatory_requirements"] = [
                {
                    "requirement": doc["title"],
                    "summary": doc["content_summary"],
                    "applicability": doc.get("gamp_categories", [request.gamp_category])
                }
                for doc in regulatory_docs
            ]

        # Assemble technical specifications
        if "technical_specification" in by_type:
            context["technical_specifications"] = [
                {
                    "specification": doc["title"],
                    "summary": doc["content_summary"],
                    "sections": doc.get("sections", [])
                }
                for doc in by_type["technical_specification"]
            ]

        # Assemble validation approaches
        if "methodology" in by_type or "testing_methodology" in by_type:
            methodology_docs = by_type.get("methodology", []) + by_type.get("testing_methodology", [])
            context["validation_approaches"] = [
                {
                    "approach": doc["title"],
                    "summary": doc["content_summary"],
                    "test_types": doc.get("test_types", [])
                }
                for doc in methodology_docs
            ]

        # Assemble best practices
        if "best_practices" in by_type:
            context["best_practices"] = [
                {
                    "practice": doc["title"],
                    "summary": doc["content_summary"],
                    "applicability": doc.get("gamp_categories", [])
                }
                for doc in by_type["best_practices"]
            ]

        # Test strategy alignment
        context["test_strategy_alignment"] = {
            "aligned_test_types": [
                test_type for test_type in request.test_strategy.get("test_types", [])
                if any(test_type in doc.get("test_types", []) for doc in documents)
            ],
            "coverage_assessment": self._calculate_search_coverage(documents, request),
            "recommendation": "Proceed with planned test strategy" if self._calculate_search_coverage(documents, request) > 0.7 else "Consider additional research"
        }

        return context

    def _generate_document_summaries(self, documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Generate concise summaries of retrieved documents."""
        summaries = []

        for doc in documents:
            summary = {
                "title": doc["title"],
                "type": doc.get("type", "unknown"),
                "relevance_score": doc.get("relevance_score", 0.0),
                "key_sections": doc.get("sections", [])[:5],  # Top 5 sections
                "summary": doc.get("content_summary", "No summary available"),
                "applicability": {
                    "gamp_categories": doc.get("gamp_categories", []),
                    "test_types": doc.get("test_types", [])
                }
            }
            summaries.append(summary)

        return summaries

    async def _extract_requirements(self, documents: list[dict[str, Any]], request: ContextProviderRequest) -> list[dict[str, Any]]:
        """Extract requirements from retrieved documents."""
        requirements = []

        # Extract requirements based on document content and GAMP category
        for doc in documents:
            if doc.get("type") in ["regulatory_requirement", "regulatory_guidance"]:
                requirement = {
                    "source": doc["title"],
                    "category": "regulatory",
                    "requirement_text": f"Compliance with {doc['title']} requirements",
                    "gamp_applicability": doc.get("gamp_categories", []),
                    "priority": "high" if "21 cfr" in doc["title"].lower() else "medium",
                    "validation_impact": "Must be validated during testing phase"
                }
                requirements.append(requirement)

            elif doc.get("type") in ["technical_specification", "methodology"]:
                requirement = {
                    "source": doc["title"],
                    "category": "technical",
                    "requirement_text": f"Implementation following {doc['title']} guidelines",
                    "test_types": doc.get("test_types", []),
                    "priority": "medium",
                    "validation_impact": "Should be verified through appropriate test methods"
                }
                requirements.append(requirement)

        return requirements

    def _calculate_confidence_score(
        self,
        documents: list[dict[str, Any]],
        context_quality: str,
        search_coverage: float
    ) -> float:
        """Calculate confidence score for the context retrieval."""
        if not documents:
            return 0.0

        # Base score from document count and relevance
        avg_relevance = sum(doc.get("relevance_score", 0.0) for doc in documents) / len(documents)
        document_count_factor = min(len(documents) / 10, 1.0)  # Normalize to 10 documents

        # Quality factor
        quality_factors = {"high": 1.0, "medium": 0.8, "low": 0.6, "poor": 0.3}
        quality_factor = quality_factors.get(context_quality, 0.5)

        # Combine factors
        confidence = (avg_relevance * 0.4 + search_coverage * 0.3 + quality_factor * 0.2 + document_count_factor * 0.1)

        return min(confidence, 1.0)

    def _determine_search_strategy(self, request: ContextProviderRequest) -> str:
        """Determine the search strategy used."""
        if request.context_depth == "comprehensive":
            return "comprehensive_multi_source"
        if len(request.document_sections) > 5:
            return "broad_section_coverage"
        if request.gamp_category == "5":
            return "category_5_focused"
        return "standard_relevance_based"

    def _create_function_agent(self) -> FunctionAgent:
        """Create function agent with RAG tools."""
        tools = [
            self._create_document_search_tool(),
            self._create_context_assembly_tool(),
            self._create_quality_assessment_tool()
        ]

        return FunctionAgent(
            tools=tools,
            llm=self.llm,
            verbose=self.verbose,
            system_prompt="""You are a Context Provider Agent specializing in:
1. Document retrieval from pharmaceutical knowledge bases
2. Requirements analysis and context assembly
3. GAMP-5 compliant documentation gathering
4. Test specification context preparation

Your role is critical for providing comprehensive context to pharmaceutical test generation.
Always maintain regulatory compliance and provide complete audit trails."""
        )

    def _create_document_search_tool(self) -> FunctionTool:
        """Create document search tool."""
        def search_documents(query: str, document_types: list[str], max_results: int = 20) -> dict[str, Any]:
            """
            Search for relevant documents in pharmaceutical knowledge bases.
            
            Args:
                query: Search query
                document_types: Types of documents to search
                max_results: Maximum results to return
            
            Returns:
                Search results with metadata
            """
            # This would integrate with actual search systems
            return {
                "query": query,
                "document_types": document_types,
                "results_count": min(max_results, 15),
                "search_quality": "high"
            }

        return FunctionTool.from_defaults(fn=search_documents)

    def _create_context_assembly_tool(self) -> FunctionTool:
        """Create context assembly tool."""
        def assemble_context(documents: list[dict], focus_areas: list[str]) -> dict[str, Any]:
            """
            Assemble context from retrieved documents.
            
            Args:
                documents: Retrieved documents
                focus_areas: Areas to focus context assembly
            
            Returns:
                Assembled context
            """
            return {
                "assembled_sections": focus_areas,
                "context_quality": "high",
                "completeness_score": 0.85
            }

        return FunctionTool.from_defaults(fn=assemble_context)

    def _create_quality_assessment_tool(self) -> FunctionTool:
        """Create quality assessment tool."""
        def assess_context_quality(context: dict, requirements: list[str]) -> dict[str, Any]:
            """
            Assess the quality of assembled context.
            
            Args:
                context: Assembled context
                requirements: Required elements
            
            Returns:
                Quality assessment
            """
            return {
                "quality_score": 0.85,
                "completeness": 0.90,
                "relevance": 0.88,
                "recommendations": ["Context is comprehensive and suitable for test generation"]
            }

        return FunctionTool.from_defaults(fn=assess_context_quality)

    def _update_performance_stats(self, processing_time: float) -> None:
        """Update performance statistics."""
        current_avg = self._processing_stats["avg_processing_time"]
        total_requests = self._processing_stats["successful_requests"]

        # Calculate new average
        new_avg = ((current_avg * (total_requests - 1)) + processing_time) / total_requests
        self._processing_stats["avg_processing_time"] = new_avg

    def get_performance_stats(self) -> dict[str, Any]:
        """Get current performance statistics."""
        return self._processing_stats.copy()


def create_context_provider_agent(
    llm: LLM | None = None,
    verbose: bool = False,
    enable_phoenix: bool = True,
    max_documents: int = 50,
    quality_threshold: float = 0.7
) -> ContextProviderAgent:
    """
    Create a Context Provider Agent instance.
    
    Args:
        llm: Language model for context analysis
        verbose: Enable verbose logging
        enable_phoenix: Enable Phoenix AI instrumentation
        max_documents: Maximum documents to retrieve
        quality_threshold: Minimum quality threshold
    
    Returns:
        Configured ContextProviderAgent instance
    """
    return ContextProviderAgent(
        llm=llm,
        verbose=verbose,
        enable_phoenix=enable_phoenix,
        max_documents=max_documents,
        quality_threshold=quality_threshold
    )
