import asyncio
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import BackgroundTasks, HTTPException
from pydantic import ValidationError
from starlette.requests import Request as StarletteRequest

from agents.germany_diagnostic import DiagnosticAIError, run_diagnostic
from models.schemas import ReviewAction, StudentProfileInput
from routers import diagnostic as diagnostic_router
from services.ai_observability import build_usage_event
from services.progress_auth import verify_progress_token


def _make_test_request(ip: str = "test-direct-call") -> StarletteRequest:
    """Minimal starlette Request for tests that call create_diagnostic directly.

    slowapi requires the first parameter to be a real starlette.requests.Request
    (it checks isinstance). The scope only needs the fields slowapi accesses:
    type, client (for IP key), and app (for app.state.limiter).
    """
    from main import app as klar_app
    return StarletteRequest({
        "type": "http",
        "method": "POST",
        "path": "/api/diagnostic/",
        "query_string": b"",
        "headers": [],
        "client": (ip, 50000),
        "app": klar_app,
    })


def sample_student() -> dict:
    return {
        "name": "Test Student",
        "email": "student@example.com",
        "country": "Colombia",
        "pathway": "university",
        "german_level": "A2",
        "education_level": "Bachelor",
        "work_experience_years": 2,
        "timeline": "1_year",
        "consent_given": True,
        "consent_timestamp": "2026-06-18T12:00:00+00:00",
    }


def sample_diagnostic_output() -> dict:
    return {
        "overall_score": 70,
        "language_score": 35,
        "education_score": 80,
        "pathway_fit_score": 75,
        "timeline_score": 65,
        "financial_score": 70,
        "documentation_score": 60,
        "summary": "A concise summary.",
        "roadmap": [{"month": 1, "title": "Start", "description": "Begin", "action_items": []}],
        "recommendations": [{"name": "DAAD", "type": "organization", "description": "Useful", "url": None}],
        "raw_output": "{}",
        "_ai_usage": build_usage_event(
            provider="anthropic",
            model="claude-sonnet-4-6",
            request_type="germany_diagnostic",
            diagnostic_id=None,
            student_id=None,
            input_tokens=1200,
            output_tokens=300,
            latency_ms=1500,
            success=True,
        ),
    }


class FakeTable:
    def __init__(self, supabase, table_name):
        self.supabase = supabase
        self.table_name = table_name
        self.operation = None
        self.payload = None
        self.filters = []

    def insert(self, payload):
        self.operation = "insert"
        self.payload = payload
        return self

    def select(self, *args, **kwargs):
        self.operation = "select"
        return self

    def update(self, payload):
        self.operation = "update"
        self.payload = payload
        return self

    def eq(self, column, value):
        self.filters.append((column, value))
        return self

    def gte(self, column, value):
        self.filters.append((column, value))
        return self

    def lt(self, column, value):
        self.filters.append((column, value))
        return self

    def single(self):
        return self

    def order(self, *args, **kwargs):
        return self

    def execute(self):
        if self.operation == "insert":
            row = dict(self.payload)
            if self.table_name == "students":
                row.setdefault("id", "student-1")
            if self.table_name == "diagnostics":
                row.setdefault("id", "diagnostic-1")
            self.supabase.inserts.setdefault(self.table_name, []).append(row)
            return SimpleNamespace(data=[row], count=None)

        if self.operation == "select" and self.table_name == "diagnostics":
            return SimpleNamespace(data=self.supabase.diagnostic_result, count=None)

        if self.operation == "update":
            self.supabase.updates.setdefault(self.table_name, []).append(dict(self.payload))
            return SimpleNamespace(data=[dict(self.payload)], count=None)

        return SimpleNamespace(data=[], count=0)


class FakeSupabase:
    def __init__(self):
        self.inserts = {}
        self.updates = {}
        self.diagnostic_result = None

    def table(self, table_name):
        return FakeTable(self, table_name)


class FakeMessages:
    def __init__(self):
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        payload = {
            "overall_score": 70,
            "language_score": 35,
            "education_score": 80,
            "pathway_fit_score": 75,
            "timeline_score": 65,
            "financial_score": 70,
            "documentation_score": 60,
            "summary": "A concise summary.",
            "roadmap": [],
            "recommendations": [],
        }
        return SimpleNamespace(
            content=[SimpleNamespace(text=json.dumps(payload))],
            usage=SimpleNamespace(input_tokens=1200, output_tokens=300),
        )


class FakeAnthropicClient:
    def __init__(self):
        self.messages = FakeMessages()


