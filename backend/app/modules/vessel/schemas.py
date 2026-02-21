# app/modules/vessel/schemas.py
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime


# ── Yacht CRUD ─────────────────────────────────────────────

class YachtCreateIn(BaseModel):
    name: str
    type: str
    length: Optional[int] = Field(None, description="Longueur en mètres")


class YachtUpdateIn(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    length: Optional[int] = None


class YachtOut(BaseModel):
    id: int
    name: str
    type: str
    length: Optional[int] = None
    employer_profile_id: int
    boarding_token: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class YachtTokenOut(BaseModel):
    id: int
    name: str
    boarding_token: str
    model_config = ConfigDict(from_attributes=True)


# ── Paramètres environnement JD-R (F_env + F_lmx) ─────────

class EnvironmentUpdateIn(BaseModel):
    """
    Paramètres JD-R normalisés (0.0 → 1.0).
    Alimentent F_env et F_lmx dans l'équation maîtresse.
    """
    # Demandes (D_yacht)
    charter_intensity:  Optional[float] = Field(None, ge=0.0, le=1.0)
    management_pressure: Optional[float] = Field(None, ge=0.0, le=1.0)
    # Ressources (R_yacht)
    salary_index:       Optional[float] = Field(None, ge=0.0, le=1.0)
    rest_days_ratio:    Optional[float] = Field(None, ge=0.0, le=1.0)
    private_cabin_ratio: Optional[float] = Field(None, ge=0.0, le=1.0)
    # Vecteur capitaine (F_lmx)
    captain_autonomy_given:    Optional[float] = Field(None, ge=0.0, le=1.0)
    captain_feedback_style:    Optional[float] = Field(None, ge=0.0, le=1.0)
    captain_structure_imposed: Optional[float] = Field(None, ge=0.0, le=1.0)


class JDRParamsOut(BaseModel):
    charter_intensity: float
    management_pressure: float
    salary_index: float
    rest_days_ratio: float
    private_cabin_ratio: float
    r_d_ratio: float            # ratio ressources/demandes calculé


class CaptainVectorOut(BaseModel):
    autonomy_given: float
    feedback_style: float
    structure_imposed: float


class VesselSnapshotOut(BaseModel):
    """Vue lisible du vessel_snapshot pour le dashboard employeur."""
    crew_count: int
    harmony_result: Optional[dict] = None
    jdr_params: Optional[JDRParamsOut] = None
    captain_vector: Optional[CaptainVectorOut] = None
    observed_scores: Optional[dict] = None    # Mis à jour par les surveys
    last_updated: Optional[str] = None