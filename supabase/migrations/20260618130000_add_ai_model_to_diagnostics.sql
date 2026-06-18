-- ITEM 3: Store the exact model snapshot used for each diagnostic.
-- Populated from the ai_usage_event returned by run_diagnostic().
ALTER TABLE diagnostics
    ADD COLUMN IF NOT EXISTS ai_model TEXT;
