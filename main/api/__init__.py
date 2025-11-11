"""
FastAPI application for pharmaceutical test generation workflow.

Provides async job submission, status tracking, and result retrieval
with GAMP-5 compliance and ALCOA+ audit trail requirements.
"""

__all__ = ["app", "audit", "dependencies", "models", "worker"]
