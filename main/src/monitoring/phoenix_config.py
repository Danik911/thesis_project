"""
Arize Phoenix configuration and management for pharmaceutical workflow observability.

This module provides environment-aware Phoenix setup supporting both local development
and production deployment with full GAMP-5 compliance tracing.
"""

import logging
import os
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import wraps
from typing import Any

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk import trace as trace_sdk
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace.export import BatchSpanProcessor

logger = logging.getLogger(__name__)

# Import custom span exporter after logger setup
try:
    from .custom_span_exporter import add_local_span_exporter
except ImportError:
    add_local_span_exporter = None
    logger.warning("Custom span exporter not available")


@dataclass
class PhoenixConfig:
    """Configuration for Arize Phoenix observability."""

    # Phoenix endpoints
    phoenix_host: str = field(default_factory=lambda: os.getenv("PHOENIX_HOST", "localhost"))
    phoenix_port: int = field(default_factory=lambda: int(os.getenv("PHOENIX_PORT", "6006")))
    phoenix_api_key: str | None = field(default_factory=lambda: os.getenv("PHOENIX_API_KEY"))

    # OTLP configuration
    otlp_endpoint: str = field(
        default_factory=lambda: os.getenv(
            "OTEL_EXPORTER_OTLP_ENDPOINT",
            f"http://{os.getenv('PHOENIX_HOST', 'localhost')}:{os.getenv('PHOENIX_PORT', '6006')}/v1/traces"
        )
    )
    otlp_headers: dict[str, str] = field(default_factory=dict)

    # Service configuration
    service_name: str = field(
        default_factory=lambda: os.getenv("OTEL_SERVICE_NAME", "test_generator")
    )
    service_version: str = field(default_factory=lambda: os.getenv("SERVICE_VERSION", "1.0.0"))
    deployment_environment: str = field(
        default_factory=lambda: os.getenv("DEPLOYMENT_ENVIRONMENT", "development")
    )

    # Project configuration
    project_name: str = field(
        default_factory=lambda: os.getenv("PHOENIX_PROJECT_NAME", "test_generation_thesis")
    )
    experiment_name: str = field(
        default_factory=lambda: os.getenv("PHOENIX_EXPERIMENT_NAME", "multi_agent_workflow")
    )

    # Feature flags
    enable_tracing: bool = field(
        default_factory=lambda: os.getenv("PHOENIX_ENABLE_TRACING", "true").lower() == "true"
    )
    enable_local_ui: bool = field(
        default_factory=lambda: os.getenv("PHOENIX_ENABLE_LOCAL_UI", "true").lower() == "true"
    )

    # Enhanced instrumentation flags
    enable_openai_instrumentation: bool = field(
        default_factory=lambda: os.getenv("PHOENIX_ENABLE_OPENAI", "true").lower() == "true"
    )
    enable_chromadb_instrumentation: bool = field(
        default_factory=lambda: os.getenv("PHOENIX_ENABLE_CHROMADB", "true").lower() == "true"
    )
    enable_tool_instrumentation: bool = field(
        default_factory=lambda: os.getenv("PHOENIX_ENABLE_TOOLS", "true").lower() == "true"
    )

    # Performance settings
    batch_span_processor_max_queue_size: int = 2048
    batch_span_processor_max_export_batch_size: int = 512
    batch_span_processor_schedule_delay_millis: int = field(
        default_factory=lambda: int(os.getenv("PHOENIX_BATCH_EXPORT_DELAY_MS", "1000"))
    )  # Reduced from 5000ms to 1000ms for faster exports

    # Compliance settings
    enable_compliance_attributes: bool = True
    enable_pii_filtering: bool = True

    def __post_init__(self):
        """Validate and prepare configuration after initialization."""
        # Add API key to headers if available
        if self.phoenix_api_key and not self.otlp_headers.get("api-key"):
            self.otlp_headers["api-key"] = self.phoenix_api_key

        # Set environment-specific defaults
        if self.deployment_environment == "production":
            self.enable_local_ui = False
            self.batch_span_processor_schedule_delay_millis = 1000  # Faster export in prod

    def to_resource_attributes(self) -> dict[str, Any]:
        """Convert config to OpenTelemetry resource attributes."""
        return {
            "service.name": self.service_name,
            "service.version": self.service_version,
            "deployment.environment": self.deployment_environment,
            "phoenix.project": self.project_name,
            "phoenix.experiment": self.experiment_name,
            "compliance.gamp5.enabled": self.enable_compliance_attributes,
            "compliance.pii.filtering": self.enable_pii_filtering,
            # Enhanced instrumentation capabilities
            "instrumentation.openai.enabled": self.enable_openai_instrumentation,
            "instrumentation.chromadb.enabled": self.enable_chromadb_instrumentation,
            "instrumentation.tools.enabled": self.enable_tool_instrumentation,
        }


