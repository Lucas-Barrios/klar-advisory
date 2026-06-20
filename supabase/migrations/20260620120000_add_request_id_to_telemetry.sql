-- Add request_id correlation column to telemetry tables.
-- Nullable text; populated automatically by the backend's RequestIdMiddleware.
-- Allows tracing a specific request across ai_usage_events, audit_log, and server logs.
ALTER TABLE ai_usage_events
    ADD COLUMN IF NOT EXISTS request_id TEXT;

ALTER TABLE audit_log
    ADD COLUMN IF NOT EXISTS request_id TEXT;
