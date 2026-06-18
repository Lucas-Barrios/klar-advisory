"""
Pydantic output schemas for AI agent responses.

These validate the parsed JSON from each agent immediately after json.loads(),
before any downstream code indexes into the result. Validation failures raise
the agent's typed exception class rather than letting KeyError/TypeError
propagate as an unhandled 500.
"""
from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field, model_validator


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
    # cv / anschreiben are the backward-compat aliases (always point to the DE versions).
    # New four-field bilingual format: cv_de / anschreiben_de / cv_target / anschreiben_target.
    # The model_validator below normalises both old and new formats transparently.
    cv: CVOutput
    anschreiben: str
    cv_de: Optional[CVOutput] = None
    anschreiben_de: Optional[str] = None
    cv_target: Optional[CVOutput] = None
    anschreiben_target: Optional[str] = None

    model_config = {"extra": "ignore"}

    @model_validator(mode="before")
    @classmethod
    def _normalise_bilingual(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        # New format → populate legacy aliases
        if "cv_de" in data and "cv" not in data:
            data["cv"] = data["cv_de"]
        if "anschreiben_de" in data and "anschreiben" not in data:
            data["anschreiben"] = data["anschreiben_de"]
        # Old format → populate new keys so callers can always read cv_de / anschreiben_de
        if "cv" in data and "cv_de" not in data:
            data["cv_de"] = data["cv"]
        if "anschreiben" in data and "anschreiben_de" not in data:
            data["anschreiben_de"] = data["anschreiben"]
        return data
