# app/modules/crew/schemas.py
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime
from app.shared.enums import YachtPosition


# ── Assignments ────────────────────────────────────────────

class CrewAssignIn(BaseModel):
    crew_profile_id: int
    role: YachtPosition
    start_date: Optional[datetime] = None


class CrewMemberOut(BaseModel):
    id: int
    crew_profile_id: int
    role: YachtPosition
    is_active: bool
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    is_harmony_verified: bool = False
    model_config = ConfigDict(from_attributes=True)


# ── Daily Pulse ────────────────────────────────────────────

class DailyPulseIn(BaseModel):
    score: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None


class DailyPulseOut(BaseModel):
    id: int
    score: int
    comment: Optional[str] = None
    created_at: datetime
    yacht_id: int
    model_config = ConfigDict(from_attributes=True)


# ── Dashboard ──────────────────────────────────────────────

class RiskFactorsOut(BaseModel):
    conscientiousness_divergence: float
    weakest_link_stability: float


class HarmonyMetricsOut(BaseModel):
    performance: float
    cohesion: float
    risk_factors: RiskFactorsOut


class WeatherTrendOut(BaseModel):
    average: float
    std: float = 0.0
    response_count: int
    days_observed: int
    status: str     # "stable" | "turbulent" | "critical"


class FullDiagnosisOut(BaseModel):
    crew_type: str
    risk_level: str
    volatility_index: float
    hidden_conflict: float
    short_term_prediction: str
    recommended_action: str
    early_warning: str


class DashboardOut(BaseModel):
    yacht_id: int
    harmony_metrics: HarmonyMetricsOut
    weather_trend: WeatherTrendOut
    full_diagnosis: FullDiagnosisOut