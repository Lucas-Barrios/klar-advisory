import json
import time

from anthropic import Anthropic
from langsmith.wrappers import wrap_anthropic
from services.ai_observability import (
    AI_MODEL,
    AI_PROVIDER,
    REQUEST_TYPE_DOCUMENT_FACTORY,
    build_usage_event,
    extract_usage_tokens,
)

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
    response = client.messages.create(
        model=AI_MODEL,
        max_tokens=5000,
        system=DOCUMENT_PROMPT,
        messages=[{"role": "user", "content": user_message}],
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
