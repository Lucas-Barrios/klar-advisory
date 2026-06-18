"""
Pydantic output schemas for AI agent responses.

These validate the parsed JSON from each agent immediately after json.loads(),
before any downstream code indexes into the result. Validation failures raise
the agent's typed exception class rather than letting KeyError/TypeError
propagate as an unhandled 500.
"""
from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# UC-01 — Germany Readiness Diagnostic
# ---------------------------------------------------------------------------

class RoadmapStep(BaseModel):
    month: int = Field(ge=1)
    title: str
    description: str
    action_items: list[str] = Field(default_factory=list)


class DiagnosticRecommendation(BaseModel):
    name: str
    type: str
    description: str
    url: Optional[str] = None


class DiagnosticAIOutput(BaseModel):
    overall_score: int = Field(ge=0, le=100)
    language_score: int = Field(ge=0, le=100)
    education_score: int = Field(ge=0, le=100)
    pathway_fit_score: int = Field(ge=0, le=100)
    timeline_score: int = Field(ge=0, le=100)
    financial_score: int = Field(ge=0, le=100)
    documentation_score: int = Field(ge=0, le=100)
    summary: str
    next_step_message: str = Field(default="")
    roadmap: list[RoadmapStep]
    recommendations: list[DiagnosticRecommendation]

    model_config = {"extra": "ignore"}


# ---------------------------------------------------------------------------
# UC-02 — Ausbildung Position Matching
# ---------------------------------------------------------------------------

class MatchItem(BaseModel):
    refnr: str
    fit_explanation: str
    estimated_german_level_needed: str
    german_level_concern: Any = False
    urgency_note: str = ""

    model_config = {"extra": "ignore"}


class MatchAIOutput(BaseModel):
    matches: list[MatchItem]
    overall_summary: str

    model_config = {"extra": "ignore"}


# ---------------------------------------------------------------------------
# UC-04 — Document Factory
# ---------------------------------------------------------------------------

class CVEntry(BaseModel):
    zeitraum: str
    beschreibung: str

    model_config = {"extra": "ignore"}


class SprachkenntnisEntry(BaseModel):
    sprache: str
    niveau: str

    model_config = {"extra": "ignore"}


class CVOutput(BaseModel):
    profil: str
    ausbildung: list[CVEntry]
    berufserfahrung: list[dict[str, Any]]
    sprachkenntnisse: list[SprachkenntnisEntry]
    kompetenzen: list[str]

    model_config = {"extra": "ignore"}


class DocumentAIOutput(BaseModel):
    cv: CVOutput
    anschreiben: str

    model_config = {"extra": "ignore"}
