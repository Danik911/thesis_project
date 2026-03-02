"""FastAPI middleware for ALCOA+ request context enrichment."""

from __future__ import annotations

import time
from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class AuditMiddleware(BaseHTTPMiddleware):
    """Inject per-request audit context onto request.state."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-Id") or uuid4().hex
        user_id = request.headers.get("X-BI-User-Id", "anonymous")
        user_role = request.headers.get("X-BI-User-Role", "unknown")

        forwarded_for = request.headers.get("X-Forwarded-For", "")
        client_ip = forwarded_for.split(",")[0].strip() if forwarded_for else ""
        if not client_ip and request.client:
            client_ip = request.client.host

        request.state.request_id = request_id
        request.state.user_id = user_id
        request.state.user_role = user_role
        request.state.client_ip = client_ip
        request.state.audit_start_time = time.monotonic()

        response = await call_next(request)
        response.headers["X-Request-Id"] = request_id
        return response
