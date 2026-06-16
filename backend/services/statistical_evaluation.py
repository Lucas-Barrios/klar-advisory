from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any, Iterable, Sequence

try:  # scipy is optional in this project.
    from scipy import stats as scipy_stats  # type: ignore
except Exception:  # pragma: no cover - exercised only when scipy is installed
    scipy_stats = None


MINIMUM_SAMPLE_SIZE = 30
SATURATION_THRESHOLD = 0.95
NEGLIGIBLE_EFFECT_SIZE = 0.1

BINARY_METRICS = {
    "passed",
    "overall_pass_rate",
    "pathway_accuracy",
    "german_level_accuracy",
    "timeline_accuracy",
}

QUALITY_METRICS = {
    "score",
    "average_score",
    "passed",
    "overall_pass_rate",
    "pathway_accuracy",
    "german_level_accuracy",
    "timeline_accuracy",
    "flag_recall",
}

ORDINAL_METRICS = {
    "reviewer_confidence",
}

LOWER_IS_BETTER_METRICS = {
    "latency_ms",
    "average_latency_ms",
    "estimated_cost",
    "average_cost_per_evaluated_example",
}

CONTINUOUS_ALIASES = {
    "average_score": "score",
    "overall_pass_rate": "passed",
    "average_latency_ms": "latency_ms",
    "average_cost_per_evaluated_example": "estimated_cost",
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _first_row(result: Any) -> dict[str, Any]:
    rows = result.data or []
    if isinstance(rows, list):
        return rows[0] if rows else {}
    return rows


def _finite(value: float | None) -> float | None:
    if value is None or not math.isfinite(value):
        return None
    return value


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    return numeric if math.isfinite(numeric) else None


def _clean(values: Iterable[Any]) -> list[float]:
    cleaned = []
    for value in values:
        numeric = _as_float(value)
        if numeric is not None:
            cleaned.append(numeric)
    return cleaned


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _sample_variance(values: Sequence[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = _mean(values)
    return sum((value - mean) ** 2 for value in values) / (len(values) - 1)


def _sample_std(values: Sequence[float]) -> float:
    return math.sqrt(_sample_variance(values))


def _normal_two_sided_p_value(test_statistic: float) -> float:
    if not math.isfinite(test_statistic):
        return 0.0
    return math.erfc(abs(test_statistic) / math.sqrt(2))


def _t_two_sided_p_value(test_statistic: float, degrees_of_freedom: float) -> float:
    if not math.isfinite(test_statistic):
        return 0.0
    if scipy_stats is not None and degrees_of_freedom > 0:
        return float(2 * scipy_stats.t.sf(abs(test_statistic), degrees_of_freedom))
    return _normal_two_sided_p_value(test_statistic)


def _t_critical(degrees_of_freedom: float, confidence: float = 0.95) -> float:
    if scipy_stats is not None and degrees_of_freedom > 0:
        return float(scipy_stats.t.ppf((1 + confidence) / 2, degrees_of_freedom))

    table = [
        (1, 12.706),
        (2, 4.303),
        (3, 3.182),
        (4, 2.776),
        (5, 2.571),
        (6, 2.447),
        (7, 2.365),
        (8, 2.306),
        (9, 2.262),
        (10, 2.228),
        (15, 2.131),
        (20, 2.086),
        (25, 2.060),
        (30, 2.042),
        (40, 2.021),
        (60, 2.000),
        (120, 1.980),
    ]
    for upper_df, critical in table:
        if degrees_of_freedom <= upper_df:
            return critical
    return 1.96


def calculate_sample_size(
    baseline_values: Sequence[Any],
    challenger_values: Sequence[Any],
    *,
    paired: bool = False,
) -> int:
    if paired:
        return min(len(baseline_values), len(challenger_values))
    return min(len(_clean(baseline_values)), len(_clean(challenger_values)))


def calculate_confidence_interval(
    values: Sequence[Any],
    *,
    confidence: float = 0.95,
) -> tuple[float | None, float | None]:
    cleaned = _clean(values)
    if not cleaned:
        return None, None
    if len(cleaned) == 1:
        return cleaned[0], cleaned[0]
    mean = _mean(cleaned)
    standard_error = _sample_std(cleaned) / math.sqrt(len(cleaned))
    margin = _t_critical(len(cleaned) - 1, confidence) * standard_error
    return mean - margin, mean + margin


def _difference_confidence_interval(
    difference: float,
    standard_error: float,
    degrees_of_freedom: float,
    *,
    confidence: float = 0.95,
) -> tuple[float | None, float | None]:
    if standard_error == 0:
        return difference, difference
    margin = _t_critical(degrees_of_freedom, confidence) * standard_error
    return difference - margin, difference + margin


def cohen_d(
    baseline_values: Sequence[Any],
    challenger_values: Sequence[Any],
    *,
    paired: bool = False,
) -> float | None:
    baseline = _clean(baseline_values)
    challenger = _clean(challenger_values)
    if not baseline or not challenger:
        return None

    if paired:
        pairs = list(zip(baseline, challenger))
        if not pairs:
            return None
        differences = [challenger_value - baseline_value for baseline_value, challenger_value in pairs]
        mean_difference = _mean(differences)
        standard_deviation = _sample_std(differences)
        if standard_deviation == 0:
            return 0.0 if mean_difference == 0 else math.copysign(math.inf, mean_difference)
        return mean_difference / standard_deviation

    if len(baseline) < 2 or len(challenger) < 2:
        return None
    baseline_variance = _sample_variance(baseline)
    challenger_variance = _sample_variance(challenger)
    pooled_degrees = len(baseline) + len(challenger) - 2
    if pooled_degrees <= 0:
        return None
    pooled_standard_deviation = math.sqrt(
        ((len(baseline) - 1) * baseline_variance + (len(challenger) - 1) * challenger_variance)
        / pooled_degrees
    )
    mean_difference = _mean(challenger) - _mean(baseline)
    if pooled_standard_deviation == 0:
        return 0.0 if mean_difference == 0 else math.copysign(math.inf, mean_difference)
    return mean_difference / pooled_standard_deviation


def welch_t_test(
    baseline_values: Sequence[Any],
    challenger_values: Sequence[Any],
) -> dict[str, Any]:
    baseline = _clean(baseline_values)
    challenger = _clean(challenger_values)
    baseline_mean = _mean(baseline)
    challenger_mean = _mean(challenger)
    difference = challenger_mean - baseline_mean
    warnings: list[str] = []

    if len(baseline) < 2 or len(challenger) < 2:
        warnings.append("Welch t-test requires at least two observations in each run.")
        return {
            "test": "welch_t_test",
            "baseline_mean": baseline_mean,
            "challenger_mean": challenger_mean,
            "difference": difference,
            "confidence_interval": (None, None),
            "p_value": None,
            "effect_size": _finite(cohen_d(baseline, challenger)),
            "sample_size": min(len(baseline), len(challenger)),
            "warnings": warnings,
        }

    baseline_variance = _sample_variance(baseline)
    challenger_variance = _sample_variance(challenger)
    standard_error = math.sqrt(
        baseline_variance / len(baseline) + challenger_variance / len(challenger)
    )

    if standard_error == 0:
        p_value = 1.0 if difference == 0 else 0.0
        confidence_interval = (difference, difference)
        degrees_of_freedom = len(baseline) + len(challenger) - 2
    else:
        test_statistic = difference / standard_error
        numerator = (baseline_variance / len(baseline) + challenger_variance / len(challenger)) ** 2
        denominator = 0.0
        if len(baseline) > 1:
            denominator += (baseline_variance / len(baseline)) ** 2 / (len(baseline) - 1)
        if len(challenger) > 1:
            denominator += (challenger_variance / len(challenger)) ** 2 / (len(challenger) - 1)
        degrees_of_freedom = numerator / denominator if denominator else len(baseline) + len(challenger) - 2
        p_value = _t_two_sided_p_value(test_statistic, degrees_of_freedom)
        confidence_interval = _difference_confidence_interval(
            difference,
            standard_error,
            degrees_of_freedom,
        )

    return {
        "test": "welch_t_test",
        "baseline_mean": baseline_mean,
        "challenger_mean": challenger_mean,
        "difference": difference,
        "confidence_interval": confidence_interval,
        "p_value": p_value,
        "effect_size": _finite(cohen_d(baseline, challenger)),
        "sample_size": min(len(baseline), len(challenger)),
        "warnings": warnings,
    }


def paired_t_test(
    baseline_values: Sequence[Any],
    challenger_values: Sequence[Any],
) -> dict[str, Any]:
    baseline = _clean(baseline_values)
    challenger = _clean(challenger_values)
    pairs = list(zip(baseline, challenger))
    baseline = [pair[0] for pair in pairs]
    challenger = [pair[1] for pair in pairs]
    baseline_mean = _mean(baseline)
    challenger_mean = _mean(challenger)
    difference = challenger_mean - baseline_mean
    warnings: list[str] = []

    if len(pairs) < 2:
        warnings.append("Paired t-test requires at least two paired examples.")
        return {
            "test": "paired_t_test",
            "baseline_mean": baseline_mean,
            "challenger_mean": challenger_mean,
            "difference": difference,
            "confidence_interval": (None, None),
            "p_value": None,
            "effect_size": _finite(cohen_d(baseline, challenger, paired=True)),
            "sample_size": len(pairs),
            "warnings": warnings,
        }

    differences = [challenger_value - baseline_value for baseline_value, challenger_value in pairs]
    mean_difference = _mean(differences)
    standard_error = _sample_std(differences) / math.sqrt(len(differences))
    degrees_of_freedom = len(differences) - 1

    if standard_error == 0:
        p_value = 1.0 if mean_difference == 0 else 0.0
        confidence_interval = (mean_difference, mean_difference)
    else:
        test_statistic = mean_difference / standard_error
        p_value = _t_two_sided_p_value(test_statistic, degrees_of_freedom)
        confidence_interval = _difference_confidence_interval(
            mean_difference,
            standard_error,
            degrees_of_freedom,
        )

    return {
        "test": "paired_t_test",
        "baseline_mean": baseline_mean,
        "challenger_mean": challenger_mean,
        "difference": mean_difference,
        "confidence_interval": confidence_interval,
        "p_value": p_value,
        "effect_size": _finite(cohen_d(baseline, challenger, paired=True)),
        "sample_size": len(pairs),
        "warnings": warnings,
    }


def _is_binary(values: Sequence[float]) -> bool:
    return all(value in {0.0, 1.0} for value in values)


def cohen_h(baseline_rate: float, challenger_rate: float) -> float:
    baseline_rate = min(max(baseline_rate, 0.0), 1.0)
    challenger_rate = min(max(challenger_rate, 0.0), 1.0)
    return (
        2 * math.asin(math.sqrt(challenger_rate))
        - 2 * math.asin(math.sqrt(baseline_rate))
    )


def _proportion_difference_confidence_interval(
    baseline: Sequence[float],
    challenger: Sequence[float],
) -> tuple[float | None, float | None]:
    if not baseline or not challenger:
        return None, None
    baseline_rate = _mean(baseline)
    challenger_rate = _mean(challenger)
    difference = challenger_rate - baseline_rate
    standard_error = math.sqrt(
        baseline_rate * (1 - baseline_rate) / len(baseline)
        + challenger_rate * (1 - challenger_rate) / len(challenger)
    )
    if standard_error == 0:
        return difference, difference
    margin = 1.96 * standard_error
    return difference - margin, difference + margin


def fisher_exact_test(
    baseline_values: Sequence[Any],
    challenger_values: Sequence[Any],
) -> dict[str, Any]:
    baseline = _clean(baseline_values)
    challenger = _clean(challenger_values)
    warnings: list[str] = []

    if not _is_binary(baseline + challenger):
        warnings.append("Binary metric evaluated with non-binary values; Fisher exact test was not applied.")
        p_value = None
    elif scipy_stats is None:
        warnings.append("Fisher exact test unavailable because scipy is not installed; binary p-value omitted.")
        p_value = None
    else:
        baseline_successes = int(sum(baseline))
        challenger_successes = int(sum(challenger))
        table = [
            [baseline_successes, len(baseline) - baseline_successes],
            [challenger_successes, len(challenger) - challenger_successes],
        ]
        p_value = float(scipy_stats.fisher_exact(table, alternative="two-sided").pvalue)

    confidence_interval = _proportion_difference_confidence_interval(baseline, challenger)
    baseline_mean = _mean(baseline)
    challenger_mean = _mean(challenger)
    return {
        "test": "fisher_exact",
        "baseline_mean": baseline_mean,
        "challenger_mean": challenger_mean,
        "difference": challenger_mean - baseline_mean,
        "confidence_interval": confidence_interval,
        "p_value": p_value,
        "effect_size": cohen_h(baseline_mean, challenger_mean) if baseline or challenger else None,
        "sample_size": min(len(baseline), len(challenger)),
        "warnings": warnings,
    }


def mann_whitney_u_test(
    baseline_values: Sequence[Any],
    challenger_values: Sequence[Any],
) -> dict[str, Any]:
    baseline = _clean(baseline_values)
    challenger = _clean(challenger_values)
    warnings: list[str] = []
    base = welch_t_test(baseline, challenger)
    base["test"] = "mann_whitney_u"

    if scipy_stats is None:
        warnings.append("Mann-Whitney U test unavailable because scipy is not installed; ordinal p-value omitted.")
        base["p_value"] = None
    elif baseline and challenger:
        base["p_value"] = float(
            scipy_stats.mannwhitneyu(
                baseline,
                challenger,
                alternative="two-sided",
            ).pvalue
        )
    else:
        base["p_value"] = None

    base["warnings"] = [*base.get("warnings", []), *warnings]
    return base


def bonferroni_correction(
    p_values: Sequence[float | None],
    *,
    alpha: float = 0.05,
) -> dict[str, list[float | bool | None]]:
    comparisons = len([p_value for p_value in p_values if p_value is not None])
    adjusted: list[float | None] = []
    significant: list[bool | None] = []
    for p_value in p_values:
        if p_value is None:
            adjusted.append(None)
            significant.append(None)
            continue
        corrected = min(p_value * comparisons, 1.0)
        adjusted.append(corrected)
        significant.append(corrected <= alpha)
    return {"adjusted_p_values": adjusted, "significant": significant}


def benjamini_hochberg_correction(
    p_values: Sequence[float | None],
    *,
    alpha: float = 0.05,
) -> dict[str, list[float | bool | None]]:
    indexed = [(index, p_value) for index, p_value in enumerate(p_values) if p_value is not None]
    count = len(indexed)
    adjusted: list[float | None] = [None] * len(p_values)
    significant: list[bool | None] = [None] * len(p_values)
    if count == 0:
        return {"adjusted_p_values": adjusted, "significant": significant}

    sorted_values = sorted(indexed, key=lambda item: item[1])
    running_min = 1.0
    for rank_from_end, (index, p_value) in enumerate(reversed(sorted_values), start=1):
        rank = count - rank_from_end + 1
        corrected = min((p_value * count) / rank, running_min, 1.0)
        running_min = corrected
        adjusted[index] = corrected

    for index, corrected in enumerate(adjusted):
        significant[index] = None if corrected is None else corrected <= alpha
    return {"adjusted_p_values": adjusted, "significant": significant}


def detect_multiple_comparisons_without_correction(
    metric_names: Sequence[str],
    correction_method: str,
) -> str | None:
    if len(metric_names) > 1 and correction_method == "none":
        return "Multiple comparisons were requested without a correction method."
    return None


def detect_underpowered_comparison(
    sample_size: int,
    *,
    minimum_sample_size: int = MINIMUM_SAMPLE_SIZE,
) -> str | None:
    if sample_size < minimum_sample_size:
        return f"N < {minimum_sample_size}; comparison is underpowered."
    return None


def detect_benchmark_saturation(
    baseline_mean: float | None,
    challenger_mean: float | None,
    metric_name: str,
) -> str | None:
    if metric_name not in QUALITY_METRICS and metric_name not in BINARY_METRICS:
        return None
    if baseline_mean is None or challenger_mean is None:
        return None
    if baseline_mean >= SATURATION_THRESHOLD and challenger_mean >= SATURATION_THRESHOLD:
        return "Benchmark appears saturated; both runs are above 95%."
    return None


def detect_paired_runs(
    baseline_results: Sequence[dict[str, Any]],
    challenger_results: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    baseline_by_example = {
        str(row["example_id"]): row
        for row in baseline_results
        if row.get("example_id") is not None
    }
    challenger_by_example = {
        str(row["example_id"]): row
        for row in challenger_results
        if row.get("example_id") is not None
    }

    common_example_ids = [
        str(row["example_id"])
        for row in baseline_results
        if row.get("example_id") is not None
        and str(row["example_id"]) in challenger_by_example
    ]
    baseline_only = sorted(set(baseline_by_example) - set(challenger_by_example))
    challenger_only = sorted(set(challenger_by_example) - set(baseline_by_example))
    warnings = []
    if common_example_ids and (baseline_only or challenger_only):
        warnings.append("Runs have partial example overlap; unmatched examples were excluded from paired comparison.")

    return {
        "is_paired": bool(common_example_ids),
        "common_example_ids": common_example_ids,
        "baseline_only_example_ids": baseline_only,
        "challenger_only_example_ids": challenger_only,
        "paired_rows": [
            (baseline_by_example[example_id], challenger_by_example[example_id])
            for example_id in common_example_ids
        ],
        "warnings": warnings,
    }


def _normalize_text(value: Any) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip().lower()
    return normalized or None


def _normalize_flags(value: Any) -> set[str]:
    if not value:
        return set()
    if isinstance(value, str):
        normalized = _normalize_text(value)
        return {normalized} if normalized else set()
    if isinstance(value, dict):
        return {
            _normalize_text(key) or ""
            for key, enabled in value.items()
            if enabled
        }
    if isinstance(value, list):
        flags = set()
        for item in value:
            if isinstance(item, dict):
                flag = item.get("flag") or item.get("name") or item.get("type")
            else:
                flag = item
            normalized = _normalize_text(flag)
            if normalized:
                flags.add(normalized)
        return flags
    return set()


def _flag_recall(expected_flags: Any, predicted_flags: Any) -> float:
    expected = _normalize_flags(expected_flags)
    if not expected:
        return 1.0
    predicted = _normalize_flags(predicted_flags)
    return len(expected & predicted) / len(expected)


def extract_metric_value(row: dict[str, Any], metric_name: str) -> float | None:
    metric_name = CONTINUOUS_ALIASES.get(metric_name, metric_name)

    if metric_name == "score":
        return _as_float(row.get("score"))
    if metric_name == "passed":
        return _as_float(row.get("passed"))
    if metric_name == "latency_ms":
        return _as_float(row.get("latency_ms"))
    if metric_name == "estimated_cost":
        return _as_float(row.get("estimated_cost"))
    if metric_name == "flag_recall":
        if row.get("flag_recall") is not None:
            return _as_float(row.get("flag_recall"))
        return _flag_recall(row.get("expected_flags"), row.get("predicted_flags"))
    if metric_name == "pathway_accuracy":
        if row.get("expected_pathway") is None:
            return None
        return 1.0 if _normalize_text(row.get("expected_pathway")) == _normalize_text(row.get("predicted_pathway")) else 0.0
    if metric_name == "german_level_accuracy":
        if row.get("expected_german_level") is None:
            return None
        return 1.0 if _normalize_text(row.get("expected_german_level")) == _normalize_text(row.get("predicted_german_level")) else 0.0
    if metric_name == "timeline_accuracy":
        if row.get("expected_timeline") is None:
            return None
        return 1.0 if _normalize_text(row.get("expected_timeline")) == _normalize_text(row.get("predicted_timeline")) else 0.0

    return _as_float(row.get(metric_name))


def infer_metric_type(
    metric_name: str,
    baseline_values: Sequence[float],
    challenger_values: Sequence[float],
) -> str:
    if metric_name in BINARY_METRICS:
        return "binary"
    if metric_name in ORDINAL_METRICS:
        return "ordinal"
    if _is_binary(list(baseline_values) + list(challenger_values)) and metric_name.endswith("_accuracy"):
        return "binary"
    return "continuous"


def _relative_difference(difference: float, baseline_mean: float) -> float | None:
    if baseline_mean == 0:
        return 0.0 if difference == 0 else None
    return difference / abs(baseline_mean)


def _challenger_is_better(metric_name: str, difference: float) -> bool:
    if metric_name in LOWER_IS_BETTER_METRICS:
        return difference < 0
    return difference > 0


def _materially_worse(baseline_mean: float | None, challenger_mean: float | None) -> bool:
    if baseline_mean is None or challenger_mean is None:
        return False
    if challenger_mean <= baseline_mean:
        return False
    if baseline_mean <= 0:
        return challenger_mean > 0
    return (challenger_mean - baseline_mean) / baseline_mean >= 0.2


def _significance_warnings(
    *,
    p_value: float | None,
    effect_size: float | None,
    statistical_significance: bool,
    practical_significance: bool,
) -> list[str]:
    warnings: list[str] = []
    if statistical_significance and not practical_significance:
        warnings.append("p-value is significant, but the effect is practically negligible.")
    if statistical_significance and effect_size is not None and abs(effect_size) < NEGLIGIBLE_EFFECT_SIZE:
        warnings.append("p-value is significant, but effect size is negligible.")
    if practical_significance and not statistical_significance:
        if p_value is None:
            warnings.append("Effect is practically meaningful, but statistical significance could not be established.")
        else:
            warnings.append("Effect size is meaningful, but p-value is not significant.")
    return warnings


def build_recommendation(
    *,
    metric_name: str,
    difference: float,
    p_value: float | None,
    effect_size: float | None,
    sample_size: int,
    statistical_significance: bool,
    practical_significance: bool,
    saturated: bool = False,
) -> str:
    if sample_size < MINIMUM_SAMPLE_SIZE:
        return "inconclusive: sample size is too small to declare a winner"
    if saturated:
        return "inconclusive: benchmark appears saturated"
    if p_value is None:
        return "inconclusive: statistical test unavailable"
    if statistical_significance and effect_size is not None and abs(effect_size) < NEGLIGIBLE_EFFECT_SIZE:
        return "inconclusive: statistically significant but effect size is negligible"
    if statistical_significance and not practical_significance:
        return "inconclusive: statistically significant but practically negligible"
    if practical_significance and not statistical_significance:
        return "inconclusive: practical effect observed but not statistically significant"
    if statistical_significance and practical_significance:
        if _challenger_is_better(metric_name, difference):
            return "challenger_wins: statistically and practically meaningful improvement"
        return "baseline_wins: challenger is statistically and practically worse"
    return "inconclusive: no statistically or practically meaningful difference"


def compare_metric_values(
    baseline_values: Sequence[Any],
    challenger_values: Sequence[Any],
    *,
    metric_name: str = "score",
    comparison_type: str = "auto",
    paired: bool = False,
    alpha: float = 0.05,
    minimum_practical_effect: float = 0.02,
    paired_possible: bool = False,
) -> dict[str, Any]:
    baseline = _clean(baseline_values)
    challenger = _clean(challenger_values)
    warnings: list[str] = []

    if paired:
        pairs = [
            (baseline_value, challenger_value)
            for baseline_value, challenger_value in zip(baseline, challenger)
        ]
        baseline = [pair[0] for pair in pairs]
        challenger = [pair[1] for pair in pairs]
    elif paired_possible:
        warnings.append("Runs were compared as unpaired even though paired examples were available.")

    if metric_name in BINARY_METRICS and comparison_type not in {"auto", "binary"}:
        warnings.append("Binary metric evaluated with non-binary test; use Fisher exact where possible.")

    metric_type = (
        infer_metric_type(metric_name, baseline, challenger)
        if comparison_type == "auto"
        else comparison_type
    )

    if metric_type == "binary":
        test_result = fisher_exact_test(baseline, challenger)
    elif metric_type == "ordinal":
        test_result = mann_whitney_u_test(baseline, challenger)
    elif paired:
        test_result = paired_t_test(baseline, challenger)
    else:
        test_result = welch_t_test(baseline, challenger)

    warnings.extend(test_result.get("warnings", []))
    sample_size = int(test_result.get("sample_size") or 0)
    underpowered = detect_underpowered_comparison(sample_size)
    if underpowered:
        warnings.append(underpowered)

    baseline_mean = _as_float(test_result.get("baseline_mean")) or 0.0
    challenger_mean = _as_float(test_result.get("challenger_mean")) or 0.0
    difference = challenger_mean - baseline_mean
    p_value = _as_float(test_result.get("p_value"))
    effect_size = _finite(_as_float(test_result.get("effect_size")))
    statistical_significance = p_value is not None and p_value <= alpha
    practical_significance = abs(difference) >= minimum_practical_effect
    saturation_warning = detect_benchmark_saturation(
        baseline_mean,
        challenger_mean,
        metric_name,
    )
    if saturation_warning:
        warnings.append(saturation_warning)

    warnings.extend(
        _significance_warnings(
            p_value=p_value,
            effect_size=effect_size,
            statistical_significance=statistical_significance,
            practical_significance=practical_significance,
        )
    )

    recommendation = build_recommendation(
        metric_name=metric_name,
        difference=difference,
        p_value=p_value,
        effect_size=effect_size,
        sample_size=sample_size,
        statistical_significance=statistical_significance,
        practical_significance=practical_significance,
        saturated=saturation_warning is not None,
    )
    interval_low, interval_high = test_result.get("confidence_interval") or (None, None)

    return {
        "test": test_result.get("test"),
        "metric_type": metric_type,
        "metric_name": metric_name,
        "baseline_mean": baseline_mean,
        "challenger_mean": challenger_mean,
        "absolute_difference": difference,
        "relative_difference": _relative_difference(difference, baseline_mean),
        "confidence_interval_low": interval_low,
        "confidence_interval_high": interval_high,
        "p_value": p_value,
        "effect_size": effect_size,
        "sample_size": sample_size,
        "statistical_significance": statistical_significance,
        "practical_significance": practical_significance,
        "recommendation": recommendation,
        "warnings": list(dict.fromkeys(warnings)),
    }


def _mean_metric(rows: Sequence[dict[str, Any]], metric_name: str) -> float | None:
    values = [
        value
        for value in (extract_metric_value(row, metric_name) for row in rows)
        if value is not None
    ]
    return _mean(values) if values else None


def _fetch_run(supabase: Any, run_id: str) -> dict[str, Any]:
    run = _first_row(
        supabase.table("evaluation_runs").select("*").eq(
            "id",
            run_id,
        ).single().execute()
    )
    if not run:
        raise ValueError("evaluation run not found")
    return run


def _comparison_row(comparison: dict[str, Any], experiment_id: str | None) -> dict[str, Any]:
    return {
        "experiment_id": experiment_id,
        "baseline_run_id": comparison["baseline_run_id"],
        "challenger_run_id": comparison["challenger_run_id"],
        "metric_name": comparison["metric_name"],
        "baseline_mean": _finite(comparison.get("baseline_mean")),
        "challenger_mean": _finite(comparison.get("challenger_mean")),
        "absolute_difference": _finite(comparison.get("absolute_difference")),
        "relative_difference": _finite(comparison.get("relative_difference")),
        "confidence_interval_low": _finite(comparison.get("confidence_interval_low")),
        "confidence_interval_high": _finite(comparison.get("confidence_interval_high")),
        "p_value": _finite(comparison.get("p_value")),
        "effect_size": _finite(comparison.get("effect_size")),
        "sample_size": comparison.get("sample_size") or 0,
        "statistical_significance": comparison.get("statistical_significance", False),
        "practical_significance": comparison.get("practical_significance", False),
        "recommendation": comparison.get("recommendation") or "inconclusive",
        "warnings": comparison.get("warnings") or [],
    }


def compare_evaluation_runs(
    supabase: Any,
    baseline_run_id: str,
    challenger_run_id: str,
    *,
    metric_name: str = "score",
    comparison_type: str = "auto",
    minimum_practical_effect: float = 0.02,
    alpha: float = 0.05,
    correction_method: str = "none",
    experiment_id: str | None = None,
    persist: bool = True,
) -> dict[str, Any]:
    from services.evaluation import fetch_results_with_expectations

    baseline_run = _fetch_run(supabase, baseline_run_id)
    challenger_run = _fetch_run(supabase, challenger_run_id)
    if baseline_run.get("dataset_id") != challenger_run.get("dataset_id"):
        raise ValueError("evaluation runs must use the same dataset")

    baseline_results = fetch_results_with_expectations(supabase, baseline_run_id)
    challenger_results = fetch_results_with_expectations(supabase, challenger_run_id)
    pairing = detect_paired_runs(baseline_results, challenger_results)
    warnings = list(pairing["warnings"])

    if pairing["is_paired"]:
        baseline_rows: list[dict[str, Any]] = []
        challenger_rows: list[dict[str, Any]] = []
        baseline_values: list[float] = []
        challenger_values: list[float] = []
        skipped = 0
        for baseline_row, challenger_row in pairing["paired_rows"]:
            baseline_value = extract_metric_value(baseline_row, metric_name)
            challenger_value = extract_metric_value(challenger_row, metric_name)
            if baseline_value is None or challenger_value is None:
                skipped += 1
                continue
            baseline_rows.append(baseline_row)
            challenger_rows.append(challenger_row)
            baseline_values.append(baseline_value)
            challenger_values.append(challenger_value)
        if skipped:
            warnings.append(f"{skipped} paired examples were excluded because the metric was unavailable.")
        paired = True
    else:
        baseline_rows = baseline_results
        challenger_rows = challenger_results
        baseline_values = [
            value
            for value in (extract_metric_value(row, metric_name) for row in baseline_rows)
            if value is not None
        ]
        challenger_values = [
            value
            for value in (extract_metric_value(row, metric_name) for row in challenger_rows)
            if value is not None
        ]
        warnings.append("Runs are unpaired; comparison uses independent samples.")
        paired = False

    if not baseline_values or not challenger_values:
        raise ValueError("selected metric is unavailable for one or both evaluation runs")

    comparison = compare_metric_values(
        baseline_values,
        challenger_values,
        metric_name=metric_name,
        comparison_type=comparison_type,
        paired=paired,
        alpha=alpha,
        minimum_practical_effect=minimum_practical_effect,
    )
    comparison["baseline_run_id"] = baseline_run_id
    comparison["challenger_run_id"] = challenger_run_id
    comparison["dataset_id"] = baseline_run.get("dataset_id")
    comparison["paired"] = paired
    comparison["minimum_practical_effect"] = minimum_practical_effect
    comparison["alpha"] = alpha
    comparison["correction_method"] = correction_method
    comparison["warnings"] = list(dict.fromkeys([*warnings, *comparison["warnings"]]))

    if experiment_id and correction_method == "none":
        try:
            existing = supabase.table("evaluation_comparisons").select("metric_name").eq(
                "experiment_id",
                experiment_id,
            ).execute()
            metric_names = {
                row.get("metric_name")
                for row in existing.data or []
                if row.get("metric_name")
            }
            metric_names.add(metric_name)
            multiple_warning = detect_multiple_comparisons_without_correction(
                sorted(metric_names),
                correction_method,
            )
            if multiple_warning and len(metric_names) > 1:
                comparison["warnings"].append(multiple_warning)
        except Exception:
            pass

    if metric_name in QUALITY_METRICS and _challenger_is_better(
        metric_name,
        comparison["absolute_difference"],
    ):
        baseline_latency = _mean_metric(baseline_rows, "latency_ms")
        challenger_latency = _mean_metric(challenger_rows, "latency_ms")
        if _materially_worse(baseline_latency, challenger_latency):
            comparison["warnings"].append("Challenger is better on quality but materially worse on latency.")

        baseline_cost = _mean_metric(baseline_rows, "estimated_cost")
        challenger_cost = _mean_metric(challenger_rows, "estimated_cost")
        if _materially_worse(baseline_cost, challenger_cost):
            comparison["warnings"].append("Challenger is better on quality but materially worse on estimated cost.")

    comparison["warnings"] = list(dict.fromkeys(comparison["warnings"]))

    if persist and experiment_id:
        inserted = _first_row(
            supabase.table("evaluation_comparisons").insert(
                _comparison_row(comparison, experiment_id)
            ).execute()
        )
        summary = {
            "latest_comparison_id": inserted.get("id"),
            "metric_name": metric_name,
            "baseline_mean": comparison["baseline_mean"],
            "challenger_mean": comparison["challenger_mean"],
            "p_value": comparison["p_value"],
            "effect_size": comparison["effect_size"],
            "recommendation": comparison["recommendation"],
            "warnings": comparison["warnings"],
        }
        supabase.table("evaluation_experiments").update({
            "status": "completed",
            "completed_at": utc_now_iso(),
            "summary": summary,
        }).eq("id", experiment_id).execute()
        return {**comparison, **inserted}

    return comparison


def create_evaluation_experiment(
    supabase: Any,
    payload: dict[str, Any],
) -> dict[str, Any]:
    baseline_run = _fetch_run(supabase, payload["baseline_run_id"])
    challenger_run = _fetch_run(supabase, payload["challenger_run_id"])
    dataset_id = payload["dataset_id"]
    if baseline_run.get("dataset_id") != dataset_id or challenger_run.get("dataset_id") != dataset_id:
        raise ValueError("experiment dataset must match both evaluation runs")
    if payload["baseline_run_id"] == payload["challenger_run_id"]:
        raise ValueError("baseline and challenger runs must be different")

    row = {
        "name": payload["name"],
        "description": payload.get("description"),
        "dataset_id": dataset_id,
        "baseline_run_id": payload["baseline_run_id"],
        "challenger_run_id": payload["challenger_run_id"],
        "comparison_type": payload.get("comparison_type") or "auto",
        "metric_name": payload.get("metric_name") or "score",
        "minimum_practical_effect": payload.get("minimum_practical_effect", 0.02),
        "alpha": payload.get("alpha", 0.05),
        "correction_method": payload.get("correction_method") or "none",
        "status": payload.get("status") or "draft",
        "summary": payload.get("summary") or {},
    }
    return _first_row(supabase.table("evaluation_experiments").insert(row).execute())


def list_evaluation_experiments(supabase: Any) -> list[dict[str, Any]]:
    result = supabase.table("evaluation_experiments").select("*").order(
        "created_at",
        desc=True,
    ).execute()
    return result.data or []


def get_evaluation_experiment(supabase: Any, experiment_id: str) -> dict[str, Any]:
    experiment = _first_row(
        supabase.table("evaluation_experiments").select("*").eq(
            "id",
            experiment_id,
        ).single().execute()
    )
    if not experiment:
        raise ValueError("evaluation experiment not found")

    comparisons = supabase.table("evaluation_comparisons").select("*").eq(
        "experiment_id",
        experiment_id,
    ).order("created_at", desc=True).execute()
    experiment["comparisons"] = comparisons.data or []
    return experiment


def run_evaluation_experiment_comparison(
    supabase: Any,
    experiment_id: str,
    overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    experiment = get_evaluation_experiment(supabase, experiment_id)
    override_data = overrides or {}
    supabase.table("evaluation_experiments").update({
        "status": "running",
    }).eq("id", experiment_id).execute()

    try:
        return compare_evaluation_runs(
            supabase,
            override_data.get("baseline_run_id") or experiment["baseline_run_id"],
            override_data.get("challenger_run_id") or experiment["challenger_run_id"],
            metric_name=override_data.get("metric_name") or experiment.get("metric_name") or "score",
            comparison_type=override_data.get("comparison_type") or experiment.get("comparison_type") or "auto",
            minimum_practical_effect=override_data.get(
                "minimum_practical_effect",
                experiment.get("minimum_practical_effect", 0.02),
            ),
            alpha=override_data.get("alpha", experiment.get("alpha", 0.05)),
            correction_method=override_data.get(
                "correction_method",
                experiment.get("correction_method", "none"),
            ),
            experiment_id=experiment_id,
            persist=True,
        )
    except Exception as exc:
        supabase.table("evaluation_experiments").update({
            "status": "failed",
            "summary": {"error": str(exc)},
        }).eq("id", experiment_id).execute()
        raise


def get_latest_statistical_comparison_for_run(
    supabase: Any,
    run_id: str,
) -> dict[str, Any] | None:
    try:
        baseline_matches = supabase.table("evaluation_comparisons").select("*").eq(
            "baseline_run_id",
            run_id,
        ).order("created_at", desc=True).limit(1).execute()
        challenger_matches = supabase.table("evaluation_comparisons").select("*").eq(
            "challenger_run_id",
            run_id,
        ).order("created_at", desc=True).limit(1).execute()
    except Exception:
        return None

    candidates = (baseline_matches.data or []) + (challenger_matches.data or [])
    if not candidates:
        return None
    comparison = sorted(
        candidates,
        key=lambda row: row.get("created_at") or "",
        reverse=True,
    )[0]
    experiment_id = comparison.get("experiment_id")
    if experiment_id:
        try:
            experiment = _first_row(
                supabase.table("evaluation_experiments").select("*").eq(
                    "id",
                    experiment_id,
                ).single().execute()
            )
            comparison["experiment"] = experiment
        except Exception:
            comparison["experiment"] = None
    return comparison


def get_latest_experiment_summary(supabase: Any) -> dict[str, Any] | None:
    try:
        latest = _first_row(
            supabase.table("evaluation_experiments").select("*").order(
                "created_at",
                desc=True,
            ).limit(1).execute()
        )
    except Exception:
        return None
    if not latest:
        return None

    try:
        comparison = _first_row(
            supabase.table("evaluation_comparisons").select("*").eq(
                "experiment_id",
                latest.get("id"),
            ).order("created_at", desc=True).limit(1).execute()
        )
    except Exception:
        comparison = {}
    latest["latest_comparison"] = comparison or None
    return latest
