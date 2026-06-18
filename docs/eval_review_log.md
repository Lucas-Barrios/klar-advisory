# Evaluation Review Log — UC-01 Diagnostic Seed v1

**Dataset:** `uc01_diagnostic_seed_v1` (version 1)  
**Examples:** 18 hand-labelled seed profiles  
**Dry-run date:** 2026-06-18  
**Run ID:** `a5586fa2-a8ed-4e16-94f1-92e7cc9e8cab`  
**Mode:** DRY-RUN (FakeAnthropicClient — routing fields echo expected labels exactly; `predicted_flags=[]` always; `predicted_overall_score` = `expected_overall_score` when set, else 60)

> **Purpose of this log:** Human sign-off on the *expected labels* (ground truth), not on model accuracy.
> The dry-run predicted values are deterministic placeholders that verify the eval infrastructure
> works end-to-end. Run `--live` to measure real model accuracy. Check each example's expected
> labels and leave notes if any label is wrong or ambiguous.

---

## Example 1 — Strong ausbildung candidate (Mexico, B2, Mechanical Engineering)

**Input profile**

| Field | Value |
|---|---|
| country | Mexico |
| pathway | ausbildung |
| german_level | B2 |
| english_level | C1 |
| education_level | bachelor |
| field_of_study | Mechanical Engineering |
| work_experience_years | 3 |
| timeline | 1_year |
| financial_situation | "I have €5,000 saved and can secure more through family support." |

**Expected labels**

| Label | Value |
|---|---|
| expected_pathway | ausbildung |
| expected_german_level | B2 |
| expected_timeline | 1_year |
| expected_flags | _(none)_ |
| expected_overall_score | **69** (Language 75×0.25=18.75 + Education ≈70×0.20=14 + Pathway Fit ≈75×0.20=15 + Timeline 60×0.15=9 + Financial ≈65×0.10=6.5 + Doc ≈60×0.10=6 = 69.25) |

**Dry-run predicted**

| Field | Predicted | Match |
|---|---|---|
| pathway | ausbildung | ✅ |
| german_level | B2 | ✅ |
| timeline | 1_year | ✅ |
| flags | _(none)_ | ✅ |
| overall_score | 69 | ✅ (within ±10) |

**Score:** 1.000 — **PASS**

**Reviewed:** [ ] yes  
**Notes:**

---

## Example 2 — Low German proficiency (Colombia, A1, high_school)

**Input profile**

| Field | Value |
|---|---|
| country | Colombia |
| pathway | ausbildung |
| german_level | A1 |
| english_level | B1 |
| education_level | high_school |
| field_of_study | General Studies |
| work_experience_years | 1 |
| timeline | 6_months |
| financial_situation | "Limited savings, need funded options." |

**Expected labels**

| Label | Value |
|---|---|
| expected_pathway | ausbildung |
| expected_german_level | A1 |
| expected_timeline | 6_months |
| expected_flags | language_gap, timeline_too_tight |
| expected_overall_score | **26** (Language 20×0.25=5 + Education ≈28×0.20=5.6 + Pathway Fit ≈20×0.20=4 + Timeline 30×0.15=4.5 + Financial ≈25×0.10=2.5 + Doc ≈40×0.10=4 = 25.6) |

**Dry-run predicted**

| Field | Predicted | Match |
|---|---|---|
| pathway | ausbildung | ✅ |
| german_level | A1 | ✅ |
| timeline | 6_months | ✅ |
| flags | _(none)_ | ❌ (dry-run always returns [] — live run will test flag prediction) |
| overall_score | 26 | ✅ (within ±10) |

**Score:** 0.800 — **PASS** _(flag miss reduces score; live run will reflect real flag accuracy)_

**Reviewed:** [ ] yes  
**Notes:**

---

## Example 3 — Borderline B1 nursing (Peru, B1, Nursing)

**Input profile**

