-- ITEM 4: Track the prompt version used when each match set was generated.
-- Allows eval harness to detect prompt drift across match results.
ALTER TABLE ausbildung_matches
    ADD COLUMN IF NOT EXISTS match_prompt_version TEXT;
