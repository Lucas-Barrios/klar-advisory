from __future__ import annotations

import contextvars
import logging

_request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id", default="-"
)


def get_request_id() -> str:
    return _request_id_var.get()


def set_request_id(value: str) -> contextvars.Token:
    return _request_id_var.set(value)


class RequestIdFilter(logging.Filter):
    """Injects the current request_id into every LogRecord automatically."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = _request_id_var.get()
        return True
