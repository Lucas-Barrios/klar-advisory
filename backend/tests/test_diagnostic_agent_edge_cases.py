"""
ITEM 4: Edge-case tests for run_diagnostic() called with FakeAnthropicClient.

Tests the REAL agent code path — no function-level mocks. The FakeAnthropicClient
is injected at the SDK level so every line of the agent executes, including:
  - Pydantic input validation (StudentProfileInput)
  - user message construction (build_user_message)
  - json.loads + DiagnosticAIOutput.model_validate (ITEM 3 gate)
  - DiagnosticAIError exception propagation

Edge cases covered:
  - All-whitespace optional fields (stripped by Pydantic to None/empty → agent must handle)
  - Non-Latin script in field_of_study ("医学")
  - Emoji in free-text fields
  - financial_situation at exactly max_length (1000 chars)
  - Deliberately malformed AI response triggers ITEM 3 schema gate
"""
import json
import unittest
from types import SimpleNamespace

from agents.germany_diagnostic import DiagnosticAIError, run_diagnostic


# ---------------------------------------------------------------------------
# Fake Anthropic client
# ---------------------------------------------------------------------------

def _fake_response(body: dict) -> SimpleNamespace:
    return SimpleNamespace(
        content=[SimpleNamespace(text=json.dumps(body))],
        usage=SimpleNamespace(input_tokens=800, output_tokens=300),
    )


def _bad_response(text: str) -> SimpleNamespace:
    return SimpleNamespace(
        content=[SimpleNamespace(text=text)],
        usage=SimpleNamespace(input_tokens=800, output_tokens=20),
    )


def _valid_body(**overrides) -> dict:
    base = {
        "overall_score": 55,
        "language_score": 55,
        "education_score": 65,
        "pathway_fit_score": 60,
        "timeline_score": 60,
        "financial_score": 50,
        "documentation_score": 55,
        "summary": "Decent candidate.",
        "next_step_message": "Book a consultation today.",
        "roadmap": [{"month": 1, "title": "Start German", "description": "Enroll in A1 course", "action_items": ["Sign up"]}],
        "recommendations": [{"name": "Goethe-Institut", "type": "organization", "description": "Language courses", "url": None}],
    }
    base.update(overrides)
    return base


class FakeMessages:
    def __init__(self, body):
        self._body = body

    def create(self, **kwargs):
        if isinstance(self._body, str):
            return _bad_response(self._body)
        return _fake_response(self._body)


class FakeAnthropicClient:
    def __init__(self, body):
        self.messages = FakeMessages(body)


