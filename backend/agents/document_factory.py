import json
import os
import time
from typing import TYPE_CHECKING

from anthropic import Anthropic
from langsmith.wrappers import wrap_anthropic
from services.ai_observability import (
    AI_MODEL,
    AI_PROVIDER,
    REQUEST_TYPE_DOCUMENT_FACTORY,
    build_usage_event,
    extract_usage_tokens,
)

if TYPE_CHECKING:
    from models.schemas import DocumentFacts

client = wrap_anthropic(Anthropic(max_retries=2))


class DocumentAIError(RuntimeError):
    def __init__(self, message: str, *, error_type: str | None = None):
        super().__init__(message)
        self.error_type = error_type

_TARGET_LANGUAGE_LABELS = {"en": "English", "es": "Spanish"}

DOCUMENT_PROMPT = """You are Klar's German Document Factory.
You write professional document DRAFTS for Latin American candidates
applying to German Ausbildung, university, or work visa pathways.
You produce BOTH the German original AND a translation into the requested
target language in a single response.

CRITICAL RULE — NEVER INVENT FACTS:
You will be given a coarse profile: education level, field of study,
years of experience, language levels. You do NOT have: exact employer
names, exact job titles, exact dates, street addresses, phone numbers,
or specific institution names.

For ANY information you do not have, use a clearly bracketed
placeholder IN GERMAN (e.g., "[Name der Bildungseinrichtung]",
"[Arbeitgeber], [Ort]", "[Zeitraum, z.B. 2021–2023]", "[Ihre Adresse]",
"[Ihre Telefonnummer]"). Keep these German-language placeholders in
BOTH the German and the translated version — they are format markers
the student fills in later, not content to translate.

NEVER fill placeholders with an invented specific name, address, date,
or employer — even a plausible-sounding one.

What you CAN write freely:
- The "profil" professional summary paragraph (translate for target version)
- General competency "beschreibung" text for entries (translate for target)
- The skills list "kompetenzen" (translate each skill for target version)
- Cover letter body text (translate for target version)

German CV conventions: reverse chronological, Profil at top, CEFR levels
real (from profile — never placeholder), formal tone.

German cover letter: "Sehr geehrte Damen und Herren,", "[Name des
Unternehmens]" for employer, max 350 words, "Mit freundlichen Grüßen,".

Target-language cover letter: equivalent greeting/closing conventions
for that language; keep all [bracketed] placeholders in German.

RESPOND ONLY WITH VALID JSON (no markdown fences):
{
  "cv_de": {
    "profil": "<German 3-4 sentence summary>",
    "ausbildung": [{"zeitraum": "[Zeitraum]", "beschreibung": "<German>"}],
    "berufserfahrung": [{"zeitraum": "[Zeitraum]", "beschreibung": "<German, employer as [Arbeitgeber], [Ort]>"}],
    "sprachkenntnisse": [{"sprache": "<language>", "niveau": "<REAL CEFR>"}],
    "kompetenzen": ["<German skill>"]
  },
  "anschreiben_de": "<German cover letter>",
  "cv_target": {
    "profil": "<target-language 3-4 sentence summary, same [bracketed] placeholders>",
    "ausbildung": [{"zeitraum": "[Zeitraum]", "beschreibung": "<target language, same placeholders>"}],
    "berufserfahrung": [{"zeitraum": "[Zeitraum]", "beschreibung": "<target language, same placeholders>"}],
    "sprachkenntnisse": [{"sprache": "<language name in target language>", "niveau": "<REAL CEFR>"}],
    "kompetenzen": ["<target-language skill>"]
  },
  "anschreiben_target": "<target-language cover letter, [bracketed] placeholders kept in German>"
}"""


