# Sensitive Data Inventory
## Klar · Germany Readiness Diagnostic Platform
### Prepared: June 2026 · Source of truth for ITEM 3 API audit and storage decisions

This document supersedes the data element table in `gdpr_documentation.md §2.2`. Any conflict between this inventory and that document should be resolved in favour of this file.

---

## How to Read This Table

| Column | Meaning |
|---|---|
| Field | Column name as it exists in Postgres |
| Table / Location | Supabase table or intake form step |
| Classification | PII = directly identifies an individual; Sensitive PII = financial/nationality/health data attracting heightened GDPR protection; Non-personal = no individual linkage |
| Displayed in | Which views or API responses expose this field |
| Protection status | Current technical controls in place |

---

## 1. `students` Table

| Field | Table / Location | Classification | Displayed in | Protection status |
|---|---|---|---|---|
| `id` (uuid) | students | Non-personal | Admin dashboard (ID only), API responses (as student_id foreign key) | RLS service_role only |
| `created_at` | students | Non-personal | Admin dashboard | RLS service_role only |
| `name` | students · intake form step 1 | **PII** (direct identifier) | Admin dashboard (full), public results page (first name via AI text), n8n webhook (approval notification) | RLS; redacted in audit_log; **not redacted in diagnostics.reviewer_notes — see Finding F-1** |
| `full_name` | students | **PII** (compatibility alias for `name`) | Same as `name` | Same as `name` |
| `email` | students · intake form step 2 | **PII** (direct identifier, contact) | Admin dashboard (full); n8n webhook; **fetched but not returned** by public result endpoint | RLS; redacted in audit_log; logs masked (post ITEM 3a fix) |
| `country` | students · intake form step 3 | **Sensitive PII** (nationality indicator per GDPR recital 30) | Admin dashboard, AI prompt (Anthropic) | RLS; transmitted to Anthropic under SCC |
| `age` | students · intake form (optional) | **PII** | Admin dashboard, AI prompt | RLS |
| `pathway` | students · intake form step 4 | Non-personal (categorical choice) | Admin dashboard, public result, n8n webhook | RLS |
| `german_level` | students · intake form step 5 | **PII** (language proficiency — quasi-identifier in combination) | Admin dashboard, AI prompt | RLS |
| `english_level` | students · intake form step 11 | **PII** (language proficiency) | Admin dashboard, AI prompt | RLS |
| `education_level` | students · intake form step 6 | **PII** (education level per GDPR recital 30) | Admin dashboard, AI prompt | RLS |
| `field_of_study` | students · intake form step 7 | **PII** | Admin dashboard, AI prompt | RLS |
| `work_experience_years` | students · intake form step 8 | **PII** | Admin dashboard, AI prompt | RLS |
| `timeline` | students · intake form step 9 | Non-personal (planning preference) | Admin dashboard, AI prompt | RLS |
| `financial_situation` | students · intake form step 10 | **Sensitive PII** (financial capacity — borderline special category, GDPR recital 30) | Admin dashboard, AI prompt; **never returned by public endpoint** | RLS; not logged; transmitted to Anthropic under SCC |
| `current_location` | students · intake form (hidden, always empty string in current frontend) | **PII** | Admin dashboard | RLS |
| `additional_info` | students · intake form (hidden, always empty string in current frontend) | **PII** (free-text — may contain incidental PII including health, family, visa status) | Admin dashboard | RLS; **if re-enabled in frontend: must be screened for special-category data** |
| `consent_given` | students | Non-personal (compliance flag) | Admin dashboard | RLS; added by migration 20260618120000 |
| `consent_timestamp` | students | Non-personal (compliance timestamp) | Admin dashboard | RLS; added by migration 20260618120000 |

---

## 2. `diagnostics` Table

