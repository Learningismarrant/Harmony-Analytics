# app/shared/models/Calibration.py
"""
Modèles isolés pour le système d'étalonnage psychométrique.

Ces tables (préfixe calib_) sont entièrement séparées du système de production.
Les calibrateurs (n=200-300 par instrument) passent les mêmes tests que les
candidats, mais leurs données alimentent uniquement le référentiel normatif.

CalibratorUser → CalibSession → CalibResponse
                     ↓
              CalibSession.completed_at (None si en cours)
"""
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Boolean, Float, DateTime, Date, JSON,
    ForeignKey, UniqueConstraint, Index,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class CalibratorUser(Base):
    """
    Utilisateur du système d'étalonnage.

    Totalement isolé de la table users principale.
    Authentification via JWT propre au module calibration.
    """
    __tablename__ = "calib_users"

    id              = Column(Integer, primary_key=True, index=True)
    email           = Column(String(255), unique=True, index=True, nullable=False)
    name            = Column(String(255), nullable=False)
    hashed_password = Column(String, nullable=False)
    cohort          = Column(String(100), nullable=True)   # ex: "ENSM Nantes 2026-03"
    is_active       = Column(Boolean, default=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())

    # ── Démographiques (analyse DIF) ──────────────────────────────────────────
    # Collectés après inscription via PATCH /calibration/me
    # Permettent de détecter les biais d'items (genre, âge, langue, expérience)
    gender          = Column(String(50),  nullable=True)   # "male"|"female"|"non_binary"|"prefer_not_to_say"
    birth_date      = Column(Date,         nullable=True)   # ex: 1990-06-15 — date de naissance complète
    education_level = Column(String(50),  nullable=True)   # "below_bac"|"bac"|"bac_plus_2"|"bac_plus_3"|"bac_plus_5"|"phd"
    native_language = Column(String(50),  nullable=True)   # "french"|"english"|"other" — critique pour items EN
    years_at_sea    = Column(Integer,     nullable=True)   # 0 = aucune expérience maritime
    maritime_role   = Column(String(100), nullable=True)   # "captain"|"officer"|"bosun"|"deckhand"|"other"|"none"
    nationality     = Column(String(100), nullable=True)   # pays (biais culturel/linguistique)

    sessions = relationship(
        "CalibSession", back_populates="calibrator",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<CalibratorUser id={self.id} email={self.email} cohort={self.cohort}>"


class CalibSession(Base):
    """
    Session de passation = un calibrateur qui passe UN catalogue de test.

    Contrainte unique (calibrator_id, catalogue_id) : un calibrateur ne peut
    passer un même catalogue qu'une seule fois.
    completed_at=None → session en cours.
    """
    __tablename__ = "calib_sessions"

    id             = Column(Integer, primary_key=True, index=True)
    calibrator_id  = Column(Integer, ForeignKey("calib_users.id", ondelete="CASCADE"), nullable=False, index=True)
    catalogue_id   = Column(Integer, ForeignKey("test_catalogues.id", ondelete="CASCADE"), nullable=False, index=True)
    started_at     = Column(DateTime(timezone=True), server_default=func.now())
    completed_at   = Column(DateTime(timezone=True), nullable=True)
    device_info    = Column(JSON, nullable=True)   # {"platform": "mobile", "os": "iOS 17"}

    __table_args__ = (
        UniqueConstraint("calibrator_id", "catalogue_id", name="uq_calib_session_calibrator_catalogue"),
    )

    calibrator = relationship("CalibratorUser", back_populates="sessions")
    catalogue  = relationship("TestCatalogue")
    responses  = relationship(
        "CalibResponse", back_populates="session",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        status = "done" if self.completed_at else "in_progress"
        return f"<CalibSession id={self.id} calibrator={self.calibrator_id} catalogue={self.catalogue_id} status={status}>"


class CalibResponse(Base):
    """
    Réponse individuelle à un item lors d'une session d'étalonnage.

    value : valeur brute choisie (0-10, couvre Likert 1-7 et QCM binaire).
    seconds_spent : temps passé sur cet item en secondes (optionnel).
    """
    __tablename__ = "calib_responses"

    id            = Column(Integer, primary_key=True, index=True)
    session_id    = Column(Integer, ForeignKey("calib_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id   = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)
    value         = Column(Integer, nullable=False)
    seconds_spent = Column(Float, nullable=True)

    session  = relationship("CalibSession", back_populates="responses")
    question = relationship("Question")

    def __repr__(self) -> str:
        return f"<CalibResponse id={self.id} session={self.session_id} question={self.question_id} value={self.value}>"
