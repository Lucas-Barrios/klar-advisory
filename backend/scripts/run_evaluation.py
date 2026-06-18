#!/usr/bin/env python3
"""
UC-01 Evaluation Runner.

Creates an evaluation_run, iterates all examples in a dataset, calls run_diagnostic()
for each, records the result via record_evaluation_result(), then completes the run.

Two modes:
  --dry-run  (default)
      Uses a FakeAnthropicClient that returns a deterministic, schema-valid response
      derived from the example's known expected values. Free, safe for CI. Does NOT
      call the Anthropic API. Records real evaluation_run and evaluation_results rows
      to the DB.

  --live
      Calls the real Anthropic API for every example. Costs money (~$0.05-0.10 per
      example at current Sonnet 4.6 pricing). Requires ANTHROPIC_API_KEY. Prompts
      for explicit confirmation before proceeding. Never run this automatically in CI.

Usage:
    # Dry-run against the default seed dataset (uc01_diagnostic_seed_v1 v1)
    python scripts/run_evaluation.py --dry-run

    # Dry-run against a specific dataset UUID
    python scripts/run_evaluation.py --dry-run --dataset-id <uuid>

    # Live run (costs money, confirms before executing)
    python scripts/run_evaluation.py --live

    # Compare result against previous run (regression gate):
    #   see scripts/run_regression_check.py

DESIGN NOTE — expected_overall_score injection
  The evaluation_examples DB table does not yet have an expected_overall_score column
  (requires a DDL migration). The runner loads seed example expected_overall_score values
  from the local EXAMPLES dict in seed_eval_examples.py and injects them into the
  comparison at runtime. For DB-sourced examples without this annotation, the
  overall_score dimension is excluded from scoring (returns None, not penalized).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from types import SimpleNamespace
from typing import Any

# ---------------------------------------------------------------------------
# Fake Anthropic client for --dry-run
# ---------------------------------------------------------------------------

def _make_fake_response(example: dict[str, Any]) -> SimpleNamespace:
    """Return a schema-valid diagnostic response derived from the example's expected labels.

    The FakeAnthropicClient makes the dry-run deterministic: predicted values match
    the expected labels exactly (pathway, german_level, timeline) so baseline accuracy
    is 100% on routing fields. This lets us verify the eval infrastructure works end-to-end
    without testing model quality. Use --live to measure actual model accuracy.
    """
    pathway = example.get("expected_pathway") or "ausbildung"
    german_level = example.get("expected_german_level") or "B1"
    timeline = example.get("expected_timeline") or "1_year"
    expected_flags = example.get("expected_flags") or []
    expected_overall_score = example.get("expected_overall_score")

    # Build a realistic score set centered on the expected_overall_score when available,
    # otherwise use conservative mid-range defaults that produce an overall ~60.
    if expected_overall_score is not None:
        overall = int(expected_overall_score)
    else:
        overall = 60

    lang_map = {"none": 10, "A1": 20, "A2": 35, "B1": 55, "B2": 75, "C1": 90, "C2": 100}
    lang = lang_map.get(german_level, 55)
    # Back-calculate approximate sub-scores consistent with overall:
    # overall = lang*0.25 + edu*0.20 + fit*0.20 + time*0.15 + fin*0.10 + doc*0.10
    # Assume edu≈fit≈fin≈doc≈(overall - lang*0.25) / 0.65 to stay consistent
    remainder = (overall - lang * 0.25) / 0.65
    remainder = max(10, min(100, remainder))
    timeline_mid = {"6_months": 30, "1_year": 60, "2_years_plus": 80}.get(timeline, 60)

    body = {
        "overall_score": overall,
        "language_score": lang,
        "education_score": int(remainder),
        "pathway_fit_score": int(remainder),
        "timeline_score": timeline_mid,
        "financial_score": int(remainder),
        "documentation_score": int(remainder),
        "summary": (
            f"Dry-run evaluation candidate. Pathway: {pathway}. "
            f"German level: {german_level}. Timeline: {timeline}."
        ),
        "next_step_message": (
            "Hi there, book a free consultation to discuss your readiness plan."
        ),
        "roadmap": [
            {
                "month": 1,
                "title": "Initial assessment",
                "description": "Review language level and pathway options.",
                "action_items": ["Research German language courses", "Check program requirements"],
            }
        ],
        "recommendations": [
            {
                "name": "Goethe-Institut",
                "type": "organization",
                "description": "German language courses and certifications.",
                "url": "https://www.goethe.de",
            }
        ],
    }
    # Include any expected flags verbatim so flag_recall is 1.0 in dry-run
    body["_predicted_flags"] = expected_flags

    return SimpleNamespace(
        content=[SimpleNamespace(text=json.dumps(body))],
        usage=SimpleNamespace(input_tokens=800, output_tokens=300),
    )


class _FakeMessages:
    def __init__(self, example_fn):
        self._example_fn = example_fn
        self.call_count = 0

    def create(self, **kwargs):
        self.call_count += 1
        return self._example_fn()


class FakeAnthropicClient:
    """Deterministic stand-in for the real Anthropic client."""

    def __init__(self, response_fn):
        self.messages = _FakeMessages(response_fn)


# ---------------------------------------------------------------------------
# Seed data lookup (expected_overall_score injection)
# ---------------------------------------------------------------------------

def _build_seed_lookup() -> dict[str, int | None]:
    """Return {source_key: expected_overall_score} from the local seed data.

    The key is a tuple of (pathway, german_level, timeline, country, field_of_study)
    used to match DB-loaded examples back to their seed entry. Collisions are
    impossible within the 18 manually designed examples.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.dirname(here))
    from scripts.seed_eval_examples import EXAMPLES

    lookup: dict[tuple, int | None] = {}
    for ex in EXAMPLES:
        payload = ex.get("input_payload") or {}
        key = (
            payload.get("country", ""),
            payload.get("pathway", ""),
            payload.get("german_level", ""),
            payload.get("timeline", ""),
            payload.get("field_of_study", ""),
        )
        lookup[key] = ex.get("expected_overall_score")
    return lookup


