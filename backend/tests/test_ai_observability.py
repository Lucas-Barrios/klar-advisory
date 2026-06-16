from datetime import datetime, timezone
import unittest

from services.ai_observability import (
    aggregate_monthly_usage,
    build_usage_event,
    calculate_estimated_cost,
    persist_usage_event,
)


class FakeTelemetryResult:
    data = []
    count = 0


class FakeTelemetryTable:
    def __init__(self, client, table_name):
        self.client = client
        self.table_name = table_name
        self.payload = None

    def insert(self, payload):
        self.payload = payload
        return self

    def execute(self):
        if self.table_name == "ai_usage_events":
            raise RuntimeError("primary database unavailable")
        if self.table_name == "audit_log" and self.client.fail_audit:
            raise RuntimeError("audit database unavailable")
        self.client.inserts.setdefault(self.table_name, []).append(self.payload)
        return FakeTelemetryResult()


class FakeTelemetrySupabase:
    def __init__(self, *, fail_audit=False):
        self.fail_audit = fail_audit
        self.inserts = {}

    def table(self, table_name):
        return FakeTelemetryTable(self, table_name)


class AIObservabilityTests(unittest.TestCase):
    def test_calculate_estimated_cost_for_sonnet(self):
        cost = calculate_estimated_cost(
            model="claude-sonnet-4-6",
            input_tokens=1000,
            output_tokens=500,
        )

        self.assertEqual(cost, 0.0105)

    def test_build_usage_event_excludes_prompt_fields(self):
        event = build_usage_event(
            provider="anthropic",
            model="claude-sonnet-4-6",
            request_type="germany_diagnostic",
            diagnostic_id="diagnostic-1",
            student_id="student-1",
            input_tokens=100,
            output_tokens=20,
            latency_ms=250,
            success=True,
        )

        self.assertEqual(event["total_tokens"], 120)
        self.assertNotIn("prompt", event)
        self.assertNotIn("email", event)
        self.assertNotIn("name", event)

    def test_aggregate_monthly_usage_and_forecast(self):
        now = datetime(2026, 6, 16, 12, 0, tzinfo=timezone.utc)
        events = [
            {
                "created_at": "2026-06-01T00:00:00+00:00",
                "provider": "anthropic",
                "model": "claude-sonnet-4-6",
                "diagnostic_id": "diagnostic-1",
                "input_tokens": 1000,
                "output_tokens": 500,
                "total_tokens": 1500,
                "estimated_cost": 0.0105,
                "latency_ms": 1000,
                "success": True,
            },
            {
                "created_at": "2026-06-02T00:00:00+00:00",
                "provider": "anthropic",
                "model": "claude-sonnet-4-6",
                "diagnostic_id": None,
                "input_tokens": 800,
                "output_tokens": 0,
                "total_tokens": 800,
                "estimated_cost": 0.0024,
                "latency_ms": 500,
                "success": False,
            },
            {
                "created_at": "2026-05-31T23:59:59+00:00",
                "provider": "anthropic",
                "model": "claude-sonnet-4-6",
                "diagnostic_id": "old",
                "input_tokens": 10_000,
                "output_tokens": 10_000,
                "total_tokens": 20_000,
                "estimated_cost": 1.0,
                "latency_ms": 500,
                "success": True,
            },
        ]

        summary = aggregate_monthly_usage(events, now=now)

        self.assertEqual(summary["current_month_ai_calls"], 2)
        self.assertEqual(summary["successful_calls"], 1)
        self.assertEqual(summary["failed_calls"], 1)
        self.assertEqual(summary["input_tokens"], 1800)
        self.assertEqual(summary["output_tokens"], 500)
        self.assertEqual(summary["total_tokens"], 2300)
        self.assertEqual(summary["estimated_cost"], 0.0129)
        self.assertEqual(summary["average_cost_per_diagnostic"], 0.0129)
        self.assertEqual(summary["average_latency_ms"], 750)
        self.assertEqual(summary["model_breakdown"][0]["calls"], 2)
        self.assertGreater(summary["forecasted_month_end_cost"], summary["estimated_cost"])

    def test_persist_usage_event_logs_primary_failure_and_uses_audit_fallback(self):
        supabase = FakeTelemetrySupabase()

        with self.assertLogs("services.ai_observability", level="WARNING") as logs:
            ok = persist_usage_event(
                supabase,
                {
                    "provider": "anthropic",
                    "model": "claude-sonnet-4-6",
                    "request_type": "germany_diagnostic",
                    "diagnostic_id": "diagnostic-1",
                    "student_id": "student-1",
                    "input_tokens": 10,
                    "output_tokens": 5,
                    "success": True,
                    "email": "student@example.com",
                    "prompt": "raw prompt",
                },
            )

        self.assertTrue(ok)
        self.assertIn("ai_usage_events persistence failed", "\n".join(logs.output))
        audit_payload = supabase.inserts["audit_log"][0]["details"]["telemetry"]
        self.assertNotIn("email", audit_payload)
        self.assertNotIn("prompt", audit_payload)
        self.assertNotIn("student@example.com", "\n".join(logs.output))
        self.assertNotIn("raw prompt", "\n".join(logs.output))

    def test_persist_usage_event_logs_fallback_failure_without_pii(self):
        supabase = FakeTelemetrySupabase(fail_audit=True)

        with self.assertLogs("services.ai_observability", level="WARNING") as logs:
            ok = persist_usage_event(
                supabase,
                {
                    "provider": "anthropic",
                    "model": "claude-sonnet-4-6",
                    "request_type": "germany_diagnostic",
                    "diagnostic_id": "diagnostic-1",
                    "student_id": "student-1",
                    "input_tokens": 10,
                    "output_tokens": 5,
                    "success": False,
                    "error_type": "TimeoutError",
                    "student_email": "student@example.com",
                },
            )

        self.assertFalse(ok)
        output = "\n".join(logs.output)
        self.assertIn("ai_usage_events audit_log fallback failed", output)
        self.assertNotIn("student@example.com", output)


if __name__ == "__main__":
    unittest.main()
