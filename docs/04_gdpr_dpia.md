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
