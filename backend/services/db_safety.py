from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)


class SupabaseOperationError(Exception):
    def __init__(self, operation: str, original: Exception):
        self.operation = operation
        self.original = original
        super().__init__(f"{operation}: {original}")


@contextmanager
def supabase_guard(operation: str):
    """Wrap a Supabase call. On failure, logs with full context
    (request_id is injected automatically by the logging filter)
    and raises a typed SupabaseOperationError instead of letting
    the raw postgrest/httpx exception propagate to the client."""
    try:
        yield
    except Exception as exc:
        logger.error(
            "Supabase operation failed: %s", operation, exc_info=True
        )
        raise SupabaseOperationError(operation, exc) from exc