class PhoenixManager:
    """Manages Phoenix lifecycle and instrumentation."""

    def __init__(self, config: PhoenixConfig | None = None):
        """Initialize Phoenix manager with configuration."""
        self.config = config or PhoenixConfig()
        self.tracer_provider: trace_sdk.TracerProvider | None = None
        self.phoenix_session = None
        self._initialized = False

    def setup(self) -> "PhoenixManager":
        """
        Set up Phoenix observability based on configuration.
        
        Returns:
            Self for method chaining
        """
        if self._initialized:
            logger.warning("Phoenix already initialized, skipping setup")
            return self

        if not self.config.enable_tracing:
            logger.info("Phoenix tracing disabled by configuration")
            return self

        try:
            # Launch local Phoenix UI if enabled and in development
            if self.config.enable_local_ui and self.config.deployment_environment == "development":
                self._launch_local_phoenix()

            # Set up OpenTelemetry tracer
            self._setup_tracer()

            # Instrument LlamaIndex
            self._instrument_llamaindex()

            # Instrument OpenAI if enabled
            openai_instrumented = False
            if self.config.enable_openai_instrumentation:
                try:
                    self._instrument_openai()
                    openai_instrumented = True
                except Exception as openai_error:
                    logger.error(f"[ERROR] OpenAI instrumentation failed: {openai_error}")
                    # For pharmaceutical systems, this is critical
                    if self.config.deployment_environment == "production":
                        raise RuntimeError("OpenAI instrumentation required for production pharmaceutical compliance") from openai_error

            # Instrument ChromaDB if enabled
            chromadb_instrumented = False
            if self.config.enable_chromadb_instrumentation:
                try:
                    self._instrument_chromadb()
                    chromadb_instrumented = True
                except Exception as chromadb_error:
                    logger.error(f"[ERROR] ChromaDB instrumentation failed: {chromadb_error}")

            self._initialized = True
            logger.info(
                f"[SUCCESS] Phoenix observability initialized for {self.config.deployment_environment} environment\n"
                f"   - Endpoint: {self.config.otlp_endpoint}\n"
                f"   - OpenAI instrumented: {openai_instrumented}\n"
                f"   - ChromaDB instrumented: {chromadb_instrumented}"
            )

        except Exception as e:
            logger.error(f"[ERROR] Failed to initialize Phoenix: {e}")
            # ENHANCED: More specific error handling
            if self.config.deployment_environment == "production":
                # In production, Phoenix is required for compliance
                logger.error("Production pharmaceutical system requires Phoenix observability")
                raise RuntimeError("Phoenix initialization failure in production environment") from e
            # In development, allow graceful degradation with warning
            logger.warning("Continuing without Phoenix in development mode - observability will be limited")
            self._initialized = False

        return self

    def _launch_local_phoenix(self) -> None:
        """Launch local Phoenix UI for development or connect to existing instance."""
        try:
            import phoenix as px

            # First try to connect to existing Phoenix (like Docker container)
            try:
                import requests
                health_url = f"http://{self.config.phoenix_host}:{self.config.phoenix_port}"
                response = requests.get(health_url, timeout=2)
                if response.status_code == 200:
                    logger.info(f"[SUCCESS] Connected to existing Phoenix instance at: {health_url}")
                    # Create a mock session object for compatibility
                    class MockSession:
                        def __init__(self, url):
                            self.url = url
                    self.phoenix_session = MockSession(health_url)
                    return
            except Exception:
                logger.debug("No existing Phoenix instance found, launching local...")

            # Launch local Phoenix if no existing instance
            # Check if PHOENIX_EXTERNAL environment variable is set
            if os.getenv("PHOENIX_EXTERNAL", "").lower() == "true":
                logger.info("PHOENIX_EXTERNAL=true, skipping local Phoenix launch")
                self.phoenix_session = MockSession(f"http://{self.config.phoenix_host}:{self.config.phoenix_port}")
                return

            self.phoenix_session = px.launch_app(
                host=self.config.phoenix_host,
                port=self.config.phoenix_port,
            )

            logger.info(f"Phoenix UI launched at: {self.phoenix_session.url}")

        except ImportError:
            logger.warning(
                "Phoenix UI not available. Install with: pip install arize-phoenix"
            )
        except Exception as e:
            logger.warning(f"Failed to launch Phoenix UI: {e}")
            # Try to create mock session for Docker Phoenix
            try:
                class MockSession:
                    def __init__(self, url):
                        self.url = url
                docker_url = f"http://{self.config.phoenix_host}:{self.config.phoenix_port}"
                self.phoenix_session = MockSession(docker_url)
                logger.info(f"[SUCCESS] Using Docker Phoenix instance at: {docker_url}")
            except Exception as mock_error:
                logger.warning(f"Failed to connect to Docker Phoenix: {mock_error}")

    def _setup_tracer(self) -> None:
        """Set up OpenTelemetry tracer with OTLP exporter using Phoenix patterns."""
        # Always use manual setup to ensure BatchSpanProcessor is used
        # This prevents the "Exporter already shutdown" issue
        logger.debug("Using manual tracer setup for better control over span processing")
        self._setup_manual_tracer()

    def _setup_manual_tracer(self) -> None:
        """Set up OpenTelemetry tracer manually (fallback method)."""
        # Create resource with attributes
        resource = Resource.create(self.config.to_resource_attributes())

        # Create tracer provider
        self.tracer_provider = trace_sdk.TracerProvider(resource=resource)

        # Create OTLP exporter
        exporter = OTLPSpanExporter(
            endpoint=self.config.otlp_endpoint,
            headers=self.config.otlp_headers,
        )

        # Create batch span processor for non-blocking export
        span_processor = BatchSpanProcessor(
            exporter,
            max_queue_size=self.config.batch_span_processor_max_queue_size,
            max_export_batch_size=self.config.batch_span_processor_max_export_batch_size,
            schedule_delay_millis=self.config.batch_span_processor_schedule_delay_millis,
        )

        # Add span processor to tracer provider
        self.tracer_provider.add_span_processor(span_processor)

        # Set as global tracer provider
        trace.set_tracer_provider(self.tracer_provider)

        logger.debug(f"Manual tracer configured with endpoint: {self.config.otlp_endpoint}")

        # Add local file exporter to capture ALL spans including ChromaDB
        if add_local_span_exporter:
            try:
                add_local_span_exporter(self.tracer_provider)
                logger.info("✅ Local span exporter added - ALL spans will be captured to files")
            except Exception as e:
                logger.warning(f"Failed to add local span exporter: {e}")

    def _instrument_llamaindex(self) -> None:
        """Instrument LlamaIndex with OpenInference and fallback options."""
        try:
            from openinference.instrumentation.llama_index import LlamaIndexInstrumentor

            # ENHANCED: Add more detailed logging for debugging
            logger.info("[CONFIG] Attempting LlamaIndex instrumentation with OpenInference...")

            # Instrument with our tracer provider
            LlamaIndexInstrumentor().instrument(
                skip_dep_check=True,
                tracer_provider=self.tracer_provider
            )

            logger.info("[SUCCESS] LlamaIndex instrumented successfully with OpenInference")

        except ImportError as e:
            logger.error(
                f"[ERROR] OpenInference LlamaIndex instrumentation not available: {e}\n"
                "Install with: pip install openinference-instrumentation-llama-index"
            )
            self._try_fallback_instrumentation()
        except Exception as e:
            logger.error(f"[ERROR] OpenInference instrumentation failed: {e}")
            self._try_fallback_instrumentation()

    def _try_fallback_instrumentation(self) -> None:
        """Try fallback instrumentation using simple global handler."""
        try:
            import llama_index.core
            llama_index.core.set_global_handler("arize_phoenix")
            logger.info("[SUCCESS] Fallback to simple Phoenix global handler successful")
        except Exception as fallback_error:
            logger.warning(f"[ERROR] Fallback instrumentation also failed: {fallback_error}")
            logger.info("Continuing without Phoenix instrumentation")

    def _instrument_openai(self) -> None:
        """Instrument OpenAI client for comprehensive LLM call tracing."""
        try:
            from openinference.instrumentation.openai import OpenAIInstrumentor

            # ENHANCED: Add more detailed logging
            logger.info("[CONFIG] Attempting OpenAI instrumentation with OpenInference...")

            # Instrument OpenAI with our tracer provider
            OpenAIInstrumentor().instrument(tracer_provider=self.tracer_provider)

            logger.info("[SUCCESS] OpenAI instrumented successfully - LLM calls will be traced with token usage and costs")

        except ImportError as e:
            logger.error(
                f"[ERROR] OpenAI instrumentation not available: {e}\n"
                "Install with: pip install openinference-instrumentation-openai"
            )
            # NO FALLBACK - fail explicitly to identify missing dependencies
            raise RuntimeError("OpenAI instrumentation required for pharmaceutical compliance tracing") from e
        except Exception as e:
            logger.error(f"[ERROR] OpenAI instrumentation failed: {e}")
            # NO FALLBACK - fail explicitly for regulatory compliance
            raise RuntimeError(f"OpenAI instrumentation failure: {e}") from e

    def _instrument_chromadb(self) -> None:
        """
        Custom ChromaDB instrumentation for pharmaceutical compliance.
        
        Since openinference-instrumentation-chromadb is not available,
        this implements custom tracing for ChromaDB operations using
        OpenTelemetry manual instrumentation.
        """
        try:
            # Check if ChromaDB is available in the environment
            import chromadb

            # Create a tracer for ChromaDB operations
            tracer = self.get_tracer("chromadb")

            # Store original ChromaDB methods for wrapping
            original_query = None
            original_add = None
            original_delete = None

            # Get the collection class to wrap
            try:
                collection_class = chromadb.Collection

                # Store original methods if they exist
                if hasattr(collection_class, "query"):
                    original_query = collection_class.query
                if hasattr(collection_class, "add"):
                    original_add = collection_class.add
                if hasattr(collection_class, "delete"):
                    original_delete = collection_class.delete

                # Create instrumented wrapper functions
                def instrumented_query(self, *args, **kwargs):
                    with tracer.start_as_current_span("chromadb.query") as span:
                        # Add pharmaceutical compliance attributes
                        span.set_attribute("vector_db.operation", "query")
                        span.set_attribute("compliance.gamp5.vector_operation", True)
                        span.set_attribute("compliance.pharmaceutical", True)
                        span.set_attribute("data_integrity.vector_search", True)

                        # Add query parameters if available
                        if "n_results" in kwargs:
                            span.set_attribute("chromadb.query.n_results", kwargs["n_results"])
                        if kwargs.get("query_texts"):
                            span.set_attribute("chromadb.query.text_count", len(kwargs["query_texts"]))

                        try:
                            result = original_query(self, *args, **kwargs)
                            span.set_attribute("chromadb.query.status", "success")

                            # Add result metadata (without exposing actual content for PII compliance)
                            if isinstance(result, dict):
                                if result.get("documents"):
                                    span.set_attribute("chromadb.query.result_count", len(result["documents"][0]) if result["documents"][0] else 0)
                                if result.get("distances"):
                                    span.set_attribute("chromadb.query.avg_distance", sum(result["distances"][0]) / len(result["distances"][0]) if result["distances"][0] else 0)

                            return result
                        except Exception as e:
                            span.set_attribute("chromadb.query.status", "error")
                            span.set_attribute("chromadb.query.error", str(e))
                            span.record_exception(e)
                            raise

                def instrumented_add(self, *args, **kwargs):
                    with tracer.start_as_current_span("chromadb.add") as span:
                        span.set_attribute("vector_db.operation", "add")
                        span.set_attribute("compliance.gamp5.vector_operation", True)
                        span.set_attribute("compliance.pharmaceutical", True)
                        span.set_attribute("data_integrity.vector_add", True)

                        # Add operation parameters
                        if kwargs.get("documents"):
                            span.set_attribute("chromadb.add.document_count", len(kwargs["documents"]))
                        if kwargs.get("ids"):
                            span.set_attribute("chromadb.add.id_count", len(kwargs["ids"]))

                        try:
                            result = original_add(self, *args, **kwargs)
                            span.set_attribute("chromadb.add.status", "success")
                            return result
                        except Exception as e:
                            span.set_attribute("chromadb.add.status", "error")
                            span.set_attribute("chromadb.add.error", str(e))
                            span.record_exception(e)
                            raise

                def instrumented_delete(self, *args, **kwargs):
                    with tracer.start_as_current_span("chromadb.delete") as span:
                        span.set_attribute("vector_db.operation", "delete")
                        span.set_attribute("compliance.gamp5.vector_operation", True)
                        span.set_attribute("compliance.pharmaceutical", True)
                        span.set_attribute("data_integrity.vector_delete", True)

                        # Add operation parameters
                        if kwargs.get("ids"):
                            span.set_attribute("chromadb.delete.id_count", len(kwargs["ids"]))

                        try:
                            result = original_delete(self, *args, **kwargs)
                            span.set_attribute("chromadb.delete.status", "success")
                            return result
                        except Exception as e:
                            span.set_attribute("chromadb.delete.status", "error")
                            span.set_attribute("chromadb.delete.error", str(e))
                            span.record_exception(e)
                            raise

                # Apply the instrumentation by monkey patching
                if original_query:
                    collection_class.query = instrumented_query
                if original_add:
                    collection_class.add = instrumented_add
                if original_delete:
                    collection_class.delete = instrumented_delete

                logger.info("[SUCCESS] ChromaDB custom instrumentation applied - Vector operations will be traced with pharmaceutical compliance")

            except AttributeError as e:
                logger.warning(f"ChromaDB class structure changed - custom instrumentation may not work: {e}")
                logger.info("Vector database operations may not be fully traced")

        except ImportError:
            logger.info("ChromaDB not installed - vector database instrumentation skipped")
        except Exception as e:
            logger.error(f"ChromaDB custom instrumentation failed: {e}")
            logger.info("Continuing without ChromaDB instrumentation")

    def get_tracer(self, name: str) -> trace.Tracer:
        """
        Get a tracer instance for manual instrumentation.
        
        Args:
            name: Name of the tracer (typically module name)
            
        Returns:
            Tracer instance
        """
        return trace.get_tracer(name)

    def create_tool_span(self, tracer: trace.Tracer, tool_name: str, **attributes):
        """
        Create a span for tool execution with pharmaceutical compliance attributes.
        
        Args:
            tracer: OpenTelemetry tracer instance
            tool_name: Name of the tool being executed
            **attributes: Additional span attributes
            
        Returns:
            Context manager for the span
        """
        span_name = f"tool.{tool_name}"
        span = tracer.start_span(span_name)

        # Set standard tool attributes
        span.set_attribute("tool.name", tool_name)
        span.set_attribute("tool.type", "pharmaceutical_agent_tool")

        # Add GAMP-5 compliance attributes if enabled
        if self.config.enable_compliance_attributes:
            span.set_attribute("compliance.gamp5.category", "tool_execution")
            span.set_attribute("compliance.audit.required", True)

        # Add custom attributes
        for key, value in attributes.items():
            span.set_attribute(f"tool.{key}", value)

        return span

    def shutdown(self, timeout_seconds: int = 5) -> None:
        """
        Gracefully shutdown Phoenix and tracing with forced flush.
        
        Args:
            timeout_seconds: Maximum time to wait for trace export completion
        """
        logger.info("Shutting down Phoenix observability...")

        if self.tracer_provider:
            try:
                # Force flush any pending spans before shutdown
                timeout_millis = timeout_seconds * 1000
                logger.info(f"Force flushing Phoenix traces (timeout: {timeout_seconds}s)...")
                flush_success = self.tracer_provider.force_flush(timeout_millis=timeout_millis)

                if flush_success:
                    logger.info("[SUCCESS] Successfully flushed all pending traces")
                else:
                    logger.warning(f"[WARNING]  Trace flush may have timed out after {timeout_seconds}s")

                # Now shutdown the tracer provider
                self.tracer_provider.shutdown()
                logger.debug("Tracer provider shut down successfully")

            except Exception as e:
                logger.warning(f"Error during tracer shutdown: {e}")

        if self.phoenix_session:
            try:
                # Keep session alive for UI accessibility
                # Don't set to None - let it persist for post-workflow access
                logger.debug("Phoenix session maintained for continued UI access")
            except Exception as e:
                logger.warning(f"Error maintaining Phoenix session: {e}")

        # Mark as not initialized but don't clear session completely
        self._initialized = False
        logger.info("Phoenix shutdown complete - UI should remain accessible")


