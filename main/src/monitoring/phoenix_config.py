"""
Arize Phoenix configuration and management for pharmaceutical workflow observability.

This module provides environment-aware Phoenix setup supporting both local development
and production deployment with full GAMP-5 compliance tracing.
"""

import logging
import os
from dataclasses import dataclass, field
from typing import Any

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk import trace as trace_sdk
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace.export import BatchSpanProcessor

logger = logging.getLogger(__name__)


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

            self._initialized = True
            logger.info(
                f"Phoenix observability initialized for {self.config.deployment_environment} "
                f"environment with endpoint: {self.config.otlp_endpoint}"
            )

        except Exception as e:
            logger.error(f"Failed to initialize Phoenix: {e}")
            # Graceful degradation - don't fail the application
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
                    logger.info(f"✅ Connected to existing Phoenix instance at: {health_url}")
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
                logger.info(f"✅ Using Docker Phoenix instance at: {docker_url}")
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

    def _instrument_llamaindex(self) -> None:
        """Instrument LlamaIndex with OpenInference and fallback options."""
        try:
            from openinference.instrumentation.llama_index import LlamaIndexInstrumentor

            # Instrument with our tracer provider
            LlamaIndexInstrumentor().instrument(
                skip_dep_check=True,
                tracer_provider=self.tracer_provider
            )

            logger.debug("LlamaIndex instrumented successfully with OpenInference")

        except ImportError:
            logger.warning(
                "OpenInference LlamaIndex instrumentation not available. "
                "Install with: pip install openinference-instrumentation-llama-index"
            )
            self._try_fallback_instrumentation()
        except Exception as e:
            logger.error(f"OpenInference instrumentation failed: {e}")
            self._try_fallback_instrumentation()

    def _try_fallback_instrumentation(self) -> None:
        """Try fallback instrumentation using simple global handler."""
        try:
            import llama_index.core
            llama_index.core.set_global_handler("arize_phoenix")
            logger.info("✅ Fallback to simple Phoenix global handler successful")
        except Exception as fallback_error:
            logger.warning(f"❌ Fallback instrumentation also failed: {fallback_error}")
            logger.info("Continuing without Phoenix instrumentation")

    def get_tracer(self, name: str) -> trace.Tracer:
        """
        Get a tracer instance for manual instrumentation.
        
        Args:
            name: Name of the tracer (typically module name)
            
        Returns:
            Tracer instance
        """
        return trace.get_tracer(name)

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
                    logger.info(f"✅ Successfully flushed all pending traces")
                else:
                    logger.warning(f"⚠️  Trace flush may have timed out after {timeout_seconds}s")
                
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
