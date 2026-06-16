from __future__ import annotations

import hashlib
import hmac
import secrets


def generate_progress_token() -> str:
    return secrets.token_urlsafe(32)


def hash_progress_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def verify_progress_token(token: str | None, expected_hash: str | None) -> bool:
    if not token or not expected_hash:
        return False
    supplied_hash = hash_progress_token(token.strip())
    return hmac.compare_digest(supplied_hash, expected_hash)