| Field | Value |
|---|---|
| country | Peru |
| pathway | ausbildung |
| german_level | B1 |
| english_level | B2 |
| education_level | associate |
| field_of_study | Nursing |
| work_experience_years | 2 |
| timeline | 1_year |
| financial_situation | "I have €2,000 and expect family support." |

**Expected labels**

| Label | Value |
|---|---|
| expected_pathway | ausbildung |
| expected_german_level | B1 |
| expected_timeline | 1_year |
| expected_flags | _(none)_ |
| expected_overall_score | **null** (pathway_fit for nursing at B1 is AI-discretionary; B2 often required for patient-facing — too uncertain for ±10 bound) |

**Dry-run predicted**

| Field | Predicted | Match |
|---|---|---|
| pathway | ausbildung | ✅ |
| german_level | B1 | ✅ |
| timeline | 1_year | ✅ |
| flags | _(none)_ | ✅ |
| overall_score | 60 (no expected — dimension excluded) | n/a |

**Score:** 1.000 — **PASS**

**Reviewed:** [ ] yes  
**Notes:**

---

## Example 4 — Missing financial info (Brazil, B1, Computer Science)

**Input profile**

| Field | Value |
|---|---|
| country | Brazil |
| pathway | ausbildung |
| german_level | B1 |
| english_level | B1 |
| education_level | bachelor |
| field_of_study | Computer Science |
| work_experience_years | 4 |
| timeline | 2_years_plus |
| financial_situation | _(not provided)_ |

**Expected labels**

| Label | Value |
|---|---|
| expected_pathway | ausbildung |
| expected_german_level | B1 |
| expected_timeline | 2_years_plus |
| expected_flags | finance_risk |
| expected_overall_score | **null** (financial penalty range too wide when info is absent) |

**Dry-run predicted**

| Field | Predicted | Match |
|---|---|---|
| pathway | ausbildung | ✅ |
| german_level | B1 | ✅ |
| timeline | 2_years_plus | ✅ |
| flags | _(none)_ | ❌ (dry-run always returns []) |
| overall_score | 60 (no expected — excluded) | n/a |

**Score:** 0.750 — **FAIL** _(flag miss; no overall_score expected → 3 dims scored)_

**Reviewed:** [ ] yes  
**Notes:**

---

## Example 5 — Strong university candidate (Argentina, C1, Economics)

**Input profile**

| Field | Value |
|---|---|
| country | Argentina |
| pathway | university |
| german_level | C1 |
| english_level | C2 |
| education_level | bachelor |
| field_of_study | Economics |
| work_experience_years | 2 |
| timeline | 1_year |
| financial_situation | "I have a €15,000 blocked account ready." |

**Expected labels**

| Label | Value |
|---|---|
| expected_pathway | university |
| expected_german_level | C1 |
| expected_timeline | 1_year |
| expected_flags | _(none)_ |
| expected_overall_score | **76** (Language 90×0.25=22.5 + Education ≈68×0.20=13.6 + Pathway Fit ≈80×0.20=16 + Timeline 60×0.15=9 + Financial ≈88×0.10=8.8 + Doc ≈60×0.10=6 = 75.9) |

**Dry-run predicted**

| Field | Predicted | Match |
|---|---|---|
| pathway | university | ✅ |
| german_level | C1 | ✅ |
| timeline | 1_year | ✅ |
| flags | _(none)_ | ✅ |
| overall_score | 76 | ✅ (within ±10) |

**Score:** 1.000 — **PASS**

**Reviewed:** [ ] yes  
**Notes:**

---

## Example 6 — University, low German + tight timeline (Chile, A2, Architecture)

**Input profile**

| Field | Value |
|---|---|
| country | Chile |
| pathway | university |
| german_level | A2 |
| english_level | B2 |
| education_level | bachelor |
| field_of_study | Architecture |
| work_experience_years | 1 |
| timeline | 6_months |
| financial_situation | "I have €5,000 saved." |

