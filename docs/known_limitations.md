# Known Model Limitations

This document records the known limitations of the AI models powering Klar's three use cases. Limitations are surfaced in the product UI where they affect user decisions.

## UC-01 — Germany Readiness Diagnostic

**Limitation: Language score calibration is coarse.**
The scoring rubric maps CEFR levels to fixed point ranges (e.g., B1 → 55, B2 → 75). Scores do not reflect dialect, regional accent exposure, or spoken vs. written proficiency split. Two students with B1 certificates from different learning contexts may have meaningfully different practical readiness.

**Limitation: Financial score cannot verify stated amounts.**
The model scores based on what the student writes about their finances. There is no verification step. A student who over-states savings will receive a higher financial score than warranted.

**Limitation: Field-of-study recognition likelihood is estimated, not sourced.**
The `education_score` dimension includes a factor for recognition of foreign qualifications. This is AI-estimated based on general knowledge of ANABIN categories, not a live lookup. Always verify with anabin.kmk.org or ZAB.

**Limitation: Recommended programs and URLs may be hallucinated.**
The model is asked to recommend 3 specific programs or resources with URLs but is given no grounding data — no retrieval, no live search, no verified catalogue. It can plausibly generate a program name that sounds real but does not exist, or a URL that looks correct but leads to a 404 or the wrong page. This is a materially different risk from a coarse score because it is a concrete, checkable claim: a student may follow the link, find the page missing or unrelated, and lose trust or — worse — waste time applying to a non-existent program.

Mitigation in place: `SYSTEM_PROMPT` (as of `germany_diagnostic_prompt_v3`) instructs the model to return `null` for `url` unless it is certain the link points to a real, active page at a well-known institution. The UI shows a disclaimer near recommendations. This reduces but does not eliminate the risk — always verify program names and links independently before applying.

**Measured URL hallucination rate (2026-06-18):** 0 out of 60 URLs emitted were on unrecognised domains, across 20 approved diagnostics (run `scripts/measure_url_hallucination_rate.py` to reproduce). The model emits ~3 URLs per diagnostic and always from recognised German institution domains (DAAD, Goethe-Institut, Make it in Germany, BIBB, AHK, DW, Ausbildung.de, etc.). Residual risk: domain-level check only — specific URL paths (e.g., database IDs in BIBB profile URLs) are not HTTP-verified. See `docs/failure_examples.md` (Failure 3) for a concrete example. Rerun this measurement after any SYSTEM_PROMPT change to the URL grounding rule.

**Limitation: Response relevance is not automatically measured (deferred).**
There is currently no automated metric for whether the diagnostic summary and roadmap are *relevant* to the student's specific profile — only routing fields (pathway, german_level, timeline) are compared against ground-truth labels. Building a reliable relevance metric requires either (a) an LLM-as-judge rubric (introduces its own hallucination risk) or (b) a human-annotated relevance scale (requires 50+ rated examples). Both are deferred until the system accumulates sufficient approved diagnostics to support meaningful annotation. Until then, relevance is assessed via the human review gate (EU AI Act Art 14 — all diagnostics are reviewed before being surfaced to students).

## UC-02 — Ausbildung Position Matching

**Limitation: German language requirements are AI-estimated, not employer-stated.**
The positions sourced from the Bundesagentur für Arbeit API do not include German language requirements. The model estimates requirements based on occupation type using a rubric (e.g., patient-facing healthcare → B2 minimum). This estimate may be wrong for specific employers or regions. The UI surfaces this explicitly with a disclosure banner and marks positions with a "German level may be insufficient" warning badge when concern is flagged.

**Limitation: Sector classification uses a 5-bucket heuristic.**
The sector classification step (Haiku model) maps a free-text `field_of_study` to one of: nursing, mechatronics, it, hospitality, gastronomy. Fields that don't map cleanly (e.g., marine biology, architecture) may land in the wrong sector or return no matches.

**Limitation: Candidate pool is limited to 15 positions per sector.**
The ranking step only sees 15 positions fetched from the DB. If the best matches for a student are outside this window, they won't be ranked. Position data is refreshed from the BA API externally.

## UC-04 — Document Factory

**Limitation: CV and cover letter use bracketed placeholders for unknown information.**
The model deliberately cannot invent specific employer names, dates, or institution names it was not given. Output always contains `[Arbeitgeber]`, `[Zeitraum]`, `[Name der Bildungseinrichtung]` placeholders. The student must fill these in with accurate information before submitting.

**Limitation: German writing quality varies by profile completeness.**
Profiles with minimal input (e.g., `field_of_study` left blank) will produce generic competency descriptions. More complete profiles produce more targeted output.

**Limitation: Cover letters use a generic salutation.**
Without a specific contact person, the letter uses "Sehr geehrte Damen und Herren," which is standard but less effective than a named addressee.

## General

**Limitation: All AI outputs are advisory, not authoritative.**
Scores, match rankings, and document drafts are starting points, not final answers. Users should verify all information with official sources (employers, consulates, recognition authorities) before making decisions.
