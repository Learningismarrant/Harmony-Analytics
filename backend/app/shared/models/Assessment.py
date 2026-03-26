# app/models/assessment.py
"""
Modèles du système de tests psychométriques.

TestCatalogue → Questions → TestResult
                              ↓
                   TestResult.scores (JSON)
                   {
                     "traits": {"conscientiousness": {"score": 72.4, "niveau": "Élevé"}},
                     "reliability": {"is_reliable": true, "reasons": []},
                     "meta": {"total_time_seconds": 240, "avg_seconds_per_question": 6.0},
                     "global_score": 68.1
                   }

TestSession + TestResponse : persistance des réponses individuelles
(candidats ET calibrateurs, discriminés par XOR crew_profile_id/calibrator_id)
"""
import enum

from sqlalchemy import (
    Column, Integer, String, Boolean, Float, DateTime, JSON, Text,
    ForeignKey, Enum, CheckConstraint, Index,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from app.shared.enums import UserRole


class CatalogueDomain(str, enum.Enum):
    personality  = "personality"
    cognitive    = "cognitive"
    motivation   = "motivation"
    person_job   = "person_job"
    person_org   = "person_org"
    person_team  = "person_team"
    physical     = "physical"


class TestCatalogue(Base):
    __tablename__ = "test_catalogues"
    id                     = Column(Integer, primary_key=True, index=True)
    name                   = Column(String, nullable=False)
    description            = Column(String, nullable=True)
    instructions           = Column(Text, nullable=True)
    test_type              = Column(String, nullable=False)   # "likert" | "qcm" | "Ipsatif"
    n_questions            = Column(Integer, default=1)
    max_score_per_question = Column(Integer, default=5)
    is_active              = Column(Boolean, default=True)
    created_at             = Column(DateTime(timezone=True), server_default=func.now())

    # Statut de validation et licence
    # status : "ALPHA" | "VALIDATED" | "CALIBRATED"
    status             = Column(String, default="ALPHA", nullable=False)
    # license : "PUBLIC_DOMAIN" | "PUBLISHED_RESEARCH" | "CUSTOM_ALPHA"
    license            = Column(String, default="CUSTOM_ALPHA", nullable=False)
    # Avertissements, limitations, TODO calibration
    validation_notes   = Column(Text, nullable=True)
    # Définition des modules : [{"index": 0, "name": "...", "n_items": 24, ...}]
    modules_config     = Column(JSON, nullable=True)
    # Domaine psychométrique du catalogue
    domain             = Column(
        Enum(CatalogueDomain, name="cataloguedomain"),
        nullable=False,
        server_default=CatalogueDomain.personality.value,
    )

    questions = relationship("Question",     back_populates="test", cascade="all, delete-orphan")
    results   = relationship("TestResult",   back_populates="test")
    sessions  = relationship("TestSession",  back_populates="catalogue")

    def __repr__(self):
        return f"<TestCatalogue id={self.id} nom={self.name}>"


class Question(Base):
    __tablename__ = "questions"
    id             = Column(Integer, primary_key=True, index=True)
    test_id        = Column(Integer, ForeignKey("test_catalogues.id"), nullable=False, index=True)
    text           = Column(Text,    nullable=False)
    question_type  = Column(String,  nullable=False)
    options        = Column(JSON,    nullable=True)
    trait          = Column(String,  nullable=True)
    correct_answer = Column(String,  nullable=True)
    reverse        = Column(Boolean, default=False)
    order          = Column(Integer, default=0)
    # Index du module auquel appartient cet item (0-based). None = pas de découpage modulaire.
    module_index   = Column(Integer, nullable=True)

    test           = relationship("TestCatalogue", back_populates="questions")
    calib_responses = relationship("TestResponse", back_populates="question")

    def __repr__(self):
        return f"<Question id={self.id} trait={self.trait}>"


class TestResult(Base):
    __tablename__ = "test_results"
    id              = Column(Integer, primary_key=True, index=True)
    # XOR strict : exactement l'un des deux doit être non-null
    crew_profile_id = Column(Integer, ForeignKey("crew_profiles.id"),  nullable=True, index=True)
    calibrator_id   = Column(Integer, ForeignKey("calib_users.id"),    nullable=True)
    session_id      = Column(Integer, ForeignKey("test_sessions.id"),  nullable=True)
    user_type       = Column(SQLEnum(UserRole, name="userrole", create_type=False), nullable=False, server_default="candidate")
    test_id         = Column(Integer, ForeignKey("test_catalogues.id"), nullable=False, index=True)
    global_score    = Column(Float,   nullable=False)
    scores          = Column(JSON,    nullable=False)   # {traits, reliability, meta, global_score}
    created_at      = Column(DateTime(timezone=True), server_default=func.now())

    crew_profile = relationship("CrewProfile", back_populates="test_results")
    test         = relationship("TestCatalogue", back_populates="results")

    @property
    def test_name(self) -> str:
        return self.test.name if self.test else f"test_{self.test_id}"

    def __repr__(self):
        return f"<TestResult id={self.id} crew={self.crew_profile_id} score={self.global_score}>"


class TestSession(Base):
    """
    Session de passation unifiée — candidats ET calibrateurs.

    Contrainte XOR : exactement l'un des deux FKs (crew_profile_id, calibrator_id)
    doit être non-null. Discriminateur : présence de l'un ou l'autre.
    completed_at=None → session en cours.
    """
    __tablename__ = "test_sessions"

    id              = Column(Integer, primary_key=True, index=True)
    catalogue_id    = Column(Integer, ForeignKey("test_catalogues.id"),  nullable=False)
    crew_profile_id = Column(Integer, ForeignKey("crew_profiles.id"),    nullable=True)
    calibrator_id   = Column(Integer, ForeignKey("calib_users.id"),      nullable=True)
    started_at      = Column(DateTime(timezone=True), server_default=func.now())
    completed_at    = Column(DateTime(timezone=True), nullable=True)
    device_info     = Column(JSON, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "(crew_profile_id IS NOT NULL)::int + (calibrator_id IS NOT NULL)::int = 1",
            name="check_xor_user_session",
        ),
        Index("ix_test_sessions_crew_catalogue",  "crew_profile_id", "catalogue_id"),
        Index("ix_test_sessions_calib_catalogue", "calibrator_id",   "catalogue_id"),
    )

    catalogue = relationship("TestCatalogue", back_populates="sessions")
    responses = relationship(
        "TestResponse", back_populates="session", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        status = "done" if self.completed_at else "in_progress"
        return f"<TestSession id={self.id} catalogue={self.catalogue_id} status={status}>"


class TestResponse(Base):
    """
    Réponse individuelle à un item lors d'une session (candidat ou calibrateur).

    response_value : str — couvre Likert ("4"), QCM ("B"), forced-choice ("left"), etc.
    catalogue_id   : dénormalisé server-side depuis session.catalogue_id — jamais accepté du client.
    """
    __tablename__ = "test_responses"

    id             = Column(Integer, primary_key=True, index=True)
    session_id     = Column(Integer, ForeignKey("test_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    catalogue_id   = Column(Integer, ForeignKey("test_catalogues.id"), nullable=False)
    question_id    = Column(Integer, ForeignKey("questions.id",       ondelete="CASCADE"), nullable=False)
    response_value = Column(String(50), nullable=False)
    seconds_spent  = Column(Float, nullable=True)

    __table_args__ = (
        Index("ix_test_responses_catalogue_question", "catalogue_id", "question_id"),
        CheckConstraint(
            "seconds_spent IS NULL OR (seconds_spent >= 0 AND seconds_spent <= 3600)",
            name="check_seconds_spent_range",
        ),
    )

    session  = relationship("TestSession",  back_populates="responses")
    question = relationship("Question",     back_populates="calib_responses")

    def __repr__(self) -> str:
        return (
            f"<TestResponse id={self.id} session={self.session_id} "
            f"question={self.question_id} value={self.response_value!r}>"
        )