**Expected labels**

| Label | Value |
|---|---|
| expected_pathway | university |
| expected_german_level | A2 |
| expected_timeline | 6_months |
| expected_flags | language_gap, timeline_too_tight |
| expected_overall_score | **39** (Language 35×0.25=8.75 + Education ≈60×0.20=12 + Pathway Fit ≈25×0.20=5 + Timeline 30×0.15=4.5 + Financial ≈25×0.10=2.5 + Doc ≈58×0.10=5.8 = 38.55) |

**Dry-run predicted**

| Field | Predicted | Match |
|---|---|---|
| pathway | university | ✅ |
| german_level | A2 | ✅ |
| timeline | 6_months | ✅ |
| flags | _(none)_ | ❌ (dry-run always returns []) |
| overall_score | 39 | ✅ (within ±10) |

**Score:** 0.800 — **PASS** _(flag miss; overall_score hit balances)_

**Reviewed:** [ ] yes  
**Notes:**

---

## Example 7 — Experienced work visa (Venezuela, B1, Software Engineering, 8 yr)

**Input profile**

| Field | Value |
|---|---|
| country | Venezuela |
| pathway | work_visa |
| german_level | B1 |
| english_level | C1 |
| education_level | master |
| field_of_study | Software Engineering |
| work_experience_years | 8 |
| timeline | 1_year |
| financial_situation | "Stable income, €10,000 in savings." |

**Expected labels**

| Label | Value |
|---|---|
| expected_pathway | work_visa |
| expected_german_level | B1 |
| expected_timeline | 1_year |
| expected_flags | _(none)_ |
| expected_overall_score | **71** (Language 55×0.25=13.75 + Education ≈85×0.20=17 + Pathway Fit ≈82×0.20=16.4 + Timeline 60×0.15=9 + Financial ≈82×0.10=8.2 + Doc ≈65×0.10=6.5 = 70.85) |

**Dry-run predicted**

| Field | Predicted | Match |
|---|---|---|
| pathway | work_visa | ✅ |
| german_level | B1 | ✅ |
| timeline | 1_year | ✅ |
| flags | _(none)_ | ✅ |
| overall_score | 71 | ✅ (within ±10) |

**Score:** 1.000 — **PASS**

**Reviewed:** [ ] yes  
**Notes:**

---

## Example 8 — Healthcare ausbildung, low German (Brazil, A2, Nursing, 3 yr)

**Input profile**

| Field | Value |
|---|---|
| country | Brazil |
| pathway | ausbildung |
| german_level | A2 |
| english_level | B1 |
| education_level | associate |
| field_of_study | Nursing |
| work_experience_years | 3 |
| timeline | 2_years_plus |
| financial_situation | "Minimal savings, need fully funded program." |

**Expected labels**

| Label | Value |
|---|---|
| expected_pathway | ausbildung |
| expected_german_level | A2 |
| expected_timeline | 2_years_plus |
| expected_flags | language_gap |
| expected_overall_score | **null** (long timeline partially offsets weak language/financial; countervailing factors make bound uncertain) |

**Dry-run predicted**

| Field | Predicted | Match |
|---|---|---|
| pathway | ausbildung | ✅ |
| german_level | A2 | ✅ |
| timeline | 2_years_plus | ✅ |
| flags | _(none)_ | ❌ (dry-run always returns []) |
| overall_score | 60 (no expected — excluded) | n/a |

**Score:** 0.750 — **FAIL** _(flag miss; no overall_score expected → 3 dims scored)_

**Reviewed:** [ ] yes  
**Notes:**

---

## Example 9 — IT ausbildung, borderline B1 (Mexico, B1, IT)

**Input profile**

| Field | Value |
|---|---|
| country | Mexico |
| pathway | ausbildung |
| german_level | B1 |
| english_level | C1 |
| education_level | bachelor |
| field_of_study | Information Technology |
| work_experience_years | 2 |
| timeline | 1_year |
| financial_situation | "€4,000 in savings, open to apprenticeship stipend." |

