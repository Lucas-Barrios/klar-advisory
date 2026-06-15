# GDPR — Data Flows and Data Subject Rights
## Klar — Germany Readiness Diagnostic Platform
### Regulation (EU) 2016/679 · June 2026

---

## 1. Data Processing Register

This document records all personal data processing activities for the Klar platform in compliance with GDPR Article 30 (Records of Processing Activities).

**Controller:** Cleo's Germany Advisory
**Contact:** hello@klar.app
**DPO:** Not required at current scale (fewer than 250 employees, processing not systematic or large-scale at MVP stage). DPO appointment to be reviewed at scale.

---

## 2. Processing Activity 1 — Student Diagnostic Submission

| Field | Detail |
|---|---|
| **Activity name** | Germany Readiness Diagnostic — Student Intake |
| **Purpose** | Collect student profile data to generate a personalised Germany readiness score and roadmap |
| **Legal basis** | Article 6(1)(b) — performance of a contract / pre-contractual steps at the request of the data subject |
| **Data categories** | Name, email, country, age, German level, English level, education level, field of study, work experience, timeline, financial situation, current location, additional context |
| **Data subjects** | Latin American students and professionals seeking Germany pathways |
| **Recipients** | Anthropic (US) — inference only, no storage; Supabase (EU-Frankfurt) — storage |
| **Retention** | 24 months from last activity |
| **Transfer outside EEA** | Yes — Anthropic (US). Legal basis: Standard Contractual Clauses (Anthropic DPA) |
| **Security measures** | HTTPS, Row-Level Security, environment variable key management |

---

## 3. Processing Activity 2 — AI Diagnostic Generation

| Field | Detail |
|---|---|
| **Activity name** | Automated Readiness Assessment |
| **Purpose** | Generate readiness scores, roadmap, and recommendations using AI agent |
| **Legal basis** | Article 6(1)(b) — necessary for service delivery |
| **Data categories** | Student profile (as above) + AI-generated scores and recommendations |
| **Data subjects** | Students who completed the intake form |
| **Recipients** | Anthropic API (inference); Supabase (storage of results) |
| **Retention** | 24 months |
| **Automated decision-making** | Scoring is automated BUT subject to mandatory human review before delivery. Not a solely automated decision per Article 22. |
| **Transfer outside EEA** | Yes — Anthropic (US). SCCs apply. |

---

## 4. Processing Activity 3 — Consultant Review and Approval

| Field | Detail |
|---|---|
| **Activity name** | Human Review Gate |
| **Purpose** | Consultant reviews AI-generated diagnostic before delivering to student. Ensures accuracy and legal safety. |
| **Legal basis** | Article 6(1)(b) — service delivery; Article 6(1)(c) — EU AI Act Article 14 compliance |
| **Data categories** | Full diagnostic record including student profile and AI outputs |
| **Data subjects** | Students |
| **Recipients** | Cleo (consultant) — access via admin dashboard |
| **Retention** | 24 months |
| **Transfer outside EEA** | None — admin dashboard hosted on Vercel (static), data retrieved from Supabase EU |

---

## 5. Processing Activity 4 — Audit Logging

| Field | Detail |
|---|---|
| **Activity name** | System Audit Log |
| **Purpose** | Record all system actions for EU AI Act Article 12 compliance and incident investigation |
| **Legal basis** | Article 6(1)(c) — legal obligation (EU AI Act Article 12) |
| **Data categories** | Diagnostic ID, action type, actor (system/consultant), timestamp, action details |
| **Data subjects** | Students (indirectly via diagnostic ID) |
| **Recipients** | Internal only — accessible via Supabase service role |
| **Retention** | 24 months — immutable (insert-only, no updates or deletes) |
| **Transfer outside EEA** | None — Supabase EU (Frankfurt) |

---

## 6. Processing Activity 5 — Results Delivery

| Field | Detail |
|---|---|
| **Activity name** | Email Notification and Results Delivery |
| **Purpose** | Notify student when results are approved and provide link to their results page |
| **Legal basis** | Article 6(1)(b) — performance of contract |
| **Data categories** | Name, email, diagnostic ID |
| **Data subjects** | Students |
| **Recipients** | Email service provider (n8n + SMTP provider — EU-based preferred) |
| **Retention** | Email logs: 12 months |
| **Transfer outside EEA** | Depends on email provider selected. EU-based provider (Brevo, Postmark EU) preferred. |

---

## 7. Full Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        DATA FLOW — KLAR                             │
└─────────────────────────────────────────────────────────────────────┘

STUDENT (LATAM)
    │
    │ Submits intake form
    │ [HTTPS — encrypted in transit]
    ▼
NEXT.JS FRONTEND (Vercel — Global CDN)
    │ No personal data stored here
    │ Form data sent directly to backend
    │ [HTTPS]
    ▼
FASTAPI BACKEND (Render — US)
    │ Receives and validates student profile
    │ Stored in memory only during request
    │ [HTTPS API call]
    ├──────────────────────────────────────────►
    │                               ANTHROPIC CLAUDE API (US)
    │                               • Receives full student profile
    │                               • Generates score + roadmap
    │                               • Returns JSON — no data retained
    │                               • Covered by Anthropic DPA + SCCs
    │◄──────────────────────────────────────────
    │
    │ [Supabase Python SDK — encrypted]
    ▼
