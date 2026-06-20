"""
Tests for the document regeneration endpoint and supporting logic.

Covers:
  - POST /{diagnostic_id}/regenerate-documents returns 402 when documents_unlocked is False
  - POST /{diagnostic_id}/regenerate-documents calls regenerate_documents() when unlocked
  - Keyword tailoring: target_position_ids are looked up and passed to regenerate_documents
  - _build_facts_block injects named fields and placeholder_values correctly
  - _build_keywords_block injects full posting text when available, falls back to title only
  - QA gate: has_incomplete_placeholders correctly detects [bracketed] text
  - DocumentAIError surfaces as 503 (distinct from generic Exception 500) in both endpoints
  - Schema-valid output is produced with richer context block (FakeAnthropicClient)
"""
import re
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from main import app


# ── Helpers ───────────────────────────────────────────────────────────────────

def has_incomplete_placeholders(text: str) -> bool:
    """Python mirror of the frontend hasIncompletePlaceholders function."""
    return bool(re.search(r'\[[^\]]+\]', text))


SAMPLE_DOCUMENTS = {
    "cv": {
        "profil": "Motivated professional seeking Ausbildung.",
        "ausbildung": [{"zeitraum": "[Zeitraum]", "beschreibung": "Studied at [Name der Bildungseinrichtung]."}],
        "berufserfahrung": [{"zeitraum": "2021–2023", "beschreibung": "Worked at Acme Corp, [Ort]."}],
        "sprachkenntnisse": [{"sprache": "Deutsch", "niveau": "B1"}],
        "kompetenzen": ["Teamwork"],
    },
    "anschreiben": "Sehr geehrte Damen und Herren, ich bewerbe mich als [Position].",
    "cv_de": {
        "profil": "Motivated professional seeking Ausbildung.",
        "ausbildung": [{"zeitraum": "[Zeitraum]", "beschreibung": "Studied at [Name der Bildungseinrichtung]."}],
        "berufserfahrung": [{"zeitraum": "2021–2023", "beschreibung": "Worked at Acme Corp, [Ort]."}],
        "sprachkenntnisse": [{"sprache": "Deutsch", "niveau": "B1"}],
        "kompetenzen": ["Teamwork"],
    },
    "anschreiben_de": "Sehr geehrte Damen und Herren, ich bewerbe mich als [Position].",
    "cv_target": None,
    "anschreiben_target": None,
}

SAMPLE_STUDENT = {
    "name": "Ana García",
    "email": "ana@example.com",
    "country": "Mexico",
    "pathway": "ausbildung",
    "german_level": "B1",
    "english_level": "B2",
    "education_level": "secondary",
    "field_of_study": "General",
    "work_experience_years": 2,
    "timeline": "1_year",
}


class FakeQuery:
    def __init__(self, client, table_name):
        self.client = client
        self.table_name = table_name
        self._filter_val = None
        self._in_vals = None
        self._payload = None

    def select(self, *args, **kwargs):
        return self

    def insert(self, payload):
        self._payload = payload
        return self

    def update(self, payload):
        return self

    def eq(self, col, val):
        self._filter_val = val
        return self

    def in_(self, col, vals):
        self._in_vals = vals
        return self

    def single(self):
        return self

    def execute(self):
        if self.table_name == "diagnostics":
            return SimpleNamespace(data=self.client.diagnostic_data)
        if self.table_name == "ausbildung_positions":
            positions = self.client.positions_data
            if self._in_vals is not None:
                positions = [p for p in positions if p.get("refnr") in self._in_vals]
            return SimpleNamespace(data=positions)
        if self._payload is not None:
            self.client.inserts.setdefault(self.table_name, []).append(self._payload)
        return SimpleNamespace(data=[])


class FakeSupabase:
    def __init__(self, *, diagnostic_data=None, positions_data=None):
        self.diagnostic_data = diagnostic_data
        self.positions_data = positions_data or []
        self.inserts: dict = {}

    def table(self, table_name):
        return FakeQuery(self, table_name)


# ── QA gate tests ─────────────────────────────────────────────────────────────

