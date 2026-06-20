"""Tests for the Supabase error boundary (db_safety.py).

Acceptance criteria:
- SupabaseOperationError handler is registered and reachable end-to-end through
  the FastAPI TestClient (not just unit-tested in isolation).
- A Supabase failure in at least two previously-unprotected endpoints now returns
  a clean 503 instead of a raw 500 with leaked internal detail.
- supabase_guard unit behaviour: logs the failure, re-raises as SupabaseOperationError.
"""
import logging
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from services.db_safety import SupabaseOperationError, supabase_guard


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _AlwaysRaisesTable:
    """Supabase table stub that raises on .execute()."""

    def __init__(self, exc: Exception):
        self._exc = exc

    def select(self, *a, **kw):
        return self

    def insert(self, *a, **kw):
        return self

    def update(self, *a, **kw):
        return self

    def eq(self, *a, **kw):
        return self

    def single(self):
        return self

    def order(self, *a, **kw):
        return self

    def gte(self, *a, **kw):
        return self

    def execute(self):
        raise self._exc


class _SelectiveFakeSupabase:
    """Returns a happy stub for some tables and raises for others."""

    def __init__(self, *, raise_on: set[str], exc: Exception | None = None):
        self._raise_on = raise_on
        self._exc = exc or RuntimeError("simulated DB failure")

    def table(self, name: str):
        if name in self._raise_on:
            return _AlwaysRaisesTable(self._exc)
        return _HappyTable(name)


class _HappyTable:
    """Supabase table stub that returns plausible data."""

    def __init__(self, name: str):
        self._name = name

    def select(self, *a, **kw):
        return self

    def insert(self, *a, **kw):
        return self

    def update(self, *a, **kw):
        return self

    def eq(self, *a, **kw):
        return self

    def single(self):
        return self

    def order(self, *a, **kw):
        return self

    def gte(self, *a, **kw):
        return self

    def lt(self, *a, **kw):
        return self

    def in_(self, *a, **kw):
        return self

    def execute(self):
        if self._name == "diagnostics":
            return SimpleNamespace(
                data={"id": "diag-1", "status": "approved", "matches_unlocked": True},
                count=0,
            )
        return SimpleNamespace(data=[], count=0)


# ---------------------------------------------------------------------------
# Unit tests for supabase_guard itself
# ---------------------------------------------------------------------------

class SupabaseGuardUnitTests(unittest.TestCase):
    def test_guard_passes_through_on_success(self):
        with supabase_guard("test operation"):
            result = 42
        self.assertEqual(result, 42)

    def test_guard_raises_SupabaseOperationError_on_exception(self):
        original = ValueError("connection refused")
        with self.assertRaises(SupabaseOperationError) as ctx:
            with supabase_guard("fetching user rows"):
                raise original
        exc = ctx.exception
        self.assertIs(exc.original, original)
        self.assertEqual(exc.operation, "fetching user rows")

    def test_guard_logs_error_with_operation_name(self):
        with self.assertLogs("services.db_safety", level="ERROR") as log_ctx:
            with self.assertRaises(SupabaseOperationError):
                with supabase_guard("fetching pending diagnostics for review queue"):
                    raise RuntimeError("timeout")
        self.assertTrue(
            any("fetching pending diagnostics" in msg for msg in log_ctx.output)
        )

    def test_SupabaseOperationError_str_includes_operation_and_original(self):
        exc = SupabaseOperationError("loading matches", RuntimeError("boom"))
        self.assertIn("loading matches", str(exc))
        self.assertIn("boom", str(exc))

    def test_guard_preserves_cause_chain(self):
        original = ConnectionError("DB unreachable")
        try:
            with supabase_guard("op"):
                raise original
        except SupabaseOperationError as e:
            self.assertIs(e.__cause__, original)


# ---------------------------------------------------------------------------
# Integration tests: end-to-end through FastAPI TestClient
# ---------------------------------------------------------------------------

def _admin_client():
    """Return a TestClient with admin auth bypassed."""
    from main import app
    from services.admin_auth import require_admin_authorization

    app.dependency_overrides[require_admin_authorization] = lambda: None
    client = TestClient(app, raise_server_exceptions=False)
    return app, client


