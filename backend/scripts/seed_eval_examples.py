#!/usr/bin/env python3
"""
Seed eval examples for offline prompt testing.

Usage:
    python scripts/seed_eval_examples.py               # print to stdout
    python scripts/seed_eval_examples.py --output eval_examples.jsonl
    python scripts/seed_eval_examples.py --insert-db   # write to eval_examples table via Supabase
"""
import argparse
import json
import sys
import os

EXAMPLES = [
    # 1. Strong candidate — ausbildung
    {
        "id": "eval_01",
        "label": "strong_ausbildung_candidate",
        "name": "Ana García",
        "country": "Mexico",
        "pathway": "ausbildung",
        "german_level": "B2",
        "english_level": "C1",
        "education_level": "bachelor",
        "field_of_study": "Mechanical Engineering",
        "work_experience_years": 3,
        "timeline": "1_year",
        "financial_situation": "I have €5,000 saved and can secure more through family support.",
        "consent_given": True,
    },
    # 2. Low German proficiency — should flag language concern
    {
        "id": "eval_02",
        "label": "low_german_ausbildung",
        "name": "Carlos Mendez",
        "country": "Colombia",
        "pathway": "ausbildung",
        "german_level": "A1",
        "english_level": "B1",
        "education_level": "high_school",
        "field_of_study": "General Studies",
        "work_experience_years": 1,
        "timeline": "6_months",
        "financial_situation": "Limited savings, need funded options.",
        "consent_given": True,
    },
    # 3. Borderline score — B1 German, moderate finances
    {
        "id": "eval_03",
        "label": "borderline_b1_ausbildung",
        "name": "Valentina Rojas",
        "country": "Peru",
        "pathway": "ausbildung",
        "german_level": "B1",
        "english_level": "B2",
        "education_level": "associate",
        "field_of_study": "Nursing",
        "work_experience_years": 2,
        "timeline": "1_year",
        "financial_situation": "I have €2,000 and expect family support.",
        "consent_given": True,
    },
    # 4. Incomplete financial info — should score conservatively on financial dimension
    {
        "id": "eval_04",
        "label": "incomplete_financial_info",
        "name": "Diego Lima",
        "country": "Brazil",
        "pathway": "ausbildung",
        "german_level": "B1",
        "english_level": "B1",
        "education_level": "bachelor",
        "field_of_study": "Computer Science",
        "work_experience_years": 4,
        "timeline": "2_years_plus",
        "financial_situation": "",
        "consent_given": True,
    },
    # 5. University pathway — strong candidate
    {
        "id": "eval_05",
        "label": "strong_university_candidate",
        "name": "Sofia Herrera",
        "country": "Argentina",
        "pathway": "university",
        "german_level": "C1",
        "english_level": "C2",
        "education_level": "bachelor",
        "field_of_study": "Economics",
        "work_experience_years": 2,
        "timeline": "1_year",
        "financial_situation": "I have a €15,000 blocked account ready.",
        "consent_given": True,
    },
    # 6. University pathway — low German, 6-month timeline (unrealistic)
    {
        "id": "eval_06",
        "label": "university_unrealistic_timeline",
        "name": "Mateo Vargas",
        "country": "Chile",
        "pathway": "university",
        "german_level": "A2",
        "english_level": "B2",
        "education_level": "bachelor",
        "field_of_study": "Architecture",
        "work_experience_years": 1,
        "timeline": "6_months",
        "financial_situation": "I have €5,000 saved.",
        "consent_given": True,
    },
    # 7. Work visa pathway — experienced professional
    {
        "id": "eval_07",
        "label": "work_visa_experienced",
        "name": "Isabella Fernandez",
        "country": "Venezuela",
        "pathway": "work_visa",
        "german_level": "B1",
        "english_level": "C1",
        "education_level": "master",
        "field_of_study": "Software Engineering",
        "work_experience_years": 8,
        "timeline": "1_year",
        "financial_situation": "Stable income, €10,000 in savings.",
        "consent_given": True,
    },
    # 8. Ausbildung — healthcare field, very low German (patient-facing requires B2)
    {
        "id": "eval_08",
        "label": "healthcare_ausbildung_low_german",
        "name": "Lucas Silva",
        "country": "Brazil",
        "pathway": "ausbildung",
        "german_level": "A2",
        "english_level": "B1",
        "education_level": "associate",
        "field_of_study": "Nursing",
        "work_experience_years": 3,
        "timeline": "2_years_plus",
        "financial_situation": "Minimal savings, need fully funded program.",
        "consent_given": True,
    },
    # 9. IT ausbildung — good fit, borderline German
    {
        "id": "eval_09",
        "label": "it_ausbildung_borderline_german",
        "name": "Camila Torres",
        "country": "Mexico",
        "pathway": "ausbildung",
        "german_level": "B1",
        "english_level": "C1",
        "education_level": "bachelor",
        "field_of_study": "Information Technology",
        "work_experience_years": 2,
        "timeline": "1_year",
        "financial_situation": "€4,000 in savings, open to apprenticeship stipend.",
        "consent_given": True,
    },
    # 10. No prior education listed (only high_school), 0 work exp
    {
        "id": "eval_10",
        "label": "minimal_profile",
        "name": "Javier Morales",
        "country": "Ecuador",
        "pathway": "ausbildung",
        "german_level": "A1",
        "english_level": "A2",
        "education_level": "high_school",
        "field_of_study": "",
        "work_experience_years": 0,
        "timeline": "2_years_plus",
        "financial_situation": "No savings, need fully funded option.",
        "consent_given": True,
    },
    # 11. Hospitality ausbildung — A2 German is borderline acceptable for kitchen
    {
        "id": "eval_11",
        "label": "hospitality_a2_german",
        "name": "Lucia Ramirez",
        "country": "Guatemala",
        "pathway": "ausbildung",
        "german_level": "A2",
        "english_level": "B1",
        "education_level": "high_school",
        "field_of_study": "Culinary Arts",
        "work_experience_years": 2,
        "timeline": "1_year",
        "financial_situation": "Limited savings, need part-time income.",
        "consent_given": True,
    },
    # 12. University — missing blocked account funds
    {
        "id": "eval_12",
        "label": "university_missing_blocked_account",
        "name": "Fernando Castro",
        "country": "Bolivia",
        "pathway": "university",
        "german_level": "B2",
        "english_level": "C1",
        "education_level": "bachelor",
        "field_of_study": "Medicine",
        "work_experience_years": 0,
        "timeline": "1_year",
        "financial_situation": "I have €3,000, cannot afford the €11,000 blocked account yet.",
        "consent_given": True,
    },
    # 13. Mechatronics ausbildung — strong fit
    {
        "id": "eval_13",
        "label": "mechatronics_strong_fit",
        "name": "Ricardo Pacheco",
        "country": "Colombia",
        "pathway": "ausbildung",
        "german_level": "B2",
        "english_level": "B1",
        "education_level": "associate",
        "field_of_study": "Mechatronics",
        "work_experience_years": 4,
        "timeline": "1_year",
        "financial_situation": "Comfortable with €7,000 saved.",
        "consent_given": True,
    },
    # 14. Near-retirement age profile — should still be assessed fairly
    {
        "id": "eval_14",
        "label": "older_professional_work_visa",
        "name": "Patricia Jimenez",
        "country": "Argentina",
        "pathway": "work_visa",
        "german_level": "B1",
        "english_level": "B2",
        "education_level": "master",
        "field_of_study": "Healthcare Administration",
        "work_experience_years": 20,
        "timeline": "2_years_plus",
        "financial_situation": "Stable, €12,000 in savings.",
        "consent_given": True,
    },
    # 15. Perfect score candidate — sanity check for ceiling calibration
    {
        "id": "eval_15",
        "label": "ceiling_calibration",
        "name": "Alejandro Reyes",
        "country": "Chile",
        "pathway": "ausbildung",
        "german_level": "C2",
        "english_level": "C2",
        "education_level": "master",
        "field_of_study": "Industrial Engineering",
        "work_experience_years": 10,
        "timeline": "2_years_plus",
        "financial_situation": "€25,000 saved, fully self-funded.",
        "consent_given": True,
    },
    # 16. EU citizen — documentation score should be easy
    {
        "id": "eval_16",
        "label": "eu_citizen_easy_docs",
        "name": "Maria Gonzalez",
        "country": "Spain",
        "pathway": "ausbildung",
        "german_level": "B2",
        "english_level": "C1",
        "education_level": "bachelor",
        "field_of_study": "Electrical Engineering",
        "work_experience_years": 3,
        "timeline": "1_year",
        "financial_situation": "€6,000 in savings.",
        "consent_given": True,
    },
    # 17. Non-standard field — tests generalization
    {
        "id": "eval_17",
        "label": "non_standard_field",
        "name": "Elena Gutierrez",
        "country": "Peru",
        "pathway": "ausbildung",
        "german_level": "B1",
        "english_level": "B2",
        "education_level": "bachelor",
        "field_of_study": "Marine Biology",
        "work_experience_years": 1,
        "timeline": "1_year",
        "financial_situation": "€3,500 saved.",
        "consent_given": True,
    },
    # 18. Very long financial text — input limit stress test
    {
        "id": "eval_18",
        "label": "long_financial_text",
        "name": "Pablo Mendoza",
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
        "consent_given": True,
    },
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed eval examples for Klar diagnostic prompt testing.")
    parser.add_argument("--output", metavar="FILE", help="Write JSONL to this file instead of stdout.")
    parser.add_argument("--insert-db", action="store_true", help="Insert into Supabase eval_examples table.")
    args = parser.parse_args()

    if args.insert_db:
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from database import get_supabase
        supabase = get_supabase()
        inserted = 0
        for ex in EXAMPLES:
            try:
                supabase.table("eval_examples").upsert(ex, on_conflict="id").execute()
                inserted += 1
            except Exception as e:
                print(f"[WARN] Failed to insert {ex['id']}: {e}", file=sys.stderr)
        print(f"Inserted/updated {inserted}/{len(EXAMPLES)} eval examples.")
        return

    lines = [json.dumps(ex) for ex in EXAMPLES]
    output = "\n".join(lines) + "\n"

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Wrote {len(EXAMPLES)} examples to {args.output}.")
    else:
        sys.stdout.write(output)


if __name__ == "__main__":
    main()