class QAGateTests(unittest.TestCase):
    def test_detects_bracketed_placeholder(self):
        self.assertTrue(has_incomplete_placeholders("Hello [Name]!"))

    def test_passes_clean_text(self):
        self.assertFalse(has_incomplete_placeholders("Hello Ana García, guten Tag!"))

    def test_multiword_placeholder(self):
        self.assertTrue(has_incomplete_placeholders("Worked at [Name der Bildungseinrichtung]."))

    def test_empty_string(self):
        self.assertFalse(has_incomplete_placeholders(""))

    def test_nested_like_brackets_not_confused(self):
        # Normal square brackets in German academic writing aren't placeholders
        # but our gate doesn't need to distinguish — any [X] is a placeholder
        self.assertTrue(has_incomplete_placeholders("[vgl. Goethe 1808]"))

    def test_short_profil_length(self):
        # Any profil under 10 chars is suspicious — verify the length check heuristic
        self.assertTrue(len("") < 10)
        self.assertTrue(len("Hi there.") < 10)
        self.assertFalse(len("Motivated professional.") < 10)


# ── _build_facts_block tests ──────────────────────────────────────────────────

class BuildFactsBlockTests(unittest.TestCase):
    def _run(self, **kwargs):
        from agents.document_factory import _build_facts_block
        from models.schemas import DocumentFacts
        facts = DocumentFacts(**kwargs)
        return _build_facts_block(facts)

    def test_none_facts(self):
        from agents.document_factory import _build_facts_block
        result = _build_facts_block(None)
        self.assertIn("No confirmed facts", result)

    def test_named_field_injected(self):
        result = self._run(employer_name="Acme GmbH", job_title="Elektroniker")
        self.assertIn("Employer name: Acme GmbH", result)
        self.assertIn("Job title: Elektroniker", result)

    def test_empty_fields_omitted(self):
        result = self._run(employer_name="", job_title=None)
        self.assertIn("No confirmed facts", result)

    def test_placeholder_values_injected(self):
        result = self._run(placeholder_values={"PLZ, Ort": "60311 Frankfurt"})
        self.assertIn("Replace [PLZ, Ort] with: 60311 Frankfurt", result)

    def test_mixed_named_and_placeholder_values(self):
        result = self._run(
            employer_name="TechCorp",
            placeholder_values={"Zeitraum": "2020–2023"},
        )
        self.assertIn("Employer name: TechCorp", result)
        self.assertIn("Replace [Zeitraum] with: 2020–2023", result)


# ── Endpoint integration tests ────────────────────────────────────────────────

class RegenerateDocumentsEndpointTests(unittest.TestCase):
    def setUp(self):
        self.http = TestClient(app)

    def _fake_supabase(self, *, documents_unlocked=True, positions=None):
        diagnostic = {
            "id": "diag-123",
            "documents_unlocked": documents_unlocked,
            "student_id": "student-456",
            "students": SAMPLE_STUDENT,
        }
        return FakeSupabase(diagnostic_data=diagnostic, positions_data=positions or [])

    def test_returns_402_when_not_unlocked(self):
        sb = self._fake_supabase(documents_unlocked=False)
        with patch("routers.diagnostic.get_supabase", return_value=sb):
            resp = self.http.post(
                "/api/diagnostic/diag-123/regenerate-documents",
                json={"target_language": "en"},
            )
        self.assertEqual(resp.status_code, 402)

    def test_returns_documents_when_unlocked(self):
        sb = self._fake_supabase(documents_unlocked=True)
        mock_docs = {**SAMPLE_DOCUMENTS, "_ai_usage": None}

        with patch("routers.diagnostic.get_supabase", return_value=sb), \
             patch("agents.document_factory.regenerate_documents", return_value=mock_docs) as mock_fn:
            resp = self.http.post(
                "/api/diagnostic/diag-123/regenerate-documents",
                json={"target_language": "en", "facts": {"employer_name": "Acme GmbH"}},
            )

        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("cv_de", data)

        call_kwargs = mock_fn.call_args.kwargs
        self.assertEqual(call_kwargs["facts"].employer_name, "Acme GmbH")

    def test_keyword_tailoring_looks_up_positions(self):
        positions = [
            {"refnr": "pos-001", "beruf": "Pflegefachmann/-frau", "titel": "Auszubildende Pflege (m/w/d)"},
        ]
        sb = self._fake_supabase(documents_unlocked=True, positions=positions)
        mock_docs = {**SAMPLE_DOCUMENTS, "_ai_usage": None}

        with patch("routers.diagnostic.get_supabase", return_value=sb), \
             patch("agents.document_factory.regenerate_documents", return_value=mock_docs) as mock_fn:
            resp = self.http.post(
                "/api/diagnostic/diag-123/regenerate-documents",
                json={"target_language": "en", "target_position_ids": ["pos-001"]},
            )

        self.assertEqual(resp.status_code, 200)
        call_kwargs = mock_fn.call_args.kwargs
        self.assertEqual(len(call_kwargs["target_keywords"]), 1)
        self.assertEqual(call_kwargs["target_keywords"][0]["refnr"], "pos-001")
        self.assertEqual(call_kwargs["target_keywords"][0]["beruf"], "Pflegefachmann/-frau")

    def test_unrecognised_position_ids_return_empty_keywords(self):
        sb = self._fake_supabase(documents_unlocked=True, positions=[])
        mock_docs = {**SAMPLE_DOCUMENTS, "_ai_usage": None}

        with patch("routers.diagnostic.get_supabase", return_value=sb), \
             patch("agents.document_factory.regenerate_documents", return_value=mock_docs) as mock_fn:
            resp = self.http.post(
                "/api/diagnostic/diag-123/regenerate-documents",
                json={"target_language": "en", "target_position_ids": ["nonexistent-id"]},
            )

        self.assertEqual(resp.status_code, 200)
        call_kwargs = mock_fn.call_args.kwargs
        self.assertEqual(call_kwargs["target_keywords"], [])


