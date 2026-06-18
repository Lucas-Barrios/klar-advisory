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
#   expected_overall_score — derived by hand from SYSTEM_PROMPT rubric weights:
#       Language 25% + Education 20% + Pathway Fit 20% + Timeline 15% +
#       Financial 10% + Documentation 10%
#     Fixed rubric anchors (SYSTEM_PROMPT):
#       language_score:  none=10, A1=20, A2=35, B1=55, B2=75, C1=90, C2=100
#       timeline_score:  6_months=20-40 (mid≈30), 1_year=50-70 (mid≈60),
#                        2_years_plus=70-90 (mid≈80)
#       documentation:   EU=easy(~88), LATAM+degree=moderate(~58-65),
#                        LATAM-no-degree=complex(~38-42)
#     AI-discretionary (no fixed rubric — best-effort estimates only):
#       education_score, pathway_fit_score, financial_score
#     expected_overall_score is set to None for examples where AI-discretionary
#     dimensions are too uncertain to bound within ±10 points honestly.
#   source — traceability tag
#   reviewed_by_human — True for manually curated examples
#
# IMPORTANT: expected_overall_score is stored only in this in-memory dict.
# The evaluation_examples DB table does not currently have this column (adding it
# requires a DDL migration). The eval runner injects it from this file at runtime;
# the compare_prediction() function reads it from the example dict directly.

