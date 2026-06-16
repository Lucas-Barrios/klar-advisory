from __future__ import annotations

import re


EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
PHONE_PATTERN = re.compile(r"(?<!\w)(?:\+?\d[\d\s().-]{7,}\d)(?!\w)")
NAME_LIKE_PATTERN = re.compile(
    r"\b[A-ZÀ-ÖØ-Þ][A-Za-zÀ-ÖØ-öø-ÿ'’-]{1,}"
    r"(?:\s+[A-ZÀ-ÖØ-Þ][A-Za-zÀ-ÖØ-öø-ÿ'’-]{1,}){1,3}\b"
)


def _redact_identifier(value: str, identifier: str) -> str:
    escaped = re.escape(identifier.strip())
    if not escaped:
        return value
    return re.sub(escaped, "[redacted-name]", value, flags=re.IGNORECASE)


def redact_sensitive_text(
    value: str | None,
    *,
    identifiers: list[str | None] | None = None,
    redact_name_like: bool = False,
) -> str | None:
    if not value:
        return value

    redacted = EMAIL_PATTERN.sub("[redacted-email]", value)
    redacted = PHONE_PATTERN.sub("[redacted-phone]", redacted)

    for identifier in identifiers or []:
        if isinstance(identifier, str) and identifier.strip():
            redacted = _redact_identifier(redacted, identifier)

    if redact_name_like:
        redacted = NAME_LIKE_PATTERN.sub("[redacted-name]", redacted)

    return redacted