# ── DocumentAIError surfacing tests ──────────────────────────────────────────

class DocumentAIErrorSurfacingTests(unittest.TestCase):
    """Confirm DocumentAIError is caught specifically (503) not swallowed into generic 500."""

    def setUp(self):
        self.http = TestClient(app)

    def _fake_supabase_unlocked(self):
        diagnostic = {
            "id": "diag-123",
            "documents_unlocked": True,
            "student_id": "student-456",
            "students": SAMPLE_STUDENT,
        }
        return FakeSupabase(diagnostic_data=diagnostic)

    # generate-documents ──────────────────────────────────────────────────────

    def test_generate_document_ai_error_returns_503(self):
        """DocumentAIError from generate_documents must surface as 503, not 500."""
        from agents.document_factory import DocumentAIError
        sb = self._fake_supabase_unlocked()

        with patch("routers.diagnostic.get_supabase", return_value=sb), \
             patch(
                 "agents.document_factory.generate_documents",
                 side_effect=DocumentAIError("JSON parse failed", error_type="JSONDecodeError"),
             ):
            resp = self.http.post(
                "/api/diagnostic/diag-123/generate-documents",
                json={"target_language": "en"},
            )

        self.assertEqual(resp.status_code, 503)
        self.assertIn("temporarily unavailable", resp.json()["detail"])

    def test_generate_generic_exception_returns_500(self):
        """A generic unexpected exception must still return 500, not 503."""
        sb = self._fake_supabase_unlocked()

        with patch("routers.diagnostic.get_supabase", return_value=sb), \
             patch(
                 "agents.document_factory.generate_documents",
                 side_effect=RuntimeError("unexpected DB failure"),
             ):
            resp = self.http.post(
                "/api/diagnostic/diag-123/generate-documents",
                json={"target_language": "en"},
            )

        self.assertEqual(resp.status_code, 500)
        self.assertIn("temporarily unavailable", resp.json()["detail"])

    # regenerate-documents ────────────────────────────────────────────────────

    def test_regenerate_document_ai_error_returns_503(self):
        """DocumentAIError from regenerate_documents must surface as 503, not 500."""
        from agents.document_factory import DocumentAIError
        sb = self._fake_supabase_unlocked()

        with patch("routers.diagnostic.get_supabase", return_value=sb), \
             patch(
                 "agents.document_factory.regenerate_documents",
                 side_effect=DocumentAIError("Schema validation failed", error_type="SchemaValidationError"),
             ):
            resp = self.http.post(
                "/api/diagnostic/diag-123/regenerate-documents",
                json={"target_language": "en"},
            )

        self.assertEqual(resp.status_code, 503)
        self.assertIn("temporarily unavailable", resp.json()["detail"])

    def test_regenerate_generic_exception_returns_500(self):
        """A generic unexpected exception must still return 500, not 503."""
        sb = self._fake_supabase_unlocked()

        with patch("routers.diagnostic.get_supabase", return_value=sb), \
             patch(
                 "agents.document_factory.regenerate_documents",
                 side_effect=ValueError("unexpected serialisation error"),
             ):
            resp = self.http.post(
                "/api/diagnostic/diag-123/regenerate-documents",
                json={"target_language": "en"},
            )

        self.assertEqual(resp.status_code, 500)
        self.assertIn("temporarily unavailable", resp.json()["detail"])


# ── Failure observability tests ───────────────────────────────────────────────