**Expected labels**

| Label | Value |
|---|---|
| expected_pathway | ausbildung |
| expected_german_level | B1 |
| expected_timeline | 1_year |
| expected_flags | _(none)_ |
| expected_overall_score | **null** (all dimensions cluster in 55–65 range; small AI variation shifts >±10) |

**Dry-run predicted**

| Field | Predicted | Match |
|---|---|---|
| pathway | ausbildung | ✅ |
| german_level | B1 | ✅ |
| timeline | 1_year | ✅ |
| flags | _(none)_ | ✅ |
| overall_score | 60 (no expected — excluded) | n/a |

**Score:** 1.000 — **PASS**

**Reviewed:** [ ] yes  
**Notes:**

---

## Example 10 — Minimal profile (Ecuador, A1, high_school, 0 yr)

**Input profile**

| Field | Value |
|---|---|
| country | Ecuador |
| pathway | ausbildung |
| german_level | A1 |
| english_level | A2 |
| education_level | high_school |
| field_of_study | _(not provided)_ |
| work_experience_years | 0 |
| timeline | 2_years_plus |
| financial_situation | _(not provided)_ |

**Expected labels**

| Label | Value |
|---|---|
| expected_pathway | ausbildung |
| expected_german_level | A1 |
| expected_timeline | 2_years_plus |
| expected_flags | language_gap, finance_risk |
| expected_overall_score | **31** (Language 20×0.25=5 + Education ≈24×0.20=4.8 + Pathway Fit ≈18×0.20=3.6 + Timeline 80×0.15=12 + Financial ≈22×0.10=2.2 + Doc ≈38×0.10=3.8 = 31.4) |

**Dry-run predicted**

| Field | Predicted | Match |
|---|---|---|
| pathway | ausbildung | ✅ |
| german_level | A1 | ✅ |
| timeline | 2_years_plus | ✅ |
| flags | _(none)_ | ❌ (dry-run always returns []) |
| overall_score | 31 | ✅ (within ±10) |

**Score:** 0.800 — **PASS** _(flag miss; overall_score hit balances)_

**Reviewed:** [ ] yes  
**Notes:**

---

## Example 11 — Hospitality ausbildung, A2 (Guatemala, A2, Culinary Arts)

**Input profile**

| Field | Value |
|---|---|
| country | Guatemala |
| pathway | ausbildung |
| german_level | A2 |
| english_level | B1 |
| education_level | high_school |
| field_of_study | Culinary Arts |
| work_experience_years | 2 |
| timeline | 1_year |
| financial_situation | "Limited savings, need part-time income." |

**Expected labels**

| Label | Value |
|---|---|
| expected_pathway | ausbildung |
| expected_german_level | A2 |
| expected_timeline | 1_year |
| expected_flags | language_gap |
| expected_overall_score | **null** (kitchen roles sometimes accept A2 — pathway_fit highly AI-discretionary) |

**Dry-run predicted**

| Field | Predicted | Match |
|---|---|---|
| pathway | ausbildung | ✅ |
| german_level | A2 | ✅ |
| timeline | 1_year | ✅ |
| flags | _(none)_ | ❌ (dry-run always returns []) |
| overall_score | 60 (no expected — excluded) | n/a |

**Score:** 0.750 — **FAIL** _(flag miss; no overall_score expected → 3 dims scored)_

**Reviewed:** [ ] yes  
**Notes:**

---

## Example 12 — University, missing blocked account funds (Bolivia, B2, Medicine)

**Input profile**

| Field | Value |
|---|---|
| country | Bolivia |
| pathway | university |
| german_level | B2 |
| english_level | C1 |
| education_level | bachelor |
| field_of_study | Medicine |
| work_experience_years | 0 |
| timeline | 1_year |
| financial_situation | "I have €3,000, cannot afford the €11,000 blocked account yet." |

