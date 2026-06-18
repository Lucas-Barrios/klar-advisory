import os
import unittest
import unittest.mock
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import BackgroundTasks, HTTPException
from fastapi.testclient import TestClient

from main import app
from models.schemas import ReviewAction
from routers import admin as admin_router
from routers import diagnostic as diagnostic_router
from services.progress_auth import generate_progress_token, hash_progress_token


class FakeQuery:
    def __init__(self, client, table_name):
        self.client = client
        self.table_name = table_name
        self.action = "select"
        self.payload = None

    def select(self, *args, **kwargs):
        self.action = "select"
        return self

    def insert(self, payload):
        self.action = "insert"
        self.payload = payload
        return self

    def update(self, payload):
        self.action = "update"
        self.payload = payload
        return self

    def eq(self, *args, **kwargs):
        return self

    def gte(self, *args, **kwargs):
        return self

    def lt(self, *args, **kwargs):
        return self

    def order(self, *args, **kwargs):
        return self

    def single(self):
        return self

    def execute(self):
        if self.action == "insert":
            self.client.inserts.setdefault(self.table_name, []).append(self.payload)
            return SimpleNamespace(data=[self.payload], count=1)

        if self.action == "update":
            self.client.updates.setdefault(self.table_name, []).append(self.payload)
            return SimpleNamespace(data=[self.payload], count=1)

        if self.table_name == "diagnostics":
            if self.client.diagnostic:
                return SimpleNamespace(data=self.client.diagnostic, count=1)
            return SimpleNamespace(data=[], count=self.client.count)

        return SimpleNamespace(data=[], count=self.client.count)


class FakeSupabase:
    def __init__(self):
        self.count = 2
        self.diagnostic = {}
        self.inserts = {}
        self.updates = {}

    def table(self, table_name):
        return FakeQuery(self, table_name)


