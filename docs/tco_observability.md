# TCO Observability

Klar records safe AI usage telemetry for each Germany diagnostic inference attempt.

## What Is Stored

The `ai_usage_events` table stores:

- provider and model
- request type
- internal `diagnostic_id` and `student_id`
- input, output, and total tokens
- estimated USD cost
- latency in milliseconds
- success/failure and safe error type
- creation timestamp

Telemetry must not include raw prompts, student names, emails, full profiles, or personal diagnostic answers.

## Pricing

Default pricing is configured in `backend/services/ai_observability.py` for Claude Sonnet 4.6:

- input: `$3.00` per million tokens
- output: `$15.00` per million tokens

Override with environment variables when contract pricing changes:

```bash
ANTHROPIC_INPUT_USD_PER_MTOK=3
ANTHROPIC_OUTPUT_USD_PER_MTOK=15
```

## Runtime Safeguards

The diagnostic agent uses:

- `ANTHROPIC_MODEL` defaulting to `claude-sonnet-4-6`
- `ANTHROPIC_MAX_OUTPUT_TOKENS` defaulting to `4000`
- `ANTHROPIC_TIMEOUT_SECONDS` defaulting to `45`
- `DIAGNOSTIC_MAX_INPUT_CHARS` defaulting to `8000`
- `N8N_WEBHOOK_TIMEOUT_SECONDS` defaulting to `10`

## Applying The Migration

Apply `supabase/migrations/20260616161253_create_ai_usage_events.sql` to create the preferred telemetry table.
If the table has not been applied yet, the backend falls back to safe telemetry entries in `audit_log.details`.
