# Data Source Mapping
## Klar · Germany Readiness Diagnostic Platform
### June 2026 · Supersedes scattered field references in use_case_definition.md

This document maps every data entry point — form fields, external API fields that get persisted, and any background collection — to the Supabase table and column where each value lands. Use this as the authoritative reference when adding fields, changing the schema, or completing a DPIA amendment.

---

## 1. Student Intake Form → `students` Table

The intake form at `/diagnostic` (frontend/app/diagnostic/page.tsx) collects data across 11 question steps. Each field maps directly to the students table via a POST to `/api/diagnostic/`.

| Form Step | Form Field ID | Backend Field | Supabase Table | Column | Required | Notes |
|---|---|---|---|---|---|---|
| 1 | `name` | `name` | students | `name` | Yes | Also synced to `full_name` at DB level |
| 2 | `email` | `email` | students | `email` | Yes | Used for results delivery via n8n |
| 3 | `country` | `country` | students | `country` | Yes | Nationality indicator (sensitive PII) |
| 4 | `pathway` | `pathway` | students | `pathway` | Yes | Enum: university / ausbildung / work_visa |
| 5 | `german_level` | `german_level` | students | `german_level` | Yes | Enum: none / A1 / A2 / B1 / B2 / C1 / C2 |
| 6 | `education_level` | `education_level` | students | `education_level` | Yes | Enum: high_school / vocational / bachelor / master / phd |
| 7 | `field_of_study` | `field_of_study` | students | `field_of_study` | No | Free text, max 120 chars |
| 8 | `work_experience_years` | `work_experience_years` | students | `work_experience_years` | Yes | Integer 0–60; UI presents as 0 / 1 / 3 / 5 |
| 9 | `timeline` | `timeline` | students | `timeline` | Yes | Enum: 6_months / 1_year / 2_years_plus |
| 10 | `financial_situation` | `financial_situation` | students | `financial_situation` | Yes | Free text (UI forces one of 3 values); sensitive PII |
| 11 | `english_level` | `english_level` | students | `english_level` | No | Enum: Basic / Intermediate / Advanced / Fluent |
| Hardcoded | n/a | `current_location` | students | `current_location` | No | Always empty string in current frontend; column retained for future use |
| Hardcoded | n/a | `additional_info` | students | `additional_info` | No | Always empty string in current frontend; free-text PII risk if re-enabled |
| Consent checkbox | `consentChecked` | `consent_given` | students | `consent_given` | Yes | Bool; submission rejected server-side if false |
| Consent timestamp | `new Date().toISOString()` | `consent_timestamp` | students | `consent_timestamp` | Yes | Set by frontend at submission time; always present when consent_given=true |

**Validation applied at:** `models/schemas.py → StudentProfileInput` (Pydantic) + `routers/diagnostic.py` (consent check before any DB write).

---

## 2. AI Diagnostic Agent → `diagnostics` Table

After the student record is inserted, `run_diagnostic()` (agents/germany_diagnostic.py) sends the full student profile to Anthropic Claude and parses the JSON response. The resulting fields are written to the `diagnostics` table in a single INSERT.

| AI Output Field | Supabase Table | Column | Type | Notes |
|---|---|---|---|---|
| `overall_score` | diagnostics | `overall_score` | integer 0–100 | Weighted average of all 6 dimensions |
| `language_score` | diagnostics | `language_score` | integer | German level dimension |
| `education_score` | diagnostics | `education_score` | integer | Education level dimension |
| `pathway_fit_score` | diagnostics | `pathway_fit_score` | integer | Pathway alignment dimension |
| `timeline_score` | diagnostics | `timeline_score` | integer | Urgency/readiness dimension |
| `financial_score` | diagnostics | `financial_score` | integer | Financial readiness dimension |
| `documentation_score` | diagnostics | `documentation_score` | integer | Document complexity dimension |
| `summary` | diagnostics | `summary` | text | 2–3 sentence AI-generated summary (references student first name) |
| `next_step_message` | diagnostics | `next_step_message` | text | Personalised consultation CTA (references student first name) |
| `roadmap` | diagnostics | `roadmap` | jsonb | Month-by-month steps array |
| `recommendations` | diagnostics | `recommendations` | jsonb | Array of 3 program/resource recommendations |
| `raw_output` | diagnostics | `raw_output` | text | Full AI response string (stored for debug/audit; not returned to public) |

