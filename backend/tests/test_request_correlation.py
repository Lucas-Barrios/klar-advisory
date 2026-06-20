"""Tests for request correlation ID infrastructure (Items 1–4).

Covers:
- Middleware assigns X-Request-ID on every response
- Upstream X-Request-ID header is honoured (pass-through)
- request_id is stored in ai_usage_events rows created during the request
- RequestIdFilter injects request_id into log records without modifying call sites
- Background tasks receive the request_id from the originating request
"""
import asyncio
import json
import logging
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from services.ai_observability import build_usage_event
from services.request_id import RequestIdFilter, get_request_id, set_request_id


# ---------------------------------------------------------------------------
# Shared fake Supabase
# ---------------------------------------------------------------------------

class _FakeTable:
    def __init__(self, supabase, table_name):
        self._supabase = supabase
        self._table_name = table_name
        self._op = None
        self._payload = None

    def insert(self, payload):
        self._op = "insert"
        self._payload = payload
        return self

    def select(self, *args, **kwargs):
        self._op = "select"
        return self

    def update(self, payload):
        self._op = "update"
        self._payload = payload
        return self

    def eq(self, *args):
        return self

    def single(self):
        return self

    def order(self, *args, **kwargs):
        return self

    def execute(self):
        if self._op == "insert":
            row = dict(self._payload)
            if self._table_name == "students":
                row.setdefault("id", "student-corr-1")
            if self._table_name == "diagnostics":
                row.setdefault("id", "diag-corr-1")
            self._supabase.inserts.setdefault(self._table_name, []).append(row)
            return SimpleNamespace(data=[row], count=None)
        return SimpleNamespace(data=[], count=0)


class _FakeSupabase:
    def __init__(self):
        self.inserts: dict = {}

    def table(self, name):
        return _FakeTable(self, name)


# ---------------------------------------------------------------------------
# Helper: minimal AI output that build_usage_event populates
# ---------------------------------------------------------------------------

def _ai_output() -> dict:
    return {
        "overall_score": 65,
        "language_score": 30,
        "education_score": 70,
        "pathway_fit_score": 60,
        "timeline_score": 65,
        "financial_score": 70,
        "documentation_score": 55,
        "summary": "Test summary.",
        "roadmap": [],
        "recommendations": [],
        "raw_output": "{}",
        "_ai_usage": build_usage_event(
            provider="anthropic",
            model="claude-sonnet-4-6",
            request_type="germany_diagnostic",
            diagnostic_id=None,
            student_id=None,
            input_tokens=100,
            output_tokens=50,
            latency_ms=200,
            success=True,
        ),
    }


def _student_payload() -> dict:
    return {
        "name": "Correlation Test",
        "email": "corr@example.com",
        "country": "Mexico",
        "pathway": "university",
        "german_level": "B1",
        "education_level": "Bachelor",
        "work_experience_years": 1,
        "timeline": "1_year",
        "consent_given": True,
        "consent_timestamp": "2026-06-20T10:00:00+00:00",
    }


# ---------------------------------------------------------------------------
# Middleware tests (via TestClient — exercises the full ASGI stack)
# ---------------------------------------------------------------------------

class RequestIdMiddlewareTests(unittest.TestCase):
    def setUp(self):
        from main import app
        self.client = TestClient(app, raise_server_exceptions=False)

    def test_health_response_has_x_request_id_header(self):
        resp = self.client.get("/health")
        self.assertIn("x-request-id", resp.headers)
        rid = resp.headers["x-request-id"]
        self.assertTrue(rid, "X-Request-ID must not be empty")

    def test_upstream_x_request_id_is_echoed_back(self):
        fixed_id = "test-upstream-abc123"
        resp = self.client.get("/health", headers={"X-Request-ID": fixed_id})
        self.assertEqual(resp.headers.get("x-request-id"), fixed_id)

    def test_each_request_gets_unique_id_when_none_provided(self):
        r1 = self.client.get("/health")
        r2 = self.client.get("/health")
        self.assertNotEqual(
            r1.headers["x-request-id"],
            r2.headers["x-request-id"],
        )

    def test_create_diagnostic_response_includes_request_id_and_usage_event_matches(self):
        """
        POST /api/diagnostic/ → response X-Request-ID must match the
        request_id stored on the ai_usage_events row created during that
        request.
        """
        from routers import diagnostic as diagnostic_router

        fake_db = _FakeSupabase()
        fixed_rid = "integration-test-rid-999"

        with patch.object(diagnostic_router, "get_supabase", return_value=fake_db):
            # side_effect (not return_value) so _ai_output() — and its
            # build_usage_event() call — runs lazily inside the request handler,
            # after the middleware has set the request_id contextvar.
            with patch.object(
                diagnostic_router, "run_diagnostic", side_effect=lambda *a, **kw: _ai_output()
            ):
                resp = self.client.post(
                    "/api/diagnostic/",
                    json=_student_payload(),
                    headers={"X-Request-ID": fixed_rid},
                )

        # Response must echo back the fixed request ID
        self.assertEqual(resp.headers.get("x-request-id"), fixed_rid)

        # ai_usage_events row must carry the same request_id
        usage_rows = fake_db.inserts.get("ai_usage_events", [])
        self.assertEqual(len(usage_rows), 1, "Expected exactly one ai_usage_events insert")
        self.assertEqual(
            usage_rows[0].get("request_id"),
            fixed_rid,
            "request_id on ai_usage_events must match the response X-Request-ID",
        )


