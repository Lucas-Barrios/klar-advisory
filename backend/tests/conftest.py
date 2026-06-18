import pytest


@pytest.fixture(autouse=True)
def reset_rate_limiter_storage():
    """Reset the in-memory rate-limit storage before every test.

    The limiter uses MemoryStorage (a global singleton) keyed on client IP.
    Without this reset, request counts from one test bleed into subsequent
    tests that share the same 'testclient' IP, causing spurious 429s.
    """
    from services.rate_limiter import limiter
    limiter._storage.reset()
    yield
