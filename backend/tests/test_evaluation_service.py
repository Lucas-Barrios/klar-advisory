import unittest

from services.evaluation import (
    build_example_from_reviewed_diagnostic,
    calculate_summary_metrics,
    compare_prediction,
    redact_direct_identifiers,
    sanitize_evaluation_payload,
)


class EvaluationServiceTests(unittest.TestCase):
    def test_sanitize_evaluation_payload_removes_direct_pii(self):
        payload = sanitize_evaluation_payload(
            {
                "name": "Real Student",
                "email": "student@example.com",
                "country": "Colombia",
                "pathway": "university",
                "german_level": "B1",
                "timeline": "1_year",
                "additional_info": "My phone is 123",
            }
        )

        self.assertEqual(payload["name"], "Evaluation Candidate")
        self.assertEqual(payload["country"], "Colombia")
        self.assertEqual(payload["pathway"], "university")
        self.assertNotIn("email", payload)
        self.assertNotIn("additional_info", payload)

    def test_redact_direct_identifiers_removes_email_phone_and_name_like_content(self):
        redacted = redact_direct_identifiers(
            "Maria Garcia emailed maria@example.com and called +49 151 2345 6789.",
            identifiers=["Maria Garcia"],
        )

        self.assertNotIn("Maria Garcia", redacted)
        self.assertNotIn("maria@example.com", redacted)
        self.assertNotIn("+49 151 2345 6789", redacted)
        self.assertIn("[redacted-name]", redacted)
        self.assertIn("[redacted-email]", redacted)
        self.assertIn("[redacted-phone]", redacted)

    def test_compare_prediction_scores_fields_and_flag_recall(self):
        example = {
            "expected_pathway": "university",
            "expected_german_level": "B2",
            "expected_timeline": "1_year",
            "expected_flags": ["language_gap", "finance_ready"],
        }
        prediction = {
            "predicted_pathway": "university",
            "predicted_german_level": "B1",
            "predicted_timeline": "1_year",
            "predicted_flags": ["language_gap"],
        }

        comparison = compare_prediction(example, prediction)

        self.assertEqual(comparison["field_scores"]["pathway"], 1.0)
        self.assertEqual(comparison["field_scores"]["german_level"], 0.0)
        self.assertEqual(comparison["field_scores"]["timeline"], 1.0)
        self.assertEqual(comparison["flag_recall"], 0.5)
        self.assertEqual(comparison["score"], 0.625)
        self.assertFalse(comparison["passed"])

    def test_calculate_summary_metrics(self):
        metrics = calculate_summary_metrics(
            [
                {
                    "expected_pathway": "university",
                    "predicted_pathway": "university",
                    "expected_german_level": "B2",
                    "predicted_german_level": "B2",
                    "expected_timeline": "1_year",
                    "predicted_timeline": "1_year",
                    "expected_flags": ["language_gap"],
                    "predicted_flags": ["language_gap"],
                    "score": 1,
                    "passed": True,
                    "latency_ms": 1000,
                    "estimated_cost": 0.01,
                },
                {
                    "expected_pathway": "ausbildung",
                    "predicted_pathway": "university",
                    "expected_german_level": "B1",
                    "predicted_german_level": "A2",
                    "expected_timeline": "6_months",
                    "predicted_timeline": "6_months",
                    "expected_flags": ["timeline_risk", "language_gap"],
                    "predicted_flags": ["timeline_risk"],
                    "score": 0.625,
                    "passed": False,
                    "latency_ms": 2000,
                    "estimated_cost": 0.03,
                },
            ]
        )

        self.assertEqual(metrics["evaluated_examples"], 2)
        self.assertEqual(metrics["pathway_accuracy"], 0.5)
        self.assertEqual(metrics["german_level_accuracy"], 0.5)
        self.assertEqual(metrics["timeline_accuracy"], 1.0)
        self.assertEqual(metrics["flag_recall"], 0.75)
        self.assertEqual(metrics["overall_pass_rate"], 0.5)
        self.assertEqual(metrics["average_score"], 0.8125)
        self.assertEqual(metrics["average_latency_ms"], 1500)
        self.assertEqual(metrics["average_cost_per_evaluated_example"], 0.02)

    def test_build_example_from_reviewed_diagnostic(self):
        example = build_example_from_reviewed_diagnostic(
            {
                "id": "diagnostic-1",
                "status": "rejected",
                "reviewer_decision": "rejected",
                "reviewer_notes": "Real Student timeline is too aggressive. Email student@example.com.",
                "students": {
                    "name": "Real Student",
                    "email": "student@example.com",
                    "country": "Mexico",
                    "pathway": "work_visa",
                    "german_level": "A2",
                    "timeline": "6_months",
                    "education_level": "Bachelor",
                    "work_experience_years": 4,
                },
            },
            dataset_id="dataset-1",
        )

        self.assertEqual(example["dataset_id"], "dataset-1")
        self.assertEqual(example["expected_pathway"], "work_visa")
        self.assertEqual(example["expected_german_level"], "A2")
        self.assertEqual(example["expected_timeline"], "6_months")
        self.assertIn("human_rejected", example["expected_flags"])
        self.assertEqual(example["input_payload"]["name"], "Evaluation Candidate")
        self.assertNotIn("email", example["input_payload"])
        self.assertNotIn("Real Student", example["expected_summary_notes"])
        self.assertNotIn("student@example.com", example["expected_summary_notes"])

    def test_unreviewed_diagnostic_cannot_become_example(self):
        with self.assertRaises(ValueError):
            build_example_from_reviewed_diagnostic(
                {"id": "diagnostic-1", "status": "pending", "students": {}},
                dataset_id="dataset-1",
            )


if __name__ == "__main__":
    unittest.main()