**Expected labels**

| Label | Value |
|---|---|
| expected_pathway | university |
| expected_german_level | B2 |
| expected_timeline | 1_year |
| expected_flags | finance_risk |
| expected_overall_score | **66** (Language 75×0.25=18.75 + Education ≈78×0.20=15.6 + Pathway Fit ≈75×0.20=15 + Timeline 60×0.15=9 + Financial ≈15×0.10=1.5 + Doc ≈60×0.10=6 = 65.85) |

**Dry-run predicted**

| Field | Predicted | Match |
|---|---|---|
| pathway | university | ✅ |
| german_level | B2 | ✅ |
| timeline | 1_year | ✅ |
| flags | _(none)_ | ❌ (dry-run always returns []) |
| overall_score | 66 | ✅ (within ±10) |

**Score:** 0.800 — **PASS** _(flag miss; overall_score hit balances)_

**Reviewed:** [ ] yes  
**Notes:**

---

## Example 13 — Mechatronics ausbildung, strong fit (Colombia, B2, Mechatronics, 4 yr)

**Input profile**

| Field | Value |
|---|---|
| country | Colombia |
| pathway | ausbildung |
| german_level | B2 |
| english_level | B1 |
| education_level | associate |
| field_of_study | Mechatronics |
| work_experience_years | 4 |
| timeline | 1_year |
| financial_situation | "Comfortable with €7,000 saved." |

**Expected labels**

| Label | Value |
|---|---|
| expected_pathway | ausbildung |
| expected_german_level | B2 |
| expected_timeline | 1_year |
| expected_flags | _(none)_ |
| expected_overall_score | **71** (Language 75×0.25=18.75 + Education ≈70×0.20=14 + Pathway Fit ≈82×0.20=16.4 + Timeline 60×0.15=9 + Financial ≈75×0.10=7.5 + Doc ≈58×0.10=5.8 = 71.45) |

**Dry-run predicted**

| Field | Predicted | Match |
|---|---|---|
| pathway | ausbildung | ✅ |
| german_level | B2 | ✅ |
| timeline | 1_year | ✅ |
| flags | _(none)_ | ✅ |
| overall_score | 71 | ✅ (within ±10) |

**Score:** 1.000 — **PASS**

**Reviewed:** [ ] yes  
**Notes:**

---

## Example 14 — Experienced work visa, 20 yr (Argentina, B1, Healthcare Administration)

**Input profile**

| Field | Value |
|---|---|
| country | Argentina |
| pathway | work_visa |
| german_level | B1 |
| english_level | B2 |
| education_level | master |
| field_of_study | Healthcare Administration |
| work_experience_years | 20 |
| timeline | 2_years_plus |
| financial_situation | "Stable, €12,000 in savings." |

**Expected labels**

| Label | Value |
|---|---|
| expected_pathway | work_visa |
| expected_german_level | B1 |
| expected_timeline | 2_years_plus |
| expected_flags | _(none)_ |
| expected_overall_score | **75** (Language 55×0.25=13.75 + Education ≈88×0.20=17.6 + Pathway Fit ≈85×0.20=17 + Timeline 80×0.15=12 + Financial ≈85×0.10=8.5 + Doc ≈65×0.10=6.5 = 75.35) |

**Dry-run predicted**

| Field | Predicted | Match |
|---|---|---|
| pathway | work_visa | ✅ |
| german_level | B1 | ✅ |
| timeline | 2_years_plus | ✅ |
| flags | _(none)_ | ✅ |
| overall_score | 75 | ✅ (within ±10) |

**Score:** 1.000 — **PASS**

**Reviewed:** [ ] yes  
**Notes:**

---

## Example 15 — Ceiling calibration (Chile, C2, Industrial Engineering, 10 yr)

**Input profile**

