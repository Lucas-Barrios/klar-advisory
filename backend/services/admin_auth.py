from __future__ import annotations

import hmac
import logging
import os
from datetime import datetime, timezone

from fastapi import Header, HTTPException, Request, status

from database import get_supabase

logger = logging.getLogger(__name__)

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


def _log_auth_failure(request: Request, failure_type: str) -> None:
    """Insert an audit row for a failed admin auth attempt.

    Non-blocking: wrapped in try/except so a DB error never prevents the
    401/403 from being returned. NEVER logs the supplied token — only
    failure_type, client IP, and timestamp.
    """
    try:
        client_ip = request.client.host if request.client else "unknown"
        supabase = get_supabase()
        supabase.table("audit_log").insert({
            "action": "admin_auth_failure",
            "actor": "unknown",
            "details": {
                "failure_type": failure_type,
                "client_ip": client_ip,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        }).execute()
    except Exception:
        logger.warning("Failed to persist admin_auth_failure audit row (non-blocking)", exc_info=True)


def require_admin_authorization(
    request: Request,
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
        _log_auth_failure(request, "missing")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing admin authorization",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not hmac.compare_digest(supplied_token, expected_token):
        _log_auth_failure(request, "invalid")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin authorization",
        )
