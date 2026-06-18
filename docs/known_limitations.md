# Known Model Limitations

This document records the known limitations of the AI models powering Klar's three use cases. Limitations are surfaced in the product UI where they affect user decisions.

## UC-01 — Germany Readiness Diagnostic

**Limitation: Language score calibration is coarse.**
The scoring rubric maps CEFR levels to fixed point ranges (e.g., B1 → 55, B2 → 75). Scores do not reflect dialect, regional accent exposure, or spoken vs. written proficiency split. Two students with B1 certificates from different learning contexts may have meaningfully different practical readiness.

**Limitation: Financial score cannot verify stated amounts.**
The model scores based on what the student writes about their finances. There is no verification step. A student who over-states savings will receive a higher financial score than warranted.

**Limitation: Field-of-study recognition likelihood is estimated, not sourced.**
The `education_score` dimension includes a factor for recognition of foreign qualifications. This is AI-estimated based on general knowledge of ANABIN categories, not a live lookup. Always verify with anabin.kmk.org or ZAB.

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