class SecurityBlockerTests(unittest.TestCase):
    def setUp(self):
        self.env_patch = patch.dict(os.environ, {"ADMIN_API_TOKEN": "admin-token"})
        self.env_patch.start()
        self.client = TestClient(app)

    def tearDown(self):
        self.env_patch.stop()

    def test_diagnostic_submission_rejected_without_consent(self):
        """Server must return 422 when consent_given is absent or false."""
        base_payload = {
            "name": "Test Student",
            "email": "test@example.com",
            "country": "Brazil",
            "pathway": "ausbildung",
            "german_level": "B1",
            "education_level": "bachelor",
            "work_experience_years": 2,
            "timeline": "1_year",
            "financial_situation": "I have some savings but need funded options",
        }

        # Omitting consent_given entirely (defaults to false)
        response = self.client.post("/api/diagnostic/", json=base_payload)
        self.assertEqual(response.status_code, 422, "Missing consent_given must yield 422")

        # Explicitly false
        response = self.client.post(
            "/api/diagnostic/",
            json={**base_payload, "consent_given": False},
        )
        self.assertEqual(response.status_code, 422, "consent_given=False must yield 422")

    def test_admin_routes_reject_missing_and_invalid_authorization(self):
        protected_requests = [
            ("GET", "/api/admin/diagnostics", None),
            ("GET", "/api/admin/stats", None),
            ("GET", "/api/admin/tco", None),
            ("GET", "/api/admin/evaluation/summary", None),
            ("GET", "/api/admin/evaluation/experiments", None),
            (
                "POST",
                "/api/admin/diagnostics/diagnostic-1/review",
                {"status": "approved"},
            ),
        ]

        for method, path, body in protected_requests:
            response = self.client.request(method, path, json=body)
            self.assertEqual(response.status_code, 401, path)

            response = self.client.request(
                method,
                path,
                json=body,
                headers={"Authorization": "Bearer wrong-token"},
            )
            self.assertEqual(response.status_code, 403, path)

    def test_admin_route_accepts_valid_authorization(self):
        fake_supabase = FakeSupabase()
        with patch.object(admin_router, "get_supabase", return_value=fake_supabase):
            response = self.client.get(
                "/api/admin/stats",
                headers={"Authorization": "Bearer admin-token"},
            )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["pending"], 2)
        self.assertEqual(body["approved_today"], 2)
        self.assertEqual(body["total"], 2)
        self.assertIn("approved_count", body)
        self.assertIn("booked_count", body)
        self.assertIn("conversion_rate", body)

    def test_review_audit_details_redact_reviewer_notes(self):
        fake_supabase = FakeSupabase()
        fake_supabase.diagnostic = {
            "id": "diagnostic-1",
            "students": {
                "name": "Maria Garcia",
                "full_name": "Maria Garcia",
                "email": "maria@example.com",
            },
        }
        action = ReviewAction(
            status="approved",
            reviewer_notes=(
                "Maria Garcia emailed maria@example.com and called +49 151 2345 6789. "
                "Timeline is realistic."
            ),
        )

        with patch.object(admin_router, "get_supabase", return_value=fake_supabase):
            result = admin_router.review_diagnostic(
                "diagnostic-1", action, BackgroundTasks()
            )

        self.assertEqual(result["status"], "ok")
        audit_details = fake_supabase.inserts["audit_log"][0]["details"]
        self.assertIn("Timeline is realistic", audit_details["notes"])
        self.assertNotIn("Maria Garcia", audit_details["notes"])
        self.assertNotIn("maria@example.com", audit_details["notes"])
        self.assertNotIn("+49 151 2345 6789", audit_details["notes"])
        self.assertIn("[redacted-name]", audit_details["notes"])
        self.assertIn("[redacted-email]", audit_details["notes"])
        self.assertIn("[redacted-phone]", audit_details["notes"])

    def test_progress_update_requires_valid_token(self):
        token = generate_progress_token()
        fake_supabase = FakeSupabase()
        fake_supabase.diagnostic = {
            "id": "diagnostic-1",
            "progress_token_hash": hash_progress_token(token),
        }
        update = diagnostic_router.ProgressUpdate(completed_steps=[2, 1, 1])

        with patch.object(diagnostic_router, "get_supabase", return_value=fake_supabase):
            with self.assertRaises(HTTPException) as missing:
                diagnostic_router.update_progress(
                    "diagnostic-1",
                    update,
                    authorization=None,
                )
            self.assertEqual(missing.exception.status_code, 401)

            with self.assertRaises(HTTPException) as invalid:
                diagnostic_router.update_progress(
                    "diagnostic-1",
                    update,
                    authorization="Bearer wrong-token",
                )
            self.assertEqual(invalid.exception.status_code, 403)

            result = diagnostic_router.update_progress(
                "diagnostic-1",
                update,
                authorization=f"Bearer {token}",
            )

        self.assertEqual(result, {"status": "ok", "completed_steps": [1, 2]})
        self.assertEqual(fake_supabase.updates["diagnostics"][0]["completed_steps"], [1, 2])

    def test_public_result_uses_name_and_full_name_compatibility(self):
        with_name = diagnostic_router.public_diagnostic_result(
            {
                "id": "diagnostic-1",
                "status": "approved",
                "students": {"name": "Canonical Name"},
            }
        )
        with_full_name = diagnostic_router.public_diagnostic_result(
            {
                "id": "diagnostic-2",
                "status": "approved",
                "students": {"full_name": "Legacy Name"},
            }
        )

        self.assertEqual(with_name["students"]["name"], "Canonical Name")
        self.assertEqual(with_full_name["students"]["name"], "Legacy Name")


class NextStepMessageSafetyTests(unittest.TestCase):
    """next_step_message must not contain manipulative urgency / dark-pattern copy."""

    def setUp(self):
        from agents.germany_diagnostic import (
            NEXT_STEP_MESSAGE_URGENCY_BLOCKLIST,
            check_next_step_message_safety,
        )
        self.check = check_next_step_message_safety
        self.blocklist = NEXT_STEP_MESSAGE_URGENCY_BLOCKLIST

    def test_clean_warm_message_passes(self):
        """Calibrated urgency from the SYSTEM_PROMPT (acting now, competitive spots) is allowed."""
        msg = (
            "Hi Maria, given how competitive spots are and how close you already are "
            "to being ready, acting now makes a real difference. Book a free consultation "
            "and let's build your personalised roadmap together."
        )
        self.assertEqual(self.check(msg), [])

    def test_last_chance_is_blocked(self):
        self.assertIn("last chance", self.check("This is your last chance to secure a spot."))

    def test_spots_are_filling_is_blocked(self):
        self.assertIn(
            "spots are filling",
            self.check("Spots are filling fast — register today!"),
        )

    def test_limited_spots_remaining_is_blocked(self):
        self.assertIn(
            "limited spots remaining",
            self.check("There are limited spots remaining for this intake."),
        )

    def test_dont_wait_any_longer_is_blocked(self):
        self.assertIn(
            "don't wait any longer",
            self.check("Don't wait any longer — reach out now."),
        )

    def test_act_immediately_is_blocked(self):
        self.assertIn("act immediately", self.check("You must act immediately to secure your place."))

    def test_check_is_case_insensitive(self):
        self.assertIn("last chance", self.check("LAST CHANCE to book your consultation!"))

    def test_none_message_returns_empty(self):
        self.assertEqual(self.check(None), [])

    def test_empty_message_returns_empty(self):
        self.assertEqual(self.check(""), [])

    def test_multiple_violations_all_returned(self):
        msg = "Last chance! Spots are filling fast. Don't wait any longer."
        violations = self.check(msg)
        self.assertGreaterEqual(len(violations), 2)

    def test_blocklist_is_nonempty(self):
        self.assertGreater(len(self.blocklist), 0)


