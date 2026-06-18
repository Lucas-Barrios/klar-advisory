from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from services.ai_observability import AI_MODEL
from services.diagnostic_versions import (
    DIAGNOSTIC_PROMPT_VERSION,
    DIAGNOSTIC_RUBRIC_VERSION,
)
from services.redaction import redact_sensitive_text


EVALUATION_PASS_THRESHOLD = 0.8

# Tolerance band for overall_score comparison: a predicted score within ±10 points
# of the expected value counts as accurate. The score is continuous (0–100) and
# cannot be derived exactly from the rubric for most profiles, so exact-match
# would be meaningless. ±10 is derived from the rubric's 20-point CEFR step size
# (e.g. A2=35→B1=55) and the 15% weight of the most discretionary dimension.
OVERALL_SCORE_TOLERANCE = 10

PII_EVALUATION_KEYS = {
    "name",
    "full_name",
    "email",
    "student_name",
    "student_email",
    "raw_output",
    "prompt",
    "raw_prompt",
}

SAFE_EVALUATION_INPUT_KEYS = {
    "country",
    "age",
    "pathway",
    "german_level",
    "english_level",
    "education_level",
    "field_of_study",
    "work_experience_years",
    "timeline",
    "financial_situation",
    "current_location",
}

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _first_row(result: Any) -> dict[str, Any]:
    rows = result.data or []
    if isinstance(rows, list):
        return rows[0] if rows else {}
    return rows


def sanitize_evaluation_payload(payload: dict[str, Any]) -> dict[str, Any]:
    safe = {}
    for key, value in payload.items():
        if key in PII_EVALUATION_KEYS:
            continue
        if key not in SAFE_EVALUATION_INPUT_KEYS:
            continue
        if isinstance(value, str):
            value = value.strip()
            if not value:
                continue
        if value is not None:
            safe[key] = value
    safe.setdefault("name", "Evaluation Candidate")
    return safe


def redact_direct_identifiers(
    value: str | None,
    *,
    identifiers: list[str | None] | None = None,
) -> str | None:
    return redact_sensitive_text(
        value,
        identifiers=identifiers,
        redact_name_like=True,
    )


def normalize_text(value: Any) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip().lower()
    return normalized or None


