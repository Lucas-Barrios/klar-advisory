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
| LangSmith (LangChain Inc.) | United States (EU endpoint: eu.api.smith.langchain.com) | Full LLM call inputs and outputs for every AI request (student profile data included in prompt) | SCCs — DPA status: unconfirmed, action required before pilot |
| Resend | Ireland (EU-west-1) | Student email address and first name only (transactional emails: diagnostic approval notification, payment confirmation) | No transfer — EU-based (Ireland) |
| Supabase | EU (Frankfurt) | All stored data | No transfer — EU-based |
| Vercel | US (CDN global) | No personal data — static assets only | N/A |
| Render | US | Processes data in transit (no storage) | SCCs |

**Note on Anthropic and LangSmith:** LangSmith receives the same input data as Anthropic on every traced call via `wrap_anthropic()`. LangSmith's DPA must be signed alongside Anthropic's before pilot.

---

## 3. Necessity and Proportionality Assessment

**Is the processing necessary?** Yes. Each data element collected maps to a specific, non-substitutable scoring function: German level is the single highest-weighted scoring dimension and cannot be omitted; financial situation is necessary because the German student visa requires demonstrable proof of ~€11,000 in a blocked account, making financial readiness a material eligibility factor, not an incidental detail; country of origin determines which visa pathway and recognition process applies.

**Is the scope proportionate?** Yes, on three grounds: (1) no data is collected beyond what each scoring dimension requires; (2) data is never used for purposes beyond the stated diagnostic service — no advertising, no resale, no secondary profiling; (3) data is not used to train or fine-tune any model, eliminating the indefinite-retention risk associated with training data; (4) the student initiates the process voluntarily and may withdraw at any point before approval.

---

## 4. Risk Assessment

### Risk 1 — Incorrect AI Assessment Causing Material Harm to the Student
**Likelihood:** 3/5 — LLM outputs can vary; scoring rubric reduces but does not eliminate this.
**Impact:** 4/5 — A student acting on an inaccurate score could make a costly, time-sensitive relocation decision.
**Risk score:** 12/25
**Mitigation:** Mandatory human review gate (Article 14 mechanism, doubling as the Article 22 safeguard described in Section 7). Explicit "guidance only" disclaimer on every results view.
**Residual risk:** Low.

### Risk 2 — Data Breach / Unauthorised Access
**Likelihood:** 2/5 — RLS policies, key separation, and HTTPS reduce likelihood.
**Impact:** 4/5 — Exposure of financial situation and nationality data could cause real harm to affected students.
**Risk score:** 8/25
**Mitigation:** Supabase Row-Level Security on all tables; service-role (write) and anon (read-only) keys kept separate; secrets never committed to source control, enforced by GitHub push protection; HTTPS enforced on all endpoints.
**Residual risk:** Low.

### Risk 3 — International Transfer to Anthropic (US) Without Adequate Safeguards
**Likelihood:** 5/5 — this transfer occurs on every single diagnostic request; it is not an edge case but the central data flow of the system.
**Impact:** 4/5 — Article 44 requires an adequate transfer mechanism for any transfer of personal data outside the EEA; absence of one would render the entire processing activity unlawful, not just risky.
**Risk score:** 20/25 (recalculated upward — see Section 8 for full treatment)
**Mitigation:** See Section 8 below for the complete transfer mechanism analysis.
**Residual risk:** See Section 8 sign-off.

### Risk 4 — Automated Decision-Making Without Adequate Safeguard
**Likelihood:** 3/5 — the AI-generated score, absent intervention, would constitute the entirety of the decision basis.
**Impact:** 3/5 — Article 22 violation risk if no qualifying safeguard is in place.
**Risk score:** 9/25
**Mitigation:** Human review gate ensures the decision is never "based solely on automated processing" — see Section 7.
**Residual risk:** Low, conditional on the human review step remaining structurally mandatory (verified — enforced at the database layer, not merely procedurally).

---

## 5. Data Subject Rights

| Right | Implementation |
|---|---|
| Access (Art. 15) | Email-based request to hello@klar.app; full JSON export within 30 days |
| Rectification (Art. 16) | Correction request via email; resubmission triggers a fresh diagnostic free of charge if the error materially affected scoring |
| Erasure (Art. 17) | Supabase cascade delete on the students table removes the student and all linked diagnostic records; audit log entries are anonymised (personal fields stripped, diagnostic_id retained for Article 12 continuity) |
| Restriction (Art. 18) | Account flagged as restricted pending dispute resolution; no further processing until resolved |
| Portability (Art. 20) | Full diagnostic record exportable as machine-readable JSON on request |
| Objection (Art. 21) | Since processing rests on Article 6(1)(b) contract performance rather than legitimate interest, objection results in inability to provide the service and triggers erasure |
| Article 22 safeguard | See Section 7 — no solely automated decision is ever made; explanation of scoring rationale available on request |

**Contact:** hello@klar.app · **Response window:** 30 days (extendable to 90 for complex requests under Article 12(3))

---

## 6. Retention Policy

| Data Type | Retention | Justification |
|---|---|---|
| Student profile | 24 months from last activity | Service delivery and follow-up |
| Diagnostic results | 24 months from creation | Audit trail, EU AI Act Article 12 |
| Audit log | 24 months, anonymised after student erasure | EU AI Act Article 12 compliance |
| Email correspondence | 12 months | Standard business retention |

---

## 7. Article 22 Safeguard Analysis

