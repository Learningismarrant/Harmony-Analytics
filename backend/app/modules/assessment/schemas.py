# app/modules/assessment/schemas.py
from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


# ── Catalogue ──────────────────────────────────────────────

class TestInfoOut(BaseModel):
    id: int
    name: str
    description: str
    instructions: Optional[str] = None
    max_score_per_question: int = 5
    test_type: str
    model_config = ConfigDict(from_attributes=True)


class QuestionOut(BaseModel):
    id: int
    test_id: int
    text: str
    question_type: str
    options: Optional[List[Any]] = None
    trait: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


# ── Soumission ─────────────────────────────────────────────

class ResponseIn(BaseModel):
    question_id: int = Field(..., gt=0)
    valeur_choisie: str = Field(..., min_length=1, max_length=50)
    seconds_spent: Optional[float] = Field(default=None, ge=0.0, le=3600.0)


class SubmitTestIn(BaseModel):
    test_id: int = Field(..., gt=0)
    responses: List[ResponseIn] = Field(..., min_length=1, max_length=200)


# ── Résultat ───────────────────────────────────────────────

class TraitScoreOut(BaseModel):
    score: float
    niveau: str                     # "Faible" | "Moyen" | "Élevé"
    percentile: Optional[float] = None


class ReliabilityOut(BaseModel):
    is_reliable: bool
    reasons: List[str] = []
    social_desirability_flag: bool = False


class TestResultOut(BaseModel):
    id: int
    test_id: int
    crew_profile_id: int
    test_name: str
    global_score: float
    scores: Dict[str, Any]          # {traits, reliability, meta}
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


