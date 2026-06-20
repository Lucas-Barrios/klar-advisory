-- Add full_description caching columns to ausbildung_positions.
-- Populated on-demand by fetch_job_description() in ausbildung_cache.py,
-- not during the bulk refresh job, to avoid multiplying calls for positions
-- no student has selected.
ALTER TABLE ausbildung_positions
  ADD COLUMN IF NOT EXISTS full_description TEXT,
  ADD COLUMN IF NOT EXISTS full_description_fetched_at TIMESTAMPTZ;
