# app/modules/survey/schemas.py
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime
from app.shared.enums import SurveyTriggerType, DepartureReason


# ── Déclenchement ──────────────────────────────────────────

class SurveyTriggerIn(BaseModel):
    trigger_type: SurveyTriggerType
    target_crew_profile_ids: List[int] = Field(..., min_length=1)
    # Si exit_interview, on renseigne le marin qui part
    exit_crew_profile_id: Optional[int] = None


class SurveyOut(BaseModel):
    id: int
    yacht_id: int
    trigger_type: str
    target_crew_ids: List[int]
    is_open: bool
    created_at: datetime
    closed_at: Optional[datetime] = None
    response_count: int = 0
    model_config = ConfigDict(from_attributes=True)


# ── Réponse ────────────────────────────────────────────────

class SurveyResponseIn(BaseModel):
    """
    Échelle 1-10 côté front — normalisée 0-100 dans le service.
    intent_to_stay est inversé : 1 = "je pars" → score 0, 10 = "je reste" → score 100.
    """
    team_cohesion:      Optional[float] = Field(None, ge=1, le=10)
    workload_felt:      Optional[float] = Field(None, ge=1, le=10)
    leadership_fit:     Optional[float] = Field(None, ge=1, le=10)
    self_performance:   Optional[float] = Field(None, ge=1, le=10)
    intent_to_stay:     float = Field(..., ge=1, le=10)
    free_text:          Optional[str] = Field(None, max_length=1000)

    # Champs exit interview uniquement
    departure_reason:  Optional[DepartureReason] = None
    actual_tenure_days: Optional[int] = Field(None, ge=0)


class SurveyResponseOut(BaseModel):
    id: int
    survey_id: int
    trigger_type: str
    intent_to_stay: float
    submitted_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ── Résultats agrégés (pour le cap/owner) ─────────────────

class SurveyAggregatedOut(BaseModel):
    """
    Résultats agrégés et anonymisés.
    Jamais de données individuelles exposées.
    """
    survey_id: int
    trigger_type: str
    response_count: int
    avg_team_cohesion: Optional[float] = None
    avg_workload_felt: Optional[float] = None
    avg_leadership_fit: Optional[float] = None
    avg_intent_to_stay: Optional[float] = None
    predicted_vs_observed: Optional[dict] = None   # {f_team: {predicted, observed, delta}}