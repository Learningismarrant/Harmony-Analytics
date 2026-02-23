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
"""
from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, JSON, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class TestCatalogue(Base):
    __tablename__ = "test_catalogues"
    id                     = Column(Integer, primary_key=True, index=True)
    name                   = Column(String, nullable=False)
    description            = Column(String, nullable=True)
    instructions           = Column(Text, nullable=True)
    test_type              = Column(String, nullable=False)   # "likert" | "cognitive"
    n_questions            = Column(Integer, default=1)
    max_score_per_question = Column(Integer, default=5)
    is_active              = Column(Boolean, default=True)
    created_at             = Column(DateTime(timezone=True), server_default=func.now())

    questions = relationship("Question",   back_populates="test", cascade="all, delete-orphan")
    results   = relationship("TestResult", back_populates="test")

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

    test = relationship("TestCatalogue", back_populates="questions")

    def __repr__(self):
        return f"<Question id={self.id} trait={self.trait}>"


class TestResult(Base):
    __tablename__ = "test_results"
    id              = Column(Integer, primary_key=True, index=True)
    crew_profile_id = Column(Integer, ForeignKey("crew_profiles.id"), nullable=False, index=True)
    test_id         = Column(Integer, ForeignKey("test_catalogues.id"), nullable=False, index=True)
    global_score    = Column(Float,   nullable=False)
    scores          = Column(JSON,    nullable=False)   # {traits, reliability, meta, global_score}
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    # reliability=Column(Boolean, nullable= False), "reasons": []},

    crew_profile = relationship("CrewProfile", back_populates="test_results")
    test         = relationship("TestCatalogue", back_populates="results")

    @property
    def test_name(self) -> str:
        return self.test.name if self.test else f"test_{self.test_id}"

    def __repr__(self):
        return f"<TestResult id={self.id} crew={self.crew_profile_id} score={self.global_score}>"