"""
ITEM 5a: Refusal behavior — DiagnosticAIError surfaces as HTTP 502.

Tests the full chain:
  parse_diagnostic_response(refusal_text)
    → DiagnosticAIError(error_type="JSONDecodeError")
      → router catches DiagnosticAIError
        → HTTP 502, not 500 or an unhandled crash

The router must NOT return 500 for a DiagnosticAIError. That would mean the
except-chain fell through to the generic handler, which means the typed error
isn't being caught — a silent protocol breach.
"""
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient


def _make_refusal_client(text: str):
    """Return a FakeAnthropicClient whose single response is `text`."""
    class FakeMessages:
        def create(self, **kwargs):
            return SimpleNamespace(
                content=[SimpleNamespace(text=text)],
                usage=SimpleNamespace(input_tokens=500, output_tokens=10),
            )

    class FakeAnthropicClient:
        messages = FakeMessages()

    return FakeAnthropicClient()


def _make_supabase_stub(student_id="fake-student-id"):
    """Minimal Supabase stub that satisfies the router's inserts."""
    class FakeQuery:
        def __init__(self):
            self._val = None

        def insert(self, val):
            self._val = val
            return self

        def update(self, val):
            return self

        def select(self, *a, **kw):
            return self

        def eq(self, *a, **kw):
            return self

        def single(self):
            return self

        def execute(self):
            return SimpleNamespace(data=[{"id": student_id}], count=1)

    class FakeSupabase:
        def table(self, _name):
            return FakeQuery()

    return FakeSupabase()


VALID_PAYLOAD = {
    "name": "Refusal Test",
    "email": "refusal@example.com",
    "country": "Brazil",
    "pathway": "ausbildung",
    "german_level": "B1",
    "education_level": "bachelor",
    "work_experience_years": 2,
    "timeline": "1_year",
    "consent_given": True,
    "consent_timestamp": "2026-06-18T12:00:00+00:00",
}


class RefusalBehaviorHTTPTests(unittest.TestCase):
    """
    Router must map DiagnosticAIError → 502.
    Not 500. Not an unhandled exception that leaks a traceback.
    """

    def _post_with_fake_ai(self, ai_text: str):
        from main import app

        fake_client = _make_refusal_client(ai_text)
        fake_db = _make_supabase_stub()

        with (
            patch("routers.diagnostic.get_supabase", return_value=fake_db),
            patch(
                "agents.germany_diagnostic.get_anthropic_client",
                return_value=fake_client,
            ),
        ):
            client = TestClient(app, raise_server_exceptions=False)
            return client.post("/api/diagnostic/", json=VALID_PAYLOAD)

    def test_plain_text_refusal_returns_502(self):
        """A plain-English refusal from the AI must produce HTTP 502, not 500."""
        response = self._post_with_fake_ai(
            "I'm sorry, I cannot assist with that request."
        )
        self.assertEqual(
            response.status_code,
            502,
            f"Expected 502 for AI refusal, got {response.status_code}: {response.text}",
        )

    def test_empty_response_returns_502(self):
        """An empty AI response must produce HTTP 502."""
        response = self._post_with_fake_ai("")
        self.assertEqual(response.status_code, 502)

    def test_partial_json_returns_502(self):
        """Truncated JSON (not valid) must produce HTTP 502."""
        response = self._post_with_fake_ai('{"overall_score": 75, "language_score":')
        self.assertEqual(response.status_code, 502)

    def test_valid_ai_response_returns_200(self):
        """Sanity check: a structurally valid AI response must return 200."""
        valid_body = json.dumps({
            "overall_score": 62,
            "language_score": 55,
            "education_score": 65,
            "pathway_fit_score": 60,
            "timeline_score": 60,
            "financial_score": 50,
            "documentation_score": 55,
            "summary": "Good candidate.",
            "next_step_message": "Hi Refusal Test, book a consultation.",
            "roadmap": [{"month": 1, "title": "Start", "description": "Begin German", "action_items": []}],
            "recommendations": [{"name": "DAAD", "type": "organization", "description": "Funding", "url": None}],
        })
        response = self._post_with_fake_ai(valid_body)
        self.assertEqual(
            response.status_code,
            200,
            f"Expected 200 for valid AI response, got {response.status_code}: {response.text}",
        )

    def test_502_detail_is_user_friendly(self):
        """The 502 response body must contain the user-friendly message, not a stack trace."""
        response = self._post_with_fake_ai("Cannot help.")
        self.assertEqual(response.status_code, 502)
        detail = response.json().get("detail", "")
        self.assertNotIn("Traceback", detail)
        self.assertNotIn("DiagnosticAIError", detail)
        self.assertIn("unavailable", detail.lower())


class RefusalBehaviorUnitTests(unittest.TestCase):
    """Unit-level: parse_diagnostic_response() must map refusals to DiagnosticAIError."""

    def test_plain_text_raises_diagnostic_ai_error(self):
        from agents.germany_diagnostic import DiagnosticAIError, parse_diagnostic_response

        fake_response = SimpleNamespace(
            content=[SimpleNamespace(text="I cannot help with that.")],
            usage=SimpleNamespace(input_tokens=100, output_tokens=5),
        )
        with self.assertRaises(DiagnosticAIError) as ctx:
            parse_diagnostic_response(fake_response)
        self.assertEqual(ctx.exception.error_type, "JSONDecodeError")

    def test_schema_violation_raises_diagnostic_ai_error(self):
        from agents.germany_diagnostic import DiagnosticAIError, parse_diagnostic_response

        body = json.dumps({"overall_score": 200, "summary": "Bad", "roadmap": [], "recommendations": []})
        fake_response = SimpleNamespace(
            content=[SimpleNamespace(text=body)],
            usage=SimpleNamespace(input_tokens=100, output_tokens=30),
        )
        with self.assertRaises(DiagnosticAIError) as ctx:
            parse_diagnostic_response(fake_response)
        self.assertEqual(ctx.exception.error_type, "SchemaValidationError")


if __name__ == "__main__":
    unittest.main()