class AdminAuthAuditLoggingTests(unittest.TestCase):
    """Failed admin auth must produce an audit_log row that never contains
    the supplied token value — only failure_type, client IP, and timestamp.

    Covers the two failure branches:
      - missing token  → HTTP 401
      - invalid token  → HTTP 403
    """

    def setUp(self):
        self.env_patch = patch.dict(os.environ, {"ADMIN_API_TOKEN": "correct-admin-token"})
        self.env_patch.start()
        self.client = TestClient(app)

    def tearDown(self):
        self.env_patch.stop()

    def _make_supabase_with_audit_capture(self):
        """Return a (fake_supabase, captured_inserts) pair.

        Uses FakeSupabase from the test module so inserts are recorded in
        fake_supabase.inserts['audit_log'].
        """
        fake = FakeSupabase()
        return fake

    def test_missing_token_logs_audit_row(self):
        """No Authorization header → 401 and one audit_log row with failure_type='missing'."""
        import services.admin_auth as admin_auth_module

        fake_supa = self._make_supabase_with_audit_capture()
        with patch.object(admin_auth_module, "get_supabase", return_value=fake_supa):
            response = self.client.get("/api/admin/diagnostics")

        self.assertEqual(response.status_code, 401)
        rows = fake_supa.inserts.get("audit_log", [])
        self.assertGreaterEqual(len(rows), 1, "Expected at least one audit_log insert")
        auth_rows = [r for r in rows if r.get("action") == "admin_auth_failure"]
        self.assertEqual(len(auth_rows), 1, "Expected exactly one admin_auth_failure row")
        self.assertEqual(auth_rows[0]["details"]["failure_type"], "missing")

    def test_invalid_token_logs_audit_row(self):
        """Wrong token → 403 and one audit_log row with failure_type='invalid'."""
        import services.admin_auth as admin_auth_module

        supplied_token = "definitely-wrong-token-xyz"
        fake_supa = self._make_supabase_with_audit_capture()
        with patch.object(admin_auth_module, "get_supabase", return_value=fake_supa):
            response = self.client.get(
                "/api/admin/diagnostics",
                headers={"Authorization": f"Bearer {supplied_token}"},
            )

        self.assertEqual(response.status_code, 403)
        rows = fake_supa.inserts.get("audit_log", [])
        auth_rows = [r for r in rows if r.get("action") == "admin_auth_failure"]
        self.assertEqual(len(auth_rows), 1)
        self.assertEqual(auth_rows[0]["details"]["failure_type"], "invalid")

        # Critical: the supplied token must never appear in the logged row
        serialized_row = str(auth_rows[0])
        self.assertNotIn(
            supplied_token,
            serialized_row,
            "The supplied token value must not be persisted in the audit_log row",
        )

    def test_valid_token_produces_no_failure_audit_row(self):
        """Correct token must not produce any admin_auth_failure audit rows."""
        import services.admin_auth as admin_auth_module

        fake_supa = FakeSupabase()
        with (
            patch.object(admin_auth_module, "get_supabase", return_value=fake_supa),
            patch.object(admin_router, "get_supabase", return_value=fake_supa),
        ):
            response = self.client.get(
                "/api/admin/stats",
                headers={"Authorization": "Bearer correct-admin-token"},
            )

        self.assertEqual(response.status_code, 200)
        auth_rows = [
            r for r in fake_supa.inserts.get("audit_log", [])
            if r.get("action") == "admin_auth_failure"
        ]
        self.assertEqual(len(auth_rows), 0, "Successful auth must not produce failure audit rows")