| Field | Table / Location | Classification | Displayed in | Protection status |
|---|---|---|---|---|
| `id` (uuid) | diagnostics | Non-personal | Admin dashboard, public result page, student-facing URLs | RLS service_role only |
| `created_at` | diagnostics | Non-personal | Admin dashboard | RLS |
| `student_id` | diagnostics | **PII** (foreign key — links to full student record) | Admin dashboard | RLS; cascade delete wired |
| `overall_score` | diagnostics | **PII** (AI profiling output about an individual) | Admin dashboard, public result page | RLS; public only after human approval |
| `language_score` | diagnostics | **PII** (dimension score) | Admin dashboard, public result page | Same |
| `education_score` | diagnostics | **PII** | Admin dashboard, public result page | Same |
| `pathway_fit_score` | diagnostics | **PII** | Admin dashboard, public result page | Same |
| `timeline_score` | diagnostics | **PII** | Admin dashboard, public result page | Same |
| `financial_score` | diagnostics | **Sensitive PII** (derived from financial_situation) | Admin dashboard, public result page | Same |
| `documentation_score` | diagnostics | **PII** | Admin dashboard, public result page | Same |
| `summary` | diagnostics | **PII** (AI-generated text referencing student by first name) | Admin dashboard, public result page | Approved by human before public delivery |
| `next_step_message` | diagnostics | **PII** (personalised AI text with first name) | Admin dashboard, public result page | Same |
| `roadmap` | diagnostics | **PII** (personalised JSONB) | Admin dashboard, public result page | Same |
| `recommendations` | diagnostics | **PII** (personalised to profile) | Admin dashboard, public result page | Same |
| `raw_output` | diagnostics | **PII** (full AI response — includes AI echo of student first name in text) | **Admin dashboard only** (via students(\*) join) — **NOT returned by public endpoint** | RLS; not exposed publicly; stored for audit/debug |
| `status` | diagnostics | Non-personal | Admin dashboard, public result page | RLS |
| `reviewer_notes` | diagnostics | **PII risk** — stored raw (not redacted); may contain student name/email if reviewer typed them | Admin dashboard only | **Finding F-1: stored unredacted — see below** |
| `reviewer_decision` | diagnostics | Non-personal | Admin dashboard | RLS |
| `reviewer_correction_notes` | diagnostics | **PII risk** — stored raw (not redacted) | Admin dashboard only | **Finding F-1** |
| `reviewer_confidence` | diagnostics | Non-personal | Admin dashboard | RLS |
| `rejection_reason` | diagnostics | **PII risk** — stored raw (not redacted) | Admin dashboard only | **Finding F-1** |
| `review_duration_seconds` | diagnostics | Non-personal | Admin dashboard (TCO) | RLS |
| `reviewed_at` | diagnostics | Non-personal | Admin dashboard | RLS |
| `completed_steps` | diagnostics | Non-personal (UI progress) | Public result page | RLS |
| `progress_token_hash` | diagnostics | Non-personal (SHA-256 hash) | Not exposed | RLS |
| `diagnostic_prompt_version` | diagnostics | Non-personal | Admin evaluation | RLS |
| `diagnostic_rubric_version` | diagnostics | Non-personal | Admin evaluation | RLS |
| `matches_unlocked` | diagnostics | Non-personal | Public result page | RLS |
| `documents_unlocked` | diagnostics | Non-personal | Public result page | RLS |
| `consultation_booked` | diagnostics | Non-personal | Admin dashboard | RLS |
| `consultation_booked_at` | diagnostics | Non-personal | Admin dashboard | RLS |

---

## 3. `audit_log` Table

| Field | Table / Location | Classification | Displayed in | Protection status |
|---|---|---|---|---|
| `id` | audit_log | Non-personal | Admin (TCO/audit) | RLS service_role only |
| `created_at` | audit_log | Non-personal | Admin | RLS |
| `diagnostic_id` | audit_log | **PII** (indirect — links chain to student) | Admin | RLS; retained after student erasure per EU AI Act Art 12 |
| `action` | audit_log | Non-personal | Admin | RLS |
| `actor` | audit_log | Non-personal | Admin | RLS |
| `details` (JSONB) | audit_log | **PII — redacted before insert** (reviewer notes, rejection reason, correction notes all pass through `redact_sensitive_text` before storage) | Admin | RLS; redaction applied at insert time |

