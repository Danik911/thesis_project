"""Cognito JWT validation and user context extraction for BI RBAC."""

from __future__ import annotations

import logging
from functools import lru_cache

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from .auth_models import BIUser, UserRole
from .config import get_bi_config

logger = logging.getLogger(__name__)

_bearer_required = HTTPBearer(auto_error=True)
_bearer_optional = HTTPBearer(auto_error=False)


@lru_cache(maxsize=1)
def _get_cognito_jwks(region: str, user_pool_id: str) -> dict:
    """Fetch and cache Cognito JWKS (JSON Web Key Set)."""
    url = (
        f"https://cognito-idp.{region}.amazonaws.com/"
        f"{user_pool_id}/.well-known/jwks.json"
    )
    response = httpx.get(url, timeout=10)
    response.raise_for_status()
    return response.json()


def _decode_cognito_token(token: str) -> dict:
    """Validate and decode a Cognito JWT token."""
    config = get_bi_config()
    region = config.cognito_region
    user_pool_id = config.cognito_user_pool_id
    client_id = config.cognito_client_id

    if not user_pool_id or not client_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Cognito not configured: "
                "BI_COGNITO_USER_POOL_ID and BI_COGNITO_CLIENT_ID required"
            ),
        )

    jwks = _get_cognito_jwks(region, user_pool_id)
    issuer = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}"

    # Get key ID from unverified header
    unverified_header = jwt.get_unverified_header(token)
    kid = unverified_header.get("kid")

    # Find matching key in JWKS
    key = None
    for k in jwks["keys"]:
        if k["kid"] == kid:
            key = k
            break

    if key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="JWT key ID not found in Cognito JWKS",
        )

    claims = jwt.decode(
        token,
        key,
        algorithms=["RS256"],
        audience=client_id,
        issuer=issuer,
        options={"verify_at_hash": False},
    )
    return claims


def _extract_user(claims: dict) -> BIUser:
    """Extract BIUser from decoded JWT claims."""
    groups = claims.get("cognito:groups", [])

    # Determine role from groups (Admin takes precedence)
    if "Admin" in groups:
        role = UserRole.ADMIN
    elif "Operator" in groups:
        role = UserRole.OPERATOR
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User has no recognized role group. Groups: {groups}",
        )

    return BIUser(
        sub=claims["sub"],
        email=claims.get("email", ""),
        role=role,
        site=claims.get("custom:site"),
        groups=groups,
        username=claims.get("cognito:username", claims.get("sub", "")),
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_required),
) -> BIUser:
    """FastAPI dependency: extract and validate the current user from JWT.

    Raises 401 if token is missing or invalid.
    Raises 403 if user has no recognized role group.
    """
    try:
        claims = _decode_cognito_token(credentials.credentials)
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {type(exc).__name__}: {exc}",
        ) from exc

    return _extract_user(claims)


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_optional),
) -> BIUser | None:
    """FastAPI dependency: returns user if token present, None otherwise.

    Used when BI_AUTH_ENABLED=false (auth is optional).
    """
    if credentials is None:
        return None
    try:
        claims = _decode_cognito_token(credentials.credentials)
        return _extract_user(claims)
    except (JWTError, HTTPException):
        return None


async def require_admin(
    user: BIUser = Depends(get_current_user),
) -> BIUser:
    """FastAPI dependency: require Admin role.

    Raises 403 if user is not in Admin group.
    """
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Admin role required. Current role: {user.role.value}",
        )
    return user


def get_user_dependency():
    """Return the appropriate auth dependency based on BI_AUTH_ENABLED config.

    When auth is enabled: returns get_current_user (requires valid JWT).
    When auth is disabled: returns get_optional_user (JWT optional).
    """
    config = get_bi_config()
    if config.auth_enabled:
        return Depends(get_current_user)
    return Depends(get_optional_user)
