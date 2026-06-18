## What changed and why

<!-- One paragraph. Focus on the "why", not just the "what". -->

## Type of change
- [ ] Bug fix
- [ ] Feature
- [ ] Prompt change ← triggers the checklist below
- [ ] Migration
- [ ] Docs / tooling

---

## Prompt Review Checklist

**Complete this section if `SYSTEM_PROMPT`, `MATCH_PROMPT`, or `DOCUMENT_PROMPT` changed.**

The version bump and the self-review are two separate steps — completing one does not complete the other.

- [ ] I re-read the **full prompt diff line by line** before approving this merge (not just the version bump commit)
- [ ] I confirmed the wording change does not introduce prompt injection surface (no new user-controlled interpolation without sanitisation)
- [ ] I bumped the relevant `*_PROMPT_VERSION` constant in `services/diagnostic_versions.py`
- [ ] I ran `python scripts/check_prompt_drift.py --update` and committed the updated `.prompt_hashes`

## Gates

- [ ] `python -m pytest tests/ -v` passes locally
- [ ] `python scripts/check_prompt_drift.py` exits 0 (CI also enforces this)