---

## 4. `ausbildung_matches` Table

| Field | Table / Location | Classification | Displayed in | Protection status |
|---|---|---|---|---|
| `id` | ausbildung_matches | Non-personal | Admin, public matches endpoint | RLS |
| `created_at` | ausbildung_matches | Non-personal | Admin | RLS |
| `diagnostic_id` | ausbildung_matches | **PII** (indirect) | Admin, public matches endpoint | RLS |
| `matched_positions` | ausbildung_matches | Non-personal (public employer/job data from BA API) | Admin, public matches endpoint (gated by payment) | RLS |
| `reasoning_summary` | ausbildung_matches | **PII** (AI text referencing student's profile characteristics) | Admin | RLS; not in public matches response |
| `status` | ausbildung_matches | Non-personal | Admin | RLS |
| `reviewed_at` | ausbildung_matches | Non-personal | Admin | RLS |

---

## 5. `ausbildung_positions` Table

| Field | Table / Location | Classification | Displayed in | Protection status |
|---|---|---|---|---|
| All fields | ausbildung_positions | Non-personal (public BA API data: employer name, job title, location) | Admin positions cache, public matches response | RLS with anon read allowed — no student PII |

---

## 6. `ai_usage_events` Table

| Field | Table / Location | Classification | Displayed in | Protection status |
|---|---|---|---|---|
| `id`, `created_at`, `provider`, `model`, `request_type` | ai_usage_events | Non-personal | Admin TCO | RLS service_role only |
| `diagnostic_id` | ai_usage_events | **PII** (indirect — links to student) | Admin TCO (aggregated) | RLS; CASCADE SET NULL on student delete |
| `student_id` | ai_usage_events | **PII** (indirect) | Admin TCO (aggregated) | RLS; CASCADE SET NULL |
| `input_tokens`, `output_tokens`, `total_tokens`, `estimated_cost`, `latency_ms`, `success`, `error_type` | ai_usage_events | Non-personal | Admin TCO | RLS |
| `details` (JSONB) | ai_usage_events | Non-personal — DB constraint `ai_usage_events_details_no_pii_keys` blocks insert of PII keys | Admin TCO | RLS; enforced at DB level |

---

## 7. Evaluation Tables (`evaluation_datasets`, `evaluation_examples`, `evaluation_results`, `evaluation_experiments`)

| Field | Table / Location | Classification | Displayed in | Protection status |
|---|---|---|---|---|
| All fields | evaluation_* | Non-personal by design — `input_payload` in `evaluation_examples` is sanitised by `sanitize_evaluation_payload()` before insert (strips name, email, raw_output, additional_info) | Admin evaluation | RLS service_role only |
| `input_payload` | evaluation_examples | **PII risk if unsanitised** — code enforces sanitisation via `sanitize_evaluation_payload()` but there is no DB-level constraint blocking PII keys | Admin evaluation | Application-layer control only — see Finding F-2 |

---

## 8. Intake Form (Frontend)

| Form Step | Field ID | Classification | Sent to | Notes |
|---|---|---|---|---|
| Step 1 | `name` | PII | Backend → students table + AI prompt | Required |
| Step 2 | `email` | PII | Backend → students table + n8n webhook | Required |
| Step 3 | `country` | Sensitive PII | Backend → students table + AI prompt | Required |
| Step 4 | `pathway` | Non-personal | Backend → students table + AI prompt | Required |
| Step 5 | `german_level` | PII | Backend → students table + AI prompt | Required |
| Step 6 | `education_level` | PII | Backend → students table + AI prompt | Required |
| Step 7 | `field_of_study` | PII | Backend → students table + AI prompt | Optional |
| Step 8 | `work_experience_years` | PII | Backend → students table + AI prompt | Required |
| Step 9 | `timeline` | Non-personal | Backend → students table + AI prompt | Required |
| Step 10 | `financial_situation` | Sensitive PII | Backend → students table + AI prompt | Required |
| Step 11 | `english_level` | PII | Backend → students table + AI prompt | Optional |
| Hardcoded | `current_location` | PII (always empty string in current implementation) | Backend → students table | Empty — not collected via UI |
| Hardcoded | `additional_info` | PII (always empty string in current implementation) | Backend → students table | Empty — not collected via UI |
| Consent checkbox | `consent_given` | Non-personal (compliance flag) | Backend → students table | Required; submission rejected server-side if false |

---

## 9. n8n Webhook Payloads

| Webhook | Fields Sent | Classification | Protection |
|---|---|---|---|
| Intake notification (`N8N_WEBHOOK_URL`) | `diagnostic_id`, `student_name`, `student_email`, `pathway`, `review_url` | PII | HTTPS only; masked in logs (post ITEM 3a fix) |
| Approval notification (`N8N_APPROVAL_WEBHOOK_URL`) | `diagnostic_id`, `student_name`, `student_email`, `results_url` | PII | HTTPS only; masked in logs (post ITEM 3a fix) |

---

## 10. Storage Encryption Note

**Supabase encryption at rest:** All Supabase databases (including the klar-advisory project on `uculdafqcybipgmobkjz.supabase.co`, region `eu-central-1`) are encrypted at rest using **AES-256** at the infrastructure level. This applies to all Supabase plans (Free, Pro, Team, Enterprise) and is implemented at the cloud storage layer (AWS EBS/RDS). This is confirmed in Supabase's security documentation and does not require application-level configuration.

**Conclusion:** Infrastructure-level AES-256 encryption at rest is confirmed active. Field-level encryption is **not required** for the current data classification — no health data or biometric data is stored. The highest-classification fields (financial_situation, country/nationality) are covered by the infrastructure encryption and by RLS policies that prevent any unauthenticated access.

**What is not encrypted at the application layer:** The `raw_output` field in `diagnostics` stores the full AI inference response. If this field is queried in a database breach scenario, the content may reference student first names (the AI echoes them in generated text). This is covered by AES-256 at rest and RLS in transit — no additional control is needed at current scale.

---

## Findings

### F-1: Reviewer Notes Stored Unredacted in `diagnostics` Table

**Status:** ⚠️ Known risk, documented

**Detail:** `diagnostics.reviewer_notes`, `diagnostics.reviewer_correction_notes`, and `diagnostics.rejection_reason` are written by the consultant during review and stored raw in the `diagnostics` table. The `audit_log` insert uses redacted versions (via `redact_sensitive_text`), but the raw values persist in `diagnostics`. If a reviewer accidentally includes a student's name or email in their notes, it remains in `diagnostics.reviewer_notes` unredacted.

**Scope:** Admin-only access (service_role key + `ADMIN_API_TOKEN` bearer token). No public exposure path.

**Recommended action:** Add a UX note in the admin dashboard instructing reviewers not to include student names or emails in notes. Optionally apply `redact_sensitive_text` before writing to `diagnostics` as well — this would be a breaking change to the admin review view (notes would appear redacted to the same reviewer who wrote them). A practical middle ground: apply redaction only at export/audit time, not at write time.

---

### F-2: `evaluation_examples.input_payload` Lacks DB-Level PII Constraint

**Status:** ⚠️ Application-layer control only

**Detail:** The `sanitize_evaluation_payload()` function strips PII keys before inserting evaluation examples, but there is no database-level CHECK constraint enforcing this (unlike `ai_usage_events` which has `ai_usage_events_details_no_pii_keys`). A code path that bypasses `sanitize_evaluation_payload()` would silently persist PII.

**Recommended action (not in scope of this sprint):** Add a DB CHECK constraint to `evaluation_examples.input_payload` blocking PII key names, mirroring the pattern in `ai_usage_events`.

---

*Sensitive Data Inventory · Klar · June 2026 · Review before any new field is added to any table*
