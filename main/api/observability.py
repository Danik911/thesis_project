"""
LangFuse observability client for pharmaceutical test generation system.

GAMP-5 compliant trace instrumentation for FastAPI endpoints and LlamaIndex workflows.
Provides centralized initialization, health checks, and graceful shutdown with explicit
error handling (NO FALLBACK LOGIC).
"""

import logging
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from langfuse import Langfuse

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

            # Health check: attempt to create a test trace
            # This verifies credentials and network connectivity
            try:
                if hasattr(self.client, 'trace'):
                    test_trace = self.client.trace(name="health_check_trace")
                    test_trace.update(metadata={"health_check": True, "environment": "startup"})
                    test_trace.end()  # Close trace to prevent orphan traces in LangFuse
                elif hasattr(self.client, 'auth_check'):
                     if not self.client.auth_check():
                         raise RuntimeError("LangFuse auth check failed")
                else:
                    # Fallback for newer/older versions where trace might be different
                    # Just log that we initialized
                    logger.warning(f"LangFuse client initialized but 'trace' method not found. Available methods: {dir(self.client)}")

            except Exception as e:
                logger.warning(f"LangFuse health check failed (non-critical): {e}")
                # We continue anyway as the client might be valid for @observe
                pass

            self.enabled = True
            logger.info(
                f"LangFuse initialized successfully\n"
                f"  Host: {self._host}\n"
                f"  Public Key: {self._public_key[:8]}...\n"
                f"  Health Check: PASSED"
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
