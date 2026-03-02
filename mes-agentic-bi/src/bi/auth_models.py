"""Pydantic models for BI RBAC authentication."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class UserRole(str, Enum):
    """User roles for BI RBAC."""

    ADMIN = "Admin"
    OPERATOR = "Operator"


class BIUser(BaseModel):
    """Authenticated user extracted from Cognito JWT."""

    sub: str  # Cognito user UUID
    email: str
    role: UserRole
    site: str | None = None  # custom:site attribute (None for Admin)
    groups: list[str]  # Cognito groups from token claims
    username: str
