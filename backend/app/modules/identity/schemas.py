# app/modules/identity/schemas.py
from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator
from typing import Optional, List, Any
from datetime import datetime, date
from app.shared.enums import YachtPosition, AvailabilityStatus, FeedbackTarget


# ── Identité (User) ────────────────────────────────────────

class UserIdentityOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    location: Optional[str] = None
    is_harmony_verified: bool
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class IdentityUpdateIn(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None


# ── Crew Profile ───────────────────────────────────────────

class CrewProfileOut(BaseModel):
    id: int
    user_id: int
    position_targeted: YachtPosition
    experience_years: int
    availability_status: str
    trust_score: Optional[int] = None
    profile_completion: float = 0.0
    model_config = ConfigDict(from_attributes=True)


class CrewProfileUpdateIn(BaseModel):
    position_targeted: Optional[YachtPosition] = None
    availability_status: Optional[AvailabilityStatus] = None
    experience_years: Optional[int] = Field(None, ge=0)


# ── Employer Profile ───────────────────────────────────────

class EmployerProfileOut(BaseModel):
    id: int
    user_id: int
    company_name: Optional[str] = None
    is_billing_active: bool
    fleet_size: int = 0
    model_config = ConfigDict(from_attributes=True)


class EmployerProfileUpdateIn(BaseModel):
    company_name: Optional[str] = None


# ── Expériences ────────────────────────────────────────────

class ExperienceCreateIn(BaseModel):
    yacht_id: Optional[int] = None
    external_yacht_name: Optional[str] = None
    role: YachtPosition
    start_date: date
    end_date: Optional[date] = None
    candidate_comment: Optional[str] = None
    contract_type: Optional[str] = None
    reference_contact_email: Optional[EmailStr] = None

    @model_validator(mode="after")
    def check_yacht(self):
        if not self.yacht_id and not self.external_yacht_name:
            raise ValueError("Précisez un yacht existant ou un nom externe.")
        return self


class ExperienceOut(BaseModel):
    id: int
    yacht_name: str
    role: str
    start_date: datetime
    end_date: Optional[datetime] = None
    is_harmony_approved: bool
    reference_comment: Optional[str] = None
    candidate_comment: Optional[str] = None
    contract_type: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


# ── Documents ──────────────────────────────────────────────

class DocumentOut(BaseModel):
    id: int
    title: str
    document_type: Optional[str] = None
    file_url: str
    expiry_date: Optional[datetime] = None
    is_verified: bool
    verification_metadata: Optional[Any] = None
    model_config = ConfigDict(from_attributes=True)


class UploadResponseOut(BaseModel):
    status: str
    message: str
    url: str
    document_id: Optional[int] = None


# ── Rapports psychométriques ───────────────────────────────

class RadarDataOut(BaseModel):
    trait: str
    label: str
    A: float        # Score candidat
    B: float        # Score SME cible
    fullMark: int = 100


class TestInsightOut(BaseModel):
    trait_key: str
    trait_label: str
    description: str
    user_score: float
    target_score: float
    gap: float
    status: str     # "aligned" | "gap_to_manage" | "strength"
    advice: Optional[Any] = None
    benchmark: str


class TestReportOut(BaseModel):
    test_id: int
    test_name: str
    test_date: datetime
    view_mode: FeedbackTarget
    position_targeted: YachtPosition
    reliability: dict
    radar_chart: List[RadarDataOut]
    insights: List[TestInsightOut]


# ── Full Profile ───────────────────────────────────────────

class AccessContextOut(BaseModel):
    view_mode: FeedbackTarget
    label: str
    context_position: Optional[str] = None
    is_active_crew: bool = False


class FullCrewProfileOut(BaseModel):
    context: AccessContextOut
    identity: UserIdentityOut
    crew: CrewProfileOut
    experiences: List[ExperienceOut] = []
    documents: List[DocumentOut] = []
    reports: List[TestReportOut] = []

# ── Snapshot (lecture externe) ─────────────────────────────

class PsychometricSnapshotOut(BaseModel):
    """Vue du psychometric_snapshot pour les services qui en ont besoin."""
    big_five: Optional[Dict[str, float]] = None
    cognitive: Optional[Dict[str, float]] = None
    motivation: Optional[Dict[str, float]] = None
    leadership_preferences: Optional[Dict[str, float]] = None
    resilience: Optional[float] = None
    meta: Optional[Dict[str, Any]] = None