def normalize_flags(value: Any) -> set[str]:
    if not value:
        return set()
    if isinstance(value, str):
        normalized = normalize_text(value)
        return {normalized} if normalized else set()
    if isinstance(value, dict):
        return {
            normalize_text(key) or ""
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
            normalized = normalize_text(flag)
            if normalized:
                flags.add(normalized)
        return flags
    return set()


def field_accuracy(expected: Any, predicted: Any) -> float | None:
    normalized_expected = normalize_text(expected)
    if normalized_expected is None:
        return None
    return 1.0 if normalized_expected == normalize_text(predicted) else 0.0


def score_within_tolerance(
    expected: Any,
    predicted: Any,
    *,
    tolerance: int = OVERALL_SCORE_TOLERANCE,
) -> float | None:
    """Return 1.0 if |predicted - expected| <= tolerance, 0.0 otherwise, None if no expected."""
    if expected is None:
        return None
    try:
        exp_val = float(expected)
        pred_val = float(predicted) if predicted is not None else None
    except (TypeError, ValueError):
        return None
    if pred_val is None:
        return 0.0
    return 1.0 if abs(pred_val - exp_val) <= tolerance else 0.0


def calculate_flag_recall(expected_flags: Any, predicted_flags: Any) -> float:
    expected = normalize_flags(expected_flags)
    if not expected:
        return 1.0
    predicted = normalize_flags(predicted_flags)
    return round(len(expected & predicted) / len(expected), 4)


def compare_prediction(
    example: dict[str, Any],
    prediction: dict[str, Any],
    *,
    pass_threshold: float = EVALUATION_PASS_THRESHOLD,
) -> dict[str, Any]:
    field_scores = {
        "pathway": field_accuracy(
            example.get("expected_pathway"),
            prediction.get("predicted_pathway"),
        ),
        "german_level": field_accuracy(
            example.get("expected_german_level"),
            prediction.get("predicted_german_level"),
        ),
        "timeline": field_accuracy(
            example.get("expected_timeline"),
            prediction.get("predicted_timeline"),
        ),
        # overall_score is scored with a ±OVERALL_SCORE_TOLERANCE point tolerance band
        # rather than exact match, since it's a continuous AI estimate not a discrete label.
        # Returns None when expected_overall_score is absent (most DB-stored examples lack it
        # until a migration adds the column; the runner injects it from seed data at eval time).
        "overall_score": score_within_tolerance(
            example.get("expected_overall_score"),
            prediction.get("predicted_overall_score"),
            tolerance=OVERALL_SCORE_TOLERANCE,
        ),
    }
    flag_recall = calculate_flag_recall(
        example.get("expected_flags"),
        prediction.get("predicted_flags"),
    )
    scored_values = [score for score in field_scores.values() if score is not None]
    scored_values.append(flag_recall)
    score = round(sum(scored_values) / len(scored_values), 4) if scored_values else 0.0

    return {
        "field_scores": field_scores,
        "flag_recall": flag_recall,
        "score": score,
        "passed": score >= pass_threshold,
    }


def calculate_summary_metrics(results: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(results)
    if total == 0:
        return {
            "evaluated_examples": 0,
            "pathway_accuracy": 0,
            "german_level_accuracy": 0,
            "timeline_accuracy": 0,
            "flag_recall": 0,
            "overall_pass_rate": 0,
            "average_score": 0,
            "average_latency_ms": 0,
            "average_cost_per_evaluated_example": 0,
        }

    def average(values: list[float]) -> float:
        return round(sum(values) / len(values), 4) if values else 0

    pathway_scores = [
        1.0
        for row in results
        if row.get("expected_pathway") is not None
        and normalize_text(row.get("expected_pathway"))
        == normalize_text(row.get("predicted_pathway"))
    ]
    pathway_total = sum(1 for row in results if row.get("expected_pathway") is not None)

    german_scores = [
        1.0
        for row in results
        if row.get("expected_german_level") is not None
        and normalize_text(row.get("expected_german_level"))
        == normalize_text(row.get("predicted_german_level"))
    ]
    german_total = sum(1 for row in results if row.get("expected_german_level") is not None)

    timeline_scores = [
        1.0
        for row in results
        if row.get("expected_timeline") is not None
        and normalize_text(row.get("expected_timeline"))
        == normalize_text(row.get("predicted_timeline"))
    ]
    timeline_total = sum(1 for row in results if row.get("expected_timeline") is not None)

    flag_recalls = []
    for row in results:
        flag_recall = row.get("flag_recall")
        if flag_recall is None:
            flag_recall = calculate_flag_recall(
                row.get("expected_flags"),
                row.get("predicted_flags"),
            )
        flag_recalls.append(float(flag_recall))
    scores = [float(row.get("score") or 0) for row in results]
    latencies = [
        int(row.get("latency_ms") or 0)
        for row in results
        if row.get("latency_ms") is not None
    ]
    costs = [float(row.get("estimated_cost") or 0) for row in results]
    passed = sum(1 for row in results if row.get("passed") is True)

    # overall_score accuracy: fraction of examples where predicted_overall_score is
    # within ±OVERALL_SCORE_TOLERANCE of expected_overall_score. Only counted when
    # expected_overall_score is present (derived from rubric in seed data).
    overall_score_hits = [
        1.0
        for row in results
        if row.get("expected_overall_score") is not None
        and score_within_tolerance(
            row.get("expected_overall_score"),
            row.get("predicted_overall_score"),
        ) == 1.0
    ]
    overall_score_total = sum(
        1 for row in results if row.get("expected_overall_score") is not None
    )

    return {
        "evaluated_examples": total,
        "pathway_accuracy": round(len(pathway_scores) / pathway_total, 4)
        if pathway_total
        else 0,
        "german_level_accuracy": round(len(german_scores) / german_total, 4)
        if german_total
        else 0,
        "timeline_accuracy": round(len(timeline_scores) / timeline_total, 4)
        if timeline_total
        else 0,
        "overall_score_accuracy": round(len(overall_score_hits) / overall_score_total, 4)
        if overall_score_total
        else None,
        "overall_score_examples_with_expected": overall_score_total,
        "flag_recall": average(flag_recalls),
        "overall_pass_rate": round(passed / total, 4),
        "average_score": average(scores),
        "average_latency_ms": round(sum(latencies) / len(latencies), 2)
        if latencies
        else 0,
        "average_cost_per_evaluated_example": round(sum(costs) / total, 8),
    }


def create_evaluation_dataset(supabase: Any, payload: dict[str, Any]) -> dict[str, Any]:
    row = {
        "name": payload["name"],
        "version": payload["version"],
        "use_case": payload["use_case"],
        "description": payload.get("description"),
        "active": payload.get("active", True),
    }
    return _first_row(supabase.table("evaluation_datasets").insert(row).execute())


def list_evaluation_datasets(supabase: Any) -> list[dict[str, Any]]:
    result = supabase.table("evaluation_datasets").select("*").order(
        "created_at",
        desc=True,
    ).execute()
    return result.data or []


def add_evaluation_example(supabase: Any, payload: dict[str, Any]) -> dict[str, Any]:
    row = {
        "dataset_id": payload["dataset_id"],
        "input_payload": sanitize_evaluation_payload(payload.get("input_payload") or {}),
        "expected_pathway": payload.get("expected_pathway"),
        "expected_german_level": payload.get("expected_german_level"),
        "expected_timeline": payload.get("expected_timeline"),
        "expected_flags": payload.get("expected_flags") or [],
        "expected_summary_notes": redact_direct_identifiers(
            payload.get("expected_summary_notes")
        ),
        "source": payload.get("source") or "manual",
        "reviewed_by_human": payload.get("reviewed_by_human", False),
    }
    return _first_row(supabase.table("evaluation_examples").insert(row).execute())


def build_example_from_reviewed_diagnostic(
    diagnostic: dict[str, Any],
    *,
    dataset_id: str,
) -> dict[str, Any]:
    student = diagnostic.get("students") or {}
    if diagnostic.get("status") not in {"approved", "rejected"}:
        raise ValueError("diagnostic must be reviewed before it becomes an evaluation example")

    flags = []
    if diagnostic.get("status") == "rejected":
        flags.append("human_rejected")
    reviewer_decision = diagnostic.get("reviewer_decision")
    if reviewer_decision:
        flags.append(f"reviewer_decision:{reviewer_decision}")

    notes = (
        diagnostic.get("reviewer_correction_notes")
        or diagnostic.get("reviewer_notes")
        or diagnostic.get("summary")
    )

    return {
        "dataset_id": dataset_id,
        "input_payload": sanitize_evaluation_payload(student),
        "expected_pathway": student.get("pathway"),
        "expected_german_level": student.get("german_level"),
        "expected_timeline": student.get("timeline"),
        "expected_flags": flags,
        "expected_summary_notes": redact_direct_identifiers(
            notes,
            identifiers=[student.get("name"), student.get("email")],
        ),
        "source": f"reviewed_diagnostic:{diagnostic.get('id')}",
        "reviewed_by_human": True,
    }


def add_example_from_diagnostic(
    supabase: Any,
    diagnostic_id: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    diagnostic = _first_row(
        supabase.table("diagnostics").select("*, students(*)").eq(
            "id",
            diagnostic_id,
        ).single().execute()
    )
    if not diagnostic:
        raise ValueError("diagnostic not found")

    example_payload = build_example_from_reviewed_diagnostic(
        diagnostic,
        dataset_id=payload["dataset_id"],
    )
    if payload.get("expected_summary_notes"):
        student = diagnostic.get("students") or {}
        example_payload["expected_summary_notes"] = redact_direct_identifiers(
            payload["expected_summary_notes"],
            identifiers=[
                student.get("name"),
                student.get("full_name"),
                student.get("email"),
            ],
        )
    if payload.get("expected_flags") is not None:
        example_payload["expected_flags"] = payload["expected_flags"]
    return add_evaluation_example(supabase, example_payload)


def create_evaluation_run(supabase: Any, payload: dict[str, Any]) -> dict[str, Any]:
    row = {
        "dataset_id": payload["dataset_id"],
        "model": payload.get("model") or AI_MODEL,
        "prompt_version": payload.get("prompt_version") or DIAGNOSTIC_PROMPT_VERSION,
        "rubric_version": payload.get("rubric_version") or DIAGNOSTIC_RUBRIC_VERSION,
        "run_type": payload.get("run_type") or "manual",
        "started_at": payload.get("started_at") or utc_now_iso(),
        "completed_at": payload.get("completed_at"),
        "status": payload.get("status") or "running",
        "summary_metrics": payload.get("summary_metrics") or {},
    }
    return _first_row(supabase.table("evaluation_runs").insert(row).execute())


def record_evaluation_result(
    supabase: Any,
    run_id: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    run = _first_row(
        supabase.table("evaluation_runs").select(
            "model, prompt_version, rubric_version"
        ).eq("id", run_id).single().execute()
    )
    if not run:
        raise ValueError("evaluation run not found")

    example = _first_row(
        supabase.table("evaluation_examples").select("*").eq(
            "id",
            payload["example_id"],
        ).single().execute()
    )
    if not example:
        raise ValueError("evaluation example not found")

    comparison = compare_prediction(example, payload)
    row = {
        "run_id": run_id,
        "example_id": payload["example_id"],
        "diagnostic_id": payload.get("diagnostic_id"),
        "model": run.get("model"),
        "prompt_version": run.get("prompt_version"),
        "rubric_version": run.get("rubric_version"),
        "predicted_pathway": payload.get("predicted_pathway"),
        "predicted_german_level": payload.get("predicted_german_level"),
        "predicted_timeline": payload.get("predicted_timeline"),
        "predicted_flags": payload.get("predicted_flags") or [],
        "score": payload.get("score", comparison["score"]),
        "passed": payload.get("passed", comparison["passed"]),
        "error_type": payload.get("error_type"),
        "latency_ms": payload.get("latency_ms", 0),
        "input_tokens": payload.get("input_tokens", 0),
        "output_tokens": payload.get("output_tokens", 0),
        "estimated_cost": payload.get("estimated_cost", 0),
        "notes": redact_direct_identifiers(payload.get("notes")),
    }
    inserted = _first_row(supabase.table("evaluation_results").insert(row).execute())
    update_run_summary_metrics(supabase, run_id)
    return inserted


def fetch_results_with_expectations(supabase: Any, run_id: str) -> list[dict[str, Any]]:
    result = supabase.table("evaluation_results").select(
        "*, evaluation_examples(expected_pathway, expected_german_level, expected_timeline, expected_flags)"
    ).eq("run_id", run_id).execute()
    rows = result.data or []
    flattened = []
    for row in rows:
        example = row.get("evaluation_examples") or {}
        comparison = compare_prediction(example, row)
        flattened.append({
            **row,
            "expected_pathway": example.get("expected_pathway"),
            "expected_german_level": example.get("expected_german_level"),
            "expected_timeline": example.get("expected_timeline"),
            "expected_flags": example.get("expected_flags"),
            "flag_recall": comparison["flag_recall"],
        })
    return flattened


def update_run_summary_metrics(supabase: Any, run_id: str) -> dict[str, Any]:
    results = fetch_results_with_expectations(supabase, run_id)
    metrics = calculate_summary_metrics(results)
    supabase.table("evaluation_runs").update({
        "summary_metrics": metrics,
    }).eq("id", run_id).execute()
    return metrics


def complete_evaluation_run(supabase: Any, run_id: str) -> dict[str, Any]:
    metrics = update_run_summary_metrics(supabase, run_id)
    return _first_row(
        supabase.table("evaluation_runs").update({
            "summary_metrics": metrics,
            "completed_at": utc_now_iso(),
            "status": "completed",
        }).eq("id", run_id).execute()
    )


def get_evaluation_run_report(supabase: Any, run_id: str) -> dict[str, Any]:
    from services.statistical_evaluation import get_latest_statistical_comparison_for_run

    run = _first_row(
        supabase.table("evaluation_runs").select(
            "*, evaluation_datasets(name, version)"
        ).eq("id", run_id).single().execute()
    )
    if not run:
        raise ValueError("evaluation run not found")

    dataset = run.get("evaluation_datasets") or {}
    examples = supabase.table("evaluation_examples").select(
        "id",
        count="exact",
    ).eq("dataset_id", run.get("dataset_id")).execute()
    results = fetch_results_with_expectations(supabase, run_id)
    metrics = calculate_summary_metrics(results)

    return {
        "run": run,
        "dataset_name": dataset.get("name"),
        "dataset_version": dataset.get("version"),
        "number_of_examples": examples.count or 0,
        "model": run.get("model"),
        "prompt_version": run.get("prompt_version"),
        "rubric_version": run.get("rubric_version"),
        "pathway_accuracy": metrics["pathway_accuracy"],
        "german_level_accuracy": metrics["german_level_accuracy"],
        "timeline_accuracy": metrics["timeline_accuracy"],
        "flag_recall": metrics["flag_recall"],
        "overall_pass_rate": metrics["overall_pass_rate"],
        "average_score": metrics["average_score"],
        "average_latency_ms": metrics["average_latency_ms"],
        "average_cost": metrics["average_cost_per_evaluated_example"],
        "statistical_comparison": get_latest_statistical_comparison_for_run(
            supabase,
            run_id,
        ),
        "results": results,
    }


def get_evaluation_summary(supabase: Any) -> dict[str, Any]:
    from services.statistical_evaluation import get_latest_experiment_summary

    datasets = supabase.table("evaluation_datasets").select("*").eq(
        "active",
        True,
    ).execute()
    examples = supabase.table("evaluation_examples").select("id", count="exact").execute()
    runs = supabase.table("evaluation_runs").select("*").order(
        "started_at",
        desc=True,
    ).limit(10).execute()

    latest_run = (runs.data or [None])[0]
    latest_metrics = latest_run.get("summary_metrics") if latest_run else {}
    return {
        "active_datasets": len(datasets.data or []),
        "total_examples": examples.count or 0,
        "latest_run": latest_run,
        "latest_metrics": latest_metrics or {},
        "recent_runs": runs.data or [],
        "latest_experiment": get_latest_experiment_summary(supabase),
    }