EXAMPLES = [
    # 1. Strong ausbildung candidate — high scores expected
    # language=75 (B2), edu≈70, pathway_fit≈75, timeline≈60, financial≈65, doc≈60
    # overall = 75×0.25 + 70×0.20 + 75×0.20 + 60×0.15 + 65×0.10 + 60×0.10
    #         = 18.75 + 14 + 15 + 9 + 6.5 + 6 = 69.25 → 69
    # Confidence: moderate (education/pathway_fit estimates carry ±8 pt uncertainty)
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
        "expected_overall_score": 69,
        "source": "manual_seed_v1",
        "reviewed_by_human": True,
    },
    # 2. Low German proficiency — language_gap flag expected
    # language=20 (A1), edu≈28, pathway_fit≈20, timeline≈30 (6_months mid),
    # financial≈25, doc≈40 (LATAM no degree)
    # overall = 20×0.25 + 28×0.20 + 20×0.20 + 30×0.15 + 25×0.10 + 40×0.10
    #         = 5 + 5.6 + 4 + 4.5 + 2.5 + 4 = 25.6 → 26
    # Confidence: HIGH — all dimensions clearly weak; below 40 with high certainty
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
        "expected_overall_score": 26,
        "source": "manual_seed_v1",
        "reviewed_by_human": True,
    },
    # 3. Borderline B1, ausbildung — moderate scores expected
    # language=55 (B1), edu≈52, pathway_fit≈48 (B1+nursing borderline for patient-facing),
    # timeline≈60, financial≈52, doc≈57
    # overall ≈ 53-54 — BUT pathway_fit for nursing at B1 is highly AI-discretionary
    # (B2 is often required for patient-facing; model may score 40-60 depending on
    # how it interprets "patient-facing" for this specific context).
    # expected_overall_score: null — too uncertain to bound within ±10
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
        "expected_overall_score": None,
        "source": "manual_seed_v1",
        "reviewed_by_human": True,
    },
    # 4. Incomplete financial info — finance_risk flag expected
    # language=55 (B1), edu≈68, pathway_fit≈60, timeline≈80 (2_years_plus mid),
    # financial≈25 (no info provided → flagged finance_risk, model penalizes heavily
    # but the exact penalty magnitude is AI-discretionary)
    # expected_overall_score: null — financial penalty range (15-35) too wide
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
        "expected_overall_score": None,
        "source": "manual_seed_v1",
        "reviewed_by_human": False,
    },
    # 5. Strong university candidate
    # language=90 (C1), edu≈68, pathway_fit≈80, timeline≈60, financial≈88
    # (€15,000 > €11,000 blocked account requirement clearly met → high score),
    # doc≈60 (LATAM with degree)
    # overall = 90×0.25 + 68×0.20 + 80×0.20 + 60×0.15 + 88×0.10 + 60×0.10
    #         = 22.5 + 13.6 + 16 + 9 + 8.8 + 6 = 75.9 → 76
    # Confidence: moderate (education/pathway_fit range ±6 pt)
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
        "expected_overall_score": 76,
        "source": "manual_seed_v1",
        "reviewed_by_human": True,
    },
    # 6. University — low German, 6-month timeline (unrealistic combo)
    # language=35 (A2), edu≈60, pathway_fit≈25 (A2 far below B2 university minimum),
    # timeline≈30 (6_months mid), financial≈25 (€5,000 insufficient for €11,000 needed),
    # doc≈58 (LATAM with degree)
    # overall = 35×0.25 + 60×0.20 + 25×0.20 + 30×0.15 + 25×0.10 + 58×0.10
    #         = 8.75 + 12 + 5 + 4.5 + 2.5 + 5.8 = 38.55 → 39
    # Confidence: moderate — language and financial penalties clear; below 40 likely
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
        "expected_overall_score": 39,
        "source": "manual_seed_v1",
        "reviewed_by_human": True,
    },
    # 7. Work visa — experienced professional
    # language=55 (B1), edu≈85 (master+SE+8yr → excellent), pathway_fit≈82,
    # timeline≈60, financial≈82 (stable+€10,000), doc≈65 (LATAM with master)
    # overall = 55×0.25 + 85×0.20 + 82×0.20 + 60×0.15 + 82×0.10 + 65×0.10
    #         = 13.75 + 17 + 16.4 + 9 + 8.2 + 6.5 = 70.85 → 71
    # Confidence: moderate (experience and education are clear; ±7 pt uncertainty)
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
        "expected_overall_score": 71,
        "source": "manual_seed_v1",
        "reviewed_by_human": True,
    },
    # 8. Healthcare ausbildung — low German (patient-facing requires B2)
    # language=35 (A2), edu≈50, pathway_fit≈28 (A2 for patient-facing nursing → poor),
    # timeline≈80 (2_years_plus mid), financial≈20 (minimal+need fully funded),
    # doc≈55 (LATAM with associate)
    # Countervailing factors: good timeline but weak language, education, and financial.
    # The timeline boost (80×0.15=12) partially offsets language and financial penalties
    # but the result is highly uncertain. expected_overall_score: null
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
        "expected_overall_score": None,
        "source": "manual_seed_v1",
        "reviewed_by_human": True,
    },
    # 9. IT ausbildung — borderline German
    # language=55 (B1), edu≈65, pathway_fit≈65, timeline≈60, financial≈62, doc≈60
    # All dimensions cluster in 55-65 range → overall ≈ 61
    # Too close to the middle; small variations in AI judgment shift ±8 pt easily.
    # expected_overall_score: null
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
        "expected_overall_score": None,
        "source": "manual_seed_v1",
        "reviewed_by_human": True,
    },
    # 10. Minimal profile (no field_of_study, no financial info, 0 work exp)
    # language=20 (A1), edu≈24 (high_school+no field+0yr), pathway_fit≈18,
    # timeline≈80 (2_years_plus mid — only positive factor), financial≈22, doc≈38
    # overall = 20×0.25 + 24×0.20 + 18×0.20 + 80×0.15 + 22×0.10 + 38×0.10
    #         = 5 + 4.8 + 3.6 + 12 + 2.2 + 3.8 = 31.4 → 31
    # Confidence: HIGH — clearly below 40 despite the timeline boost
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
        "expected_overall_score": 31,
        "source": "manual_seed_v1",
        "reviewed_by_human": False,
    },
    # 11. Hospitality ausbildung — A2 German (kitchen roles sometimes acceptable)
    # language=35 (A2), edu≈38 (high_school+culinary+2yr), pathway_fit≈45
    # (kitchen roles may accept A2 but AI judgment varies widely on this),
    # timeline≈60, financial≈30 (limited+need part-time), doc≈42
    # The "kitchen sometimes A2" caveat makes pathway_fit highly AI-discretionary.
    # expected_overall_score: null
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
        "expected_overall_score": None,
        "source": "manual_seed_v1",
        "reviewed_by_human": False,
    },
    # 12. University — missing blocked account funds
    # language=75 (B2), edu≈78 (bachelor+medicine), pathway_fit≈75,
    # timeline≈60, financial≈15 (€3,000 when €11,000 is required → very poor),
    # doc≈60 (LATAM with degree)
    # overall = 75×0.25 + 78×0.20 + 75×0.20 + 60×0.15 + 15×0.10 + 60×0.10
    #         = 18.75 + 15.6 + 15 + 9 + 1.5 + 6 = 65.85 → 66
    # Confidence: moderate — financial penalty is explicit (€3k vs €11k stated);
    # other dims are predictable for medicine+B2
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
        "expected_overall_score": 66,
        "source": "manual_seed_v1",
        "reviewed_by_human": True,
    },
    # 13. Mechatronics ausbildung — strong fit
    # language=75 (B2), edu≈70 (associate+mechatronics+4yr), pathway_fit≈82
    # (B2+mechatronics is an excellent ausbildung match), timeline≈60, financial≈75
    # (€7,000 → good for ausbildung), doc≈58 (LATAM with associate)
    # overall = 75×0.25 + 70×0.20 + 82×0.20 + 60×0.15 + 75×0.10 + 58×0.10
    #         = 18.75 + 14 + 16.4 + 9 + 7.5 + 5.8 = 71.45 → 71
    # Confidence: moderate (pathway_fit for mechatronics at B2 is reliably high)
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
        "expected_overall_score": 71,
        "source": "manual_seed_v1",
        "reviewed_by_human": True,
    },
    # 14. Experienced professional, work visa, 20 years experience
    # language=55 (B1), edu≈88 (master+healthcare admin+20yr), pathway_fit≈85,
    # timeline≈80 (2_years_plus mid), financial≈85 (stable+€12,000), doc≈65
    # overall = 55×0.25 + 88×0.20 + 85×0.20 + 80×0.15 + 85×0.10 + 65×0.10
    #         = 13.75 + 17.6 + 17 + 12 + 8.5 + 6.5 = 75.35 → 75
    # Confidence: moderate (experience dominates; B1 pulls language weight down)
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
        "expected_overall_score": 75,
        "source": "manual_seed_v1",
        "reviewed_by_human": True,
    },
    # 15. Ceiling calibration — perfect candidate
    # language=100 (C2), edu≈90 (master+industrial eng+10yr), pathway_fit≈92,
    # timeline≈80 (2_years_plus mid), financial≈95 (€25,000 fully self-funded),
    # doc≈65 (LATAM with master)
    # overall = 100×0.25 + 90×0.20 + 92×0.20 + 80×0.15 + 95×0.10 + 65×0.10
    #         = 25 + 18 + 18.4 + 12 + 9.5 + 6.5 = 89.4 → 89
    # Confidence: HIGH — clearly in the "strong candidate" (>80) band
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
        "expected_overall_score": 89,
        "source": "manual_seed_v1",
        "reviewed_by_human": True,
    },
    # 16. EU citizen — documentation score should be easy
    # language=75 (B2), edu≈72 (bachelor+elec eng+3yr), pathway_fit≈78,
    # timeline≈60, financial≈70 (€6,000 → good for ausbildung),
    # doc≈88 (EU citizen → easy — significantly higher than LATAM baseline)
    # overall = 75×0.25 + 72×0.20 + 78×0.20 + 60×0.15 + 70×0.10 + 88×0.10
    #         = 18.75 + 14.4 + 15.6 + 9 + 7 + 8.8 = 73.55 → 74
    # Confidence: moderate — EU documentation advantage is a clear differentiator vs LATAM
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
        "expected_overall_score": 74,
        "source": "manual_seed_v1",
        "reviewed_by_human": True,
    },
    # 17. Non-standard field — tests generalisation
    # language=55 (B1), edu≈40-50 (marine biology→no clear ausbildung sector),
    # pathway_fit≈30-40 (very poor sector fit; model must invent a mapping),
    # timeline≈60, financial≈55, doc≈60
    # This is explicitly the "generalisation" test case — the point is to see how
    # the model handles an unusual field. The education/pathway scores depend entirely
    # on the model's sector mapping, making overall_score unpredictable within ±10.
    # expected_overall_score: null
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
        "expected_overall_score": None,
        "source": "manual_seed_v1",
        "reviewed_by_human": False,
    },
    # 18. Long financial text — input length stress test
    # language=55 (B1), edu≈65 (bachelor+accounting+5yr), pathway_fit≈58,
    # timeline≈60, financial≈78 (detailed: €8k+bonus+rent income+no debts+stipend)
    # BUT: the model's interpretation of the detailed financial text is
    # highly variable — it may focus on the €8k floor or the full picture.
    # expected_overall_score: null
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
        "expected_overall_score": None,
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
