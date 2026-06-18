"""
LangSmith evaluator functions for Klar's diagnostic agent.

Wire these into a LangSmith evaluation run via langsmith.evaluate():

    from langsmith import evaluate
    from services.langsmith_evaluators import recommendation_relevance

    results = evaluate(
        target_fn,
        data="klar-uc01-diagnostic",
        evaluators=[recommendation_relevance],
    )

The judge uses Claude Haiku to keep evaluation costs low.  It is intentionally
wrapped with wrap_anthropic so judge calls also appear in LangSmith traces.
"""
from __future__ import annotations

import json
import os

import anthropic
from langsmith.evaluation import EvaluationResult
from langsmith.schemas import Example, Run
from langsmith.wrappers import wrap_anthropic

JUDGE_MODEL = os.getenv("LANGSMITH_JUDGE_MODEL", "claude-haiku-4-5-20251001")

_RUBRIC = """\
You are an impartial evaluator assessing how relevant the 3 recommendations are
for a specific student profile.

Scoring rubric (1–5):
  1 — Completely irrelevant; recommendations have no connection to the student's pathway,
      German level, or situation.
  2 — Vaguely related; recommendations are real but barely address the student's gaps.
  3 — Relevant but generic; any similar student could receive the same recommendations
      without personalisation.
  4 — Clearly relevant; recommendations directly address the student's pathway, German
      level, and key preparation gaps.
  5 — Highly specific and actionable; each recommendation is well-matched to this exact
      profile and addresses the most important next steps.

Student profile:
{profile}

Recommendations provided:
{recommendations}

Respond with ONLY valid JSON — no markdown, no extra text:
{{"score": <integer 1-5>, "rationale": "<one or two sentences explaining the score>"}}"""


def recommendation_relevance(run: Run, example: Example) -> EvaluationResult:
    """LangSmith evaluator: score recommendation relevance 1-5 via Claude Haiku."""
    outputs = run.outputs or {}
    recommendations = outputs.get("recommendations") or []
    profile = (example.inputs or {}) if example else {}

    if not recommendations:
        return EvaluationResult(
            key="recommendation_relevance",
            score=0.0,
            comment="No recommendations present in run output.",
        )

    judge_client = wrap_anthropic(anthropic.Anthropic())

    prompt = _RUBRIC.format(
        profile=json.dumps(profile, indent=2, ensure_ascii=False),
        recommendations=json.dumps(recommendations, indent=2, ensure_ascii=False),
    )

    response = judge_client.messages.create(
        model=JUDGE_MODEL,
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        parsed = json.loads(raw)
        raw_score = int(parsed["score"])
        rationale = str(parsed.get("rationale", ""))
    except (json.JSONDecodeError, KeyError, ValueError):
        return EvaluationResult(
            key="recommendation_relevance",
            score=None,
            comment=f"Judge returned unparseable response: {raw[:200]}",
        )

    # Clamp to valid range and normalise to [0, 1] for LangSmith
    clamped = max(1, min(5, raw_score))
    normalised = round((clamped - 1) / 4, 4)  # 1→0.0, 3→0.5, 5→1.0

    return EvaluationResult(
        key="recommendation_relevance",
        score=normalised,
        comment=f"Raw score {clamped}/5 — {rationale}",
    )
