#!/usr/bin/env python3
"""
Push evaluation_examples rows from Supabase to a LangSmith Dataset.

Each row is mapped as:
  inputs  → input_payload (the sanitised student profile)
  outputs → expected_pathway, expected_german_level, expected_timeline,
             expected_flags, expected_summary_notes

Usage:
    python scripts/push_to_langsmith.py [--dataset-name NAME] [--dry-run]

Requires:
    SUPABASE_URL, SUPABASE_KEY  — Supabase credentials
    LANGSMITH_API_KEY           — LangSmith credentials
    LANGSMITH_TRACING           — set to "true" (or just LANGSMITH_API_KEY is enough for SDK use)
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

DEFAULT_DATASET_NAME = "klar-uc01-diagnostic"
DEFAULT_DATASET_DESCRIPTION = (
    "Klar Advisory UC-01 Germany Readiness Diagnostic evaluation examples. "
    "Each example is a sanitised (non-PII) student profile mapped to expected "
    "pathway, German level, timeline, and flag labels."
)


def fetch_evaluation_examples(supabase) -> list[dict]:
    result = (
        supabase.table("evaluation_examples")
        .select(
            "id, input_payload, expected_pathway, expected_german_level, "
            "expected_timeline, expected_flags, expected_summary_notes, "
            "source, reviewed_by_human"
        )
        .order("created_at")
        .execute()
    )
    return result.data or []


def build_langsmith_example(row: dict) -> tuple[dict, dict]:
    inputs = row.get("input_payload") or {}
    outputs = {
        "expected_pathway": row.get("expected_pathway"),
        "expected_german_level": row.get("expected_german_level"),
        "expected_timeline": row.get("expected_timeline"),
        "expected_flags": row.get("expected_flags") or [],
        "expected_summary_notes": row.get("expected_summary_notes"),
    }
    return inputs, outputs


def push_to_langsmith(
    rows: list[dict],
    *,
    dataset_name: str,
    dry_run: bool = False,
) -> None:
    from langsmith import Client

    print(f"Found {len(rows)} evaluation examples.")

    if dry_run:
        for i, row in enumerate(rows, start=1):
            inputs, outputs = build_langsmith_example(row)
            print(f"[{i:02d}] inputs={json.dumps(inputs)[:80]}... outputs={list(outputs.keys())}")
        print("\n[dry-run] No data pushed to LangSmith.")
        return

    ls_client = Client()

    # Get or create dataset
    existing = list(ls_client.list_datasets(dataset_name=dataset_name))
    if existing:
        dataset = existing[0]
        print(f"Using existing LangSmith dataset: '{dataset_name}' (id={dataset.id})")
    else:
        dataset = ls_client.create_dataset(
            dataset_name=dataset_name,
            description=DEFAULT_DATASET_DESCRIPTION,
        )
        print(f"Created LangSmith dataset: '{dataset_name}' (id={dataset.id})")

    pushed = 0
    failed = 0
    for i, row in enumerate(rows, start=1):
        inputs, outputs = build_langsmith_example(row)
        try:
            ls_client.create_example(
                inputs=inputs,
                outputs=outputs,
                dataset_id=dataset.id,
                metadata={
                    "supabase_id": row.get("id"),
                    "source": row.get("source"),
                    "reviewed_by_human": row.get("reviewed_by_human"),
                },
            )
            pushed += 1
            print(
                f"  [{i:02d}] OK  pathway={outputs['expected_pathway']}"
                f"  german={outputs['expected_german_level']}"
            )
        except Exception as exc:
            failed += 1
            print(f"  [{i:02d}] FAIL {type(exc).__name__}: {exc}", file=sys.stderr)

    print(f"\nPushed {pushed}/{len(rows)} examples to LangSmith dataset '{dataset_name}'.")
    if failed:
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Push Supabase evaluation_examples to a LangSmith dataset."
    )
    parser.add_argument(
        "--dataset-name",
        default=DEFAULT_DATASET_NAME,
        help=f"LangSmith dataset name (default: {DEFAULT_DATASET_NAME})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be pushed without actually calling LangSmith.",
    )
    args = parser.parse_args()

    from database import get_supabase

    supabase = get_supabase()
    rows = fetch_evaluation_examples(supabase)

    if not rows:
        print("No evaluation examples found in Supabase. Run seed_eval_examples.py --insert-db first.")
        sys.exit(1)

    push_to_langsmith(rows, dataset_name=args.dataset_name, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
