# EU AI Act — Technical Documentation Outline
## Klar · Germany Readiness Diagnostic Agent (UC-01)
### Regulation (EU) 2024/1689, Article 11 · June 2026

---

This document is the **table of contents and skeleton** of the full Technical Documentation that would be required before placing the Klar system on the market at scale. Each section heading is accompanied by a description of what the full documentation would contain.

---

## Section 1 — General Description of the AI System

**1.1 System Identity**
Full name, version number, deployment date, operator identity, developer identity, intended purpose statement.

**1.2 Intended Purpose**
Detailed description of what the system is designed to do, the population it serves (Latin American students aged 18–45 seeking Germany pathways), the geographic scope (Latin America → Germany), and what the system explicitly does NOT do (it does not provide legal immigration advice, it does not make visa decisions, it does not guarantee outcomes).

**1.3 Interaction with Other Systems**
Description of integrations: Anthropic Claude API (LLM inference), Supabase (data storage and retrieval), n8n (notification automation), Vercel (frontend hosting), Render (backend hosting). Data flows between each system component.

**1.4 System Architecture Diagram**
Visual diagram showing: Student → Next.js frontend → FastAPI backend → LangChain agent → Claude API → Supabase → Admin dashboard → Consultant → Student (approved results). Full request/response flow with data types at each step.

---

## Section 2 — Description of the Elements of the AI System

**2.1 Model Description**
Identification of the foundation model: Anthropic Claude Sonnet (claude-sonnet-4-6). Description of model capabilities and limitations. Reference to Anthropic's model card and usage policies.

**2.2 System Prompt and Agent Logic**
Full text of the system prompt used for UC-01. Description of the scoring rubric (6 dimensions, weighting, anchor values). Description of the output schema (JSON structure, required fields, validation). Temperature and sampling parameters used.

**2.3 Input Specification**
Complete list of input fields: name, email, country, age, pathway, german_level, english_level, education_level, field_of_study, work_experience_years, timeline, financial_situation, current_location, additional_info. Data types, validation rules, and required/optional status for each field.

**2.4 Output Specification**
Full schema of the diagnostic output: overall_score (integer 0–100), 6 dimension scores (integer 0–100 each), summary (string, 2–3 sentences), roadmap (array of month objects with title, description, action_items), recommendations (array of 3 objects with name, type, description, url). Constraints and validation applied to each output field.

**2.5 Human Review Interface**
Description of the admin dashboard used by the consultant. Review workflow: pending → approved/rejected. What the consultant sees (all 6 scores, summary, full roadmap, notes field). What the consultant can do (approve, reject, add notes). What cannot be bypassed (approval gate — results cannot be delivered without approval action).

---

## Section 3 — Training, Validation and Testing Data

**3.1 Data Used for Development**
Statement that UC-01 uses a pre-trained foundation model (Claude Sonnet) and does not involve custom model training. No student data is used to fine-train or fine-tune the model.

**3.2 Inference Data Governance**
Description of data governance for inference inputs: structured form validation, required fields, data type enforcement, no free-text fields in the scoring-relevant inputs (except field_of_study and additional_info which are informational only).

**3.3 Bias Assessment Plan**
Description of the planned bias testing methodology: evaluate scoring consistency across nationality subgroups (Colombia, Brazil, Mexico, Chile), age groups (18–25, 25–35, 35–45), gender (where disclosed), and pathway types. Planned tooling: Giskard for structured bias detection. Timeline: before scale deployment (Month 6).

**3.4 Known Limitations**
- Model outputs can vary slightly between identical inputs (temperature 0.3 mitigates but does not eliminate)
- Roadmap quality depends on accuracy of student self-report
- Scoring rubric calibrated on publicly available German immigration requirements — may not capture all recent policy changes
- System does not have access to real-time German job vacancy data

---

## Section 4 — Risk Management Documentation

**4.1 Risk Register**
Full risk register with all 9 identified risks, likelihood scores (1–5), impact scores (1–5), composite risk scores, and mitigation strategies. Reference: `research/opportunities_risks.md`.

**4.2 Residual Risk Statement**
After all mitigations are applied, the residual risk level for each critical risk. Statement that the human review gate reduces the residual risk of all three critical risks (EU AI Act non-compliance, GDPR breach, incorrect visa advice) to acceptable levels for MVP scale.

**4.3 Risk Review Schedule**
Risk register reviewed at: MVP launch (Week 2), Pilot evaluation (Week 3), Scale decision (Month 2), Monthly thereafter.

---

## Section 5 — Monitoring, Operation and Control

**5.1 Logging Architecture**
Description of the audit_log table: fields (id, created_at, diagnostic_id, action, actor, details), retention policy (24 months), immutability design (insert-only), access controls (service_role key only).

**5.2 Performance Monitoring**
Metrics monitored: diagnostic completion rate, conversion rate, consultant review time, student satisfaction (30-day survey), system uptime. Monitoring tools: Supabase dashboard, Render metrics, Vercel analytics.

**5.3 Incident Response**
Procedure for: AI output errors identified post-approval, data breach events, system downtime, GDPR subject access requests. Contact: consultant@klar.app, escalation path to developer.

**5.4 Model Update Policy**
Procedure for handling model version updates from Anthropic: test on 20 historical profiles before deploying new model version, document version change in technical documentation, re-run bias assessment after any model change.

---

## Section 6 — Compliance and Certification

**6.1 EU AI Act Classification Evidence**
Step-by-step classification reasoning referencing Annex III, Point 3(a). Cross-reference with Conformity Assessment Summary.

**6.2 Conformity Assessment Summary**
Reference to the separate Conformity Assessment Summary document (see `02_eu_ai_act_conformity_assessment.md`).

**6.3 GDPR Compliance Reference**
Reference to the DPIA document and data processing records (see `04_gdpr_dpia.md` and `05_gdpr_data_flows.md`).

**6.4 EU Database Registration**
When required (at scale, per Article 71): register the system in the EU database for high-risk AI systems. Planned timeline: before exceeding 100 monthly active users or August 2, 2026 — whichever comes first.

---

## Section 7 — Changes and Versions

**7.1 Version History**

| Version | Date | Changes | Approved by |
|---|---|---|---|
| 0.1 MVP | June 2026 | Initial deployment. UC-01 only. Pilot with <20 users. | Lucas Barrios |
| 0.2 Pilot | July 2026 | Add UC-02 (Ausbildung Matcher). Expand to 200 users. | TBD |
| 1.0 Scale | Sept 2026 | Full platform launch. External compliance audit complete. | TBD |

---

*EU AI Act Technical Documentation Outline · Klar · Regulation (EU) 2024/1689, Article 11 · June 2026*
