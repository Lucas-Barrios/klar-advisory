# Strategic Deployment and Commercialisation Plan
## Klar — Germany Readiness Diagnostic Platform
### Ironhack Berlin AI & Integration Consulting · June 2026

---

## 1. Deployment Phases

### Phase 1 — MVP (Weeks 1–2)
**Goal:** Validate that the AI diagnostic produces useful, accurate results that convert to self-serve Germany Application Kit purchases.

**Scope:**
- UC-01 Germany Readiness Diagnostic Agent only
- 20 pilot students (recruited from Cleo's existing network + LinkedIn)
- Manual outreach only — no paid marketing
- Cleo reviews all diagnostics personally

**Success metrics:**
- 20 diagnostics completed
- Consultant review time <3 minutes per diagnostic
- 3+ students purchase the Germany Application Kit (15% conversion)
- Zero incorrect visa/legal information delivered
- Student satisfaction >7/10 on post-result survey

**Cost:** €3,700 (one-time MVP build)
**Revenue target:** 3+ Germany Application Kit purchases × €39 = €117+ (first conversions expected Month 3 as pilot diagnostics are approved and delivered)

---

### Phase 2 — Pilot (Weeks 3–6)
**Goal:** Scale to 100 diagnostics per month. Validate conversion funnel. Sign Anthropic DPA. Add email notification via n8n.

**Scope:**
- UC-01 live + n8n email notifications active
- LinkedIn content strategy launches (3 posts per week)
- WhatsApp community outreach begins (Colombian and Brazilian student groups in Germany)
- DAAD partnership conversation initiated

**Success metrics:**
- 100 diagnostics per month
- Consultant review time <2 minutes average (efficiency improving)
- 15%+ conversion rate maintained
- Email notification delivered within 24 hours of approval
- Anthropic DPA signed

**Cost:** €200/month (infrastructure only — solo operator model)
**Revenue target:** 100 × 15% × €39 = €585/month

---

### Phase 3 — Scale (Months 2–6)
**Goal:** Grow diagnostic volume to 200+/month. Move Stripe paywall to live production. Hire one part-time reviewer. Explore optional premium upsell and B2B institutional partnerships.

**Scope:**
- UC-01, UC-02 (Ausbildung Matcher), and UC-04 (Document Factory) all live — these are already deployed; Phase 3 is about growing volume on existing features, not launching new ones
- Stripe Checkout moved from test mode to live production
- Small team of 2 (Cleo + 1 part-time reviewer)
- Partnership conversations with 3 German universities and 2 NGOs
- EU AI Act registration in EU database (if >100 monthly users)
- External compliance audit completed

**Success metrics:**
- 200+ diagnostics per month
- 20% conversion rate
- 2 B2B partnership conversations initiated
- EU AI Act registration complete
- Full GDPR compliance documentation published

**Cost:** ~€900/month (€200 infrastructure + €700 part-time reviewer)
**Revenue target:** 200 × 20% × €39 = €1,560+/month, growing toward €3,861/month by Month 12

---

## 2. Go-to-Market Strategy

### Who Buys

**B2C — Primary (Year 1)**

The primary buyer is a Latin American student or professional aged 22–38 who is actively considering Germany but doesn't know if they qualify or where to start.

Profile:
- Colombian, Brazilian, or Mexican
- Has university education or vocational background
- Speaks some English, little or no German
- Actively researching Germany after Canada/Australia closed
- Sees Germany as a long-term career move, not a holiday visa

They find Cleo through: LinkedIn content, WhatsApp student communities, word of mouth from other LATAM immigrants in Germany, Instagram, TikTok (future).

**B2B — Secondary (Year 2+)**

Institutional buyers who need international candidate pipelines:
- German universities with unfilled international seats
- Nursing homes and hospitals with Ausbildung vacancies (222 days average unfilled)
- NGOs supporting international integration (Caritas, AWO, Die Heilsarmee)
- DAAD partner institutions in Latin America

B2B deal: white-label platform access or batch diagnostic processing at €200–€500/month per institution.

---

### How We Reach Them

**Channel 1 — LinkedIn (Cleo's personal brand)**
3 posts per week. Content mix:
- Germany pathway explainers (Ausbildung, university, Chancenkarte)
- Student success stories (anonymised)
- Common myths about moving to Germany
- Behind-the-scenes of the advisory process

Target: 5,000 followers in Colombia/Brazil/Mexico within 6 months. Each post includes a CTA to the free diagnostic.

**Channel 2 — WhatsApp Communities**
There are active WhatsApp groups for LATAM students interested in Germany. Klar participates genuinely — answering questions, sharing resources — and offers the free diagnostic as a value-add. No spam.

**Channel 3 — DAAD Partnership**
DAAD (German Academic Exchange Service) has active scholarship programs in Colombia and Brazil. A referral partnership where DAAD scholarship applicants are directed to Klar for a readiness pre-check could generate 50–100 diagnostics per month at zero CAC.

**Channel 4 — YouTube / TikTok (Month 4+)**
Short-form video content in Spanish explaining Germany pathways. "Is Germany realistic for you?" as a hook. Each video links to the free diagnostic.

---

### Pricing Model

| Tier | Price | What's included |
|---|---|---|
| Free Diagnostic | €0 | Readiness score + roadmap (AI-scored, reviewed by consultant) |
| Germany Application Kit | €39 | Bundesagentur für Arbeit matched positions + bilingual (German + English/Spanish) AI-generated CV and cover letter with editable placeholders — self-serve, instant unlock via Stripe Checkout |
| Free 15-min Consultation (Cal.com) | €0 | Optional trust-building call with Cleo — not a paid tier; a relationship touchpoint that can lead to a kit purchase |

The free diagnostic is the lead generation engine. It delivers real value and creates a natural conversion moment: "Your score is 68/100 — you're ready with preparation. Here's your personalised Germany Application Kit with real matched positions."

---

## 3. Stakeholder Communication Plan

### Cleo (CEO — Primary Operator)
**What she needs to hear:**
- The human review gate is non-negotiable — it protects her legally and professionally
- The AI doesn't replace her expertise, it handles the intake so she can focus on high-value consultations
- Compliance is not overhead — it's a competitive moat that closes B2B deals her competitors can't even participate in
- The roadmap is sequenced so she never has to bet large before validating small

**Communication approach:** Weekly sprint review showing diagnostic volume, conversion rate, and review time. Dashboard gives her real-time visibility. No technical jargon.

---

### Students (End Users)
**What they need to hear:**
- This is free and takes 3 minutes
- A real human reviews your result before you receive it — this isn't just an AI chatbot
- The score is honest — if you're not ready, we'll tell you, and we'll show you exactly what to do to get there
- Your data is stored securely in Germany and never sold

**Communication approach:** Conversational form design, warm personalised result delivery, clear disclaimer that results are guidance not legal advice.

---

### Legal Advisor (Future engagement)
**What they need to hear:**
- UC-01 is classified High Risk under EU AI Act Annex III Point 3(a)
- A human review gate is in place — no automated decisions reach students
- The DPIA identifies four material risks, all with mitigations
- Anthropic DPA needs to be signed before pilot launch — this is the most urgent legal action

**Communication approach:** Share the Conformity Assessment Summary and DPIA. Request review and sign-off before pilot launch.

---

### DAAD / Institutional Partners (B2B)
**What they need to hear:**
- Klar pre-screens students before they apply, reducing wasted applications
- The AI scoring is reviewed by a human consultant — no black box
- GDPR compliant, EU AI Act aware — institutional partners can trust the data handling
- We are building toward a white-label B2B version for institutional use in Year 2

**Communication approach:** One-page partnership brief with student outcome data from the pilot. Personal outreach from Cleo.

---

### Investors / Accelerators (Month 6+)
**What they need to hear:**
- €3,700 MVP validating in 2 weeks — extremely capital efficient
- TAM: $23.5B study abroad market, 420K+ Germany international students, 617K unfilled German jobs
- Compliance as moat: no competitor can match the EU AI Act + GDPR posture for institutional deals
- First-mover in Spanish-language AI advisory for Germany — zero direct competition

**Communication approach:** Investor deck with market data from the research phase, live dashboard demo, pilot conversion metrics.

---

## 4. Success Metrics Per Phase

| Metric | Phase 1 (MVP) | Phase 2 (Pilot) | Phase 3 (Scale) |
|---|---|---|---|
| Monthly diagnostics | 20 | 100 | 200+ |
| Conversion rate | 15% | 15% | 20% |
| Average ticket | €39 | €39 | €39 |
| Monthly revenue | €117 | €585 | €1,560+ |
| Review time avg | <3 min | <2 min | <90 sec |
| Student satisfaction | >7/10 | >8/10 | >8.5/10 |
| B2B partnerships | 0 | 0 | 0 (exploring) |
| EU AI Act compliant | Partial | Full | Full + audited |

---

## 5. Commercialisation Model

**Year 1 (Current — MVP + Pilot): Self-serve digital product**

Klar's monetised product is the **€39 Germany Application Kit** — a one-time self-serve purchase that unlocks Bundesagentur für Arbeit matched Ausbildung and job positions plus bilingual AI-generated CV and cover letter. The free diagnostic handles lead generation and qualification automatically. Human review is a quality and EU AI Act Article 14 compliance layer on every result, not a separate billable service. The Cal.com free 15-minute consultation (UC-05) builds trust and can lead naturally to a kit purchase, but is not a conversion step in the sales funnel and is not a paid tier.

Year 1 total revenue: €18,720. Total cost: €5,900. Net profit: €12,820 (see ROI and Risk Assessment for the monthly breakdown).

**Phase 3+ (Scale, Months 2–6 onward): Expansion options**

Two legitimate expansion paths — clearly labelled as future options, not baked into Year 1 revenue:

a) **Optional premium consulting upsell:** Students who want deeper, personalised support beyond the self-serve kit can book paid 1:1 sessions with Cleo. Pricing to be determined once the self-serve model is validated at volume. Not yet implemented.

b) **B2B/institutional licensing:** Universities, NGOs, and Ausbildung training providers pay for bulk diagnostic access or white-label deployment. Deal structure: flat monthly licensing fee per institution (~€200–€500/month per partner). Conversations to begin once pilot metrics validate the product at scale.

