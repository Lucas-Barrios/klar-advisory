"""Tests for backend/services/alerting.py.

Acceptance criteria:
- error-rate check fires when threshold is crossed, does not fire when it isn't.
- cooldown correctly prevents a second alert within the window.
- a failure inside alerting code does not propagate or break the calling request.
- cost alert fires above threshold, is silent below it.
"""
import os
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Supabase stubs
# ---------------------------------------------------------------------------

class _FakeTable:
    """Chainable stub that ignores filters and returns configured data."""

    def __init__(self, data, *, insert_store=None):
        self._data = data
        self._insert_store = insert_store

    def select(self, *a, **kw):
        return self

    def insert(self, row, **kw):
        if self._insert_store is not None:
            self._insert_store.append(row)
        return self

    def eq(self, *a, **kw):
        return self

    def gte(self, *a, **kw):
        return self

    def execute(self):
        return SimpleNamespace(data=self._data, count=len(self._data))


class _FakeSupabase:
    """Returns per-table configurable data; tracks audit_log inserts."""

    def __init__(self, *, ai_usage_rows=None, audit_log_rows=None):
        self._ai_usage_rows = ai_usage_rows or []
        self._audit_log_rows = audit_log_rows or []
        self.inserted = []

    def table(self, name: str):
        if name == "ai_usage_events":
            return _FakeTable(self._ai_usage_rows)
        if name == "audit_log":
            return _FakeTable(self._audit_log_rows, insert_store=self.inserted)
        return _FakeTable([])


# ---------------------------------------------------------------------------
# Shared env patch helpers
# ---------------------------------------------------------------------------

_BASE_ENV = {
    "RESEND_API_KEY": "test-resend-key",
    "ALERT_EMAIL_TO": "alert@example.com",
    "RESEND_FROM_EMAIL": "noreply@example.com",
    "ALERT_ERROR_THRESHOLD_COUNT": "3",
    "ALERT_ERROR_THRESHOLD_WINDOW_MINUTES": "15",
    "ALERT_COST_THRESHOLD_DAILY": "5.00",
}


