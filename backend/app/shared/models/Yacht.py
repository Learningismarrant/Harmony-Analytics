# app/models/yacht.py
"""
Modèles liés aux yachts et à la gestion d'équipage.

CrewAssignment sert à deux fins :
1. Équipage actif (is_active=True, is_harmony_approved=False)
2. Expériences passées déclarées par le candidat (is_active=False, is_harmony_approved selon véri.)

Champs snapshot sur Yacht :
  - vessel_snapshot           : cache harmony + JD-R params + observed scores
  - captain_leadership_vector : vecteur style capitaine pour F_lmx
  - snapshot_updated_at       : TTL guard (< 10 min → pas de recalcul)
"""
from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, JSON, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from app.shared.enums import YachtPosition
import secrets


class Yacht(Base):
    __tablename__ = "yachts"

    id        = Column(Integer, primary_key=True, index=True)
    employer_profile_id       = Column(Integer, ForeignKey("employer_profiles.id"), nullable=False, index=True)

    name   = Column(String, nullable=False)
    type   = Column(String, nullable=False)     # "Motor", "Sail"
    length = Column(Integer, nullable=True)      # mètres

    # ── Token d'embarquement (QR code) ──────────────────────
    # Régénéré après chaque usage (voir identity/repository.py)
    boarding_token = Column(
        String,
        default=lambda: secrets.token_urlsafe(16),
        unique=True,
        nullable=False,
    )

    # ── Snapshot vessel (cache multi-niveaux) ────────────────
    # Mis à jour en background après changement équipe ou test
    # Structure définie dans modules/vessel/repository.py
    vessel_snapshot     = Column(JSON, nullable=True)
    snapshot_updated_at = Column(DateTime(timezone=True), nullable=True)

    # Vecteur leadership du capitaine — input F_lmx
    # {"autonomy_given": 0.6, "feedback_style": 0.4, "structure_imposed": 0.7}
    captain_leadership_vector = Column(JSON, nullable=True)

    # Flag automatique ANOVA : toxicité détectée
    toxicity_flag        = Column(Boolean, default=False)
    required_es_minimum  = Column(Float, nullable=True)   # Seuil ES requis si yacht toxique

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # ── Relations ────────────────────────────────────────────
    employer         = relationship("EmployerProfile", back_populates="yachts_managed")
    crew_assignments = relationship("CrewAssignment", back_populates="yacht", cascade="all, delete-orphan")
    campaigns        = relationship("Campaign", back_populates="yacht")
    daily_pulses     = relationship("DailyPulse", back_populates="yacht", cascade="all, delete-orphan")
    surveys          = relationship("Survey", back_populates="yacht")

    def __repr__(self):
        return f"<Yacht id={self.id} name={self.name}>"


class CrewAssignment(Base):
    """
    Usage dual :
    - Équipage actif       : is_active=True
    - Expérience déclarée  : is_active=False + verification_token

    Les expériences déclarées sans yacht_id utilisent external_yacht_name.
    """
    __tablename__ = "crew_assignments"

    id       = Column(Integer, primary_key=True, index=True)
    crew_profile_id = Column(Integer, ForeignKey("crew_profiles.id"), nullable=False, index=True)
    yacht_id        = Column(Integer, ForeignKey("yachts.id"), nullable=True, index=True)

    role      = Column(SAEnum(YachtPosition), nullable=False)
    is_active = Column(Boolean, default=True)

    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date   = Column(DateTime(timezone=True), nullable=True)

    # ── Expériences déclarées ────────────────────────────────
    external_yacht_name = Column(String, nullable=True)  # Si hors Harmony
    contract_type       = Column(String, nullable=True)  # "CDI", "CDD", "Freelance"

    # Commentaires
    candidate_comment = Column(String, nullable=True)  # Note du candidat
    reference_comment = Column(String, nullable=True)  # Note du référent (après verif email)

    # Vérification par email
    is_harmony_approved      = Column(Boolean, default=False)
    reference_contact_email  = Column(String, nullable=True)
    verification_token       = Column(String, default=lambda: secrets.token_urlsafe(16), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # ── Relations ────────────────────────────────────────────
    crew_profile = relationship("CrewProfile", back_populates="experiences", foreign_keys=[crew_profile_id])
    yacht        = relationship("Yacht", back_populates="crew_assignments")

    # ── Properties pratiques ─────────────────────────────────
    @property
    def yacht_name(self) -> str:
        if self.yacht:
            return self.yacht.name
        return self.external_yacht_name or "Yacht non répertorié"

    @property
    def name(self) -> str:
        return self.crew_profile.name if self.crew_profile else ""

    @property
    def avatar_url(self):
        return self.crew_profile.avatar_url if self.crew_profile else None

    @property
    def is_harmony_verified(self) -> bool:
        return self.crew_profile.is_harmony_verified if self.crew_profile else False

    def __repr__(self):
        return f"<CrewAssignment id={self.id} crew={self.crew_profile_id} yacht={self.yacht_id} active={self.is_active}>"
