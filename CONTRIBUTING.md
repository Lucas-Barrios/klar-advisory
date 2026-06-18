# Contributing to Klar Advisory

## Prompt Changes

Changing `SYSTEM_PROMPT`, `MATCH_PROMPT`, or `DOCUMENT_PROMPT` requires **two separate steps**. These are not the same thing and one does not substitute for the other.

### Step 1 — Self-review (before committing)

Re-read the full diff line by line. Not the summary. Not the version bump. The actual text change.

Ask yourself:
- Is this wording change intentional?
- Does it affect score calibration in a way that needs eval re-running?
- Does it interpolate any user-controlled input without sanitisation? (Injection risk.)
- Does it contradict any constraint in `docs/known_limitations.md`?

This step has no automation. It requires you to read the diff.

### Step 2 — Version bump + hash update (before pushing)

After reviewing and confirming the change, bump the version string:

| Prompt | Location | Version constant |
|--------|----------|-----------------|
| Germany Readiness Diagnostic | `backend/agents/germany_diagnostic.py` — `SYSTEM_PROMPT` | `DIAGNOSTIC_PROMPT_VERSION_DEFAULT` in `services/diagnostic_versions.py` |
| Ausbildung Position Matcher | `backend/agents/ausbildung_matcher.py` — `MATCH_PROMPT` | `MATCH_PROMPT_VERSION_DEFAULT` in `services/diagnostic_versions.py` |
| Document Factory | `backend/agents/document_factory.py` — `DOCUMENT_PROMPT` | `DOCUMENT_PROMPT_VERSION_DEFAULT` in `services/diagnostic_versions.py` |

Then record the new hash baseline:

```bash
cd backend
python scripts/check_prompt_drift.py --update
```

Commit both the `diagnostic_versions.py` change and the updated `.prompt_hashes` together in the same commit as the prompt change. CI enforces this — `check_prompt_drift.py` exits 1 if the hash changed without a version bump.

---

## CI Gates

The GitHub Actions workflow (`ci.yml`) runs on every push and PR to `main`:

1. `python -m pytest tests/ -v` — full test suite
2. `python scripts/check_prompt_drift.py` — prompt drift detection

Both must pass before merge. Branch protection on `main` requires these checks.

---

## Migrations

New columns or tables go in a new file under `supabase/migrations/` with a timestamp prefix (`YYYYMMDDHHMMSS_description.sql`). Never edit existing migration files.

---

## Tests

Run locally before pushing:

```bash
cd backend
pip install stripe  # required for test_security_blockers.py
python -m pytest tests/ -v
python scripts/check_prompt_drift.py
```
