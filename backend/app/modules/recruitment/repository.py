# modules/recruitment/repository.py
"""
Accès DB pour les campagnes de recrutement, candidatures et RecruitmentEvents.
Agrège les CRUD campaign.py, candidates.py et links.py existants.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from sqlalchemy.exc import IntegrityError
from typing import List, Optional, Dict, Any

from app.models.campaign import Campaign, CampaignCandidate
from app.models.yacht import Yacht
from app.models.user import User
from app.models.survey import RecruitmentEvent, ModelVersion
from backend.app.shared.enums import CampaignStatus, ApplicationStatus
from datetime import datetime


class RecruitmentRepository:

    # ─────────────────────────────────────────────
    # CAMPAGNES
    # ─────────────────────────────────────────────

    def create_campaign(self, db: Session, payload, client_id: int) -> Campaign:
        db_obj = Campaign(
            **payload.model_dump(),
            client_id=client_id,
            status=CampaignStatus.OPEN,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_campaign_by_id(self, db: Session, campaign_id: int) -> Optional[Campaign]:
        return db.query(Campaign).filter(Campaign.id == campaign_id).first()

    def get_campaign_secure(
        self, db: Session, campaign_id: int, client_id: int
    ) -> Optional[Campaign]:
        return db.query(Campaign).filter(
            Campaign.id == campaign_id,
            Campaign.client_id == client_id,
        ).first()

    def get_campaigns_for_client(
        self,
        db: Session,
        client_id: int,
        campaign_status: Optional[CampaignStatus] = None,
        is_archived: bool = False,
    ) -> List[Campaign]:
        q = db.query(Campaign).filter(
            Campaign.client_id == client_id,
            Campaign.is_archived == is_archived,
        )
        if campaign_status:
            q = q.filter(Campaign.status == campaign_status)
        return q.order_by(Campaign.created_at.desc()).all()

    def get_by_invite_token(self, db: Session, token: str) -> Optional[Campaign]:
        return db.query(Campaign).filter(Campaign.invite_token == token).first()

    def get_active_campaign_for_yacht(
        self, db: Session, yacht_id: int, position: str
    ) -> Optional[Campaign]:
        return db.query(Campaign).filter(
            Campaign.yacht_id == yacht_id,
            Campaign.position == position,
            Campaign.status == CampaignStatus.OPEN,
            Campaign.is_archived == False,
        ).first()

    def update_campaign(self, db: Session, campaign: Campaign, payload) -> Campaign:
        for field, value in payload.model_dump(exclude_unset=True).items():
            if hasattr(campaign, field):
                setattr(campaign, field, value)
        db.commit()
        db.refresh(campaign)
        return campaign

    def update_status(
        self, db: Session, campaign: Campaign, new_status: CampaignStatus
    ) -> Campaign:
        campaign.status = new_status
        db.commit()
        db.refresh(campaign)
        return campaign

    def archive_campaign(self, db: Session, campaign: Campaign) -> Campaign:
        campaign.is_archived = True
        campaign.status = CampaignStatus.CLOSED
        db.commit()
        db.refresh(campaign)
        return campaign

    def soft_delete_campaign(self, db: Session, campaign: Campaign) -> None:
        campaign.is_archived = True
        db.commit()

    def count_hired_candidates(self, db: Session, campaign_id: int) -> int:
        return db.query(CampaignCandidate).filter(
            CampaignCandidate.campaign_id == campaign_id,
            CampaignCandidate.is_hired == True,
        ).count()

    # ─────────────────────────────────────────────
    # CANDIDATURES
    # ─────────────────────────────────────────────

    def get_application(
        self, db: Session, campaign_id: int, candidate_id: int
    ) -> Optional[CampaignCandidate]:
        return db.query(CampaignCandidate).filter(
            CampaignCandidate.campaign_id == campaign_id,
            CampaignCandidate.candidate_id == candidate_id,
        ).first()

    def create_application(
        self, db: Session, campaign_id: int, candidate_id: int
    ) -> Optional[CampaignCandidate]:
        existing = self.get_application(db, campaign_id, candidate_id)
        if existing:
            return existing
        db_obj = CampaignCandidate(
            campaign_id=campaign_id,
            candidate_id=candidate_id,
            status=ApplicationStatus.PENDING,
        )
        try:
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except IntegrityError:
            db.rollback()
            return None

    def update_candidate_status(
        self,
        db: Session,
        campaign_id: int,
        candidate_id: int,
        new_status: ApplicationStatus,
    ) -> Optional[CampaignCandidate]:
        link = self.get_application(db, campaign_id, candidate_id)
        if not link:
            return None
        link.status = new_status
        link.reviewed_at = datetime.utcnow()
        db.commit()
        db.refresh(link)
        return link

    def hire_candidate(
        self, db: Session, campaign_id: int, candidate_id: int
    ) -> Optional[CampaignCandidate]:
        link = self.get_application(db, campaign_id, candidate_id)
        if not link:
            return None
        link.is_hired = True
        link.is_rejected = False
        link.status = ApplicationStatus.HIRED
        link.reviewed_at = datetime.utcnow()
        db.commit()
        db.refresh(link)
        return link

    def reject_candidate(
        self, db: Session, campaign_id: int, candidate_id: int, reason: str
    ) -> Optional[CampaignCandidate]:
        link = self.get_application(db, campaign_id, candidate_id)
        if not link:
            return None
        link.is_rejected = True
        link.is_hired = False
        link.status = ApplicationStatus.REJECTED
        link.rejected_reason = reason
        link.reviewed_at = datetime.utcnow()
        db.commit()
        db.refresh(link)
        return link

    def reject_pending_candidates(
        self, db: Session, campaign_id: int, reason: str
    ) -> int:
        """Rejet en masse de tous les candidats non embauchés (archivage campagne)."""
        links = db.query(CampaignCandidate).filter(
            CampaignCandidate.campaign_id == campaign_id,
            CampaignCandidate.is_hired == False,
            CampaignCandidate.is_rejected == False,
        ).all()
        for link in links:
            link.is_rejected = True
            link.status = ApplicationStatus.REJECTED
            link.rejected_reason = reason
        db.commit()
        return len(links)

    def bulk_reject_candidates(
        self, db: Session, campaign_id: int, candidate_ids: List[int], reason: str
    ) -> int:
        count = 0
        for cid in candidate_ids:
            result = self.reject_candidate(db, campaign_id, cid, reason)
            if result:
                count += 1
        return count

    def get_applications_for_candidate(
        self, db: Session, candidate_id: int
    ) -> List[Dict]:
        """Vue côté candidat : toutes ses candidatures avec contexte campagne."""
        return db.query(
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
        ).join(
            Campaign, Campaign.id == CampaignCandidate.campaign_id
        ).outerjoin(
            Yacht, Yacht.id == Campaign.yacht_id
        ).filter(
            CampaignCandidate.candidate_id == candidate_id
        ).all()

    def get_applications_status_map(
        self, db: Session, campaign_id: int
    ) -> Dict[int, Dict]:
        """Map candidat_id → statut, pour la fusion dans le matching."""
        links = db.query(CampaignCandidate).filter(
            CampaignCandidate.campaign_id == campaign_id
        ).all()
        return {
            link.candidate_id: {
                "is_hired": link.is_hired,
                "is_rejected": link.is_rejected,
                "status": link.status,
                "rejected_reason": link.rejected_reason,
            }
            for link in links
        }

    # ─────────────────────────────────────────────
    # MATCHING — hydratation des snapshots
    # ─────────────────────────────────────────────

    def get_candidates_with_snapshots(
        self, db: Session, campaign_id: int
    ) -> List[Dict]:
        """
        Retourne les candidats d'une campagne avec leurs snapshots.
        C'est l'input principal du moteur de matching.
        """
        rows = (
            db.query(User)
            .join(CampaignCandidate, CampaignCandidate.candidate_id == User.id)
            .filter(CampaignCandidate.campaign_id == campaign_id)
            .all()
        )
        return [
            {
                "id": u.id,
                "name": u.name,
                "avatar_url": u.avatar_url,
                "location": u.location,
                "experience_years": u.experience_years or 0,
                "profile": u.psychometric_snapshot or {},
                "snapshot": u.psychometric_snapshot,
            }
            for u in rows
        ]

    def get_candidate_snapshot(
        self, db: Session, candidate_id: int
    ) -> Optional[Dict]:
        user = db.query(User).filter(User.id == candidate_id).first()
        return user.psychometric_snapshot if user else None

    def get_campaign_statistics(self, db: Session, campaign_id: int) -> Dict:
        total = db.query(CampaignCandidate).filter(
            CampaignCandidate.campaign_id == campaign_id
        ).count()
        hired = db.query(CampaignCandidate).filter(
            CampaignCandidate.campaign_id == campaign_id,
            CampaignCandidate.is_hired == True,
        ).count()
        rejected = db.query(CampaignCandidate).filter(
            CampaignCandidate.campaign_id == campaign_id,
            CampaignCandidate.is_rejected == True,
        ).count()
        return {
            "total_candidates": total,
            "hired_count": hired,
            "rejected_count": rejected,
            "pending_count": total - hired - rejected,
        }

    # ─────────────────────────────────────────────
    # RECRUITMENT EVENTS (ML Temps 2)
    # ─────────────────────────────────────────────

    def create_recruitment_event(
        self, db: Session, data: Dict[str, Any]
    ) -> RecruitmentEvent:
        db_obj = RecruitmentEvent(**data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_active_event_for_crew(
        self, db: Session, yacht_id: int, user_id: int
    ) -> Optional[RecruitmentEvent]:
        return db.query(RecruitmentEvent).filter(
            RecruitmentEvent.yacht_id == yacht_id,
            RecruitmentEvent.candidate_id == user_id,
            RecruitmentEvent.outcome == "hired",
        ).order_by(RecruitmentEvent.created_at.desc()).first()

    def update_y_actual(
        self, db: Session, event_id: int, y_actual: float
    ) -> None:
        event = db.query(RecruitmentEvent).filter(RecruitmentEvent.id == event_id).first()
        if event:
            event.y_actual = y_actual
            event.updated_at = datetime.utcnow()
            db.commit()

    def count_events_with_y_actual(self, db: Session) -> int:
        return db.query(RecruitmentEvent).filter(
            RecruitmentEvent.y_actual.isnot(None)
        ).count()

    def get_active_model_betas(self, db: Session) -> Dict:
        """Retourne les betas du ModelVersion actif (fallback sur defaults si absent)."""
        from engine.recruitment.master import DEFAULT_BETAS
        version = db.query(ModelVersion).filter(
            ModelVersion.is_active == True
        ).order_by(ModelVersion.created_at.desc()).first()

        if not version:
            return DEFAULT_BETAS

        return {
            "b1_p_ind": version.b1_p_ind,
            "b2_f_team": version.b2_f_team,
            "b3_f_env": version.b3_f_env,
            "b4_f_lmx": version.b4_f_lmx,
        }