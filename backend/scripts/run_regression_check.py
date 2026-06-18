#!/usr/bin/env python3
"""
Manual regression gate for UC-01 diagnostic quality.

IMPORTANT: This script is NOT wired into CI. It calls the live Anthropic API and costs
money (~$0.90–1.80 per run for 18 examples at Sonnet 4.6 pricing). Run it manually before
promoting a prompt change to production. Add `--baseline-run-id` to compare against a
specific previous run; omit it to compare against the most recent completed run.

When to run:
  1. Before merging any prompt change to the SYSTEM_PROMPT in germany_diagnostic.py.
  2. After updating OVERALL_SCORE_TOLERANCE or the scoring rubric weights.
  3. After any change to DiagnosticAIOutput schema fields.

Usage:
    # Run against default seed dataset, compare to most recent completed run
    python scripts/run_regression_check.py

    # Compare to a specific baseline run
    python scripts/run_regression_check.py --baseline-run-id <uuid>

    # Override pass thresholds (defaults: accuracy>=0.9, latency_ms<=8000)
    python scripts/run_regression_check.py --min-accuracy 0.85 --max-latency-ms 10000

Exit code:
  0 — regression gate passed (new run meets or exceeds baseline on all metrics)
  1 — regression gate failed (see output for which metrics regressed)
  2 — baseline not found or insufficient data for comparison

NOTE: This script intentionally does NOT call run_evaluation.py's --dry-run mode.
Dry-run results are useful for infrastructure smoke-testing but not for quality
regression because FakeAnthropicClient returns deterministic expected values.
Only --live results reflect actual model behavior.
"""
from __future__ import annotations

import argparse
import os
import sys


METRIC_THRESHOLDS = {
    "pathway_accuracy": (">=", 0.90),
    "german_level_accuracy": (">=", 0.90),
    "timeline_accuracy": (">=", 0.90),
    "overall_pass_rate": (">=", 0.80),
    "average_latency_ms": ("<=", 8000),
}

REGRESSION_RELATIVE_TOLERANCE = 0.05


def _load_run_metrics(supabase, run_id: str) -> dict | None:
    result = (
        supabase.table("evaluation_runs")
        .select("id, summary_metrics, completed_at, status, run_type")
        .eq("id", run_id)
        .single()
        .execute()
    )
    rows = result.data or {}
    if isinstance(rows, list):
        return rows[0] if rows else None
    return rows or None


def _find_latest_live_run(supabase, dataset_id: str | None) -> dict | None:
    query = (
        supabase.table("evaluation_runs")
        .select("id, summary_metrics, completed_at, status, run_type")
        .eq("status", "completed")
        .eq("run_type", "live")
        .order("completed_at", desc=True)
        .limit(1)
    )
    if dataset_id:
        query = query.eq("dataset_id", dataset_id)
    result = query.execute()
    rows = result.data or []
    return rows[0] if rows else None


def _check_absolute_thresholds(metrics: dict) -> list[str]:
    failures = []
    for metric, (op, threshold) in METRIC_THRESHOLDS.items():
        value = metrics.get(metric)
        if value is None:
            continue
        if op == ">=" and value < threshold:
            failures.append(
                f"  {metric}: {value:.4f} < minimum {threshold:.4f}"
            )
        elif op == "<=" and value > threshold:
            failures.append(
                f"  {metric}: {value:.1f} > maximum {threshold:.1f}ms"
            )
    return failures


