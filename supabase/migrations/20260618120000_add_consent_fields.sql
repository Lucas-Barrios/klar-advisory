-- GDPR/EU AI Act consent fields for the students (intake) table.
-- consent_given must be true for a submission to be accepted (enforced at the API layer).
-- consent_timestamp records when the data subject checked the consent box.

ALTER TABLE public.students
  ADD COLUMN IF NOT EXISTS consent_given    BOOLEAN     NOT NULL DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS consent_timestamp TIMESTAMPTZ;

COMMENT ON COLUMN public.students.consent_given IS
  'GDPR Art 7 / EU AI Act Art 14 consent flag. API rejects submissions where this is false.';

COMMENT ON COLUMN public.students.consent_timestamp IS
  'UTC timestamp at which the data subject checked the consent checkbox. Null for legacy rows.';
