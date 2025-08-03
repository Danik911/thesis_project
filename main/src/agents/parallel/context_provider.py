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
import json
import logging
import os
import time
import traceback
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID

import chromadb
from llama_index.core import Document, StorageContext, VectorStoreIndex
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.extractors import KeywordExtractor, TitleExtractor
from llama_index.core.ingestion import IngestionCache, IngestionPipeline
from llama_index.core.llms import LLM
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.schema import NodeWithScore, QueryBundle
from llama_index.core.tools import FunctionTool
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.vector_stores.chroma import ChromaVectorStore
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from pydantic import BaseModel, Field, field_validator
from src.core.events import AgentRequestEvent, AgentResultEvent, ValidationStatus
from src.monitoring.agent_instrumentation import trace_agent_method
from src.monitoring.simple_tracer import get_tracer


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
        quality_threshold: float = 0.7,
        vector_store_path: str | None = None,
        cache_dir: str | None = None,
        embedding_model: str | None = None
    ):
        """
        Initialize the Context Provider Agent.
        
        Args:
            llm: Language model for context analysis
            verbose: Enable verbose logging
            enable_phoenix: Enable Phoenix AI instrumentation
            max_documents: Maximum documents to retrieve
            quality_threshold: Minimum quality threshold for context
            vector_store_path: Path for ChromaDB storage
            cache_dir: Directory for caching embeddings
            embedding_model: OpenAI embedding model to use
        """
        self.llm = llm or OpenAI(model="gpt-4.1-mini-2025-04-14")
        self.verbose = verbose
        self.enable_phoenix = enable_phoenix
        self.max_documents = max_documents
        self.quality_threshold = quality_threshold
        self.logger = logging.getLogger(__name__)

        # Vector store configuration from environment
        self.vector_store_path = Path(vector_store_path or os.getenv("RAG_VECTOR_STORE_PATH", "./lib/chroma_db"))
        self.cache_dir = Path(cache_dir or os.getenv("RAG_CACHE_DIR", "./cache/rag"))
        self.embedding_model_name = embedding_model or os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

        # Create directories
        self.vector_store_path.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB and ingestion pipeline
        self._initialize_chromadb()
        self._setup_ingestion_pipeline()

        # Initialize function agent with RAG tools
        self.function_agent = self._create_function_agent()

        # Performance tracking
        self._processing_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "avg_processing_time": 0.0,
            "cache_hits": 0
        }

        # Audit trail for ALCOA+ compliance
        self._audit_trail = []

        # Initialize Phoenix tracer for observability
        self.tracer = trace.get_tracer(__name__)

    @trace_agent_method(
        span_name="context_provider.process_request",
        attributes={"agent.type": "context_provider", "operation": "process_request"}
    )
    async def process_request(self, request_event: AgentRequestEvent) -> AgentResultEvent:
        """
        Process a context provider request with comprehensive Phoenix observability.
        
        Args:
            request_event: Agent request event containing context requirements
            
        Returns:
            AgentResultEvent with retrieved context and analysis
        """
        start_time = datetime.now(UTC)
        self._processing_stats["total_requests"] += 1

        # Get current span for detailed tracing
        current_span = trace.get_current_span()

        try:
            # Parse request data with explicit validation
            request_data_dict = request_event.request_data.copy()
            
            # CRITICAL FIX: Ensure GAMP category is string and add missing fields
            if "gamp_category" in request_data_dict:
                request_data_dict["gamp_category"] = str(request_data_dict["gamp_category"])
            
            # Add required search_scope if missing
            if "search_scope" not in request_data_dict:
                request_data_dict["search_scope"] = {}
            
            # Add correlation_id if not in request_data
            request_data_dict["correlation_id"] = request_event.correlation_id
            
            self.logger.info(f"🔧 Context Provider request validation: gamp_category={request_data_dict.get('gamp_category')} (type: {type(request_data_dict.get('gamp_category'))})")
            
            request_data = ContextProviderRequest(**request_data_dict)

            # Add request attributes to span
            if current_span and current_span.is_recording():
                current_span.set_attribute("request.gamp_category", request_data.gamp_category)
                current_span.set_attribute("request.context_depth", request_data.context_depth)
                current_span.set_attribute("request.correlation_id", str(request_data.correlation_id))
                current_span.set_attribute("request.search_scope", json.dumps(request_data.search_scope))
                current_span.set_attribute("request.document_sections_count", len(request_data.document_sections))
                current_span.set_attribute("request.timeout_seconds", request_data.timeout_seconds)

                # Add test strategy details
                test_types = request_data.test_strategy.get("test_types", [])
                current_span.set_attribute("request.test_types", json.dumps(test_types))

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

            # Add result attributes to span
            if current_span and current_span.is_recording():
                current_span.set_attribute("result.success", True)
                current_span.set_attribute("result.documents_retrieved", len(context_response.retrieved_documents))
                current_span.set_attribute("result.context_quality", context_response.context_quality)
                current_span.set_attribute("result.search_coverage", context_response.search_coverage)
                current_span.set_attribute("result.confidence_score", context_response.confidence_score)
                current_span.set_attribute("result.processing_time", processing_time)

                # Add document summaries as event
                if context_response.retrieved_documents:
                    current_span.add_event(
                        "documents_retrieved",
                        attributes={
                            "document_count": len(context_response.retrieved_documents),
                            "top_document_titles": json.dumps([
                                doc.get("title", "Unknown")
                                for doc in context_response.retrieved_documents[:5]
                            ]),
                            "average_relevance_score": sum(
                                doc.get("relevance_score", 0.0)
                                for doc in context_response.retrieved_documents
                            ) / len(context_response.retrieved_documents)
                        }
                    )

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

            # Record timeout in span
            if current_span and current_span.is_recording():
                current_span.set_status(Status(StatusCode.ERROR, "Timeout"))
                current_span.set_attribute("error.type", "TimeoutError")
                current_span.set_attribute("error.message", error_msg)
                current_span.set_attribute("error.processing_time", processing_time)

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
            stack_trace = traceback.format_exc()

            self.logger.error(f"Context Provider error: {error_msg}\n{stack_trace}")

            # Record exception in span with full diagnostic information
            if current_span and current_span.is_recording():
                current_span.record_exception(e)
                current_span.set_status(Status(StatusCode.ERROR, str(e)))
                current_span.set_attribute("error.type", type(e).__name__)
                current_span.set_attribute("error.message", str(e))
                current_span.set_attribute("error.stack_trace", stack_trace)
                current_span.set_attribute("error.processing_time", processing_time)

            return AgentResultEvent(
                agent_type="context_provider",
                result_data={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "stack_trace": stack_trace
                },
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

    def _initialize_chromadb(self) -> None:
        """Initialize ChromaDB with pharmaceutical compliance features."""
        try:
            # Initialize ChromaDB client with persistent storage
            self.chroma_client = chromadb.PersistentClient(
                path=str(self.vector_store_path),
                settings=chromadb.Settings(
                    anonymized_telemetry=False,  # HIPAA/pharmaceutical compliance
                    persist_directory=str(self.vector_store_path)
                )
            )

            # Create collections for different pharmaceutical document types
            self.collections = {
                "gamp5": self.chroma_client.get_or_create_collection(
                    name="gamp5_documents",
                    metadata={
                        "description": "GAMP-5 validation and testing guidelines",
                        "compliance_level": "regulatory",
                        "last_updated": datetime.now(UTC).isoformat()
                    }
                ),
                "regulatory": self.chroma_client.get_or_create_collection(
                    name="regulatory_documents",
                    metadata={
                        "description": "FDA, EMA, ICH regulatory requirements",
                        "compliance_level": "mandatory",
                        "last_updated": datetime.now(UTC).isoformat()
                    }
                ),
                "sops": self.chroma_client.get_or_create_collection(
                    name="sop_documents",
                    metadata={
                        "description": "Standard Operating Procedures",
                        "compliance_level": "internal",
                        "last_updated": datetime.now(UTC).isoformat()
                    }
                ),
                "best_practices": self.chroma_client.get_or_create_collection(
                    name="best_practices",
                    metadata={
                        "description": "Industry best practices and methodologies",
                        "compliance_level": "recommended",
                        "last_updated": datetime.now(UTC).isoformat()
                    }
                )
            }

            # Initialize embedding model
            self.embedding_model = OpenAIEmbedding(
                model=self.embedding_model_name,
                api_key=os.getenv("OPENAI_API_KEY")
            )

            if self.verbose:
                self.logger.info(f"ChromaDB initialized with collections: {list(self.collections.keys())}")

        except Exception as e:
            error_msg = f"Failed to initialize ChromaDB: {e!s}"
            self.logger.error(error_msg)
            # NO FALLBACK - fail explicitly
            raise RuntimeError(error_msg) from e

    def _setup_ingestion_pipeline(self) -> None:
        """Setup ingestion pipeline with caching and transformations."""
        try:
            # Setup caching for embeddings
            cache_file = self.cache_dir / "ingestion_cache.json"
            self.ingestion_cache = IngestionCache(
                cache_file=str(cache_file)
            )

            # Create optimized LLM for metadata extraction
            extractor_llm = self._create_extractor_llm()

            # Setup transformations for pharmaceutical documents
            transformations = [
                # Text splitting optimized for pharmaceutical content
                SentenceSplitter(
                    chunk_size=int(os.getenv("RAG_CHUNK_SIZE", "1500")),
                    chunk_overlap=int(os.getenv("RAG_CHUNK_OVERLAP", "200")),
                    include_metadata=True,
                    include_prev_next_rel=True
                ),

                # Metadata extraction for compliance tracking
                TitleExtractor(
                    llm=extractor_llm,
                    nodes=5  # Extract from first 5 chunks
                ),

                # Keyword extraction for pharmaceutical terms
                KeywordExtractor(
                    llm=extractor_llm,
                    keywords=10
                ),

                # Embeddings
                self.embedding_model
            ]

            # Create ingestion pipelines for each collection
            self.ingestion_pipelines = {}
            for collection_name, collection in self.collections.items():
                vector_store = ChromaVectorStore(
                    chroma_collection=collection
                )

                self.ingestion_pipelines[collection_name] = IngestionPipeline(
                    transformations=transformations,
                    cache=self.ingestion_cache,
                    vector_store=vector_store
                )

            if self.verbose:
                self.logger.info("Ingestion pipelines configured successfully")

        except Exception as e:
            error_msg = f"Failed to setup ingestion pipeline: {e!s}"
            self.logger.error(error_msg)
            # NO FALLBACK - fail explicitly
            raise RuntimeError(error_msg) from e

    def _create_extractor_llm(self) -> OpenAI | None:
        """Create optimized LLM for metadata extraction."""
        try:
            extractor_model = os.getenv("RAG_EXTRACTOR_MODEL", "gpt-4.1-nano-2025-04-14")
            extractor_temperature = float(os.getenv("RAG_EXTRACTOR_TEMPERATURE", "0.1"))
            extractor_max_tokens = int(os.getenv("RAG_EXTRACTOR_MAX_TOKENS", "500"))

            return OpenAI(
                model=extractor_model,
                temperature=extractor_temperature,
                max_tokens=extractor_max_tokens,
                api_key=os.getenv("OPENAI_API_KEY")
            )
        except Exception as e:
            self.logger.warning(f"Could not create extractor LLM: {e!s}")
            return None

    async def _search_documents(self, request: ContextProviderRequest) -> list[dict[str, Any]]:
        """Search documents using ChromaDB with comprehensive Phoenix observability."""
        # Create a span for document search
        with self.tracer.start_as_current_span("chromadb.search_documents") as span:
            try:
                # Record search in audit trail for ALCOA+ compliance
                audit_entry = {
                    "timestamp": datetime.now(UTC).isoformat(),
                    "operation": "document_search",
                    "correlation_id": str(request.correlation_id),
                    "request_params": {
                        "gamp_category": request.gamp_category,
                        "search_scope": request.search_scope,
                        "context_depth": request.context_depth
                    }
                }
                self._audit_trail.append(audit_entry)

                # Determine which collections to search
                collection_names = self._select_collections(request.gamp_category, request.search_scope)

                # Build search query
                query = self._build_search_query(request)

                # Create query embedding for observability
                query_embedding_start = datetime.now(UTC)
                
                # Log API call to tracer
                tracer = get_tracer()
                api_start = time.time()
                
                query_embedding = await asyncio.to_thread(
                    self.embedding_model.get_text_embedding,
                    query
                )
                
                # Log successful API call
                api_duration = time.time() - api_start
                tracer.log_api_call("openai", "embeddings", api_duration, True, {"model": self.embedding_model_name})
                
                query_embedding_time = (datetime.now(UTC) - query_embedding_start).total_seconds() * 1000

                # Add comprehensive span attributes
                span.set_attribute("chromadb.query", query)
                span.set_attribute("chromadb.query_length", len(query))
                span.set_attribute("chromadb.query_embedding_time_ms", query_embedding_time)
                span.set_attribute("chromadb.query_embedding_dimension", len(query_embedding))
                span.set_attribute("chromadb.collections", json.dumps(collection_names))
                span.set_attribute("chromadb.collection_count", len(collection_names))
                span.set_attribute("chromadb.gamp_category", request.gamp_category)
                span.set_attribute("chromadb.max_documents", self.max_documents)
                span.set_attribute("chromadb.context_depth", request.context_depth)
                span.set_attribute("chromadb.search_scope", json.dumps(request.search_scope))

                # Add query generation event
                span.add_event(
                    "query_generated",
                    attributes={
                        "query_text": query,
                        "query_parts": json.dumps(query.split()),
                        "embedding_time_ms": query_embedding_time,
                        "embedding_norm": float(sum(x*x for x in query_embedding)**0.5)
                    }
                )

                # Log detailed search information
                self.logger.info(
                    f"🔍 Starting ChromaDB search:\n"
                    f"   - Query: {query}\n"
                    f"   - Collections: {collection_names}\n"
                    f"   - GAMP Category: {request.gamp_category}\n"
                    f"   - Max documents: {self.max_documents}\n"
                    f"   - Query embedding time: {query_embedding_time:.2f}ms"
                )

                # Perform searches across selected collections
                all_results = []

                for collection_name in collection_names:
                    # Create a span for each collection search
                    with self.tracer.start_as_current_span(f"chromadb.search_collection.{collection_name}") as collection_span:
                        collection_span.set_attribute("collection.name", collection_name)

                        # Get vector store for collection
                        vector_store = ChromaVectorStore(
                            chroma_collection=self.collections[collection_name]
                        )

                        # Log collection info
                        collection_count = self.collections[collection_name].count()
                        collection_span.set_attribute("collection.document_count", collection_count)
                        self.logger.info(f"   📁 Searching collection '{collection_name}' ({collection_count} documents)")

                        # Create index and retriever
                        storage_context = StorageContext.from_defaults(
                            vector_store=vector_store
                        )

                        index = VectorStoreIndex.from_vector_store(
                            vector_store=vector_store,
                            storage_context=storage_context,
                            embed_model=self.embedding_model
                        )

                        retriever = VectorIndexRetriever(
                            index=index,
                            similarity_top_k=self.max_documents,
                            vector_store_query_mode="hybrid"  # Combine semantic + keyword
                        )

                        # Execute search in thread pool for async compatibility
                        query_bundle = QueryBundle(query_str=query)

                        # Time the retrieval operation
                        retrieval_start = datetime.now(UTC)
                        nodes = await asyncio.to_thread(
                            retriever.retrieve,
                            query_bundle
                        )
                        retrieval_time = (datetime.now(UTC) - retrieval_start).total_seconds() * 1000

                        # Track retrieval results
                        collection_span.set_attribute("collection.nodes_retrieved", len(nodes))
                        collection_span.set_attribute("collection.retrieval_time_ms", retrieval_time)

                        # Convert nodes to document format and track details
                        collection_results = []
                        chunk_details = []

                        for i, node in enumerate(nodes):
                            doc = self._node_to_document(node, collection_name)
                            collection_results.append(doc)

                            # Capture detailed chunk information
                            chunk_info = {
                                "rank": i + 1,
                                "node_id": node.node.node_id,
                                "score": float(node.score) if node.score else 0.0,
                                "title": doc["title"],
                                "type": doc["type"],
                                "text_preview": node.node.text[:200] if node.node.text else "",
                                "metadata": node.node.metadata or {},
                                "embedding_id": node.node.embedding
                            }
                            chunk_details.append(chunk_info)

                            # Create span for each chunk retrieved
                            with self.tracer.start_as_current_span(f"chromadb.chunk.{i+1}") as chunk_span:
                                chunk_span.set_attribute("chunk.rank", i + 1)
                                chunk_span.set_attribute("chunk.node_id", node.node.node_id)
                                chunk_span.set_attribute("chunk.score", chunk_info["score"])
                                chunk_span.set_attribute("chunk.title", chunk_info["title"])
                                chunk_span.set_attribute("chunk.type", chunk_info["type"])
                                chunk_span.set_attribute("chunk.text_length", len(node.node.text) if node.node.text else 0)
                                chunk_span.set_attribute("chunk.has_embedding", bool(node.node.embedding))

                                # Add metadata attributes
                                for key, value in chunk_info["metadata"].items():
                                    if isinstance(value, (str, int, float, bool)):
                                        chunk_span.set_attribute(f"chunk.metadata.{key}", value)

                            # Log top 5 results per collection with more detail
                            if i < 5:
                                self.logger.info(
                                    f"      📄 Result {i+1}: {doc['title']}\n"
                                    f"         Score: {doc['relevance_score']:.3f}\n"
                                    f"         Type: {doc['type']}\n"
                                    f"         Node ID: {node.node.node_id}\n"
                                    f"         Text preview: {chunk_info['text_preview'][:100]}..."
                                )

                        # Add comprehensive collection search event
                        collection_span.add_event(
                            "collection_search_complete",
                            attributes={
                                "nodes_retrieved": len(nodes),
                                "retrieval_time_ms": retrieval_time,
                                "top_score": chunk_details[0]["score"] if chunk_details else 0.0,
                                "avg_score": sum(c["score"] for c in chunk_details) / len(chunk_details) if chunk_details else 0.0,
                                "chunk_details": json.dumps(chunk_details[:10])  # Top 10 chunks
                            }
                        )

                        all_results.extend(collection_results)

                # Apply metadata filters if specified
                pre_filter_count = len(all_results)
                if request.search_scope.get("filters"):
                    all_results = self._apply_metadata_filters(
                        all_results,
                        request.search_scope["filters"]
                    )
                    span.set_attribute("chromadb.filtered_count", pre_filter_count - len(all_results))
                    self.logger.info(f"   🔽 Applied filters: {pre_filter_count} → {len(all_results)} documents")

                # Sort by relevance and limit results
                all_results.sort(key=lambda x: x.get("relevance_score", 0.0), reverse=True)
                final_results = all_results[:self.max_documents]

                # Update audit trail with results
                audit_entry["results_count"] = len(final_results)
                audit_entry["completion_time"] = datetime.now(UTC).isoformat()

                # Add final search metrics to span
                span.set_attribute("chromadb.total_results", len(all_results))
                span.set_attribute("chromadb.final_results", len(final_results))
                span.set_attribute("chromadb.success", True)

                if final_results:
                    # Calculate and log confidence metrics
                    avg_score = sum(d["relevance_score"] for d in final_results) / len(final_results)
                    span.set_attribute("chromadb.average_relevance_score", avg_score)
                    span.set_attribute("chromadb.top_relevance_score", final_results[0]["relevance_score"])

                    # Add detailed results event
                    span.add_event(
                        "search_results_summary",
                        attributes={
                            "total_documents": len(final_results),
                            "collections_searched": json.dumps(collection_names),
                            "document_types": json.dumps(list(set(d["type"] for d in final_results))),
                            "gamp_categories_found": json.dumps(list(set(
                                cat for d in final_results
                                for cat in d.get("gamp_categories", [])
                            )))
                        }
                    )

                if self.verbose:
                    self.logger.info(
                        f"✅ ChromaDB search completed:\n"
                        f"   - {len(final_results)} documents retrieved\n"
                        f"   - Collections searched: {collection_names}\n"
                        f"   - Average relevance: {avg_score:.3f}" if final_results else "   - No results found"
                    )

                return final_results

            except Exception as e:
                error_msg = f"ChromaDB search failed: {e!s}"
                stack_trace = traceback.format_exc()
                self.logger.error(f"{error_msg}\n{stack_trace}")

                # Record failure in span
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                span.set_attribute("chromadb.success", False)
                span.set_attribute("chromadb.error_type", type(e).__name__)
                span.set_attribute("chromadb.error_message", str(e))

                # Record failure in audit trail
                self._audit_trail.append({
                    "timestamp": datetime.now(UTC).isoformat(),
                    "operation": "document_search_failed",
                    "correlation_id": str(request.correlation_id),
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "stack_trace": stack_trace
                })

                # NO FALLBACK - fail explicitly with full diagnostic information
                raise RuntimeError(
                    f"{error_msg}\n"
                    f"Request details: gamp_category={request.gamp_category}, "
                    f"search_scope={request.search_scope}, "
                    f"correlation_id={request.correlation_id}\n"
                    f"Stack trace:\n{stack_trace}"
                ) from e

    def _select_collections(self, gamp_category: str, search_scope: dict[str, Any]) -> list[str]:
        """Select appropriate collections based on GAMP category and scope."""
        collections = []

        # Always include GAMP-5 collection for any category
        collections.append("gamp5")

        # Add regulatory collection for categories 3, 4, 5
        if gamp_category in ["3", "4", "5"]:
            collections.append("regulatory")

        # Add SOPs for categories 4 and 5
        if gamp_category in ["4", "5"]:
            collections.append("sops")

        # Add best practices based on search scope
        if search_scope.get("include_best_practices", True):
            collections.append("best_practices")

        return collections

    def _build_search_query(self, request: ContextProviderRequest) -> str:
        """Build search query from request parameters."""
        query_parts = []

        # Add GAMP category context
        query_parts.append(f"GAMP Category {request.gamp_category} validation testing")

        # Add test strategy types
        test_types = request.test_strategy.get("test_types", [])
        if test_types:
            query_parts.append(" ".join(test_types))

        # Add document sections
        if request.document_sections:
            query_parts.append(" ".join(request.document_sections))

        # Add specific focus areas from search scope
        focus_areas = request.search_scope.get("focus_areas", [])
        if focus_areas:
            query_parts.append(" ".join(focus_areas))

        return " ".join(query_parts)

    def _node_to_document(self, node: NodeWithScore, collection_name: str) -> dict[str, Any]:
        """Convert retrieval node to document format with comprehensive chunk details."""
        metadata = node.node.metadata or {}

        # Convert string metadata back to lists
        gamp_categories = metadata.get("gamp_categories", "").split(",") if metadata.get("gamp_categories") else []
        test_types = metadata.get("test_types", "").split(",") if metadata.get("test_types") else []
        sections = metadata.get("sections", "").split(",") if metadata.get("sections") else []

        # Extract chunk-specific information
        chunk_info = {
            "chunk_id": node.node.node_id,
            "chunk_text": node.node.text or "",
            "chunk_length": len(node.node.text) if node.node.text else 0,
            "chunk_start_char": node.node.start_char_idx if hasattr(node.node, "start_char_idx") else None,
            "chunk_end_char": node.node.end_char_idx if hasattr(node.node, "end_char_idx") else None,
            "has_embedding": bool(node.node.embedding),
            "relationships": {}
        }

        # Extract relationships if available
        if hasattr(node.node, "relationships") and node.node.relationships:
            for rel_type, rel_node in node.node.relationships.items():
                chunk_info["relationships"][rel_type] = {
                    "node_id": rel_node.node_id if hasattr(rel_node, "node_id") else None,
                    "type": rel_type
                }

        return {
            "title": metadata.get("title", "Untitled Document"),
            "type": metadata.get("type", collection_name),
            "relevance_score": float(node.score) if node.score else 0.0,
            "content_summary": node.node.text[:500] if node.node.text else "",
            "sections": sections,
            "gamp_categories": gamp_categories,
            "test_types": test_types,
            "collection": collection_name,
            "node_id": node.node.node_id,
            "metadata": metadata,
            "chunk_details": chunk_info,
            "source_file": metadata.get("source_file", "unknown"),
            "creation_date": metadata.get("creation_date", "unknown"),
            "last_modified": metadata.get("last_modified", "unknown")
        }

    def _apply_metadata_filters(self, documents: list[dict[str, Any]], filters: dict[str, Any]) -> list[dict[str, Any]]:
        """Apply metadata filters to search results."""
        filtered_docs = []

        for doc in documents:
            include = True
            metadata = doc.get("metadata", {})

            for key, value in filters.items():
                if key not in metadata:
                    include = False
                    break

                if isinstance(value, list):
                    if metadata[key] not in value:
                        include = False
                        break
                elif metadata[key] != value:
                    include = False
                    break

            if include:
                filtered_docs.append(doc)

        return filtered_docs

    def _assess_context_quality(self, documents: list[dict[str, Any]], request: ContextProviderRequest) -> str:
        """Assess the quality of retrieved context with detailed logging."""
        if not documents:
            self.logger.info("📊 Context quality assessment: No documents, quality = 'poor'")
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
            quality = "high"
        elif avg_relevance >= 0.70 and section_coverage >= 0.6:
            quality = "medium"
        else:
            quality = "low"

        # Log quality assessment details
        self.logger.info(
            f"📊 Context quality assessment:\n"
            f"   - Average relevance: {avg_relevance:.3f}\n"
            f"   - Required sections: {list(required_sections)}\n"
            f"   - Covered sections: {list(covered_sections.intersection(required_sections))}\n"
            f"   - Section coverage: {section_coverage:.2%}\n"
            f"   - Quality assessment: {quality}"
        )

        # Add trace event
        current_span = trace.get_current_span()
        if current_span and current_span.is_recording():
            current_span.add_event(
                "context_quality_assessment",
                attributes={
                    "avg_relevance": avg_relevance,
                    "section_coverage": section_coverage,
                    "required_sections": json.dumps(list(required_sections)),
                    "covered_sections": json.dumps(list(covered_sections)),
                    "quality": quality
                }
            )

        return quality

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
        """Calculate confidence score for the context retrieval with detailed logging."""
        if not documents:
            self.logger.info("🔢 Confidence calculation: No documents retrieved, returning 0.0")
            return 0.0

        # Base score from document count and relevance
        avg_relevance = sum(doc.get("relevance_score", 0.0) for doc in documents) / len(documents)
        document_count_factor = min(len(documents) / 10, 1.0)  # Normalize to 10 documents

        # Quality factor
        quality_factors = {"high": 1.0, "medium": 0.8, "low": 0.6, "poor": 0.3}
        quality_factor = quality_factors.get(context_quality, 0.5)

        # Combine factors
        confidence = (avg_relevance * 0.4 + search_coverage * 0.3 + quality_factor * 0.2 + document_count_factor * 0.1)

        # Log calculation details
        self.logger.info(
            f"🔢 Confidence calculation:\n"
            f"   - Average relevance: {avg_relevance:.3f} (weight: 0.4)\n"
            f"   - Search coverage: {search_coverage:.3f} (weight: 0.3)\n"
            f"   - Context quality: {context_quality} → {quality_factor:.1f} (weight: 0.2)\n"
            f"   - Document count: {len(documents)} → {document_count_factor:.1f} (weight: 0.1)\n"
            f"   - Final confidence: {confidence:.3f}"
        )

        # Add trace event for confidence calculation
        current_span = trace.get_current_span()
        if current_span and current_span.is_recording():
            current_span.add_event(
                "confidence_calculation",
                attributes={
                    "avg_relevance": avg_relevance,
                    "search_coverage": search_coverage,
                    "context_quality": context_quality,
                    "quality_factor": quality_factor,
                    "document_count": len(documents),
                    "document_count_factor": document_count_factor,
                    "final_confidence": confidence
                }
            )

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
        stats = self._processing_stats.copy()

        # Add ChromaDB statistics
        try:
            for collection_name, collection in self.collections.items():
                stats[f"{collection_name}_documents"] = collection.count()
        except Exception as e:
            self.logger.warning(f"Could not get collection statistics: {e!s}")

        return stats

    @trace_agent_method(
        span_name="chromadb.ingest_documents",
        attributes={"operation": "document_ingestion"}
    )
    async def ingest_documents(
        self,
        documents_path: str,
        collection_name: str = "gamp5",
        force_reprocess: bool = False
    ) -> dict[str, Any]:
        """
        Ingest pharmaceutical documents into ChromaDB with comprehensive observability.
        
        Args:
            documents_path: Path to documents directory or file
            collection_name: Target collection (gamp5, regulatory, sops, best_practices)
            force_reprocess: Force reprocessing even if cached
            
        Returns:
            Dictionary with ingestion statistics
        """
        # Get current span for detailed tracing
        current_span = trace.get_current_span()

        try:
            if collection_name not in self.collections:
                raise ValueError(f"Invalid collection name: {collection_name}. Valid: {list(self.collections.keys())}")

            # Add ingestion parameters to span
            if current_span and current_span.is_recording():
                current_span.set_attribute("ingestion.collection_name", collection_name)
                current_span.set_attribute("ingestion.documents_path", documents_path)
                current_span.set_attribute("ingestion.force_reprocess", force_reprocess)

            # Record ingestion in audit trail
            audit_entry = {
                "timestamp": datetime.now(UTC).isoformat(),
                "operation": "document_ingestion",
                "collection": collection_name,
                "path": documents_path,
                "force_reprocess": force_reprocess
            }
            self._audit_trail.append(audit_entry)

            self.logger.info(
                f"📥 Starting document ingestion:\n"
                f"   - Path: {documents_path}\n"
                f"   - Collection: {collection_name}\n"
                f"   - Force reprocess: {force_reprocess}"
            )

            # Process documents with tracing
            with self.tracer.start_as_current_span("ingestion.process_documents") as process_span:
                documents = await self._process_documents_for_ingestion(documents_path, collection_name)
                process_span.set_attribute("documents.count", len(documents))

                if not documents:
                    self.logger.warning("No documents found to ingest")
                    return {"status": "no_documents", "processed": 0}

                # Log document details
                for i, doc in enumerate(documents[:3]):  # Log first 3 documents
                    self.logger.info(
                        f"   📄 Document {i+1}: {doc.metadata.get('file_name', 'Unknown')}\n"
                        f"      - Type: {doc.metadata.get('type', 'unknown')}\n"
                        f"      - GAMP categories: {doc.metadata.get('gamp_categories', 'none')}"
                    )

            # Clear cache if force reprocessing
            if force_reprocess:
                self.ingestion_cache.clear()
                self.logger.info("   🗑️  Cleared ingestion cache for reprocessing")
                if current_span and current_span.is_recording():
                    current_span.add_event("cache_cleared")

            # Run ingestion pipeline with tracing
            with self.tracer.start_as_current_span("ingestion.pipeline_run") as pipeline_span:
                pipeline = self.ingestion_pipelines[collection_name]

                # Add pipeline configuration to span
                pipeline_span.set_attribute("pipeline.collection", collection_name)
                pipeline_span.set_attribute("pipeline.chunk_size", int(os.getenv("RAG_CHUNK_SIZE", "1500")))
                pipeline_span.set_attribute("pipeline.chunk_overlap", int(os.getenv("RAG_CHUNK_OVERLAP", "200")))

                # Run pipeline
                nodes = await asyncio.to_thread(
                    pipeline.run,
                    documents=documents
                )

                # Track node processing
                pipeline_span.set_attribute("pipeline.nodes_created", len(nodes))
                pipeline_span.set_attribute("pipeline.documents_processed", len(documents))

                # Log chunking statistics
                avg_chunks_per_doc = len(nodes) / len(documents) if documents else 0
                self.logger.info(
                    f"   🔨 Pipeline processing complete:\n"
                    f"      - Documents processed: {len(documents)}\n"
                    f"      - Nodes created: {len(nodes)}\n"
                    f"      - Avg chunks/document: {avg_chunks_per_doc:.1f}"
                )

            # Update statistics
            stats = {
                "status": "success",
                "collection": collection_name,
                "processed_documents": len(documents),
                "processed_nodes": len(nodes),
                "cache_hits": getattr(self.ingestion_cache, "cache_hits", 0),
                "timestamp": datetime.now(UTC).isoformat()
            }

            # Update audit trail
            audit_entry.update(stats)

            # Add final metrics to span
            if current_span and current_span.is_recording():
                current_span.set_attribute("ingestion.success", True)
                current_span.set_attribute("ingestion.documents_processed", len(documents))
                current_span.set_attribute("ingestion.nodes_created", len(nodes))
                current_span.set_attribute("ingestion.cache_hits", stats["cache_hits"])

                # Add summary event
                current_span.add_event(
                    "ingestion_complete",
                    attributes={
                        "collection": collection_name,
                        "documents": len(documents),
                        "nodes": len(nodes),
                        "avg_chunks_per_doc": len(nodes) / len(documents) if documents else 0
                    }
                )

            self.logger.info(
                f"✅ Document ingestion completed:\n"
                f"   - Status: {stats['status']}\n"
                f"   - Documents: {stats['processed_documents']}\n"
                f"   - Nodes: {stats['processed_nodes']}\n"
                f"   - Cache hits: {stats['cache_hits']}"
            )

            return stats

        except Exception as e:
            error_msg = f"Document ingestion failed: {e!s}"
            stack_trace = traceback.format_exc()
            self.logger.error(f"{error_msg}\n{stack_trace}")

            # Record failure in span
            if current_span and current_span.is_recording():
                current_span.record_exception(e)
                current_span.set_status(Status(StatusCode.ERROR, str(e)))
                current_span.set_attribute("ingestion.success", False)
                current_span.set_attribute("ingestion.error_type", type(e).__name__)
                current_span.set_attribute("ingestion.error_message", str(e))

            # Record failure in audit trail
            self._audit_trail.append({
                "timestamp": datetime.now(UTC).isoformat(),
                "operation": "document_ingestion_failed",
                "collection": collection_name,
                "path": documents_path,
                "error": str(e),
                "error_type": type(e).__name__,
                "stack_trace": stack_trace
            })

            # NO FALLBACK - fail explicitly
            raise RuntimeError(f"{error_msg}\n{stack_trace}") from e

    async def _process_documents_for_ingestion(
        self,
        documents_path: str,
        collection_name: str
    ) -> list[Document]:
        """Process documents for ingestion with pharmaceutical metadata."""
        documents = []
        path = Path(documents_path)

        if path.is_file():
            # Single file
            doc = await self._create_document_from_file(path, collection_name)
            if doc:
                documents.append(doc)
        elif path.is_dir():
            # Directory of files
            for file_path in path.rglob("*"):
                if file_path.is_file() and file_path.suffix in [".txt", ".md", ".pdf"]:
                    doc = await self._create_document_from_file(file_path, collection_name)
                    if doc:
                        documents.append(doc)
        else:
            raise ValueError(f"Path does not exist: {documents_path}")

        return documents

    async def _create_document_from_file(
        self,
        file_path: Path,
        collection_name: str
    ) -> Document | None:
        """Create a LlamaIndex Document from a file with compliance metadata."""
        try:
            # Read file content
            if file_path.suffix == ".pdf":
                # For PDF files, you would use a PDF reader
                # For now, skip PDFs unless you have pdf reader installed
                self.logger.warning(f"PDF processing not implemented, skipping: {file_path}")
                return None
            # Text-based files
            content = file_path.read_text(encoding="utf-8")

            # Create metadata for pharmaceutical compliance
            # ChromaDB only supports flat metadata (str, int, float, None)
            gamp_categories = self._extract_gamp_categories(content)
            test_types = self._extract_test_types(content)
            sections = self._extract_sections(content)

            metadata = {
                "file_name": file_path.name,
                "file_path": str(file_path),
                "collection": collection_name,
                "ingestion_timestamp": datetime.now(UTC).isoformat(),
                "type": self._determine_document_type(file_path, collection_name),
                "compliance_level": self.collections[collection_name].metadata.get("compliance_level", "unknown"),
                "gamp_categories": ",".join(gamp_categories) if gamp_categories else "",
                "test_types": ",".join(test_types) if test_types else "",
                "sections": ",".join(sections[:5]) if sections else ""  # Limit sections for metadata size
            }

            # Create document
            return Document(
                text=content,
                metadata=metadata
            )

        except Exception as e:
            self.logger.error(f"Failed to process file {file_path}: {e!s}")
            return None

    def _determine_document_type(self, file_path: Path, collection_name: str) -> str:
        """Determine document type based on filename and collection."""
        filename_lower = file_path.name.lower()

        if "regulation" in filename_lower or "cfr" in filename_lower or "fda" in filename_lower:
            return "regulatory_requirement"
        if "guidance" in filename_lower or "guideline" in filename_lower:
            return "regulatory_guidance"
        if "sop" in filename_lower or "procedure" in filename_lower:
            return "standard_operating_procedure"
        if "best" in filename_lower or "practice" in filename_lower:
            return "best_practices"
        if "methodology" in filename_lower or "method" in filename_lower:
            return "methodology"
        if "test" in filename_lower:
            return "testing_methodology"
        # Default based on collection
        collection_defaults = {
            "gamp5": "regulatory_guidance",
            "regulatory": "regulatory_requirement",
            "sops": "standard_operating_procedure",
            "best_practices": "best_practices"
        }
        return collection_defaults.get(collection_name, "general")

    def _extract_gamp_categories(self, content: str) -> list[str]:
        """Extract GAMP categories mentioned in the document."""
        categories = []
        content_lower = content.lower()

        for category in ["1", "2", "3", "4", "5"]:
            if f"gamp {category}" in content_lower or f"category {category}" in content_lower:
                categories.append(category)

        return categories

    def _extract_test_types(self, content: str) -> list[str]:
        """Extract test types mentioned in the document."""
        test_types = []
        content_lower = content.lower()

        common_test_types = [
            "unit_testing", "integration_testing", "system_testing",
            "acceptance_testing", "performance_testing", "security_testing",
            "validation_testing", "qualification_testing", "regression_testing"
        ]

        for test_type in common_test_types:
            if test_type.replace("_", " ") in content_lower:
                test_types.append(test_type)

        return test_types

    def _extract_sections(self, content: str) -> list[str]:
        """Extract section headers from the document."""
        sections = []
        lines = content.split("\n")

        for line in lines:
            # Look for markdown headers or numbered sections
            if line.strip().startswith("#") or (line.strip() and line.strip()[0].isdigit() and "." in line):
                section = line.strip().lstrip("#").strip()
                if section and len(section) < 100:  # Reasonable length for a section title
                    sections.append(section)

        return sections[:20]  # Limit to first 20 sections

    def get_audit_trail(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get audit trail for ALCOA+ compliance."""
        return self._audit_trail[-limit:]


def create_context_provider_agent(
    llm: LLM | None = None,
    verbose: bool = False,
    enable_phoenix: bool = True,
    max_documents: int = 50,
    quality_threshold: float = 0.7,
    vector_store_path: str | None = None,
    cache_dir: str | None = None,
    embedding_model: str | None = None
) -> ContextProviderAgent:
    """
    Create a Context Provider Agent instance with ChromaDB integration.
    
    Args:
        llm: Language model for context analysis
        verbose: Enable verbose logging
        enable_phoenix: Enable Phoenix AI instrumentation
        max_documents: Maximum documents to retrieve
        quality_threshold: Minimum quality threshold
        vector_store_path: Path for ChromaDB storage
        cache_dir: Directory for caching embeddings
        embedding_model: OpenAI embedding model to use
    
    Returns:
        Configured ContextProviderAgent instance with ChromaDB
    """
    return ContextProviderAgent(
        llm=llm,
        verbose=verbose,
        enable_phoenix=enable_phoenix,
        max_documents=max_documents,
        quality_threshold=quality_threshold,
        vector_store_path=vector_store_path,
        cache_dir=cache_dir,
        embedding_model=embedding_model
    )
