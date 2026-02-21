# app/models/campaign.py
"""
Modèles des campagnes de recrutement.

Campaign        : une offre de poste sur un yacht
CampaignCandidate : le lien candidat ↔ campagne (candidature)
"""
from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, JSON, ForeignKey, Enum as SAEnum, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from app.shared.enums import CampaignStatus, ApplicationStatus
import secrets


class Campaign(Base):
    __tablename__ = "campaigns"

    id                  = Column(Integer, primary_key=True, index=True)
    employer_profile_id = Column(Integer, ForeignKey("employer_profiles.id"), nullable=False, index=True)
    yacht_id            = Column(Integer, ForeignKey("yachts.id"), nullable=True,  index=True)

    title       = Column(String, nullable=False)
    position    = Column(String, nullable=False)
    description = Column(String, nullable=True)
    status      = Column(SAEnum(CampaignStatus), default=CampaignStatus.OPEN, nullable=False)
    is_archived = Column(Boolean, default=False)
    invite_token = Column(String, default=lambda: secrets.token_urlsafe(16), unique=True, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    employer   = relationship("EmployerProfile", back_populates="campaigns")
    yacht      = relationship("Yacht", back_populates="campaigns")
    candidates = relationship("CampaignCandidate", back_populates="campaign", cascade="all, delete-orphan")

    @property
    def yacht_name(self) -> str:
        return self.yacht.name if self.yacht else None

    @property
    def candidate_count(self) -> int:
        return len(self.candidates) if self.candidates else 0

    def __repr__(self):
        return f"<Campaign id={self.id} title={self.title} status={self.status}>"


class CampaignCandidate(Base):
    """
    Lien candidature entre un CrewProfile et une Campaign.
    Cycle : PENDING → HIRED → JOINED / PENDING → REJECTED
    """
    __tablename__ = "campaign_candidates"

    id              = Column(Integer, primary_key=True, index=True)
    campaign_id     = Column(Integer, ForeignKey("campaigns.id"), nullable=False, index=True)
    crew_profile_id = Column(Integer, ForeignKey("crew_profiles.id"), nullable=False, index=True)

    status      = Column(SAEnum(ApplicationStatus), default=ApplicationStatus.PENDING)
    is_hired    = Column(Boolean, default=False)
    is_rejected = Column(Boolean, default=False)

    rejected_reason = Column(String, nullable=True)
    joined_at       = Column(DateTime(timezone=True), server_default=func.now())
    reviewed_at     = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("campaign_id", "crew_profile_id", name="uq_campaign_crew"),
    )

    campaign     = relationship("Campaign", back_populates="candidates")
    crew_profile = relationship("CrewProfile", back_populates="applications")

    def __repr__(self):
        return f"<CampaignCandidate campaign={self.campaign_id} crew={self.crew_profile_id} hired={self.is_hired}>"


