# Failure Examples — UC-01 Germany Readiness Diagnostic

**Last updated:** 2026-06-18  
**Source:** 20 approved diagnostics in production DB + eval pipeline runs  
**PII status:** All student names redacted to [Student A/B/C]; email, phone never stored

> **Honest status:** There are currently **0 human-reviewed rejected diagnostics** in the production DB.
> All 20 diagnostics were approved by a reviewer. This document therefore captures two types of evidence:
> (a) structural/system failures caught in the pipeline before outputs reached students, and
> (b) a real schema-inconsistency found in production data. It does NOT contain examples of diagnostics
> that were wrong and flagged by a human reviewer — that data does not exist yet at this volume.
> When rejected diagnostics accrue, they should be added here with their `reviewer_notes` (PII-scrubbed)
> and the pattern that caused the rejection.

---

## Failure 1 — Markdown-wrapped JSON response (historical, now mitigated)

**Diagnostic IDs:** 17 of 20 production diagnostics (all pre-2026-06-18)  
**Status when observed:** Approved (reviewers did not surface this as a failure — it was invisible at the output layer)  
**Severity:** Low-latency-impact, now mitigated  

### What happened

The model returned valid JSON wrapped in a Markdown code fence:

```
```json
{
  "overall_score": 62,
  "language_score": 55,
  ...
}
```
```

`json.loads()` on this string raises `JSONDecodeError` because of the ` ```json\n ` prefix. Without the stripping logic, the diagnostic would fail with a `500 Internal Server Error`.

### How it was caught

The `parse_diagnostic_response()` function was updated to detect and strip Markdown wrappers before parsing:

```python
if raw.startswith("```"):
    raw = raw.split("```")[1]
    if raw.startswith("json"):
        raw = raw[4:]
```

`scripts/measure_url_hallucination_rate.py` (2026-06-18 run) confirmed that 17/20 production `raw_output` values had this wrapper — meaning the early deployment accepted responses that would have crashed the current parser.

### Lesson

The SYSTEM_PROMPT must include an explicit "RESPOND ONLY WITH VALID JSON. No markdown, no text outside the JSON." directive. This was added in `germany_diagnostic_prompt_v3`. The stripping logic in `parse_diagnostic_response()` is a belt-and-suspenders fallback, not the primary mitigation.

---

## Failure 2 — Non-canonical field values bypass schema normalization (real production case)

**Diagnostic ID:** `4960d5a0` (truncated)  
**Status:** Approved  
**Severity:** Medium — causes silent routing errors downstream  

### What happened

Student submitted a profile with non-canonical field values:

| Field | Submitted value | Canonical value |
|---|---|---|
| pathway | `"University"` (capital U) | `"university"` |
| education_level | `"Bachelor's Degree"` (human-readable phrase) | `"bachelor"` |

The API accepted these values and passed them to `run_diagnostic()`. The model produced a valid response (overall_score=52, financial_score=20, timeline_score=25 for a 6-month university pathway with minimal savings — all realistic). However, downstream evaluation comparisons and sector-routing used the raw non-canonical values, causing silent mismatches.

### Evidence

```python
# From production DB (students table):
{
    "pathway": "University",      # should be "university"
    "education_level": "Bachelor's Degree",  # should be "bachelor"
    "german_level": "B1",
    "timeline": "6_months",
    "country": "Argentina"
}
# Diagnostic output (correct given inputs):
{
    "overall_score": 52,
    "language_score": 55,
    "financial_score": 20,       # low — student had minimal savings for a university pathway
    "timeline_score": 25         # low — 6 months is unrealistic for university
}
```

### How it was caught

Spotted during the 2026-06-18 evaluation audit when `check_prompt_drift.py` identified a diagnostic with `pathway_noncanon=True` in the data sweep.

### Lesson

The `StudentProfile` Pydantic schema should enforce lowercase-enum validation for `pathway`, `education_level`, `german_level`, and `timeline` fields. Currently these are free-text strings with no enum constraint. A `validator` that calls `.lower()` and maps known aliases (`"Bachelor's Degree"` → `"bachelor"`) would prevent this class of issue.

**Recommended fix (not yet implemented):**
```python
from pydantic import field_validator

@field_validator("pathway", mode="before")
@classmethod
def normalize_pathway(cls, v):
    return str(v).lower().strip() if v else v
```

---

## Failure 3 — URL path specificity risk (not HTTP-verified, residual risk)

**Diagnostic ID:** `c41f70c1` (truncated)  
**Status:** Approved  
**Severity:** Low — domain is real, path might be wrong  

### What happened

The model recommended BIBB with a specific URL containing an apprenticeship profile ID:

```
"name": "BIBB – Kfz-Mechatroniker Ausbildungsprofil"
"url": "https://www.bibb.de/dienst/berufesuche/de/index_berufesuche.php/profile/apprenticeship/21376"
```

The domain (`bibb.de`) is a real, well-known German institution explicitly in the URL grounding safe-domain list. However, the specific path `/dienst/berufesuche/de/.../profile/apprenticeship/21376` contains a numeric ID (`21376`) that the model may have invented or hallucinated. A student following this URL might land on a 404 or the wrong apprenticeship profile.

The `measure_url_hallucination_rate.py` script performs domain-level classification only — it cannot verify whether a specific URL path is accurate without making an HTTP request.

### Evidence

```
[measure] 2026-06-18 run: 60 URLs seen from 20 diagnostics, 0 on unrecognized domains.
NOTE: domain-level only. Path-level accuracy not verified.
```

### Lesson

The SYSTEM_PROMPT URL grounding rule (`return null unless certain the specific URL points to a real, currently active page`) is the only mitigation. For complex URLs with specific path IDs (like database record IDs), the model should prefer to emit `null` rather than attempt to reconstruct the full path. This is a known residual risk documented in `docs/known_limitations.md`.

**Monitoring:** Add periodic HTTP-reachability checks of all emitted URLs (could be run as a weekly cron against the last N approved diagnostics). Not yet implemented.

---

## Template for future failure entries

When a human reviewer rejects a diagnostic, capture it here:

```markdown
## Failure N — [brief description]

**Diagnostic ID:** [first 8 chars only, never full UUID unless needed]
**Status when observed:** Rejected
**Reviewer notes (PII-scrubbed):** "[reviewer_notes field with names/emails/phones redacted]"
**Severity:** Low / Medium / High

### What happened
[2-3 sentences describing the failure mode]

### Evidence
[Relevant fields from the diagnostic output — scores, summary snippet, flags]

### Pattern
[Does this match a known limitation? Is this a new failure mode? Which prompt
version was active (check DIAGNOSTIC_PROMPT_VERSION at time of run)?]

### Resolution
[Was this a one-off or a systematic issue? Was a prompt fix applied? Was it
added to the adversarial test suite?]
```