class DiagnosticRateLimitTests(unittest.TestCase):
    """POST /api/diagnostic/ must enforce 5 requests/hour per IP.
    The 6th request within the window must be rejected with 429 and a
    human-readable message — not a raw library error."""

    _VALID_PAYLOAD = {
        "name": "Rate Limit Test",
        "email": "ratelimit@example.com",
        "country": "Brazil",
        "pathway": "ausbildung",
        "german_level": "B1",
        "education_level": "bachelor",
        "work_experience_years": 2,
        "timeline": "1_year",
        "financial_situation": "Some savings",
        "consent_given": True,
    }

    _MOCK_DIAGNOSTIC_OUTPUT = {
        "overall_score": 52,
        "language_score": 35,
        "education_score": 65,
        "pathway_fit_score": 55,
        "timeline_score": 60,
        "financial_score": 50,
        "documentation_score": 55,
        "summary": "Rate limit test diagnostic.",
        "next_step_message": "Hi Rate Limit Test, book a consultation.",
        "roadmap": [{"month": 1, "title": "Start", "description": "Begin", "action_items": []}],
        "recommendations": [],
        "_ai_usage": None,
    }

    def setUp(self):
        from services.rate_limiter import limiter
        limiter._storage.reset()
        self.client = TestClient(app)

    def _make_supabase_mock(self):
        mock_supa = unittest.mock.MagicMock()
        mock_supa.table.return_value.insert.return_value.execute.return_value = (
            SimpleNamespace(data=[{"id": "test-uuid-001"}])
        )
        mock_supa.table.return_value.update.return_value.execute.return_value = (
            SimpleNamespace(data=[])
        )
        return mock_supa

    def test_first_five_requests_succeed_sixth_is_rejected(self):
        """First 5 requests must not be rate-limited; the 6th must return 429."""
        supabase_mock = self._make_supabase_mock()

        with (
            patch.object(diagnostic_router, "get_supabase", return_value=supabase_mock),
            patch.object(diagnostic_router, "run_diagnostic", return_value=self._MOCK_DIAGNOSTIC_OUTPUT),
            patch.object(diagnostic_router, "notify_n8n"),
            patch.object(diagnostic_router, "run_ausbildung_matching"),
        ):
            for i in range(5):
                resp = self.client.post("/api/diagnostic/", json=self._VALID_PAYLOAD)
                self.assertNotEqual(resp.status_code, 429, f"Request {i+1} should not be rate-limited")

            resp = self.client.post("/api/diagnostic/", json=self._VALID_PAYLOAD)
            self.assertEqual(resp.status_code, 429, "6th request must be rate-limited")
            body = resp.json()
            self.assertIn("detail", body)
            self.assertIn("too many", body["detail"].lower(), "429 response must include a human-readable message")


class CrossResourceAuthorizationTests(unittest.TestCase):
    """Progress token for diagnostic A must be rejected (403) when presented
    against diagnostic B's /progress endpoint.

    This closes the gap flagged in the prior audit: the cross-resource
    isolation is enforced in code but was never asserted in a test.
    """

    def setUp(self):
        self.env_patch = patch.dict(os.environ, {"ADMIN_API_TOKEN": "admin-token"})
        self.env_patch.start()

    def tearDown(self):
        self.env_patch.stop()

    def test_token_a_rejected_for_diagnostic_b(self):
        """Token issued to diagnostic A must yield 403 against diagnostic B."""
        token_a = generate_progress_token()
        token_b = generate_progress_token()

        fake_supabase_b = FakeSupabase()
        fake_supabase_b.diagnostic = {
            "id": "diagnostic-b",
            "progress_token_hash": hash_progress_token(token_b),
        }

        update = diagnostic_router.ProgressUpdate(completed_steps=[1])

        with patch.object(diagnostic_router, "get_supabase", return_value=fake_supabase_b):
            # Token A must be rejected (403) when targeting diagnostic B
            with self.assertRaises(HTTPException) as ctx:
                diagnostic_router.update_progress(
                    "diagnostic-b",
                    update,
                    authorization=f"Bearer {token_a}",
                )
            self.assertEqual(ctx.exception.status_code, 403, "Wrong token must yield 403, not 200")

            # Token B must succeed for diagnostic B (baseline sanity check)
            result = diagnostic_router.update_progress(
                "diagnostic-b",
                update,
                authorization=f"Bearer {token_b}",
            )
            self.assertEqual(result["status"], "ok")


