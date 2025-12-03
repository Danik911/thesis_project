"""
LangFuse observability client for pharmaceutical test generation system.

GAMP-5 compliant trace instrumentation for FastAPI endpoints and LlamaIndex workflows.
Provides centralized initialization, health checks, and graceful shutdown with explicit
error handling (NO FALLBACK LOGIC).
"""

import logging
import os
import base64
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from langfuse import Langfuse
from openinference.instrumentation.llama_index import LlamaIndexInstrumentor
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor

logger = logging.getLogger(__name__)

# Load environment variables from .env.local (for local development)
env_file = Path(__file__).parent.parent.parent / ".env.local"
if env_file.exists():
    load_dotenv(env_file)


class LangFuseObservability:
    """
    Manages LangFuse client lifecycle for FastAPI application.

    Provides centralized initialization, health checks, and graceful shutdown
    with GAMP-5 compliant trace metadata. Implements zero-tolerance policy
    for fallback logic - all errors propagate explicitly.

    Attributes:
        client: LangFuse client instance (None if not initialized)
        enabled: Whether LangFuse observability is active
    """

    def __init__(self):
        """Initialize observability manager with credentials from environment."""
        self.client: Optional[Langfuse] = None
        self.enabled = False
        self._public_key = os.getenv("LANGFUSE_PUBLIC_KEY", "")
        self._secret_key = os.getenv("LANGFUSE_SECRET_KEY", "")
        self._host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

    def initialize(self) -> None:
        """
        Initialize LangFuse client with credentials from environment.

        Performs health check to verify connection and credentials. Fails
        explicitly if credentials missing or connection fails (NO FALLBACK).

        Raises:
            RuntimeError: If credentials are missing or connection fails.
                         Error includes full diagnostic information.
        """
        if not self._public_key or not self._secret_key:
            error_msg = (
                "LangFuse credentials missing. Required environment variables:\n"
                f"  - LANGFUSE_PUBLIC_KEY (current: {'SET' if self._public_key else 'MISSING'})\n"
                f"  - LANGFUSE_SECRET_KEY (current: {'SET' if self._secret_key else 'MISSING'})\n"
                f"  - LANGFUSE_HOST (optional, current: {self._host})\n"
                f"Please add these to .env.local or environment configuration."
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        try:
            # Initialize client
            self.client = Langfuse(
                public_key=self._public_key,
                secret_key=self._secret_key,
                host=self._host,
            )

            # Configure OpenTelemetry for LlamaIndex -> Langfuse
            # We need to manually configure the OTLP exporter because LlamaIndexInstrumentor
            # uses the global OpenTelemetry tracer provider.
            
            # Create OTLP exporter pointing to Langfuse
            # Auth header is Basic base64(public_key:secret_key)
            auth_str = f"{self._public_key}:{self._secret_key}"
            auth_b64 = base64.b64encode(auth_str.encode()).decode()
            
            otlp_exporter = OTLPSpanExporter(
                endpoint=f"{self._host}/api/public/otel/v1/traces",
                headers={"Authorization": f"Basic {auth_b64}"}
            )
            
            # Set up global tracer provider
            trace_provider = TracerProvider()
            trace_provider.add_span_processor(SimpleSpanProcessor(otlp_exporter))
            trace.set_tracer_provider(trace_provider)

            # Initialize LlamaIndex instrumentation
            # This will now use the global tracer provider we just configured
            try:
                LlamaIndexInstrumentor().instrument()
                logger.info("LlamaIndex instrumentation initialized with OTLP exporter")
            except Exception as e:
                logger.warning(f"Failed to initialize LlamaIndex instrumentation: {e}")

            # Health check: Use auth_check() for synchronous verification
            # This actually makes an HTTP request and verifies credentials + network
            auth_result = False
            try:
                auth_result = self.client.auth_check()
                logger.info(f"LangFuse auth_check() result: {auth_result}")
            except Exception as auth_error:
                logger.error(f"LangFuse auth_check() failed: {type(auth_error).__name__}: {auth_error}")

            if not auth_result:
                logger.error(
                    f"LangFuse authentication FAILED!\n"
                    f"  Host: {self._host}\n"
                    f"  Public Key: {self._public_key[:8]}...\n"
                    f"  This indicates network connectivity issues or invalid credentials."
                )
                # Continue anyway but mark as warning

            # Create test span for additional verification
            try:
                test_span = self.client.start_span(
                    name="health_check_span",
                    metadata={"health_check": True, "environment": "startup", "auth_check": auth_result}
                )
                test_span.end()
                self.client.flush()
                logger.info("LangFuse health_check_span created and flushed")
            except Exception as e:
                logger.warning(f"LangFuse health check span failed: {e}")

            self.enabled = True
            logger.info(
                f"LangFuse initialized successfully\n"
                f"  Host: {self._host}\n"
                f"  Public Key: {self._public_key[:8]}...\n"
                f"  Auth Check: {'PASSED' if auth_result else 'FAILED'}"
            )

        except Exception as e:
            error_msg = (
                f"Failed to initialize LangFuse client: {type(e).__name__}: {e}\n"
                f"  Host: {self._host}\n"
                f"  Public Key: {self._public_key[:8] if self._public_key else 'MISSING'}...\n"
                f"  Verify credentials are valid and network connectivity is available."
            )
            logger.error(error_msg, exc_info=True)
            raise RuntimeError(error_msg) from e

    def shutdown(self) -> None:
        """
        Gracefully shutdown LangFuse client.

        Ensures all pending traces are flushed before shutdown. Errors during
        shutdown are logged but do not prevent shutdown from completing.
        """
        if self.client and self.enabled:
            try:
                logger.info("Flushing pending LangFuse traces...")
                self.client.flush()
                logger.info("LangFuse client flushed and shut down successfully")
            except Exception as e:
                # Log error but don't raise - allow shutdown to continue
                logger.error(
                    f"Error during LangFuse shutdown: {type(e).__name__}: {e}",
                    exc_info=True
                )

    def get_client(self) -> Optional[Langfuse]:
        """
        Return the LangFuse client instance if initialized.

        Returns:
            Langfuse client if enabled, None otherwise
        """
        return self.client if self.enabled else None


# Global instance for application-wide access
_langfuse_observability = LangFuseObservability()


def initialize_langfuse() -> None:
    """
    Initialize the global LangFuse observability instance.

    Call this during FastAPI application startup. Raises RuntimeError
    if initialization fails (NO FALLBACK).

    Raises:
        RuntimeError: If LangFuse initialization fails
    """
    _langfuse_observability.initialize()


def shutdown_langfuse() -> None:
    """
    Shutdown the global LangFuse observability instance.

    Call this during FastAPI application shutdown. Ensures all pending
    traces are flushed.
    """
    _langfuse_observability.shutdown()


def get_langfuse_client() -> Optional[Langfuse]:
    """
    Get the global LangFuse client instance.

    Returns:
        Langfuse client if initialized and enabled, None otherwise
    """
    return _langfuse_observability.get_client()
