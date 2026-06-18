-- ITEM 5a: Track AI-layer outcomes per student without orphan deletion.
-- Values: NULL (not yet attempted), 'diagnostic_failed'.
-- Prefer status field over deletion for auditability.
ALTER TABLE students
    ADD COLUMN IF NOT EXISTS ai_status TEXT;