Both expansion paths are clearly labelled as future options — not baked into Year 1 revenue targets.

**Revenue summary:**

| Year | Model | Revenue Target |
|---|---|---|
| Year 1 | Self-serve €39 kit (validated model) | €18,720 |
| Year 2 | Self-serve + optional consulting upsell | ~€75,600 (directional) |
| Year 3 | Self-serve + upsell + B2B institutional licensing | ~€140,400 (directional) |

Year 2 and Year 3 figures are directional projections built on Year 1's validated self-serve model, not committed targets. See ROI and Risk Assessment for the full 36-month assumptions and methodology.

---

## 6. Monetization Model — Current State and Phased Roadmap

### Phase 1 — Current (self-serve kit + Cal.com trust touchpoint)

The free diagnostic (UC-01) functions as the lead magnet. Every approved result includes a personalised next-step message and a Cal.com link offering a free 15-minute consultation with Cleo. The consultation is a **trust-building touchpoint** — not the primary conversion event, and not a billable service tier. Students who want to go further are directed to the self-serve Germany Application Kit (Phase 1.5). Cleo's time is the quality and compliance layer on the free diagnostic, not a billable product.

---

### Phase 1.5 — Built and tested (Stripe test mode, not yet production)

Two features are now gated behind a Stripe Checkout paywall, currently running in **Stripe TEST MODE only** — no real money changes hands, and only test API keys are in use:

- **Germany Application Kit — €39 (one-time):** unlocks both matched Ausbildung/job positions sourced from Bundesagentur für Arbeit AND bilingual CV + Cover Letter generation in German + English or Spanish. Both features are unlocked simultaneously by a single Stripe Checkout payment. The kit is offered after the student receives their free, human-reviewed diagnostic score.

**Architecture:** a Stripe Checkout Session is created server-side on the FastAPI backend; a webhook endpoint with Stripe signature verification listens for `checkout.session.completed` and sets `matches_unlocked` or `documents_unlocked = true` on the relevant row in the `diagnostics` table (Supabase). The frontend reflects the unlocked state on next page load.

**Going to production requires:** Stripe business account verification (bank details, tax registration), switching from test to live API keys, and re-pointing the webhook to live mode. This was out of scope for the submission timeline but the architecture is production-ready.

This is a **self-serve upsell layer** that converts without requiring Cleo's time — structurally distinct from Phase 1's trust-building consultation call.

---

### Phase 2 — Near-term (next 4–6 weeks)

- **Move the Phase 1.5 paywall to production** once Stripe business verification is complete.
- **Affiliate commission links:** convert the static resource recommendations already generated by UC-01 (Goethe Institut, blocked account providers such as Fintiba and Expatrio, language schools) into tracked affiliate links once formal partnership agreements are in place. Revenue model: commission per signup or percentage of referred transaction, paid by the partner, not the student. Required disclosure: any affiliate relationship must be clearly labelled near the relevant recommendation per EU consumer protection requirements — same transparency principle applied throughout this project's compliance documentation.

---

### Phase 3 — Medium-term (months 2–4)

- **Formalise optional consulting upsell:** once the self-serve model is validated at volume, add a clearly priced paid session option (e.g., 45-minute 1:1 with Cleo) for students who want deeper personalised support. Replace ad hoc post-call invoicing with an automated Stripe Payment Link.
- **Future recurring tier:** continuously refreshed Ausbildung matches, unlimited document regeneration, and monthly AI-generated progress check-ins. Not yet implemented.

---

### Phase 4 — Scale (month 6+)

**B2B institutional licensing:** German employers and Ausbildung training providers pay for access to the pool of AI-scored, human-reviewed candidates — either as a flat licensing fee or a per-successful-placement fee. This shifts the revenue model from per-student transactions to a B2B contract model where the AI does the matching work at scale.

---

### Summary

| Phase | Mechanism | Requires consultant time? | Status |
|---|---|---|---|
| 1 | Free 15-min Cal.com consultation (trust touchpoint) | Yes (quality/compliance layer) | Live |
| 1.5 | Stripe paywall — €39 Germany Application Kit (self-serve) | No | Built, not production |
| 2 | Affiliate commissions | No | Planned |
| 3 | Optional paid consulting sessions + automated Payment Links | Partial | Planned |
| 4 | B2B licensing | No (per-student) | Planned |

---

*Strategic Deployment and Commercialisation Plan · Klar · Ironhack Berlin · June 2026*