**Additional fields set at INSERT time:**

| Source | Supabase Table | Column | Value |
|---|---|---|---|
| Application | diagnostics | `status` | `'pending'` (always at creation) |
| `generate_progress_token()` → hashed | diagnostics | `progress_token_hash` | SHA-256 of bearer token |
| `DIAGNOSTIC_PROMPT_VERSION` constant | diagnostics | `diagnostic_prompt_version` | e.g. `'germany_diagnostic_prompt_v1'` |
| `DIAGNOSTIC_RUBRIC_VERSION` constant | diagnostics | `diagnostic_rubric_version` | e.g. `'germany_readiness_rubric_v1'` |
| Application | diagnostics | `student_id` | UUID FK → students.id |

---

## 3. AI Usage Telemetry → `ai_usage_events` Table

After every Anthropic API call (success or failure), `build_usage_event()` (services/ai_observability.py) constructs a telemetry record. No student PII is stored here — a DB CHECK constraint enforces this.

| Source | Supabase Table | Column | Notes |
|---|---|---|---|
| Anthropic response | ai_usage_events | `input_tokens`, `output_tokens`, `total_tokens` | Token counts from the API response |
| Computed | ai_usage_events | `estimated_cost` | Based on per-MTok rates in env vars |
| Computed | ai_usage_events | `latency_ms` | Wall-clock time of the API call |
| Context | ai_usage_events | `diagnostic_id`, `student_id` | UUID FKs — indirect PII |
| Constants | ai_usage_events | `provider`, `model`, `request_type` | e.g. `anthropic / claude-sonnet-4-6 / germany_diagnostic` |
| Boolean | ai_usage_events | `success` | True/false |
| Exception class | ai_usage_events | `error_type` | e.g. `APIError`, `InputTooLong` |

---

## 4. Bundesagentur für Arbeit API → `ausbildung_positions` + `ausbildung_matches` Tables

The ausbildung matcher (agents/ausbildung_matcher.py) calls the BA job search API (`rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4/jobs?angebotsart=4`) and persists the results. No student PII is stored in these tables.

### 4a. Cached Position Data → `ausbildung_positions`

| BA API Field | Supabase Table | Column | Notes |
|---|---|---|---|
| `refnr` | ausbildung_positions | `refnr` | Unique position reference number |
| `beruf` | ausbildung_positions | `beruf` | Occupation category |
| `titel` | ausbildung_positions | `titel` | Job title |
| `arbeitgeber` | ausbildung_positions | `arbeitgeber` | Employer name (public data) |
| `arbeitsort.plz` | ausbildung_positions | `plz` | Postal code |
| `arbeitsort.ort` | ausbildung_positions | `ort` | City |
| `arbeitsort.region` | ausbildung_positions | `region` | Federal state |
| `arbeitsort.koordinaten.lat/lon` | ausbildung_positions | `lat`, `lon` | Coordinates |
| `eintrittsdatum` | ausbildung_positions | `eintrittsdatum` | Intended start date |
| `aktuelleVeroeffentlichungsdatum` | ausbildung_positions | `veroeffentlichungsdatum` | Listing publication date |
| Computed | ausbildung_positions | `application_url` | `https://www.arbeitsagentur.de/jobsuche/jobdetail/{refnr}` |
| System | ausbildung_positions | `cached_at` | Timestamp of cache write |

**Fields the BA API has but Klar does NOT persist:** language requirements (not in API data — Claude infers from occupation type), salary, full description text (too large; not needed for matching).

### 4b. AI Match Results → `ausbildung_matches`

After Claude ranks positions against the student's profile, the result is written as a single JSONB record per diagnostic:

