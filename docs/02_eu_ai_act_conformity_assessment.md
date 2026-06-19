# EU AI Act — Conformity Assessment Summary
## Klar · Germany Readiness Diagnostic Agent (UC-01)
### Regulation (EU) 2024/1689 · Assessment Date: June 2026

---

## 1. System Description

**System name:** Klar Germany Readiness Diagnostic Agent
**Version:** MVP 1.0
**Operator:** Cleo's Germany Advisory (solo operator)
**Developer:** Lucas Barrios / Kairos Consulting
**Deployment context:** B2C web platform serving Spanish-speaking Latin Americans seeking Germany pathways

**What the system does:**
The system collects a structured profile from a student (language level, education, target pathway, timeline, financial situation) and uses a large language model (Anthropic Claude Sonnet) via a raw Anthropic Python SDK to:
1. Score the student across 6 readiness dimensions (0–100 each)
2. Generate an overall readiness score
3. Produce a month-by-month roadmap
4. Recommend specific programs, organisations, and resources

Results are held in a pending state until a human consultant reviews and approves them before delivery to the student.

---

## 2. Risk Classification

**Risk Level: HIGH RISK**

**Classification basis:** Annex III, Point 3(a) of Regulation (EU) 2024/1689

> "AI systems intended to be used for the purpose of determining access to educational and vocational training institutions, as well as for assessing persons in the context of educational and vocational training institutions, including for the purpose of assessing learning outcomes..."

**Classification reasoning:**

| Criterion | Assessment |
|---|---|
| Does the system profile individuals? | ✅ Yes — scores students across 6 dimensions |
| Does output affect access to education or vocational training? | ✅ Yes — determines whether and how a student can pursue Ausbildung or university in Germany |
| Is the processing automated? | ✅ Yes — LLM agent generates the assessment without direct human involvement in the scoring step |
| Is there meaningful human oversight? | ✅ Yes — mandatory consultant review gate before results are delivered (mitigating factor, does not change classification) |

UC-01 and UC-02 (Ausbildung Position Matcher) are both classified **HIGH RISK** under Annex III Point 3(a). All other use cases in the Klar roadmap are classified Limited Risk or Minimal Risk.

---

## 3. Mandatory Requirements and Compliance Status

### Article 9 — Risk Management System

**Obligation:** Establish and maintain a risk management system throughout the system lifecycle.

**Implementation:**
- Risk register maintained in `research/opportunities_risks.md`
- 9 identified risks with likelihood × impact scoring
- 3 critical risks identified: EU AI Act non-compliance (20/25), GDPR breach (15/25), incorrect visa advice (15/25)
- Risk review scheduled at each phase milestone (MVP → Pilot → Scale)
- Mitigation owner assigned for each risk

**Status:** ✅ Implemented at MVP level. Full risk management system to be formalised before pilot launch.

---

### Article 10 — Data and Data Governance

**Obligation:** Training, validation and testing data must be relevant, representative, and free from errors and biases. Data governance practices must be documented.

**Implementation:**
- UC-01 does not use custom training data — it uses a pre-trained foundation model (Claude Sonnet) via API
- Student profile data used as inference input only, not for model training
- Input data governance: structured intake form with defined field types and validation
- Bias risk: scoring rubric is explicitly defined in the system prompt to ensure consistent application across nationalities, ages, and genders
- No personal data is used for model fine-tuning

**Status:** ✅ Applicable obligations met. Model training data governance is Anthropic's responsibility (documented in their usage policies).

---

### Article 11 — Technical Documentation

**Obligation:** Maintain technical documentation before the system is placed on the market.

**Implementation:**
- Technical Documentation Outline prepared (see separate document)
- System architecture documented in README.md
- API documentation auto-generated via FastAPI /docs
- Agent prompt and scoring rubric documented in `backend/agents/germany_diagnostic.py`

**Status:** 🔄 Outline complete. Full technical documentation to be completed before pilot launch (Week 3).

---

### Article 12 — Record-Keeping and Logging

**Obligation:** High-risk AI systems must maintain logs to the extent necessary to enable the identification of situations that may result in the AI system presenting a risk.

**Implementation:**
- `audit_log` table in Supabase records every event:
  - `diagnostic_created` — when agent generates a score
  - `review_approved` / `review_rejected` — when consultant acts
  - Actor field distinguishes `system` from `consultant`
  - Timestamps on all events (UTC)
- Logs are immutable (insert-only, no update operations on audit_log)
- Retention: 24 months (configurable in Supabase)

**Status:** ✅ Implemented and active from Day 1 of deployment.

---

### Article 13 — Transparency and Provision of Information

**Obligation:** High-risk AI systems must be transparent. Users must be informed they are interacting with an AI system and understand its capabilities and limitations.

**Implementation:**
- Results page footer: "Results are reviewed by a human consultant and are for guidance only. Not legal or immigration advice."
- Demo banner on sample results page clearly labels AI-generated content
- Pending screen explains consultant review process to student
- System prompt instructs the agent to be honest about uncertainty
- No results are presented as definitive legal or immigration determinations

**Status:** ✅ Implemented. Full transparency notice to be added to Terms of Service before pilot.

---

### Article 14 — Human Oversight

**Obligation:** High-risk AI systems must be designed to allow natural persons to effectively oversee and intervene.

**Implementation:**
- **Mandatory review gate:** No diagnostic result reaches a student without explicit consultant approval
- Admin dashboard displays all pending diagnostics with full AI output visible for review
- Consultant can: approve, reject, or add reviewer notes before approval
- Reject path prevents delivery entirely
- Consultant can override any element of the AI output via the notes field
- The human review gate was designed specifically to satisfy Article 14 — it is not optional and cannot be bypassed by the student

**Status:** ✅ Implemented. This is the core compliance mechanism of the system.

---

### Article 15 — Accuracy, Robustness and Cybersecurity

**Obligation:** High-risk AI systems must achieve appropriate levels of accuracy and be robust.

**Implementation:**
- Scoring rubric explicitly defined in system prompt with numeric anchors (e.g. German level: none=10, A1=20, A2=35...)
- Temperature set to 0.3 to reduce output variability
- JSON-structured output enforced via response_format parameter
- Error handling: if agent fails, 500 error is returned and no partial result is saved
- Consultant review catches any inaccurate outputs before delivery
- Cybersecurity: API keys stored in environment variables, never committed to source control. HTTPS enforced on all deployments.

**Status:** ✅ Implemented at MVP level. Formal accuracy testing (disaggregated by nationality and pathway) scheduled before scale deployment.

---

## 4. Statement of Conformity

This Conformity Assessment Summary confirms that the Klar Germany Readiness Diagnostic Agent (UC-01) has been assessed against the mandatory requirements of the EU AI Act (Regulation EU 2024/1689) applicable to High Risk AI systems under Annex III.

At MVP stage (June 2026), the system implements all mandatory obligations at a level appropriate to its deployment scale (pilot with <20 users). Full conformity documentation, formal bias testing, and external audit are planned before the system scales beyond 100 monthly users, and no later than the EU AI Act enforcement deadline for Annex III systems (August 2, 2026).

**Key compliance statement:** The mandatory human review gate (Article 14) is the central architectural decision that simultaneously satisfies:
- Article 14 — human oversight requirement
- GDPR Article 22 — no solely automated decision-making affecting legal status
- Operational risk mitigation — incorrect visa advice cannot reach a student without human validation

**Prepared by:** Lucas Barrios, AI Consulting & Integration, Ironhack Berlin
**Date:** June 2026

---

*EU AI Act Conformity Assessment Summary · Klar · Regulation (EU) 2024/1689*
