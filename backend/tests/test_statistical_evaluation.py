import unittest

from services.statistical_evaluation import (
    benjamini_hochberg_correction,
    bonferroni_correction,
    calculate_confidence_interval,
    cohen_d,
    compare_evaluation_runs,
    compare_metric_values,
    detect_benchmark_saturation,
    detect_paired_runs,
    detect_underpowered_comparison,
)


class FakeResult:
    def __init__(self, data=None, count=None):
        self.data = data
        self.count = count if count is not None else len(data or [])


class FakeSupabase:
    def __init__(self, tables):
        self.tables = tables

    def table(self, name):
        return FakeQuery(self, name)


class FakeQuery:
    def __init__(self, client, table_name):
        self.client = client
        self.table_name = table_name
        self.filters = []
        self.order_by = None
        self.order_desc = False
        self.limit_count = None
        self.single_row = False
        self.action = "select"
        self.payload = None

    def select(self, *args, **kwargs):
        return self

    def eq(self, key, value):
        self.filters.append((key, value))
        return self

    def order(self, key, desc=False):
        self.order_by = key
        self.order_desc = desc
        return self

    def limit(self, count):
        self.limit_count = count
        return self

    def single(self):
        self.single_row = True
        return self

    def insert(self, payload):
        self.action = "insert"
        self.payload = payload
        return self

    def update(self, payload):
        self.action = "update"
        self.payload = payload
        return self

    def execute(self):
        table = self.client.tables.setdefault(self.table_name, [])
        if self.action == "insert":
            row = dict(self.payload)
            row.setdefault("id", f"{self.table_name}-{len(table) + 1}")
            table.append(row)
            return FakeResult([row])

        rows = [row for row in table if all(row.get(key) == value for key, value in self.filters)]

        if self.action == "update":
            updated = []
            for row in rows:
                row.update(self.payload)
                updated.append(dict(row))
            return FakeResult(updated)

        selected = [dict(row) for row in rows]
        if self.table_name == "evaluation_results":
            examples = {
                row["id"]: row
                for row in self.client.tables.get("evaluation_examples", [])
            }
            for row in selected:
                row["evaluation_examples"] = examples.get(row.get("example_id"), {})

        if self.order_by:
            selected = sorted(
                selected,
                key=lambda row: row.get(self.order_by) or "",
                reverse=self.order_desc,
            )
        if self.limit_count is not None:
            selected = selected[: self.limit_count]
        if self.single_row:
            return FakeResult(selected[0] if selected else {})
        return FakeResult(selected)


