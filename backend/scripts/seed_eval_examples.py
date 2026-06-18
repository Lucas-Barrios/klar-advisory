#!/usr/bin/env python3
"""
Seed eval examples into evaluation_examples (+ evaluation_datasets if needed).

Fixes from original version:
  - Table was "eval_examples" → now "evaluation_examples" (FK to evaluation_datasets)
  - Raw student profiles are now reshaped to the correct evaluation example shape
  - dataset_id is required (NOT NULL FK); we create or reuse a dataset row first
  - Inserts route through add_evaluation_example() for PII sanitisation and audit trail

Usage:
    # Print JSON to stdout (default, no DB writes)
    python scripts/seed_eval_examples.py

    # Write JSONL to a file
    python scripts/seed_eval_examples.py --output eval_seed.jsonl

    # Insert into Supabase (requires SUPABASE_URL + SUPABASE_KEY env vars)
    python scripts/seed_eval_examples.py --insert-db

    # Insert into Supabase and print verbose per-row output
    python scripts/seed_eval_examples.py --insert-db --verbose
"""
import argparse
import json
import os
import sys

# Each example has:
#   input_payload — the safe (non-PII) student profile fields
#   expected_* — the ground-truth labels for evaluation comparison
#   source — traceability tag
#   reviewed_by_human — True for manually curated examples