class SupabaseErrorBoundaryEndToEndTests(unittest.TestCase):
    """These tests confirm SupabaseOperationError is wired all the way through
    FastAPI's exception handler — not just the guard in isolation."""

    def tearDown(self):
        from main import app
        app.dependency_overrides.clear()

    # ------------------------------------------------------------------
    # GET /api/admin/diagnostics  (previously unprotected: get_pending)
    # ------------------------------------------------------------------

    def test_get_pending_returns_503_when_supabase_fails(self):
        from routers import admin as admin_router

        app, client = _admin_client()
        fake_db = _SelectiveFakeSupabase(raise_on={"diagnostics"})

        with patch.object(admin_router, "get_supabase", return_value=fake_db):
            resp = client.get("/api/admin/diagnostics")

        self.assertEqual(resp.status_code, 503)
        body = resp.json()
        self.assertEqual(body["detail"], "A database operation failed. Please try again.")

    def test_get_pending_503_does_not_leak_internal_error_text(self):
        from routers import admin as admin_router

        app, client = _admin_client()
        fake_db = _SelectiveFakeSupabase(
            raise_on={"diagnostics"},
            exc=RuntimeError("secret internal connection string xyz"),
        )

        with patch.object(admin_router, "get_supabase", return_value=fake_db):
            resp = client.get("/api/admin/diagnostics")

        self.assertEqual(resp.status_code, 503)
        self.assertNotIn("secret internal", resp.text)
        self.assertNotIn("connection string", resp.text)

    # ------------------------------------------------------------------
    # GET /api/admin/stats  (previously unprotected: get_stats)
    # ------------------------------------------------------------------

    def test_get_stats_returns_503_when_supabase_fails(self):
        from routers import admin as admin_router

        app, client = _admin_client()
        fake_db = _SelectiveFakeSupabase(raise_on={"diagnostics"})

        with patch.object(admin_router, "get_supabase", return_value=fake_db):
            resp = client.get("/api/admin/stats")

        self.assertEqual(resp.status_code, 503)
        self.assertEqual(
            resp.json()["detail"], "A database operation failed. Please try again."
        )

    # ------------------------------------------------------------------
    # GET /api/admin/diagnostics/{id}/matches  (previously unprotected)
    # ------------------------------------------------------------------

    def test_get_diagnostic_matches_returns_503_when_supabase_fails(self):
        from routers import admin as admin_router

        app, client = _admin_client()
        fake_db = _SelectiveFakeSupabase(raise_on={"ausbildung_matches"})

        with patch.object(admin_router, "get_supabase", return_value=fake_db):
            resp = client.get("/api/admin/diagnostics/diag-1/matches")

        self.assertEqual(resp.status_code, 503)

    # ------------------------------------------------------------------
    # GET /api/diagnostic/{id}/matches  (public; ausbildung_matches was unprotected)
    # ------------------------------------------------------------------

    def test_public_matches_returns_503_when_ausbildung_matches_fails(self):
        """The diagnostics select (guarded by existing try/except) succeeds;
        the ausbildung_matches select (newly wrapped) fails → 503."""
        from routers import diagnostic as diag_router

        from main import app
        client = TestClient(app, raise_server_exceptions=False)

        fake_db = _SelectiveFakeSupabase(raise_on={"ausbildung_matches"})

        with patch.object(diag_router, "get_supabase", return_value=fake_db):
            resp = client.get("/api/diagnostic/diag-1/matches")

        self.assertEqual(resp.status_code, 503)
        self.assertEqual(
            resp.json()["detail"], "A database operation failed. Please try again."
        )

    # ------------------------------------------------------------------
    # Handler registration sanity: the handler must be on the app instance
    # ------------------------------------------------------------------

    def test_SupabaseOperationError_handler_is_registered_on_app(self):
        from main import app

        registered_types = list(app.exception_handlers.keys())
        self.assertIn(
            SupabaseOperationError,
            registered_types,
            "SupabaseOperationError must be registered as a FastAPI exception handler",
        )


# ---------------------------------------------------------------------------
# ITEM 4: error-detail leak fixes in diagnostic.py
# ---------------------------------------------------------------------------

class ErrorDetailLeakTests(unittest.TestCase):
    """Confirm that internal error text is no longer sent to the client."""

    def test_update_progress_returns_generic_message_on_db_failure(self):
        from main import app
        from routers import diagnostic as diag_router

        client = TestClient(app, raise_server_exceptions=False)

        # Make the first DB call (select diagnostic) raise with recognisable text
        fake_db = _SelectiveFakeSupabase(
            raise_on={"diagnostics"},
            exc=RuntimeError("pg: auth token expired xyzSecret"),
        )

        with patch.object(diag_router, "get_supabase", return_value=fake_db):
            resp = client.patch(
                "/api/diagnostic/diag-1/progress",
                json={"completed_steps": [1, 2]},
                headers={"Authorization": "Bearer some-token"},
            )

        # 500 from update_progress (Supabase failure → generic detail, not str(e))
        self.assertNotIn("xyzSecret", resp.text)
        self.assertNotIn("pg:", resp.text)


if __name__ == "__main__":
    unittest.main()