| Field | Value |
|---|---|
| country | Chile |
| pathway | ausbildung |
| german_level | C2 |
| english_level | C2 |
| education_level | master |
| field_of_study | Industrial Engineering |
| work_experience_years | 10 |
| timeline | 2_years_plus |
| financial_situation | "€25,000 saved, fully self-funded." |

**Expected labels**

| Label | Value |
|---|---|
| expected_pathway | ausbildung |
| expected_german_level | C2 |
| expected_timeline | 2_years_plus |
| expected_flags | _(none)_ |
| expected_overall_score | **89** (Language 100×0.25=25 + Education ≈90×0.20=18 + Pathway Fit ≈92×0.20=18.4 + Timeline 80×0.15=12 + Financial ≈95×0.10=9.5 + Doc ≈65×0.10=6.5 = 89.4) |

**Dry-run predicted**

| Field | Predicted | Match |
|---|---|---|
| pathway | ausbildung | ✅ |
| german_level | C2 | ✅ |
| timeline | 2_years_plus | ✅ |
| flags | _(none)_ | ✅ |
| overall_score | 89 | ✅ (within ±10) |

**Score:** 1.000 — **PASS**

**Reviewed:** [ ] yes  
**Notes:**

---

## Example 16 — EU citizen documentation advantage (Spain, B2, Electrical Engineering)

**Input profile**

| Field | Value |
|---|---|
| country | Spain |
| pathway | ausbildung |
| german_level | B2 |
| english_level | C1 |
| education_level | bachelor |
| field_of_study | Electrical Engineering |
| work_experience_years | 3 |
| timeline | 1_year |
| financial_situation | "€6,000 in savings." |

**Expected labels**

| Label | Value |
|---|---|
| expected_pathway | ausbildung |
| expected_german_level | B2 |
| expected_timeline | 1_year |
| expected_flags | _(none)_ |
| expected_overall_score | **74** (Language 75×0.25=18.75 + Education ≈72×0.20=14.4 + Pathway Fit ≈78×0.20=15.6 + Timeline 60×0.15=9 + Financial ≈70×0.10=7 + Doc ≈88×0.10=8.8 = 73.55; EU citizen → documentation_score ~88 vs ~60 for LATAM) |

**Dry-run predicted**

| Field | Predicted | Match |
|---|---|---|
| pathway | ausbildung | ✅ |
| german_level | B2 | ✅ |
| timeline | 1_year | ✅ |
| flags | _(none)_ | ✅ |
| overall_score | 74 | ✅ (within ±10) |

**Score:** 1.000 — **PASS**

**Reviewed:** [ ] yes  
**Notes:**

---

## Example 17 — Generalisation test (Peru, B1, Marine Biology)

**Input profile**

| Field | Value |
|---|---|
| country | Peru |
| pathway | ausbildung |
| german_level | B1 |
| english_level | B2 |
| education_level | bachelor |
| field_of_study | Marine Biology |
| work_experience_years | 1 |
| timeline | 1_year |
| financial_situation | "€3,500 saved." |

**Expected labels**

| Label | Value |
|---|---|
| expected_pathway | ausbildung |
| expected_german_level | B1 |
| expected_timeline | 1_year |
| expected_flags | _(none)_ |
| expected_overall_score | **null** (non-standard field — model must invent a sector mapping; pathway_fit unpredictable within ±10) |

**Dry-run predicted**

| Field | Predicted | Match |
|---|---|---|
| pathway | ausbildung | ✅ |
| german_level | B1 | ✅ |
| timeline | 1_year | ✅ |
| flags | _(none)_ | ✅ |
| overall_score | 60 (no expected — excluded) | n/a |

**Score:** 1.000 — **PASS**

**Reviewed:** [ ] yes  
**Notes:**

---

## Example 18 — Long financial text, input-length stress test (Mexico, B1, Accounting)

**Input profile**

