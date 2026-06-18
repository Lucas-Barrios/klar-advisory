import json
import os
import time
from typing import Any

from anthropic import Anthropic
from dotenv import load_dotenv
from services.ai_observability import (
    AI_MODEL,
    AI_PROVIDER,
    REQUEST_TYPE_GERMANY_DIAGNOSTIC,
    build_usage_event,
    estimate_tokens_from_text,
    extract_usage_tokens,
    safe_error_type,
)

load_dotenv()
client: Anthropic | None = None

SYSTEM_PROMPT = """You are Klar's Germany Readiness Diagnostic Agent.
You assess Latin American students and professionals who want to study or work in Germany.

Your job:
1. Score across 6 dimensions (0-100 each)
2. Calculate an overall readiness score
3. Write an honest 2-3 sentence summary
4. Create a realistic month-by-month roadmap
5. Recommend 3 specific programs or resources
6. Write a personalized next-step message

SCORING DIMENSIONS:
- language_score: none=10, A1=20, A2=35, B1=55, B2=75, C1=90, C2=100
  Ausbildung needs B1 minimum. University needs B2. Work Visa varies.
- education_score: degree level, field relevance, recognition likelihood
- pathway_fit_score: how well background fits chosen pathway
- timeline_score: 6_months=tight(20-40), 1_year=realistic(50-70), 2_years_plus=ideal(70-90)
- financial_score: university needs ~11,000 EUR blocked account. Ausbildung pays 700-1,200 EUR/month.
- documentation_score: EU=easy, LATAM with degree=moderate, LATAM without=complex

OVERALL SCORE: Language 25% + Education 20% + Pathway Fit 20% + Timeline 15% + Financial 10% + Documentation 10%

SCORE MEANING: Below 40=not ready. 40-60=getting there. 60-80=ready with preparation. 80+=strong candidate.

ROADMAP: 6_months=6 steps, 1_year=8 steps, 2_years_plus=12 steps

NEXT_STEP_MESSAGE: A warm, personalized 2-3 sentence message encouraging the student to book a free consultation.
Calibrate urgency to their overall score:
- Below 50: emphasize that expert guidance saves significant time and money by avoiding costly early mistakes.
- 50-75: emphasize how a consultation helps avoid the most common mistakes that derail candidates at this stage.
- 75+: emphasize acting now given how competitive spots are and how close they already are to being ready.
Address the student by first name. Be specific to their pathway and situation.

Be honest. Be warm. This is career-changing advice.
RESPOND ONLY WITH VALID JSON. No markdown, no text outside the JSON."""


class DiagnosticAIError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        usage_event: dict[str, Any] | None = None,
        error_type: str | None = None,
    ):
        super().__init__(message)
        self.usage_event = usage_event
        self.error_type = error_type