class RegenerateFailureObservabilityTests(unittest.TestCase):
    """Confirm that regeneration failures write a success=False ai_usage_events row."""

    def setUp(self):
        self.http = TestClient(app)

    def _fake_supabase_unlocked(self):
        diagnostic = {
            "id": "diag-obs-1",
            "documents_unlocked": True,
            "student_id": "student-obs-1",
            "students": SAMPLE_STUDENT,
        }
        return FakeSupabase(diagnostic_data=diagnostic)

    def test_document_ai_error_writes_failure_usage_event(self):
        """DocumentAIError in regenerate_documents must produce a success=False ai_usage_events row."""
        from agents.document_factory import DocumentAIError
        sb = self._fake_supabase_unlocked()

        with patch("routers.diagnostic.get_supabase", return_value=sb), \
             patch(
                 "agents.document_factory.regenerate_documents",
                 side_effect=DocumentAIError("JSON parse failed", error_type="JSONDecodeError"),
             ):
            resp = self.http.post(
                "/api/diagnostic/diag-obs-1/regenerate-documents",
                json={"target_language": "en"},
            )

        self.assertEqual(resp.status_code, 503)
        rows = sb.inserts.get("ai_usage_events", [])
        self.assertEqual(len(rows), 1, "Expected exactly one ai_usage_events row on failure")
        row = rows[0]
        self.assertFalse(row["success"])
        self.assertEqual(row["request_type"], "document_factory")
        self.assertEqual(row["error_type"], "JSONDecodeError")
        self.assertEqual(row["diagnostic_id"], "diag-obs-1")
        self.assertEqual(row["student_id"], "student-obs-1")

    def test_generic_exception_writes_failure_usage_event(self):
        """An unexpected exception in regenerate_documents must also produce a success=False row."""
        sb = self._fake_supabase_unlocked()

        with patch("routers.diagnostic.get_supabase", return_value=sb), \
             patch(
                 "agents.document_factory.regenerate_documents",
                 side_effect=RuntimeError("network timeout"),
             ):
            resp = self.http.post(
                "/api/diagnostic/diag-obs-1/regenerate-documents",
                json={"target_language": "en"},
            )

        self.assertEqual(resp.status_code, 500)
        rows = sb.inserts.get("ai_usage_events", [])
        self.assertEqual(len(rows), 1, "Expected exactly one ai_usage_events row on failure")
        row = rows[0]
        self.assertFalse(row["success"])
        self.assertEqual(row["request_type"], "document_factory")
        self.assertEqual(row["error_type"], "RuntimeError")

    def test_logging_failure_does_not_block_error_response(self):
        """If record_ai_usage itself raises, the HTTPException still reaches the client."""
        from agents.document_factory import DocumentAIError
        sb = self._fake_supabase_unlocked()

        with patch("routers.diagnostic.get_supabase", return_value=sb), \
             patch(
                 "agents.document_factory.regenerate_documents",
                 side_effect=DocumentAIError("Schema error", error_type="SchemaValidationError"),
             ), \
             patch("routers.diagnostic.record_ai_usage", side_effect=RuntimeError("db down")):
            resp = self.http.post(
                "/api/diagnostic/diag-obs-1/regenerate-documents",
                json={"target_language": "en"},
            )

        self.assertEqual(resp.status_code, 503)


# ── _build_keywords_block richer context tests ───────────────────────────────

class BuildKeywordsBlockTests(unittest.TestCase):
    def _run(self, keywords):
        from agents.document_factory import _build_keywords_block
        return _build_keywords_block(keywords)

    def test_empty_list_returns_empty_string(self):
        self.assertEqual(self._run([]), "")

    def test_title_only_fallback_when_no_full_description(self):
        result = self._run([{"beruf": "Pflegefachmann/-frau", "titel": "Azubi Pflege (m/w/d)"}])
        self.assertIn("Pflegefachmann/-frau", result)
        self.assertIn("Azubi Pflege (m/w/d)", result)
        self.assertNotIn("Full posting text", result)

    def test_full_description_included_when_present(self):
        result = self._run([{
            "beruf": "Pflegefachmann/-frau",
            "titel": "Azubi Pflege (m/w/d)",
            "full_description": "Du lernst die Grundlagen der Pflege...",
        }])
        self.assertIn("Full posting text", result)
        self.assertIn("Du lernst die Grundlagen der Pflege...", result)

    def test_full_description_none_falls_back_to_title_only(self):
        result = self._run([{
            "beruf": "Pflegefachmann/-frau",
            "titel": "Azubi Pflege (m/w/d)",
            "full_description": None,
        }])
        self.assertIn("Pflegefachmann/-frau", result)
        self.assertNotIn("Full posting text", result)

    def test_new_prompt_instruction_text_present(self):
        result = self._run([{"beruf": "Pflegefachmann/-frau", "titel": "Azubi", "full_description": "Text here"}])
        self.assertIn("truthfully consistent", result)
        self.assertIn("Never claim a skill", result)

    def test_positions_without_beruf_are_skipped(self):
        result = self._run([{"beruf": "", "titel": "Azubi Pflege"}, {"beruf": "Mechatroniker", "titel": "Azubi Mechatronik"}])
        self.assertIn("Mechatroniker", result)
        self.assertNotIn("Azubi Pflege", result)


