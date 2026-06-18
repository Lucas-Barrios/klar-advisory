import unittest

from services.evaluation import (
    OVERALL_SCORE_TOLERANCE,
    build_example_from_reviewed_diagnostic,
    calculate_summary_metrics,
    compare_prediction,
    redact_direct_identifiers,
    sanitize_evaluation_payload,
    score_within_tolerance,
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

    # ------------------------------------------------------------------
    # score_within_tolerance tests
    # ------------------------------------------------------------------

    def test_score_within_tolerance_hit(self):
        self.assertEqual(score_within_tolerance(70, 75), 1.0)

    def test_score_within_tolerance_exact_boundary(self):
        self.assertEqual(score_within_tolerance(70, 70 + OVERALL_SCORE_TOLERANCE), 1.0)
        self.assertEqual(score_within_tolerance(70, 70 - OVERALL_SCORE_TOLERANCE), 1.0)

    def test_score_within_tolerance_miss(self):
        self.assertEqual(score_within_tolerance(70, 70 + OVERALL_SCORE_TOLERANCE + 1), 0.0)

    def test_score_within_tolerance_returns_none_when_no_expected(self):
        self.assertIsNone(score_within_tolerance(None, 65))

    def test_score_within_tolerance_returns_zero_when_no_predicted(self):
        self.assertEqual(score_within_tolerance(70, None), 0.0)

    # ------------------------------------------------------------------
    # compare_prediction now includes overall_score field
    # ------------------------------------------------------------------

    def test_compare_prediction_includes_overall_score_within_tolerance(self):
        example = {
            "expected_pathway": "ausbildung",
            "expected_german_level": "B1",
            "expected_timeline": "1_year",
            "expected_flags": [],
            "expected_overall_score": 65,
        }
        prediction = {
            "predicted_pathway": "ausbildung",
            "predicted_german_level": "B1",
            "predicted_timeline": "1_year",
            "predicted_flags": [],
            "predicted_overall_score": 70,
        }
        comparison = compare_prediction(example, prediction)
        self.assertEqual(comparison["field_scores"]["overall_score"], 1.0)

    def test_compare_prediction_overall_score_miss_reduces_score(self):
        example = {
            "expected_pathway": "ausbildung",
            "expected_german_level": "B1",
            "expected_timeline": "1_year",
            "expected_flags": [],
            "expected_overall_score": 65,
        }
        prediction = {
            "predicted_pathway": "ausbildung",
            "predicted_german_level": "B1",
            "predicted_timeline": "1_year",
            "predicted_flags": [],
            "predicted_overall_score": 50,  # 15 pts off — outside ±10 tolerance
        }
        comparison = compare_prediction(example, prediction)
        self.assertEqual(comparison["field_scores"]["overall_score"], 0.0)
        # score should be lower than 1.0 since overall_score miss counts
        self.assertLess(comparison["score"], 1.0)

    def test_compare_prediction_overall_score_absent_does_not_penalize(self):
        """When expected_overall_score is None, that dimension is excluded from scoring."""
        example_with = {
            "expected_pathway": "ausbildung",
            "expected_german_level": "B1",
            "expected_timeline": "1_year",
            "expected_flags": [],
            "expected_overall_score": 65,
        }
        example_without = {
            "expected_pathway": "ausbildung",
            "expected_german_level": "B1",
            "expected_timeline": "1_year",
            "expected_flags": [],
            "expected_overall_score": None,
        }
        prediction = {
            "predicted_pathway": "ausbildung",
            "predicted_german_level": "B1",
            "predicted_timeline": "1_year",
            "predicted_flags": [],
            "predicted_overall_score": 65,
        }
        comparison_with = compare_prediction(example_with, prediction)
        comparison_without = compare_prediction(example_without, prediction)
        # Without expected, score is computed over fewer dims — both should pass
        self.assertIsNone(comparison_without["field_scores"]["overall_score"])
        self.assertTrue(comparison_with["passed"])
        self.assertTrue(comparison_without["passed"])

    # ------------------------------------------------------------------
    # calculate_summary_metrics now includes overall_score_accuracy
    # ------------------------------------------------------------------

    def test_calculate_summary_metrics_includes_overall_score_accuracy(self):
        metrics = calculate_summary_metrics(
            [
                {
                    "expected_pathway": "ausbildung",
                    "predicted_pathway": "ausbildung",
                    "expected_german_level": "B1",
                    "predicted_german_level": "B1",
                    "expected_timeline": "1_year",
                    "predicted_timeline": "1_year",
                    "expected_flags": [],
                    "predicted_flags": [],
                    "expected_overall_score": 65,
                    "predicted_overall_score": 70,  # within ±10 → hit
                    "score": 1.0,
                    "passed": True,
                    "latency_ms": 1000,
                    "estimated_cost": 0.01,
                },
                {
                    "expected_pathway": "ausbildung",
                    "predicted_pathway": "ausbildung",
                    "expected_german_level": "B1",
                    "predicted_german_level": "B1",
                    "expected_timeline": "1_year",
                    "predicted_timeline": "1_year",
                    "expected_flags": [],
                    "predicted_flags": [],
                    "expected_overall_score": 65,
                    "predicted_overall_score": 50,  # 15 pts off → miss
                    "score": 0.8,
                    "passed": True,
                    "latency_ms": 2000,
                    "estimated_cost": 0.01,
                },
                {
                    # No expected_overall_score — should not count toward accuracy
                    "expected_pathway": "university",
                    "predicted_pathway": "university",
                    "expected_german_level": "B2",
                    "predicted_german_level": "B2",
                    "expected_timeline": "1_year",
                    "predicted_timeline": "1_year",
                    "expected_flags": [],
                    "predicted_flags": [],
                    "expected_overall_score": None,
                    "predicted_overall_score": 77,
                    "score": 1.0,
                    "passed": True,
                    "latency_ms": 1500,
                    "estimated_cost": 0.01,
                },
            ]
        )
        self.assertEqual(metrics["overall_score_accuracy"], 0.5)
        self.assertEqual(metrics["overall_score_examples_with_expected"], 2)

    def test_calculate_summary_metrics_overall_score_accuracy_is_none_when_no_expected(self):
        metrics = calculate_summary_metrics(
            [
                {
                    "expected_pathway": "ausbildung",
                    "predicted_pathway": "ausbildung",
                    "expected_german_level": "B1",
                    "predicted_german_level": "B1",
                    "expected_timeline": "1_year",
                    "predicted_timeline": "1_year",
                    "expected_flags": [],
                    "predicted_flags": [],
                    "expected_overall_score": None,
                    "predicted_overall_score": 65,
                    "score": 1.0,
                    "passed": True,
                    "latency_ms": 1000,
                    "estimated_cost": 0.01,
                }
            ]
        )
        self.assertIsNone(metrics["overall_score_accuracy"])
        self.assertEqual(metrics["overall_score_examples_with_expected"], 0)


if __name__ == "__main__":
    unittest.main()
