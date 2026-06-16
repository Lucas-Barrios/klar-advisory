-- UC-02: Ausbildung Position Matcher
-- Cached positions from Bundesagentur für Arbeit (angebotsart=4)
CREATE TABLE IF NOT EXISTS ausbildung_positions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  refnr TEXT UNIQUE NOT NULL,
  sector_keyword TEXT NOT NULL,
  beruf TEXT,
  titel TEXT,
  arbeitgeber TEXT,
  plz TEXT,
  ort TEXT,
  region TEXT,
  lat FLOAT,
  lon FLOAT,
  eintrittsdatum TEXT,
  veroeffentlichungsdatum TEXT,
  application_url TEXT,
  cached_at TIMESTAMPTZ DEFAULT NOW()
);

-- AI match results linked to a diagnostic (pending human review)
CREATE TABLE IF NOT EXISTS ausbildung_matches (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  diagnostic_id UUID REFERENCES diagnostics(id) ON DELETE CASCADE,
  matched_positions JSONB,
  reasoning_summary TEXT,
  status TEXT DEFAULT 'pending' CHECK (status IN ('pending','approved','rejected')),
  reviewed_at TIMESTAMPTZ
);

ALTER TABLE ausbildung_positions ENABLE ROW LEVEL SECURITY;
ALTER TABLE ausbildung_matches ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'ausbildung_positions' AND policyname = 'anon_read_positions'
  ) THEN
    CREATE POLICY "anon_read_positions" ON ausbildung_positions FOR SELECT TO anon USING (true);
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'ausbildung_matches' AND policyname = 'anon_read_matches'
  ) THEN
    CREATE POLICY "anon_read_matches" ON ausbildung_matches FOR SELECT TO anon USING (true);
  END IF;
END $$;
