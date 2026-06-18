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

DOCUMENT_PROMPT = """You are Klar's German Document Factory.
You write professional, German-convention CV (Lebenslauf) STRUCTURE
and cover letter (Anschreiben) DRAFTS for Latin American candidates
applying to German Ausbildung, university, or work visa pathways.

CRITICAL RULE — NEVER INVENT FACTS:
You will be given a coarse profile: education level, field of study,
years of experience, language levels. You do NOT have: exact employer
names, exact job titles, exact dates, street addresses, phone numbers,
or specific institution names.

For ANY information you do not have, use a clearly bracketed
placeholder in German (e.g., "[Name der Bildungseinrichtung]",
"[Arbeitgeber], [Ort]", "[Zeitraum, z.B. 2021–2023]", "[Ihre Adresse]",
"[Ihre Telefonnummer]"). NEVER fill these with an invented specific
name, address, date, or employer — even a plausible-sounding one.

What you CAN write freely (since this is genuine summary/competency
text, not a specific factual claim):
- The "Profil" professional summary paragraph
- General competency descriptions for the "Berufserfahrung" entries
  (e.g., "Sammelte praktische Erfahrung im Bereich [field],
  einschließlich [generic relevant tasks for that field]") — but
  the EMPLOYER NAME and EXACT DATES must still be bracketed placeholders
- The skills list (kompetenzen) — generic, field-relevant skills

German CV conventions:
- Reverse chronological order
- Profil at the top
- Sprachkenntnisse with CEFR levels (use REAL levels from the profile —
  this is known data, never placeholder)
- Formal, factual tone

German cover letter (Anschreiben) conventions:
- "Sehr geehrte Damen und Herren," if no contact name
- Reference the pathway and field genuinely
- Use "[Name des Unternehmens]" placeholder for the employer name
  since no specific employer is known at draft time
- Maximum 350 words
- "Mit freundlichen Grüßen," closing

RESPOND ONLY WITH VALID JSON:
{
  "cv": {
    "profil": "<3-4 sentence summary, no fabricated specifics>",
    "ausbildung": [{"zeitraum": "[Zeitraum]", "beschreibung": "<real education level/field + bracketed institution placeholder>"}],
    "berufserfahrung": [{"zeitraum": "[Zeitraum]", "beschreibung": "<generic relevant description, employer as [Arbeitgeber], [Ort]>"}],
    "sprachkenntnisse": [{"sprache": "<language>", "niveau": "<REAL CEFR level from profile>"}],
    "kompetenzen": ["<generic skill 1>", "<generic skill 2>", "<generic skill 3>"]
  },
  "anschreiben": "<cover letter with [Name des Unternehmens] placeholder for employer>"
}"""


def generate_documents(
    student_data: dict,
    *,
    diagnostic_id: str | None = None,
    student_id: str | None = None,
) -> dict:
    user_message = f"""Generate German CV and cover letter for:

Name: {student_data['name']}
Pathway: {student_data['pathway']}
Education: {student_data['education_level']} in {student_data.get('field_of_study', 'General Studies')}
Work experience: {student_data['work_experience_years']} years
German level: {student_data['german_level']}
English level: {student_data.get('english_level', 'Not specified')}
Country: {student_data['country']}

Return the JSON structure specified."""

    # Document generation: Sonnet for long-form structured JSON requiring German writing quality
    doc_start = time.perf_counter()
    response = client.messages.create(
        model=AI_MODEL,
        max_tokens=2500,
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