EXAMPLES = [
    # 1. Strong ausbildung candidate — high scores expected
    {
        "input_payload": {
            "country": "Mexico",
            "pathway": "ausbildung",
            "german_level": "B2",
            "english_level": "C1",
            "education_level": "bachelor",
            "field_of_study": "Mechanical Engineering",
            "work_experience_years": 3,
            "timeline": "1_year",
            "financial_situation": "I have €5,000 saved and can secure more through family support.",
        },
        "expected_pathway": "ausbildung",
        "expected_german_level": "B2",
        "expected_timeline": "1_year",
        "expected_flags": [],
        "source": "manual_seed_v1",
        "reviewed_by_human": True,
    },
    # 2. Low German proficiency — language_gap flag expected
    {
        "input_payload": {
            "country": "Colombia",
            "pathway": "ausbildung",
            "german_level": "A1",
            "english_level": "B1",
            "education_level": "high_school",
            "field_of_study": "General Studies",
            "work_experience_years": 1,
            "timeline": "6_months",
            "financial_situation": "Limited savings, need funded options.",
        },
        "expected_pathway": "ausbildung",
        "expected_german_level": "A1",
        "expected_timeline": "6_months",
        "expected_flags": ["language_gap", "timeline_too_tight"],
        "source": "manual_seed_v1",
        "reviewed_by_human": True,
    },
    # 3. Borderline B1, ausbildung — moderate scores expected
    {
        "input_payload": {
            "country": "Peru",
            "pathway": "ausbildung",
            "german_level": "B1",
            "english_level": "B2",
            "education_level": "associate",
            "field_of_study": "Nursing",
            "work_experience_years": 2,
            "timeline": "1_year",
            "financial_situation": "I have €2,000 and expect family support.",
        },
        "expected_pathway": "ausbildung",
        "expected_german_level": "B1",
        "expected_timeline": "1_year",
        "expected_flags": [],
        "source": "manual_seed_v1",
        "reviewed_by_human": True,
    },
    # 4. Incomplete financial info — finance_risk flag expected
    {
        "input_payload": {
            "country": "Brazil",
            "pathway": "ausbildung",
            "german_level": "B1",
            "english_level": "B1",
            "education_level": "bachelor",
            "field_of_study": "Computer Science",
            "work_experience_years": 4,
            "timeline": "2_years_plus",
        },
        "expected_pathway": "ausbildung",
        "expected_german_level": "B1",
        "expected_timeline": "2_years_plus",
        "expected_flags": ["finance_risk"],
        "source": "manual_seed_v1",
        "reviewed_by_human": False,
    },
    # 5. Strong university candidate
    {
        "input_payload": {
            "country": "Argentina",
            "pathway": "university",
            "german_level": "C1",
            "english_level": "C2",
            "education_level": "bachelor",
            "field_of_study": "Economics",
            "work_experience_years": 2,
            "timeline": "1_year",
            "financial_situation": "I have a €15,000 blocked account ready.",
        },
        "expected_pathway": "university",
        "expected_german_level": "C1",
        "expected_timeline": "1_year",
        "expected_flags": [],
        "source": "manual_seed_v1",
        "reviewed_by_human": True,
    },
    # 6. University — low German, 6-month timeline (unrealistic combo)
    {
        "input_payload": {
            "country": "Chile",
            "pathway": "university",
            "german_level": "A2",
            "english_level": "B2",
            "education_level": "bachelor",
            "field_of_study": "Architecture",
            "work_experience_years": 1,
            "timeline": "6_months",
            "financial_situation": "I have €5,000 saved.",
        },
        "expected_pathway": "university",
        "expected_german_level": "A2",
        "expected_timeline": "6_months",
        "expected_flags": ["language_gap", "timeline_too_tight"],
        "source": "manual_seed_v1",
        "reviewed_by_human": True,
    },
    # 7. Work visa — experienced professional
    {
        "input_payload": {
            "country": "Venezuela",
            "pathway": "work_visa",
            "german_level": "B1",
            "english_level": "C1",
            "education_level": "master",
            "field_of_study": "Software Engineering",
            "work_experience_years": 8,
            "timeline": "1_year",
            "financial_situation": "Stable income, €10,000 in savings.",
        },
        "expected_pathway": "work_visa",
        "expected_german_level": "B1",
        "expected_timeline": "1_year",
        "expected_flags": [],
        "source": "manual_seed_v1",
        "reviewed_by_human": True,
    },
    # 8. Healthcare ausbildung — low German (patient-facing requires B2)
    {
        "input_payload": {
            "country": "Brazil",
            "pathway": "ausbildung",
            "german_level": "A2",
            "english_level": "B1",
            "education_level": "associate",
            "field_of_study": "Nursing",
            "work_experience_years": 3,
            "timeline": "2_years_plus",
            "financial_situation": "Minimal savings, need fully funded program.",
        },
        "expected_pathway": "ausbildung",
        "expected_german_level": "A2",
        "expected_timeline": "2_years_plus",
        "expected_flags": ["language_gap"],
        "source": "manual_seed_v1",
        "reviewed_by_human": True,
    },
    # 9. IT ausbildung — borderline German
    {
        "input_payload": {
            "country": "Mexico",
            "pathway": "ausbildung",
            "german_level": "B1",
            "english_level": "C1",
            "education_level": "bachelor",
            "field_of_study": "Information Technology",
            "work_experience_years": 2,
            "timeline": "1_year",
            "financial_situation": "€4,000 in savings, open to apprenticeship stipend.",
        },
        "expected_pathway": "ausbildung",
        "expected_german_level": "B1",
        "expected_timeline": "1_year",
        "expected_flags": [],
        "source": "manual_seed_v1",
        "reviewed_by_human": True,
    },
    # 10. Minimal profile (no field_of_study, no financial info, 0 work exp)
    {
        "input_payload": {
            "country": "Ecuador",
            "pathway": "ausbildung",
            "german_level": "A1",
            "english_level": "A2",
            "education_level": "high_school",
            "work_experience_years": 0,
            "timeline": "2_years_plus",
        },
        "expected_pathway": "ausbildung",
        "expected_german_level": "A1",
        "expected_timeline": "2_years_plus",
        "expected_flags": ["language_gap", "finance_risk"],
        "source": "manual_seed_v1",
        "reviewed_by_human": False,
    },
    # 11. Hospitality ausbildung — A2 German (kitchen roles sometimes acceptable)
    {
        "input_payload": {
            "country": "Guatemala",
            "pathway": "ausbildung",
            "german_level": "A2",
            "english_level": "B1",
            "education_level": "high_school",
            "field_of_study": "Culinary Arts",
            "work_experience_years": 2,
            "timeline": "1_year",
            "financial_situation": "Limited savings, need part-time income.",
        },
        "expected_pathway": "ausbildung",
        "expected_german_level": "A2",
        "expected_timeline": "1_year",
        "expected_flags": ["language_gap"],
        "source": "manual_seed_v1",
        "reviewed_by_human": False,
    },
    # 12. University — missing blocked account funds
    {
        "input_payload": {
            "country": "Bolivia",
            "pathway": "university",
            "german_level": "B2",
            "english_level": "C1",
            "education_level": "bachelor",
            "field_of_study": "Medicine",
            "work_experience_years": 0,
            "timeline": "1_year",
            "financial_situation": "I have €3,000, cannot afford the €11,000 blocked account yet.",
        },
        "expected_pathway": "university",
        "expected_german_level": "B2",
        "expected_timeline": "1_year",
        "expected_flags": ["finance_risk"],
        "source": "manual_seed_v1",
        "reviewed_by_human": True,
    },
    # 13. Mechatronics ausbildung — strong fit
    {
        "input_payload": {
            "country": "Colombia",
            "pathway": "ausbildung",
            "german_level": "B2",
            "english_level": "B1",
            "education_level": "associate",
            "field_of_study": "Mechatronics",
            "work_experience_years": 4,
            "timeline": "1_year",
            "financial_situation": "Comfortable with €7,000 saved.",
        },
        "expected_pathway": "ausbildung",
        "expected_german_level": "B2",
        "expected_timeline": "1_year",
        "expected_flags": [],
        "source": "manual_seed_v1",
        "reviewed_by_human": True,
    },
    # 14. Experienced professional, work visa, 20 years experience
    {
        "input_payload": {
            "country": "Argentina",
            "pathway": "work_visa",
            "german_level": "B1",
            "english_level": "B2",
            "education_level": "master",
            "field_of_study": "Healthcare Administration",
            "work_experience_years": 20,
            "timeline": "2_years_plus",
            "financial_situation": "Stable, €12,000 in savings.",
        },
        "expected_pathway": "work_visa",
        "expected_german_level": "B1",
        "expected_timeline": "2_years_plus",
        "expected_flags": [],
        "source": "manual_seed_v1",
        "reviewed_by_human": True,
    },
    # 15. Ceiling calibration — perfect candidate
    {
        "input_payload": {
            "country": "Chile",
            "pathway": "ausbildung",
            "german_level": "C2",
            "english_level": "C2",
            "education_level": "master",
            "field_of_study": "Industrial Engineering",
            "work_experience_years": 10,
            "timeline": "2_years_plus",
            "financial_situation": "€25,000 saved, fully self-funded.",
        },
        "expected_pathway": "ausbildung",
        "expected_german_level": "C2",
        "expected_timeline": "2_years_plus",
        "expected_flags": [],
        "source": "manual_seed_v1",
        "reviewed_by_human": True,
    },
    # 16. EU citizen — documentation score should be easy
    {
        "input_payload": {
            "country": "Spain",
            "pathway": "ausbildung",
            "german_level": "B2",
            "english_level": "C1",
            "education_level": "bachelor",
            "field_of_study": "Electrical Engineering",
            "work_experience_years": 3,
            "timeline": "1_year",
            "financial_situation": "€6,000 in savings.",
        },
        "expected_pathway": "ausbildung",
        "expected_german_level": "B2",
        "expected_timeline": "1_year",
        "expected_flags": [],
        "source": "manual_seed_v1",
        "reviewed_by_human": True,
    },
    # 17. Non-standard field — tests generalisation
    {
        "input_payload": {
            "country": "Peru",
            "pathway": "ausbildung",
            "german_level": "B1",
            "english_level": "B2",
            "education_level": "bachelor",
            "field_of_study": "Marine Biology",
            "work_experience_years": 1,
            "timeline": "1_year",
            "financial_situation": "€3,500 saved.",
        },
        "expected_pathway": "ausbildung",
        "expected_german_level": "B1",
        "expected_timeline": "1_year",
        "expected_flags": [],
        "source": "manual_seed_v1",
        "reviewed_by_human": False,
    },
    # 18. Long financial text — input length stress test
    {
        "input_payload": {
            "country": "Mexico",
            "pathway": "ausbildung",
            "german_level": "B1",
            "english_level": "B1",
            "education_level": "bachelor",
            "field_of_study": "Accounting",
            "work_experience_years": 5,
            "timeline": "1_year",
            "financial_situation": (
                "I currently have €8,000 in savings and am expecting a bonus from my current employer "
                "in Q3 worth approximately €3,000 after tax. My parents have agreed to provide up to "
                "€5,000 as a one-time gift. I also have a small rental income of €200/month from a "
                "property I co-own with my brother. I have no debts. My monthly expenses in my current "
                "country are €700. I am open to apprenticeship stipends and working part-time during "
                "language course. I do not expect to need external loans if I am accepted into an "
                "Ausbildung program, since the monthly stipend would cover living costs."
            ),
        },
        "expected_pathway": "ausbildung",
        "expected_german_level": "B1",
        "expected_timeline": "1_year",
        "expected_flags": [],
        "source": "manual_seed_v1",
        "reviewed_by_human": False,
    },
]

