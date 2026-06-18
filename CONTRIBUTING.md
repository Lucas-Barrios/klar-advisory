# Contributing to Klar Advisory

## Prompt Versioning

Klar uses prompt version strings to track which generation of each prompt produced a given output. The eval harness (`check_prompt_drift.py`) enforces this automatically in CI.

**Rule: bump the version string whenever you edit a system prompt.**

| Prompt | Location | Version constant |
|--------|----------|-----------------|
| Germany Readiness Diagnostic | `backend/agents/germany_diagnostic.py` — `SYSTEM_PROMPT` | `DIAGNOSTIC_PROMPT_VERSION` in `services/diagnostic_versions.py` |
| Ausbildung Position Matcher | `backend/agents/ausbildung_matcher.py` — `MATCH_PROMPT` | `MATCH_PROMPT_VERSION` in `services/diagnostic_versions.py` |
| Document Factory | `backend/agents/document_factory.py` — `DOCUMENT_PROMPT` | `DOCUMENT_PROMPT_VERSION` in `services/diagnostic_versions.py` |

After bumping a version, update the baseline hash file:

```bash
cd backend
python scripts/check_prompt_drift.py --update
```

Commit the updated `.prompt_hashes` file alongside the prompt change so CI passes.

## Migrations

New columns or tables go in a new file under `supabase/migrations/` with a timestamp prefix (`YYYYMMDDHHMMSS_description.sql`). Never edit existing migration files.

## Tests

Run the test suite before opening a PR:

```bash
cd backend
pip install stripe  # required for test_security_blockers.py
python -m pytest tests/
```
