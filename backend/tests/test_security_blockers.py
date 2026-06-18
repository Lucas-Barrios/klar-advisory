import os
import unittest
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


if __name__ == "__main__":
    unittest.main()
