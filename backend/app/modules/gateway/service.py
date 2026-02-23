# app/modules/gateway/service.py
import secrets
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.shared.models import (User, CrewProfile, EmployerProfile,
                                Yacht, CrewAssignment,
                                Campaign, CampaignCandidate
                                )
from app.modules.gateway.schemas import (
    TokenResolveOut, 
    YachtJoinOut
)

class GatewayService:

    # ─────────────────────────────────────────────
    # RÉSOLUTION UNIVERSELLE
    # ─────────────────────────────────────────────

    async def resolve_token(self, db: AsyncSession, token: str) -> TokenResolveOut | None:
        """
        Cherche le token dans : Yachts (boarding), Campagnes (invite), ou Assignments (verify).
        """
        # 1. Check Yacht (Boarding Token)
        res_yacht = await db.execute(
            select(Yacht.id, Yacht.name).where(Yacht.boarding_token == token)
        )
        yacht = res_yacht.first()
        if yacht:
            return TokenResolveOut(
                target_type="yacht",
                target_id=yacht.id,
                name=yacht.name
            )

        # 2. Check Campaign (Invite Token)
        res_camp = await db.execute(
            select(Campaign.id, Campaign.title).where(Campaign.invite_token == token)
        )
        camp = res_camp.first()
        if camp:
            return TokenResolveOut(
                target_type="campaign",
                target_id=camp.id,
                name=camp.title
            )

        # 3. Check CrewAssignment (Verification Token d'une expérience passée)
        res_exp = await db.execute(
            select(CrewAssignment.id, CrewAssignment.external_yacht_name, Yacht.name)
            .outerjoin(Yacht, CrewAssignment.yacht_id == Yacht.id)
            .where(CrewAssignment.verification_token == token)
        )
        exp = res_exp.first()
        if exp:
            return TokenResolveOut(
                target_type="experience",
                target_id=exp[0],
                name=exp[2] or exp[1] or "Yacht Inconnu"
            )

        return None

    # ─────────────────────────────────────────────
    # EMBARQUEMENT YACHT
    # ─────────────────────────────────────────────

    async def get_yacht_public_info(self, db: AsyncSession, token: str) -> dict | None:
        """Récupère les infos publiques du yacht via boarding_token."""
        stmt = (
            select(Yacht, EmployerProfile.company_name, User.name)
            .join(EmployerProfile, Yacht.employer_profile_id == EmployerProfile.id)
            .join(User, EmployerProfile.user_id == User.id)
            .where(Yacht.boarding_token == token)
        )
        result = await db.execute(stmt)
        row = result.first()
        if not row: return None
            
        yacht, co_name, user_name = row
        
        # Count de l'équipage actif
        res_count = await db.execute(
            select(func.count(CrewAssignment.id))
            .where(and_(CrewAssignment.yacht_id == yacht.id, CrewAssignment.is_active == True))
        )
        
        return {
            "name": yacht.name,
            "type": yacht.type,
            "length": yacht.length,
            "employer_name": co_name or user_name or "Employeur Privé",
            "current_crew_count": res_count.scalar() or 0
        }

    async def join_yacht(self, db: AsyncSession, token: str, user_id: int) -> YachtJoinOut:
        """Action d'embarquement : crée un CrewAssignment actif."""
        # 1. Trouver le Yacht & le CrewProfile
        yacht_stmt = await db.execute(select(Yacht).where(Yacht.boarding_token == token))
        yacht = yacht_stmt.scalar_one_or_none()
        if not yacht: raise ValueError("INVALID_TOKEN")

        crew_stmt = await db.execute(select(CrewProfile).where(CrewProfile.user_id == user_id))
        crew = crew_stmt.scalar_one_or_none()
        if not crew: raise ValueError("CREW_PROFILE_REQUIRED")

        # 2. Vérifier si une assignation existe déjà
        assign_stmt = await db.execute(
            select(CrewAssignment).where(
                and_(CrewAssignment.crew_profile_id == crew.id, CrewAssignment.yacht_id == yacht.id)
            )
        )
        existing = assign_stmt.scalar_one_or_none()
        
        if existing:
            if existing.is_active: raise ValueError("ALREADY_ABOARD")
            # Réactivation si c'était une ancienne expérience
            existing.is_active = True
            existing.start_date = datetime.now(timezone.utc)
        else:
            # Nouveau marquage
            new_assign = CrewAssignment(
                crew_profile_id=crew.id,
                yacht_id=yacht.id,
                role=crew.position_targeted, # Role par défaut basé sur le profil
                is_active=True,
                start_date=datetime.now(timezone.utc)
            )
            db.add(new_assign)

        await db.commit()
        return YachtJoinOut(yacht_id=yacht.id, yacht_name=yacht.name, joined_at=datetime.now(timezone.utc))

    # ─────────────────────────────────────────────
    # CANDIDATURE CAMPAGNE
    # ─────────────────────────────────────────────

    async def apply_to_campaign(self, db: AsyncSession, token: str, user_id: int) -> dict:
        """Crée un CampaignCandidate via invite_token."""
        camp_stmt = await db.execute(select(Campaign).where(Campaign.invite_token == token))
        campaign = camp_stmt.scalar_one_or_none()
        if not campaign or campaign.is_archived: raise ValueError("CAMPAIGN_UNAVAILABLE")

        crew_stmt = await db.execute(select(CrewProfile).where(CrewProfile.user_id == user_id))
        crew = crew_stmt.scalar_one_or_none()

        # Check duplicata
        dup_stmt = await db.execute(
            select(CampaignCandidate).where(
                and_(CampaignCandidate.campaign_id == campaign.id, CampaignCandidate.crew_profile_id == crew.id)
            )
        )
        if dup_stmt.scalar_one_or_none(): raise ValueError("ALREADY_APPLIED")

        candidate = CampaignCandidate(
            campaign_id=campaign.id,
            crew_profile_id=crew.id,
            status="pending"
        )
        db.add(candidate)
        await db.commit()

        return {"campaign_id": campaign.id, "applied_at": datetime.now(timezone.utc), "status": "pending"}

    # ─────────────────────────────────────────────
    # VÉRIFICATION D'EXPÉRIENCE (HTML)
    # ─────────────────────────────────────────────

    async def get_experience_by_token(self, db: AsyncSession, token: str) -> dict | None:
        """Données pour le template HTML de validation capitaine."""
        stmt = (
            select(CrewAssignment, User.name)
            .join(CrewProfile, CrewAssignment.crew_profile_id == CrewProfile.id)
            .join(User, CrewProfile.user_id == User.id)
            .where(CrewAssignment.verification_token == token)
        )
        result = await db.execute(stmt)
        row = result.first()
        if not row: return None
            
        assign, crew_name = row
        return {
            "candidate_name": crew_name,
            "yacht_name": assign.yacht_name, # Utilise la property du modèle
            "position": assign.role,
            "start_date": assign.start_date,
            "end_date": assign.end_date
        }

    async def submit_experience_verification(self, db: AsyncSession, token: str, comment: str) -> bool:
        """Le capitaine valide l'expérience déclarée."""
        stmt = await db.execute(select(CrewAssignment).where(CrewAssignment.verification_token == token))
        assign = stmt.scalar_one_or_none()
        if not assign: return False

        assign.is_harmony_approved = True
        assign.reference_comment = comment
        assign.verification_token = None # Brûle le token
        
        await db.commit()
        return True