| Field | Value |
|---|---|
| country | Mexico |
| pathway | ausbildung |
| german_level | B1 |
| english_level | B1 |
| education_level | bachelor |
| field_of_study | Accounting |
| work_experience_years | 5 |
| timeline | 1_year |
| financial_situation | "I currently have €8,000 in savings and am expecting a bonus from my current employer in Q3 worth approximately €3,000 after tax. My parents have agreed to provide up to €5,000 as a one-time gift. I also have a small rental income of €200/month from a property I co-own with my brother. I have no debts. My monthly expenses in my current country are €700. I am open to apprenticeship stipends and working part-time during language course. I do not expect to need external loans if I am accepted into an Ausbildung program, since the monthly stipend would cover living costs." |

**Expected labels**

| Label | Value |
|---|---|
| expected_pathway | ausbildung |
| expected_german_level | B1 |
| expected_timeline | 1_year |
| expected_flags | _(none)_ |
| expected_overall_score | **null** (financial score depends on whether model reads €8k floor or full €16k+ picture — too variable for ±10 bound) |

**Dry-run predicted**

| Field | Predicted | Match |
|---|---|---|
| pathway | ausbildung | ✅ |
| german_level | B1 | ✅ |
| timeline | 1_year | ✅ |
| flags | _(none)_ | ✅ |
| overall_score | 60 (no expected — excluded) | n/a |

**Score:** 1.000 — **PASS**

**Reviewed:** [ ] yes  
**Notes:**

---

## Summary

| # | Profile | Dry-run Score | Status | Needs Live-run Flag Review |
|---|---|---|---|---|
| 1 | Mexico · ausbildung · B2 · Mechanical Eng | 1.000 | PASS | — |
| 2 | Colombia · ausbildung · A1 · General Studies | 0.800 | PASS | ⚠️ flags |
| 3 | Peru · ausbildung · B1 · Nursing | 1.000 | PASS | — |
| 4 | Brazil · ausbildung · B1 · Computer Science | 0.750 | FAIL | ⚠️ flags |
| 5 | Argentina · university · C1 · Economics | 1.000 | PASS | — |
| 6 | Chile · university · A2 · Architecture | 0.800 | PASS | ⚠️ flags |
| 7 | Venezuela · work_visa · B1 · Software Eng | 1.000 | PASS | — |
| 8 | Brazil · ausbildung · A2 · Nursing | 0.750 | FAIL | ⚠️ flags |
| 9 | Mexico · ausbildung · B1 · IT | 1.000 | PASS | — |
| 10 | Ecuador · ausbildung · A1 · (none) | 0.800 | PASS | ⚠️ flags |
| 11 | Guatemala · ausbildung · A2 · Culinary Arts | 0.750 | FAIL | ⚠️ flags |
| 12 | Bolivia · university · B2 · Medicine | 0.800 | PASS | ⚠️ flags |
| 13 | Colombia · ausbildung · B2 · Mechatronics | 1.000 | PASS | — |
| 14 | Argentina · work_visa · B1 · Healthcare Admin | 1.000 | PASS | — |
| 15 | Chile · ausbildung · C2 · Industrial Eng | 1.000 | PASS | — |
| 16 | Spain · ausbildung · B2 · Electrical Eng | 1.000 | PASS | — |
| 17 | Peru · ausbildung · B1 · Marine Biology | 1.000 | PASS | — |
| 18 | Mexico · ausbildung · B1 · Accounting | 1.000 | PASS | — |

**Dry-run totals:** 13 PASS / 5 FAIL (pass rate 72%) — all FAIL cases are flag-prediction misses only (routing fields 100% accurate). Flag accuracy requires `--live` run.

> **Note on flag prediction in dry-run:** The FakeAnthropicClient returns `predicted_flags=[]` for all examples. This is a known dry-run limitation — it does NOT mean the real model fails to predict flags. Run `python scripts/run_evaluation.py --live` (and confirm the €0.90–1.80 cost) to measure real flag recall.
