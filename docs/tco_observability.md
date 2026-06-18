# TCO Observability

Klar records safe AI usage telemetry for each inference attempt across all AI-powered use cases (UC-01 diagnostic, UC-02 Ausbildung matching, UC-04 document factory).

## What Is Stored

The `ai_usage_events` table stores:

- provider and model
- request type (`germany_diagnostic`, `ausbildung_sector`, `ausbildung_match`, `document_factory`)
- internal `diagnostic_id` and `student_id`
- input, output, and total tokens
- estimated USD cost
- latency in milliseconds
- success/failure and safe error type
- creation timestamp

Telemetry must not include raw prompts, student names, emails, full profiles, or personal diagnostic answers.

## Model Routing

| Call | Model | Rationale |
|------|-------|-----------|
| UC-01 Germany diagnostic | `claude-sonnet-4-6` | Multi-dimensional scoring and narrative; requires reasoning quality |
| UC-02 Sector classification | `claude-haiku-4-5` | Simple 5-way routing, max_tokens=20; Haiku is 3× cheaper per MTok |
| UC-02 Position ranking | `claude-sonnet-4-6` | Multi-criteria reasoning across a JSON position payload |
| UC-04 Document factory | `claude-sonnet-4-6` | Long-form structured German writing; quality matters for a career doc |

## Model Version Traceability

The exact model snapshot used for each diagnostic is stored in `diagnostics.ai_model`, populated from the `ai_usage_events` telemetry when the diagnostic row is created.

### Are these model IDs pinned or rolling aliases?

**`claude-sonnet-4-6`** is a fully pinned snapshot identifier per the Anthropic API documentation. The SDK explicitly documents this string as complete — no date suffix should be appended (any date-suffixed variant such as `claude-sonnet-4-6-20251114` would be a training-data artefact, not a valid ID). The string as-is is the stable, pinned identifier.

**`claude-haiku-4-5`** is an alias. The fully pinned snapshot ID is `claude-haiku-4-5-20251001`. Both IDs are present in `MODEL_PRICING` in `ai_observability.py` so cost is calculated correctly regardless of which form appears in telemetry.

### Model deprecation process

When Anthropic deprecates a model version and it needs to be replaced:

1. Update the `ANTHROPIC_MODEL` / `ANTHROPIC_HAIKU_MODEL` env vars in the deployment environment.
2. Add the new model's pricing to `MODEL_PRICING` in `backend/services/ai_observability.py`.
3. Run `python scripts/check_prompt_drift.py` — if behavior changes require prompt updates, bump the relevant `*_PROMPT_VERSION` in `services/diagnostic_versions.py`.
4. Apply a migration to note the model change in any relevant schema fields if needed.
5. Deploy; monitor `ai_usage_events` for unexpected cost or latency spikes in the first 24 hours.

## Pricing

| Model | Input $/MTok | Output $/MTok |
|-------|-------------|--------------|
| `claude-sonnet-4-6` | $3.00 | $15.00 |
| `claude-haiku-4-5` | $1.00 | $5.00 |

Override with environment variables when contract pricing changes:

```bash
ANTHROPIC_INPUT_USD_PER_MTOK=3
ANTHROPIC_OUTPUT_USD_PER_MTOK=15
```

## Runtime Safeguards

The diagnostic agent uses:

- `ANTHROPIC_MODEL` defaulting to `claude-sonnet-4-6`
- `ANTHROPIC_HAIKU_MODEL` defaulting to `claude-haiku-4-5`
- `ANTHROPIC_MAX_OUTPUT_TOKENS` defaulting to `4000`
- `ANTHROPIC_TIMEOUT_SECONDS` defaulting to `45`
- `DIAGNOSTIC_MAX_INPUT_CHARS` defaulting to `8000`
- `max_retries=2` on all Anthropic client instances (automatic retry on transient errors)

## Applying The Migrations

Apply migrations in order:

```
supabase/migrations/20260616161253_create_ai_usage_events.sql   — ai_usage_events table
supabase/migrations/20260618130000_add_ai_model_to_diagnostics.sql — diagnostics.ai_model
supabase/migrations/20260618140000_add_match_prompt_version.sql — ausbildung_matches.match_prompt_version
supabase/migrations/20260618150000_add_ai_status_to_students.sql — students.ai_status
```

If the `ai_usage_events` table has not been applied yet, the backend falls back to safe telemetry entries in `audit_log.details`.