def generate_documents(
    student_data: dict,
    *,
    diagnostic_id: str | None = None,
    student_id: str | None = None,
    target_language: str = "en",
) -> dict:
    lang_label = _TARGET_LANGUAGE_LABELS.get(target_language, "English")
    user_message = f"""Generate bilingual German + {lang_label} CV and cover letter for:

Name: {student_data['name']}
Pathway: {student_data['pathway']}
Education: {student_data['education_level']} in {student_data.get('field_of_study', 'General Studies')}
Work experience: {student_data['work_experience_years']} years
German level: {student_data['german_level']}
English level: {student_data.get('english_level', 'Not specified')}
Country: {student_data['country']}
Target translation language: {lang_label}

Return the four-field JSON structure specified (cv_de, anschreiben_de, cv_target, anschreiben_target)."""

    doc_start = time.perf_counter()
    timeout = float(os.getenv("DOCUMENT_TIMEOUT_SECONDS", "60"))
    response = client.messages.create(
        model=AI_MODEL,
        max_tokens=5000,
        system=DOCUMENT_PROMPT,
        messages=[{"role": "user", "content": user_message}],
        timeout=timeout,
    )
    doc_latency_ms = int((time.perf_counter() - doc_start) * 1000)
    doc_in, doc_out = extract_usage_tokens(response)
    doc_usage = build_usage_event(
        provider=AI_PROVIDER,
        model=AI_MODEL,
        request_type=REQUEST_TYPE_DOCUMENT_FACTORY,
        diagnostic_id=diagnostic_id,
        student_id=student_id,
        input_tokens=doc_in,
        output_tokens=doc_out,
        latency_ms=doc_latency_ms,
        success=True,
    )

    from pydantic import ValidationError
    from models.ai_outputs import DocumentAIOutput

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    try:
        parsed = json.loads(raw.strip())
    except json.JSONDecodeError as exc:
        raise DocumentAIError(
            "Document response was not valid JSON.",
            error_type="JSONDecodeError",
        ) from exc

    try:
        validated = DocumentAIOutput.model_validate(parsed)
    except ValidationError as exc:
        raise DocumentAIError(
            "Document response failed schema validation.",
            error_type="SchemaValidationError",
        ) from exc

    result = validated.model_dump()
    result["_ai_usage"] = doc_usage
    return result


REGENERATE_PROMPT_VERSION = "document_factory_regenerate_prompt_v1"

REGENERATE_SYSTEM = """You are Klar's German Document Factory — regeneration pass.
You have already produced a first-draft CV and cover letter for this candidate.
Now you are producing a refined version using REAL facts the student has confirmed.

CRITICAL RULE — NEVER INVENT FACTS:
Use ONLY the confirmed facts provided. For any detail NOT in the confirmed facts,
keep the original bracketed placeholder (e.g., "[Arbeitgeber]", "[Zeitraum]").

CONFIRMED FACTS (use these naturally — do NOT bracket them):
{facts_block}

{keywords_block}

German CV conventions: reverse chronological, Profil at top, CEFR levels real (from profile).
German cover letter: "Sehr geehrte Damen und Herren,", formal tone, max 350 words.

RESPOND ONLY WITH VALID JSON (no markdown fences), same schema as before:
{{
  "cv_de": {{
    "profil": "<German 3-4 sentence summary>",
    "ausbildung": [{{"zeitraum": "...", "beschreibung": "..."}}],
    "berufserfahrung": [{{"zeitraum": "...", "beschreibung": "..."}}],
    "sprachkenntnisse": [{{"sprache": "...", "niveau": "..."}}],
    "kompetenzen": ["..."]
  }},
  "anschreiben_de": "<German cover letter>",
  "cv_target": {{
    "profil": "<target-language summary, same [bracketed] placeholders>",
    "ausbildung": [{{"zeitraum": "...", "beschreibung": "..."}}],
    "berufserfahrung": [{{"zeitraum": "...", "beschreibung": "..."}}],
    "sprachkenntnisse": [{{"sprache": "...", "niveau": "..."}}],
    "kompetenzen": ["..."]
  }},
  "anschreiben_target": "<target-language cover letter, [bracketed] placeholders kept in German>"
}}"""


