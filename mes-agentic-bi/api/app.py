"""MES Agentic BI – standalone FastAPI application."""

from __future__ import annotations

import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

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


@app.get("/health")
async def health() -> dict:
    return {"status": "healthy", "service": "mes-agentic-bi"}


# Register BI routers
from api.bi_router import router as bi_router  # noqa: E402
from api.bi_voice_router import router as bi_voice_router  # noqa: E402

app.include_router(bi_router, prefix="/bi")
app.include_router(bi_voice_router, prefix="/bi/voice")