DATASET_PAYLOAD = {
    "name": "uc01_diagnostic_seed_v1",
    "version": "1",
    "use_case": "uc01_germany_diagnostic",
    "description": "18 hand-labelled student profiles for UC-01 prompt regression testing.",
    "active": True,
}


def _get_or_create_dataset(supabase) -> str:
    """Return dataset_id for the seed dataset, creating it if it doesn't exist."""
    existing = (
        supabase.table("evaluation_datasets")
        .select("id")
        .eq("name", DATASET_PAYLOAD["name"])
        .eq("version", DATASET_PAYLOAD["version"])
        .execute()
    )
    rows = existing.data or []
    if rows:
        return rows[0]["id"]

    from services.evaluation import create_evaluation_dataset
    row = create_evaluation_dataset(supabase, DATASET_PAYLOAD)
    return row["id"]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed evaluation examples for Klar UC-01 diagnostic prompt testing."
    )
    parser.add_argument("--output", metavar="FILE", help="Write JSONL to this file instead of stdout.")
    parser.add_argument("--insert-db", action="store_true", help="Insert into Supabase via add_evaluation_example().")
    parser.add_argument("--verbose", action="store_true", help="Print per-row output when inserting.")
    args = parser.parse_args()

    if args.insert_db:
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from database import get_supabase
        from services.evaluation import add_evaluation_example

        supabase = get_supabase()
        dataset_id = _get_or_create_dataset(supabase)
        print(f"Dataset: {DATASET_PAYLOAD['name']} v{DATASET_PAYLOAD['version']} → id={dataset_id}")

        inserted = 0
        failed = 0
        for i, ex in enumerate(EXAMPLES, start=1):
            payload = {**ex, "dataset_id": dataset_id}
            try:
                row = add_evaluation_example(supabase, payload)
                inserted += 1
                if args.verbose:
                    print(f"  [{i:02d}] OK  id={row.get('id')} pathway={ex.get('expected_pathway')} german={ex.get('expected_german_level')}")
            except Exception as e:
                failed += 1
                print(f"  [{i:02d}] FAIL {type(e).__name__}: {e}", file=sys.stderr)

        print(f"\nInserted {inserted}/{len(EXAMPLES)} examples. Failed: {failed}.")
        if failed:
            sys.exit(1)
        return

    # Default: print JSON to stdout
    lines = []
    for ex in EXAMPLES:
        lines.append(json.dumps(ex, ensure_ascii=False))

    output = "\n".join(lines) + "\n"

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Wrote {len(EXAMPLES)} examples to {args.output}.")
    else:
        sys.stdout.write(output)


if __name__ == "__main__":
    main()