class DiagnosticSerializationTests(unittest.TestCase):
    """Regression: student_data inserted into Supabase must be JSON-serializable.

    The live 500 was caused by model_dump() returning a datetime object for
    consent_timestamp, which Supabase's JSON serialization rejected. The fix
    (model_dump(mode='json')) converts it to an ISO-8601 string. This suite
    catches that class of bug by round-tripping every insert payload through
    json.dumps() before reporting success.
    """

    _BASE_PAYLOAD = {
        "name": "Ana Souza",
        "email": "ana@example.com",
        "country": "Brazil",
        "pathway": "ausbildung",
        "german_level": "B1",
        "education_level": "bachelor",
        "work_experience_years": 3,
        "timeline": "1_year",
        "financial_situation": "I have some savings",
        "consent_given": True,
    }

    _MOCK_DIAGNOSTIC_OUTPUT = {
        "overall_score": 60,
        "language_score": 55,
        "education_score": 65,
        "pathway_fit_score": 60,
        "timeline_score": 65,
        "financial_score": 55,
        "documentation_score": 60,
        "summary": "Good candidate.",
        "next_step_message": "Hi Ana, book a consultation.",
        "roadmap": [{"month": 1, "title": "Start", "description": "Begin", "action_items": []}],
        "recommendations": [],
        "_ai_usage": None,
    }

    def _make_serialization_checking_supabase(self):
        """Return a fake Supabase that raises TypeError on any non-JSON-serializable insert."""
        import json as _json

        outer = self

        class _StrictQuery:
            def __init__(self, client, table_name):
                self._client = client
                self._table_name = table_name
                self._action = "select"
                self._payload = None

            def select(self, *args, **kwargs):
                return self

            def insert(self, payload):
                self._action = "insert"
                self._payload = payload
                return self

            def update(self, payload):
                self._action = "update"
                self._payload = payload
                return self

            def eq(self, *args, **kwargs):
                return self

            def single(self):
                return self

            def execute(self):
                if self._action == "insert" and self._payload is not None:
                    # Raises TypeError if any value is not JSON-serializable (e.g. a raw datetime).
                    # This is what Supabase's HTTP layer does; the test replicates it locally.
                    _json.dumps(self._payload)
                    self._client.inserts.setdefault(self._table_name, []).append(self._payload)
                if self._action == "update":
                    return SimpleNamespace(data=[self._payload], count=1)
                return SimpleNamespace(data=[{"id": "test-id"}], count=1)

        class _StrictSupabase:
            def __init__(self):
                self.inserts = {}

            def table(self, name):
                return _StrictQuery(self, name)

        return _StrictSupabase()

    def setUp(self):
        from services.rate_limiter import limiter
        limiter._storage.reset()
        self.client = TestClient(app)

    def test_auto_generated_timestamp_is_json_serializable(self):
        """When consent_timestamp is omitted, the router fills it in.
        model_dump(mode='json') must convert the resulting datetime to a string
        before the payload reaches Supabase — otherwise json.dumps raises TypeError.
        """
        fake_supa = self._make_serialization_checking_supabase()
        with (
            patch.object(diagnostic_router, "get_supabase", return_value=fake_supa),
            patch.object(diagnostic_router, "run_diagnostic", return_value=self._MOCK_DIAGNOSTIC_OUTPUT),
            patch.object(diagnostic_router, "notify_n8n"),
            patch.object(diagnostic_router, "run_ausbildung_matching"),
        ):
            resp = self.client.post("/api/diagnostic/", json=self._BASE_PAYLOAD)

        self.assertEqual(resp.status_code, 200, f"Expected 200, got {resp.status_code}: {resp.text}")
        self.assertIn("students", fake_supa.inserts, "Students row must have been inserted")
        student_row = fake_supa.inserts["students"][0]
        self.assertIsInstance(
            student_row.get("consent_timestamp"),
            str,
            "consent_timestamp in the Supabase payload must be a string, not a datetime",
        )

    def test_explicit_timestamp_string_is_json_serializable(self):
        """An explicit ISO timestamp supplied by the client also survives json.dumps()."""
        payload = {**self._BASE_PAYLOAD, "consent_timestamp": "2026-06-01T12:00:00Z"}
        fake_supa = self._make_serialization_checking_supabase()
        with (
            patch.object(diagnostic_router, "get_supabase", return_value=fake_supa),
            patch.object(diagnostic_router, "run_diagnostic", return_value=self._MOCK_DIAGNOSTIC_OUTPUT),
            patch.object(diagnostic_router, "notify_n8n"),
            patch.object(diagnostic_router, "run_ausbildung_matching"),
        ):
            resp = self.client.post("/api/diagnostic/", json=payload)

        self.assertEqual(resp.status_code, 200, f"Expected 200, got {resp.status_code}: {resp.text}")

    def test_bare_datetime_is_not_json_serializable(self):
        """Document why mode='json' matters: a raw datetime object fails json.dumps().
        This is not a router test — it confirms the failure mode we are guarding against.
        """
        import json as _json
        from datetime import datetime, timezone

        dt = datetime.now(timezone.utc)
        with self.assertRaises(TypeError):
            _json.dumps({"consent_timestamp": dt})


if __name__ == "__main__":
    unittest.main()
