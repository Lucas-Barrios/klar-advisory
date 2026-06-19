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

---

## Pilot-Phase Infrastructure Known Limitations

The following gaps were identified in a reliability audit on 2026-06-19. They are deferred from the initial fix night (Items 1–4 of that audit were patched in the same session). They are documented here rather than fixed because they are acceptable during the pilot phase but should be addressed before scaling.

**Limitation: No automated alerting on error-rate spikes.**
There is no Sentry, Datadog, or equivalent integration. Server-side errors are logged but only visible by manually tailing Railway/Render logs or querying Supabase. During the pilot, the operator monitors logs actively; at scale this is not sustainable. Mitigation path: add a Sentry DSN and `sentry-sdk` integration to the FastAPI app.

**Limitation: Supabase calls in most endpoints have no per-call error boundaries.**
Only the Stripe webhook's critical DB unlock (payments.py) and the student-fetch block are individually try/caught. All other Supabase calls (audit log, progress updates, AI usage logging) can surface as unhandled 500s. During the pilot the Supabase service has been reliable; at scale or during Supabase incidents, these would need individual error boundaries with graceful degradation.

**Limitation: No durable job queue — background tasks are in-process.**
`BackgroundTasks` (FastAPI) runs position matching and n8n notification in the same process as the HTTP handler. If the server restarts mid-flight or a task crashes silently, there is no retry. The n8n webhook has a 10s timeout (patched 2026-06-19) and will log errors, but a missed webhook means the admin never receives the review notification for that diagnostic. Mitigation path: move background work to a durable queue (e.g., Celery + Redis, or a Supabase edge function trigger).

**Limitation: No load testing has been run.**
The system has not been benchmarked under concurrent load. Anthropic API concurrency limits, Supabase connection pool limits, and rate-limiter behaviour under traffic bursts are untested. The 5/hour per-IP rate limit on the diagnostic endpoint is the primary defence at pilot scale.

**Limitation: Stripe SDK retry config is default.**
`stripe` SDK retry behaviour is using library defaults (typically 2 retries). For the webhook path, Stripe's own retry mechanism is the safety net (raising 500 causes Stripe to retry). For the checkout-session creation path, a transient Stripe API error returns 500 to the user with no server-side retry. This is acceptable at pilot volume.

**Limitation: Frontend errors.ts has two uncovered edge cases.**
The `verify-session` 400 path (Stripe session not found) and the `create-checkout-session` 500 path currently return raw error strings rather than a typed user-facing message. These were identified in the audit but deferred; they affect error display only, not payment processing correctness.

---

## Observability and Traceability Known Limitations

The following gaps were identified in a reliability audit on 2026-06-19. They are documented here as a record; none are blocking for the pilot phase.

**Limitation: LangSmith traces contained unredacted student PII — now mitigated with field-level redaction.**
Field-level redaction is now applied to LangSmith traces via a `hide_inputs` / `hide_outputs` callback wired into all three agent `Client` instances (`germany_diagnostic`, `document_factory`, `ausbildung_matcher`). The callback (`services/trace_redaction.py`) replaces the values of known PII labels (student name, financial situation, current location, employer name, street address, phone number, full address) with `[REDACTED]` before they are stored in LangSmith. The redaction operates exclusively on the LangSmith trace copy — it is never in the path between the application and the Anthropic API. Residual gaps: free-form PII that does not follow the structured label format (e.g., PII embedded in a student's free-text answer) is not caught by label-based patterns. Before scaling to production, verify LangSmith project-level data-processing agreement is in place per the privacy register GDPR processor entry.

**Limitation: No request correlation ID spans a single diagnostic's multi-service call chain.**
A diagnostic run invokes the Germany diagnostic agent, sector classifier, Ausbildung matcher, and optionally the document factory in sequence or as background tasks. Each generates its own LangSmith trace and `ai_usage_events` row, but there is no shared `correlation_id` that links them. Reconstructing the full chain for a given diagnostic requires joining on `diagnostic_id` and inferring ordering from timestamps.

**Limitation: No aggregate error-rate or cost-overrun alerting exists.**
Failures are logged to Render/Railway stderr and written to `ai_usage_events` (with `success=False`), but no threshold-based alert fires if the error rate or cumulative cost exceeds a bound. Mitigation path: add a Sentry DSN or a Supabase Edge Function cron that queries `ai_usage_events` and pages on anomalies.

**Limitation: LangSmith traces are not grouped into a connected multi-step workflow per student.**
Each service call (diagnostic, sector, match, document) creates an isolated LangSmith trace rather than a nested chain under a single parent run. There is no parent run ID threaded through the call chain, so LangSmith shows four unrelated traces rather than one cohesive workflow view per diagnostic.

**Limitation: No student-facing feedback mechanism exists.**
Students have no way to flag a diagnostic result as wrong, irrelevant, or harmful. This is distinct from the consultant review/approval flow (which is an operator-facing gate, not a student-facing signal). Absent student feedback, quality regression can only be detected via the operator's post-approval review or by running `scripts/measure_url_hallucination_rate.py` periodically.