class DiagnosticObservabilityTests(unittest.TestCase):
    def test_run_diagnostic_uses_timeout_output_cap_and_usage_metadata(self):
        fake_client = FakeAnthropicClient()

        result = run_diagnostic(
            sample_student(),
            anthropic_client=fake_client,
            max_output_tokens=999,
            timeout_seconds=7,
        )

        call = fake_client.messages.calls[0]
        self.assertEqual(call["max_tokens"], 999)
        self.assertEqual(call["timeout"], 7)
        self.assertEqual(result["_ai_usage"]["input_tokens"], 1200)
        self.assertEqual(result["_ai_usage"]["output_tokens"], 300)
        self.assertTrue(result["_ai_usage"]["success"])
        self.assertNotIn("prompt", result["_ai_usage"])

    def test_run_diagnostic_rejects_overlong_input_without_api_call(self):
        fake_client = FakeAnthropicClient()

        with self.assertRaises(DiagnosticAIError) as ctx:
            run_diagnostic(
                sample_student(),
                anthropic_client=fake_client,
                max_input_chars=10,
            )

        self.assertEqual(len(fake_client.messages.calls), 0)
        self.assertEqual(ctx.exception.error_type, "InputTooLong")
        self.assertFalse(ctx.exception.usage_event["success"])

    def test_successful_diagnostic_logs_ai_usage_event(self):
        fake_supabase = FakeSupabase()
        student = StudentProfileInput(**sample_student())

        with patch.object(diagnostic_router, "get_supabase", return_value=fake_supabase):
            with patch.object(
                diagnostic_router,
                "run_diagnostic",
                return_value=sample_diagnostic_output(),
            ):
                response = asyncio.run(
                    diagnostic_router.create_diagnostic(
                        _make_test_request("obs-success"), student, BackgroundTasks()
                    )
                )

        self.assertEqual(response.diagnostic_id, "diagnostic-1")
        self.assertTrue(response.progress_token)
        diagnostic_insert = fake_supabase.inserts["diagnostics"][0]
        self.assertIn("progress_token_hash", diagnostic_insert)
        self.assertNotEqual(diagnostic_insert["progress_token_hash"], response.progress_token)
        self.assertTrue(
            verify_progress_token(
                response.progress_token,
                diagnostic_insert["progress_token_hash"],
            )
        )
        usage = fake_supabase.inserts["ai_usage_events"][0]
        self.assertEqual(usage["diagnostic_id"], "diagnostic-1")
        self.assertEqual(usage["student_id"], "student-1")
        self.assertTrue(usage["success"])
        self.assertNotIn("student_email", usage)
        self.assertNotIn("prompt", usage)

        audit = fake_supabase.inserts["audit_log"][0]
        self.assertEqual(audit["action"], "diagnostic_created")
        self.assertNotIn("student_email", audit["details"])

    def test_failed_diagnostic_logs_ai_usage_event(self):
        fake_supabase = FakeSupabase()
        student = StudentProfileInput(**sample_student())
        usage_event = build_usage_event(
            provider="anthropic",
            model="claude-sonnet-4-6",
            request_type="germany_diagnostic",
            diagnostic_id=None,
            student_id=None,
            input_tokens=800,
            output_tokens=0,
            latency_ms=250,
            success=False,
            error_type="TimeoutError",
        )

        with patch.object(diagnostic_router, "get_supabase", return_value=fake_supabase):
            with patch.object(
                diagnostic_router,
                "run_diagnostic",
                side_effect=DiagnosticAIError(
                    "failed",
                    usage_event=usage_event,
                    error_type="TimeoutError",
                ),
            ):
                with self.assertRaises(HTTPException) as ctx:
                    asyncio.run(
                        diagnostic_router.create_diagnostic(
                            _make_test_request("obs-failure"), student, BackgroundTasks()
                        )
                    )

        self.assertEqual(ctx.exception.status_code, 502)
        usage = fake_supabase.inserts["ai_usage_events"][0]
        self.assertIsNone(usage["diagnostic_id"])
        self.assertEqual(usage["student_id"], "student-1")
        self.assertFalse(usage["success"])
        self.assertEqual(usage["error_type"], "TimeoutError")
        self.assertNotIn("email", usage)
        self.assertNotIn("prompt", usage)
        self.assertNotIn("diagnostics", fake_supabase.inserts)

    def test_pydantic_validation_for_enums(self):
        invalid_student = sample_student()
        invalid_student["pathway"] = "tourist"
        with self.assertRaises(ValidationError):
            StudentProfileInput(**invalid_student)

        invalid_level = sample_student()
        invalid_level["german_level"] = "B3"
        with self.assertRaises(ValidationError):
            StudentProfileInput(**invalid_level)

        with self.assertRaises(ValidationError):
            ReviewAction(status="pending")

    def test_rejected_diagnostic_public_result_hides_report(self):
        payload = diagnostic_router.public_diagnostic_result(
            {
                "id": "diagnostic-1",
                "status": "rejected",
                "overall_score": 95,
                "summary": "Do not expose this.",
                "roadmap": [{"month": 1}],
                "recommendations": [{"name": "Secret"}],
                "students": {"name": "Test Student"},
            }
        )

        self.assertEqual(payload["status"], "not_available")
        self.assertNotIn("summary", payload)
        self.assertNotIn("roadmap", payload)
        self.assertNotIn("recommendations", payload)
        self.assertNotIn("student", payload)


if __name__ == "__main__":
    unittest.main()
