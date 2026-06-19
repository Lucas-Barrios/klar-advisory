# ROI and Risk Assessment
## Klar — Germany Readiness Diagnostic Platform
### Ironhack Berlin AI & Integration Consulting · June 2026

---

## 1. Investment Summary

| Item | Cost |
|---|---|
| MVP build (2-week sprint) | €3,700 |
| Monthly infrastructure — Solo (Months 1–2) | €200/month |
| Monthly infrastructure — Small Team (Month 3+) | €16,200/month |
| Monthly infrastructure — Full Team (Month 6+) | €19,000/month |

**MVP cost breakdown:**
- Developer time (40 hours × €85/hour) — €3,400
- Infrastructure setup (Vercel, Render, Supabase Pro) — €150
- Domain and email — €50
- API costs during build (Anthropic testing) — €100
- **Total MVP: €3,700**

**Monthly operational costs (Solo Operator model — Months 1–6):**
- Anthropic API (~500 diagnostics/month × €0.05/call) — €25
- Supabase Pro — €25
- Vercel Pro — €20
- Render Starter — €25
- Miscellaneous (email, tools) — €105
- **Total solo monthly: ~€200**

---

## 2. Revenue Model

| Tier | Price | Expected Conversion |
|---|---|---|
| Free Diagnostic | €0 | — (lead generation) |
| Guided Consultation | €99 | 8% of diagnostics |
| Full Service | €499 | 6% of diagnostics |
| Premium Advisory | €1,500 | 1% of diagnostics |
| **Blended average ticket** | **~€500** | **15% total conversion** |

---

## 3. 12-Month ROI Projection

**Assumptions:**
- Monthly diagnostic volume ramps from 20 (Month 1) to 660 (Month 12)
- Conversion rate: 15% across all paid tiers
- Average ticket: €500
- Solo operator model through Month 6, Small Team from Month 7

| Month | Diagnostics | Conversions | Monthly Revenue | Monthly Cost | Cumulative Revenue | Cumulative Cost |
|---|---|---|---|---|---|---|
| 1 | 0 | 0 | €0 | €3,700 | €0 | €3,700 |
| 2 | 0 | 0 | €0 | €200 | €0 | €3,900 |
| 3 | 30 | 5 | €2,250 | €200 | €2,250 | €4,100 |
| 4 | 80 | 12 | €6,000 | €200 | €8,250 | €4,300 |
| 5 | 130 | 20 | €9,750 | €200 | €18,000 | €4,500 |
| 6 | 190 | 29 | €14,250 | €200 | €32,250 | €4,700 |
| 7 | 260 | 39 | €19,500 | €16,200 | €51,750 | €20,900 |
| 8 | 340 | 51 | €25,500 | €16,200 | €77,250 | €37,100 |
| 9 | 420 | 63 | €31,500 | €16,200 | €108,750 | €53,300 |
| 10 | 500 | 75 | €37,500 | €16,200 | €146,250 | €69,500 |
| 11 | 580 | 87 | €43,500 | €16,200 | €189,750 | €85,700 |
| 12 | 660 | 99 | €49,500 | €16,200 | €239,250 | €101,900 |

**12-Month Summary:**
- Total revenue: €239,250
- Total cost: €101,900
- Net profit: €137,350
- **ROI (12 months): 135%**
- **Break-even: Month 5** (cumulative revenue exceeds cumulative cost)

---

## 4. 36-Month ROI Projection

**Assumptions for Year 2 (Months 13–24):**
- UC-02 Ausbildung Matcher launched (Month 14) — increases conversion rate to 20%
- UC-04 Document Factory launched (Month 16) — increases average ticket to €625
- B2B institutional tier launched (Month 18) — 20 institutional diagnostics/month at €35 each
- Small team of 3 throughout Year 2
- Monthly diagnostic volume: 700 → 1,200

**Assumptions for Year 3 (Months 25–36):**
- Platform model: 3 consultant seats on Klar at €500/month each
- Employer placement fees: 5 successful Ausbildung placements/month at €1,000 each
- Monthly diagnostic volume: 1,200 → 2,000
- Average ticket increases to €750 as premium tier grows

| Period | Monthly Revenue (avg) | Monthly Cost (avg) | Monthly Profit | Cumulative Profit |
|---|---|---|---|---|
| Year 1 (M1–M12) | €19,938 | €8,492 | €11,446 | €137,350 |
| Year 2 (M13–M24) | €67,500 | €19,000 | €48,500 | €719,350 |
| Year 3 (M25–M36) | €142,000 | €35,000 | €107,000 | €2,003,350 |

**36-Month Summary:**
- Total revenue: ~€2,750,000
- Total cost: ~€747,000
- Net profit: ~€2,003,350
- **ROI (36 months): 268%**

**Key 36-month milestones:**
- Month 5: Break-even on MVP investment
- Month 12: €239K cumulative revenue, team of 3
- Month 18: B2B institutional partnerships active
- Month 24: €719K cumulative profit, platform model launching
- Month 36: €2M+ cumulative profit, considering Series A

---

## 5. Break-Even Sensitivity Analysis

How break-even month changes with different conversion rates and average tickets:

| Conversion Rate | Avg Ticket €300 | Avg Ticket €500 | Avg Ticket €750 |
|---|---|---|---|
| 10% | Month 8 | Month 6 | Month 5 |
| 15% | Month 6 | Month 5 | Month 4 |
| 20% | Month 5 | Month 4 | Month 3 |
| 25% | Month 4 | Month 3 | Month 3 |