GDPR Article 22(1) gives a data subject the right not to be subject to a decision "based solely on automated processing" that produces legal effects or similarly significantly affects them. Klar's architecture is designed so that this provision is never triggered in the first place, rather than relying on one of the Article 22(2) exceptions:

- The AI agent's output is held in a pending state that is structurally incapable of reaching the student without an affirmative consultant action
- The consultant reviews the complete substantive output (all scores, summary, roadmap) before approving — this is a genuine, informed review, not a procedural rubber stamp, satisfying the EDPB's "meaningful human involvement" standard
- The consultant can reject the output outright, which is functionally equivalent to overriding the automated result
- No automated rejection or denial of service ever occurs — the system only ever generates a score for the consultant's consideration; it does not itself grant or deny anything

**Conclusion:** Processing does not fall within the scope of Article 22(1) because the relevant decision is not, in fact, based solely on automated processing.

---

## 8. International Transfer Analysis — Anthropic (United States)

This is the highest-rated residual risk in this DPIA and is given dedicated treatment.

**Nature of the transfer:** On every diagnostic request, the full student profile (name, country, age, language levels, education, work experience, timeline, financial situation, location, and any free-text context) is transmitted to Anthropic's API, hosted in the United States, for inference. Anthropic's standard API terms specify that this data is not used to train models and is retained only transiently for abuse-monitoring purposes before deletion.

**Transfer mechanism under Chapter V GDPR:**
The United States is not currently covered by a general EU adequacy decision for commercial data transfers of this kind (the EU-US Data Privacy Framework covers participating certified organisations specifically — this must be verified against Anthropic's current certification status). Absent confirmed adequacy coverage, the lawful transfer mechanism is Article 46(2)(c): Standard Contractual Clauses (SCCs), made available by Anthropic as part of its commercial Data Processing Addendum.

**Required actions before this transfer can be considered fully compliant:**
1. Execute Anthropic's Data Processing Addendum, incorporating the SCCs, before pilot launch
2. Conduct a Transfer Impact Assessment (TIA) confirming that, notwithstanding US surveillance laws (e.g., FISA 702), the SCCs together with Anthropic's technical and organisational measures provide a level of protection essentially equivalent to that guaranteed in the EU, per the Schrems II standard
3. Document the outcome of the TIA in this DPIA as an addendum once complete

**Interim risk position (as of this assessment, prior to DPA execution):** The transfer is currently occurring on a provisional basis during MVP testing with synthetic and consenting pilot-tester data only. No real student personal data should be processed through this pathway in a live commercial pilot until the DPA is executed. This is the single most time-sensitive compliance action in the entire project.

**Planned long-term mitigation:** Evaluate EU-based foundation model providers (e.g., Mistral AI, headquartered in Paris) as an alternative inference provider, which would eliminate this transfer risk entirely rather than merely mitigating it. This is recorded as a Phase 3 (Scale) consideration in the Strategic Deployment Plan.

---

## 9. Residual Risk Sign-Off

| Risk | Pre-mitigation score | Post-mitigation residual | Acceptable to proceed? |
|---|---|---|---|
| Incorrect AI assessment | 12/25 | Low | Yes — human review gate active from Day 1 |
| Data breach / unauthorised access | 8/25 | Low | Yes — RLS and key separation active from Day 1 |
| International transfer to Anthropic | 20/25 | Medium — pending DPA execution | Conditional — proceed with synthetic/consenting test data only until DPA is signed; full real-user pilot launch is gated on this action |
| Automated decision-making | 9/25 | Low | Yes — Article 22 safeguard structurally enforced |

**Overall DPIA conclusion:** Processing may proceed for MVP testing and limited pilot recruitment under the current safeguards, with one binding condition: the Anthropic DPA with Standard Contractual Clauses must be executed before any diagnostic is run using real, non-test student personal data at pilot scale. This condition is the controller's explicit pre-requisite for treating the international transfer risk as adequately mitigated rather than merely identified.

**Assessed by:** Lucas Barrios, AI Consulting & Integration, Ironhack Berlin
**Date:** June 2026
**Sign-off status:** Approved to proceed, subject to the binding condition above
**Scheduled review:** Before Pilot phase transition (Week 3), and again before Scale phase (Month 2)

---

*GDPR Data Protection Impact Assessment · Klar · Regulation (EU) 2016/679, Article 35 · June 2026*

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
| LangSmith (LangChain Inc.) | United States (EU endpoint: eu.api.smith.langchain.com) | Full LLM call inputs and outputs for every AI request (student profile data included in prompt) | SCCs | **DPA status: unconfirmed — action required before pilot** |
| Resend | Ireland (EU-west-1) | Student email address and first name only (transactional emails: diagnostic approval notification, payment confirmation) | No transfer — EU-based (Ireland) | No DPA required — EU-based |
| Supabase | EU (Frankfurt) | All stored data | EU-based — no transfer | Supabase DPA available at supabase.com/privacy |
| Vercel | US (CDN) | No personal data — static assets and HTML only | N/A | N/A |
| Render | US | Processes data in transit, no persistent storage | SCCs | Render DPA available |
| n8n (self-hosted or cloud) | EU preferred | Name, email, diagnostic ID only | SCCs if cloud — self-hosted preferred | Configure before pilot |

**Note on Anthropic and LangSmith:** LangSmith receives the same input data as Anthropic on every traced call via `wrap_anthropic()`. LangSmith's DPA must be signed alongside Anthropic's before pilot.

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
