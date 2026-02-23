# app/modules/gateway/schemas.py
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Literal
from datetime import datetime


# ── RÉSOLUTION DE TOKEN ─────────────────────────────────────

class TokenResolveOut(BaseModel):
    """
    Réponse du résolveur universel. 
    Indique au frontend quel composant afficher.
    """
    target_type: Literal["yacht", "campaign", "experience"] = Field(
        ..., description="Type d'entité pointée par le token"
    )
    target_id: int = Field(..., description="ID de l'entité (YachtID, CampaignID, etc.)")
    name: str = Field(..., description="Nom de l'entité pour l'affichage")
    is_active: bool = True


# ── EMBARQUEMENT YACHT (Public) ─────────────────────────────

class YachtPublicInfoOut(BaseModel):
    """
    Infos visibles par un marin AVANT de cliquer sur "Rejoindre".
    Sécurité : on ne donne pas l'ID interne de l'employeur ici.
    """
    name: str
    type: str
    length: Optional[int] = None
    employer_name: str = Field(..., description="Nom de la société ou du profil employeur")
    current_crew_count: int


class YachtJoinOut(BaseModel):
    """Confirmation d'embarquement réussi."""
    yacht_id: int
    yacht_name: str
    joined_at: datetime
    status: str = "active"
    model_config = ConfigDict(from_attributes=True)


# ── CAMPAGNE DE RECRUTEMENT ─────────────────────────────────

class CampaignPublicInfoOut(BaseModel):
    """Infos sur une campagne via un lien de partage."""
    job_title: str
    yacht_name: str
    description: Optional[str] = None
    is_open: bool


class CampaignApplyOut(BaseModel):
    """Confirmation de candidature."""
    campaign_id: int
    applied_at: datetime
    status: str = "pending"
    model_config = ConfigDict(from_attributes=True)


# ── VÉRIFICATION D'EXPÉRIENCE (Interne Service) ─────────────

class ExperienceVerificationData(BaseModel):
    """
    Données extraites du token pour générer la page HTML 
    de vérification destinée au capitaine.
    """
    candidate_name: str
    yacht_name: str
    position: str
    start_date: datetime
    end_date: Optional[datetime] = None