class StatisticalEvaluationTests(unittest.TestCase):
    def test_paired_comparison_detection(self):
        pairing = detect_paired_runs(
            [{"example_id": "a"}, {"example_id": "b"}],
            [{"example_id": "b"}, {"example_id": "c"}],
        )

        self.assertTrue(pairing["is_paired"])
        self.assertEqual(pairing["common_example_ids"], ["b"])
        self.assertEqual(pairing["baseline_only_example_ids"], ["a"])
        self.assertEqual(pairing["challenger_only_example_ids"], ["c"])
        self.assertTrue(pairing["warnings"])

    def test_continuous_metric_comparison(self):
        baseline = [0.70 + (i % 5) * 0.01 for i in range(40)]
        challenger = [value + 0.05 + (i % 3) * 0.002 for i, value in enumerate(baseline)]

        result = compare_metric_values(
            baseline,
            challenger,
            metric_name="score",
            paired=True,
            minimum_practical_effect=0.02,
        )

        self.assertEqual(result["test"], "paired_t_test")
        self.assertEqual(result["sample_size"], 40)
        self.assertGreater(result["challenger_mean"], result["baseline_mean"])
        self.assertTrue(result["statistical_significance"])
        self.assertTrue(result["practical_significance"])

    def test_binary_metric_comparison(self):
        baseline = [1] * 20 + [0] * 20
        challenger = [1] * 30 + [0] * 10

        result = compare_metric_values(
            baseline,
            challenger,
            metric_name="passed",
            comparison_type="binary",
            minimum_practical_effect=0.05,
        )

        self.assertEqual(result["metric_type"], "binary")
        self.assertEqual(result["test"], "fisher_exact")
        self.assertEqual(result["baseline_mean"], 0.5)
        self.assertEqual(result["challenger_mean"], 0.75)
        if result["p_value"] is None:
            self.assertIn("Fisher exact test unavailable", " ".join(result["warnings"]))
        else:
            self.assertGreaterEqual(result["p_value"], 0)
            self.assertLessEqual(result["p_value"], 1)

    def test_confidence_interval_calculation(self):
        low, high = calculate_confidence_interval([1, 2, 3, 4, 5])

        self.assertLess(low, 3)
        self.assertGreater(high, 3)

    def test_cohens_d(self):
        effect = cohen_d([1, 2, 3], [2, 3, 4])

        self.assertAlmostEqual(effect, 1.0)

    def test_bonferroni_correction(self):
        corrected = bonferroni_correction([0.01, 0.04, None], alpha=0.05)

        self.assertEqual(corrected["adjusted_p_values"], [0.02, 0.08, None])
        self.assertEqual(corrected["significant"], [True, False, None])

    def test_benjamini_hochberg_correction(self):
        corrected = benjamini_hochberg_correction([0.01, 0.04, 0.03, None], alpha=0.05)

        self.assertAlmostEqual(corrected["adjusted_p_values"][0], 0.03)
        self.assertAlmostEqual(corrected["adjusted_p_values"][1], 0.04)
        self.assertAlmostEqual(corrected["adjusted_p_values"][2], 0.04)
        self.assertIsNone(corrected["adjusted_p_values"][3])
        self.assertEqual(corrected["significant"], [True, True, True, None])

    def test_underpowered_warning(self):
        self.assertEqual(
            detect_underpowered_comparison(12),
            "N < 30; comparison is underpowered.",
        )

    def test_saturation_warning(self):
        self.assertEqual(
            detect_benchmark_saturation(0.96, 0.97, "passed"),
            "Benchmark appears saturated; both runs are above 95%.",
        )

    def test_inconclusive_recommendation_for_small_sample(self):
        result = compare_metric_values(
            [0.8, 0.82],
            [0.9, 0.91],
            metric_name="score",
            paired=True,
            minimum_practical_effect=0.02,
        )

        self.assertIn("sample size is too small", result["recommendation"])
        self.assertIn("N < 30", " ".join(result["warnings"]))

    def test_statistically_significant_but_practically_negligible_case(self):
        baseline = [0.800 + (i % 5) * 0.0005 for i in range(60)]
        challenger = [
            value + 0.005 + ((i % 3) - 1) * 0.00005
            for i, value in enumerate(baseline)
        ]

        result = compare_metric_values(
            baseline,
            challenger,
            metric_name="score",
            paired=True,
            minimum_practical_effect=0.02,
        )

        self.assertTrue(result["statistical_significance"])
        self.assertFalse(result["practical_significance"])
        self.assertIn("practically negligible", result["recommendation"])
        self.assertIn("practically negligible", " ".join(result["warnings"]))

    def test_practically_meaningful_but_statistically_inconclusive_case(self):
        baseline = [0.0] * 40
        challenger = [0.7 if i < 10 else -0.1 for i in range(40)]

        result = compare_metric_values(
            baseline,
            challenger,
            metric_name="score",
            paired=True,
            minimum_practical_effect=0.05,
        )

        self.assertFalse(result["statistical_significance"])
        self.assertTrue(result["practical_significance"])
        self.assertIn("not statistically significant", result["recommendation"])
        self.assertIn("p-value is not significant", " ".join(result["warnings"]))

    def test_compare_evaluation_runs_with_mocked_supabase(self):
        examples = [
            {
                "id": f"example-{i}",
                "expected_pathway": "university",
                "expected_german_level": "B1",
                "expected_timeline": "1_year",
                "expected_flags": [],
            }
            for i in range(40)
        ]
        baseline_results = []
        challenger_results = []
        for i in range(40):
            baseline_score = 0.62 + (i % 5) * 0.02
            lift = 0.04 + (i % 7) * 0.005
            challenger_score = baseline_score + lift
            baseline_results.append(
                {
                    "id": f"baseline-result-{i}",
                    "run_id": "baseline-run",
                    "example_id": f"example-{i}",
                    "score": baseline_score,
                    "passed": baseline_score >= 0.8,
                    "predicted_pathway": "university",
                    "predicted_german_level": "B1",
                    "predicted_timeline": "1_year",
                    "predicted_flags": [],
                    "latency_ms": 1000,
                    "estimated_cost": 0.01,
                }
            )
            challenger_results.append(
                {
                    "id": f"challenger-result-{i}",
                    "run_id": "challenger-run",
                    "example_id": f"example-{i}",
                    "score": challenger_score,
                    "passed": challenger_score >= 0.8,
                    "predicted_pathway": "university",
                    "predicted_german_level": "B1",
                    "predicted_timeline": "1_year",
                    "predicted_flags": [],
                    "latency_ms": 1300,
                    "estimated_cost": 0.013,
                }
            )

        supabase = FakeSupabase(
            {
                "evaluation_runs": [
                    {
                        "id": "baseline-run",
                        "dataset_id": "dataset-1",
                        "model": "claude-sonnet-4-6",
                    },
                    {
                        "id": "challenger-run",
                        "dataset_id": "dataset-1",
                        "model": "claude-sonnet-4-6",
                    },
                ],
                "evaluation_examples": examples,
                "evaluation_results": [*baseline_results, *challenger_results],
            }
        )

        result = compare_evaluation_runs(
            supabase,
            "baseline-run",
            "challenger-run",
            metric_name="score",
            minimum_practical_effect=0.02,
            persist=False,
        )

        self.assertTrue(result["paired"])
        self.assertEqual(result["sample_size"], 40)
        self.assertGreater(result["challenger_mean"], result["baseline_mean"])
        self.assertTrue(result["statistical_significance"])
        self.assertTrue(result["practical_significance"])
        self.assertIn("challenger_wins", result["recommendation"])
        self.assertIn("materially worse on latency", " ".join(result["warnings"]))
        self.assertIn("materially worse on estimated cost", " ".join(result["warnings"]))


if __name__ == "__main__":
    unittest.main()