# ---------------------------------------------------------------------------
# RequestIdFilter — log injection without touching call sites
# ---------------------------------------------------------------------------

class RequestIdFilterTests(unittest.TestCase):
    def test_filter_injects_request_id_into_log_record(self):
        set_request_id("filter-test-id")
        try:
            f = RequestIdFilter()
            record = logging.LogRecord(
                name="test", level=logging.INFO,
                pathname="", lineno=0, msg="hello", args=(), exc_info=None,
            )
            f.filter(record)
            self.assertEqual(record.request_id, "filter-test-id")
        finally:
            set_request_id("-")

    def test_filter_substitutes_dash_when_no_request_in_flight(self):
        set_request_id("-")
        f = RequestIdFilter()
        record = logging.LogRecord(
            name="test", level=logging.INFO,
            pathname="", lineno=0, msg="background", args=(), exc_info=None,
        )
        f.filter(record)
        self.assertEqual(record.request_id, "-")

    def test_existing_log_call_site_gets_request_id_without_modification(self):
        """payments.py logs without any request_id kwarg — filter must inject it."""
        set_request_id("payments-test-rid")
        try:
            f = RequestIdFilter()
            # Simulate what a logger.warning("some message") call produces
            record = logging.LogRecord(
                name="routers.payments", level=logging.WARNING,
                pathname="payments.py", lineno=99,
                msg="checkout.session.completed received but payment_status=%s — ignoring",
                args=("unpaid",), exc_info=None,
            )
            f.filter(record)
            self.assertEqual(record.request_id, "payments-test-rid")
        finally:
            set_request_id("-")


# ---------------------------------------------------------------------------
# Background task propagation
# ---------------------------------------------------------------------------

class BackgroundTaskPropagationTests(unittest.TestCase):
    def test_notify_n8n_sets_request_id_before_logging(self):
        from routers.diagnostic import notify_n8n

        captured = {}

        async def run():
            # Simulate: request_id NOT in contextvar (background context)
            set_request_id("-")
            # The explicit request_id arg simulates what create_diagnostic passes
            await notify_n8n(
                "diag-bg-1", "Test", "t@example.com", "university", "bg-task-rid-42"
            )
            captured["rid"] = get_request_id()

        import os
        with patch.dict(os.environ, {"N8N_WEBHOOK_URL": ""}):
            asyncio.run(run())

        self.assertEqual(captured["rid"], "bg-task-rid-42")

    def test_run_ausbildung_matching_sets_request_id(self):
        from routers.diagnostic import run_ausbildung_matching

        captured = {}

        def fake_match(*args, **kwargs):
            captured["rid_during"] = get_request_id()
            return {"matches": [], "overall_summary": ""}

        fake_db = _FakeSupabase()
        # match_positions is imported locally inside run_ausbildung_matching,
        # so we patch it at its source module.
        with patch("routers.diagnostic.get_supabase", return_value=fake_db):
            with patch("agents.ausbildung_matcher.match_positions", fake_match):
                set_request_id("-")
                run_ausbildung_matching(
                    "diag-bg-2", "student-bg-2", {}, "bg-matching-rid-77"
                )

        self.assertEqual(captured.get("rid_during"), "bg-matching-rid-77")


if __name__ == "__main__":
    unittest.main()
