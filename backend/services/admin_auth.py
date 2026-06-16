from __future__ import annotations

import hmac
import os

from fastapi import Header, HTTPException, status


ADMIN_TOKEN_ENV = "ADMIN_API_TOKEN"
LEGACY_ADMIN_TOKEN_ENV = "ADMIN_SECRET"


def get_configured_admin_token() -> str | None:
    token = os.getenv(ADMIN_TOKEN_ENV) or os.getenv(LEGACY_ADMIN_TOKEN_ENV)
    return token.strip() if token and token.strip() else None


def extract_bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    scheme, separator, token = authorization.partition(" ")
    if separator != " " or scheme.lower() != "bearer" or not token.strip():
        return None
    return token.strip()


def require_admin_authorization(
    authorization: str | None = Header(default=None),
) -> None:
    expected_token = get_configured_admin_token()
    if expected_token is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin authentication is not configured",
        )

    supplied_token = extract_bearer_token(authorization)
    if supplied_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing admin authorization",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not hmac.compare_digest(supplied_token, expected_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin authorization",
        )
