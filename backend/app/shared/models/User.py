# app/models/user.py
"""
Modèles liés aux utilisateurs.

Stratégie de découpage User :
- User          : données auth + psychometric_snapshot (cache)
- UserDocument  : certificats STCW et documents vérifiés via OCR/Promete

Note sur psychometric_snapshot et snapshot_updated_at :
  Ces champs remplacent le pattern "relire tous les TestResult à chaque appel".
  Mis à jour de façon synchrone après chaque soumission de test.
  Format JSON défini dans engine/psychometrics/snapshot.py.
"""
# app/models/user.py
from sqlalchemy import (
    Column, Integer, String, Boolean, Float,
    DateTime, JSON, ForeignKey, Enum as SAEnum,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.shared.enums import UserRole, YachtPosition


class User(Base):
    __tablename__ = "users"

    id    = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=True)
    name  = Column(String, nullable=False)

    avatar_url      = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)

    is_harmony_verified = Column(Boolean, default=False, index=True)
    role      = Column(SAEnum(UserRole), default=UserRole.CANDIDATE, nullable=False, index=True)
    is_active = Column(Boolean, default=True)

    location   = Column(String, nullable=True)    # ex: "Antibes, FR"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # ── Relations 1:1 vers les profils ───────────────────────
    crew_profile = relationship(
        "CrewProfile", back_populates="user",
        uselist=False, cascade="all, delete-orphan",
    )
    employer_profile = relationship(
        "EmployerProfile", back_populates="user",
        uselist=False, cascade="all, delete-orphan",
    )

    # Documents liés à l'humain (Passeport, Visa, STCW…)
    documents = relationship(
        "UserDocument", back_populates="owner",
        cascade="all, delete-orphan",
    )

    # ── Helpers ──────────────────────────────────────────────
    @property
    def is_crew(self) -> bool:
        return self.role == UserRole.CANDIDATE

    @property
    def is_employer(self) -> bool:
        return self.role in (UserRole.CLIENT, UserRole.ADMIN)

    def __repr__(self):
        return f"<User id={self.id} email={self.email} role={self.role}>"


class CrewProfile(Base):
    """
    Profil pour les candidats et capitaines (en tant qu'employés).

    psychometric_snapshot : cache JSON reconstruit après chaque test.
    Ne jamais écrire manuellement — passer par assessment/service._refresh_crew_snapshot().
    Structure : {big_five, cognitive, motivation, leadership_preferences, resilience, meta}
    """
    __tablename__ = "crew_profiles"

    id      = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    position_targeted   = Column(SAEnum(YachtPosition), default=YachtPosition.DECKHAND, nullable=False)
    experience_years    = Column(Integer, default=0)
    availability_status = Column(String, default="available")
    # "available" | "on_board" | "unavailable" | "soon"

    psychometric_snapshot = Column(JSON, nullable=True)
    snapshot_updated_at   = Column(DateTime(timezone=True), nullable=True)

    trust_score = Column(Integer, nullable=True)

    # ── Relations ────────────────────────────────────────────
    user = relationship("User", back_populates="crew_profile")

    experiences = relationship(
        "CrewAssignment", back_populates="crew_profile",
        cascade="all, delete-orphan",
        foreign_keys="CrewAssignment.crew_profile_id",
    )
    applications = relationship(
        "CampaignCandidate", back_populates="crew_profile",
        cascade="all, delete-orphan",
    )
    test_results = relationship(
        "TestResult", back_populates="crew_profile",
        cascade="all, delete-orphan",
    )
    daily_pulses = relationship(
        "DailyPulse", back_populates="crew_profile",
        cascade="all, delete-orphan",
    )

    # ── Pass-through helpers ──────────────────────────────────
    @property
    def name(self) -> str:
        return self.user.name if self.user else ""

    @property
    def email(self) -> str:
        return self.user.email if self.user else ""

    @property
    def avatar_url(self):
        return self.user.avatar_url if self.user else None

    @property
    def is_harmony_verified(self) -> bool:
        return self.user.is_harmony_verified if self.user else False

    @property
    def profile_completion(self) -> float:
        if not self.user:
            return 0.0
        checks = [
            bool(self.user.location),
            bool(self.user.phone),
            bool(self.user.avatar_url),
            bool(self.experiences),
            bool(self.user.documents),
            bool(self.psychometric_snapshot),
        ]
        return round(sum(checks) / len(checks), 2)

    def __repr__(self):
        return f"<CrewProfile id={self.id} user_id={self.user_id} pos={self.position_targeted}>"


class EmployerProfile(Base):
    """
    Profil pour les clients (Management, Owners, Captains recruteurs).

    fleet_snapshot : cache agrégé de la flotte.
    Mis à jour par Cron (engine/fleet/aggregator.py).
    """
    __tablename__ = "employer_profiles"

    id      = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    company_name      = Column(String, nullable=True)
    is_billing_active = Column(Boolean, default=False)

    fleet_snapshot   = Column(JSON, nullable=True)
    fleet_updated_at = Column(DateTime(timezone=True), nullable=True)

    # ── Relations ────────────────────────────────────────────
    user = relationship("User", back_populates="employer_profile")

    yachts_managed = relationship(
        "Yacht", back_populates="employer",
        cascade="all, delete-orphan",
    )
    campaigns = relationship(
        "Campaign", back_populates="employer",
        cascade="all, delete-orphan",
    )
    surveys_triggered = relationship(
        "Survey", back_populates="triggered_by",
        foreign_keys="Survey.triggered_by_id",
    )

    # ── Helpers ──────────────────────────────────────────────
    @property
    def name(self) -> str:
        return self.user.name if self.user else ""

    @property
    def fleet_size(self) -> int:
        return len(self.yachts_managed) if self.yachts_managed else 0

    def __repr__(self):
        return f"<EmployerProfile id={self.id} user_id={self.user_id} company={self.company_name}>"


class UserDocument(Base):
    __tablename__ = "user_documents"

    id      = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    title         = Column(String, nullable=False, default="Document")
    document_type = Column(String, nullable=True)   # "certificate" | "identity" | "visa"
    file_url      = Column(String, nullable=False)
    expiry_date   = Column(DateTime(timezone=True), nullable=True)

    is_verified = Column(Boolean, default=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)

    # Données officielles Promete
    official_id            = Column(String, nullable=True)
    official_brevet        = Column(String, nullable=True)
    num_titulaire_officiel = Column(String, nullable=True)
    official_name          = Column(String, nullable=True)
    verification_metadata  = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates="documents")

    def __repr__(self):
        return f"<UserDocument id={self.id} title={self.title} verified={self.is_verified}>"