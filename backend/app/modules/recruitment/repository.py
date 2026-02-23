# modules/recruitment/repository.py
"""
Accès DB pour les campagnes, candidatures et RecruitmentEvents.

Changements v2 :
- Campaign.employer_profile_id      (était client_id)
- CampaignCandidate.crew_profile_id (était candidate_id)
- RecruitmentEvent.crew_profile_id  (était candidate_id/user_id)
- get_candidates_with_snapshots → lit CrewProfile.psychometric_snapshot
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.exc import IntegrityError
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from app.shared.models import (Campaign, CampaignCandidate,
                               Yacht,
                               User, CrewProfile,
                               RecruitmentEvent, ModelVersion)

from app.shared.enums import CampaignStatus, ApplicationStatus


class RecruitmentRepository:

    # ── Campagnes ─────────────────────────────────────────────

    async def create_campaign(
        self, db: AsyncSession, payload, employer_profile_id: int  # v2
    ) -> Campaign:
        import secrets
        db_obj = Campaign(
            **payload.model_dump(),
            employer_profile_id=employer_profile_id,
            status=CampaignStatus.OPEN,
            invite_token=secrets.token_urlsafe(12),
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_campaign_by_id(
        self, db: AsyncSession, campaign_id: int
    ) -> Optional[Campaign]:
        r = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
        return r.scalar_one_or_none()

    async def get_campaign_secure(
        self, db: AsyncSession, campaign_id: int, employer_profile_id: int  # v2
    ) -> Optional[Campaign]:
        r = await db.execute(
            select(Campaign).where(
                Campaign.id == campaign_id,
                Campaign.employer_profile_id == employer_profile_id,
            )
        )
        return r.scalar_one_or_none()

    async def get_campaigns_for_employer(
        self,
        db: AsyncSession,
        employer_profile_id: int,   # v2
        campaign_status: Optional[CampaignStatus] = None,
        is_archived: bool = False,
    ) -> List[Campaign]:
        q = select(Campaign).where(
            Campaign.employer_profile_id == employer_profile_id,
            Campaign.is_archived == is_archived,
        )
        if campaign_status:
            q = q.where(Campaign.status == campaign_status)
        r = await db.execute(q.order_by(Campaign.created_at.desc()))
        return r.scalars().all()

    async def get_by_invite_token(
        self, db: AsyncSession, token: str
    ) -> Optional[Campaign]:
        r = await db.execute(select(Campaign).where(Campaign.invite_token == token))
        return r.scalar_one_or_none()

    async def update_campaign(
        self, db: AsyncSession, campaign: Campaign, payload
    ) -> Campaign:
        for field, value in payload.model_dump(exclude_unset=True).items():
            if hasattr(campaign, field):
                setattr(campaign, field, value)
        await db.commit()
        await db.refresh(campaign)
        return campaign

    async def archive_campaign(self, db: AsyncSession, campaign: Campaign) -> Campaign:
        campaign.is_archived = True
        campaign.status = CampaignStatus.CLOSED
        await db.commit()
        await db.refresh(campaign)
        return campaign

    # ── Candidatures ──────────────────────────────────────────

    async def get_application(
        self, db: AsyncSession, campaign_id: int, crew_profile_id: int  # v2
    ) -> Optional[CampaignCandidate]:
        r = await db.execute(
            select(CampaignCandidate).where(
                CampaignCandidate.campaign_id == campaign_id,
                CampaignCandidate.crew_profile_id == crew_profile_id,
            )
        )
        return r.scalar_one_or_none()

    async def create_application(
        self, db: AsyncSession, campaign_id: int, crew_profile_id: int  # v2
    ) -> Optional[CampaignCandidate]:
        existing = await self.get_application(db, campaign_id, crew_profile_id)
        if existing:
            return existing
        db_obj = CampaignCandidate(
            campaign_id=campaign_id,
            crew_profile_id=crew_profile_id,
            status=ApplicationStatus.PENDING,
        )
        try:
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
        except IntegrityError:
            await db.rollback()
            return None

    async def hire_candidate(
        self, db: AsyncSession, campaign_id: int, crew_profile_id: int  # v2
    ) -> Optional[CampaignCandidate]:
        link = await self.get_application(db, campaign_id, crew_profile_id)
        if not link:
            return None
        link.is_hired = True
        link.is_rejected = False
        link.status = ApplicationStatus.HIRED
        link.reviewed_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(link)
        return link

    async def reject_candidate(
        self, db: AsyncSession, campaign_id: int, crew_profile_id: int, reason: str  # v2
    ) -> Optional[CampaignCandidate]:
        link = await self.get_application(db, campaign_id, crew_profile_id)
        if not link:
            return None
        link.is_rejected = True
        link.is_hired = False
        link.status = ApplicationStatus.REJECTED
        link.rejected_reason = reason
        link.reviewed_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(link)
        return link

    async def reject_pending_candidates(
        self, db: AsyncSession, campaign_id: int, reason: str
    ) -> int:
        r = await db.execute(
            select(CampaignCandidate).where(
                CampaignCandidate.campaign_id == campaign_id,
                CampaignCandidate.is_hired == False,
                CampaignCandidate.is_rejected == False,
            )
        )
        links = r.scalars().all()
        for link in links:
            link.is_rejected = True
            link.status = ApplicationStatus.REJECTED
            link.rejected_reason = reason
        await db.commit()
        return len(links)

    async def get_applications_for_crew(
        self, db: AsyncSession, crew_profile_id: int  # v2
    ) -> List[Dict]:
        """Vue candidat — toutes ses candidatures avec contexte campagne."""
        r = await db.execute(
            select(
                Campaign.id.label("campaign_id"),
                Campaign.title.label("campaign_title"),
                Campaign.description.label("campaign_description"),
                Campaign.position,
                Campaign.status.label("campaign_status"),
                Campaign.created_at,
                Campaign.is_archived,
                CampaignCandidate.status.label("application_status"),
                CampaignCandidate.is_hired,
                CampaignCandidate.is_rejected,
                CampaignCandidate.rejected_reason,
                CampaignCandidate.joined_at,
                CampaignCandidate.reviewed_at,
                Yacht.name.label("yacht_name"),
            )
            .join(Campaign, Campaign.id == CampaignCandidate.campaign_id)
            .outerjoin(Yacht, Yacht.id == Campaign.yacht_id)
            .where(CampaignCandidate.crew_profile_id == crew_profile_id)
        )
        return [dict(row._mapping) for row in r.all()]

    async def get_applications_status_map(
        self, db: AsyncSession, campaign_id: int
    ) -> Dict[int, Dict]:
        """Map crew_profile_id → statut — pour la fusion dans le matching."""
        r = await db.execute(
            select(CampaignCandidate).where(
                CampaignCandidate.campaign_id == campaign_id
            )
        )
        links = r.scalars().all()
        return {
            link.crew_profile_id: {    # v2 : key = crew_profile_id
                "is_hired":       link.is_hired,
                "is_rejected":    link.is_rejected,
                "status":         link.status,
                "rejected_reason": link.rejected_reason,
            }
            for link in links
        }

    async def get_campaign_statistics(
        self, db: AsyncSession, campaign_id: int
    ) -> Dict:
        total = (await db.execute(
            select(func.count()).where(CampaignCandidate.campaign_id == campaign_id)
        )).scalar()
        hired = (await db.execute(
            select(func.count()).where(
                CampaignCandidate.campaign_id == campaign_id,
                CampaignCandidate.is_hired == True,
            )
        )).scalar()
        rejected = (await db.execute(
            select(func.count()).where(
                CampaignCandidate.campaign_id == campaign_id,
                CampaignCandidate.is_rejected == True,
            )
        )).scalar()
        return {
            "total_candidates": total,
            "hired_count": hired,
            "rejected_count": rejected,
            "pending_count": total - hired - rejected,
        }

    # ── Matching — hydratation snapshots ─────────────────────

    async def get_candidates_with_snapshots(
        self, db: AsyncSession, campaign_id: int
    ) -> List[Dict]:
        """
        v2 : joint via CrewProfile pour lire :
        - CrewProfile.psychometric_snapshot
        - CrewProfile.position_targeted
        - CrewProfile.experience_years
        - User.name, avatar_url, location (via CrewProfile.user)
        """
        r = await db.execute(
            select(CrewProfile, User)
            .join(User, User.id == CrewProfile.user_id)
            .join(CampaignCandidate, CampaignCandidate.crew_profile_id == CrewProfile.id)
            .where(CampaignCandidate.campaign_id == campaign_id)
        )
        rows = r.all()
        return [
            {
                "crew_profile_id": crew.id,    # v2 : clé principale
                "name": user.name,
                "avatar_url": user.avatar_url,
                "location": user.location,
                "experience_years": crew.experience_years or 0,
                "position_targeted": crew.position_targeted,
                "snapshot": crew.psychometric_snapshot,    # v2 : sur CrewProfile
            }
            for crew, user in rows
        ]

    async def get_candidate_snapshot(
        self, db: AsyncSession, crew_profile_id: int  # v2
    ) -> Optional[Dict]:
        r = await db.execute(
            select(CrewProfile.psychometric_snapshot)
            .where(CrewProfile.id == crew_profile_id)
        )
        return r.scalar_one_or_none()

    # ── RecruitmentEvents (ML Temps 2) ────────────────────────

    async def create_recruitment_event(
        self, db: AsyncSession, data: Dict[str, Any]
    ) -> RecruitmentEvent:
        db_obj = RecruitmentEvent(**data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_active_event_for_crew(
        self, db: AsyncSession, yacht_id: int, crew_profile_id: int  # v2
    ) -> Optional[RecruitmentEvent]:
        r = await db.execute(
            select(RecruitmentEvent).where(
                RecruitmentEvent.yacht_id == yacht_id,
                RecruitmentEvent.crew_profile_id == crew_profile_id,
                RecruitmentEvent.outcome == "hired",
            ).order_by(RecruitmentEvent.created_at.desc())
        )
        return r.scalars().first()

    async def update_y_actual(
        self, db: AsyncSession, event_id: int, y_actual: float
    ) -> None:
        r = await db.execute(
            select(RecruitmentEvent).where(RecruitmentEvent.id == event_id)
        )
        event = r.scalar_one_or_none()
        if event:
            event.y_actual = y_actual
            event.updated_at = datetime.now(timezone.utc)
            await db.commit()

    async def count_events_with_y_actual(self, db: AsyncSession) -> int:
        r = await db.execute(
            select(func.count()).where(RecruitmentEvent.y_actual.isnot(None))
        )
        return r.scalar()

    async def get_active_model_betas(self, db: AsyncSession) -> Dict:
        """Betas du ModelVersion actif — fallback sur DEFAULT_BETAS si absent."""
        from engine.recruitment.master import DEFAULT_BETAS
        r = await db.execute(
            select(ModelVersion)
            .where(ModelVersion.is_active == True)
            .order_by(ModelVersion.created_at.desc())
        )
        version = r.scalars().first()
        if not version:
            return DEFAULT_BETAS
        return {
            "b1_p_ind":  version.b1_p_ind,
            "b2_f_team": version.b2_f_team,
            "b3_f_env":  version.b3_f_env,
            "b4_f_lmx":  version.b4_f_lmx,
        }