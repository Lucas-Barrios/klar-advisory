"""
Tests for PII trace redaction (LangSmith hide_inputs path).

Covers:
  - redact_trace_inputs() replaces known PII labels with [REDACTED]
  - Structure (role, non-PII fields, model key) is preserved after redaction
  - Original dict is never mutated (operates on a deep copy)
  - Content passed to Anthropic's messages.create() is fully unredacted (critical constraint)
"""
import json
import unittest
from unittest.mock import MagicMock

from services.trace_redaction import redact_trace_inputs


class RedactTraceInputsTests(unittest.TestCase):
    """Unit tests for the redact_trace_inputs function."""

    def _make_inputs(self, user_content: str, system_content: str = "") -> dict:
        messages = []
        if system_content:
            messages.append({"role": "system", "content": system_content})
        messages.append({"role": "user", "content": user_content})
        return {"messages": messages, "model": "claude-3-5-sonnet-20241022", "max_tokens": 4000}

    def test_redacts_student_name(self):
        inputs = self._make_inputs("Name: Ana García\nCountry: Mexico")
        result = redact_trace_inputs(inputs)
        user_content = result["messages"][-1]["content"]
        self.assertIn("[REDACTED]", user_content)
        self.assertNotIn("Ana García", user_content)

    def test_redacts_financial_situation(self):
        inputs = self._make_inputs("Financial Situation: limited savings, partly funded by family")
        result = redact_trace_inputs(inputs)
        user_content = result["messages"][-1]["content"]
        self.assertIn("[REDACTED]", user_content)
        self.assertNotIn("limited savings", user_content)

    def test_redacts_current_location_uppercase(self):
        inputs = self._make_inputs("Current Location: Buenos Aires, Argentina")
        result = redact_trace_inputs(inputs)
        user_content = result["messages"][-1]["content"]
        self.assertIn("[REDACTED]", user_content)
        self.assertNotIn("Buenos Aires", user_content)

    def test_redacts_current_location_lowercase(self):
        # ausbildung_matcher uses "Current location:" (lowercase l)
        inputs = self._make_inputs("Current location: Bogotá, Colombia")
        result = redact_trace_inputs(inputs)
        user_content = result["messages"][-1]["content"]
        self.assertIn("[REDACTED]", user_content)
        self.assertNotIn("Bogotá", user_content)

    def test_redacts_employer_name(self):
        inputs = self._make_inputs("- Employer name: Acme GmbH & Co. KG")
        result = redact_trace_inputs(inputs)
        user_content = result["messages"][-1]["content"]
        self.assertIn("[REDACTED]", user_content)
        self.assertNotIn("Acme GmbH", user_content)

    def test_redacts_street_address(self):
        inputs = self._make_inputs("- Street address: Musterstraße 12, 10115 Berlin")
        result = redact_trace_inputs(inputs)
        user_content = result["messages"][-1]["content"]
        self.assertIn("[REDACTED]", user_content)
        self.assertNotIn("Musterstraße", user_content)

    def test_redacts_phone_number(self):
        inputs = self._make_inputs("- Phone number: +49 30 12345678")
        result = redact_trace_inputs(inputs)
        user_content = result["messages"][-1]["content"]
        self.assertIn("[REDACTED]", user_content)
        self.assertNotIn("+49 30", user_content)

    def test_redacts_full_address(self):
        inputs = self._make_inputs("- Full address: Ana García, Hauptstraße 5, 80331 München")
        result = redact_trace_inputs(inputs)
        user_content = result["messages"][-1]["content"]
        self.assertIn("[REDACTED]", user_content)
        self.assertNotIn("Hauptstraße", user_content)

    def test_preserves_role_and_non_pii_fields(self):
        """role, non-PII content, and top-level keys must survive redaction unchanged."""
        inputs = self._make_inputs(
            user_content="Name: Sofia Ramirez\nPathway: ausbildung\nGerman Level: B1",
            system_content="You are Klar's diagnostic agent.",
        )
        result = redact_trace_inputs(inputs)

        # roles preserved
        self.assertEqual(result["messages"][0]["role"], "system")
        self.assertEqual(result["messages"][1]["role"], "user")
        # system content untouched (no PII labels in system prompt here)
        self.assertIn("diagnostic agent", result["messages"][0]["content"])
        # non-PII lines in user content preserved
        user_content = result["messages"][1]["content"]
        self.assertIn("Pathway: ausbildung", user_content)
        self.assertIn("German Level: B1", user_content)
        # PII line redacted
        self.assertNotIn("Sofia Ramirez", user_content)
        self.assertIn("Name: [REDACTED]", user_content)
        # top-level keys preserved
        self.assertEqual(result["model"], "claude-3-5-sonnet-20241022")
        self.assertEqual(result["max_tokens"], 4000)

    def test_does_not_mutate_original(self):
        inputs = self._make_inputs("Name: Ana García\nFinancial Situation: stable")
        original_content = inputs["messages"][-1]["content"]
        redact_trace_inputs(inputs)
        self.assertEqual(inputs["messages"][-1]["content"], original_content)

    def test_no_messages_key_passes_through(self):
        inputs = {"model": "claude-3-5-sonnet-20241022", "prompt": "Hello"}
        result = redact_trace_inputs(inputs)
        self.assertEqual(result, inputs)

    def test_handles_list_content_blocks(self):
        """Content can be a list of typed blocks (e.g. vision API format)."""
        inputs = {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Name: Carlos Mendez\nFinancial Situation: good"},
                        {"type": "image", "source": "..."},
                    ],
                }
            ]
        }
        result = redact_trace_inputs(inputs)
        text_block = result["messages"][0]["content"][0]
        self.assertNotIn("Carlos Mendez", text_block["text"])
        self.assertIn("[REDACTED]", text_block["text"])
        # Non-text block untouched
        self.assertEqual(result["messages"][0]["content"][1]["source"], "...")

    def test_multiple_pii_fields_in_one_message(self):
        content = (
            "Name: Maria González\n"
            "Country: Colombia\n"
            "Financial Situation: stable savings of 5000 EUR\n"
            "Current Location: Medellín, Colombia\n"
            "Pathway: ausbildung\n"
        )
        inputs = self._make_inputs(content)
        result = redact_trace_inputs(inputs)
        user_content = result["messages"][-1]["content"]

        self.assertNotIn("Maria González", user_content)
        self.assertNotIn("stable savings of 5000 EUR", user_content)
        self.assertNotIn("Medellín, Colombia", user_content)
        # Non-PII preserved
        self.assertIn("Country: Colombia", user_content)
        self.assertIn("Pathway: ausbildung", user_content)


