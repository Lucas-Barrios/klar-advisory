from pydantic import BaseModel
from typing import Optional, List

class StudentProfileInput(BaseModel):
    name: str
    email: str
    country: str
    age: Optional[int] = None
    pathway: str        # 'university' | 'ausbildung' | 'work_visa'
    german_level: str   # 'none' | 'A1' | 'A2' | 'B1' | 'B2' | 'C1' | 'C2'
    english_level: Optional[str] = None
    education_level: str
    field_of_study: Optional[str] = None
    work_experience_years: int = 0
    timeline: str       # '6_months' | '1_year' | '2_years_plus'
    financial_situation: Optional[str] = None
    current_location: Optional[str] = None
    additional_info: Optional[str] = None

class DiagnosticResponse(BaseModel):
    diagnostic_id: str
    status: str
    message: str

class ReviewAction(BaseModel):
    status: str  # 'approved' | 'rejected'
    reviewer_notes: Optional[str] = None