def instrument_tool(tool_name: str, tool_category: str = "agent_tool", **span_attributes):
    """
    Decorator to instrument pharmaceutical agent tools with Phoenix observability.
    
    This decorator creates detailed spans for tool execution with pharmaceutical
    compliance attributes, performance metrics, and error tracking.
    
    Args:
        tool_name: Name of the tool being instrumented
        tool_category: Category of tool (e.g., 'categorization', 'confidence', 'analysis')
        **span_attributes: Additional span attributes to add
        
    Usage:
        @instrument_tool("gamp_analysis", "categorization", critical=True)
        def gamp_analysis_tool(urs_content: str) -> dict:
            return analyze_urs(urs_content)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Get global Phoenix manager and tracer
            phoenix_manager = get_phoenix_manager()
            if not phoenix_manager or not phoenix_manager._initialized:
                # If Phoenix not initialized, run function without instrumentation
                return func(*args, **kwargs)

            tracer = phoenix_manager.get_tracer("pharmaceutical_tools")

            # Create tool span with enhanced attributes
            span_name = f"tool.{tool_category}.{tool_name}"
            with tracer.start_as_current_span(span_name) as span:
                try:
                    # Set standard tool attributes
                    span.set_attribute("tool.name", tool_name)
                    span.set_attribute("tool.category", tool_category)
                    span.set_attribute("tool.type", "pharmaceutical_agent_tool")
                    span.set_attribute("tool.function", func.__name__)

                    # Add GAMP-5 compliance attributes if enabled
                    if phoenix_manager.config.enable_compliance_attributes:
                        span.set_attribute("compliance.gamp5.category", "tool_execution")
                        span.set_attribute("compliance.audit.required", True)
                        span.set_attribute("compliance.pharmaceutical.tool", True)

                    # Add custom span attributes
                    for key, value in span_attributes.items():
                        span.set_attribute(f"tool.{key}", value)

                    # Add input parameter information (be careful with PII)
                    if phoenix_manager.config.enable_pii_filtering:
                        # Only add non-sensitive parameter counts and types
                        span.set_attribute("tool.input.arg_count", len(args))
                        span.set_attribute("tool.input.kwarg_count", len(kwargs))

                        # Add parameter types (not values for PII safety)
                        arg_types = [type(arg).__name__ for arg in args]
                        span.set_attribute("tool.input.arg_types", str(arg_types))

                    # Record execution start time
                    start_time = time.time()

                    # Execute the tool function
                    result = func(*args, **kwargs)

                    # Record execution metrics
                    execution_time = time.time() - start_time
                    span.set_attribute("tool.execution.duration_ms", execution_time * 1000)
                    span.set_attribute("tool.execution.status", "success")

                    # Add result information (safe for PII)
                    if result is not None:
                        span.set_attribute("tool.output.type", type(result).__name__)
                        if isinstance(result, dict):
                            span.set_attribute("tool.output.dict_keys", list(result.keys()))
                        elif isinstance(result, (list, tuple)):
                            span.set_attribute("tool.output.collection_size", len(result))

                    # Set span status as OK
                    span.set_status(trace.Status(trace.StatusCode.OK))

                    return result

                except Exception as e:
                    # Record error information
                    execution_time = time.time() - start_time
                    span.set_attribute("tool.execution.duration_ms", execution_time * 1000)
                    span.set_attribute("tool.execution.status", "error")
                    span.set_attribute("tool.error.type", type(e).__name__)
                    span.set_attribute("tool.error.message", str(e))

                    # Set span status as error
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    span.record_exception(e)

                    # Re-raise the exception
                    raise

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Get global Phoenix manager and tracer
            phoenix_manager = get_phoenix_manager()
            if not phoenix_manager or not phoenix_manager._initialized:
                # If Phoenix not initialized, run function without instrumentation
                return await func(*args, **kwargs)

            tracer = phoenix_manager.get_tracer("pharmaceutical_tools")

            # Create tool span with enhanced attributes
            span_name = f"tool.{tool_category}.{tool_name}"
            with tracer.start_as_current_span(span_name) as span:
                try:
                    # Set standard tool attributes
                    span.set_attribute("tool.name", tool_name)
                    span.set_attribute("tool.category", tool_category)
                    span.set_attribute("tool.type", "pharmaceutical_agent_tool")
                    span.set_attribute("tool.function", func.__name__)
                    span.set_attribute("tool.async", True)

                    # Add GAMP-5 compliance attributes if enabled
                    if phoenix_manager.config.enable_compliance_attributes:
                        span.set_attribute("compliance.gamp5.category", "tool_execution")
                        span.set_attribute("compliance.audit.required", True)
                        span.set_attribute("compliance.pharmaceutical.tool", True)

                    # Add custom span attributes
                    for key, value in span_attributes.items():
                        span.set_attribute(f"tool.{key}", value)

                    # Add input parameter information (be careful with PII)
                    if phoenix_manager.config.enable_pii_filtering:
                        # Only add non-sensitive parameter counts and types
                        span.set_attribute("tool.input.arg_count", len(args))
                        span.set_attribute("tool.input.kwarg_count", len(kwargs))

                        # Add parameter types (not values for PII safety)
                        arg_types = [type(arg).__name__ for arg in args]
                        span.set_attribute("tool.input.arg_types", str(arg_types))

                    # Record execution start time
                    start_time = time.time()

                    # Execute the tool function
                    result = await func(*args, **kwargs)

                    # Record execution metrics
                    execution_time = time.time() - start_time
                    span.set_attribute("tool.execution.duration_ms", execution_time * 1000)
                    span.set_attribute("tool.execution.status", "success")

                    # Add result information (safe for PII)
                    if result is not None:
                        span.set_attribute("tool.output.type", type(result).__name__)
                        if isinstance(result, dict):
                            span.set_attribute("tool.output.dict_keys", list(result.keys()))
                        elif isinstance(result, (list, tuple)):
                            span.set_attribute("tool.output.collection_size", len(result))

                    # Set span status as OK
                    span.set_status(trace.Status(trace.StatusCode.OK))

                    return result

                except Exception as e:
                    # Record error information
                    execution_time = time.time() - start_time
                    span.set_attribute("tool.execution.duration_ms", execution_time * 1000)
                    span.set_attribute("tool.execution.status", "error")
                    span.set_attribute("tool.error.type", type(e).__name__)
                    span.set_attribute("tool.error.message", str(e))

                    # Set span status as error
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    span.record_exception(e)

                    # Re-raise the exception
                    raise

        # Return appropriate wrapper based on function type
        if hasattr(func, "__code__") and func.__code__.co_flags & 0x80:  # CO_COROUTINE
            return async_wrapper
        return sync_wrapper

    return decorator


def enhance_workflow_span_with_compliance(span, workflow_type: str = "general", **metadata):
    """
    Enhance workflow spans with pharmaceutical compliance attributes.
    
    This function adds comprehensive GAMP-5 and pharmaceutical validation
    attributes to workflow spans for regulatory compliance and audit trails.
    
    Args:
        span: OpenTelemetry span to enhance
        workflow_type: Type of workflow (categorization, planning, unified, etc.)
        **metadata: Additional metadata to include
    """
    if not span:
        return

    try:
        # Core pharmaceutical compliance attributes
        span.set_attribute("workflow.type", workflow_type)
        span.set_attribute("workflow.pharmaceutical.compliant", True)

        # GAMP-5 specific attributes
        span.set_attribute("compliance.gamp5.workflow", True)
        span.set_attribute("compliance.gamp5.validation_required", True)
        span.set_attribute("compliance.gamp5.category", "workflow_execution")

        # Regulatory compliance attributes
        span.set_attribute("compliance.21cfr_part11.applicable", True)
        span.set_attribute("compliance.alcoa_plus.principles", True)

        # Audit trail attributes
        span.set_attribute("audit.pharmaceutical.workflow", True)
        span.set_attribute("audit.trail.required", True)
        span.set_attribute("audit.regulatory.significance", "high")

        # Data integrity attributes (ALCOA+)
        span.set_attribute("data_integrity.attributable", True)
        span.set_attribute("data_integrity.legible", True)
        span.set_attribute("data_integrity.contemporaneous", True)
        span.set_attribute("data_integrity.original", True)
        span.set_attribute("data_integrity.accurate", True)
        span.set_attribute("data_integrity.complete", True)
        span.set_attribute("data_integrity.consistent", True)
        span.set_attribute("data_integrity.enduring", True)
        span.set_attribute("data_integrity.available", True)

        # Process attributes
        span.set_attribute("process.validation.category", "automated")
        span.set_attribute("process.pharmaceutical.test_generation", True)
        span.set_attribute("process.quality.assurance", True)

        # Add custom metadata
        for key, value in metadata.items():
            if isinstance(value, (str, int, float, bool)):
                span.set_attribute(f"workflow.{key}", value)
            else:
                span.set_attribute(f"workflow.{key}", str(value))

    except Exception as e:
        # Don't fail if span enhancement fails
        logger.warning(f"Failed to enhance workflow span with compliance attributes: {e}")


def get_workflow_tracer(workflow_name: str):
    """
    Get a tracer specifically configured for workflow instrumentation.
    
    Args:
        workflow_name: Name of the workflow (e.g., 'unified_workflow', 'categorization')
    
    Returns:
        Tracer configured for workflow instrumentation
    """
    phoenix_manager = get_phoenix_manager()
    if phoenix_manager and phoenix_manager._initialized:
        return phoenix_manager.get_tracer(f"pharmaceutical_workflows.{workflow_name}")
    return None


def get_current_span():
    """
    Get the current active span from OpenTelemetry context.
    
    Returns:
        Current span or None if no active span
    """
    try:
        from opentelemetry.trace import get_current_span as otel_get_current_span
        return otel_get_current_span()
    except ImportError:
        return None


# Singleton instance
_phoenix_manager: PhoenixManager | None = None


def setup_phoenix(config: PhoenixConfig | None = None) -> PhoenixManager:
    """
    Set up Phoenix observability with the given configuration.
    
    This is the main entry point for Phoenix setup. It creates or returns
    a singleton PhoenixManager instance.
    
    Args:
        config: Optional Phoenix configuration. Uses environment defaults if None.
        
    Returns:
        Configured PhoenixManager instance
    """
    global _phoenix_manager

    if _phoenix_manager is None:
        _phoenix_manager = PhoenixManager(config)
        _phoenix_manager.setup()

    return _phoenix_manager


def shutdown_phoenix(timeout_seconds: int = 5) -> None:
    """
    Shutdown Phoenix observability system with proper cleanup.
    
    Args:
        timeout_seconds: Maximum time to wait for trace export completion
    """
    global _phoenix_manager

    if _phoenix_manager:
        _phoenix_manager.shutdown(timeout_seconds=timeout_seconds)
        # Don't set to None - keep manager for potential reuse
        logger.info("Phoenix manager shutdown complete")
    else:
        logger.debug("No Phoenix manager to shutdown")


def get_phoenix_manager() -> PhoenixManager | None:
    """Get the current Phoenix manager instance."""
    return _phoenix_manager
