# app/modules/recruitment/schemas.py
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.shared.enums import CampaignStatus, ApplicationStatus


# ── Campagne ───────────────────────────────────────────────

class CampaignCreateIn(BaseModel):
    title: str = Field(..., min_length=5, max_length=100)
    position: str
    description: Optional[str] = Field(None, max_length=500)
    yacht_id: int = Field(..., gt=0)

    @field_validator("title")
    @classmethod
    def strip_title(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Le titre ne peut pas être vide.")
        return v


class CampaignUpdateIn(BaseModel):
    title: Optional[str] = Field(None, min_length=5, max_length=100)
    position: Optional[str] = None
    description: Optional[str] = Field(None, max_length=500)
    yacht_id: Optional[int] = Field(None, gt=0)
    status: Optional[CampaignStatus] = None


class CampaignOut(BaseModel):
    id: int
    title: str
    position: str
    description: Optional[str] = None
    status: CampaignStatus
    yacht_id: Optional[int] = None
    yacht_name: Optional[str] = None
    invite_token: str
    is_archived: bool = False
    candidate_count: int = 0
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class CampaignPublicOut(BaseModel):
    """Vue publique — accessible via token d'invitation sans auth."""
    id: int
    title: str
    position: str
    description: Optional[str] = None
    yacht_name: Optional[str] = None
    status: CampaignStatus


# ── Matching ───────────────────────────────────────────────

class CategoryScoreOut(BaseModel):
    normative_score: float
    relative_percentile: Optional[float] = None
    feedback: str


class MatchResultOut(BaseModel):
    """
    Résultat de matching fusionné :
    - global_fit : score SME normative (engine/matching/sme.py)
    - y_success  : équation maîtresse Ŷ (engine/recruitment/master.py)
    - f_team_delta : impact sur l'équipe (engine/recruitment/simulator.py)
    """
    crew_profile_id: int
    name: str
    avatar_url: Optional[str] = None
    location: Optional[str] = None
    experience_years: int = 0
    test_status: str            # "completed" | "pending"

    global_fit: float
    categories: Optional[Dict[str, CategoryScoreOut]] = None

    y_success: Optional[float] = None
    f_team_delta: Optional[float] = None
    impact_flags: List[str] = []
    confidence: Optional[str] = None   # "HIGH" | "MEDIUM" | "LOW"

    is_hired: bool = False
    is_rejected: bool = False
    application_status: Optional[str] = None
    rejected_reason: Optional[str] = None
    joined_at: Optional[Any] = None


class RecruitmentImpactOut(BaseModel):
    """Rapport What-If détaillé pour un candidat spécifique."""
    y_success_predicted: float
    p_ind: float
    f_team: float
    f_env: float
    f_lmx: float
    f_team_delta: float
    jerk_filter_delta: float
    faultline_risk_delta: float
    emotional_buffer_delta: float
    performance_delta: float
    flags: List[str] = []
    data_completeness: float
    confidence_label: str


class CampaignStatsOut(BaseModel):
    total_candidates: int
    hired_count: int
    rejected_count: int
    pending_count: int
    matching_distribution: Dict[str, int] = {}


# ── Décisions candidats ────────────────────────────────────

class CandidateDecisionIn(BaseModel):
    rejected_reason: Optional[str] = Field(None, max_length=200)


class BulkRejectIn(BaseModel):
    crew_profile_ids: List[int] = Field(..., min_length=1)
    reason: str = Field(..., min_length=1, max_length=200)


class CandidateDecisionOut(BaseModel):
    id: int
    campaign_id: int
    crew_profile_id: int
    status: ApplicationStatus
    is_hired: bool
    is_rejected: bool
    rejected_reason: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


# ── Vue côté candidat ──────────────────────────────────────

class MyApplicationOut(BaseModel):
    campaign_id: int
    campaign_title: str
    campaign_description: Optional[str] = None
    position: str
    yacht_name: Optional[str] = None
    campaign_status: str
    application_status: str
    is_hired: bool
    is_rejected: bool
    rejected_reason: Optional[str] = None
    joined_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    is_archived: bool