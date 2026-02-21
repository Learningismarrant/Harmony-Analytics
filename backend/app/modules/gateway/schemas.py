# app/modules/gateway/schemas.py
"""
Schemas pour les flux d'entrée par token (QR codes).
Deux flux distincts :
  - Boarding token  : marin rejoint l'équipage d'un yacht
  - Invite token    : candidat rejoint une campagne de recrutement
"""
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from app.shared.enums import CampaignStatus


# ── Boarding (yacht) ───────────────────────────────────────

class BoardingYachtInfoOut(BaseModel):
    """Info publique du yacht accessible via boarding token."""
    yacht_id: int
    yacht_name: str
    employer_name: str


class BoardingJoinOut(BaseModel):
    """Réponse après embarquement réussi."""
    message: str
    yacht_id: int
    yacht_name: str
    assignment_id: int


# ── Campagne (invite) ──────────────────────────────────────

class CampaignPublicOut(BaseModel):
    """Info publique de la campagne accessible via invite token."""
    campaign_id: int
    title: str
    position: str
    description: Optional[str] = None
    yacht_name: Optional[str] = None
    status: CampaignStatus


class CampaignJoinOut(BaseModel):
    """Réponse après candidature réussie."""
    message: str
    campaign_id: int
    application_id: int