"""
Langfuse API routes for trace retrieval.

Provides endpoints for fetching Langfuse trace data to display in the frontend
observability dashboard. Proxies requests to Langfuse Cloud API with caching.

CRITICAL: NO FALLBACK LOGIC - All errors propagate explicitly with full diagnostics.

GAMP-5 Compliance:
- Audit trail via logging
- Error traceability
- No data masking or artificial success responses
"""

import base64
import logging
import os
from datetime import UTC, datetime
from typing import Annotated

import httpx
from cachetools import TTLCache
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse

from .dependencies import CurrentUserDep

logger = logging.getLogger(__name__)

router = APIRouter(tags=["langfuse"])

# =============================================================================
# Cache Configuration
# =============================================================================

# Cache: 2-minute TTL, max 100 traces (matches frontend behavior)
# This prevents hammering Langfuse API with repeated requests for the same trace
TRACE_CACHE_TTL = 120  # seconds
_trace_cache: TTLCache[str, tuple[dict, datetime]] = TTLCache(
    maxsize=100,
    ttl=TRACE_CACHE_TTL
)


# =============================================================================
# Helper Functions
# =============================================================================


def _get_langfuse_credentials() -> tuple[str, str, str]:
    """
    Get Langfuse API credentials from environment variables.

    Returns:
        Tuple of (public_key, secret_key, host)

    Raises:
        HTTPException: If required credentials are missing

    CRITICAL: NO FALLBACK LOGIC - Missing credentials raise explicit errors.
    """
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    host = os.getenv("LANGFUSE_HOST") or os.getenv("LANGFUSE_BASE_URL") or "https://cloud.langfuse.com"

    if not public_key:
        logger.error("[Langfuse API] CRITICAL: LANGFUSE_PUBLIC_KEY not configured")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="CRITICAL: LANGFUSE_PUBLIC_KEY environment variable not configured"
        )

    if not secret_key:
        logger.error("[Langfuse API] CRITICAL: LANGFUSE_SECRET_KEY not configured")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="CRITICAL: LANGFUSE_SECRET_KEY environment variable not configured"
        )

    return public_key, secret_key, host


async def _fetch_langfuse_trace(trace_id: str) -> dict:
    """
    Fetch trace from Langfuse Cloud API using HTTP Basic Auth.

    Args:
        trace_id: Langfuse trace identifier

    Returns:
        Raw trace data from Langfuse API

    Raises:
        HTTPException: On API errors or network issues

    CRITICAL: NO FALLBACK LOGIC - All errors propagate with full diagnostics.
    """
    public_key, secret_key, host = _get_langfuse_credentials()

    # Build HTTP Basic Auth header (same format as Next.js implementation)
    auth_string = f"{public_key}:{secret_key}"
    auth_b64 = base64.b64encode(auth_string.encode()).decode()

    # Normalize host URL
    normalized_host = host.rstrip("/")

    # Request fields (match Next.js: core,io,observations,scores,metrics)
    fields = "core,io,observations,scores,metrics"
    url = f"{normalized_host}/api/public/traces/{trace_id}?fields={fields}"

    logger.info(f"[Langfuse API] Fetching trace {trace_id} from {normalized_host}")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                url,
                headers={
                    "Authorization": f"Basic {auth_b64}",
                    "Accept": "application/json"
                }
            )

        if not response.is_success:
            error_text = response.text
            logger.error(
                f"[Langfuse API] Error fetching trace {trace_id}: "
                f"status={response.status_code}, response={error_text[:500]}"
            )
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Langfuse API error: {error_text}"
            )

        logger.info(f"[Langfuse API] Successfully fetched trace {trace_id}")
        return response.json()

    except httpx.TimeoutException as e:
        logger.error(f"[Langfuse API] Timeout fetching trace {trace_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"Langfuse API timeout: {e}"
        )
    except httpx.RequestError as e:
        logger.error(f"[Langfuse API] Network error fetching trace {trace_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Langfuse API network error: {e}"
        )


# =============================================================================
# API Endpoints
# =============================================================================


@router.get("/api/langfuse/trace")
async def get_langfuse_trace(
    traceId: Annotated[str, Query(description="Langfuse trace ID to fetch")],
    user: CurrentUserDep,
):
    """
    Fetch Langfuse trace details by ID.

    Proxies requests to Langfuse Cloud API with HTTP Basic Auth.
    Responses are cached for 2 minutes to prevent API hammering.

    **Authentication:** Requires valid Clerk JWT token.

    **Response Format:**
    - `success: true` with `data` containing trace payload
    - `success: false` with `error` and `details` on failure

    **Cache Behavior:**
    - 2-minute TTL
    - Max 100 traces cached
    - Cache hits logged for debugging

    CRITICAL: NO FALLBACK LOGIC - All errors return explicit failure responses.
    """
    logger.info(f"[Langfuse API] Request for trace {traceId} by user {user.sub}")

    # Check cache first
    cache_hit = False
    if traceId in _trace_cache:
        payload, cached_at = _trace_cache[traceId]
        cache_hit = True
        logger.info(f"[Langfuse API] Cache HIT for trace {traceId} (cached at {cached_at.isoformat()})")
    else:
        try:
            payload = await _fetch_langfuse_trace(traceId)
            # Store in cache with timestamp
            _trace_cache[traceId] = (payload, datetime.now(UTC))
            logger.info(f"[Langfuse API] Cache MISS for trace {traceId} - fetched from Langfuse Cloud")
        except HTTPException:
            # Re-raise HTTP exceptions directly
            raise
        except Exception as e:
            # Unexpected errors - log full stack trace and return explicit error
            logger.exception(f"[Langfuse API] Unexpected error fetching trace {traceId}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "success": False,
                    "error": "Trace fetch failed",
                    "details": str(e)
                }
            )

    # Return success response matching frontend expectations
    return {
        "success": True,
        "data": payload,
        "metadata": {
            "fetchedAt": datetime.now(UTC).isoformat(),
            "traceId": traceId,
            "cacheHit": cache_hit,
        }
    }
