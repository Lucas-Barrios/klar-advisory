# ROI and Risk Assessment
## Klar — Germany Readiness Diagnostic Platform
### Ironhack Berlin AI & Integration Consulting · June 2026

---

## 1. Investment Summary

| Item | Cost |
|---|---|
| MVP build (2-week sprint) | €3,700 |
| Monthly infrastructure — Solo operator (Months 1–12) | €200/month |
| Monthly infrastructure + part-time reviewer (Year 2+) | ~€900/month |

**MVP cost breakdown:**
- Developer time (40 hours × €85/hour) — €3,400
- Infrastructure setup (Vercel, Render, Supabase Pro) — €150
- Domain and email — €50
- API costs during build (Anthropic testing) — €100
- **Total MVP: €3,700**

**Monthly operational costs (Solo Operator model — Months 1–12):**
- Anthropic API (~500 diagnostics/month × €0.05/call) — €25
- Supabase Pro — €25
- Vercel Pro — €20
- Render Starter — €25
- Miscellaneous (email, tools) — €105
- **Total solo monthly: ~€200**

Note: costs remain flat at €200/month through Year 1 because Klar is a self-serve digital product — each diagnostic incurs one AI call at ~€0.05 plus minimal storage and bandwidth. There is no scaling human consulting team in this model. A part-time reviewer (~€700/month) is added in Year 2 when volume makes it operationally necessary.

---

## 2. Revenue Model

| Tier | Price | Expected Conversion |
|---|---|---|
| Free Diagnostic | €0 | — (lead generation and qualification) |
| Germany Application Kit | €39 | ~15% of diagnostics |

The Application Kit is a one-time self-serve purchase unlocking Bundesagentur für Arbeit matched positions and bilingual CV/cover letter generation. No manual sales process required — Stripe Checkout handles the transaction automatically.

---

## 3. 12-Month ROI Projection

**Assumptions:**
- Monthly diagnostic volume ramps from 0 (Months 1–2) to 660 (Month 12)
- Conversion rate: ~15% across all months
- Kit price: €39 (fixed — self-serve, no tiering)
- Solo operator model throughout — cost stays flat at €200/month after MVP

| Month | Diagnostics | Conversions | Monthly Rev | Monthly Cost | Cum Rev | Cum Cost |
|---|---|---|---|---|---|---|
| 1 | 0 | 0 | €0 | €3,700 | €0 | €3,700 |
| 2 | 0 | 0 | €0 | €200 | €0 | €3,900 |
| 3 | 30 | 5 | €195 | €200 | €195 | €4,100 |
| 4 | 80 | 12 | €468 | €200 | €663 | €4,300 |
| 5 | 130 | 20 | €780 | €200 | €1,443 | €4,500 |
| 6 | 190 | 29 | €1,131 | €200 | €2,574 | €4,700 |
| 7 | 260 | 39 | €1,521 | €200 | €4,095 | €4,900 |
| 8 | 340 | 51 | €1,989 | €200 | €6,084 | €5,100 |
| 9 | 420 | 63 | €2,457 | €200 | €8,541 | €5,300 |
| 10 | 500 | 75 | €2,925 | €200 | €11,466 | €5,500 |
| 11 | 580 | 87 | €3,393 | €200 | €14,859 | €5,700 |
| 12 | 660 | 99 | €3,861 | €200 | €18,720 | €5,900 |

**12-Month Summary:**
- Total revenue: €18,720
- Total cost: €5,900
- Net profit: €12,820
- **ROI (12 months): 217%**
- **Break-even: Month 8** (cumulative revenue €6,084 exceeds cumulative cost €5,100)

---

## 4. 36-Month ROI Projection

Year 2 and Year 3 figures below are directional projections built on Year 1's validated self-serve model. They are not committed targets — the purpose is to show the trajectory assuming the core €39 self-serve model continues to grow and is complemented by modest, realistic expansion.

**Assumptions for Year 2 (Months 13–24):**
- Diagnostic volume grows from ~700/month (Month 13) to ~1,200/month (Month 24) through organic growth and word-of-mouth — UC-02 (Ausbildung Matcher) and UC-04 (Document Factory) are already live in Year 1; they continue to drive kit quality but are not new launches in Year 2
- Conversion rate improves slightly from 16% to 18% as targeting and messaging improve — average 17% across Year 2
- Kit price stays at €39 (no change to the self-serve model)
- One part-time reviewer added (~€700/month) as volume requires it
- Monthly cost: ~€900/month (€200 infra + €700 reviewer)
- Average monthly revenue: ~950 diagnostics × 17% × €39 ≈ €6,300/month

**Assumptions for Year 3 (Months 25–36):**
- Volume grows from ~1,250/month to ~1,800/month (average ~1,525/month)
- Self-serve revenue: ~1,525 × 18% × €39 ≈ €10,700/month
- B2B institutional revenue: 3–5 institutional partnerships at ~€250/month each ≈ €1,000/month — flat licensing fee per institution; clearly labelled as early-stage directional projections, not confirmed deals
- Monthly cost: ~€1,500/month (€200 infra + €700 reviewer + €600 B2B admin/overhead)
- Average monthly revenue: ~€11,700/month

| Period | Monthly Revenue (avg) | Monthly Cost (avg) | Monthly Profit | Cumulative Profit |
|---|---|---|---|---|
| Year 1 (M1–M12) | €1,560 | €492 | €1,068 | €12,820 |
| Year 2 (M13–M24) | €6,300 | €900 | €5,400 | €77,620 |
| Year 3 (M25–M36) | €11,700 | €1,500 | €10,200 | €200,020 |

**36-Month Summary:**
- Total revenue: ~€234,720
- Total cost: ~€34,700
- Net profit: ~€200,020
- **ROI (36 months): ~577%**

**Key milestones:**
- Month 8: Break-even on MVP investment (cumulative revenue exceeds cumulative cost)
- Month 12: €18,720 cumulative revenue, €12,820 net profit
- Year 2: Self-serve model validated at scale; part-time reviewer added
- Year 3: B2B institutional partnerships active (3–5 partners); cumulative profit ~€200,000

---

## 5. Break-Even Sensitivity Analysis

All scenarios use the real €39 kit price. The only variable between scenarios is the conversion rate assumption.

| Scenario | Conversion Rate | Ticket Price | Break-even | 12-Month Net |
|---|---|---|---|---|
| Conservative | 10% | €39 | Month 9 | €6,541 |
| Base | 15% | €39 | Month 8 | €12,820 |
| Optimistic | 20% | €39 | Month 7 | €18,982 |

**Conservative scenario (10% conversion, €39):** Break-even Month 9. Total revenue €12,441. Net profit €6,541.

**Base scenario (15% conversion, €39):** Break-even Month 8. Total revenue €18,720. Net profit €12,820.

**Optimistic scenario (20% conversion, €39):** Break-even Month 7. Total revenue €24,882. Net profit €18,982.

All three scenarios produce positive ROI within 12 months. The investment case is robust: even at half the projected conversion rate, Klar returns a positive net within Year 1.

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
| Consultant (Cleo) bottleneck at high volume | 3/5 | 3/5 | **9/25** | Review time target <2 minutes. Add part-time reviewer at 200 diagnostics/month. Explore batch review workflow. |
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