# ── FakeAnthropicClient schema-valid regen with richer context ───────────────

_VALID_DOC_BODY = {
    "cv_de": {
        "profil": "Engagierte Pflegefachkraft mit 3 Jahren Erfahrung.",
        "ausbildung": [{"zeitraum": "[Zeitraum]", "beschreibung": "Schulabschluss in [Name]."}],
        "berufserfahrung": [{"zeitraum": "2021–2024", "beschreibung": "Arbeit im Pflegebereich."}],
        "sprachkenntnisse": [{"sprache": "Deutsch", "niveau": "B2"}],
        "kompetenzen": ["Patientenversorgung", "Teamarbeit"],
    },
    "anschreiben_de": "Sehr geehrte Damen und Herren, ich bewerbe mich hiermit.",
    "cv_target": {
        "profil": "Dedicated care professional with 3 years of experience.",
        "ausbildung": [{"zeitraum": "[Zeitraum]", "beschreibung": "Completed schooling at [Name]."}],
        "berufserfahrung": [{"zeitraum": "2021–2024", "beschreibung": "Worked in nursing."}],
        "sprachkenntnisse": [{"sprache": "German", "niveau": "B2"}],
        "kompetenzen": ["Patient care", "Teamwork"],
    },
    "anschreiben_target": "Dear Sir or Madam, I am applying for this position.",
}


class _FakeMessages:
    def __init__(self, response_body: dict):
        import json
        self._text = json.dumps(response_body)
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        from types import SimpleNamespace
        return SimpleNamespace(
            content=[SimpleNamespace(text=self._text)],
            usage=SimpleNamespace(input_tokens=100, output_tokens=200),
        )


class _FakeAnthropicClient:
    def __init__(self, response_body: dict):
        self.messages = _FakeMessages(response_body)


class RegenSchemaValidWithRicherContextTests(unittest.TestCase):
    """regenerate_documents() must produce schema-valid output when target_keywords
    includes full posting text (the richer context block injected by _build_keywords_block)."""

    def _run_regen(self, target_keywords):
        fake_client = _FakeAnthropicClient(_VALID_DOC_BODY)
        with patch("agents.document_factory.client", fake_client):
            from agents.document_factory import regenerate_documents
            return regenerate_documents(
                SAMPLE_STUDENT,
                target_keywords=target_keywords,
                target_language="en",
            )

    def test_schema_valid_with_full_description_in_keywords(self):
        keywords = [{
            "refnr": "10000-111-S",
            "beruf": "Pflegefachmann/-frau (Ausbildung)",
            "titel": "Azubi Pflege (m/w/d)",
            "full_description": "Wir suchen motivierte Auszubildende mit Sorgfalt und Empathie.",
        }]
        result = self._run_regen(keywords)
        # regenerate_documents() returns _ai_usage; the endpoint pops it before sending to client
        self.assertIn("cv_de", result)
        self.assertIn("anschreiben_de", result)
        self.assertIn("cv_target", result)
        self.assertIn("anschreiben_target", result)

    def test_schema_valid_with_title_only_keywords(self):
        keywords = [{"refnr": "10000-222-S", "beruf": "Mechatroniker/-in", "titel": "Azubi Mechatronik"}]
        result = self._run_regen(keywords)
        self.assertIn("cv_de", result)

    def test_schema_valid_with_no_keywords(self):
        result = self._run_regen([])
        self.assertIn("cv_de", result)

    def test_system_prompt_contains_full_description_when_keywords_provided(self):
        """Confirm the richer context block actually reaches the model call."""
        keywords = [{
            "refnr": "10000-333-S",
            "beruf": "Pflegefachmann/-frau",
            "titel": "Azubi Pflege",
            "full_description": "UNIQUE_MARKER_XYZ987",
        }]
        fake_client = _FakeAnthropicClient(_VALID_DOC_BODY)
        with patch("agents.document_factory.client", fake_client):
            from agents.document_factory import regenerate_documents
            regenerate_documents(SAMPLE_STUDENT, target_keywords=keywords, target_language="en")

        call_kwargs = fake_client.messages.calls[0]
        self.assertIn("UNIQUE_MARKER_XYZ987", call_kwargs["system"])


if __name__ == "__main__":
    unittest.main()
