from pydantic import BaseModel, Field, field_validator
from typing import Any, Literal, Optional

Pathway = Literal["university", "ausbildung", "work_visa"]
GermanLevel = Literal["none", "A1", "A2", "B1", "B2", "C1", "C2"]
Timeline = Literal["6_months", "1_year", "2_years_plus"]
DiagnosticStatus = Literal["pending", "approved", "rejected"]
ReviewStatus = Literal["approved", "rejected"]
EvaluationRunStatus = Literal["running", "completed", "failed"]
EvaluationExperimentStatus = Literal["draft", "running", "completed", "failed"]
EvaluationComparisonType = Literal["auto", "continuous", "binary", "ordinal"]
EvaluationCorrectionMethod = Literal["none", "bonferroni", "benjamini_hochberg"]

class StudentProfileInput(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=254)
    country: str = Field(min_length=1, max_length=80)
    age: Optional[int] = Field(default=None, ge=16, le=80)
    pathway: Pathway
    german_level: GermanLevel
    english_level: Optional[str] = Field(default=None, max_length=40)
    education_level: str = Field(min_length=1, max_length=120)
    field_of_study: Optional[str] = Field(default=None, max_length=120)
    work_experience_years: int = Field(default=0, ge=0, le=60)
    timeline: Timeline
    financial_situation: Optional[str] = Field(default=None, max_length=1000)
    current_location: Optional[str] = Field(default=None, max_length=120)
    additional_info: Optional[str] = Field(default=None, max_length=1500)

    @field_validator(
        "name",
        "email",
        "country",
        "english_level",
        "education_level",
        "field_of_study",
        "financial_situation",
        "current_location",
        "additional_info",
        mode="before",
    )
    @classmethod
    def strip_text(cls, value):
        if isinstance(value, str):
            value = value.strip()
        return value

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        if "@" not in value or value.startswith("@") or value.endswith("@"):
            raise ValueError("email must be a valid email address")
        return value

class DiagnosticResponse(BaseModel):
    diagnostic_id: str
    status: DiagnosticStatus
    message: str
    progress_token: Optional[str] = None

class ReviewAction(BaseModel):
    status: ReviewStatus
    reviewer_notes: Optional[str] = Field(default=None, max_length=2000)
    reviewer_decision: Optional[str] = Field(default=None, max_length=120)
    reviewer_correction_notes: Optional[str] = Field(default=None, max_length=2000)
    reviewer_confidence: Optional[int] = Field(default=None, ge=1, le=5)
    rejection_reason: Optional[str] = Field(default=None, max_length=1000)
    review_duration_seconds: Optional[int] = Field(default=None, ge=0, le=86400)


class EvaluationDatasetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    version: str = Field(min_length=1, max_length=80)
    use_case: str = Field(min_length=1, max_length=120)
    description: Optional[str] = Field(default=None, max_length=2000)
    active: bool = True


class EvaluationExampleCreate(BaseModel):
    dataset_id: str
    input_payload: dict[str, Any] = Field(default_factory=dict)
    expected_pathway: Optional[Pathway] = None
    expected_german_level: Optional[GermanLevel] = None
    expected_timeline: Optional[Timeline] = None
    expected_flags: list[str] = Field(default_factory=list, max_length=50)
    expected_summary_notes: Optional[str] = Field(default=None, max_length=3000)
    source: Optional[str] = Field(default="manual", max_length=200)
    reviewed_by_human: bool = False


class EvaluationExampleFromDiagnosticCreate(BaseModel):
    dataset_id: str
    expected_flags: Optional[list[str]] = Field(default=None, max_length=50)
    expected_summary_notes: Optional[str] = Field(default=None, max_length=3000)


class EvaluationRunCreate(BaseModel):
    dataset_id: str
    model: Optional[str] = Field(default=None, max_length=120)
    prompt_version: Optional[str] = Field(default=None, max_length=120)
    rubric_version: Optional[str] = Field(default=None, max_length=120)
    run_type: str = Field(default="manual", max_length=80)
    status: EvaluationRunStatus = "running"


class EvaluationResultCreate(BaseModel):
    example_id: str
    diagnostic_id: Optional[str] = None
    predicted_pathway: Optional[Pathway] = None
    predicted_german_level: Optional[GermanLevel] = None
    predicted_timeline: Optional[Timeline] = None
    predicted_flags: list[str] = Field(default_factory=list, max_length=50)
    score: Optional[float] = Field(default=None, ge=0, le=1)
    passed: Optional[bool] = None
    error_type: Optional[str] = Field(default=None, max_length=120)
    latency_ms: int = Field(default=0, ge=0)
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    estimated_cost: float = Field(default=0, ge=0)
    notes: Optional[str] = Field(default=None, max_length=2000)


class EvaluationExperimentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    description: Optional[str] = Field(default=None, max_length=2000)
    dataset_id: str
    baseline_run_id: str
    challenger_run_id: str
    comparison_type: EvaluationComparisonType = "auto"
    metric_name: str = Field(default="score", min_length=1, max_length=120)
    minimum_practical_effect: float = Field(default=0.02, ge=0)
    alpha: float = Field(default=0.05, gt=0, lt=1)
    correction_method: EvaluationCorrectionMethod = "none"
    status: EvaluationExperimentStatus = "draft"


class EvaluationExperimentCompareRequest(BaseModel):
    metric_name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    comparison_type: Optional[EvaluationComparisonType] = None
    minimum_practical_effect: Optional[float] = Field(default=None, ge=0)
    alpha: Optional[float] = Field(default=None, gt=0, lt=1)
    correction_method: Optional[EvaluationCorrectionMethod] = None
