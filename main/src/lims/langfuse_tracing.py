"""LIMS Langfuse client initialization and access.

Provides a separate Langfuse client for the AI4LIMS PoC, independent of
the thesis ``main/api/observability.py`` (which bundles OTEL + LlamaIndex
instrumentation).

Reads credentials from ``LANGFUSE_SECRET_KEY``, ``LANGFUSE_PUBLIC_KEY``,
and ``LANGFUSE_BASE_URL`` environment variables.  Uses ``python-dotenv``
to load ``.env.local`` automatically.

Behaviour:
- If keys are **missing**: tracing is explicitly disabled (returns None).
- If keys are **present but auth fails**: raises ``RuntimeError`` (no silent fallback).

NO FALLBACK LOGIC.
"""

from __future__ import annotations

import logging
import os

from dotenv import load_dotenv
from langfuse import Langfuse

logger = logging.getLogger(__name__)

# Module-level cached client
_client: Langfuse | None = None
_initialized: bool = False


def init_lims_langfuse() -> Langfuse | None:
    """Initialize the LIMS Langfuse client.

    Returns:
        Langfuse client if credentials are present and auth succeeds,
        None if credentials are not configured.

    Raises:
        RuntimeError: If credentials are present but authentication fails.
    """
    global _client, _initialized

    if _initialized:
        return _client

    # Load .env.local (same pattern as main/api/observability.py)
    load_dotenv(".env.local", override=True)

    secret_key = os.getenv("LANGFUSE_SECRET_KEY", "")
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY", "")
    base_url = os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com")

    if not secret_key or not public_key:
        logger.info(
            "LIMS Langfuse tracing disabled: LANGFUSE_SECRET_KEY or "
            "LANGFUSE_PUBLIC_KEY not set"
        )
        _initialized = True
        _client = None
        return None

    client = Langfuse(
        public_key=public_key,
        secret_key=secret_key,
        host=base_url,
    )

    # Verify credentials -- fail loudly if they are invalid
    try:
        auth_ok = client.auth_check()
    except Exception as e:
        raise RuntimeError(
            f"LIMS Langfuse auth_check() raised {type(e).__name__}: {e}\n"
            f"  Host: {base_url}\n"
            f"  Public Key: {public_key[:8]}...\n"
            "Verify credentials in .env.local"
        ) from e

    if not auth_ok:
        raise RuntimeError(
            "LIMS Langfuse auth_check() returned False.\n"
            f"  Host: {base_url}\n"
            f"  Public Key: {public_key[:8]}...\n"
            "Credentials are invalid or network is unreachable."
        )

    logger.info(
        "LIMS Langfuse initialized: host=%s, key=%s...",
        base_url,
        public_key[:8],
    )

    _client = client
    _initialized = True
    return _client


def get_lims_langfuse() -> Langfuse | None:
    """Return cached Langfuse client, or None if tracing is disabled.

    Calls ``init_lims_langfuse()`` on first access.
    """
    if not _initialized:
        return init_lims_langfuse()
    return _client


def flush_lims_langfuse() -> None:
    """Flush pending Langfuse traces."""
    if _client is not None:
        _client.flush()
        logger.debug("LIMS Langfuse flushed")
