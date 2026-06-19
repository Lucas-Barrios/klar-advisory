# Use Case Definition
## Klar — Germany Readiness Diagnostic Agent
### AI Adoption Opportunity Project · Ironhack Berlin · June 2026
**Student:** Lucas Barrios

---

## 1. Business Problem

Education consulting for Latin Americans pursuing German pathways is a manually intensive, time-capped business. A solo consultant can realistically serve 10–15 clients per month — each requiring 3–5 hours of intake, research, and advisory work. There is no scalable way to expand into international markets without hiring, and hiring increases fixed costs before revenue justifies it.

Simultaneously, demand is structural and growing. Canada cut LATAM student permits by over 50% in 2024. Australia tightened. Germany enrolled a record 420,000+ international students in 2025/26 and opened non-EU Ausbildung visas under the 2023 Fachkräfteeinwanderungsgesetz. Spanish-speaking Latin Americans are permanently rerouting toward Germany — but no AI-native advisory service exists in Spanish for this specific pathway.

The business problem is therefore twofold:
1. **Supply constraint:** Cleo cannot serve the demand she is generating without AI automation
2. **Market gap:** The LATAM → Germany advisory niche has zero AI-native competition

---

## 2. Company Profile

**Company name:** Cleo's Germany Advisory (fictional client)
**Industry:** Education consulting / Immigration advisory
**Size:** Solo operator, 1 employee, fully remote
**Current state:** Manual intake process, 10–15 clients per month ceiling, German pathways focus
**Location:** Berlin, Germany
**Target market:** Spanish-speaking Latin Americans (Colombia, Brazil, Mexico, Chile, Peru) aged 20–40 pursuing university, Ausbildung, or work visa pathways in Germany
**Revenue model:** Self-serve digital product — free AI diagnostic (lead generation + qualification) followed by a one-time €39 Germany Application Kit (matched positions + bilingual CV/cover letter). A free 15-minute consultation booking (Cal.com) is offered as an additional trust-building touchpoint, not a separate paid tier.
**Technology maturity:** Low — currently using email, spreadsheets, and video calls

---

## 3. The AI-Powered Solution: Klar

**Klar** is a Germany readiness diagnostic platform built on an agentic AI pipeline.

A student fills a multi-step conversational intake form (11 questions covering language level, education, pathway goals, timeline, and financial situation). A raw Anthropic Python SDK powered by Claude Sonnet analyses the profile and generates:

- An **overall readiness score** (0–100) across 6 dimensions
- A **dimension breakdown** (Language, Education, Pathway Fit, Timeline, Financial, Documentation)
- A **month-by-month roadmap** tailored to their specific situation and timeline
- **Three specific recommendations** (programs, organisations, resources) relevant to their profile

Before the student receives any results, Cleo reviews and approves the diagnostic through a dedicated admin dashboard. This human review gate is both an EU AI Act Article 14 compliance mechanism and a quality control layer.

**Core use case:** UC-01 — Germany Readiness Diagnostic Agent

**Tech stack:**
- Frontend: Next.js 15 (TypeScript, Tailwind CSS)
- Backend: FastAPI (Python)
- AI Agent: Anthropic Claude Sonnet (raw SDK, traced via LangSmith)
- Database: Supabase (PostgreSQL)
- Notifications: n8n workflow automation
- Deployment: Vercel (frontend) + Render (backend)

---

## 4. Key Stakeholders

| Stakeholder | Role | Interest |
|---|---|---|
| Cleo (CEO) | Primary user of admin dashboard | Wants to scale without hiring. Needs AI to handle intake and scoring while she focuses on high-value consultations. |
| Latin American students | End users of the diagnostic | Want honest, personalised guidance in Spanish about whether Germany is realistic for them and what to do next. |
| German employers (B2B) | Potential future partners | Want pre-screened, language-ready international candidates for Ausbildung vacancies. |
| Anthropic (Claude API) | AI infrastructure provider | US-based processor — relevant to GDPR data transfer obligations. |
| Supabase | Database provider | EU-region option available — relevant to GDPR Article 46. |
| Regulatory bodies | EU AI Act, GDPR | UC-01 is classified High Risk under Annex III — compliance obligations apply. |

---

## 5. Success Criteria

**What does "this works" look like?**

| Metric | Target | Measurement method |
|---|---|---|
| Diagnostic completion rate | >70% of students who start the form complete it | Supabase analytics: students table count vs form start events |
| Conversion rate (diagnostic → paid service) | >15% | CRM tracking of diagnostic_id to invoice |
| Cleo's review time per diagnostic | <3 minutes | Admin dashboard timestamp: created_at to reviewed_at |
| Diagnostic accuracy | >80% satisfaction on follow-up survey | Post-result email survey at 30 days |
| Time to deliver results | <24 hours from submission | reviewed_at - created_at in audit_log |
| System uptime | >99% during business hours | Render/Vercel monitoring |
| EU AI Act compliance | Full Article 9–15 compliance before scale | External compliance audit at Month 6 |

**MVP success definition (2-week pilot):**
- 20 diagnostics completed by real students
- Cleo reviews and approves within 24 hours
- At least 3 students convert to a paid consultation
- No incorrect visa or legal information delivered
- Zero data breaches

---

## 6. Out-of-Scope Boundaries

Klar explicitly does not:
- Provide legal immigration or visa advice — the diagnostic is an informational readiness assessment, not legal counsel
- Guarantee admission, visa approval, or Ausbildung placement outcomes
- Replace a licensed immigration lawyer or certified translator for official document submission
- Verify the authenticity of user-reported information (financial situation, education credentials) — scores are based on self-reported data
- Generate final, submission-ready legal/government documents — CV and cover letter outputs use bracketed placeholders for anything the AI cannot verify, requiring the student to confirm or complete all factual details before use
- Operate without human review — no AI-generated diagnostic reaches a student without prior consultant approval, by design

---

## 7. Why This Use Case First

UC-01 (Germany Readiness Diagnostic) was selected as the primary use case because it is the **architectural foundation** — every other AI capability in the roadmap depends on the student profile it generates. The Ausbildung Matcher (UC-02), Application Tracker (UC-03), and Document Factory (UC-04) all require knowing who the student is and what they need before they can operate.

Building UC-01 first means validating the core AI capability, the human review infrastructure, the compliance architecture, and the product–market fit — all in a single 2-week MVP sprint at a total cost of €3,700.

---

*Use Case Definition · Klar · Ironhack Berlin AI & Integration Consulting · June 2026*