def _build_facts_block(facts: "DocumentFacts | None") -> str:
    if not facts:
        return "No confirmed facts provided — keep all placeholders."
    lines = []
    mapping = [
        ("Employer name", facts.employer_name),
        ("Employer location", facts.employer_location),
        ("Job title", facts.job_title),
        ("Employment period", facts.employment_period),
        ("Employment duties", facts.employment_duties),
        ("Institution name", facts.institution_name),
        ("Institution location", facts.institution_location),
        ("Study period", facts.study_period),
        ("Street address", facts.street_address),
        ("Phone number", facts.phone_number),
        ("Full address", facts.full_address),
        ("City", facts.city),
    ]
    for label, value in mapping:
        if value and value.strip():
            lines.append(f"- {label}: {value.strip()}")
    if facts.placeholder_values:
        for placeholder, value in facts.placeholder_values.items():
            if value and value.strip():
                lines.append(f"- Replace [{placeholder}] with: {value.strip()}")
    return "\n".join(lines) if lines else "No confirmed facts provided — keep all placeholders."


def _build_keywords_block(target_keywords: list[dict]) -> str:
    if not target_keywords:
        return ""
    titles = ", ".join(
        f"{p.get('beruf', '')} ({p.get('titel', '')})" for p in target_keywords if p.get("beruf")
    )
    return (
        f"KEYWORD TAILORING — the student is applying to these positions: {titles}. "
        "Where truthful and natural, use matching professional vocabulary in the Profil and Kompetenzen sections. "
        "Never claim a skill or experience the student has not indicated, and never force unnatural keyword stuffing."
    )


def regenerate_documents(
    student_data: dict,
    *,
    facts: "DocumentFacts | None" = None,
    target_keywords: list[dict] | None = None,
    target_language: str = "en",
    diagnostic_id: str | None = None,
    student_id: str | None = None,
) -> dict:
    from models.schemas import DocumentFacts as _DocumentFacts  # avoid circular at module load

    lang_label = _TARGET_LANGUAGE_LABELS.get(target_language, "English")
    facts_block = _build_facts_block(facts)
    keywords_block = _build_keywords_block(target_keywords or [])

    system_prompt = REGENERATE_SYSTEM.format(
        facts_block=facts_block,
        keywords_block=keywords_block,
    )

    user_message = (
        f"Regenerate bilingual German + {lang_label} CV and cover letter for:\n\n"
        f"Name: {student_data['name']}\n"
        f"Pathway: {student_data['pathway']}\n"
        f"Education: {student_data['education_level']} in {student_data.get('field_of_study', 'General Studies')}\n"
        f"Work experience: {student_data['work_experience_years']} years\n"
        f"German level: {student_data['german_level']}\n"
        f"English level: {student_data.get('english_level', 'Not specified')}\n"
        f"Country: {student_data['country']}\n"
        f"Target translation language: {lang_label}\n\n"
        "Incorporate the confirmed facts naturally. "
        "Return the four-field JSON structure (cv_de, anschreiben_de, cv_target, anschreiben_target)."
    )

    start = time.perf_counter()
    timeout = float(os.getenv("DOCUMENT_TIMEOUT_SECONDS", "60"))
    response = client.messages.create(
        model=AI_MODEL,
        max_tokens=5000,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
        timeout=timeout,
    )
    latency_ms = int((time.perf_counter() - start) * 1000)
    in_tok, out_tok = extract_usage_tokens(response)
    usage = build_usage_event(
        provider=AI_PROVIDER,
        model=AI_MODEL,
        request_type=REQUEST_TYPE_DOCUMENT_FACTORY,
        diagnostic_id=diagnostic_id,
        student_id=student_id,
        input_tokens=in_tok,
        output_tokens=out_tok,
        latency_ms=latency_ms,
        success=True,
    )

    from pydantic import ValidationError
    from models.ai_outputs import DocumentAIOutput

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    try:
        parsed = json.loads(raw.strip())
    except json.JSONDecodeError as exc:
        raise DocumentAIError(
            "Regenerated document response was not valid JSON.",
            error_type="JSONDecodeError",
        ) from exc

    try:
        validated = DocumentAIOutput.model_validate(parsed)
    except ValidationError as exc:
        raise DocumentAIError(
            "Regenerated document response failed schema validation.",
            error_type="SchemaValidationError",
        ) from exc

    result = validated.model_dump()
    result["_ai_usage"] = usage
    return result
