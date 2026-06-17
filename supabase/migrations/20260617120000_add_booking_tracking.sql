ALTER TABLE diagnostics ADD COLUMN IF NOT EXISTS next_step_message TEXT;
ALTER TABLE diagnostics ADD COLUMN IF NOT EXISTS consultation_booked BOOLEAN DEFAULT FALSE;
ALTER TABLE diagnostics ADD COLUMN IF NOT EXISTS consultation_booked_at TIMESTAMPTZ;
