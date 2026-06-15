# GDPR — Data Protection Impact Assessment (DPIA)
## Klar · Germany Readiness Diagnostic Agent (UC-01)
### Regulation (EU) 2016/679, Article 35 · June 2026

---

## 1. Why a DPIA Is Required

A DPIA is mandatory when processing is "likely to result in a high risk to the rights and freedoms of natural persons" (GDPR Article 35). UC-01 meets this threshold for three reasons:

1. **Systematic profiling** — the system profiles individuals using personal data to evaluate characteristics related to their education, career prospects, and economic situation (Article 35(3)(a))
2. **Large-scale processing** — the system is designed to scale to thousands of students across multiple countries
3. **Combination with High Risk AI Act classification** — the system is classified High Risk under EU AI Act Annex III Point 3(a), reinforcing the need for a DPIA

---

## 2. Description of the Processing

### 2.1 Nature of Processing

The system collects personal data from students via a web form, transmits it to an AI agent for automated scoring, stores the results in a database, and delivers approved results by email. The processing involves:

- Collection of personal and demographic data
- Transmission to a US-based third-party AI provider (Anthropic)
- Automated profiling and scoring
- Storage in a cloud database
- Human review by a consultant
- Delivery of results to the student

### 2.2 Scope of Processing

| Data Element | Personal Data? | Sensitive? | Purpose |
|---|---|---|---|
| Full name | ✅ Yes | No | Personalisation of results |
| Email address | ✅ Yes | No | Results delivery, identity |
| Country of origin | ✅ Yes | Borderline (nationality) | Pathway eligibility scoring |
| Age | ✅ Yes | No | Pathway fit scoring (Ausbildung age preference) |
| German language level | ✅ Yes | No | Core scoring dimension |
| English language level | ✅ Yes | No | Supplementary scoring |
| Education level | ✅ Yes | No | Core scoring dimension |
| Field of study | ✅ Yes | No | Pathway matching |
| Work experience | ✅ Yes | No | Core scoring dimension |
| Timeline | No | No | Roadmap generation |
| Financial situation | ✅ Yes | Borderline (financial status) | Financial readiness scoring |
| Current location | ✅ Yes | No | Context for recommendations |
| AI-generated score | ✅ Yes | No | The profiling output itself |
| Roadmap content | ✅ Yes | No | Personalised to individual |
| Audit log entries | ✅ Yes | No | Compliance and review record |

**Special category data:** None collected directly. Country of origin may indirectly indicate ethnicity but is not processed for this purpose.

### 2.3 Purposes of Processing

| Purpose | Legal Basis |
|---|---|
| Delivering the diagnostic service requested by the student | Article 6(1)(b) — performance of a contract / pre-contractual steps at the request of the data subject |
| Storing diagnostic results for consultant review | Article 6(1)(b) — necessary for service delivery |
| Audit logging for EU AI Act Article 12 compliance | Article 6(1)(c) — legal obligation |
| Improving service quality (aggregate, anonymised only) | Article 6(1)(f) — legitimate interests (no individual profiling) |

### 2.4 Data Flows

```
Student (LATAM country)
    ↓ [HTTPS]
Next.js Frontend (Vercel — EU/US)
    ↓ [HTTPS]
FastAPI Backend (Render — US)
    ↓ [HTTPS API call]
Anthropic Claude API (US) ← DATA TRANSFER OUTSIDE EU
    ↓ [JSON response]
FastAPI Backend
    ↓ [Supabase SDK]
Supabase Database (EU region — Frankfurt)
    ↓ [Supabase SDK]
Admin Dashboard ← Consultant review
    ↓ [Email via future n8n/email provider]
Student (results delivery)
```

**Third-party processors:**
| Processor | Location | Data Received | Legal Basis for Transfer |
|---|---|---|---|
| Anthropic (Claude API) | United States | Full student profile (inference input) | Standard Contractual Clauses (SCCs) — Anthropic DPA |
| Supabase | EU (Frankfurt) | All stored data | No transfer — EU-based |
| Vercel | US (CDN global) | No personal data — static assets only | N/A |
| Render | US | Processes data in transit (no storage) | SCCs |

---

## 3. Assessment of Necessity and Proportionality

### 3.1 Is Processing Necessary?

The processing is necessary to deliver the service. The student explicitly requests the diagnostic and provides their data for this purpose. Each data element collected serves a specific scoring function:

- Name and email → identity and delivery (cannot be removed)
- Country → eligibility varies significantly by country (cannot be removed)
- German level → the single most important scoring factor (cannot be removed)
- Financial situation → German student visa requires ~€11,000 blocked account (cannot be removed)
- Age → optional but affects Ausbildung recommendations (students over 35 face more barriers)

No data elements are collected beyond what is necessary for the stated purpose.

### 3.2 Is the Scope Proportionate?

The scope is proportionate because:
- Data is used only for the stated diagnostic purpose
- No data is sold, shared with advertisers, or used for unrelated profiling
- Data is not used to train or fine-tune the AI model
- Retention is limited (see Section 5)
- The student explicitly initiates the process and can withdraw at any time

---

## 4. Risk Assessment

