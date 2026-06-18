import json
import logging
import time
from typing import Any

from anthropic import Anthropic
from database import get_supabase
from services.ai_observability import (
    AI_MODEL,
    AI_MODEL_HAIKU,
    AI_PROVIDER,
    REQUEST_TYPE_AUSBILDUNG_MATCH,
    REQUEST_TYPE_AUSBILDUNG_SECTOR,
    build_usage_event,
    extract_usage_tokens,
    persist_usage_event,
)

logger = logging.getLogger(__name__)
client = Anthropic(max_retries=2)


class MatchingAIError(RuntimeError):
    def __init__(self, message: str, *, error_type: str | None = None):
        super().__init__(message)
        self.error_type = error_type

MATCH_PROMPT = """You are Klar's Ausbildung Position Matcher.

You receive a student profile and a list of real, currently open German apprenticeship
(Ausbildung) positions from the Bundesagentur für Arbeit (Germany's Federal Employment Agency).

IMPORTANT — these positions do NOT include German language requirements in their data.
You must ESTIMATE the realistic German level needed based on the occupation type:
- Patient-facing healthcare roles (Pflege, medizinisch): B2 minimum
- Technical/manual trades (Mechatroniker, Elektroniker): B1 typically sufficient
- Office/IT roles: B1-B2 depending on client contact
- Hospitality/kitchen: A2-B1 for back-of-house, B1-B2 for guest-facing

Select the TOP 3 positions that best fit this student's profile, considering:
field of study relevance, German level vs. estimated requirement, location
reasonableness, and start date vs. their timeline.

For each selected position, explain in 2-3 sentences why it fits, and flag clearly
if their German level appears insufficient.

RESPOND ONLY WITH VALID JSON in this structure:
{
  "matches": [
    {
      "refnr": "<the refnr from the input>",
      "fit_explanation": "<2-3 sentences>",
      "estimated_german_level_needed": "<A2|B1|B2|C1>",
      "german_level_concern": "<true|false>",
      "urgency_note": "<comment on start date timing>"
    }
  ],
  "overall_summary": "<2-3 sentence summary of the match quality and any general advice>"
}"""


def match_positions(
    student_profile: dict,
    *,
    diagnostic_id: str | None = None,
    student_id: str | None = None,
) -> dict:
    supabase = get_supabase()

    sector_prompt = (
        f'Given this field of study: "{student_profile.get("field_of_study", "unspecified")}"\n'
        "Map it to ONE of these German Ausbildung sectors: nursing, mechatronics, it, hospitality, gastronomy\n"
        "Respond with ONLY the single best matching sector name, nothing else."
    )

    # Sector classification: Haiku is sufficient for this simple 5-way routing task (max_tokens=20)
    sector_start = time.perf_counter()
    try:
        sector_response = client.messages.create(
            model=AI_MODEL_HAIKU,
            max_tokens=20,
            messages=[{"role": "user", "content": sector_prompt}],
        )
    except Exception as exc:
        raise MatchingAIError(
            "Sector classification call failed.",
            error_type=type(exc).__name__,
        ) from exc
    sector_latency_ms = int((time.perf_counter() - sector_start) * 1000)
    sector_in, sector_out = extract_usage_tokens(sector_response)
    sector_usage = build_usage_event(
        provider=AI_PROVIDER,
        model=AI_MODEL_HAIKU,
        request_type=REQUEST_TYPE_AUSBILDUNG_SECTOR,
        diagnostic_id=diagnostic_id,
        student_id=student_id,
        input_tokens=sector_in,
        output_tokens=sector_out,
        latency_ms=sector_latency_ms,
        success=True,
    )
    persist_usage_event(supabase, sector_usage)
    sector = sector_response.content[0].text.strip().lower()

    candidates = (
        supabase.table("ausbildung_positions")
        .select("*")
        .eq("sector_keyword", sector)
        .limit(15)
        .execute()
    )

    if not candidates.data:
        return {
            "matches": [],
            "overall_summary": "No current positions found in this sector.",
            "_ai_usage": sector_usage,
        }

    candidate_list = json.dumps(candidates.data, indent=2, default=str)

    user_message = (
        f"Student profile:\n"
        f"Field of study: {student_profile.get('field_of_study')}\n"
        f"German level: {student_profile.get('german_level')}\n"
        f"Timeline: {student_profile.get('timeline')}\n"
        f"Current location: {student_profile.get('current_location')}\n\n"
        f"Available positions in this sector:\n{candidate_list}\n\n"
        "Select and explain the top 3 matches per the instructions."
    )

    # Position ranking: Sonnet for multi-criteria reasoning across a JSON position payload
    rank_start = time.perf_counter()
    response = client.messages.create(
        model=AI_MODEL,
        max_tokens=2000,
        system=MATCH_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )
    rank_latency_ms = int((time.perf_counter() - rank_start) * 1000)
    rank_in, rank_out = extract_usage_tokens(response)
    rank_usage = build_usage_event(
        provider=AI_PROVIDER,
        model=AI_MODEL,
        request_type=REQUEST_TYPE_AUSBILDUNG_MATCH,
        diagnostic_id=diagnostic_id,
        student_id=student_id,
        input_tokens=rank_in,
        output_tokens=rank_out,
        latency_ms=rank_latency_ms,
        success=True,
    )
    persist_usage_event(supabase, rank_usage)

    from pydantic import ValidationError
    from models.ai_outputs import MatchAIOutput

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    try:
        parsed = json.loads(raw.strip())
    except json.JSONDecodeError as exc:
        raise MatchingAIError(
            "Matching response was not valid JSON.",
            error_type="JSONDecodeError",
        ) from exc

    try:
        validated = MatchAIOutput.model_validate(parsed)
    except ValidationError as exc:
        raise MatchingAIError(
            "Matching response failed schema validation.",
            error_type="SchemaValidationError",
        ) from exc

    result = validated.model_dump()

    position_lookup = {p["refnr"]: p for p in candidates.data}
    for match in result.get("matches", []):
        refnr = match.get("refnr")
        if not refnr:
            logger.warning("match item missing refnr, skipping position lookup")
            continue
        full = position_lookup.get(refnr, {})
        match.update(
            {
                "titel": full.get("titel"),
                "arbeitgeber": full.get("arbeitgeber"),
                "ort": full.get("ort"),
                "eintrittsdatum": full.get("eintrittsdatum"),
                "application_url": full.get("application_url"),
            }
        )

    result["_ai_usage"] = rank_usage
    return result