def _check_regression_vs_baseline(
    new_metrics: dict,
    baseline_metrics: dict,
) -> list[str]:
    regressions = []
    for metric in (
        "pathway_accuracy",
        "german_level_accuracy",
        "timeline_accuracy",
        "overall_pass_rate",
        "average_score",
    ):
        new_val = new_metrics.get(metric)
        base_val = baseline_metrics.get(metric)
        if new_val is None or base_val is None or base_val == 0:
            continue
        drop = base_val - new_val
        if drop > REGRESSION_RELATIVE_TOLERANCE:
            regressions.append(
                f"  {metric}: {new_val:.4f} (was {base_val:.4f}, dropped {drop:.4f} > tolerance {REGRESSION_RELATIVE_TOLERANCE})"
            )
    # Latency increase is a regression if >20% worse
    new_lat = new_metrics.get("average_latency_ms")
    base_lat = baseline_metrics.get("average_latency_ms")
    if new_lat and base_lat and base_lat > 0:
        pct_increase = (new_lat - base_lat) / base_lat
        if pct_increase > 0.20:
            regressions.append(
                f"  average_latency_ms: {new_lat:.0f}ms (was {base_lat:.0f}ms, +{pct_increase*100:.0f}% > 20% tolerance)"
            )
    return regressions


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Manual regression gate — runs a live eval and compares to baseline.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--baseline-run-id",
        help="UUID of the run to compare against. Defaults to most recent completed live run.",
    )
    parser.add_argument(
        "--dataset-id",
        help="Dataset UUID. Defaults to uc01_diagnostic_seed_v1 v1.",
    )
    parser.add_argument(
        "--min-accuracy",
        type=float,
        default=0.90,
        help="Minimum acceptable accuracy for routing fields (default: 0.90).",
    )
    parser.add_argument(
        "--max-latency-ms",
        type=float,
        default=8000.0,
        help="Maximum acceptable average latency in ms (default: 8000).",
    )
    parser.add_argument(
        "--skip-live-run",
        action="store_true",
        help=(
            "Compare two existing runs without triggering a new live run. "
            "Requires --baseline-run-id and --new-run-id."
        ),
    )
    parser.add_argument(
        "--new-run-id",
        help="UUID of the already-completed run to treat as 'new'. Used with --skip-live-run.",
    )
    args = parser.parse_args()

    METRIC_THRESHOLDS["pathway_accuracy"] = (">=", args.min_accuracy)
    METRIC_THRESHOLDS["german_level_accuracy"] = (">=", args.min_accuracy)
    METRIC_THRESHOLDS["timeline_accuracy"] = (">=", args.min_accuracy)
    METRIC_THRESHOLDS["average_latency_ms"] = ("<=", args.max_latency_ms)

    here = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.dirname(here))

    from dotenv import load_dotenv
    load_dotenv()

    from database import get_supabase
    supabase = get_supabase()

    # Resolve dataset ID
    dataset_id = args.dataset_id
    if not dataset_id:
        result = (
            supabase.table("evaluation_datasets")
            .select("id")
            .eq("name", "uc01_diagnostic_seed_v1")
            .eq("version", "1")
            .execute()
        )
        rows = result.data or []
        if rows:
            dataset_id = rows[0]["id"]

    # Get or run the "new" evaluation
    if args.skip_live_run:
        if not args.new_run_id:
            print("[ERROR] --skip-live-run requires --new-run-id", file=sys.stderr)
            sys.exit(2)
        new_run = _load_run_metrics(supabase, args.new_run_id)
        if not new_run:
            print(f"[ERROR] Run {args.new_run_id} not found.", file=sys.stderr)
            sys.exit(2)
        print(f"[gate] Using existing run {args.new_run_id} as 'new' result.")
    else:
        print("=" * 60)
        print("REGRESSION GATE — Live API Run")
        print("This will call the Anthropic API for every seed example.")
        print("Estimated cost: ~$0.90–1.80 for 18 examples (Sonnet 4.6).")
        print("=" * 60)
        confirm = input("Type 'yes' to proceed: ").strip().lower()
        if confirm != "yes":
            print("Aborted.")
            sys.exit(0)

        from scripts.run_evaluation import run_evaluation
        result = run_evaluation(
            supabase,
            dataset_id,
            dry_run=False,
            run_type="regression_gate",
            verbose=True,
        )
        new_run = _load_run_metrics(supabase, result["run_id"])

    new_metrics = (new_run or {}).get("summary_metrics") or {}
    print(f"\n[gate] New run metrics: {new_metrics}")

    # Get baseline
    if args.baseline_run_id:
        baseline_run = _load_run_metrics(supabase, args.baseline_run_id)
        if not baseline_run:
            print(f"[ERROR] Baseline run {args.baseline_run_id} not found.", file=sys.stderr)
            sys.exit(2)
    else:
        # Exclude the current new run from the baseline search
        new_run_id = (new_run or {}).get("id")
        baseline_run = _find_latest_live_run(supabase, dataset_id)
        if baseline_run and baseline_run.get("id") == new_run_id:
            # The new run IS the most recent — look for the second most recent
            result2 = (
                supabase.table("evaluation_runs")
                .select("id, summary_metrics, completed_at, status, run_type")
                .eq("status", "completed")
                .neq("id", new_run_id)
                .in_("run_type", ["live", "regression_gate"])
                .order("completed_at", desc=True)
                .limit(1)
                .execute()
            )
            rows2 = result2.data or []
            baseline_run = rows2[0] if rows2 else None

    if not baseline_run:
        print("[gate] No baseline run found — skipping regression comparison.")
        print("[gate] Checking absolute thresholds only.")
        failures = _check_absolute_thresholds(new_metrics)
        if failures:
            print("[gate] FAIL — absolute threshold violations:")
            for f in failures:
                print(f)
            sys.exit(1)
        print("[gate] PASS — all absolute thresholds met. (No baseline for delta comparison.)")
        sys.exit(0)

    baseline_metrics = baseline_run.get("summary_metrics") or {}
    print(f"[gate] Baseline run {baseline_run.get('id')} ({baseline_run.get('completed_at', '')[:10]}):")
    print(f"       metrics: {baseline_metrics}")

    failures = _check_absolute_thresholds(new_metrics)
    regressions = _check_regression_vs_baseline(new_metrics, baseline_metrics)

    all_problems = failures + regressions
    if all_problems:
        print("\n[gate] FAIL — regression or threshold violations detected:")
        for p in all_problems:
            print(p)
        sys.exit(1)

    print("\n[gate] PASS — no regressions detected, all absolute thresholds met.")
    sys.exit(0)


if __name__ == "__main__":
    main()
