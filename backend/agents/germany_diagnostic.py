import json
import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
client = Anthropic()

SYSTEM_PROMPT = """You are Klar's Germany Readiness Diagnostic Agent.
You assess Latin American students and professionals who want to study or work in Germany.

Your job:
1. Score across 6 dimensions (0-100 each)
2. Calculate an overall readiness score
3. Write an honest 2-3 sentence summary
4. Create a realistic month-by-month roadmap
5. Recommend 3 specific programs or resources

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

Be honest. Be warm. This is career-changing advice.
RESPOND ONLY WITH VALID JSON. No markdown, no text outside the JSON."""


def run_diagnostic(student_data: dict) -> dict:
    user_message = f"""Assess this student's Germany readiness:

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

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}]
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    result = json.loads(raw)
    result["raw_output"] = response.content[0].text
    return result