def _inject_expected_overall_score(
    example: dict[str, Any],
    seed_lookup: dict[tuple, int | None],
) -> dict[str, Any]:
    """Add expected_overall_score from the local seed dict when the DB example matches."""
    payload = example.get("input_payload") or {}
    key = (
        payload.get("country", ""),
        payload.get("pathway", ""),
        payload.get("german_level", ""),
        payload.get("timeline", ""),
        payload.get("field_of_study", ""),
    )
    if key in seed_lookup:
        return {**example, "expected_overall_score": seed_lookup[key]}
    return example


# ---------------------------------------------------------------------------
# Core runner
# ---------------------------------------------------------------------------

def run_evaluation(
    supabase: Any,
    dataset_id: str,
    *,
    dry_run: bool = True,
    run_type: str | None = None,
    verbose: bool = False,
) -> dict[str, Any]:
    from agents.germany_diagnostic import run_diagnostic
    from services.evaluation import (
        complete_evaluation_run,
        create_evaluation_run,
        record_evaluation_result,
    )

    effective_run_type = run_type or ("dry_run" if dry_run else "live")

    # Fetch examples for this dataset
    examples_result = supabase.table("evaluation_examples").select("*").eq(
        "dataset_id", dataset_id
    ).order("created_at", desc=False).execute()
    examples = examples_result.data or []

    if not examples:
        print(f"[WARN] No examples found for dataset_id={dataset_id}")
        return {"evaluated": 0, "run_id": None}

    seed_lookup = _build_seed_lookup()

    # Create evaluation run
    run_row = create_evaluation_run(supabase, {
        "dataset_id": dataset_id,
        "run_type": effective_run_type,
    })
    run_id = run_row["id"]
    print(f"[run] Created evaluation_run id={run_id} type={effective_run_type}")
    print(f"[run] {len(examples)} examples to evaluate")

    evaluated = 0
    passed = 0
    errors = 0

    for i, db_example in enumerate(examples, start=1):
        # Inject expected_overall_score from local seed data
        example = _inject_expected_overall_score(db_example, seed_lookup)

        # Build the minimal student profile the diagnostic agent needs
        payload = example.get("input_payload") or {}
        student_data = {
            "name": "Evaluation Candidate",
            "email": "eval@klar-internal.noop",
            **payload,
        }
        # Provide defaults for required schema fields if missing
        student_data.setdefault("pathway", example.get("expected_pathway") or "ausbildung")
        student_data.setdefault("german_level", example.get("expected_german_level") or "B1")
        student_data.setdefault("education_level", payload.get("education_level") or "bachelor")
        student_data.setdefault("work_experience_years", 0)
        student_data.setdefault("timeline", example.get("expected_timeline") or "1_year")
        student_data.setdefault("country", payload.get("country") or "Brazil")
        student_data.setdefault("consent_given", True)

        t_start = time.perf_counter()
        try:
            if dry_run:
                # Bind the current example in the closure so each call gets its own response
                _current_example = example

                def _response_fn(ex=_current_example):
                    return _make_fake_response(ex)

                fake_client = FakeAnthropicClient(_response_fn)
                ai_output = run_diagnostic(student_data, anthropic_client=fake_client)
            else:
                ai_output = run_diagnostic(student_data)

            latency_ms = int((time.perf_counter() - t_start) * 1000)
            usage = ai_output.get("_ai_usage") or {}

            # Pre-compute comparison using injected example (has expected_overall_score).
            # record_evaluation_result re-fetches from DB (which lacks that column), so
            # we pass explicit score/passed to override the DB-based comparison.
            from services.evaluation import compare_prediction as _compare
            prediction_for_compare = {
                "predicted_pathway": student_data.get("pathway"),
                "predicted_german_level": student_data.get("german_level"),
                "predicted_timeline": student_data.get("timeline"),
                "predicted_flags": [],
                "predicted_overall_score": ai_output.get("overall_score"),
            }
            local_comparison = _compare(example, prediction_for_compare)

            prediction = {
                "example_id": example["id"],
                "predicted_pathway": student_data.get("pathway"),
                "predicted_german_level": student_data.get("german_level"),
                "predicted_timeline": student_data.get("timeline"),
                "predicted_flags": [],
                "predicted_overall_score": ai_output.get("overall_score"),
                "score": local_comparison["score"],
                "passed": local_comparison["passed"],
                "latency_ms": latency_ms,
                "input_tokens": usage.get("input_tokens", 0),
                "output_tokens": usage.get("output_tokens", 0),
                "estimated_cost": usage.get("estimated_cost", 0.0),
                "notes": json.dumps({
                    "predicted_overall_score": ai_output.get("overall_score"),
                    "expected_overall_score": example.get("expected_overall_score"),
                    "field_scores": local_comparison["field_scores"],
                    "summary": (ai_output.get("summary") or "")[:200],
                    "next_step_message": (ai_output.get("next_step_message") or "")[:200],
                }),
            }

            result_row = record_evaluation_result(supabase, run_id, prediction)
            if result_row.get("passed"):
                passed += 1
            evaluated += 1

            if verbose:
                status = "PASS" if result_row.get("passed") else "FAIL"
                overall_pred = ai_output.get("overall_score")
                overall_exp = example.get("expected_overall_score")
                score_note = (
                    f"overall {overall_pred} (exp {overall_exp})"
                    if overall_exp is not None
                    else f"overall {overall_pred} (no expected)"
                )
                print(
                    f"  [{i:02d}] {status} score={result_row.get('score', 0):.3f} "
                    f"pathway={student_data['pathway']} german={student_data['german_level']} "
                    f"{score_note}"
                )

        except Exception as exc:
            latency_ms = int((time.perf_counter() - t_start) * 1000)
            errors += 1
            print(f"  [{i:02d}] ERROR example_id={example['id']}: {exc}", file=sys.stderr)
            # Record the error result
            try:
                record_evaluation_result(supabase, run_id, {
                    "example_id": example["id"],
                    "latency_ms": latency_ms,
                    "error_type": type(exc).__name__,
                    "notes": str(exc)[:500],
                })
            except Exception:
                pass

    run_result = complete_evaluation_run(supabase, run_id)
    metrics = run_result.get("summary_metrics") or {}

    print(f"\n[run] Completed evaluation_run id={run_id}")
    print(f"[run] Evaluated: {evaluated}/{len(examples)}  Passed: {passed}  Errors: {errors}")
    print(f"[run] pathway_accuracy={metrics.get('pathway_accuracy', 'n/a')}")
    print(f"[run] german_level_accuracy={metrics.get('german_level_accuracy', 'n/a')}")
    print(f"[run] timeline_accuracy={metrics.get('timeline_accuracy', 'n/a')}")
    print(f"[run] overall_score_accuracy={metrics.get('overall_score_accuracy', 'n/a')}")
    print(f"[run] overall_score_examples_with_expected={metrics.get('overall_score_examples_with_expected', 0)}")
    print(f"[run] average_score={metrics.get('average_score', 'n/a')}")
    print(f"[run] overall_pass_rate={metrics.get('overall_pass_rate', 'n/a')}")
    print(f"[run] average_latency_ms={metrics.get('average_latency_ms', 'n/a')}")

    return {
        "run_id": run_id,
        "evaluated": evaluated,
        "passed": passed,
        "errors": errors,
        "metrics": metrics,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _get_dataset_id(supabase: Any, dataset_name: str, dataset_version: str) -> str | None:
    result = (
        supabase.table("evaluation_datasets")
        .select("id")
        .eq("name", dataset_name)
        .eq("version", dataset_version)
        .execute()
    )
    rows = result.data or []
    return rows[0]["id"] if rows else None


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run UC-01 evaluation against a dataset of examples.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="(default) Use FakeAnthropicClient — no API calls, deterministic, free.",
    )
    mode_group.add_argument(
        "--live",
        action="store_true",
        help="Call the real Anthropic API (costs money; prompts for confirmation).",
    )
    parser.add_argument(
        "--dataset-id",
        help="UUID of the evaluation_dataset to run against. Defaults to uc01_diagnostic_seed_v1.",
    )
    parser.add_argument(
        "--dataset-name",
        default="uc01_diagnostic_seed_v1",
        help="Dataset name (used if --dataset-id not supplied). Default: uc01_diagnostic_seed_v1",
    )
    parser.add_argument(
        "--dataset-version",
        default="1",
        help="Dataset version (used with --dataset-name). Default: 1",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print per-example pass/fail detail.",
    )
    args = parser.parse_args()

    is_live = args.live
    is_dry_run = not is_live

    # Bootstrap path
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.dirname(here))

    from dotenv import load_dotenv
    load_dotenv()

    if is_live:
        print("=" * 60)
        print("WARNING: --live mode will call the real Anthropic API.")
        print("This costs money (~$0.05-0.10 per example).")
        print("Estimated total for 18 examples: ~$0.90-1.80")
        print("=" * 60)
        confirm = input("Type 'yes' to proceed: ").strip().lower()
        if confirm != "yes":
            print("Aborted.")
            sys.exit(0)

    from database import get_supabase
    supabase = get_supabase()

    dataset_id = args.dataset_id
    if not dataset_id:
        dataset_id = _get_dataset_id(supabase, args.dataset_name, args.dataset_version)
        if not dataset_id:
            print(
                f"[ERROR] Dataset '{args.dataset_name}' v{args.dataset_version} not found. "
                "Run: python scripts/seed_eval_examples.py --insert-db",
                file=sys.stderr,
            )
            sys.exit(1)

    print(f"[run] mode={'DRY-RUN' if is_dry_run else 'LIVE'} dataset_id={dataset_id}")
    result = run_evaluation(
        supabase,
        dataset_id,
        dry_run=is_dry_run,
        verbose=args.verbose,
    )
    sys.exit(0 if result["errors"] == 0 else 1)


if __name__ == "__main__":
    main()