class AnthropicCallUnredactedTests(unittest.TestCase):
    """
    Critical constraint: redact_trace_inputs must never touch what's sent to Anthropic.

    We pass a plain MagicMock as anthropic_client directly to run_diagnostic(),
    bypassing LangSmith entirely.  The mock captures exactly what the agent passes
    to messages.create() — i.e., what would reach Anthropic in production.
    We assert the PII is fully present and [REDACTED] is absent.
    """

    def _valid_diagnostic_response(self) -> str:
        return json.dumps({
            "overall_score": 65,
            "language_score": 55,
            "education_score": 70,
            "pathway_fit_score": 60,
            "timeline_score": 65,
            "financial_score": 50,
            "documentation_score": 60,
            "summary": "Good candidate with room to grow.",
            "next_step_message": "Book a consultation, Maria.",
            "roadmap": [
                {
                    "month": 1,
                    "title": "Start German",
                    "description": "Enroll in a language course.",
                    "action_items": ["Find a Goethe Institut class"],
                }
            ],
            "recommendations": [
                {
                    "name": "Goethe Institut",
                    "type": "organization",
                    "description": "German language courses.",
                    "url": None,
                }
            ],
        })

    def test_run_diagnostic_sends_unredacted_content_to_anthropic(self):
        from agents.germany_diagnostic import run_diagnostic

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=self._valid_diagnostic_response())]
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 50
        mock_client.messages.create.return_value = mock_response

        student_data = {
            "name": "Maria González",
            "country": "Colombia",
            "age": 25,
            "pathway": "ausbildung",
            "german_level": "B1",
            "english_level": "B2",
            "education_level": "secondary",
            "field_of_study": "Healthcare",
            "work_experience_years": 2,
            "timeline": "1_year",
            "financial_situation": "stable savings of 5000 EUR",
            "current_location": "Medellín, Colombia",
        }

        run_diagnostic(student_data, anthropic_client=mock_client)

        self.assertTrue(
            mock_client.messages.create.called,
            "messages.create was never called — the mock did not intercept the call",
        )
        call_kwargs = mock_client.messages.create.call_args.kwargs
        messages = call_kwargs["messages"]
        user_content = messages[0]["content"]

        # PII must be PRESENT (unredacted) in what Anthropic receives
        self.assertIn("Maria González", user_content, "Student name must reach Anthropic unredacted")
        self.assertIn(
            "stable savings of 5000 EUR",
            user_content,
            "Financial situation must reach Anthropic unredacted",
        )
        self.assertIn(
            "Medellín, Colombia",
            user_content,
            "Current location must reach Anthropic unredacted",
        )
        # No redaction marker in the Anthropic call
        self.assertNotIn(
            "[REDACTED]",
            user_content,
            "[REDACTED] must never appear in the content sent to Anthropic",
        )


if __name__ == "__main__":
    unittest.main()