def _ok_http_mock():
    """Return a context-manager mock for httpx.Client whose post() returns 200."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client.post.return_value = mock_resp
    return mock_client


# ---------------------------------------------------------------------------
# Error-rate alert tests
# ---------------------------------------------------------------------------

class ErrorRateAlertTests(unittest.TestCase):

    def test_fires_when_threshold_crossed(self):
        from services.alerting import check_and_alert_error_rate

        db = _FakeSupabase(
            ai_usage_rows=[{"id": f"e{i}", "success": False} for i in range(3)],
        )
        mock_client = _ok_http_mock()

        with patch.dict(os.environ, _BASE_ENV):
            with patch("services.alerting.httpx.Client", return_value=mock_client):
                check_and_alert_error_rate(db)

        mock_client.post.assert_called_once()
        call_kwargs = mock_client.post.call_args
        subject = call_kwargs[1]["json"]["subject"]
        self.assertIn("3 failures", subject)

    def test_does_not_fire_below_threshold(self):
        from services.alerting import check_and_alert_error_rate

        db = _FakeSupabase(
            ai_usage_rows=[{"id": "e1", "success": False}, {"id": "e2", "success": False}],
        )
        mock_client = _ok_http_mock()

        with patch.dict(os.environ, _BASE_ENV):
            with patch("services.alerting.httpx.Client", return_value=mock_client):
                check_and_alert_error_rate(db)

        mock_client.post.assert_not_called()

    def test_cooldown_prevents_second_alert(self):
        from services.alerting import check_and_alert_error_rate

        db = _FakeSupabase(
            ai_usage_rows=[{"id": f"e{i}", "success": False} for i in range(5)],
            audit_log_rows=[{"details": {"alert_type": "error_rate"}}],
        )
        mock_client = _ok_http_mock()

        with patch.dict(os.environ, _BASE_ENV):
            with patch("services.alerting.httpx.Client", return_value=mock_client):
                check_and_alert_error_rate(db)

        mock_client.post.assert_not_called()
        # Also confirm no new audit_log row was written (no alert recorded)
        self.assertEqual(db.inserted, [])

    def test_cooldown_does_not_block_different_alert_type(self):
        from services.alerting import check_and_alert_error_rate

        # Cooldown exists for "cost" — should NOT block "error_rate"
        db = _FakeSupabase(
            ai_usage_rows=[{"id": f"e{i}", "success": False} for i in range(3)],
            audit_log_rows=[{"details": {"alert_type": "cost"}}],
        )
        mock_client = _ok_http_mock()

        with patch.dict(os.environ, _BASE_ENV):
            with patch("services.alerting.httpx.Client", return_value=mock_client):
                check_and_alert_error_rate(db)

        mock_client.post.assert_called_once()

    def test_httpx_failure_does_not_propagate(self):
        from services.alerting import check_and_alert_error_rate

        db = _FakeSupabase(
            ai_usage_rows=[{"id": f"e{i}", "success": False} for i in range(5)],
        )
        mock_client = _ok_http_mock()
        mock_client.post.side_effect = RuntimeError("network error")

        with patch.dict(os.environ, _BASE_ENV):
            with patch("services.alerting.httpx.Client", return_value=mock_client):
                # Must not raise
                check_and_alert_error_rate(db)

    def test_records_alert_sent_in_audit_log(self):
        from services.alerting import check_and_alert_error_rate

        db = _FakeSupabase(
            ai_usage_rows=[{"id": f"e{i}", "success": False} for i in range(3)],
        )
        mock_client = _ok_http_mock()

        with patch.dict(os.environ, _BASE_ENV):
            with patch("services.alerting.httpx.Client", return_value=mock_client):
                check_and_alert_error_rate(db)

        self.assertEqual(len(db.inserted), 1)
        row = db.inserted[0]
        self.assertEqual(row["action"], "alert_sent")
        self.assertEqual(row["details"]["alert_type"], "error_rate")
        self.assertEqual(row["details"]["failure_count"], 3)


# ---------------------------------------------------------------------------
# Cost alert tests
# ---------------------------------------------------------------------------

class CostAlertTests(unittest.TestCase):

    def test_fires_when_daily_cost_exceeded(self):
        from services.alerting import check_and_alert_cost

        db = _FakeSupabase(
            ai_usage_rows=[{"estimated_cost": 3.00}, {"estimated_cost": 2.50}],  # 5.50 > 5.00
        )
        mock_client = _ok_http_mock()

        with patch.dict(os.environ, _BASE_ENV):
            with patch("services.alerting.httpx.Client", return_value=mock_client):
                check_and_alert_cost(db)

        mock_client.post.assert_called_once()
        subject = mock_client.post.call_args[1]["json"]["subject"]
        self.assertIn("5.5000", subject)
        self.assertIn("5.00", subject)

    def test_does_not_fire_below_threshold(self):
        from services.alerting import check_and_alert_cost

        db = _FakeSupabase(
            ai_usage_rows=[{"estimated_cost": 2.00}, {"estimated_cost": 1.50}],  # 3.50 < 5.00
        )
        mock_client = _ok_http_mock()

        with patch.dict(os.environ, _BASE_ENV):
            with patch("services.alerting.httpx.Client", return_value=mock_client):
                check_and_alert_cost(db)

        mock_client.post.assert_not_called()

    def test_cooldown_prevents_repeat_cost_alert(self):
        from services.alerting import check_and_alert_cost

        db = _FakeSupabase(
            ai_usage_rows=[{"estimated_cost": 10.0}],
            audit_log_rows=[{"details": {"alert_type": "cost"}}],
        )
        mock_client = _ok_http_mock()

        with patch.dict(os.environ, _BASE_ENV):
            with patch("services.alerting.httpx.Client", return_value=mock_client):
                check_and_alert_cost(db)

        mock_client.post.assert_not_called()

    def test_records_alert_sent_in_audit_log(self):
        from services.alerting import check_and_alert_cost

        db = _FakeSupabase(
            ai_usage_rows=[{"estimated_cost": 6.00}],
        )
        mock_client = _ok_http_mock()

        with patch.dict(os.environ, _BASE_ENV):
            with patch("services.alerting.httpx.Client", return_value=mock_client):
                check_and_alert_cost(db)

        self.assertEqual(len(db.inserted), 1)
        row = db.inserted[0]
        self.assertEqual(row["action"], "alert_sent")
        self.assertEqual(row["details"]["alert_type"], "cost")
        self.assertAlmostEqual(row["details"]["daily_cost"], 6.0, places=3)

    def test_no_alert_when_env_vars_missing(self):
        from services.alerting import check_and_alert_cost

        db = _FakeSupabase(ai_usage_rows=[{"estimated_cost": 99.0}])
        mock_client = _ok_http_mock()

        env_without_keys = {k: v for k, v in _BASE_ENV.items() if k not in ("RESEND_API_KEY", "ALERT_EMAIL_TO")}
        with patch.dict(os.environ, env_without_keys, clear=False):
            # Temporarily unset the keys
            with patch.dict(os.environ, {"RESEND_API_KEY": "", "ALERT_EMAIL_TO": ""}):
                with patch("services.alerting.httpx.Client", return_value=mock_client):
                    check_and_alert_cost(db)

        mock_client.post.assert_not_called()


# ---------------------------------------------------------------------------
# Integration: alerting failure must not break persist_usage_event
# ---------------------------------------------------------------------------

class PersistUsageEventAlertIntegrationTests(unittest.TestCase):
    """Confirm that a crash inside alert checks never propagates out of persist_usage_event."""

    def _ok_supabase(self):
        class _OkTable:
            def insert(self, *a, **kw): return self
            def execute(self): return SimpleNamespace(data=[{}], count=1)

        class _OkSupabase:
            def table(self, name): return _OkTable()

        return _OkSupabase()

    def _sample_event(self):
        return {
            "provider": "anthropic",
            "model": "claude-sonnet-4-6",
            "request_type": "germany_diagnostic",
            "diagnostic_id": "diag-test",
            "student_id": "s-test",
            "input_tokens": 100,
            "output_tokens": 50,
            "total_tokens": 150,
            "estimated_cost": 0.001,
            "latency_ms": 500,
            "success": True,
            "error_type": None,
        }

    def test_persist_returns_true_when_error_rate_check_raises(self):
        from services.ai_observability import persist_usage_event

        with patch("services.ai_observability.check_and_alert_error_rate", side_effect=RuntimeError("alert boom")):
            with patch("services.ai_observability.check_and_alert_cost"):
                result = persist_usage_event(self._ok_supabase(), self._sample_event())

        self.assertTrue(result)

    def test_persist_returns_true_when_cost_check_raises(self):
        from services.ai_observability import persist_usage_event

        with patch("services.ai_observability.check_and_alert_error_rate"):
            with patch("services.ai_observability.check_and_alert_cost", side_effect=RuntimeError("cost boom")):
                result = persist_usage_event(self._ok_supabase(), self._sample_event())

        self.assertTrue(result)

    def test_persist_does_not_call_alerts_when_primary_insert_fails(self):
        """Alert checks must not run if the insert itself failed."""
        from services.ai_observability import persist_usage_event

        class _FailTable:
            def insert(self, *a, **kw): return self
            def execute(self): raise RuntimeError("DB down")

        class _FailPrimarySupabase:
            def __init__(self): self.audit_inserts = []
            def table(self, name):
                if name == "ai_usage_events":
                    return _FailTable()
                # audit_log succeeds (fallback path)
                class _OkTable:
                    def __init__(s): s.store = self.audit_inserts
                    def insert(s, row, **kw): s.store.append(row); return s
                    def execute(s): return SimpleNamespace(data=[{}], count=1)
                return _OkTable()

        db = _FailPrimarySupabase()
        with patch("services.ai_observability.check_and_alert_error_rate") as mock_err:
            with patch("services.ai_observability.check_and_alert_cost") as mock_cost:
                result = persist_usage_event(db, self._sample_event())

        # Returns True via fallback
        self.assertTrue(result)
        mock_err.assert_not_called()
        mock_cost.assert_not_called()


if __name__ == "__main__":
    unittest.main()