**Conservative scenario (10% conversion, €300 avg ticket):** Break-even Month 8. Still profitable within Year 1.

**Base scenario (15% conversion, €500 avg ticket):** Break-even Month 5.

**Optimistic scenario (25% conversion, €750 avg ticket):** Break-even Month 3.

All scenarios result in positive ROI within 12 months. The investment case is robust across the full sensitivity range.

---

## 6. Risk Assessment Matrix

### Regulatory Risks

| Risk | Likelihood | Impact | Score | Mitigation |
|---|---|---|---|---|
| EU AI Act non-compliance (UC-01 = High Risk) | 4/5 | 5/5 | **20/25** | Human review gate satisfies Article 14. Conformity Assessment prepared. Technical Documentation Outline complete. Registration in EU database before scale. |
| GDPR breach — student data via Anthropic US API | 3/5 | 5/5 | **15/25** | Sign Anthropic DPA with SCCs before pilot. Evaluate EU-based LLM providers at scale. Supabase EU region already configured. |
| Regulatory change — German immigration law | 2/5 | 4/5 | **8/25** | RAG pipeline planned for UC-07 to ingest live regulatory updates. Consultant review gate catches outdated advice before delivery. |

---

### Technical Risks

| Risk | Likelihood | Impact | Score | Mitigation |
|---|---|---|---|---|
| LLM generates incorrect visa/legal advice at scale | 3/5 | 5/5 | **15/25** | Human review gate is mandatory architectural component. System prompt includes explicit disclaimer instructions. Consultant validates before delivery. |
| Single LLM provider dependency (Anthropic) | 2/5 | 4/5 | **8/25** | LLM calls use the raw Anthropic SDK wrapped with LangSmith tracing — the client is instantiated in one place per agent file, so swapping providers requires changing the client constructor only. Evaluate Mistral AI (EU-based) as backup. |
| Supabase outage affecting service | 2/5 | 3/5 | **6/25** | Supabase SLA 99.9% uptime. Automatic retry logic in FastAPI. Results page shows graceful error state. |
| API cost spike at scale | 2/5 | 3/5 | **6/25** | Switch to smaller model (claude-haiku-4-5) for standard diagnostics at scale. Cost per diagnostic drops from €0.05 to €0.008. |

---

### Ethical Risks

| Risk | Likelihood | Impact | Score | Mitigation |
|---|---|---|---|---|
| Algorithmic bias in readiness scoring | 3/5 | 4/5 | **12/25** | Scoring rubric explicitly defined with numeric anchors. Disaggregated bias testing planned (by nationality, age, gender) before scale. Giskard tooling planned. Human review catches outlier scores. |
| Students making life decisions based on incorrect AI output | 3/5 | 4/5 | **12/25** | Disclaimer on all results pages. Scores described as guidance not determinations. Consultant review gate. Resubmission available if student believes score is wrong. |
| Over-reliance on AI discourages students who could succeed | 2/5 | 4/5 | **8/25** | Score messaging designed to be constructive at all levels. Below-40 score shows "Not ready yet — but here's your roadmap" not "You cannot go to Germany." |

---

### Operational Risks

| Risk | Likelihood | Impact | Score | Mitigation |
|---|---|---|---|---|
| Leverage Edu enters Spanish-language Germany market | 3/5 | 4/5 | **12/25** | First-mover advantage. EU AI Act compliance as moat — institutional partners cannot work with non-compliant competitors. Build community flywheel before they arrive. |
| Consultant (Cleo) bottleneck at high volume | 3/5 | 3/5 | **9/25** | Review time target <2 minutes. Hire second reviewer at 200 diagnostics/month. Explore batch review workflow. |
| Student drop-off on form (language barrier) | 4/5 | 3/5 | **12/25** | Conversational one-question-at-a-time UX. Form available in Spanish (future). Emoji-based choice cards reduce text dependency. Progress bar shows completion proximity. |
| Green AI / carbon footprint concerns | 2/5 | 2/5 | **4/25** | Use smaller model (haiku) where full capability not needed. Anthropic publishes carbon offset commitments. Batch non-urgent API calls. |

---

## 7. Risk Priority Matrix

```
         HIGH IMPACT
              │
    EU AI Act │  LLM incorrect advice
    (20/25)   │  (15/25)
              │
    GDPR      │  Algorithmic bias    Student decisions
    (15/25)   │  (12/25)             (12/25)
              │
──────────────┼──────────────────────────────── HIGH LIKELIHOOD
              │
    API cost  │  Leverage Edu
    (6/25)    │  (12/25)
              │
    Green AI  │
    (4/25)    │
              │
         LOW IMPACT
```

**Top 3 priorities requiring immediate action:**
1. **EU AI Act compliance** (20/25) — Human review gate implemented. Conformity Assessment complete. Register in EU database before scale.
2. **GDPR + Anthropic DPA** (15/25) — Sign DPA before pilot launch. This is the single most urgent legal action.
3. **LLM incorrect advice** (15/25) — Human review gate mitigates. Add explicit disclaimer to all result pages.

---

*ROI and Risk Assessment · Klar · Ironhack Berlin AI & Integration Consulting · June 2026*
