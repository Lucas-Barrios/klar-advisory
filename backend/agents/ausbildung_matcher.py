import json
from anthropic import Anthropic
from database import get_supabase

client = Anthropic()

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


def match_positions(student_profile: dict) -> dict:
    supabase = get_supabase()

    sector_prompt = (
        f'Given this field of study: "{student_profile.get("field_of_study", "unspecified")}"\n'
        "Map it to ONE of these German Ausbildung sectors: nursing, mechatronics, it, hospitality, gastronomy\n"
        "Respond with ONLY the single best matching sector name, nothing else."
    )

    sector_response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=20,
        messages=[{"role": "user", "content": sector_prompt}],
    )
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

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        system=MATCH_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    result = json.loads(raw.strip())

    position_lookup = {p["refnr"]: p for p in candidates.data}
    for match in result.get("matches", []):
        full = position_lookup.get(match["refnr"], {})
        match.update(
            {
                "titel": full.get("titel"),
                "arbeitgeber": full.get("arbeitgeber"),
                "ort": full.get("ort"),
                "eintrittsdatum": full.get("eintrittsdatum"),
                "application_url": full.get("application_url"),
            }
        )

    return result