| Source | Supabase Table | Column | Notes |
|---|---|---|---|
| Claude output | ausbildung_matches | `matched_positions` | JSONB array of ranked positions (public employer data only) |
| Claude output | ausbildung_matches | `reasoning_summary` | AI text explaining match rationale (may reference student profile characteristics) |
| Application | ausbildung_matches | `diagnostic_id` | UUID FK → diagnostics.id |
| Application | ausbildung_matches | `status` | `'pending'` at creation; set to `approved`/`rejected` by consultant review |

---

## 5. Consultant Review → `diagnostics` + `audit_log` Tables

When the consultant acts on a diagnostic (approve/reject), the following fields are written:

### 5a. `diagnostics` table (raw values):

| Source | Column | Notes |
|---|---|---|
| Action payload | `status` | `approved` or `rejected` |
| Action payload | `reviewer_notes` | Raw text — **not redacted** (Finding F-1 in sensitive_data_inventory.md) |
| Action payload | `reviewer_decision` | String label |
| Action payload | `reviewer_correction_notes` | Raw text — **not redacted** |
| Action payload | `reviewer_confidence` | Integer 1–5 |
| Action payload | `rejection_reason` | Raw text — **not redacted** |
| Action payload | `review_duration_seconds` | Integer |
| System | `reviewed_at` | UTC timestamp |

### 5b. `audit_log` table (redacted values via `redact_sensitive_text`):

| Source | Column | Notes |
|---|---|---|
| `diagnostic_id` | `diagnostic_id` | FK |
| Action type | `action` | e.g. `review_approved`, `review_rejected` |
| Hardcoded | `actor` | `'consultant'` |
| Redacted payload | `details` | JSONB with reviewer_notes, rejection_reason, correction_notes — all passed through `redact_sensitive_text()` before storage |

---

## 6. Stripe Payment Webhook → `diagnostics` Table

When a payment succeeds (router: routers/payments.py), two unlock fields are toggled:

| Event | Supabase Table | Column | Value |
|---|---|---|---|
| Stripe `checkout.session.completed` (matches) | diagnostics | `matches_unlocked` | `true` |
| Stripe `checkout.session.completed` (documents) | diagnostics | `documents_unlocked` | `true` |

No payment card data is stored. Stripe handles all payment data.

---

## 7. Progress Updates → `diagnostics` Table

Students can mark roadmap steps complete via `PATCH /api/diagnostic/{id}/progress` with a bearer token:

| Source | Supabase Table | Column | Notes |
|---|---|---|---|
| Client payload | diagnostics | `completed_steps` | Integer array, sorted, deduplicated |

---

## 8. Consultation Booking → `diagnostics` + `audit_log` Tables

When the consultant marks a booking:

| Source | Supabase Table | Column | Value |
|---|---|---|---|
| Admin action | diagnostics | `consultation_booked` | `true` |
| System | diagnostics | `consultation_booked_at` | UTC timestamp |
| System | audit_log | `action` | `'consultation_booked'` |

---

## 9. Evaluation Examples → `evaluation_examples` Table

When an admin promotes a reviewed diagnostic to an evaluation dataset, `sanitize_evaluation_payload()` (services/evaluation.py) strips all PII before persisting:

| Source | Kept in `input_payload`? | Notes |
|---|---|---|
| `country` | ✅ Yes | Non-identifying at country level |
| `pathway`, `german_level`, `english_level`, `education_level`, `field_of_study`, `work_experience_years`, `timeline`, `financial_situation`, `current_location` | ✅ Yes | Profile characteristics, no direct identifiers |
| `name`, `full_name`, `email` | ❌ Stripped | Direct identifiers removed |
| `raw_output`, `additional_info` | ❌ Stripped | Free-text PII risk |

**Note:** A synthetic `"name": "Evaluation Candidate"` placeholder is set in the saved payload.

---

*Data Source Mapping · Klar · June 2026 · Update this file whenever a new table, column, or integration is added*