def get_env_int(name: str, default: int, *, minimum: int, maximum: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError:
        value = default
    return min(max(value, minimum), maximum)


def get_env_float(name: str, default: float, *, minimum: float, maximum: float) -> float:
    try:
        value = float(os.getenv(name, str(default)))
    except ValueError:
        value = default
    return min(max(value, minimum), maximum)


def get_anthropic_client() -> Anthropic:
    global client
    if client is None:
        client = Anthropic(max_retries=2)
    return client


def build_user_message(student_data: dict) -> str:
    return f"""Assess this student's Germany readiness:

Name: {student_data['name']}
Country: {student_data['country']}
Age: {student_data.get('age', 'Not provided')}
Target Pathway: {student_data['pathway']}
German Level: {student_data['german_level']}
English Level: {student_data.get('english_level', 'Not provided')}
Education Level: {student_data['education_level']}
Field of Study: {student_data.get('field_of_study', 'Not provided')}
Work Experience: {student_data['work_experience_years']} years
Timeline: {student_data['timeline']}
Financial Situation: {student_data.get('financial_situation', 'Not provided')}
Current Location: {student_data.get('current_location', 'Not provided')}

Return exactly this JSON structure:
{{
  "overall_score": <0-100>,
  "language_score": <0-100>,
  "education_score": <0-100>,
  "pathway_fit_score": <0-100>,
  "timeline_score": <0-100>,
  "financial_score": <0-100>,
  "documentation_score": <0-100>,
  "summary": "<2-3 honest sentences>",
  "next_step_message": "<personalized 2-3 sentence message encouraging the student to book a consultation, urgency calibrated to score>",
  "roadmap": [
    {{
      "month": 1,
      "title": "<step title>",
      "description": "<what to do and why>",
      "action_items": ["<action>", "<action>"]
    }}
  ],
  "recommendations": [
    {{
      "name": "<program or resource name>",
      "type": "<program|course|organization>",
      "description": "<why relevant for this student>",
      "url": "<url or null>"
    }}
  ]
}}"""


def parse_diagnostic_response(response: Any) -> dict:
    from pydantic import ValidationError
    from models.ai_outputs import DiagnosticAIOutput

    raw_text = response.content[0].text
    raw = raw_text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        raise DiagnosticAIError(
            "AI response was not valid JSON.",
            error_type="JSONDecodeError",
        ) from e

    try:
        validated = DiagnosticAIOutput.model_validate(parsed)
    except ValidationError as e:
        raise DiagnosticAIError(
            "AI response failed schema validation.",
            error_type="SchemaValidationError",
        ) from e

    result = validated.model_dump()
    result["raw_output"] = raw_text
    return result


def run_diagnostic(
    student_data: dict,
    *,
    anthropic_client: Any | None = None,
    model: str | None = None,
    max_output_tokens: int | None = None,
    timeout_seconds: float | None = None,
    max_input_chars: int | None = None,
) -> dict:
    selected_model = model or AI_MODEL
    max_tokens = max_output_tokens or get_env_int(
        "ANTHROPIC_MAX_OUTPUT_TOKENS",
        4000,
        minimum=256,
        maximum=8000,
    )
    timeout = timeout_seconds or get_env_float(
        "ANTHROPIC_TIMEOUT_SECONDS",
        45.0,
        minimum=5.0,
        maximum=120.0,
    )
    input_limit = max_input_chars or get_env_int(
        "DIAGNOSTIC_MAX_INPUT_CHARS",
        8000,
        minimum=1000,
        maximum=20000,
    )
    user_message = build_user_message(student_data)
    estimated_input_tokens = estimate_tokens_from_text(SYSTEM_PROMPT + user_message)

    if len(user_message) > input_limit:
        usage_event = build_usage_event(
            provider=AI_PROVIDER,
            model=selected_model,
            request_type=REQUEST_TYPE_GERMANY_DIAGNOSTIC,
            diagnostic_id=None,
            student_id=None,
            input_tokens=estimated_input_tokens,
            output_tokens=0,
            latency_ms=0,
            success=False,
            error_type="InputTooLong",
        )
        raise DiagnosticAIError(
            "Diagnostic input is too long.",
            usage_event=usage_event,
            error_type="InputTooLong",
        )

    active_client = anthropic_client or get_anthropic_client()
    input_tokens = estimated_input_tokens
    output_tokens = 0
    start = time.perf_counter()
    try:
        response = active_client.messages.create(
            model=selected_model,
            max_tokens=max_tokens,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
            timeout=timeout,
        )
        latency_ms = int((time.perf_counter() - start) * 1000)
        input_tokens, output_tokens = extract_usage_tokens(response)
        if input_tokens == 0:
            input_tokens = estimated_input_tokens

        result = parse_diagnostic_response(response)
        result["_ai_usage"] = build_usage_event(
            provider=AI_PROVIDER,
            model=selected_model,
            request_type=REQUEST_TYPE_GERMANY_DIAGNOSTIC,
            diagnostic_id=None,
            student_id=None,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            success=True,
        )
        return result
    except DiagnosticAIError:
        raise
    except Exception as exc:
        latency_ms = int((time.perf_counter() - start) * 1000)
        error_type = safe_error_type(exc) or "AIError"
        usage_event = build_usage_event(
            provider=AI_PROVIDER,
            model=selected_model,
            request_type=REQUEST_TYPE_GERMANY_DIAGNOSTIC,
            diagnostic_id=None,
            student_id=None,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            success=False,
            error_type=error_type,
        )
        raise DiagnosticAIError(
            "Diagnostic AI request failed.",
            usage_event=usage_event,
            error_type=error_type,
        ) from exc