SUPABASE DATABASE (EU — Frankfurt, Germany)
    │ Stores:
    │   • students table (personal data)
    │   • diagnostics table (AI output)
    │   • audit_log table (compliance)
    │
    ├── ADMIN DASHBOARD (Next.js — Vercel)
    │       │ Consultant retrieves pending diagnostics
    │       │ Reviews, approves or rejects
    │       │ [Supabase anon key — RLS enforced]
    │       ▼
    │   CLEO (CONSULTANT) — reviews on screen, no download
    │
    │ On approval:
    │ [n8n webhook — EU-based]
    ▼
EMAIL PROVIDER
    │ Sends approval notification to student
    │ Contains: name, results page link only
    │ No score data in email body
    ▼
STUDENT — accesses results via link
    │ [HTTPS]
    ▼
RESULTS PAGE (Next.js — Vercel)
    • Fetches from Supabase using diagnostic ID
    • Student sees: score, roadmap, recommendations
    • Disclaimer: "For guidance only. Not legal advice."
```

---

## 8. Third-Party Data Processor Register

| Processor | Location | Data Shared | Legal Basis | DPA Status |
|---|---|---|---|---|
| Anthropic (Claude API) | United States | Full student profile (inference input only, no storage) | Standard Contractual Clauses | **Action required: Sign Anthropic DPA before pilot** |
| Supabase | EU (Frankfurt) | All stored data | EU-based — no transfer | Supabase DPA available at supabase.com/privacy |
| Vercel | US (CDN) | No personal data — static assets and HTML only | N/A | N/A |
| Render | US | Processes data in transit, no persistent storage | SCCs | Render DPA available |
| n8n (self-hosted or cloud) | EU preferred | Name, email, diagnostic ID only | SCCs if cloud — self-hosted preferred | Configure before pilot |

---

## 9. Data Subject Rights

GDPR grants the following rights to all data subjects (students). Each right is listed with the implementation method.

---

### Right of Access (Article 15)
**What it means:** The student can request a copy of all personal data held about them.

**What we hold:** Student profile, diagnostic scores, roadmap, recommendations, audit log entries referencing their diagnostic, email correspondence.

**How to exercise:** Email hello@klar.app with subject "Data Access Request" and full name and email used for the diagnostic.

**Response:** Within 30 calendar days. Delivered as a JSON export of all records linked to the student's email.

---

### Right to Rectification (Article 16)
**What it means:** The student can request correction of inaccurate personal data.

**How to exercise:** Email hello@klar.app with the correction needed. For diagnostic re-run with corrected data, student resubmits the form.

**Response:** Within 30 days. Updated immediately for simple field corrections. Diagnostic re-run offered free of charge if the error materially affected the score.

---

### Right to Erasure (Article 17)
**What it means:** The student can request deletion of all personal data ("right to be forgotten").

**Exceptions:** Audit log entries cannot be fully deleted (legal obligation under EU AI Act Article 12) but will be anonymised — the diagnostic ID is retained, all personal identifiers removed.

**How to exercise:** Email hello@klar.app with subject "Erasure Request."

**Implementation:** Supabase cascade delete on the students table removes the student record and all linked diagnostic data. Audit log anonymised via SQL UPDATE removing personal fields.

**Response:** Confirmed in writing within 30 days.

---

### Right to Restriction of Processing (Article 18)
**What it means:** The student can request that processing be restricted while a dispute is resolved.

**How to exercise:** Email hello@klar.app.

**Implementation:** Student account flagged as restricted in Supabase. No further processing until dispute is resolved.

---

### Right to Data Portability (Article 20)
**What it means:** The student can request their data in a machine-readable format for transfer to another service.

**How to exercise:** Email hello@klar.app with subject "Portability Request."

**Format:** JSON export of all stored data.

**Response:** Within 30 days.

---

### Right to Object (Article 21)
**What it means:** The student can object to processing of their personal data.

**Context for Klar:** Processing is based on contract performance (Article 6(1)(b)), not legitimate interests. Right to object therefore applies to any processing beyond direct service delivery.

**How to exercise:** Email hello@klar.app.

**Consequence:** If the student objects to service delivery processing, the service cannot be provided and all data is erased.

---

### Rights Related to Automated Decision-Making (Article 22)
**What it means:** The student has the right not to be subject to a decision based solely on automated processing if it produces legal or similarly significant effects.

**Klar's position:** No solely automated decisions are made. Every diagnostic is reviewed and approved by a human consultant before delivery. The AI generates a score; the consultant validates it and approves delivery.

**Student entitlement:** The student can request an explanation of the scoring rationale. The consultant provides this via the reviewer notes field or by email.

**How to exercise:** Email hello@klar.app.

---

## 10. Data Breach Response Procedure

**Detection:** Any team member who identifies a potential breach immediately notifies Cleo (data controller).

**Assessment (within 24 hours):**
- What data was accessed or exposed?
- How many individuals affected?
- What is the likely risk to individuals?

**Reporting (within 72 hours if high risk):**
- Notify the relevant supervisory authority (Berlin Data Protection Authority — BlnBDI)
- Notification to: https://www.datenschutz-berlin.de
- If high risk to individuals: also notify affected students directly

**Documentation:** All breach events documented in the incident log regardless of severity.

---

*GDPR Data Flows and Data Subject Rights · Klar · Regulation (EU) 2016/679 · June 2026*
