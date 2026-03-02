"""MES Agentic BI – standalone FastAPI application."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

_ROOT_ENV = Path(__file__).resolve().parents[1] / ".env.local"
load_dotenv(dotenv_path=_ROOT_ENV)
load_dotenv()

from src.bi.audit.logger import AuditLogger
from src.bi.audit.middleware import AuditMiddleware
from src.bi.audit.models import AuditEventType
from src.bi.config import get_bi_config

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MES Agentic BI",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS: restrict origins when auth is enabled, permissive otherwise
_cors_origins_raw = os.getenv("BI_CORS_ORIGINS", "*")
_cors_origins = (
    ["*"]
    if _cors_origins_raw.strip() == "*"
    else [o.strip() for o in _cors_origins_raw.split(",") if o.strip()]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(AuditMiddleware)


@app.get("/health")
async def health() -> dict:
    return {"status": "healthy", "service": "mes-agentic-bi"}


@app.on_event("startup")
async def startup_init_audit() -> None:
    config = get_bi_config()
    audit = AuditLogger.initialize(config)
    await audit.emit(
        AuditEventType.SYSTEM_STARTUP,
        payload={
            "service": "mes-agentic-bi",
            "audit_enabled": config.audit_enabled,
            "cloudtrail_lake_enabled": config.cloudtrail_lake_enabled,
        },
    )


# Register BI routers
from api.bi_router import router as bi_router  # noqa: E402
from api.bi_voice_router import router as bi_voice_router  # noqa: E402

app.include_router(bi_router, prefix="/bi")
app.include_router(bi_voice_router, prefix="/bi/voice")