def _base_profile(**overrides) -> dict:
    base = {
        "name": "Edge Test",
        "email": "edge@example.com",
        "country": "Brazil",
        "pathway": "ausbildung",
        "german_level": "B1",
        "education_level": "bachelor",
        "work_experience_years": 2,
        "timeline": "1_year",
        "consent_given": True,
        "consent_timestamp": "2026-06-18T12:00:00+00:00",
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class WhitespaceFieldTests(unittest.TestCase):
    """Optional free-text fields containing only whitespace must not crash the agent."""

    def test_whitespace_field_of_study(self):
        """Whitespace-only field_of_study is stripped by Pydantic to None; agent must not crash."""
        fake = FakeAnthropicClient(_valid_body())
        result = run_diagnostic(
            _base_profile(field_of_study="   "),
            anthropic_client=fake,
        )
        self.assertIsInstance(result["overall_score"], int)

    def test_whitespace_financial_situation(self):
        fake = FakeAnthropicClient(_valid_body())
        result = run_diagnostic(
            _base_profile(financial_situation="   \t  "),
            anthropic_client=fake,
        )
        self.assertIsInstance(result["overall_score"], int)

    def test_whitespace_current_location(self):
        fake = FakeAnthropicClient(_valid_body())
        result = run_diagnostic(
            _base_profile(current_location="   "),
            anthropic_client=fake,
        )
        self.assertIsInstance(result["overall_score"], int)

    def test_whitespace_additional_info(self):
        fake = FakeAnthropicClient(_valid_body())
        result = run_diagnostic(
            _base_profile(additional_info="\n\n"),
            anthropic_client=fake,
        )
        self.assertIsInstance(result["overall_score"], int)


class NonAsciiFieldTests(unittest.TestCase):
    """Non-Latin script and emoji in free-text fields must be accepted and not crash."""

    def test_chinese_field_of_study(self):
        """Chinese characters in field_of_study must not crash the agent."""
        fake = FakeAnthropicClient(_valid_body())
        result = run_diagnostic(
            _base_profile(field_of_study="医学"),
            anthropic_client=fake,
        )
        self.assertIsInstance(result["overall_score"], int)

    def test_arabic_field_of_study(self):
        fake = FakeAnthropicClient(_valid_body())
        result = run_diagnostic(
            _base_profile(field_of_study="الطب"),
            anthropic_client=fake,
        )
        self.assertIsInstance(result["overall_score"], int)

    def test_emoji_in_additional_info(self):
        fake = FakeAnthropicClient(_valid_body())
        result = run_diagnostic(
            _base_profile(additional_info="I love Germany 🇩🇪 and want to study there! 🎓"),
            anthropic_client=fake,
        )
        self.assertIsInstance(result["overall_score"], int)

    def test_emoji_in_financial_situation(self):
        fake = FakeAnthropicClient(_valid_body())
        result = run_diagnostic(
            _base_profile(financial_situation="I have €5,000 saved 💰"),
            anthropic_client=fake,
        )
        self.assertIsInstance(result["overall_score"], int)

    def test_mixed_script_field_of_study(self):
        """Mixed Latin + CJK in field_of_study."""
        fake = FakeAnthropicClient(_valid_body())
        result = run_diagnostic(
            _base_profile(field_of_study="Software Engineering / ソフトウェア"),
            anthropic_client=fake,
        )
        self.assertIsInstance(result["overall_score"], int)


class MaxLengthBoundaryTests(unittest.TestCase):
    """Fields at exactly max_length must be accepted by Pydantic and not crash the agent."""

    def test_financial_situation_at_max_length(self):
        """financial_situation max_length=1000 — exactly 1000 chars must be accepted."""
        payload_1000 = "A" * 1000
        self.assertEqual(len(payload_1000), 1000)
        fake = FakeAnthropicClient(_valid_body())
        result = run_diagnostic(
            _base_profile(financial_situation=payload_1000),
            anthropic_client=fake,
        )
        self.assertIsInstance(result["overall_score"], int)

    def test_additional_info_at_max_length(self):
        """additional_info max_length=1500 — exactly 1500 chars must be accepted."""
        payload_1500 = "B" * 1500
        self.assertEqual(len(payload_1500), 1500)
        fake = FakeAnthropicClient(_valid_body())
        result = run_diagnostic(
            _base_profile(additional_info=payload_1500),
            anthropic_client=fake,
        )
        self.assertIsInstance(result["overall_score"], int)

    def test_field_of_study_at_max_length(self):
        """field_of_study max_length=120 — exactly 120 chars must be accepted."""
        payload_120 = "C" * 120
        fake = FakeAnthropicClient(_valid_body())
        result = run_diagnostic(
            _base_profile(field_of_study=payload_120),
            anthropic_client=fake,
        )
        self.assertIsInstance(result["overall_score"], int)


class MalformedResponseSchemaGateTests(unittest.TestCase):
    """ITEM 3 schema gate: malformed AI responses must raise DiagnosticAIError, not crash silently."""

    def _run(self, body) -> dict:
        if isinstance(body, str):
            fake = FakeAnthropicClient(body)
        else:
            fake = FakeAnthropicClient(body)
        return run_diagnostic(_base_profile(), anthropic_client=fake)

    def test_missing_required_score_key_raises(self):
        """A response missing language_score must fail schema validation."""
        body = {
            "overall_score": 55,
            # missing language_score, education_score, etc.
            "summary": "Missing keys.",
            "roadmap": [],
            "recommendations": [],
        }
        with self.assertRaises(DiagnosticAIError) as ctx:
            self._run(body)
        self.assertEqual(ctx.exception.error_type, "SchemaValidationError")

    def test_wrong_type_on_score_raises(self):
        """A string where an int is expected must fail schema validation."""
        body = _valid_body(overall_score="very high")
        with self.assertRaises(DiagnosticAIError) as ctx:
            self._run(body)
        self.assertEqual(ctx.exception.error_type, "SchemaValidationError")

    def test_out_of_range_score_raises(self):
        """overall_score > 100 must fail ge=0, le=100 validation."""
        body = _valid_body(overall_score=150)
        with self.assertRaises(DiagnosticAIError) as ctx:
            self._run(body)
        self.assertEqual(ctx.exception.error_type, "SchemaValidationError")

    def test_plain_text_refusal_raises(self):
        """A plain-English refusal is not valid JSON — must raise DiagnosticAIError."""
        with self.assertRaises(DiagnosticAIError) as ctx:
            self._run("Sorry, I cannot help with that.")
        self.assertIn(ctx.exception.error_type, {"JSONDecodeError", "SchemaValidationError"})

    def test_empty_string_response_raises(self):
        """An empty response must raise DiagnosticAIError."""
        with self.assertRaises(DiagnosticAIError) as ctx:
            self._run("")
        self.assertIn(ctx.exception.error_type, {"JSONDecodeError", "SchemaValidationError"})

    def test_roadmap_wrong_type_raises(self):
        """roadmap as a string instead of a list must fail validation."""
        body = _valid_body(roadmap="not a list")
        with self.assertRaises(DiagnosticAIError) as ctx:
            self._run(body)
        self.assertEqual(ctx.exception.error_type, "SchemaValidationError")


if __name__ == "__main__":
    unittest.main()
