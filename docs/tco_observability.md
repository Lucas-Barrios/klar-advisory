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

**`claude-sonnet-4-6`** is a fully pinned snapshot. Per [platform.claude.com/docs/en/about-claude/models/model-ids-and-versions](https://platform.claude.com/docs/en/about-claude/models/model-ids-and-versions): *"Starting with the Claude 4.6 generation, model IDs use a dateless format… A 4.6-generation ID such as `claude-sonnet-4-6` is not an alias. It is the snapshot."* No date suffix exists or should be appended.

**`claude-haiku-4-5-20251001`** is the pinned snapshot for Haiku 4.5. Haiku 4.5 predates the 4.6 generation, so it follows the pre-4.6 convention. Per the same page: *"Models before the 4.6 generation include a snapshot date in the ID… For example: `claude-sonnet-4-5-20250929`, `claude-haiku-4-5-20251001`"* and *"On the Claude API, these models also have shorter aliases (for example, `claude-sonnet-4-5`) that point to the most recent dated snapshot for that minor version."* The bare `claude-haiku-4-5` is that convenience alias — it is not the pinned ID. `AI_MODEL_HAIKU` therefore defaults to `claude-haiku-4-5-20251001`. Both the dated and undated forms are present in `MODEL_PRICING` so cost is calculated correctly if either appears in legacy telemetry rows.

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

The document factory (UC-04) uses a hardcoded `max_tokens=5000` ceiling. Any cost-per-request figures derived from this document for document generation are based on that ceiling as a proxy — not on measured average `output_tokens` from `ai_usage_events` — because no `document_factory` rows exist in production at the time of writing (pilot phase, 2026-06-19). Once sufficient rows accumulate, recalculate using `SELECT AVG(output_tokens), AVG(estimated_cost) FROM ai_usage_events WHERE request_type = 'document_factory' AND success = true` and update any stated figures accordingly.

## Applying The Migrations

Apply migrations in order:

```
supabase/migrations/20260616161253_create_ai_usage_events.sql   — ai_usage_events table
supabase/migrations/20260618130000_add_ai_model_to_diagnostics.sql — diagnostics.ai_model
supabase/migrations/20260618140000_add_match_prompt_version.sql — ausbildung_matches.match_prompt_version
supabase/migrations/20260618150000_add_ai_status_to_students.sql — students.ai_status
```

If the `ai_usage_events` table has not been applied yet, the backend falls back to safe telemetry entries in `audit_log.details`.
