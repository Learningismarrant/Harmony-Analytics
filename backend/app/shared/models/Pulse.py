# app/models/pulse.py
"""
Daily Pulse — signal quotidien de bien-être d'équipage.

Distinct du Survey (signal hebdo/mensuel plus riche).
Le Pulse (score 1-5) alimente le TVI (Team Volatility Index)
et le Hidden Conflict Detector dans engine/team/diagnosis.py.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base as _Base


class DailyPulse(_Base):
    __tablename__ = "daily_pulses"

    id              = Column(Integer, primary_key=True, index=True)
    crew_profile_id = Column(Integer, ForeignKey("crew_profiles.id"), nullable=False, index=True)
    yacht_id        = Column(Integer, ForeignKey("yachts.id"), nullable=False, index=True)

    score   = Column(Integer, nullable=False)        # 1 à 5
    comment = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # ── Relations ────────────────────────────────────────────
    crew_profile = relationship("CrewProfile", back_populates="daily_pulses")
    yacht        = relationship("Yacht", back_populates="daily_pulses")

    def __repr__(self):
        return f"<DailyPulse id={self.id} crew={self.crew_profile_id} score={self.score}>"
    

   

    