### Risk 1 — Incorrect AI Assessment Causing Harm
**Description:** The AI agent generates an inaccurate readiness score, leading a student to make incorrect decisions about their Germany pathway (e.g. moving too early, or being discouraged when they shouldn't be).

**Likelihood:** Medium (3/5) — LLMs can produce inconsistent outputs; scoring rubric reduces but doesn't eliminate this.

**Impact:** High (4/5) — A student acting on incorrect advice could waste significant money and time.

**Risk score:** 12/25

**Mitigation:** Mandatory human review gate (Article 14). Consultant validates all outputs before delivery. Disclaimer on results page: "For guidance only, not legal or immigration advice."

**Residual risk:** Low — no student receives results without human validation.

---

### Risk 2 — Data Breach / Unauthorised Access
**Description:** Student personal data (including financial situation and country of origin) is accessed by unauthorised parties.

**Likelihood:** Low (2/5) — Supabase RLS policies, API key management, HTTPS enforced.

**Impact:** High (4/5) — Exposure of financial situation and nationality could cause significant harm.

**Risk score:** 8/25

**Mitigation:** Row-Level Security on all Supabase tables. API keys in environment variables, never in source code. GitHub push protection blocks accidental commits. Service role key (read/write) separated from anon key (read-only). HTTPS enforced on all endpoints.

**Residual risk:** Low.

---

### Risk 3 — Transfer to Anthropic (US) Without Adequate Safeguards
**Description:** Student personal data is sent to Anthropic's US-based API without adequate transfer mechanism.

**Likelihood:** Medium (3/5) — Transfer happens on every diagnostic request.

**Impact:** High (4/5) — GDPR Article 46 requires adequate safeguards for transfers outside EEA.

**Risk score:** 12/25

**Mitigation:** Anthropic offers a Data Processing Agreement (DPA) with Standard Contractual Clauses. Before pilot launch: sign Anthropic DPA, document the transfer in processing records. Alternative option at scale: evaluate EU-based LLM providers (Mistral AI — Paris-based) to eliminate the transfer risk entirely.

**Residual risk:** Medium until DPA is signed. Low after.

---

### Risk 4 — Automated Decision-Making Without Consent
**Description:** The AI score could be considered a solely automated decision with legal/significant effect under GDPR Article 22.

**Likelihood:** Medium (3/5) — The score affects whether a student pursues Germany, which is a significant life decision.

**Impact:** Medium (3/5) — Article 22 violation could result in regulatory action.

**Risk score:** 9/25

**Mitigation:** The human review gate ensures no decision is solely automated — a consultant reviews every score before delivery. The disclaimer makes clear results are guidance only. Students have the right to request human review (which is already mandatory). No automated rejection occurs — the system only generates scores, it never denies access.

**Residual risk:** Low — the architecture explicitly prevents solely automated decisions.

---

## 5. Data Subject Rights

| Right | Applicable? | How Implemented |
|---|---|---|
| Right of access (Article 15) | ✅ Yes | Student can request full diagnostic record by emailing consultant. Response within 30 days. |
| Right to rectification (Article 16) | ✅ Yes | Student can request correction of incorrect personal data. Resubmission of form available. |
| Right to erasure (Article 17) | ✅ Yes | Student can request deletion of all records. Implemented via Supabase cascade delete on students table. Audit log anonymised (diagnostic_id retained, personal data removed). |
| Right to restriction (Article 18) | ✅ Yes | Processing can be restricted on request pending review. |
| Right to data portability (Article 20) | ✅ Yes | Full diagnostic JSON exportable on request. |
| Right to object (Article 21) | ✅ Yes | Student can object to processing. Service cannot be delivered without the data, so objection results in account deletion. |
| Rights re: automated decisions (Article 22) | ✅ Yes | No solely automated decisions — human review mandatory. Students can request human review explanation at any time. |

**Contact for rights requests:** hello@klar.app (to be set up before pilot launch)
**Response deadline:** 30 days (extendable to 90 days for complex requests)

---

## 6. Retention Policy

| Data Type | Retention Period | Justification |
|---|---|---|
| Student profile data | 24 months from last activity | Service delivery and follow-up |
| Diagnostic results | 24 months from creation | Audit trail, EU AI Act Article 12 |
| Audit log entries | 24 months from creation | EU AI Act compliance requirement |
| Email correspondence | 12 months | Standard business retention |

After retention period: personal data deleted, aggregate/anonymised data retained for product improvement.

---

## 7. Conclusion and Sign-Off

This DPIA identifies four material risks associated with the Klar UC-01 diagnostic system. All four risks have identified mitigations. The most significant residual risk (Anthropic DPA not yet signed) has a clear action item: sign the Anthropic DPA before pilot launch.

The system architecture — specifically the mandatory human review gate — is the single most important design decision for GDPR compliance. It simultaneously satisfies Article 22 (no solely automated decisions), reduces the risk of incorrect advice reaching students, and implements Article 14 of the EU AI Act.

**DPIA conclusion:** Processing may proceed, subject to completion of the Anthropic DPA before pilot launch and implementation of the data subject rights process.

**Prepared by:** Lucas Barrios, AI Consulting & Integration, Ironhack Berlin
**Date:** June 2026
**Review date:** September 2026 (before scale launch)

---

*GDPR Data Protection Impact Assessment · Klar · Regulation (EU) 2016/679, Article 35 · June 2026*
-e 

---

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
